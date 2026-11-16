# ClippingAI — Architecture

## High-level flow

1. User submits a supported URL or uploads a file they are authorized to use.
2. API validates the source and records rights declaration + provenance.
3. An ingestion adapter obtains media only through an authorized method.
4. Worker extracts audio, scene boundaries, timestamps and metadata.
5. ASR creates a timestamped transcript.
6. Moment ranker scores candidate ranges using hook strength, completeness, novelty, audio energy and visual changes.
7. Deduplication chooses 5–10 non-overlapping moments.
8. User reviews and adjusts in the desktop editor.
9. Render worker uses FFmpeg and licensed assets to create 9:16 exports.
10. User downloads the result and retains source / license provenance.

## Services

- Web client: React + TypeScript + Vite. Keep dependencies small; no video rendering in the browser.
- API: FastAPI, Pydantic schemas, PostgreSQL in production.
- Queue: Redis + Celery / Dramatiq worker (not wired in this foundation).
- Storage: S3-compatible object storage with lifecycle policies.
- Media: FFmpeg, ffprobe; optional GPU acceleration for supported operations.
- AI: ASR, embeddings / LLM-assisted semantic ranking, scene detection and face tracking behind provider interfaces.

## Clip ranking

A ranking model should combine measurable signals rather than promise virality:
- Opening hook / question / surprising statement
- Self-contained context and payoff
- Emotional or conversational intensity
- Transcript topic relevance
- Visual scene changes / speaker activity
- Novelty versus other selected clips
- Penalties for incomplete sentences, missing context and excessive overlap

The score is a prioritization estimate, not a prediction of actual virality.

## Performance requirements

- Browser only handles UI, preview playback and lightweight editing state.
- All transcription, analysis and rendering run on server workers.
- Use chunked uploads, resumable jobs, bounded concurrency and queue back-pressure.
- Generate preview proxies and thumbnails; do not load full-resolution media into dashboard lists.
- Lazy-load editor modules and avoid shipping AI / FFmpeg dependencies to the browser.
- Show progress from persisted job state, not a permanently running browser process.

## Security and rights

- Validate URL scheme and host; defend against SSRF and private-network targets.
- Never accept arbitrary filesystem paths from clients.
- Store credentials only in server-side secret storage.
- Keep a source URL, uploader / owner assertion, license or permission evidence, and processing timestamps.
- Rights declarations are not proof. Provide a takedown / deletion workflow before public launch.
- No watermark removal, DRM bypass, access-control circumvention or platform scraping.

## Delivery phases

### Phase 1 — Foundation
Dashboard, API skeleton, design system, schemas, docs and local run instructions.

### Phase 2 — Source access
Official API / OAuth integrations and authorized file upload. Validate platform terms and permissions before enabling each adapter.

### Phase 3 — Analysis
Transcription with word timestamps, scene detection, candidate extraction, semantic ranking and deduplication.

### Phase 4 — Editing
Editable timeline, speaker-aware crop, animated captions, graphics presets, licensed music / SFX.

### Phase 5 — Rendering and operations
FFmpeg worker, job queue, storage, retries, observability, export profiles and resource limits.

### Phase 6 — Hardening
Auth, rate limits, abuse controls, tests, security review, accessibility and production deployment.
