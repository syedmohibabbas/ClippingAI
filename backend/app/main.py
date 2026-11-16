from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import Literal
from datetime import datetime, timezone

app = FastAPI(
    title="ClippingAI API",
    version="0.1.0",
    description="API foundation for the ClippingAI video clipping studio.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

Platform = Literal["youtube", "facebook", "instagram", "upload"]

class ProjectIntake(BaseModel):
    source_url: HttpUrl | None = None
    source_type: Platform
    requested_clips: int = Field(default=10, ge=5, le=10)
    rights_confirmed: bool
    rights_basis: str | None = None

class IntakeResponse(BaseModel):
    status: str
    message: str
    created_at: datetime

@app.get("/health")
def health():
    return {"status": "ok", "service": "clippingai-api", "version": "0.1.0"}

@app.post("/v1/projects", response_model=IntakeResponse)
def create_project(payload: ProjectIntake):
    if not payload.rights_confirmed:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="A rights declaration is required.")
    # Deliberately does not download or process arbitrary URLs.
    # A production adapter must verify platform permissions / authorized media access.
    return IntakeResponse(
        status="intake_received",
        message="Intake schema validated. Authorized source ingestion is not connected in this foundation build.",
        created_at=datetime.now(timezone.utc),
    )
