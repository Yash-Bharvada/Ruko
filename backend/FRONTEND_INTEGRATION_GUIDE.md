# Ruko Frontend Integration Guide & API Reference

> **Base URL**: `http://localhost:8000`  
> **Interactive Swagger Documentation**: `http://localhost:8000/docs`  
> **OpenAPI 3.1 Spec**: `http://localhost:8000/openapi.json`  
> **Supported Languages**: English (`en`), Hindi (`hi`), Gujarati (`gu`)  
> **CORS**: Configured to accept all origins (`*`) in development.

---

## 1. Architecture & Capabilities Overview

Ruko is an investor-protection anti-fraud backend designed to protect retail investors from financial fraud, unauthorized stock tip channels, and impersonation scams.

### Key Capabilities for the Frontend:
1. **Universal Dropzone (`POST /v1/check/media`)**:
   - Accepts `.txt`, images (`.png`, `.jpg`, `.jpeg`, `.webp`), audio voice notes (`.mp3`, `.wav`, `.m4a`, `.ogg`), or video reels (`.mp4`, `.mov`, `.webm`).
   - Automatically routes bytes to plain text parsing, in-memory Vision OCR, Indic Speech-to-Text, or video frame extraction.
2. **Instant SEBI Intermediary Search (`GET /v1/registry/lookup`)**:
   - Searches **6,583+ official live SEBI intermediaries** offline in under 2ms.
   - Verifies claimed registration numbers (`INA...`, `INH...`, `INP...`, `INZ...`) and matches company names.
3. **Verdict Engine**:
   - Returns one of 4 standardized verdicts with localized explanations, risk score (0.0 to 1.0), and strict evidence snippets quoted from the message.
4. **Vernacular Read-Aloud (`POST /v1/speak`)**:
   - Reads the verdict aloud in Hindi, Gujarati, or Indian English via Sarvam AI, with an automatic browser Web Speech API fallback.
5. **Cooling-Off Pause Intervention (`POST /v1/pause/plan`)**:
   - Generates 3 reflection questions, loss arithmetic, a pre-filled WhatsApp accountability message, and a 24-hour calendar event `.ics` file.
6. **Emergency Recovery Resources (`GET /v1/pause/recovery-resources`)**:
   - Provides direct one-tap links to the National Cybercrime Portal (`1930`), SEBI SCORES, and RBI Sachet.

---

## 2. API Endpoints Reference

| Method | Endpoint | Format | Description |
|---|---|---|---|
| `POST` | `/v1/check/media` | `multipart/form-data` | **Primary Universal Check**: Text, Screenshot, Voice Note, or Video Reel |
| `POST` | `/v1/check` | `application/json` | Text-only message checking |
| `POST` | `/v1/check/image` | `multipart/form-data` | Direct screenshot/image OCR check |
| `POST` | `/v1/check/audio` | `multipart/form-data` | Direct audio voice-note check |
| `GET` | `/v1/registry/lookup` | Query Param `?q=` | Live search against 6,583+ registered SEBI advisers & brokers |
| `POST` | `/v1/pause/plan` | `application/json` | Generate 24-hour cooling-off intervention & reflection questions |
| `GET` | `/v1/pause/cooling-off.ics` | Query Params | Direct `.ics` iCalendar download for Apple/Google Calendar reminder |
| `GET` | `/v1/pause/recovery-resources` | Query Param `?lang=` | Directory of emergency numbers (1930) and reporting portals |
| `POST` | `/v1/speak` | `application/json` | Vernacular audio readout (`audio/wav`) with browser fallback script |
| `GET` | `/v1/privacy` | — | Zero-storage policy and third-party AI processing disclosure |
| `GET` | `/health` | — | Backend health and module readiness |

---

## 3. TypeScript Interfaces

