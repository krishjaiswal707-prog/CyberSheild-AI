"""
Pydantic v2 request/response schemas for all endpoints.
All API shapes are defined here — import from this module in routers.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# Shared / Base
# ═══════════════════════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    timestamp: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 1 & 2 — Risk Analysis
# ═══════════════════════════════════════════════════════════════════════════════

class MessageAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Forwarded message or call description text")
    user_id: str = Field(default="anonymous", max_length=100)

    model_config = {"json_schema_extra": {"example": {"text": "CBI officer here. You have a case registered against you. Pay ₹50,000 immediately or face arrest.", "user_id": "user_abc123"}}}


class CallAnalysisRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=5000, description="Description of the call you received")
    user_id: str = Field(default="anonymous", max_length=100)

    model_config = {"json_schema_extra": {"example": {"description": "A man claiming to be from Customs called me on video call. He showed a fake badge and said my Aadhaar is linked to drug trafficking.", "user_id": "user_abc123"}}}


class AnalysisResponse(BaseModel):
    analysis_id: uuid.UUID
    risk_score: int = Field(..., ge=0, le=100, description="0 = no risk, 100 = definite scam")
    risk_tier: str = Field(..., description="LOW | MEDIUM | HIGH | CRITICAL")
    confidence: float = Field(..., ge=0.0, le=1.0)
    matched_red_flags: list[str]
    explanation: str
    language: str = Field(..., description="Detected language code, e.g. 'en' or 'hi'")
    rule_override_fired: bool = Field(False, description="True if the rule-based layer overrode the LLM score")
    rule_fired_name: str | None = None
    checklist_triggered: bool = Field(False, description="True if risk tier is HIGH/CRITICAL — frontend should show safety checklist")


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 6 — NCRB Complaint Auto-fill
# ═══════════════════════════════════════════════════════════════════════════════

class ComplaintExtractRequest(BaseModel):
    conversation_text: str = Field(..., min_length=1, max_length=10000)
    user_id: str = Field(default="anonymous", max_length=100)

    model_config = {"json_schema_extra": {"example": {"conversation_text": "I received a call from +919876543210. They asked me to transfer ₹25000 on 15 July 2025. They claimed to be from ED.", "user_id": "user_abc123"}}}


class ComplaintDraft(BaseModel):
    complaint_id: uuid.UUID
    user_id: str
    phone_number: str | None
    amount: str | None
    incident_timestamp: str | None
    description: str | None
    scam_type: str | None
    created_at: datetime


class ComplaintSubmitResponse(BaseModel):
    reference_number: str
    message: str
    # MVP-DEPTH: real NCRB API submission — https://cybercrime.gov.in/ integration
    note: str = "This is a mock submission. Real NCRB API integration is planned for production."


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 7 — Known Scammer Database
# ═══════════════════════════════════════════════════════════════════════════════

class ScammerLookupRequest(BaseModel):
    identifier: str = Field(..., description="Phone number (e.g. +919876543210) or email address")

    model_config = {"json_schema_extra": {"example": {"identifier": "+919876543210"}}}


class ScammerRecord(BaseModel):
    identifier: str
    identifier_type: str
    report_count: int
    scam_type: str
    source: str | None
    last_reported: datetime
    notes: str | None


class ScammerLookupResponse(BaseModel):
    found: bool
    record: ScammerRecord | None = None
    message: str


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 8 — Personal Scam History
# ═══════════════════════════════════════════════════════════════════════════════

class HistoryItem(BaseModel):
    analysis_id: uuid.UUID
    analysis_type: str
    risk_score: int
    risk_tier: str
    matched_red_flags: list[str]
    language: str
    created_at: datetime


class HistoryResponse(BaseModel):
    user_id: str
    total_analyses: int
    history: list[HistoryItem]


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 9 — Deepfake / Voice Spoofing Check
# ═══════════════════════════════════════════════════════════════════════════════

class DeepfakeVerdict(BaseModel):
    likely_deepfake: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    media_type: str  # "video" | "audio"
    notes: str
    heuristics_used: list[str]
    # MVP-DEPTH: production would use a dedicated deepfake detection model
    # (e.g. FaceForensics++, Wav2Vec2-based audio anomaly detection)


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 10 — Community Reporting & Clustering
# ═══════════════════════════════════════════════════════════════════════════════

class ScamReportRequest(BaseModel):
    report_text: str = Field(..., min_length=10, max_length=3000)
    user_id: str = Field(default="anonymous", max_length=100)
    scam_type: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=200)
    phone_number: str | None = Field(None, max_length=20)

    model_config = {"json_schema_extra": {"example": {"report_text": "Got a WhatsApp call from someone claiming to be CBI officer. Showed a fake arrest warrant on video.", "user_id": "user_abc123", "scam_type": "digital_arrest", "location": "Mumbai", "phone_number": "+919876543210"}}}


class ScamReportResponse(BaseModel):
    report_id: uuid.UUID
    message: str
    similar_reports_found: int
    cluster_id: int | None


class ClusterSummary(BaseModel):
    cluster_id: int
    report_count: int
    representative_text: str
    common_scam_type: str | None


class ClusteringResponse(BaseModel):
    total_reports_analyzed: int
    clusters_found: int
    clusters: list[ClusterSummary]


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 11 — Verification Hotline Lookup
# ═══════════════════════════════════════════════════════════════════════════════

class HotlineEntry(BaseModel):
    organization: str
    number: str
    type: str  # "tollfree" | "helpline" | "whatsapp"
    available: str  # "24x7" | "9am-6pm" etc.
    notes: str | None


class HotlineLookupResponse(BaseModel):
    query: str
    results: list[HotlineEntry]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 12 — Post-Scam Safety Checklist
# ═══════════════════════════════════════════════════════════════════════════════

class ChecklistItem(BaseModel):
    step: int
    action: str
    urgency: str  # "IMMEDIATE" | "WITHIN_24H" | "WITHIN_WEEK"
    contact: str | None  # e.g. phone number or URL
    description: str


class SafetyChecklistResponse(BaseModel):
    trigger: str  # why checklist was triggered
    total_steps: int
    checklist: list[ChecklistItem]


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 13 — Analytics & Trends
# ═══════════════════════════════════════════════════════════════════════════════

class RiskDistribution(BaseModel):
    LOW: int = 0
    MEDIUM: int = 0
    HIGH: int = 0
    CRITICAL: int = 0


class TrendAnalyticsResponse(BaseModel):
    total_analyses: int
    total_community_reports: int
    risk_distribution: RiskDistribution
    top_scam_types: list[dict[str, Any]]
    top_red_flags: list[dict[str, Any]]
    daily_volume: list[dict[str, Any]]  # [{date: "2025-07-15", count: 42}, ...]
    language_breakdown: dict[str, int]


# ═══════════════════════════════════════════════════════════════════════════════
# WhatsApp Webhook
# ═══════════════════════════════════════════════════════════════════════════════

class WhatsAppWebhookResponse(BaseModel):
    message_sent: bool
    response_text: str
