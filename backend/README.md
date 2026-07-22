# 🛡️ Digital Arrest Scam Detector — Backend

> WhatsApp-based AI system to detect Indian "Digital Arrest" scams in real-time.
> Built for the Indian Digital Public Safety Hackathon.

---

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Create & activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env — fill in DATABASE_URL and ANTHROPIC_API_KEY

# 4. Run database migration
alembic upgrade head

# 5. Seed the database
python seed_data.py

# 7. Start the backend server (automatically serves compiled React UI on http://localhost:8000)
uvicorn app.main:app --reload --port 8000

# 8. (Optional) Run React frontend in dev mode on http://localhost:3000
cd frontend
npm run dev
```

Open **http://localhost:8000** (or **http://localhost:3000**) for the React web app!
Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## 📁 Project Structure

```
app/
├── main.py              # FastAPI app, CORS, router registration
├── config.py            # Settings via pydantic-settings + dotenv
├── database.py          # SQLAlchemy async engine + session factory
├── models/
│   ├── orm.py           # SQLAlchemy ORM table definitions (5 tables)
│   └── schemas.py       # Pydantic v2 request/response models (all endpoints)
├── routers/
│   ├── analysis.py      # Features 1 & 2: message + call risk analysis
│   ├── complaint.py     # Feature 6: NCRB complaint auto-fill
│   ├── scammer_db.py    # Feature 7: known scammer database lookup
│   ├── history.py       # Feature 8: personal scam history
│   ├── deepfake.py      # Feature 9: video/audio deepfake check
│   ├── community.py     # Feature 10: community reporting + clustering
│   ├── hotline.py       # Feature 11: verification hotline lookup
│   ├── checklist.py     # Feature 12: post-scam safety checklist
│   ├── analytics.py     # Feature 13: analytics + trend dashboard
│   └── whatsapp.py      # Twilio WhatsApp webhook handler
├── services/
│   ├── claude_service.py      # Anthropic SDK (analysis + extraction prompts)
│   ├── rule_engine.py         # Feature 3: pre-LLM rule-based override
│   ├── language.py            # Feature 5: langdetect + bilingual prompts
│   ├── clustering.py          # Feature 10: TF-IDF + cosine similarity
│   └── deepfake_heuristic.py  # Feature 9: OpenCV + librosa heuristics
└── data/
    ├── hotlines.json    # 18 verified Indian fraud helplines (static)
    └── checklist.json   # 15-step post-scam safety checklist (static)

alembic/
└── versions/001_initial.py   # Single migration — all tables

seed_data.py     # Idempotent DB seeder (70 scammers, demo history)
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Supabase Postgres (pooler/transaction mode) connection string |
| `ANTHROPIC_API_KEY` | Claude API key from console.anthropic.com |
| `TWILIO_ACCOUNT_SID` | From twilio.com/console |
| `TWILIO_AUTH_TOKEN` | From twilio.com/console |
| `CLAUDE_MODEL` | Default: `claude-sonnet-4-5` |
| `ALLOWED_ORIGINS` | Comma-separated frontend origins, e.g. `http://localhost:3000` |

