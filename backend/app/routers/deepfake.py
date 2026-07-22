"""
Feature 9 — Video Call Deepfake / Voice Spoofing Check

POST /api/v1/deepfake/check — accepts a file upload, returns structured verdict

Supported: video/mp4, video/webm, audio/wav, audio/mpeg, audio/ogg
Max file size: 50 MB (enforced by FastAPI/uvicorn — set in main.py)

MVP-DEPTH: Uses heuristic analysis only (OpenCV frame variance + librosa spectral analysis).
Production would use:
  - FaceForensics++ / EfficientNet-B4 trained deepfake model
  - Wav2Vec2-based voice synthesis classifier
  - Real-time stream analysis instead of file upload
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import DeepfakeVerdict
from app.services.deepfake_heuristic import analyse_media

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/deepfake", tags=["Deepfake Detection"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post(
    "/check",
    response_model=DeepfakeVerdict,
    summary="Check a video or audio file for deepfake/voice spoofing signals",
    description=(
        "Feature 9: Accepts a video or audio file and runs heuristic analysis. "
        "Returns likely_deepfake verdict, confidence score, and notes on which signals fired."
    ),
)
async def check_deepfake(
    file: UploadFile = File(..., description="Video (mp4/webm) or audio (wav/mp3/ogg) file to analyse"),
) -> DeepfakeVerdict:
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "upload"

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE // (1024*1024)} MB.",
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    logger.info(
        "Deepfake check: file=%s content_type=%s size=%d bytes",
        filename, content_type, len(file_bytes),
    )

    result = await analyse_media(file_bytes, content_type, filename)

    return DeepfakeVerdict(
        likely_deepfake=result["likely_deepfake"],
        confidence=result["confidence"],
        media_type=result["media_type"],
        notes=result["notes"],
        heuristics_used=result["heuristics_used"],
    )
