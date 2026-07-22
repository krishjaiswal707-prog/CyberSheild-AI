"""
seed_data.py — Idempotent database seeder

Populates:
  1. ~70 known scammer entries (phone/email, report_count, scam_type)
  2. 10 sample community scam reports
  3. 5 sample scam analyses (demo user history)
  4. 1 demo user session

Safe to re-run: checks existence before inserting.

Usage:
    python seed_data.py

Requires DATABASE_URL in .env
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import os
os.environ.setdefault("DATABASE_URL", "")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func

# ── Import ORM models ──────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from app.models.orm import Base, KnownScammer, ScamReport, ScamAnalysis, UserSession
from app.config import get_settings

settings = get_settings()


# ═══════════════════════════════════════════════════════════════════════════════
# Seed data definitions
# ═══════════════════════════════════════════════════════════════════════════════

KNOWN_SCAMMERS = [
    # ── Digital Arrest / CBI / ED impersonation ─────────────────────────────────
    {"identifier": "+919876543210", "type": "phone", "count": 47, "scam": "digital_arrest", "source": "cybercrime.gov.in", "notes": "Posed as CBI officer, demanded ₹2 lakh bail money"},
    {"identifier": "+919765432101", "type": "phone", "count": 23, "scam": "digital_arrest", "source": "cybercrime.gov.in", "notes": "Conducted video call impersonating ED officer"},
    {"identifier": "+919654321012", "type": "phone", "count": 31, "scam": "digital_arrest", "source": "community", "notes": "Claims Aadhaar linked to money laundering"},
    {"identifier": "+919543210123", "type": "phone", "count": 18, "scam": "digital_arrest", "source": "cybercrime.gov.in", "notes": "Customs officer impersonation, package seizure threat"},
    {"identifier": "+919432101234", "type": "phone", "count": 12, "scam": "digital_arrest", "source": "community", "notes": "Income Tax raid threat, demands UPI transfer"},
    {"identifier": "+918765432109", "type": "phone", "count": 56, "scam": "digital_arrest", "source": "cybercrime.gov.in", "notes": "Uses WhatsApp video call, fake government office background"},
    {"identifier": "+918654321098", "type": "phone", "count": 29, "scam": "digital_arrest", "source": "sanchar_saathi", "notes": "TRAI call, threatens to disconnect number"},
    {"identifier": "+918543210987", "type": "phone", "count": 15, "scam": "digital_arrest", "source": "community", "notes": "Narcotics Bureau officer impersonation"},
    {"identifier": "+917654321098", "type": "phone", "count": 8,  "scam": "digital_arrest", "source": "community", "notes": "Interpol impersonation, international arrest warrant"},
    {"identifier": "+917543210987", "type": "phone", "count": 34, "scam": "digital_arrest", "source": "cybercrime.gov.in", "notes": "RBI officer fraud, demands KYC update via UPI"},

    # ── Customs / Package scam ─────────────────────────────────────────────────
    {"identifier": "+919988776655", "type": "phone", "count": 41, "scam": "customs_scam", "source": "cybercrime.gov.in", "notes": "Fake customs clearance, demands fee for held package"},
    {"identifier": "+919877665544", "type": "phone", "count": 19, "scam": "customs_scam", "source": "community", "notes": "FedEx customs alert scam variant"},
    {"identifier": "+919766554433", "type": "phone", "count": 27, "scam": "customs_scam", "source": "cybercrime.gov.in", "notes": "Package with drugs found in your name"},
    {"identifier": "+919655443322", "type": "phone", "count": 9,  "scam": "customs_scam", "source": "community", "notes": "DHL parcel seized, demands ₹15,000 clearance fee"},
    {"identifier": "customs.helpline@gmail.com", "type": "email", "count": 63, "scam": "customs_scam", "source": "cybercrime.gov.in", "notes": "Fake customs email with HTML form to collect payment"},

    # ── Money laundering / Bank account freeze ─────────────────────────────────
    {"identifier": "+918899776655", "type": "phone", "count": 22, "scam": "money_laundering", "source": "cybercrime.gov.in", "notes": "Bank account frozen threat, demands verification payment"},
    {"identifier": "+918788665544", "type": "phone", "count": 37, "scam": "money_laundering", "source": "community", "notes": "Aadhaar linked to laundering racket"},
    {"identifier": "+918677554433", "type": "phone", "count": 14, "scam": "money_laundering", "source": "cybercrime.gov.in", "notes": "PAN card misuse claim, demands ₹50,000"},
    {"identifier": "ed.india.official@protonmail.com", "type": "email", "count": 28, "scam": "money_laundering", "source": "cybercrime.gov.in", "notes": "Fake ED email with case number, demands compliance fee"},
    {"identifier": "+918566443322", "type": "phone", "count": 11, "scam": "money_laundering", "source": "community", "notes": "SIM card misuse claim, demands immediate transfer"},

    # ── UPI / Banking fraud ────────────────────────────────────────────────────
    {"identifier": "+917788996655", "type": "phone", "count": 89, "scam": "upi_fraud", "source": "cybercrime.gov.in", "notes": "Fake refund request, sends QR code for victim to scan"},
    {"identifier": "+917677885544", "type": "phone", "count": 45, "scam": "upi_fraud", "source": "community", "notes": "KYC update scam, collects OTP"},
    {"identifier": "+917566774433", "type": "phone", "count": 33, "scam": "upi_fraud", "source": "cybercrime.gov.in", "notes": "Loan approval fee fraud"},
    {"identifier": "sbi.alert@sbi-india.net", "type": "email", "count": 156, "scam": "upi_fraud", "source": "cybercrime.gov.in", "notes": "Fake SBI phishing email, collects internet banking credentials"},
    {"identifier": "hdfc.kyc@hdfc-bank-india.com", "type": "email", "count": 94, "scam": "upi_fraud", "source": "cybercrime.gov.in", "notes": "Fake HDFC KYC link, harvests login credentials"},

    # ── Fake government portals ────────────────────────────────────────────────
    {"identifier": "+917455663322", "type": "phone", "count": 17, "scam": "fake_warrant", "source": "community", "notes": "Sends fake arrest warrant PDF via WhatsApp"},
    {"identifier": "+917344552211", "type": "phone", "count": 25, "scam": "fake_warrant", "source": "cybercrime.gov.in", "notes": "Fake Supreme Court notice, demands bail amount"},
    {"identifier": "cbi.arrest@cbi-india.org", "type": "email", "count": 48, "scam": "fake_warrant", "source": "cybercrime.gov.in", "notes": "Fake CBI arrest notice, links to spoofed government site"},
    {"identifier": "ncrb.complaint@ncrb.net", "type": "email", "count": 31, "scam": "fake_warrant", "source": "community", "notes": "Fake NCRB complaint notice demanding clearance payment"},

    # ── Investment / Stock trading ─────────────────────────────────────────────
    {"identifier": "+916655443322", "type": "phone", "count": 72, "scam": "investment_fraud", "source": "sebi.gov.in", "notes": "Fake SEBI-registered advisor, promises 40% monthly returns"},
    {"identifier": "+916544332211", "type": "phone", "count": 38, "scam": "investment_fraud", "source": "community", "notes": "WhatsApp stock tips group, pump and dump scheme"},
    {"identifier": "+916433221100", "type": "phone", "count": 21, "scam": "investment_fraud", "source": "sebi.gov.in", "notes": "Fake NSE trading app, initial profits then frozen withdrawals"},
    {"identifier": "trading.profits@investindia-real.com", "type": "email", "count": 44, "scam": "investment_fraud", "source": "sebi.gov.in", "notes": "Fake investment platform email, collects deposits"},

    # ── Job / Recruitment ──────────────────────────────────────────────────────
    {"identifier": "+915544332211", "type": "phone", "count": 29, "scam": "job_fraud", "source": "community", "notes": "WFH data entry job, demands registration fee"},
    {"identifier": "+915433221100", "type": "phone", "count": 16, "scam": "job_fraud", "source": "cybercrime.gov.in", "notes": "Amazon/Flipkart part-time job fraud, task completion scam"},
    {"identifier": "hr@tata-group-jobs.com", "type": "email", "count": 87, "scam": "job_fraud", "source": "cybercrime.gov.in", "notes": "Fake Tata job offer, demands security deposit"},

    # ── Electricity / Utility ─────────────────────────────────────────────────
    {"identifier": "+914433221100", "type": "phone", "count": 53, "scam": "utility_fraud", "source": "community", "notes": "Electricity bill disconnection threat, BESCOM impersonation"},
    {"identifier": "+914322110099", "type": "phone", "count": 24, "scam": "utility_fraud", "source": "community", "notes": "Gas pipeline service fee, Indane impersonation"},

    # ── Lottery / Prize ───────────────────────────────────────────────────────
    {"identifier": "+913322110099", "type": "phone", "count": 35, "scam": "lottery_fraud", "source": "cybercrime.gov.in", "notes": "KBC/Amazon lottery, demands GST/tax before releasing prize"},
    {"identifier": "kbc.lottery@kbc-india-official.com", "type": "email", "count": 112, "scam": "lottery_fraud", "source": "cybercrime.gov.in", "notes": "KBC winner email, asks for fee to release ₹25 lakh prize"},

    # ── Romance / Sextortion ──────────────────────────────────────────────────
    {"identifier": "+916677889900", "type": "phone", "count": 19, "scam": "sextortion", "source": "community", "notes": "Video call honey trap, threatens to share recording"},
    {"identifier": "+916566778899", "type": "phone", "count": 11, "scam": "sextortion", "source": "community", "notes": "Instagram friendship scam, turns to blackmail"},

    # ── Tech support ──────────────────────────────────────────────────────────
    {"identifier": "+919911223344", "type": "phone", "count": 43, "scam": "tech_support", "source": "cybercrime.gov.in", "notes": "Microsoft/Google tech support, remote access via AnyDesk"},
    {"identifier": "support@windows-security.help", "type": "email", "count": 67, "scam": "tech_support", "source": "cybercrime.gov.in", "notes": "Fake virus alert email, remote access scam"},

    # ── Additional digital arrest variants ────────────────────────────────────
    {"identifier": "+919001122334", "type": "phone", "count": 62, "scam": "digital_arrest", "source": "cybercrime.gov.in", "notes": "Police commissioner impersonation, Zoom call scam"},
    {"identifier": "+919112233445", "type": "phone", "count": 28, "scam": "digital_arrest", "source": "community", "notes": "CID officer, drug parcel in victim name at airport"},
    {"identifier": "+919223344556", "type": "phone", "count": 16, "scam": "digital_arrest", "source": "cybercrime.gov.in", "notes": "Fake court summons via WhatsApp"},
    {"identifier": "+919334455667", "type": "phone", "count": 39, "scam": "digital_arrest", "source": "sanchar_saathi", "notes": "NCB officer, claims victim's number used in drug calls"},
    {"identifier": "+919445566778", "type": "phone", "count": 7,  "scam": "digital_arrest", "source": "community", "notes": "NCRP officer, demands payment to close case"},
    {"identifier": "+919556677889", "type": "phone", "count": 21, "scam": "digital_arrest", "source": "cybercrime.gov.in", "notes": "Calls from a 'Mumbai Crime Branch' number"},
    {"identifier": "+919667788990", "type": "phone", "count": 33, "scam": "digital_arrest", "source": "cybercrime.gov.in", "notes": "ED summons on video call, fake badge shown"},
    {"identifier": "+919778899001", "type": "phone", "count": 48, "scam": "digital_arrest", "source": "sanchar_saathi", "notes": "RBI money laundering charge, asks for OTP"},
    {"identifier": "+919889900112", "type": "phone", "count": 15, "scam": "digital_arrest", "source": "community", "notes": "Tax evasion notice, demands immediate payment"},
    {"identifier": "+919990011223", "type": "phone", "count": 26, "scam": "digital_arrest", "source": "cybercrime.gov.in", "notes": "Calls itself government helpline 1800-XXXXX"},

    # ── More UPI frauds ───────────────────────────────────────────────────────
    {"identifier": "+918001234567", "type": "phone", "count": 78, "scam": "upi_fraud", "source": "cybercrime.gov.in", "notes": "Paytm KYC update scam, screenshares and steals OTP"},
    {"identifier": "+918112345678", "type": "phone", "count": 31, "scam": "upi_fraud", "source": "community", "notes": "Google Pay cashback refund scam"},
    {"identifier": "paytm.kyc@paytmverify.in", "type": "email", "count": 52, "scam": "upi_fraud", "source": "cybercrime.gov.in", "notes": "Fake Paytm KYC email with phishing link"},

    # ── Student / Education fraud ─────────────────────────────────────────────
    {"identifier": "+917001122334", "type": "phone", "count": 20, "scam": "education_fraud", "source": "community", "notes": "Fake university scholarship, demands processing fee"},
    {"identifier": "+917112233445", "type": "phone", "count": 13, "scam": "education_fraud", "source": "community", "notes": "NEET/JEE paper leak scam, sells fake question papers"},
]

COMMUNITY_REPORTS = [
    {
        "user_id": "seed_user_001",
        "report_text": "A man called from +919876543210 saying he was from CBI. He showed me a badge on video call and said my Aadhaar is linked to a money laundering case. He said I will be arrested in 2 hours if I don't pay ₹1 lakh as bail money.",
        "scam_type": "digital_arrest",
        "location": "Mumbai, Maharashtra",
        "phone_number": "+919876543210",
    },
    {
        "user_id": "seed_user_002",
        "report_text": "Received WhatsApp message saying my package from Dubai is held at customs. They asked for ₹15,000 customs clearance fee. The number was +919988776655. They had a fake government website.",
        "scam_type": "customs_scam",
        "location": "Delhi",
        "phone_number": "+919988776655",
    },
    {
        "user_id": "seed_user_003",
        "report_text": "Lady called saying she is from ED (Enforcement Directorate). Said my bank account is linked to a crime ring. Kept me on video call for 3 hours. Demanded I transfer ₹2.5 lakh to clear my name. I paid ₹50,000 before my son stopped me.",
        "scam_type": "digital_arrest",
        "location": "Pune, Maharashtra",
        "phone_number": "+919765432101",
    },
    {
        "user_id": "seed_user_004",
        "report_text": "Got an email from cbi.arrest@cbi-india.org with an arrest warrant PDF attached. The warrant had my name and Aadhaar number. It asked me to pay ₹75,000 to avoid arrest. The website linked in the email looked like the real CBI website but the URL was different.",
        "scam_type": "fake_warrant",
        "location": "Bengaluru, Karnataka",
        "phone_number": None,
    },
    {
        "user_id": "seed_user_005",
        "report_text": "A person claiming to be from TRAI called and said my mobile number will be disconnected in 2 hours because it was used for illegal calls. He transferred me to a fake 'police officer' who asked for my bank account details to verify my identity.",
        "scam_type": "digital_arrest",
        "location": "Hyderabad, Telangana",
        "phone_number": "+918654321098",
    },
    {
        "user_id": "seed_user_006",
        "report_text": "I received a call saying I won KBC lottery of ₹25 lakh. They asked me to pay ₹50,000 as processing fee to release the prize. The email they sent was from kbc.lottery@kbc-india-official.com.",
        "scam_type": "lottery_fraud",
        "location": "Ahmedabad, Gujarat",
        "phone_number": "+913322110099",
    },
    {
        "user_id": "seed_user_007",
        "report_text": "Man on video call showed a Delhi Police badge and said a drug parcel with my name was caught at IGI airport. He said I need to pay ₹3 lakh as security deposit and it will be refunded after investigation. He kept saying don't tell your family.",
        "scam_type": "digital_arrest",
        "location": "Delhi",
        "phone_number": "+919112233445",
    },
    {
        "user_id": "seed_user_008",
        "report_text": "Received an SMS saying my SBI internet banking is blocked. The link in SMS went to a site that looked exactly like SBI but URL was sbi-india.net. I entered my details and immediately ₹45,000 was transferred from my account.",
        "scam_type": "upi_fraud",
        "location": "Chennai, Tamil Nadu",
        "phone_number": None,
    },
    {
        "user_id": "seed_user_009",
        "report_text": "CBI officer called on Zoom. He had a professional-looking background with CBI logo. Said my Aadhaar is used by a terrorist group. Demanded video call stay connected for 6 hours — digital arrest. Kept threatening arrest if I disconnected.",
        "scam_type": "digital_arrest",
        "location": "Kolkata, West Bengal",
        "phone_number": "+919001122334",
    },
    {
        "user_id": "seed_user_010",
        "report_text": "An Enforcement Directorate officer called and said my PAN card is linked to a ₹50 crore money laundering case. They said I need to transfer ₹2 lakh to a 'safe RBI account' for verification. They emailed a document from ed.india.official@protonmail.com",
        "scam_type": "money_laundering",
        "location": "Jaipur, Rajasthan",
        "phone_number": "+918788665544",
    },
]

DEMO_ANALYSES = [
    {
        "user_id": "demo_user_whatsapp",
        "analysis_type": "MESSAGE",
        "input_text": "Dear customer, your Aadhaar card has been linked to illegal activities. CBI has registered a case against you. You will be arrested within 2 hours. To avoid arrest, transfer ₹50,000 to the following account immediately.",
        "language": "en",
        "risk_score": 95,
        "risk_tier": "CRITICAL",
        "confidence": 0.97,
        "matched_red_flags": ["CBI_impersonation", "arrest_threat", "money_transfer_demand", "urgency_tactic", "Aadhaar_linked_crime"],
        "explanation": "This is a classic digital arrest scam. Real CBI never contacts citizens via WhatsApp or demands immediate money transfers. The urgency ('2 hours'), Aadhaar mention, and payment demand are textbook scam signals.",
        "rule_fired": "RULE_AGENCY_URGENCY_MONEY",
    },
    {
        "user_id": "demo_user_whatsapp",
        "analysis_type": "CALL",
        "input_text": "A man called saying he was from the Narcotics Control Bureau. He was on video call wearing a khaki uniform. He said a package of drugs was found at Mumbai airport with my name. He wants me to stay on video call and transfer ₹2 lakh as security deposit.",
        "language": "en",
        "risk_score": 97,
        "risk_tier": "CRITICAL",
        "confidence": 0.98,
        "matched_red_flags": ["NCB_impersonation", "video_call_demand", "package_seizure_threat", "isolation_tactic", "large_money_demand"],
        "explanation": "Definite digital arrest scam. The NCB does not conduct 'digital arrests' or ask for security deposits via phone. Uniform on video call is a well-known scammer prop. Disconnect immediately and call 1930.",
        "rule_fired": "RULE_AGENCY_URGENCY_MONEY",
    },
    {
        "user_id": "demo_user_whatsapp",
        "analysis_type": "MESSAGE",
        "input_text": "Hi! I'm selling my old iPhone 13 for ₹25,000. If interested, contact me on 9876543210.",
        "language": "en",
        "risk_score": 8,
        "risk_tier": "LOW",
        "confidence": 0.91,
        "matched_red_flags": [],
        "explanation": "This appears to be a legitimate phone sale advertisement. No government impersonation, no threats, no urgency tactics detected.",
        "rule_fired": None,
    },
    {
        "user_id": "demo_user_whatsapp",
        "analysis_type": "MESSAGE",
        "input_text": "आपके आधार कार्ड पर मनी लॉन्ड्रिंग का केस दर्ज हुआ है। ED अधिकारी आपसे वीडियो कॉल पर बात करना चाहते हैं। अभी फोन पर रहें वरना गिरफ्तारी होगी।",
        "language": "hi",
        "risk_score": 93,
        "risk_tier": "CRITICAL",
        "confidence": 0.95,
        "matched_red_flags": ["hindi_ED_impersonation", "hindi_money_laundering_claim", "hindi_arrest_threat", "video_call_demand", "urgency_tactic"],
        "explanation": "यह एक डिजिटल अरेस्ट घोटाला है। ED कभी भी WhatsApp या SMS पर संपर्क नहीं करता। गिरफ्तारी की धमकी और वीडियो कॉल की मांग इस घोटाले के सामान्य संकेत हैं। तुरंत 1930 पर कॉल करें।",
        "rule_fired": "RULE_AGENCY_URGENCY",
    },
    {
        "user_id": "demo_user_whatsapp",
        "analysis_type": "CALL",
        "input_text": "Someone from TRAI called and said my phone number is being used for illegal calls and will be disconnected. They transferred me to a 'police officer' who asked for my bank account number to verify my identity.",
        "language": "en",
        "risk_score": 88,
        "risk_tier": "CRITICAL",
        "confidence": 0.93,
        "matched_red_flags": ["TRAI_impersonation", "police_impersonation", "bank_account_demand", "multi_stage_call_routing"],
        "explanation": "Classic TRAI disconnection + police transfer scam. TRAI never calls to disconnect numbers. Transferring to a 'police officer' is a known escalation tactic. Never give bank details to unsolicited callers.",
        "rule_fired": "RULE_AGENCY_URGENCY_MONEY",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# Seeder functions
# ═══════════════════════════════════════════════════════════════════════════════

async def seed_known_scammers(session: AsyncSession) -> int:
    count = 0
    for entry in KNOWN_SCAMMERS:
        # Idempotency check: skip if identifier already exists
        result = await session.execute(
            select(KnownScammer).where(KnownScammer.identifier == entry["identifier"]).limit(1)
        )
        if result.scalar_one_or_none() is not None:
            continue

        session.add(KnownScammer(
            identifier=entry["identifier"],
            identifier_type=entry["type"],
            report_count=entry["count"],
            scam_type=entry["scam"],
            source=entry["source"],
            notes=entry["notes"],
        ))
        count += 1

    await session.commit()
    return count


async def seed_community_reports(session: AsyncSession) -> int:
    count = 0
    for i, entry in enumerate(COMMUNITY_REPORTS):
        result = await session.execute(
            select(ScamReport)
            .where(ScamReport.user_id == entry["user_id"])
            .limit(1)
        )
        if result.scalar_one_or_none() is not None:
            continue

        session.add(ScamReport(
            id=uuid.uuid4(),
            user_id=entry["user_id"],
            report_text=entry["report_text"],
            scam_type=entry["scam_type"],
            location=entry["location"],
            phone_number=entry["phone_number"],
        ))
        count += 1

    await session.commit()
    return count


async def seed_demo_analyses(session: AsyncSession) -> int:
    count = 0
    base_time = datetime.now(timezone.utc) - timedelta(days=7)

    for i, entry in enumerate(DEMO_ANALYSES):
        result = await session.execute(
            select(ScamAnalysis)
            .where(
                ScamAnalysis.user_id == entry["user_id"],
                ScamAnalysis.input_text == entry["input_text"][:100],
            )
            .limit(1)
        )
        if result.scalar_one_or_none() is not None:
            continue

        session.add(ScamAnalysis(
            id=uuid.uuid4(),
            user_id=entry["user_id"],
            analysis_type=entry["analysis_type"],
            input_text=entry["input_text"][:2000],
            language=entry["language"],
            risk_score=entry["risk_score"],
            risk_tier=entry["risk_tier"],
            confidence=entry["confidence"],
            matched_red_flags=entry["matched_red_flags"],
            explanation=entry["explanation"],
            rule_fired=entry["rule_fired"],
        ))
        count += 1

    await session.commit()
    return count


async def seed_demo_session(session: AsyncSession) -> int:
    result = await session.execute(
        select(UserSession).where(UserSession.user_id == "demo_user_whatsapp").limit(1)
    )
    if result.scalar_one_or_none() is not None:
        return 0

    session.add(UserSession(
        id=uuid.uuid4(),
        user_id="demo_user_whatsapp",
        whatsapp_number="+919999999999",
        state="idle",
    ))
    await session.commit()
    return 1


async def main() -> None:
    db_url = settings.database_url
    if not db_url or "REPLACE" in db_url or "placeholder" in db_url.lower():
        print("❌ ERROR: DATABASE_URL is not configured in .env")
        print("   Copy .env.example to .env and fill in your Supabase connection string.")
        sys.exit(1)

    print(f"🌱 Connecting to database...")
    engine = create_async_engine(db_url, echo=False)
    Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        print("🔍 Seeding known scammers...")
        n = await seed_known_scammers(session)
        print(f"   ✅ Inserted {n} scammer records (skipped existing)")

        print("🔍 Seeding community reports...")
        n = await seed_community_reports(session)
        print(f"   ✅ Inserted {n} community reports (skipped existing)")

        print("🔍 Seeding demo analysis history...")
        n = await seed_demo_analyses(session)
        print(f"   ✅ Inserted {n} demo analyses (skipped existing)")

        print("🔍 Seeding demo user session...")
        n = await seed_demo_session(session)
        print(f"   ✅ Inserted {n} demo session (skipped existing)")

    await engine.dispose()
    print("\n🎉 Seeding complete! Your database is ready for demo.")
    print("   Demo user ID: demo_user_whatsapp")
    print("   Test scammer: +919876543210")
    print("   Run the app: uvicorn app.main:app --reload")


if __name__ == "__main__":
    asyncio.run(main())
