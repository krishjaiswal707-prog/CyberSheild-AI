"""
Feature 7 — Known Scammer Database Lookup

GET /api/v1/scammer/lookup?identifier=+919876543210

Looks up a phone number or email against the seeded known_scammers table.
Returns match info or "not found".

MVP-DEPTH: Production would integrate with:
  - I4C (Indian Cybercrime Coordination Centre) suspect database
  - TRAI's DNCR (Do Not Call Registry) and fraud number blacklists
  - Sanchar Saathi API for real-time number checks
"""
from __future__ import annotations

import logging
import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.orm import KnownScammer
from app.models.schemas import ScammerLookupResponse, ScammerRecord

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scammer", tags=["Scammer Database"])

# Normalise Indian phone numbers for matching
_PHONE_RE = re.compile(r"[\s\-\(\)]+")


def _normalise_identifier(identifier: str) -> str:
    """Strip spaces/dashes, normalise +91 prefix."""
    norm = _PHONE_RE.sub("", identifier.strip())
    if norm.startswith("0") and len(norm) == 11:
        norm = "+91" + norm[1:]
    elif re.match(r"^\d{10}$", norm):
        norm = "+91" + norm
    return norm.lower()


@router.get(
    "/lookup",
    response_model=ScammerLookupResponse,
    summary="Check if a phone number or email is in the known scammer database",
    description="Feature 7: Looks up the known_scammers table. Returns report count and scam type if found.",
)
async def lookup_scammer(
    identifier: str = Query(..., description="Phone number (+91XXXXXXXXXX) or email address"),
    db: AsyncSession = Depends(get_db),
) -> ScammerLookupResponse:
    norm = _normalise_identifier(identifier)

    result = await db.execute(
        select(KnownScammer).where(
            or_(
                func.lower(KnownScammer.identifier) == norm,
                func.lower(KnownScammer.identifier) == identifier.lower().strip(),
            )
        ).limit(1)
    )
    record = result.scalar_one_or_none()

    if not record:
        return ScammerLookupResponse(
            found=False,
            record=None,
            message=f"'{identifier}' not found in known scammer database. This does not guarantee the number is safe.",
        )

    return ScammerLookupResponse(
        found=True,
        record=ScammerRecord(
            identifier=record.identifier,
            identifier_type=record.identifier_type,
            report_count=record.report_count,
            scam_type=record.scam_type,
            source=record.source,
            last_reported=record.last_reported,
            notes=record.notes,
        ),
        message=f"⚠️ WARNING: This {'number' if record.identifier_type == 'phone' else 'address'} has been reported {record.report_count} time(s) for '{record.scam_type}' scams.",
    )
