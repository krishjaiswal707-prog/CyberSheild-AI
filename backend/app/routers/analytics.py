"""
Feature 13 — Analytics & Trend Dashboard

GET /api/v1/analytics/trends — aggregate stats for frontend dashboard

Returns:
  - Total analyses and community reports
  - Risk tier distribution
  - Top scam types (from community reports)
  - Top red flags (across all analyses)
  - Daily volume (last 30 days)
  - Language breakdown

MVP-DEPTH: Production would add:
  - Real-time streaming updates via WebSocket
  - Geographic heatmap data (if location is collected)
  - Time-series trend alerting (spike detection)
  - Per-state breakdowns
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.orm import ScamAnalysis, ScamReport
from app.models.schemas import RiskDistribution, TrendAnalyticsResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/trends",
    response_model=TrendAnalyticsResponse,
    summary="Aggregate analytics and trend data for the dashboard",
    description="Feature 13: Returns risk distribution, top flags, scam types, daily volume, and language stats.",
)
async def get_trends(db: AsyncSession = Depends(get_db)) -> TrendAnalyticsResponse:
    # ── Total counts ───────────────────────────────────────────────────────────
    total_analyses_result = await db.execute(
        select(func.count(ScamAnalysis.id))
    )
    total_analyses = total_analyses_result.scalar() or 0

    total_reports_result = await db.execute(
        select(func.count(ScamReport.id))
    )
    total_reports = total_reports_result.scalar() or 0

    # ── Risk tier distribution ─────────────────────────────────────────────────
    tier_result = await db.execute(
        select(ScamAnalysis.risk_tier, func.count(ScamAnalysis.id).label("cnt"))
        .group_by(ScamAnalysis.risk_tier)
    )
    tier_rows = tier_result.fetchall()
    tier_dist = RiskDistribution()
    for row in tier_rows:
        if hasattr(tier_dist, row.risk_tier):
            setattr(tier_dist, row.risk_tier, row.cnt)

    # ── Top scam types (from community reports) ────────────────────────────────
    scam_type_result = await db.execute(
        select(ScamReport.scam_type, func.count(ScamReport.id).label("cnt"))
        .where(ScamReport.scam_type.isnot(None))
        .group_by(ScamReport.scam_type)
        .order_by(func.count(ScamReport.id).desc())
        .limit(10)
    )
    top_scam_types = [
        {"scam_type": row.scam_type, "count": row.cnt}
        for row in scam_type_result.fetchall()
    ]

    # ── Top red flags (across all analyses) ───────────────────────────────────
    # Pull matched_red_flags JSON arrays and count occurrences
    flags_result = await db.execute(
        select(ScamAnalysis.matched_red_flags)
        .where(ScamAnalysis.matched_red_flags.isnot(None))
        .order_by(ScamAnalysis.created_at.desc())
        .limit(500)
    )
    all_flags = []
    for row in flags_result.fetchall():
        flags = row[0]
        if isinstance(flags, list):
            all_flags.extend(flags)

    flag_counter = Counter(all_flags).most_common(15)
    top_red_flags = [{"flag": f, "count": c} for f, c in flag_counter]

    # ── Daily volume (last 30 days) ────────────────────────────────────────────
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    date_col = func.date(ScamAnalysis.created_at)
    daily_result = await db.execute(
        select(date_col.label("day"), func.count(ScamAnalysis.id).label("cnt"))
        .where(ScamAnalysis.created_at >= thirty_days_ago)
        .group_by(date_col)
        .order_by(date_col.desc())
        .limit(30)
    )
    daily_volume = [
        {"date": str(row.day), "count": row.cnt}
        for row in daily_result.fetchall()
    ]

    # ── Language breakdown ─────────────────────────────────────────────────────
    lang_result = await db.execute(
        select(ScamAnalysis.language, func.count(ScamAnalysis.id).label("cnt"))
        .group_by(ScamAnalysis.language)
    )
    language_breakdown = {row.language: row.cnt for row in lang_result.fetchall()}

    return TrendAnalyticsResponse(
        total_analyses=total_analyses,
        total_community_reports=total_reports,
        risk_distribution=tier_dist,
        top_scam_types=top_scam_types,
        top_red_flags=top_red_flags,
        daily_volume=daily_volume,
        language_breakdown=language_breakdown,
    )
