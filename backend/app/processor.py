import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

def run(cmd: list[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)

def probe_duration(path: Path) -> float:
    result = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                  "-of", "default=noprint_wrappers=1:nokey=1", str(path)], timeout=120)
    return max(0.0, float(result.stdout.strip()))

def transcribe(path: Path):
    enabled = os.getenv("ENABLE_TRANSCRIPTION", "false").lower() == "true"
    if not enabled:
        return []
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(
            os.getenv("WHISPER_MODEL", "small"),
            device=os.getenv("WHISPER_DEVICE", "cpu"),
            compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
        )
        segments, _ = model.transcribe(str(path), vad_filter=True, word_timestamps=False)
        output = []
        for seg in segments:
            text = (seg.text or "").strip()
            if text:
                output.append({"start": float(seg.start), "end": float(seg.end), "text": text})
        return output
    except Exception as exc:
        # A failed optional model must not silently pretend transcription worked.
        return [{"error": f"Transcription unavailable: {type(exc).__name__}: {exc}"}]

def select_moments(duration: float, requested: int, segments: list[dict]):
    clean = [s for s in segments if "start" in s and "end" in s and s["end"] > s["start"]]
    candidates = []
    if clean:
        # Group nearby transcript segments into candidate windows; score by speech density.
        for seg in clean:
            start = max(0.0, seg["start"] - 3.0)
            end = min(duration, max(seg["end"] + 5.0, start + 18.0))
            if end - start < 8:
                continue
            text = " ".join(x["text"] for x in clean if x["start"] < end and x["end"] > start)
            words = len(re.findall(r"\w+", text))
            # Prefer concise, information-dense spoken passages; score is a ranking heuristic.
            score = min(100.0, 35.0 + words * 0.8 + min(15.0, (end-start) * 0.25))
            candidates.append({"start": start, "end": end, "score": round(score, 1), "transcript": text[:1200]})
    if not candidates:
        # Explicit fallback: evenly spaced candidate windows, not claimed to be AI-ranked.
        clip_len = min(30.0, max(12.0, duration / max(1, requested * 2)))
        if duration <= clip_len:
            starts = [0.0]
        else:
            starts = [((i + 1) * duration / (requested + 1)) - clip_len / 2 for i in range(requested)]
        for i, start in enumerate(starts):
            start = max(0.0, min(start, max(0.0, duration - clip_len)))
            candidates.append({"start": start, "end": min(duration, start + clip_len),
                               "score": round(50.0 - i * 0.1, 1), "transcript": ""})
    candidates.sort(key=lambda x: x["score"], reverse=True)
    selected = []
    for item in candidates:
        if all(abs(item["start"] - old["start"]) > 8 for old in selected):
            selected.append(item)
        if len(selected) >= requested:
            break
    selected.sort(key=lambda x: x["start"])
    return selected

def srt_timestamp(seconds: float) -> str:
    ms = int(max(0, seconds) * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def write_srt(path: Path, segments: list[dict], start: float, end: float):
    rows, idx = [], 1
    for seg in segments:
        if "start" not in seg or seg["end"] <= start or seg["start"] >= end:
            continue
        a, b = max(0, seg["start"] - start), min(end, seg["end"]) - start
        text = seg["text"].replace("-->", "→").strip()
        if text:
            rows.extend([str(idx), f"{srt_timestamp(a)} --> {srt_timestamp(b)}", text, ""])
            idx += 1
    path.write_text("\n".join(rows), encoding="utf-8")

def render_clip(source: Path, destination: Path, start: float, end: float, srt: Path | None):
    duration = max(1.0, end - start)
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1"
    if srt and srt.exists() and srt.stat().st_size:
        escaped = str(srt.resolve()).replace("\\", "/").replace(":", r"\:")
        vf += f",subtitles='{escaped}':force_style='FontName=DejaVu Sans,FontSize=18,Bold=1,Outline=2,Shadow=1,Alignment=2,MarginV=190'"
    run(["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(source), "-t", f"{duration:.3f}",
         "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(destination)], timeout=7200)

def process_project(project_id: str, db_path: Path, data_dir: Path):
    import sqlite3
    def update(status, error=None):
        with sqlite3.connect(db_path) as db:
            db.execute("UPDATE projects SET status=?, error=? WHERE id=?", (status, error, project_id))
    try:
        with sqlite3.connect(db_path) as db:
            row = db.execute("SELECT source_file, requested_clips FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row:
            return
        source, requested = Path(row[0]), int(row[1])
        if not source.exists():
            raise FileNotFoundError("Uploaded source file no longer exists.")
        update("analysing")
        duration = probe_duration(source)
        if duration <= 0:
            raise ValueError("Could not read video duration. Ensure the file is a valid video.")
        segments = transcribe(source)
        transcript_error = next((s.get("error") for s in segments if "error" in s), None)
        segments = [s for s in segments if "start" in s]
        moments = select_moments(duration, requested, segments)
        with sqlite3.connect(db_path) as db:
            db.execute("UPDATE projects SET duration=?, transcript_json=?, analysis_note=? WHERE id=?",
                       (duration, json.dumps(segments), transcript_error or
                        ("Speech transcription completed." if segments else "Transcription disabled; evenly spaced fallback moments selected."), project_id))
            db.execute("DELETE FROM clips WHERE project_id=?", (project_id,))
            for moment in moments:
                clip_id = str(uuid.uuid4())
                db.execute("""INSERT INTO clips(id, project_id, start_time, end_time, score, transcript, status)
                              VALUES(?,?,?,?,?,?,?)""",
                           (clip_id, project_id, moment["start"], moment["end"], moment["score"],
                            moment["transcript"], "queued"))
        update("rendering")
        export_dir = data_dir / "exports" / project_id
        export_dir.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as db:
            clips = db.execute("SELECT id,start_time,end_time FROM clips WHERE project_id=? ORDER BY start_time", (project_id,)).fetchall()
        for clip_id, start, end in clips:
            srt = export_dir / f"{clip_id}.srt"
            write_srt(srt, segments, start, end)
            output = export_dir / f"{clip_id}.mp4"
            render_clip(source, output, start, end, srt)
            with sqlite3.connect(db_path) as db:
                db.execute("UPDATE clips SET status='ready', file_path=? WHERE id=?", (str(output), clip_id))
        update("completed")
    except Exception as exc:
        update("failed", f"{type(exc).__name__}: {exc}")
