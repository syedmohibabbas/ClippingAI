# ClippingAI

A desktop-first, dark-only AI-assisted video clipping and editing studio.

> Status: foundation / early development. The UI and API scaffold are included; production AI moment ranking, authorized platform ingestion, GPU rendering, authentication, and deployment still require implementation and credentials.

## Product principles

- Original moments from source footage; AI does **not** invent replacement footage.
- 5–10 candidate clips ranked from transcript, scene and audio signals.
- 9:16 exports with editable captions, reframing, graphics and sound design.
- Desktop-only interface. Narrow viewports receive a deliberate unsupported-device screen.
- Black / charcoal visual system; no light theme.
- Lightweight browser client. CPU/GPU-heavy analysis and rendering belong on workers.
- Copyright-aware workflow: rights declaration, provenance records and risk flags. No editing trick can guarantee copyright clearance.

## Repository layout

- `frontend/` — React + TypeScript + Vite desktop workspace.
- `backend/` — FastAPI API foundation and health endpoint.
- `docs/ARCHITECTURE.md` — system design and implementation phases.
- `docs/PLATFORM_ACCESS.md` — YouTube, Facebook and Instagram constraints.
- `docker-compose.yml` — local API + Redis development services.

## Requirements

- Node.js 20+
- Python 3.11+
- Docker Desktop (optional, for Redis)
- FFmpeg installed on the worker host before rendering is enabled

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health: http://localhost:8000/health

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite. The UI currently uses sample project data and clearly labels processing actions as a foundation preview.

## Important implementation notes

1. Do not scrape or bypass platform access controls, DRM, login walls, rate limits or download restrictions.
2. Use official APIs, creator-authorized uploads, or licensed/otherwise authorized source files.
3. Instagram and Facebook access depends on Meta app review, permissions, account type and content ownership/access.
4. YouTube API access does not grant a general-purpose right to download arbitrary videos. Use authorized uploads or permitted access paths.
5. A copyright risk score is a workflow aid, not legal advice or a guarantee against claims.
6. Never store platform access tokens in the browser. Keep secrets in server-side environment variables.

## Current scope

Included:
- Dark-only, desktop-only dashboard UI foundation
- URL intake form with platform recognition
- Project / clip list presentation
- API health endpoint and typed job models
- Copyright / rights workflow guidance
- Architecture and platform integration notes

Not yet production-ready:
- Real platform ingestion and live-stream capture
- ASR/transcription and semantic moment ranking
- Face tracking / speaker-aware reframing
- FFmpeg render pipeline and timeline editor
- Authentication, billing, object storage, job queue workers
- Automated copyright matching (and no system can guarantee zero claims)

See `docs/ARCHITECTURE.md` for the staged build plan.
