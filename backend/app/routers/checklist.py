"""
Feature 12 — Post-Scam Safety Checklist

GET /api/v1/checklist                           — return the full checklist
GET /api/v1/checklist?trigger=already_paid      — contextual trigger label
GET /api/v1/checklist?risk_tier=CRITICAL        — triggered by analysis result

IMPORTANT: This endpoint is NOT LLM-backed.
The checklist is static JSON — deterministic and safety-critical.
Content must NEVER vary based on AI output.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Query

from app.models.schemas import ChecklistItem, SafetyChecklistResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/checklist", tags=["Safety Checklist"])

DATA_PATH = Path(__file__).parent.parent / "data" / "checklist.json"


@lru_cache(maxsize=1)
def _load_checklist() -> list[dict]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["checklist"]


def _determine_trigger(risk_tier: str | None, already_paid: bool) -> str:
    if already_paid:
        return "User indicated they already transferred money"
    if risk_tier in ("HIGH", "CRITICAL"):
        return f"Analysis returned {risk_tier} risk — immediate action recommended"
    return "User requested safety checklist"


@router.get(
    "",
    response_model=SafetyChecklistResponse,
    summary="Get the post-scam safety checklist",
    description=(
        "Feature 12: Returns a fixed, ordered safety checklist. "
        "Triggered automatically when risk_tier is HIGH/CRITICAL, or when user indicates they already paid. "
        "NOT LLM-generated — fully deterministic for safety-critical reliability."
    ),
)
async def get_checklist(
    risk_tier: str | None = Query(None, description="Risk tier from analysis: LOW/MEDIUM/HIGH/CRITICAL"),
    already_paid: bool = Query(False, description="Set true if the user already transferred money"),
) -> SafetyChecklistResponse:
    items = _load_checklist()
    trigger = _determine_trigger(risk_tier, already_paid)

    return SafetyChecklistResponse(
        trigger=trigger,
        total_steps=len(items),
        checklist=[ChecklistItem(**item) for item in items],
    )