```typescript
// --- Core Check Result ---
export type VerdictType = "strong_red_flags" | "cannot_verify" | "no_red_flags_found" | "out_of_scope";
export type SeverityType = "high" | "medium" | "low" | "info";
export type InputSourceType = "text" | "ocr" | "stt" | "video";

export interface Reason {
  code: string;            // e.g. "guaranteed_returns", "personal_upi_payment"
  severity: SeverityType;  // "high" | "medium" | "low" | "info"
  text: string;            // Localized explanation of the red flag
  evidence: string;        // Exact text snippet matched from the message
  source: "rule" | "model" | "registry" | "extractor";
}

export interface CheckResult {
  request_id: string;
  verdict: VerdictType;
  score: number;           // 0.0 (safe) to 1.0 (high risk)
  language: "en" | "hi" | "gu";
  input_source: InputSourceType;
  speech_text?: string;    // Transcribed speech if video was uploaded
  on_screen_text?: string; // OCR text from video frames
  reasons: Reason[];
  note: string;            // Summary advice badge
  disclaimer: string;      // Legal disclaimer
  hint?: string | null;    // Contextual hints (e.g. Instagram link warnings)
  degraded: string[];      // Non-blocking degraded flags (e.g. ["model_unavailable"])
}

// --- SEBI Registry Lookup ---
export interface RegistryMatch {
  reg_no: string;          // e.g. "INA000000094"
  name: string;            // e.g. "ICICI SECURITIES LIMITED"
  category: string;        // "Investment Adviser", "Research Analyst", "Stock Broker"
  status: string;          // "Active" | "Inactive"
  similarity: number;      // 0.0 - 100.0
  is_sample: boolean;      // false for live SEBI entities
}

export interface RegistryLookupResponse {
  status: "found_in_snapshot" | "possible_match" | "not_found_in_snapshot";
  query: string;
  matches: RegistryMatch[];
  snapshot_date: string;
  is_sample_data: boolean;
  verify_url: string;
}

// --- Cooling-Off Pause Plan ---
export interface LossCalculation {
  amount: number | null;
  worst_case_loss: number | null;
  loss_text: string;       // e.g. "If this is a scam, you stand to lose the entire ₹50,000.00."
}

export interface PausePlanResponse {
  pause_hours: number;     // 24
  questions: string[];     // 3 targeted reflection questions
  loss_calculation: LossCalculation;
  whatsapp_share_url: string;    // Pre-filled WhatsApp web link for loved ones
  calendar_download_url: string; // URL to download .ics event
  language: string;
}

// --- Emergency Recovery Resources ---
export interface ResourceItem {
  name: string;
  url: string;
  action: string;
  category: "cybercrime" | "regulator" | "banking";
}

export interface RecoveryResourcesResponse {
  language: string;
  emergency_helpline: string;       // "1930"
  emergency_helpline_label: string; // "National Cyber Crime Helpline (Toll-Free 24x7)"
  resources: ResourceItem[];
}

// --- Read-Aloud Voice ---
export interface SpeakResponse {
  audio_base64: string | null;  // base64 WAV audio string, null if fallback
  content_type: string;        // "audio/wav"
  browser_fallback: boolean;   // true if frontend should use window.speechSynthesis
  spoken_text: string;         // Plain safe script to speak
  language: string;
}
```

---

## 4. Endpoint Specifications & Examples

### 1. `POST /v1/check/media` (Universal Multi-Modal Uploader)
Upload **any** media file (text, screenshot, voice note, or screen-recorded reel).

* **Header**: `Content-Type: multipart/form-data`
* **Parameters**:
  * `file` *(File, required)*: Binary file.
  * `language` *(string, optional)*: `"en"` | `"hi"` | `"gu"`.
  * `amount` *(number, optional)*: Investment amount mentioned (e.g. `25000`).

#### Fetch Example:
```typescript
const formData = new FormData();
formData.append("file", fileObject);
formData.append("language", "en"); // optional
if (amount) formData.append("amount", amount.toString());

const response = await fetch("http://localhost:8000/v1/check/media", {
  method: "POST",
  body: formData,
});
const data: CheckResult = await response.json();
```