**Supabase URL format:**
```
postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

---

## 🔌 Features & Endpoints

### Feature 1 — Message Risk Analysis
`POST /api/v1/analysis/message`

Analyses forwarded WhatsApp/SMS text. Returns risk score, tier, matched red flags, and bilingual explanation.

**Pipeline:** Language detect → Rule engine → Claude → Fusion → DB store

### Feature 2 — Call Description Analysis
`POST /api/v1/analysis/call`

Same output shape as Feature 1 but uses a call-tuned prompt optimised for verbal/video call scenarios (CBI/ED impersonation, isolation tactics, video call demands).

### Feature 3 — Rule-Based Override Layer *(inside analysis pipeline)*
Before every Claude call, a deterministic rule engine checks for:
- Government agency names (CBI, ED, Customs, TRAI, RBI, NCB, Interpol…)
- Urgency/threat keywords (arrest, warrant, FIR, jail, "last warning"…)
- Money/action demands (UPI, bank account, "transfer ₹"…)
- Isolation tactics ("don't tell family", "stay on call"…)
- Hindi equivalents of all the above

If 2+ categories match, the risk score is **floored at ≥75** regardless of LLM output. Every rule that fires is logged by name.

### Feature 4 — Red Flag Explanation
Grounded in `matched_red_flags`: all flags are injected into the Claude prompt so explanations reference specific detected signals.

### Feature 5 — Bilingual Support
`langdetect` identifies Hindi (hi) vs English (en). The detected `lang_code` is injected into every Claude prompt. Adding a new language requires only one entry in `SUPPORTED_LANGUAGES` dict in `language.py`.

### Feature 6 — NCRB Complaint Auto-fill
- `POST /api/v1/complaint/extract` — Claude + regex extraction
- `POST /api/v1/complaint/submit/{id}` — **mocked** submission
- `GET /api/v1/complaint/list/{user_id}` — list drafts

### Feature 7 — Known Scammer Database
`GET /api/v1/scammer/lookup?identifier=+919876543210`

Looks up phone or email against 70+ seeded scammer records.

### Feature 8 — Personal Scam History
- `GET /api/v1/history/{user_id}` — full history
- `GET /api/v1/history/{user_id}/summary` — quick stats

### Feature 9 — Deepfake / Voice Spoofing Check
`POST /api/v1/deepfake/check` (multipart file upload)

Heuristic analysis — no trained model required:
- **Video:** OpenCV frame motion variance, brightness uniformity, sharpness (Laplacian)
- **Audio:** librosa spectral flatness, zero-crossing rate, spectral rolloff

### Feature 10 — Community Reporting & Clustering
- `POST /api/v1/community/report` — submit report (returns similar_reports_found count)
- `GET /api/v1/community/clusters` — TF-IDF + cosine similarity clustering
- `GET /api/v1/community/reports` — list recent reports

### Feature 11 — Verification Hotline Lookup
- `GET /api/v1/hotline/all` — all 18 verified helplines
- `GET /api/v1/hotline/lookup?q=CBI` — partial name search

### Feature 12 — Post-Scam Safety Checklist
`GET /api/v1/checklist?risk_tier=CRITICAL`

Returns a 15-step ordered checklist. **Fully static — not LLM-generated.** Always deterministic.

### Feature 13 — Analytics & Trends
`GET /api/v1/analytics/trends`

Returns: risk distribution, top scam types, top red flags, daily volume (30 days), language breakdown.

### WhatsApp Webhook
`POST /api/v1/whatsapp/webhook` (Twilio TwiML)

Commands: just paste a message → auto-analyse, `/call`, `/lookup`, `/checklist`, `/hotline`, `/history`

---

## 🗺️ MVP-DEPTH Roadmap (Pitch Deck "Coming Soon")

| Feature | Current (MVP) | Production Upgrade |
|---|---|---|
| NCRB submission | Mock reference number | Real cybercrime.gov.in API (MHA integration) |
| Deepfake detection | OpenCV + librosa heuristics | FaceForensics++, Wav2Vec2-based model |
| Scammer DB | 70 seeded rows | I4C live API + Sanchar Saathi blacklist |
| Clustering | Single-pass TF-IDF threshold | DBSCAN / hierarchical, incremental updates |
| Languages | en + hi | mr, te, ta, bn, gu, kn (prompt already parameterised) |
| WhatsApp sessions | Stateless with user_id | Full multi-turn state machine for complaint filing |
| Analytics | SQL aggregates | Real-time WebSocket + geographic heatmap |
| Twilio auth | No signature verification | X-Twilio-Signature HMAC validation |
| Rate limiting | None | Per-number rate limits, abuse detection |
| Real-time alerts | None | Spike detection → push notifications to authorities |

---

## 📞 WhatsApp Bot Setup (Twilio Sandbox)

1. Go to [Twilio Console → Messaging → WhatsApp Sandbox](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn)
2. Set the sandbox webhook URL to: `https://your-ngrok-url.io/api/v1/whatsapp/webhook`
3. Use ngrok for local testing: `ngrok http 8000`
4. Send `join <sandbox-code>` from your WhatsApp to the Twilio number

---

## 🧪 curl Examples

### Health Check
```bash
curl http://localhost:8000/health
```

