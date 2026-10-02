# Ruko Backend API Contract & Specification

This document details all HTTP API endpoints implemented by the Ruko backend, including request/response schemas, error handling behavior, and copy-pasteable `curl` examples.

---

## 1. Global Specifications

- **Base URL**: `http://localhost:8000`
- **Default Headers**:
  - `Accept: application/json`
  - `X-Request-ID`: Optional client UUID (auto-generated if omitted)
- **Rate Limit**: 30 requests per minute per IP. The 31st request receives HTTP 429.
- **Privacy By Design**:
  - Zero persistence of user messages, images, audio, or PII.
  - Request bodies and messages are NEVER logged.

---

## 2. API Endpoints

### 2.1 Health & Liveness
- **Method**: `GET`
- **Path**: `/health`
- **Purpose**: Liveness probe and status of internal modules.

```bash
curl -X GET http://localhost:8000/health
```

**Response (200 OK)**:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "modules": {
    "model_adapter": "active",
    "rules": "active",
    "registry": "active",
    "extractor": "active",
    "ingest": "active",
    "verdict": "active",
    "voice": "active",
    "pause": "active",
    "guardrails": "active"
  },
  "model": "active"
}
```

---

### 2.2 Check Text Message
- **Method**: `POST`
- **Path**: `/v1/check`
- **Request Body**:
  - `text` (string, required, 1-4000 chars): Message content.
  - `language` (string, optional): `"gu"`, `"hi"`, or `"en"`.
  - `amount` (float, optional): Investment amount mentioned.

```bash
curl -X POST http://localhost:8000/v1/check \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Join VIP group t.me/vip_trading. Guaranteed 30% monthly return! Transfer 5000 to trade@ybl immediately. SEBI Reg: INA000012345.",
    "language": "en",
    "amount": 5000
  }'
```

**Response (200 OK - `CheckResult`)**:
```json
{
  "request_id": "c71a396e-52f6-499f-8be7-78da47f0bc62",
  "language": "en",
  "verdict": "strong_red_flags",
  "score": 0.95,
  "reasons": [
    {
      "code": "guaranteed_returns",
      "severity": "high",
      "text": "Promises guaranteed or risk-free returns, which is prohibited under SEBI regulations.",
      "evidence": "Guaranteed 30% monthly return",
      "source": "rule"
    },
    {
      "code": "unauthorized_channel",
      "severity": "high",
      "text": "Directs communication to private chat groups rather than registered SEBI channels.",
      "evidence": "t.me/vip_trading",
      "source": "rule"
    }
  ],
  "registry": {
    "status": "not_found_in_snapshot",
    "matches": [
      {
        "reg_no": "INA000012345",
        "match_type": "unconfirmed_reg_no",
        "format_valid": true,
        "inferred_category": "Investment Adviser (IA)"
      }
    ],
    "snapshot_date": "2026-03-01",
    "is_sample_data": true,
    "verify_url": "https://www.sebi.gov.in"
  },
  "model": {
    "available": true,
    "score": 0.88,
    "top_words": ["guaranteed", "vip", "transfer"],
    "calming_words": []
  },
  "claims": {
    "claimed_registration_numbers": ["INA000012345"],
    "promised_returns": [{"value": 30.0, "period": "monthly"}],
    "payment_requests": [{"amount": 5000.0, "method": "upi", "target": "trade@ybl"}],
    "group_links": ["https://t.me/vip_trading"]
  },
  "note": "Critical red flags detected. Registered entities cannot promise fixed returns or demand private transfers.",
  "degraded": [],
  "disclaimer": "Educational analysis based on offline heuristics and local snapshot. Verify directly at https://www.sebi.gov.in.",
  "text": null,
  "source": "text"
}
```

---

### 2.3 Check Image (Screenshot OCR)
- **Method**: `POST`
- **Path**: `/v1/check/image`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Image file (PNG, JPEG, WEBP <= 5MB).
  - `language` (string, optional): `"gu"`, `"hi"`, or `"en"`.
  - `amount` (float, optional): Investment amount.

```bash
curl -X POST http://localhost:8000/v1/check/image \
  -F "file=@screenshot.png;type=image/png" \
  -F "language=gu"
