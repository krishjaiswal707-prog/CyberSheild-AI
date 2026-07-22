"""
Feature 11 — Verification Hotline Lookup

GET /api/v1/hotline/all            — list all verified hotlines
GET /api/v1/hotline/lookup?q=CBI   — search by organization name (partial match)
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Query

from app.models.schemas import HotlineEntry, HotlineLookupResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hotline", tags=["Verification Hotlines"])

DATA_PATH = Path(__file__).parent.parent / "data" / "hotlines.json"


@lru_cache(maxsize=1)
def _load_hotlines() -> list[dict]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["hotlines"]


@router.get(
    "/all",
    response_model=HotlineLookupResponse,
    summary="List all verified hotlines",
    description="Feature 11: Returns all verified government and banking fraud hotlines.",
)
async def list_all_hotlines() -> HotlineLookupResponse:
    hotlines = _load_hotlines()
    return HotlineLookupResponse(
        query="*",
        results=[HotlineEntry(**h) for h in hotlines],
        total=len(hotlines),
    )


@router.get(
    "/lookup",
    response_model=HotlineLookupResponse,
    summary="Search hotlines by organization name",
    description="Feature 11: Case-insensitive partial search on organization name.",
)
async def lookup_hotline(
    q: str = Query(..., min_length=1, description="Organization name to search, e.g. 'CBI', 'RBI', 'SBI'"),
) -> HotlineLookupResponse:
    hotlines = _load_hotlines()
    q_lower = q.lower()
    matched = [h for h in hotlines if q_lower in h["organization"].lower()]
    return HotlineLookupResponse(
        query=q,
        results=[HotlineEntry(**h) for h in matched],
        total=len(matched),
    )
