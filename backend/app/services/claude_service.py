"""
Claude API service — all Anthropic SDK calls in one place.

Covers:
  Feature 1 & 2 — Risk analysis (message + call variants)
  Feature 4     — Red flag explanation (grounded in matched flags)
  Feature 6     — Structured complaint field extraction
  Feature 5     — Bilingual support via lang_code injection

Error handling:
  If the Claude API call fails, the caller catches the exception and
  falls back to rule-layer-only scoring (see routers/analysis.py).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

from app.config import get_settings
from app.services.language import build_response_instruction

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy singleton client
_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


# ── Prompt Templates ───────────────────────────────────────────────────────────

MESSAGE_ANALYSIS_PROMPT = """You are an expert fraud analyst specialising in Indian digital-arrest scams.
Analyse the following forwarded message or text and determine if it is a scam.

{lang_instruction}

Digital arrest scams involve fraudsters impersonating government officials (CBI, ED, Customs, Income Tax,
Police, TRAI, RBI, Narcotics) threatening arrest/legal action and demanding money.

Common red flags to look for:
- Impersonation of CBI/ED/Customs/Police/TRAI/RBI/NCB
- Arrest warrants, FIR threats, court summons
- Demands for money to "clear your name" or "post bail"
- Requests for bank account details, UPI payments
- Video call demands while showing fake badges
- Instructions to keep the matter secret from family/lawyers
- Urgency/panic-inducing language
- Requests to stay on call / "digital arrest"
- Suspicious links to fake government portals
- Package seized at customs scam variant
- Money laundering accusation via Aadhaar/bank account

Pre-identified rule-based red flags already detected:
{rule_flags}

INPUT MESSAGE:
---
{input_text}
---

Return ONLY valid JSON with this exact structure (no markdown, no explanation outside JSON):
{{
  "risk_score": <integer 0-100>,
  "confidence": <float 0.0-1.0>,
  "matched_red_flags": [<list of specific red flag strings found, in the response language>],
  "explanation": "<plain language explanation in {lang_name}, 2-4 sentences, grounded in the flags above>",
  "scam_type": "<primary scam variant: digital_arrest | customs_scam | money_laundering | fake_warrant | other>"
}}"""


CALL_ANALYSIS_PROMPT = """You are an expert fraud analyst specialising in Indian digital-arrest phone/video scams.
A user is describing a phone or video call they received. Analyse the description.

{lang_instruction}

Key patterns of digital arrest calls:
- Caller claims to be CBI/ED/Customs/Police/NCB officer
- Shows a fake badge or warrant document on video call
- Claims victim's Aadhaar/bank account is linked to drug trafficking or money laundering
- Creates extreme urgency — "you will be arrested in 2 hours"
- Demands victim stay on video call ("digital arrest")
- Asks for money transfer to "clear the case"
- Instructs victim not to tell family or call lawyers
- Uses spoofed government office backgrounds
- Voice may sound robotic or have audio artifacts (deepfake voice)

Pre-identified rule-based red flags already detected:
{rule_flags}

CALL DESCRIPTION:
---
{input_text}
---

Return ONLY valid JSON with this exact structure:
{{
  "risk_score": <integer 0-100>,
  "confidence": <float 0.0-1.0>,
  "matched_red_flags": [<list of specific red flags identified, in {lang_name}>],
  "explanation": "<plain language explanation in {lang_name}, 2-4 sentences, grounded in the flags above>",
  "scam_type": "<primary variant: digital_arrest | customs_scam | money_laundering | fake_warrant | other>"
}}"""


COMPLAINT_EXTRACTION_PROMPT = """Extract structured information from the following conversation or scam description
for filing a cybercrime complaint. The user may have been a victim of a digital arrest scam.

{lang_instruction}

Extract the following fields if present (return null for missing fields):
- phone_number: the scammer's phone number (format: +91XXXXXXXXXX if Indian)
- amount: amount demanded or paid (include currency symbol, e.g. "₹25,000")
- incident_timestamp: when the incident occurred (ISO 8601 or human readable)
- description: a concise 1-2 sentence summary of what happened
- scam_type: one of [digital_arrest, customs_scam, money_laundering, fake_warrant, other]

