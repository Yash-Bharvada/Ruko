/**
 * Ruko Frontend API Client
 * Connects directly to Ruko FastAPI Backend running ML Model, Rule Engine,
 * and SEBI 6,583+ Registry.
 */

const API_BASE = ""; // Relative path automatically proxies to http://localhost:8000 in dev via vite proxy

export type VerdictType =
  "strong_red_flags" | "cannot_verify" | "no_red_flags_found" | "out_of_scope";
export type SeverityType = "high" | "medium" | "low" | "info";

export interface Reason {
  code: string;
  severity: SeverityType;
  text: string;
  evidence: string;
  source: "rule" | "model" | "registry" | "extractor";
}

export interface ModelInfo {
  available: boolean;
  score: number | null;
  top_words: string[];
  calming_words: string[];
}

export interface RegistryMatch {
  reg_no: string;
  name: string;
  category: string;
  status: string;
  similarity: number;
  is_sample: boolean;
}

export interface RegistryInfo {
  status: string;
  matches: RegistryMatch[];
  snapshot_date: string;
  is_sample_data: boolean;
  verify_url: string;
}

export interface CheckResult {
  request_id: string;
  language: string;
  verdict: VerdictType;
  score: number; // 0.0 to 1.0
  reasons: Reason[];
  registry?: RegistryInfo;
  model?: ModelInfo;
  claims?: Record<string, any>;
  note: string;
  disclaimer: string;
  text?: string;
  source: string;
  input_source: string;
  speech_text?: string | null;
  on_screen_text?: string | null;
  hint?: string | null;
  degraded?: string[];
}

export interface RegistryLookupResponse {
  status: "found_in_snapshot" | "possible_match" | "not_found_in_snapshot";
  query: string;
  matches: RegistryMatch[];
  snapshot_date: string;
  is_sample_data: boolean;
  verify_url: string;
}

export interface PausePlanResponse {
  decision_questions: string[];
  cooling_off_hours: number;
  loss_arithmetic: {
    amount: number;
    months_of_expenses: number;
    sentence: string;
  } | null;
  calendar_ics: string;
  calendar_data_uri: string;
  share_link: string;
  share_text: string;
}

export interface RecoveryChecklistStep {
  step: number;
  priority: string;
  action: string;
  description: string;
  contact: string;
  verify: boolean;
}

export interface RecoveryResourcesResponse {
  language: string;
  title: string;
  note: string;
  checklist: RecoveryChecklistStep[];
}

export interface SpeakResponse {
  source: "sarvam_tts" | "browser_speech";
  text?: string;
  lang_code?: string;
  audio_url?: string;
}

/**
 * Client-side OCR using Tesseract.js for images.
 * Extracts real text from screenshots before sending to backend.
 */
async function extractTextFromImage(file: File, onProgress?: (p: number) => void): Promise<string> {
  try {
    // Dynamic import so Tesseract is only loaded when needed
    const { createWorker } = await import("tesseract.js");
    const worker = await createWorker(["eng", "hin"], 1, {
      logger: (m) => {
        if (m.status === "recognizing text" && onProgress) {
          onProgress(Math.round(m.progress * 100));
        }
      },
    });

    const arrayBuffer = await file.arrayBuffer();
    const uint8 = new Uint8Array(arrayBuffer);
    const { data } = await worker.recognize(uint8);
    await worker.terminate();

    const text = data.text?.trim() ?? "";
    return text;
  } catch (err) {
    console.warn("Client OCR failed, sending image without extracted text:", err);
    return "";
  }
}

/**
 * Check plain text offer or message using the real ML model and rule engine
 */
