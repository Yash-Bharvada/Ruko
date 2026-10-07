# 🚀 Ruko — Startup & Server Operations Guide

This guide provides all the exact commands and instructions required to run the **Ruko Backend (FastAPI)** and **Ruko Frontend (TanStack Start / Vite / Nitro)** servers concurrently, test all features, and manage environment configurations.

---

## 📋 Quick Start Summary

Open two separate terminal windows or tabs:

```bash
# Terminal 1 — Start Backend Server (Port 8000)
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Start Frontend Application (Port 3000)
cd frontend
npm run dev
```

- **Frontend URL**: [http://localhost:3000](http://localhost:3000)
- **Backend API & Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🛠️ Detailed Setup & Execution

### 1. Backend Setup & Run (`/backend`)

#### Prerequisites
- **Python**: 3.11, 3.12, or 3.13
- **System Binaries** (optional for local media/OCR):
  ```bash
  # macOS (Homebrew)
  brew install ffmpeg tesseract
  
  # Ubuntu/Debian
  sudo apt update && sudo apt install -y ffmpeg tesseract-ocr
  ```

#### Virtual Environment & Dependencies
```bash
cd backend

# Create virtual environment (if not already created)
python3 -m venv .venv

# Activate environment
source .venv/bin/activate

# Install strictly pinned dependencies
pip install -r requirements.txt
```

#### Starting the Backend Server
```bash
# Option A: Standard Dev Server with Hot-Reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Option B: Run with Python module syntax
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Option C: Production multi-worker setup
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Running Backend Test Suite
```bash
# Run all 186 unit, integration, and security tests
pytest tests/ -v

# Run only Breach & Vapi tests
pytest tests/test_breach.py tests/test_vapi.py -v
```

---

### 2. Frontend Setup & Run (`/frontend`)

#### Prerequisites
- **Node.js**: >= 20.0.0
- **npm**: >= 10.0.0

#### Installation & Development
```bash
cd frontend

# Install node dependencies
npm install

# Start development dev server (Vite + TanStack Router SSR)
npm run dev
```

#### Production Build & Preview
```bash
# Build production bundle (.output)
npm run build

# Preview production build locally
npx vite preview
```

---

## ⚙️ Environment Configuration (`backend/.env`)

Ensure `backend/.env` is populated with the following configuration:

```env
# Ruko Backend Environment Configuration
ENV=development
VERSION=0.1.0
CORS_ORIGINS=*

# Ingestion & Rate Limits
MAX_TEXT_CHARS=4000
MAX_IMAGE_MB=5
MAX_AUDIO_MB=10
MAX_VIDEO_MB=25
MAX_VIDEO_SECONDS=60
MAX_FRAMES=8
FRAME_INTERVAL_SECONDS=3
RATE_LIMIT_PER_MIN=30

# Feature Flags & Paths
DEMO_MODE=false
ENABLE_THIRD_PARTY_AI=true
TRANSCRIBED_NEVER_CLEAR=true
MODEL_DIR=model_store
MODEL_REQUIRED=false
HIGH_BAND=0.80
LOW_BAND=0.20

# Third-Party AI Providers
LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-flash-lite-latest
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_STT_URL=https://api.sarvam.ai/speech-to-text
SARVAM_STT_MODEL=saaras:v2
SARVAM_TTS_URL=https://api.sarvam.ai/text-to-speech
SARVAM_TTS_MODEL=bulbul:v1
SARVAM_TTS_SPEAKER=meera
MAX_TTS_CHARS=500

# Explain a Document Module Settings
EXPLAIN_ENABLED=true
EXPLAIN_MAX_MB=10
EXPLAIN_MAX_PAGES=20
EXPLAIN_MAX_CHARS=30000
EXPLAIN_LLM_TIMEOUT_S=40.0
EXPLAIN_SIGNING_KEY=ruko_signing_key_2026_sebi_audit_sec
EXPLAIN_TOKEN_TTL_S=1800

# Official Verification URL
SEBI_VERIFY_URL=https://www.sebi.gov.in

# Breach Exposure Check & Emergency Voice Alert (Twilio & Hybrid Fallback)
BREACH_PROVIDER=xposedornot
XPOSEDORNOT_API_KEY=
LEAKCHECK_API_KEY=your_leakcheck_api_key_here
HIBP_API_KEY=
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here
TWILIO_VERIFY_SERVICE_SID=your_twilio_verify_service_sid_here
VOICE_ALERTS_ENABLED=true
BREACH_ALERT_SIMULATE=true
BREACH_QUIET_START=21
BREACH_QUIET_END=8
BREACH_SIGNING_KEY=ruko_breach_signing_key_2026_sec

# Vapi AI Voice Agent Configuration
VAPI_API_KEY=your_vapi_private_api_key_here
VAPI_PUBLIC_KEY=your_vapi_public_key_here
VAPI_ASSISTANT_ID=your_vapi_assistant_id_here
VAPI_PHONE_NUMBER_ID=
VAPI_SIMULATE=true
```

---

## 🛡️ Zero-Credit Safety & Graceful Fallback Architecture

All external integrations prioritize live APIs, but seamlessly fall back to realistic, structured local responses in the event of credit exhaustion, rate limits, or network timeouts:

1. **Data Breach Monitor**:
   - Primary: `XposedOrNot` (100% Free Open-Source API)
   - Secondary: `HybridBreachProvider` (LeakCheck)
   - Tertiary: `MockProvider` (synthetic breach data)
2. **Vapi AI Multilingual Calling Agent**:
   - `VAPI_SIMULATE=true`: Injects real dynamic breach context variables into the multilingual Cyber Shield assistant prompt without consuming paid live telephony credits.
3. **Emergency Voice Alert**:
   - Respects regulatory quiet hours (21:00 to 08:00 IST) for background jobs, but allows instant developer test calls when triggered manually from the UI (`is_test_call=true`).
4. **Document Explainer & Storyboard**:
   - If external LLM is offline or out of quota, falls back to deterministic AST/regex rule parsing for key points, flowcharts, timelines, and signed scene tokens.
5. **Speech Synthesis**:
   - If Sarvam API is unreachable, falls back to in-browser Web Speech API (`browser_speech`) with complete multilingual scripts (EN, HI, GU).

---

## 🧪 Smoke Test Curl Commands

Run these commands in your terminal to verify live backend health:

```bash
# 1. Health Check
curl -s http://127.0.0.1:8000/health

# 2. Scam Detection Check
curl -s -X POST http://127.0.0.1:8000/v1/check \
  -H "Content-Type: application/json" \
  -d '{"text": "Guaranteed 20% daily profit on WhatsApp group!", "language": "en"}'

# 3. Data Breach Search
curl -s -X POST http://127.0.0.1:8000/v1/breach/check \
  -H "Content-Type: application/json" \
  -d '{"email": "clean_investor@ruko.in", "consent": true}'

# 4. Vapi Session Initialization
curl -s -X POST http://127.0.0.1:8000/v1/vapi/session \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "total_breaches": 2, "high_risk_count": 1, "financial_exposed": true, "breach_names": ["FinPay"], "exposure_categories": ["Credit cards"]}'

# 5. Emergency Cooling-Off Pause Plan
curl -s -X POST http://127.0.0.1:8000/v1/pause/plan \
  -H "Content-Type: application/json" \
  -d '{"verdict": "strong_red_flags", "language": "en"}'
```