---

### 2. `POST /v1/check` (Plain Text Check)
* **Header**: `Content-Type: application/json`
* **Request Body**:
```json
{
  "text": "Guaranteed 35% monthly returns! 100% risk free. Join VIP group t.me/profit and send 10,000 to invest@okaxis. SEBI Reg No: INA000099999",
  "language_hint": "en",
  "amount": 10000
}
```

---

### 3. `GET /v1/registry/lookup` (SEBI Registry Search)
* **URL**: `http://localhost:8000/v1/registry/lookup?q=INA000000094` *(or `?q=Zerodha`)*
* **Response**:
```json
{
  "status": "found_in_snapshot",
  "query": "INA000000094",
  "matches": [
    {
      "reg_no": "INA000000094",
      "name": "ICICI SECURITIES LIMITED",
      "category": "Investment Adviser",
      "status": "Active",
      "similarity": 100.0,
      "is_sample": false
    }
  ],
  "snapshot_date": "2026-10-03",
  "is_sample_data": false,
  "verify_url": "https://www.sebi.gov.in"
}
```

---

### 4. `POST /v1/pause/plan` (Cooling-Off Intervention)
Call this when `data.verdict === "strong_red_flags"` to render the 24-hour pause intervention modal.

* **Header**: `Content-Type: application/json`
* **Request Body**:
```json
{
  "reasons": data.reasons,
  "amount": 50000,
  "language": "en"
}
```
* **Response**:
```json
{
  "pause_hours": 24,
  "questions": [
    "Who is guaranteeing this return? SEBI prohibits registered advisors from guaranteeing fixed returns.",
    "Are you being asked to transfer money into an individual's personal UPI ID instead of a SEBI-registered corporate bank account?",
    "Were you added to a Telegram or WhatsApp group without requesting it?"
  ],
  "loss_calculation": {
    "amount": 50000.0,
    "worst_case_loss": 50000.0,
    "loss_text": "If this is a scam, you stand to lose the entire ₹50,000.00."
  },
  "whatsapp_share_url": "https://api.whatsapp.com/send?text=I%20am%20considering%20an%20investment%20that%20flagged%20potential%20risks%20on%20Ruko.%20Can%20you%20review%20this%20with%20me%3F",
  "calendar_download_url": "/v1/pause/cooling-off.ics?hours=24&lang=en",
  "language": "en"
}
```

---

### 5. `GET /v1/pause/cooling-off.ics` (Calendar Event Download)
Direct file download endpoint. Point a standard anchor tag to this link:
```html
<a href="http://localhost:8000/v1/pause/cooling-off.ics?hours=24&lang=en" download="ruko_cooling_off.ics">
  🗓 Add 24-Hour Reminder to Calendar
</a>
```

---

### 6. `POST /v1/speak` (Vernacular Audio Readout)
* **Header**: `Content-Type: application/json`
* **Request Body**:
```json
{
  "verdict": data.verdict,
  "reasons": data.reasons,
  "language": data.language
}
```
* **Client Audio Playback Handling**:
```typescript
const speakRes = await fetch("http://localhost:8000/v1/speak", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ verdict: data.verdict, reasons: data.reasons, language: data.language }),
});
const voiceData: SpeakResponse = await speakRes.json();

if (voiceData.audio_base64) {
  // Play Sarvam AI audio directly
  const audio = new Audio(`data:audio/wav;base64,${voiceData.audio_base64}`);
  audio.play();
} else if (voiceData.browser_fallback && "speechSynthesis" in window) {
  // Fall back to native browser speech synthesis
  const utterance = new SpeechSynthesisUtterance(voiceData.spoken_text);
  utterance.lang = voiceData.language === "hi" ? "hi-IN" : voiceData.language === "gu" ? "gu-IN" : "en-IN";
  window.speechSynthesis.speak(utterance);
}
```

