"""
Feature 8 — Personal Scam History

GET /api/v1/history/{user_id}          — full history for a user
GET /api/v1/history/{user_id}/summary  — quick stats (total, highest risk seen)
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.orm import ScamAnalysis
from app.models.schemas import HistoryItem, HistoryResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/history", tags=["Personal History"])


@router.get(
    "/{user_id}",
    response_model=HistoryResponse,
    summary="Get scam analysis history for a user",
    description="Feature 8: Returns all analysis records for the given user_id, newest first.",
)
async def get_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> HistoryResponse:
    result = await db.execute(
        select(ScamAnalysis)
        .where(ScamAnalysis.user_id == user_id)
        .order_by(ScamAnalysis.created_at.desc())
        .limit(limit)
    )
    records = result.scalars().all()

    items = [
        HistoryItem(
            analysis_id=r.id,
            analysis_type=r.analysis_type,
            risk_score=r.risk_score,
            risk_tier=r.risk_tier,
            matched_red_flags=r.matched_red_flags or [],
            language=r.language,
            created_at=r.created_at,
        )
        for r in records
    ]

    return HistoryResponse(
        user_id=user_id,
        total_analyses=len(items),
        history=items,
    )


@router.get(
    "/{user_id}/summary",
    summary="Quick stats for a user's analysis history",
)
async def get_history_summary(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(
            func.count(ScamAnalysis.id).label("total"),
            func.max(ScamAnalysis.risk_score).label("highest_score"),
            func.avg(ScamAnalysis.risk_score).label("avg_score"),
        ).where(ScamAnalysis.user_id == user_id)
    )
    row = result.one()

    return {
        "user_id": user_id,
        "total_analyses": row.total or 0,
        "highest_risk_score": row.highest_score or 0,
        "average_risk_score": round(float(row.avg_score or 0), 1),
    }
