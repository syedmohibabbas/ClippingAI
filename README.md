# ClippingAI — consolidated self-hosted MVP

ClippingAI turns **authorized video files** into vertical short-form clips. This package replaces the repository contents and includes a connected frontend, FastAPI backend, FFmpeg rendering pipeline, optional Faster-Whisper transcription, project history, and deployment instructions.

## What works in this package
- Upload MP4, MOV, MKV, WEBM or M4V files (up to the configured limit).
- Create a project and track processing status.
- Extract audio and inspect source duration.
- Optional speech transcription with Faster-Whisper.
- Select candidate moments from transcript segments; fallback to evenly distributed moments when transcription is unavailable.
- Render selected moments as 9:16 MP4 clips with burned-in captions when transcript segments exist.
- Download completed clips and inspect source timestamps.
- Dark desktop-first React dashboard connected to the API.

## Important limits — read before deployment
- This is a self-hosted MVP, **not a finished commercial SaaS**. It has no user accounts, billing, team permissions, malware scanning, cloud object storage, distributed queue, or production observability.
- The default transcription mode is `auto`: it attempts Faster-Whisper only when installed and enabled; otherwise it uses a transparent fallback. Install the `ai` requirements and set `ENABLE_TRANSCRIPTION=true` to enable speech transcription. First model run downloads model weights and needs internet access.
- Candidate selection is an automated heuristic, not a guarantee that every selected moment is viral or contextually perfect. Review clips before publishing.
- Face tracking, speaker diarization, advanced motion graphics, music licensing, SFX library, and a multi-track timeline editor are not included in this MVP.
- A URL pasted from YouTube, Facebook or Instagram is **not downloaded**. Platform ingestion requires official permitted APIs, app review, account permissions and/or creator-authorized source files. This app intentionally does not scrape, bypass DRM, or circumvent platform restrictions.
- Copyright risk cannot be eliminated by cropping, captions, zooms or editing. Only process material you own, have licensed, or are otherwise legally authorized to use. The rights declaration is a workflow record, not legal advice.

## Requirements
- Python 3.11+
- Node.js 20+
- FFmpeg and FFprobe installed and available on PATH
- Optional: `pip install -r backend/requirements-ai.txt` for Faster-Whisper

## Run on Windows
### Backend
```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# Optional speech transcription:
# pip install -r requirements-ai.txt
$env:CLIPPINGAI_DATA_DIR = "$PWD\data"
$env:ENABLE_TRANSCRIPTION = "false" # change to true after installing requirements-ai
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Check `http://127.0.0.1:8000/health` and API docs at `http://127.0.0.1:8000/docs`.

### Frontend
Open another terminal:
```powershell
cd frontend
npm install
# Optional: point to a separately hosted API:
# create .env.local and set VITE_API_BASE_URL=https://your-api.example.com
npm run dev
```
Open the Vite URL printed in the terminal.

## Docker
```bash
docker compose up --build
```
The API is exposed on port 8000. The compose file mounts persistent `./backend/data`. For transcription, build with the optional AI requirements or install them in a custom image. Configure a real domain and HTTPS before public use.

## GitHub Pages
GitHub Pages can host the frontend only. It cannot run Python, FFmpeg, background processing or store uploaded files durably. Deploy the backend separately to a server/container platform with persistent disk, FFmpeg, HTTPS, and sufficient CPU/RAM. Then set the GitHub Actions repository variable `VITE_API_BASE_URL` to the backend's public base URL (no trailing slash), or build/deploy the frontend with that environment variable. Never put secrets in `VITE_*` variables.

## Configuration
- `CLIPPINGAI_DATA_DIR`: persistent directory for SQLite database and uploads/exports.
- `MAX_UPLOAD_MB`: upload limit (default 2048).
- `ENABLE_TRANSCRIPTION`: `true` / `false` (default false).
- `WHISPER_MODEL`: `small` by default when transcription is enabled.
- `WHISPER_DEVICE`: `cpu` by default.
- `WHISPER_COMPUTE_TYPE`: `int8` by default.
- `CORS_ORIGINS`: comma-separated allowed browser origins. Set to your deployed frontend origin(s).

## API
- `GET /health`
- `POST /v1/projects/upload` (multipart: `file`, `requested_clips`, `rights_confirmed`, `rights_basis`)
- `POST /v1/projects/url` (records a supported source URL only; does not fetch it)
- `GET /v1/projects`
- `GET /v1/projects/{project_id}`
- `GET /v1/projects/{project_id}/clips`
- `GET /v1/clips/{clip_id}/download`

## Security checklist before public launch
1. Add authentication and per-user authorization to every project and download route.
2. Put uploads/exports in private object storage; use signed URLs.
3. Add reverse-proxy request-size limits, rate limiting, malware scanning and abuse controls.
4. Restrict CORS to your exact frontend origin.
5. Run workers in isolated containers with CPU/memory/time quotas and no unnecessary network access.
6. Add backups, retention/deletion controls, monitoring and error reporting.
7. Review platform terms, API policies, privacy law and copyright requirements for each supported workflow.