---

## 5. UI Design Guidelines & Verdict Themes

Use these colors, icons, and card treatments based on `data.verdict`:

| Verdict | Color | Theme Class | Header Title | Suggested Action |
|---|---|---|---|---|
| `strong_red_flags` | 🔴 **Crimson** (`#E11D48`) | `bg-red-50 text-red-900 border-red-500` | **High Risk Scam Warning** | Show "Start 24-Hour Pause" button + full list of red flag badges. |
| `cannot_verify` | 🟡 **Amber** (`#D97706`) | `bg-amber-50 text-amber-900 border-amber-500` | **Unconfirmed Claims — Caution** | Warn user that claimed SEBI registration was not found in official snapshot. |
| `no_red_flags_found` | 🟢 **Emerald** (`#059669`) | `bg-emerald-50 text-emerald-900 border-emerald-500` | **No Obvious Red Flags** | Remind user that absence of red flags does not mean guaranteed safety. |
| `out_of_scope` | 🔵 **Cyan** (`#0891B2`) | `bg-cyan-50 text-cyan-900 border-cyan-500` | **Investment Advice Not Supported** | Inform user that Ruko only screens for fraud, not stock predictions. |

---

## 6. Recommended Screen Flow & UI Hierarchy

```text
[Navbar]
  - Logo + Brand ("Ruko - Investor Protection")
  - Language Selector dropdown [ English | हिन्दी | ગુજરાતી ]
  - "Verify SEBI License" search trigger button

[Hero Section]
  - Heading: "Check Any Investment Tip Before You Pay"
  - Subhead: "Paste a message, upload a screenshot, voice note, or video reel."

[Universal Ingest Box]
  - Tabs: [ 📝 Text Message | 📸 Screenshot | 🎙 Voice Note | 🎥 Video Reel ]
  - Dropzone: Accepts drag-and-drop or file browsing
  - Optional Input: "Amount mentioned (₹)"
  - "Check Message" CTA button

[Results Card] (Appears upon response)
  - Verdict Banner (Color-coded badge + audio speaker icon for /v1/speak)
  - Key Findings List:
      - High/Medium Severity badges
      - Quoted evidence pill: e.g. "Guaranteed 35% monthly"
      - Explanation text
  - Video Reel Details (if input_source === "video"):
      - Spoken dialogue transcript
      - On-screen frame text

[24-Hour Cooling-Off Modal] (Auto-prompted if strong_red_flags)
  - 3 Reflection Questions
  - Loss Arithmetic Banner: "You stand to lose the entire ₹X."
  - "Share with Family / Friend" -> opens WhatsApp pre-filled link
  - "Add 24h Reminder to Calendar" -> downloads .ics file

[Already Transferred Money? Emergency Drawer]
  - Toll-free 1930 Cybercrime Helpline direct call button
  - Quick links to cybercrime.gov.in, SEBI SCORES, RBI Sachet

[Footer]
  - Direct link to /v1/privacy
  - Real-time Backend Health indicator
```

---

## 7. Error Handling Standard

All non-200 responses return this uniform JSON schema:
```json
{
  "error": {
    "code": "invalid_video_format",
    "message": "Uploaded file is not a supported video format (MP4, MOV, WEBM)",
    "request_id": "993a4b08-3cfc-4d51-9311-66c5a31b4097",
    "details": {}
  }
}
```

* Common HTTP Status Codes:
  * `413 Payload Too Large`: File exceeds size limit (Text > 4000 chars, Image > 5MB, Audio > 10MB, Video > 25MB or > 60s).
  * `422 Unprocessable Entity`: Corrupted file or not enough readable text extracted.
  * `429 Too Many Requests`: Client exceeded 30 requests per minute.
  * `503 Service Unavailable`: Feature disabled (e.g. third-party AI disabled or missing ffmpeg).