TEXT:
---
{conversation_text}
---

Return ONLY valid JSON:
{{
  "phone_number": <string or null>,
  "amount": <string or null>,
  "incident_timestamp": <string or null>,
  "description": <string or null>,
  "scam_type": <string or null>
}}"""


# ── API Call Helpers ───────────────────────────────────────────────────────────

async def _call_claude(prompt: str, max_tokens: int = 1024) -> str:
    """Raw Claude call — returns message text content."""
    client = get_client()
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _safe_parse_json(raw: str) -> dict[str, Any]:
    """
    Parse Claude's JSON output safely.
    Strips markdown code fences if present.
    """
    # Remove ```json ... ``` fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw.strip())
    return json.loads(raw)


# ── Public Functions ───────────────────────────────────────────────────────────

async def analyse_message(
    text: str,
    lang_code: str,
    rule_flags: list[str],
) -> dict[str, Any]:
    """
    Feature 1 — Analyse a forwarded message for scam risk.
    Returns parsed dict with: risk_score, confidence, matched_red_flags, explanation, scam_type
    """
    from app.services.language import get_lang_name
    prompt = MESSAGE_ANALYSIS_PROMPT.format(
        lang_instruction=build_response_instruction(lang_code),
        lang_name=get_lang_name(lang_code),
        rule_flags=", ".join(rule_flags) if rule_flags else "none",
        input_text=text,
    )
    raw = await _call_claude(prompt)
    logger.debug("Claude message analysis raw response: %s", raw[:300])
    return _safe_parse_json(raw)


async def analyse_call(
    description: str,
    lang_code: str,
    rule_flags: list[str],
) -> dict[str, Any]:
    """
    Feature 2 — Analyse a call description for scam risk.
    Same output shape as analyse_message but uses the call-tuned prompt.
    """
    from app.services.language import get_lang_name
    prompt = CALL_ANALYSIS_PROMPT.format(
        lang_instruction=build_response_instruction(lang_code),
        lang_name=get_lang_name(lang_code),
        rule_flags=", ".join(rule_flags) if rule_flags else "none",
        input_text=description,
    )
    raw = await _call_claude(prompt)
    logger.debug("Claude call analysis raw response: %s", raw[:300])
    return _safe_parse_json(raw)


async def extract_complaint_fields(
    conversation_text: str,
    lang_code: str,
) -> dict[str, Any]:
    """
    Feature 6 — Extract NCRB complaint fields from conversation text.
    Returns partial dict; caller applies regex fallback for phone/amount.
    """
    prompt = COMPLAINT_EXTRACTION_PROMPT.format(
        lang_instruction=build_response_instruction(lang_code),
        conversation_text=conversation_text,
    )
    raw = await _call_claude(prompt, max_tokens=512)
    logger.debug("Claude complaint extraction raw response: %s", raw[:300])
    return _safe_parse_json(raw)


# ── Regex Fallbacks (Feature 6) ────────────────────────────────────────────────

PHONE_REGEX = re.compile(
    r"(?:\+91|0)?[6-9]\d{9}"  # Indian mobile numbers
)
AMOUNT_REGEX = re.compile(
    r"(?:₹|Rs\.?|INR)\s?[\d,]+(?:\.\d{1,2})?"
    r"|[\d,]+(?:\.\d{1,2})?\s?(?:rupees?|lakh|lakhs?|crore)",
    re.IGNORECASE,
)


def regex_extract_phone(text: str) -> str | None:
    match = PHONE_REGEX.search(text)
    if match:
        raw = match.group()
        # Normalise to +91XXXXXXXXXX
        digits = re.sub(r"\D", "", raw)
        if len(digits) == 10:
            return f"+91{digits}"
        if len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"
        return raw
    return None


def regex_extract_amount(text: str) -> str | None:
    match = AMOUNT_REGEX.search(text)
    return match.group().strip() if match else None
