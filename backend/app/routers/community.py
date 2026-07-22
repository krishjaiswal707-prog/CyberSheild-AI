"""
Feature 10 — Community Reporting & Clustering

POST /api/v1/community/report    — submit a new scam report
GET  /api/v1/community/clusters  — cluster recent reports by TF-IDF similarity
GET  /api/v1/community/reports   — list recent raw reports (for dashboard)
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.orm import ScamReport
from app.models.schemas import (
    ClusteringResponse,
    ClusterSummary,
    ScamReportRequest,
    ScamReportResponse,
)
from app.services.clustering import (
    build_cluster_summaries,
    cluster_reports,
    find_similar_count,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/community", tags=["Community Reports"])


@router.post(
    "/report",
    response_model=ScamReportResponse,
    summary="Submit a community scam report",
    description="Feature 10: Submit a new scam report. Returns the number of similar reports already in the database.",
)
async def submit_report(
    body: ScamReportRequest,
    db: AsyncSession = Depends(get_db),
) -> ScamReportResponse:
    # Fetch existing report texts to compute similarity
    result = await db.execute(
        select(ScamReport.report_text).order_by(ScamReport.created_at.desc()).limit(500)
    )
    existing_texts = [row[0] for row in result.fetchall()]

    similar_count = find_similar_count(body.report_text, existing_texts)

    report_id = uuid.uuid4()
    record = ScamReport(
        id=report_id,
        user_id=body.user_id,
        report_text=body.report_text,
        scam_type=body.scam_type,
        location=body.location,
        phone_number=body.phone_number,
    )
    db.add(record)

    return ScamReportResponse(
        report_id=report_id,
        message=f"Report submitted. {similar_count} similar report(s) found in our database." if similar_count else "Report submitted. First report of this type.",
        similar_reports_found=similar_count,
        cluster_id=None,  # Cluster ID assigned on next /clusters call
    )


@router.get(
    "/clusters",
    response_model=ClusteringResponse,
    summary="Cluster recent community reports by text similarity",
    description="Feature 10: Runs TF-IDF + cosine similarity clustering on the N most recent reports and returns cluster summaries.",
)
async def get_clusters(
    limit: int = Query(200, ge=10, le=1000, description="Max reports to cluster"),
    db: AsyncSession = Depends(get_db),
) -> ClusteringResponse:
    result = await db.execute(
        select(ScamReport).order_by(ScamReport.created_at.desc()).limit(limit)
    )
    reports = result.scalars().all()

    if not reports:
        return ClusteringResponse(
            total_reports_analyzed=0,
            clusters_found=0,
            clusters=[],
        )

    report_dicts = [
        {
            "id": str(r.id),
            "report_text": r.report_text,
            "scam_type": r.scam_type,
            "cluster_id": None,
        }
        for r in reports
    ]

    clustered = cluster_reports(report_dicts)
    summaries = build_cluster_summaries(clustered)

    # Persist cluster IDs back to DB
    for rd in clustered:
        await db.execute(
            update(ScamReport)
            .where(ScamReport.id == uuid.UUID(rd["id"]))
            .values(cluster_id=rd.get("cluster_id"))
        )

    return ClusteringResponse(
        total_reports_analyzed=len(reports),
        clusters_found=len(summaries),
        clusters=[
            ClusterSummary(
                cluster_id=s["cluster_id"],
                report_count=s["report_count"],
                representative_text=s["representative_text"],
                common_scam_type=s["common_scam_type"],
            )
            for s in summaries
        ],
    )


@router.get(
    "/reports",
    summary="List recent community reports",
)
async def list_reports(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    result = await db.execute(
        select(ScamReport).order_by(ScamReport.created_at.desc()).limit(limit)
    )
    reports = result.scalars().all()
    return [
        {
            "report_id": str(r.id),
            "user_id": r.user_id,
            "report_text": r.report_text[:300],
            "scam_type": r.scam_type,
            "location": r.location,
            "phone_number": r.phone_number,
            "cluster_id": r.cluster_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]
