"""
Feature 6 — NCRB Complaint Auto-fill

POST /api/v1/complaint/extract   — extract complaint fields from conversation text
POST /api/v1/complaint/submit    — mock submission (returns fake reference number)
GET  /api/v1/complaint/{user_id} — list draft complaints for a user

MVP-DEPTH: Real NCRB / cybercrime.gov.in API submission is future work.
The submission endpoint is clearly mocked and comments explain the integration path.
"""
from __future__ import annotations

import logging
import uuid
import random
import string
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.orm import NcrbComplaint
from app.models.schemas import (
    ComplaintDraft,
    ComplaintExtractRequest,
    ComplaintSubmitResponse,
)
from app.services import claude_service
from app.services.language import detect_language

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/complaint", tags=["NCRB Complaint"])


def _generate_ref_number() -> str:
    """Generate a plausible-looking mock complaint reference number."""
    year = datetime.now().year
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"NCRB-{year}-{rand}"


@router.post(
    "/extract",
    response_model=ComplaintDraft,
    summary="Auto-extract NCRB complaint fields from conversation text",
    description="Feature 6: Uses Claude + regex fallback to extract phone, amount, timestamp, description from scam conversation.",
)
async def extract_complaint(
    body: ComplaintExtractRequest,
    db: AsyncSession = Depends(get_db),
) -> ComplaintDraft:
    lang_code = detect_language(body.conversation_text)

    # Try Claude extraction first
    extracted: dict = {}
    try:
        extracted = await claude_service.extract_complaint_fields(
            body.conversation_text, lang_code
        )
    except Exception as exc:
        logger.warning("Claude extraction failed: %s — using regex fallback only", exc)

    # Regex fallback for phone and amount (always applied, overrides None)
    phone = extracted.get("phone_number") or claude_service.regex_extract_phone(body.conversation_text)
    amount = extracted.get("amount") or claude_service.regex_extract_amount(body.conversation_text)
    timestamp = extracted.get("incident_timestamp")
    description = extracted.get("description")
    scam_type = extracted.get("scam_type")

    complaint_id = uuid.uuid4()
    record = NcrbComplaint(
        id=complaint_id,
        user_id=body.user_id,
        phone_number=phone,
        amount=amount,
        incident_timestamp=timestamp,
        description=description,
        scam_type=scam_type,
    )
    db.add(record)

    return ComplaintDraft(
        complaint_id=complaint_id,
        user_id=body.user_id,
        phone_number=phone,
        amount=amount,
        incident_timestamp=timestamp,
        description=description,
        scam_type=scam_type,
        created_at=datetime.utcnow(),
    )


@router.post(
    "/submit/{complaint_id}",
    response_model=ComplaintSubmitResponse,
    summary="Submit a complaint (mock)",
    description="Feature 6: Mocked NCRB submission. Returns a fake reference number. Real API integration is future work.",
)
async def submit_complaint(
    complaint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ComplaintSubmitResponse:
    # Fetch existing draft
    result = await db.execute(
        select(NcrbComplaint).where(NcrbComplaint.id == complaint_id)
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # MVP-DEPTH: Replace this block with real HTTP call to cybercrime.gov.in API
    # when the NCRB API becomes publicly available (expected under MHA Digital India initiative).
    ref = _generate_ref_number()
    complaint.reference_number = ref
    complaint.submitted = True

    logger.info("Mock NCRB submission for complaint %s — ref: %s", complaint_id, ref)

    return ComplaintSubmitResponse(
        reference_number=ref,
        message=f"Complaint submitted successfully. Your reference number is {ref}.",
    )


@router.get(
    "/list/{user_id}",
    response_model=list[ComplaintDraft],
    summary="List complaint drafts for a user",
)
async def list_complaints(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ComplaintDraft]:
    result = await db.execute(
        select(NcrbComplaint)
        .where(NcrbComplaint.user_id == user_id)
        .order_by(NcrbComplaint.created_at.desc())
        .limit(20)
    )
    records = result.scalars().all()
    return [
        ComplaintDraft(
            complaint_id=r.id,
            user_id=r.user_id,
            phone_number=r.phone_number,
            amount=r.amount,
            incident_timestamp=r.incident_timestamp,
            description=r.description,
            scam_type=r.scam_type,
            created_at=r.created_at,
        )
        for r in records
    ]