### Feature 1 — Analyse a Message
```bash
curl -X POST http://localhost:8000/api/v1/analysis/message \
  -H "Content-Type: application/json" \
  -d '{
    "text": "CBI officer speaking. Your Aadhaar is linked to money laundering. Transfer Rs 50000 immediately to avoid arrest.",
    "user_id": "test_user_001"
  }'
```

### Feature 2 — Analyse a Call Description
```bash
curl -X POST http://localhost:8000/api/v1/analysis/call \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A man on video call showed a CBI badge and said my bank account is linked to a drug trafficking case. He demanded Rs 2 lakh bail and said to stay on call or face arrest.",
    "user_id": "test_user_001"
  }'
```

### Feature 6 — Extract NCRB Complaint Fields
```bash
curl -X POST http://localhost:8000/api/v1/complaint/extract \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_text": "Received call from +919876543210 on 15 July 2025. They asked me to transfer Rs 25000 via UPI claiming to be from ED. I paid before realising it was a scam.",
    "user_id": "test_user_001"
  }'
```

### Feature 6 — Submit Complaint (Mock)
```bash
curl -X POST http://localhost:8000/api/v1/complaint/submit/YOUR-COMPLAINT-UUID
```

### Feature 7 — Scammer Lookup
```bash
curl "http://localhost:8000/api/v1/scammer/lookup?identifier=%2B919876543210"
```

### Feature 8 — Personal History
```bash
curl "http://localhost:8000/api/v1/history/demo_user_whatsapp"
curl "http://localhost:8000/api/v1/history/demo_user_whatsapp/summary"
```

### Feature 9 — Deepfake Check (video)
```bash
curl -X POST http://localhost:8000/api/v1/deepfake/check \
  -F "file=@/path/to/suspicious_call.mp4"
```

### Feature 9 — Deepfake Check (audio)
```bash
curl -X POST http://localhost:8000/api/v1/deepfake/check \
  -F "file=@/path/to/voice_recording.wav"
```

### Feature 10 — Submit Community Report
```bash
curl -X POST http://localhost:8000/api/v1/community/report \
  -H "Content-Type: application/json" \
  -d '{
    "report_text": "Man called from +919876543210 claiming to be from CBI. Demanded Rs 1 lakh via UPI to avoid arrest.",
    "user_id": "test_user_002",
    "scam_type": "digital_arrest",
    "location": "Mumbai",
    "phone_number": "+919876543210"
  }'
```

### Feature 10 — Get Clusters
```bash
curl "http://localhost:8000/api/v1/community/clusters?limit=100"
```

### Feature 11 — Hotline Lookup
```bash
curl "http://localhost:8000/api/v1/hotline/lookup?q=CBI"
curl "http://localhost:8000/api/v1/hotline/all"
```

### Feature 12 — Safety Checklist
```bash
curl "http://localhost:8000/api/v1/checklist?risk_tier=CRITICAL"
curl "http://localhost:8000/api/v1/checklist?already_paid=true"
```

### Feature 13 — Analytics Trends
```bash
curl "http://localhost:8000/api/v1/analytics/trends"
```

### WhatsApp Webhook (simulate Twilio)
```bash
curl -X POST http://localhost:8000/api/v1/whatsapp/webhook \
  -d "Body=CBI%20officer%20here.%20Your%20account%20is%20frozen.%20Pay%20Rs50000%20now.&From=whatsapp%3A%2B919999999999&To=whatsapp%3A%2B14155238886"
```

---

## 🗄️ Database Schema

| Table | Purpose |
|---|---|
| `scam_analyses` | All analysis results (feeds history + analytics) |
| `ncrb_complaints` | Draft complaint fields extracted from conversations |
| `known_scammers` | Seeded scammer phone/email blacklist |
| `scam_reports` | Community reports (used for clustering) |
| `user_sessions` | WhatsApp session state per user |

---

## 🔒 Security Notes

- Never commit `.env` — add it to `.gitignore`
- Twilio webhook signature verification should be added before production (see `routers/whatsapp.py` MVP-DEPTH comment)
- The `SECRET_KEY` env var is reserved for future JWT auth
- All Claude prompts are server-side — no prompt injection surface from frontend

---

## 👥 Team

Backend: FastAPI + Claude + PostgreSQL
Frontend: React (separate repo)

**Hackathon:** Indian Digital Public Safety Hackathon 2025