export async function checkText(
  text: string,
  language?: string,
  amount?: number,
): Promise<CheckResult> {
  const payload: Record<string, any> = { text };
  if (language) payload.language = language;
  if (amount !== undefined && amount !== null && !isNaN(amount) && amount > 0) {
    payload.amount = amount;
  }

  const res = await fetch(`${API_BASE}/v1/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    const errorMsg = data?.error?.message || "Failed to analyze message.";
    throw new Error(errorMsg);
  }
  return data as CheckResult;
}

/**
 * Check uploaded file (screenshot, voice note, video reel, PDF, text)
 * For images: runs client-side Tesseract OCR first, then sends extracted text.
 */
export async function checkMedia(
  file: File,
  language?: string,
  amount?: number,
  onOcrProgress?: (p: number) => void,
): Promise<CheckResult> {
  const formData = new FormData();
  formData.append("file", file);
  if (language) {
    formData.append("language", language);
    formData.append("language_hint", language);
  }
  if (amount !== undefined && amount !== null && !isNaN(amount) && amount > 0) {
    formData.append("amount", String(amount));
  }

  // For images: run Tesseract OCR client-side and send extracted text
  const mime = file.type.toLowerCase();
  const name = file.name.toLowerCase();
  const isImage =
    mime.startsWith("image/") ||
    name.endsWith(".png") ||
    name.endsWith(".jpg") ||
    name.endsWith(".jpeg") ||
    name.endsWith(".webp");

  if (isImage) {
    const extractedText = await extractTextFromImage(file, onOcrProgress);
    if (extractedText && extractedText.length >= 5) {
      formData.append("extracted_text", extractedText);
    }
  }

  const res = await fetch(`${API_BASE}/v1/check/media`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    const errorMsg = data?.error?.message || "Failed to analyze media file.";
    throw new Error(errorMsg);
  }
  return data as CheckResult;
}

/**
 * Live search across 6,583+ official SEBI registered entities
 */
export async function lookupRegistry(query: string): Promise<RegistryLookupResponse> {
  if (!query || !query.trim()) {
    return {
      status: "not_found_in_snapshot",
      query: "",
      matches: [],
      snapshot_date: "2026-10-03",
      is_sample_data: false,
      verify_url: "https://www.sebi.gov.in",
    };
  }

  const res = await fetch(`${API_BASE}/v1/registry/lookup?q=${encodeURIComponent(query.trim())}`);
  const data = await res.json();
  if (!res.ok) {
    const errorMsg = data?.error?.message || "Registry search failed.";
    throw new Error(errorMsg);
  }
  return data as RegistryLookupResponse;
}

/**
 * Generate 24-hour cooling-off intervention plan
 */
export async function getPausePlan(params: {
  verdict: VerdictType;
  amount?: number;
  monthlyExpenses?: number;
  language?: string;
}): Promise<PausePlanResponse> {
  const res = await fetch(`${API_BASE}/v1/pause/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      verdict: params.verdict,
      amount: params.amount ?? 50000,
      monthly_expenses: params.monthlyExpenses ?? 25000,
      language: params.language ?? "en",
    }),
  });

  const data = await res.json();
  if (!res.ok) {
    const errorMsg = data?.error?.message || "Failed to build pause plan.";
    throw new Error(errorMsg);
  }
  return data as PausePlanResponse;
}

/**
 * Retrieve verified emergency recovery resources & cyber helpline numbers
 */
export async function getRecoveryResources(language = "en"): Promise<RecoveryResourcesResponse> {
  const res = await fetch(
    `${API_BASE}/v1/resources/already-paid?lang=${encodeURIComponent(language)}`,
  );
  const data = await res.json();
  if (!res.ok) {
    const errorMsg = data?.error?.message || "Failed to load recovery resources.";
    throw new Error(errorMsg);
  }
  return data as RecoveryResourcesResponse;
}

/**
 * Speak verdict aloud using backend TTS or browser Web Speech API
 */
