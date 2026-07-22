"""
Features 1 & 2 — Message and Call Risk Analysis

POST /api/v1/analysis/message  — analyse a forwarded text message
POST /api/v1/analysis/call     — analyse a described voice/video call

Pipeline per request:
  1. Detect language (langdetect)
  2. Run rule engine (pre-LLM, auditable)
  3. Call Claude (with rule flags injected into prompt)
  4. Fuse outputs (rule override if rule floor > LLM score)
  5. Persist result to DB
  6. Return clean JSON response

If Claude fails: fall back to rule-engine-only scoring.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.orm import ScamAnalysis
from app.models.schemas import (
    AnalysisResponse,
    CallAnalysisRequest,
    MessageAnalysisRequest,
)
from app.services import claude_service
from app.services.language import detect_language
from app.services.rule_engine import apply_rule_override, fallback_score_from_flags, run_rule_engine, score_to_tier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Analysis"])


# ── Shared pipeline ────────────────────────────────────────────────────────────

async def _run_analysis_pipeline(
    text: str,
    user_id: str,
    analysis_type: str,  # "MESSAGE" | "CALL"
    db: AsyncSession,
) -> AnalysisResponse:
    # 1. Language detection
    lang_code = detect_language(text)

    # 2. Rule engine (always runs first — auditable)
    floor_score, rule_name, rule_flags = run_rule_engine(text)

    # 3. Claude analysis (with graceful fallback)
    llm_score: int = 0
    llm_flags: list[str] = []
    llm_explanation: str = ""
    claude_succeeded = False

    try:
        if analysis_type == "MESSAGE":
            result = await claude_service.analyse_message(text, lang_code, rule_flags)
        else:
            result = await claude_service.analyse_call(text, lang_code, rule_flags)

        llm_score = int(result.get("risk_score", 0))
        llm_flags = result.get("matched_red_flags", [])
        llm_explanation = result.get("explanation", "")
        claude_succeeded = True

    except Exception as exc:
        logger.error("Claude API call failed: %s — falling back to rule-engine-only", exc)
        # Rule-engine fallback explanation
        if floor_score is not None:
            llm_explanation = (
                f"[Auto-generated — AI unavailable] Rule '{rule_name}' triggered. "
                f"Input contains government agency names, urgency/threat language, and/or "
                f"money transfer demands — classic digital arrest scam pattern."
            )
        else:
            llm_explanation = "[Auto-generated — AI unavailable] No specific scam patterns detected."

    # 4. Fuse rule + LLM outputs
    final_score, final_tier, final_flags, override_fired, fired_rule = apply_rule_override(
        llm_score=llm_score,
        llm_flags=llm_flags,
        floor_score=floor_score,
        rule_name=rule_name,
        rule_flags=rule_flags,
    )

    # Fallback: if Claude failed and no rule fired but signals exist, compute partial score
    if not claude_succeeded and not override_fired and rule_flags:
        fallback = fallback_score_from_flags(rule_flags)
        if fallback > final_score:
            final_score = fallback
            final_tier = score_to_tier(final_score)

    # Derive confidence
    if not claude_succeeded:
        confidence = 0.85 if override_fired else max(0.40, final_score / 100)
    else:
        confidence = min(0.99, max(0.1, final_score / 100))

    # Determine if checklist should be triggered
    checklist_triggered = final_tier in ("HIGH", "CRITICAL")

    # 5. Persist to DB
    analysis_id = uuid.uuid4()
    db_record = ScamAnalysis(
        id=analysis_id,
        user_id=user_id,
        analysis_type=analysis_type,
        input_text=text[:2000],  # truncate for storage
        language=lang_code,
        risk_score=final_score,
        risk_tier=final_tier,
        confidence=confidence,
        matched_red_flags=final_flags,
        explanation=llm_explanation,
        rule_fired=fired_rule,
    )
    db.add(db_record)
    # Session commit handled by get_db dependency

    return AnalysisResponse(
        analysis_id=analysis_id,
        risk_score=final_score,
        risk_tier=final_tier,
        confidence=confidence,
        matched_red_flags=final_flags,
        explanation=llm_explanation,
        language=lang_code,
        rule_override_fired=override_fired,
        rule_fired_name=fired_rule,
        checklist_triggered=checklist_triggered,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post(
    "/message",
    response_model=AnalysisResponse,
    summary="Analyse a forwarded message for scam risk",
    description="Feature 1: Accepts forwarded WhatsApp/SMS text and returns risk verdict with red flags and explanation.",
)
async def analyse_message(
    body: MessageAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    return await _run_analysis_pipeline(
        text=body.text,
        user_id=body.user_id,
        analysis_type="MESSAGE",
        db=db,
    )


@router.post(
    "/call",
    response_model=AnalysisResponse,
    summary="Analyse a described phone/video call for scam risk",
    description="Feature 2: Accepts a description of a received call and returns risk verdict tuned for verbal/live-call scenarios.",
)
async def analyse_call(
    body: CallAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    return await _run_analysis_pipeline(
        text=body.description,
        user_id=body.user_id,
        analysis_type="CALL",
        db=db,
    )
