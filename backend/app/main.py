import os, sqlite3, uuid, threading, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, HttpUrl
from .processor import process_project

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("CLIPPINGAI_DATA_DIR", APP_DIR.parent / "data")).resolve()
UPLOAD_DIR, EXPORT_DIR = DATA_DIR / "uploads", DATA_DIR / "exports"
DB_PATH = DATA_DIR / "clippingai.sqlite3"
MAX_BYTES = int(os.getenv("MAX_UPLOAD_MB", "2048")) * 1024 * 1024
ALLOWED_EXT = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
ALLOWED_HOSTS = {"youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com"}
DATA_DIR.mkdir(parents=True, exist_ok=True); UPLOAD_DIR.mkdir(parents=True, exist_ok=True); EXPORT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="ClippingAI API", version="1.0.0",
              description="Authorized source upload, automated moment selection and vertical clip rendering.")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                   allow_methods=["GET","POST","OPTIONS"], allow_headers=["*"])

def db_conn():
    c = sqlite3.connect(DB_PATH); c.row_factory = sqlite3.Row; return c

def init_db():
    with db_conn() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS projects(
          id TEXT PRIMARY KEY, title TEXT NOT NULL, source_type TEXT NOT NULL,
          source_url TEXT, source_file TEXT, original_filename TEXT, file_size INTEGER,
          duration REAL, requested_clips INTEGER NOT NULL, rights_basis TEXT NOT NULL,
          status TEXT NOT NULL, error TEXT, transcript_json TEXT, analysis_note TEXT,
          created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS clips(
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL, start_time REAL NOT NULL,
          end_time REAL NOT NULL, score REAL NOT NULL, transcript TEXT,
          status TEXT NOT NULL, file_path TEXT,
          FOREIGN KEY(project_id) REFERENCES projects(id));
        """)
init_db()

class URLIntake(BaseModel):
    source_url: HttpUrl
    requested_clips: int = Field(default=10, ge=5, le=10)
    rights_confirmed: bool
    rights_basis: str = Field(min_length=10, max_length=1000)

def project_dict(row):
    d = dict(row)
    d.pop("source_file", None); d.pop("rights_basis", None); d.pop("transcript_json", None)
    d["message"] = d.get("analysis_note") or ("Processing source video." if d["status"] not in ("completed","failed") else "")
    return d

@app.get("/health")
def health():
    return {"status":"ok","service":"clippingai-api","version":"1.0.0",
            "ffmpeg_available": __import__("shutil").which("ffmpeg") is not None,
            "transcription_enabled": os.getenv("ENABLE_TRANSCRIPTION","false").lower()=="true",
            "url_downloader_available": __import__("importlib.util").util.find_spec("yt_dlp") is not None}

@app.post("/v1/projects/upload", status_code=202)
async def upload_project(background: BackgroundTasks, file: UploadFile=File(...),
                         requested_clips: int=Form(10), rights_confirmed: bool=Form(...),
                         rights_basis: str=Form(...)):
    if not rights_confirmed: raise HTTPException(400,"A rights declaration is required.")
    if not 5 <= requested_clips <= 10: raise HTTPException(400,"Choose 5 to 10 clips.")
    if len(rights_basis.strip()) < 10: raise HTTPException(400,"Explain your rights basis (at least 10 characters).")
    filename = Path(file.filename or "source-video").name
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT: raise HTTPException(415,"Supported formats: MP4, MOV, MKV, WEBM, M4V.")
    pid = str(uuid.uuid4()); dest = UPLOAD_DIR / f"{pid}{ext}"; size = 0
    try:
        with dest.open("wb") as out:
            while chunk := await file.read(1024*1024):
                size += len(chunk)
                if size > MAX_BYTES: raise HTTPException(413,f"Upload exceeds {MAX_BYTES//(1024*1024)} MB.")
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True); raise
    finally: await file.close()
    if not size: dest.unlink(missing_ok=True); raise HTTPException(400,"Uploaded file is empty.")
    created = datetime.now(timezone.utc).isoformat()
    with db_conn() as db:
        db.execute("""INSERT INTO projects(id,title,source_type,source_file,original_filename,file_size,
                   requested_clips,rights_basis,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                   (pid,Path(filename).stem[:180] or "Uploaded video","upload",str(dest),filename,size,
                    requested_clips,rights_basis.strip(),"queued",created))
    background.add_task(process_project,pid,DB_PATH,DATA_DIR)
    with db_conn() as db: row=db.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    return project_dict(row)

def download_and_process_url(project_id: str, source_url: str):
    """Fetch a publicly accessible, non-DRM video with yt-dlp, then run the normal clip pipeline."""
    import glob
    download_dir = UPLOAD_DIR / project_id
    download_dir.mkdir(parents=True, exist_ok=True)
    try:
        with db_conn() as db:
            db.execute("UPDATE projects SET status='downloading', analysis_note=? WHERE id=?",
                       ("Fetching the public video source…", project_id))
        template = str(download_dir / "source.%(ext)s")
        cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-warnings",
               "--restrict-filenames", "--max-filesize", str(MAX_BYTES),
               "-f", "bv*+ba/b", "--merge-output-format", "mp4",
               "-o", template, source_url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        candidates = [Path(x) for x in glob.glob(str(download_dir / "source.*"))
                      if Path(x).suffix.lower() in ALLOWED_EXT and Path(x).is_file()]
        if result.returncode != 0 or not candidates:
            detail = (result.stderr or result.stdout or "The source could not be downloaded.").strip()
            raise RuntimeError(detail[-1800:])
        source = max(candidates, key=lambda x: x.stat().st_size)
        size = source.stat().st_size
        if size > MAX_BYTES:
            raise RuntimeError(f"Downloaded video exceeds {MAX_BYTES // (1024*1024)} MB.")
        with db_conn() as db:
            db.execute("UPDATE projects SET title=?, source_file=?, original_filename=?, file_size=?, status='queued', analysis_note=? WHERE id=?",
                       (source.stem[:180], str(source), source.name, size, "Video fetched. Analysis and clip rendering are queued.", project_id))
        process_project(project_id, DB_PATH, DATA_DIR)
    except Exception as exc:
        with db_conn() as db:
            db.execute("UPDATE projects SET status='failed', error=?, analysis_note=? WHERE id=?",
                       (f"{type(exc).__name__}: {exc}", "Could not fetch or process this link. Some posts require login, are private, region-restricted, or unavailable to the downloader.", project_id))

@app.post("/v1/projects/url", status_code=202)
def register_url(payload: URLIntake, background: BackgroundTasks):
    if not payload.rights_confirmed: raise HTTPException(400,"A rights declaration is required.")
    host=(urlparse(str(payload.source_url)).hostname or "").lower()
    if not any(host==h or host.endswith("."+h) for h in ALLOWED_HOSTS):
        raise HTTPException(400,"Only YouTube, Facebook and Instagram links are accepted.")
    pid=str(uuid.uuid4()); created=datetime.now(timezone.utc).isoformat()
    with db_conn() as db:
        db.execute("""INSERT INTO projects(id,title,source_type,source_url,requested_clips,rights_basis,status,created_at,analysis_note)
        VALUES(?,?,?,?,?,?,?,?,?)""",(pid,"Video link","url",str(payload.source_url),payload.requested_clips,
        payload.rights_basis.strip(),"queued",created,"Link accepted. Video download is queued."))
        row=db.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    background.add_task(download_and_process_url, pid, str(payload.source_url))
    return project_dict(row)

@app.get("/v1/projects")
def list_projects():
    with db_conn() as db: rows=db.execute("SELECT * FROM projects ORDER BY created_at DESC LIMIT 100").fetchall()
    return [project_dict(r) for r in rows]

@app.get("/v1/projects/{project_id}")
def get_project(project_id:str):
    with db_conn() as db: row=db.execute("SELECT * FROM projects WHERE id=?",(project_id,)).fetchone()
    if not row: raise HTTPException(404,"Project not found.")
    return project_dict(row)

@app.get("/v1/projects/{project_id}/clips")
def list_clips(project_id:str):
    with db_conn() as db:
        exists=db.execute("SELECT 1 FROM projects WHERE id=?",(project_id,)).fetchone()
        if not exists: raise HTTPException(404,"Project not found.")
        rows=db.execute("SELECT id,project_id,start_time,end_time,score,transcript,status FROM clips WHERE project_id=? ORDER BY start_time",(project_id,)).fetchall()
    return [dict(r) for r in rows]

@app.get("/v1/clips/{clip_id}/download")
def download_clip(clip_id:str):
    with db_conn() as db: row=db.execute("SELECT file_path FROM clips WHERE id=? AND status='ready'",(clip_id,)).fetchone()
    if not row or not row["file_path"]: raise HTTPException(404,"Clip is not ready.")
    path=Path(row["file_path"])
    if not path.is_file(): raise HTTPException(404,"Export file is missing.")
    return FileResponse(path,media_type="video/mp4",filename=f"clippingai-{clip_id[:8]}.mp4")

@app.get("/v1/projects/{project_id}/transcript")
def get_transcript(project_id:str):
    with db_conn() as db: row=db.execute("SELECT transcript_json FROM projects WHERE id=?",(project_id,)).fetchone()
    if not row: raise HTTPException(404,"Project not found.")
    import json
    return {"segments":json.loads(row["transcript_json"] or "[]")}
