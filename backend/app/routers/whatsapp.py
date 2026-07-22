"""
Twilio WhatsApp Webhook Handler

POST /api/v1/whatsapp/webhook — receives inbound WhatsApp messages from Twilio sandbox

Message routing:
  - "hi" / "hello" / "शुरू" → welcome + instructions
  - "/check <text>"          → message risk analysis
  - "/call <text>"           → call description analysis
  - "/lookup <number>"       → scammer DB lookup
  - "/checklist"             → safety checklist (short version)
  - "/hotline"               → hotline numbers
  - "/history"               → show last 3 analyses
  - anything else            → treat as a forwarded message and analyse it

The session is tracked via the sender's WhatsApp number (user_id).

MVP-DEPTH: Production would add:
  - Twilio webhook signature verification (X-Twilio-Signature header)
  - State machine for multi-turn conversations (complaint filing flow)
  - Media message handling (images, documents)
  - Opt-in/out management
  - Rate limiting per sender
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import PlainTextResponse

from app.database import AsyncSessionLocal
from app.models.orm import ScamAnalysis, ScamReport
from app.routers.analysis import _run_analysis_pipeline
from app.routers.scammer_db import _normalise_identifier
from app.services.rule_engine import run_rule_engine
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Webhook"])

WELCOME_MESSAGE = """🛡️ *Digital Arrest Scam Detector*

Send me any suspicious message or describe a suspicious call — I'll analyse it instantly!

*Commands:*
• Just paste the message → Auto-analyse
• `/call <description>` → Analyse a call
• `/lookup +91XXXXXXXXXX` → Check scammer database  
• `/checklist` → Post-scam safety steps
• `/hotline` → Verified fraud helplines
• `/history` → Your last analyses

Powered by AI + Rule Engine 🤖
National Cybercrime Helpline: *1930*"""

RISK_EMOJIS = {
    "LOW": "✅",
    "MEDIUM": "⚠️",
    "HIGH": "🔴",
    "CRITICAL": "🚨",
}


def _format_analysis_for_whatsapp(result) -> str:
    emoji = RISK_EMOJIS.get(result.risk_tier, "❓")
    flags_text = "\n".join(f"  • {f}" for f in result.matched_red_flags[:5]) or "  None detected"
    rule_note = f"\n🔒 *Rule override:* {result.rule_fired_name}" if result.rule_override_fired else ""

    msg = (
        f"{emoji} *Risk Level: {result.risk_tier}* ({result.risk_score}/100)\n\n"
        f"📋 *Red Flags Found:*\n{flags_text}\n\n"
        f"📝 *Explanation:*\n{result.explanation[:300]}"
        f"{rule_note}"
    )
    if result.checklist_triggered:
        msg += "\n\n⚡ Reply */checklist* for immediate safety steps!"
    return msg


async def _handle_message(body: str, sender: str) -> str:
    """Route inbound message and return reply text."""
    text = body.strip()
    lower = text.lower()
    user_id = sender.replace("whatsapp:", "").replace("+", "")

    # Welcome
    if lower in ("hi", "hello", "hey", "start", "शुरू", "नमस्ते", "help", "/help"):
        return WELCOME_MESSAGE

    # Safety checklist
    if lower in ("/checklist", "checklist"):
        import json
        from pathlib import Path
        data = json.loads((Path(__file__).parent.parent / "data" / "checklist.json").read_text())
        top5 = data["checklist"][:5]
        steps = "\n".join(f"{s['step']}. *{s['action']}*" for s in top5)
        return f"🚨 *Post-Scam Safety Steps* (Top 5 of 15):\n\n{steps}\n\nReply to this bot or visit cybercrime.gov.in"

    # Hotlines
    if lower in ("/hotline", "hotline", "helpline"):
        import json
        from pathlib import Path
        data = json.loads((Path(__file__).parent.parent / "data" / "hotlines.json").read_text())
        top4 = data["hotlines"][:4]
        lines = "\n".join(f"• *{h['organization']}*: {h['number']}" for h in top4)
        return f"📞 *Verified Fraud Helplines:*\n\n{lines}\n\n🔴 *Cybercrime Helpline: 1930* (24x7)"

    # Scammer lookup
    if lower.startswith("/lookup "):
        identifier = text[8:].strip()
        async with AsyncSessionLocal() as db:
            from app.models.orm import KnownScammer
            from sqlalchemy import func, or_
            norm = _normalise_identifier(identifier)
            res = await db.execute(
                select(KnownScammer).where(
                    or_(
                        func.lower(KnownScammer.identifier) == norm,
                        func.lower(KnownScammer.identifier) == identifier.lower().strip(),
                    )
                ).limit(1)
            )
            record = res.scalar_one_or_none()
        if record:
            return (
                f"⚠️ *SCAMMER FOUND*\n"
                f"Number: {record.identifier}\n"
                f"Scam Type: {record.scam_type}\n"
                f"Reports: {record.report_count}\n"
                f"Source: {record.source or 'community'}"
            )
        return f"✅ '{identifier}' not found in known scammer database. Stay cautious anyway."

    # History
    if lower in ("/history", "history"):
        async with AsyncSessionLocal() as db:
            res = await db.execute(
                select(ScamAnalysis)
                .where(ScamAnalysis.user_id == user_id)
                .order_by(ScamAnalysis.created_at.desc())
                .limit(3)
            )
            records = res.scalars().all()
        if not records:
            return "No analysis history found for your number."
        lines = []
        for r in records:
            emoji = RISK_EMOJIS.get(r.risk_tier, "❓")
            lines.append(f"{emoji} {r.risk_tier} ({r.risk_score}/100) — {r.created_at.strftime('%d %b %H:%M') if r.created_at else 'N/A'}")
        return "📊 *Your Recent Analyses:*\n" + "\n".join(lines)

    # Call analysis
    if lower.startswith("/call "):
        description = text[6:].strip()
        async with AsyncSessionLocal() as db:
            result = await _run_analysis_pipeline(
                text=description, user_id=user_id, analysis_type="CALL", db=db
            )
        return _format_analysis_for_whatsapp(result)

    # Default: treat entire message as forwarded text for analysis
    async with AsyncSessionLocal() as db:
        result = await _run_analysis_pipeline(
            text=text, user_id=user_id, analysis_type="MESSAGE", db=db
        )
    return _format_analysis_for_whatsapp(result)


@router.post(
    "/webhook",
    response_class=PlainTextResponse,
    summary="Twilio WhatsApp inbound webhook",
    description="Receives Twilio WhatsApp messages and responds with scam analysis or commands.",
)
async def whatsapp_webhook(
    request: Request,
    Body: Annotated[str, Form()] = "",
    From: Annotated[str, Form()] = "whatsapp:+910000000000",
    To: Annotated[str, Form()] = "",
) -> PlainTextResponse:
    logger.info("WhatsApp inbound from %s: %.80s", From, Body)

    try:
        reply_text = await _handle_message(Body, From)
    except Exception as exc:
        logger.exception("Error handling WhatsApp message: %s", exc)
        reply_text = (
            "⚠️ An error occurred processing your message. "
            "If you've been scammed, call *1930* immediately."
        )

    # Return TwiML XML response
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply_text}</Message>
</Response>"""

    return PlainTextResponse(content=twiml, media_type="text/xml")
