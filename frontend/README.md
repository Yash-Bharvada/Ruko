# Ruko Frontend

Investor Protection & Anti-Fraud Web Application for Indian Retail Investors.

## Features

- **Universal Dropzone**: Real-time scam analysis for text messages, screenshots (OCR), voice notes (STT), and video reels.
- **SEBI Registry Verification**: Offline search across 6,583+ registered SEBI intermediaries with exact and fuzzy matching.
- **Explainable Verdicts**: Multi-tier risk scoring (0–100) with evidence highlights and vernacular read-aloud support.
- **24-Hour Cooling-Off Pause**: Loss arithmetic, family accountability WhatsApp sharing, and calendar reminder `.ics` export.
- **Emergency Recovery Hub**: One-tap access to national cybercrime helpline (1930), NCRP, SEBI SCORES, and RBI CMS.

## Development

```bash
bun install
bun run dev
```

The frontend dev server runs at `http://localhost:3000` and automatically proxies `/v1/*` requests to the Ruko FastAPI backend running at `http://localhost:8000`.
