# Architecture

- React + TypeScript + Vite frontend (GitHub Pages compatible static build).
- FastAPI backend for upload, project history, transcript and clip downloads.
- SQLite for local MVP metadata.
- FFmpeg / FFprobe for source probing and 9:16 rendering.
- Optional Faster-Whisper for local transcription.
- BackgroundTasks runs processing in the API process for easy local setup.

## Production evolution still required
Move processing to a durable queue and isolated worker service; replace SQLite/local disk with managed database and private object storage; add authentication/authorization, signed downloads, retention, monitoring, autoscaling and billing. BackgroundTasks is not a durable job queue and a server restart can interrupt processing.