```

**Response (200 OK - `CheckResult`)**:
Returns `CheckResult` with `source: "ocr"` and `text: "<extracted OCR text>"`.

---

### 2.4 Check Audio (Voice Note STT)
- **Method**: `POST`
- **Path**: `/v1/check/audio`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Audio file (WAV, MP3, OGG, WEBM, M4A <= 10MB).
  - `language` (string, optional): `"gu"`, `"hi"`, or `"en"`.

```bash
curl -X POST http://localhost:8000/v1/check/audio \
  -F "file=@voicenote.wav;type=audio/wav" \
  -F "language=hi"
```

**Response (200 OK - `CheckResult`)**:
Returns `CheckResult` with `source: "stt"` and `text: "<transcribed voice text>"`.

---

### 2.5 Text-to-Speech Voice Synthesis
- **Method**: `POST`
- **Path**: `/v1/speak`
- **Request Body**:
  - `verdict` (string, required): `"strong_red_flags"`, `"cannot_verify"`, etc.
  - `reason_codes` (list of strings, required): Reason codes.
  - `language` (string, optional): `"en"`, `"hi"`, or `"gu"`.

```bash
curl -X POST http://localhost:8000/v1/speak \
  -H "Content-Type: application/json" \
  -d '{
    "verdict": "strong_red_flags",
    "reason_codes": ["guaranteed_returns", "unauthorized_channel"],
    "language": "gu"
  }'
```

**Response (200 OK)**:
```json
{
  "mode": "audio",
  "mime_type": "audio/wav",
  "audio_base64": "UklGRi...",
  "spoken_script": "સાવધાન: ગંભીર જોખમી સંકેતો મળ્યા છે...",
  "cached": true
}
```

---

### 2.6 Pause Layer Decision Card & Action Plan
- **Method**: `POST`
- **Path**: `/v1/pause/plan`
- **Request Body**:
  - `verdict` (string, required): Current verdict.
  - `language` (string, optional): `"en"`, `"hi"`, or `"gu"`.
  - `amount` (float, optional): Proposed investment amount.
  - `monthly_expenses` (float, optional): Monthly living costs.

```bash
curl -X POST http://localhost:8000/v1/pause/plan \
  -H "Content-Type: application/json" \
  -d '{
    "verdict": "strong_red_flags",
    "language": "hi",
    "amount": 50000,
    "monthly_expenses": 25000
  }'
```

**Response (200 OK)**:
```json
{
  "headline": "रुको — पैसे भेजने से पहले 24 घंटे का विराम लें",
  "cooling_off_hours": 24,
  "questions": [
    {
      "id": "guaranteed_check",
      "prompt": "क्या आपको बिना किसी जोखिम के गारंटीड रिटर्न का वादा किया गया है?",
      "educational_note": "सेबी के नियमानुसार कोई भी पंजीकृत इकाई कभी गारंटीड रिटर्न का वादा नहीं कर सकती।"
    }
  ],
  "loss_math": {
    "proposed_amount": 50000.0,
    "monthly_expenses": 25000.0,
    "expense_months_equivalent": 2.0,
    "statement": "यदि यह पैसा डूब जाता है, तो यह आपके लगभग 2.0 महीने के घरेलू खर्च के बराबर होगा।"
  },
  "calendar_reminder_ics": "BEGIN:VCALENDAR\nVERSION:2.0\n...",
  "share_link": "https://api.whatsapp.com/send?text=...",
  "disclaimer": "यह वित्तीय सलाह नहीं है। केवल शैक्षिक उद्देश्य के लिए है।"
}
```

---

### 2.7 Recovery Resources for Victims
- **Method**: `GET`
- **Path**: `/v1/resources/already-paid?lang=en`
- **Query Params**:
  - `lang` (optional): `"en"`, `"hi"`, `"gu"`.

```bash
curl -X GET "http://localhost:8000/v1/resources/already-paid?lang=hi"
```

---

### 2.8 SEBI Registry Snapshot Lookup
- **Method**: `GET`
- **Path**: `/v1/registry/lookup?q=INA000000001`
- **Query Params**:
  - `q` (required): Registration number or entity name.

```bash
curl -X GET "http://localhost:8000/v1/registry/lookup?q=INA000000001"
```

---

### 2.9 Privacy & Third-Party Disclosure
- **Method**: `GET`
- **Path**: `/v1/privacy`
- **Purpose**: Discloses zero-persistence architecture and external AI processors.

```bash
curl -X GET http://localhost:8000/v1/privacy
```

---

## 3. Uniform Error Envelope

All 4xx and 5xx errors return a consistent envelope:

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit of 30 requests per minute exceeded. Please try again later.",
    "request_id": "9d2b270a-7ca7-4c4f-9e58-692d9f187a55"
  }
}
```
