import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("CLIPPINGAI_DATA_DIR", APP_DIR.parent / "data")).resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "clippingai.sqlite3"
MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
ALLOWED_HOSTS = {"youtube.com", "youtu.be", "facebook.com", "fb.watch", "instagram.com"}

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="ClippingAI API",
    version="0.2.0",
    description="Project intake and authorized media upload API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://syedmohibabbas.github.io",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

Platform = Literal["youtube", "facebook", "instagram"]


def connect_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def initialize_db():
    with connect_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_url TEXT,
                source_file TEXT,
                original_filename TEXT,
                file_size INTEGER,
                requested_clips INTEGER NOT NULL,
                rights_basis TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


initialize_db()


class UrlProjectIntake(BaseModel):
    source_url: HttpUrl
    source_type: Platform
    requested_clips: int = Field(default=10, ge=5, le=10)
    rights_confirmed: bool
    rights_basis: str = Field(min_length=10, max_length=1000)


class ProjectResponse(BaseModel):
    id: str
    title: str
    source_type: str
    source_url: str | None
    original_filename: str | None
    file_size: int | None
    requested_clips: int
    status: str
    created_at: str
    message: str


def serialize(row):
    if row["source_type"] == "upload":
        message = (
            "File stored on this API host. The AI analysis worker is not connected yet."
        )
    else:
        message = (
            "Source URL registered. No video was downloaded; an authorized platform "
            "adapter and analysis worker are not connected yet."
        )
    return {
        "id": row["id"],
        "title": row["title"],
        "source_type": row["source_type"],
        "source_url": row["source_url"],
        "original_filename": row["original_filename"],
        "file_size": row["file_size"],
        "requested_clips": row["requested_clips"],
        "status": row["status"],
        "created_at": row["created_at"],
        "message": message,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "clippingai-api",
        "version": "0.2.0",
        "upload_enabled": True,
        "analysis_worker_enabled": False,
    }


@app.post("/v1/projects/url", response_model=ProjectResponse, status_code=202)
def create_url_project(payload: UrlProjectIntake):
    if not payload.rights_confirmed:
        raise HTTPException(status_code=400, detail="A rights declaration is required.")

    host = (urlparse(str(payload.source_url)).hostname or "").lower()
    if not any(host == allowed or host.endswith("." + allowed) for allowed in ALLOWED_HOSTS):
        raise HTTPException(
            status_code=400,
            detail="Only YouTube, Facebook and Instagram URLs are accepted.",
        )

    project_id = str(uuid.uuid4())
    created = datetime.now(timezone.utc).isoformat()
    title = f"{payload.source_type.title()} source project"

    with connect_db() as db:
        db.execute(
            """INSERT INTO projects
            (id, title, source_type, source_url, requested_clips, rights_basis, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                title,
                payload.source_type,
                str(payload.source_url),
                payload.requested_clips,
                payload.rights_basis.strip(),
                "awaiting_worker",
                created,
            ),
        )
        row = db.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()

    return serialize(row)


@app.post("/v1/projects/upload", response_model=ProjectResponse, status_code=202)
async def upload_project(
    file: UploadFile = File(...),
    requested_clips: int = Form(10),
    rights_confirmed: bool = Form(...),
    rights_basis: str = Form(...),
):
    if not rights_confirmed:
        raise HTTPException(status_code=400, detail="A rights declaration is required.")
    if not 5 <= requested_clips <= 10:
        raise HTTPException(status_code=400, detail="Choose between 5 and 10 clips.")
    if len(rights_basis.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Please provide a rights basis of at least 10 characters.",
        )

    filename = Path(file.filename or "source-video").name
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Supported formats: MP4, MOV, MKV, WEBM and M4V.",
        )

    project_id = str(uuid.uuid4())
    destination = UPLOAD_DIR / f"{project_id}{extension}"
    size = 0

    try:
        with destination.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="Maximum upload size is 2 GB.")
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    if size == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    created = datetime.now(timezone.utc).isoformat()
    title = Path(filename).stem[:180] or "Uploaded video"

    with connect_db() as db:
        db.execute(
            """INSERT INTO projects
            (id, title, source_type, source_file, original_filename, file_size,
             requested_clips, rights_basis, status, created_at)
            VALUES (?, ?, 'upload', ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                title,
                str(destination),
                filename,
                size,
                requested_clips,
                rights_basis.strip(),
                "awaiting_worker",
                created,
            ),
        )
        row = db.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()

    return serialize(row)


@app.get("/v1/projects", response_model=list[ProjectResponse])
def list_projects():
    with connect_db() as db:
        rows = db.execute(
            "SELECT * FROM projects ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
    return [serialize(row) for row in rows]


@app.get("/v1/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str):
    with connect_db() as db:
        row = db.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    return serialize(row)
