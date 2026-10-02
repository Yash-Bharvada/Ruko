# Ruko Backend — Investor Protection Engine

Ruko is an explainable, multilingual investor-protection backend designed for the SANGYAN Hackathon (SEBI / NSDL). It inspects suspicious investment tips forwarded by retail investors across Gujarati, Hindi, and English (including Romanized script) **before** payments or commitments move.

---

## 1. Key Invariants & Hackathon Guardrails

1. **Strictly Non-Advisory**: NEVER outputs stock recommendations, buy/sell/hold calls, or target price forecasts. Queries asking for investment advice are safely intercepted and redirected to `out_of_scope`.
2. **Zero Commercial Bias**: Zero monetisation, referral schemes, upsells, broker promotions, or affiliate links.
3. **Privacy by Design**: Zero persistence of user message text, uploaded images, or voice notes. Ingestion is strictly in-memory. Server logs record only metadata (`request_id`, `endpoint`, `verdict`, `language`, `latency_ms`, `degraded`). Request bodies and PII are NEVER logged.
4. **Honest Uncertainty**: Local SEBI registry data is treated as a dated snapshot. Unconfirmed registration numbers trigger `registry_not_confirmed` ("could not confirm in our snapshot"), never "fake".
5. **Prompt-Injection Defense**: User messages are treated as UNTRUSTED DATA enclosed in strict boundaries. LLMs (when enabled) perform structured entity extraction only; they never determine the scam verdict.

---

## 2. Architecture & Module Pipeline

| Module | Subsystem | Responsibility |
|---|---|---|
| **M0** | Core & Scaffold | FastAPI factory, standard error handlers, rate limiting (30 req/min), structured JSON logging |
| **M1** | Model Adapter | Scikit-learn scam classifier adapter with fallback `DummyScorer` and top word risk explanation |
| **M2** | Rule Engine | Deterministic regex engine evaluating 12 red-flag patterns with exact substring quotes |
| **M3** | Registry Verifier | RapidFuzz fuzzy matcher & regex validator querying dated offline SEBI snapshot |
| **M4** | Claim Extractor | Vision/LLM structured entity extractor with prompt-injection boundaries and regex fallback |
| **M5** | Ingest (OCR & STT) | Magic-byte sniffed in-memory image OCR (Gemini Vision) and Indic voice STT (Sarvam AI) |
| **M6** | Verdict Engine | Deterministic decision table combining rules, ML, and registry into explainable verdicts |
| **M7** | Voice Output | Templated safe text-to-speech synthesis via Sarvam AI with Web Speech API browser fallback |
| **M8** | Pause Layer | 24-hour cooling-off decision plan, loss arithmetic vs living costs, RFC 5545 `.ics` & WhatsApp share |
| **M9** | Guardrails & API | Full concurrent orchestrator (`POST /v1/check`), advice filter, and privacy disclosure (`/v1/privacy`) |
| **M10** | Hardening & Eval | Evaluation benchmark suite, 10 curated demo cases, smoke test script, and Dockerfile |

---

## 3. Quickstart & Local Setup

### 3.1 Prerequisites
- Python 3.10 or 3.11
- Git

### 3.2 Installation
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install locked dependencies
pip install -r requirements.txt
```

### 3.3 Configuration
Copy the sample environment file:
```bash
cp .env.example .env
```

Key environment options in `.env`:
```ini
ENV=development
PORT=8000
RATE_LIMIT_PER_MIN=30
DEMO_MODE=false
ENABLE_THIRD_PARTY_AI=true
LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_key_here
SARVAM_API_KEY=your_sarvam_key_here
```

### 3.4 Start the Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
- Liveness Check: `http://localhost:8000/health`
- Interactive API Docs: `http://localhost:8000/docs`
- OpenAPI JSON Spec: `http://localhost:8000/openapi.json`

---

## 4. Verification & Testing

### 4.1 Run Test Suite with Coverage
```bash
python -m pytest --cov=app tests/
```
Runs 113+ automated tests validating all modules, security middlewares, and error handlers with ~86% statement coverage.

### 4.2 Run the Evaluation Benchmark Pipeline
```bash
python scripts/eval_pipeline.py
```
Executes the evaluation benchmark across multi-lingual scam cases, genuine bank alerts, and stock tip queries, generating `reports/eval.md`.
- **Target Scam Recall**: ≥ 90.0% (Achieved: 100.0%)
- **Target False Positive Rate**: 0.0% (Achieved: 0.0%)
- **Target Advice Interception**: 100.0% (Achieved: 100.0%)
- **Mean Latency**: < 10ms on local CPU

### 4.3 Run the Demo Smoke Test
```bash
python scripts/demo_smoke.py
```
Executes all 10 curated demo cases from `data/demo_cases.json` and prints a real-time presentation report to the console.

### 4.4 Export OpenAPI Specification
```bash
python scripts/export_openapi.py
```
Exports `openapi.json` to `backend/openapi.json` and the repository root.

---

## 5. Docker Deployment

Build and run using the production container:

```bash
# Build Docker image
docker build -t ruko-backend:latest .

# Run container as non-root user on port 8000
docker run -p 8000:8000 --env-file .env ruko-backend:latest
```

The Docker container runs with:
- Non-root user `appuser` (UID 1000)
- Automatic Docker healthcheck probing `/health` every 30 seconds
- Minimal attack surface (`python:3.11-slim`)

---

## 6. API Endpoints Overview

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check and internal module availability map |
| `POST` | `/v1/check` | Analyze suspicious message text (JSON payload) |
| `POST` | `/v1/check/image` | Ingest screenshot photo (Multipart OCR -> CheckResult) |
| `POST` | `/v1/check/audio` | Ingest voice note audio (Multipart STT -> CheckResult) |
| `POST` | `/v1/speak` | Read safe verdict aloud via Indic voice synthesis |
| `POST` | `/v1/pause/plan` | Generate cooling-off plan, loss comparison, and calendar reminder |
| `GET` | `/v1/resources/already-paid` | Recovery checklist and emergency numbers for victims |
| `GET` | `/v1/registry/lookup` | Offline dated SEBI intermediary snapshot search |
| `GET` | `/v1/privacy` | Discloses zero-persistence guarantees and active AI processors |

For full request/response schemas and curl examples, see [API_CONTRACT.md](file:///d:/Ruko/backend/API_CONTRACT.md).