export async function speakVerdict(verdict: VerdictType, language = "en"): Promise<SpeakResponse> {
  const res = await fetch(`${API_BASE}/v1/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ verdict, language }),
  });

  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("audio/")) {
    const blob = await res.blob();
    const audioUrl = URL.createObjectURL(blob);
    return { source: "sarvam_tts", audio_url: audioUrl };
  }

  const data = await res.json();
  if (!res.ok) {
    const errorMsg = data?.error?.message || "Text-to-speech failed.";
    throw new Error(errorMsg);
  }
  return data as SpeakResponse;
}

// ─── Chat & AI Insights ───────────────────────────────────────────────────────

export interface ChatMsg {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
  suggestions: string[];
}

export interface InsightChartData {
  label: string;
  value: number;
  color?: string;
}

export interface InsightChart {
  title: string;
  type: "donut" | "bar" | "gauge" | "risk_matrix";
  data: InsightChartData[];
  insight: string;
  color: string;
}

export interface InsightsResponse {
  summary: string;
  risk_level: "critical" | "high" | "medium" | "low";
  charts: InsightChart[];
  action_items: string[];
  confidence_note: string;
}

/**
 * Ruko AI Chat Agent — Groq Llama 3.3-70b
 */
export async function chatWithRuko(
  messages: ChatMsg[],
  context?: Partial<CheckResult>,
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, context }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || "Chat failed.");
  return data as ChatResponse;
}

/**
 * Generate AI insight charts for a completed scan result
 */
export async function getInsights(result: CheckResult): Promise<InsightsResponse> {
  const res = await fetch(`${API_BASE}/v1/analyze/insights`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      score: result.score,
      verdict: result.verdict,
      reasons: result.reasons,
      claims: result.claims,
      language: result.language,
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || "Insights failed.");
  return data as InsightsResponse;
}

// ─── Explain a Document (DocExplain) ──────────────────────────────────────────

export interface GlossaryItem {
  term: string;
  meaning: string;
  evidence: string;
}

export interface KeyPoint {
  id: string;
  category: "obligation" | "fee" | "deadline" | "risk" | "right" | "other" | string;
  text: string;
  evidence: string;
}

export interface Step {
  order: number;
  title: string;
  text: string;
  evidence: string;
}

export interface GraphNode {
  id: string;
  label: string;
  kind: "start" | "step" | "decision" | "end" | "money" | "party" | "loop";
}

export interface GraphEdge {
  source: string;
  target: string;
  label?: string | null;
}

export interface FlowGraph {
  title: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface TimelineItem {
  label: string;
  date_text: string;
  evidence: string;
}

export interface Diagrams {
  flowchart?: FlowGraph | null;
  money_flow?: FlowGraph | null;
  timeline?: TimelineItem[];
}

export interface SceneVisual {
  type: "title" | "bullets" | "flowchart" | "timeline" | "money_flow";
  ref?: string | null;
}

export interface Scene {
  scene_id: string;
  narration: string;
  caption: string;
  visual: SceneVisual;
  issued_at: number;
  speak_token: string;
}

export interface DocExplanation {
  request_id: string;
  language: string;
  input_source: string;
  doc_type_guess: string;
  document_type?: string;
  summary: string;
  glossary: GlossaryItem[];
  key_points: KeyPoint[];
  steps: Step[];
  diagrams: Diagrams;
  storyboard: Scene[];
  ruko_flags: Reason[];
  registry?: RegistryInfo | null;
  ocr_quality: "good" | "low" | "n/a";
  confidence_notes: string[];
  disclaimer: string;
  degraded: string[];
}

export interface ExplainSpeakRequest {
  request_id: string;
  scene_id: string;
  language: string;
  narration: string;
  issued_at: number;
  speak_token: string;
}

export interface ExplainSpeakResponse {
  source: "sarvam" | "browser_speech";
  audio_base64?: string;
  mime?: string;
  text?: string;
  lang_code?: string;
}

/**
 * Submit document or pasted text to /v1/explain with 90s timeout
 */
export async function explainDocument(formData: FormData): Promise<DocExplanation> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 90000);

  try {
    const res = await fetch(`${API_BASE}/v1/explain`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });

    const data = await res.json();
    if (!res.ok) {
      const errorMsg = data?.error?.message || data?.detail || "Failed to explain document.";
      throw new Error(errorMsg);
    }
    return data as DocExplanation;
  } catch (err: any) {
    if (err.name === "AbortError") {
      throw new Error(
        "Document explanation timed out after 90 seconds. Please try a shorter excerpt or paste the text directly.",
      );
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Synthesize speech for a verified storyboard scene with HMAC signature token
 */
export async function speakExplainScene(
  payload: ExplainSpeakRequest,
): Promise<ExplainSpeakResponse> {
  const res = await fetch(`${API_BASE}/v1/explain/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    const errorMsg = data?.error?.message || data?.detail || "Audio synthesis failed for scene.";
    throw new Error(errorMsg);
  }
  return data as ExplainSpeakResponse;
}
