import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { RukoLogo } from "../components/RukoLogo";
import { ThemeToggle } from "../components/ThemeToggle";
import { ScamThreatCarousel } from "../components/ScamThreatCarousel";
import { ContinuousThreatStream } from "../components/ContinuousThreatStream";
import {
  checkText,
  checkMedia,
  lookupRegistry,
  getPausePlan,
  getRecoveryResources,
  speakVerdict,
  type CheckResult,
  type RegistryMatch,
  type PausePlanResponse,
  type RecoveryChecklistStep,
} from "../lib/api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Ruko — Check before you invest" },
      {
        name: "description",
        content:
          "Ruko helps Indian investors spot scams, verify SEBI registration, and take a cooling-off pause before their money moves.",
      },
      { property: "og:title", content: "Ruko — Check before you invest" },
      {
        property: "og:description",
        content: "Spot investment scams, verify SEBI registration, and recover quickly.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll(".reveal");
    const io = new IntersectionObserver(
      (es) =>
        es.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        }),
      { threshold: 0.12 }
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  });
}

const R = ({
  children,
  d = 0,
  className = "",
}: {
  children: ReactNode;
  d?: number;
  className?: string;
}) => (
  <div className={`reveal ${className}`} style={{ ["--d" as string]: `${d}ms` }}>
    {children}
  </div>
);

const Arrow = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 14 14"
    fill="none"
    className="transition-transform group-hover:translate-x-1"
  >
    <path d="M1 7h12M8 2l5 5-5 5" stroke="currentColor" strokeWidth="1.3" />
  </svg>
);

const Logo = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden>
    <rect x="2" y="2" width="20" height="20" rx="5" stroke="currentColor" strokeWidth="1.6" />
    <path d="M7 6h10M7 10h8M9 6v8c0 0 6 0 6-4s-6-4-6-4l7 10" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const SecHead = ({
  n,
  label,
  title,
  id,
}: {
  n: string;
  label: string;
  title: ReactNode;
  id?: string;
}) => (
  <R>
    <div id={id} className="flex items-center gap-3 label-mono text-muted-foreground scroll-mt-24">
      <span>[N.{n}/05]</span>
      <span className="h-px w-8 bg-border" />
      <span>&gt; {label}</span>
      <span className="h-px flex-1 bg-border" />
    </div>
    <h2 className="mt-6 text-4xl font-normal leading-[1.05] tracking-tight md:text-6xl">{title}</h2>
  </R>
);

const btnDark =
  "group inline-flex items-center justify-between gap-6 bg-primary px-5 py-3.5 label-mono text-primary-foreground transition-all hover:bg-accent hover:text-accent-foreground active:scale-[.98] disabled:opacity-40";
const btnLight = btnDark
  .replace("bg-primary", "bg-ink-foreground")
  .replace("text-primary-foreground", "text-ink");

const LANG_OPTIONS = [
  { code: "en", label: "EN · English" },
  { code: "hi", label: "हिं · हिन्दी" },
  { code: "gu", label: "ગુ · ગુજરાતી" },
];

function Nav({
  lang,
  onLangChange,
}: {
  lang: string;
  onLangChange: (l: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const f = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", f);
    return () => window.removeEventListener("scroll", f);
  }, []);

  const links = [
    ["Check", "#check"],
    ["Result", "#result"],
    ["Verify SEBI", "#sebi"],
    ["Safety Pause", "#pause"],
    ["Recovery", "#recovery"],
  ];

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-500 ${
        scrolled ? "bg-background/85 backdrop-blur-md border-b border-border shadow-lg" : "bg-transparent"
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3.5 text-foreground md:px-8">
        <a href="#top" className="flex items-center gap-2.5">
          <RukoLogo size={32} />
        </a>

        <nav className="hidden gap-1 lg:flex items-center">
          {links.map(([l, h]) => (
            <a
              key={l}
              href={h}
              className="px-3 py-1.5 label-mono text-muted-foreground transition-colors hover:text-foreground hover:bg-secondary rounded"
            >
              {l}
            </a>
          ))}
          <Link
            to="/model-stats"
            className="ml-2 inline-flex items-center gap-1.5 rounded-md border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 label-mono text-xs text-cyan-400 transition-all hover:bg-cyan-500 hover:text-slate-950 font-semibold shadow-sm"
          >
            <span>Model & Stats</span>
            <span className="text-[10px] font-mono px-1 py-0.2 bg-cyan-400/20 rounded">0.410</span>
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <ThemeToggle />

          <div className="relative hidden sm:block">
            <select
              aria-label="Language"
              value={lang}
              onChange={(e) => onLangChange(e.target.value)}
              className="appearance-none border border-border bg-card/80 px-3 py-2 pr-7 label-mono text-foreground outline-none focus:border-cyan-400 rounded-md text-xs"
            >
              {LANG_OPTIONS.map((o) => (
                <option key={o.code} value={o.code} className="bg-card text-foreground">
                  {o.label}
                </option>
              ))}
            </select>
            <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground">
              ▼
            </span>
          </div>

          <a
            href="#sebi"
            className="hidden bg-primary px-4 py-2 label-mono text-xs text-primary-foreground transition-all hover:opacity-90 active:scale-95 sm:inline-flex rounded-md"
          >
            ↗ Verify SEBI
          </a>

          <button
            aria-label="Menu"
            onClick={() => setOpen(!open)}
            className="border border-border px-3 py-1.5 label-mono lg:hidden text-foreground rounded-md text-xs"
          >
            {open ? "Close" : "Menu"}
          </button>
        </div>
      </div>

      <div
        className={`overflow-hidden bg-background/95 backdrop-blur-xl border-b border-border transition-[max-height] duration-500 lg:hidden ${
          open ? "max-h-96" : "max-h-0"
        }`}
      >
        <div className="flex flex-col gap-1 px-5 pb-5 text-foreground">
          {links.map(([l, h]) => (
            <a
              key={l}
              href={h}
              onClick={() => setOpen(false)}
              className="border-b border-border/60 py-3 text-base font-medium"
            >
              {l}
            </a>
          ))}
          <Link
            to="/model-stats"
            onClick={() => setOpen(false)}
            className="border-b border-border/60 py-3 text-base font-medium text-cyan-400 flex items-center justify-between"
          >
            <span>Model Thresholds & Stats</span>
            <span className="label-mono text-xs px-2 py-0.5 rounded bg-cyan-500/20 font-mono">0.410</span>
          </Link>
          <div className="flex gap-2 pt-3">
            {LANG_OPTIONS.map((o) => (
              <button
                key={o.code}
                onClick={() => {
                  onLangChange(o.code);
                  setOpen(false);
                }}
                className={`border px-3 py-1.5 label-mono rounded text-xs ${
                  lang === o.code ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground"
                }`}
              >
                {o.label.split(" ")[0]}
              </button>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const f = () => {
      if (ref.current) {
        ref.current.style.transform = `translateY(${window.scrollY * 0.18}px)`;
      }
    };
    window.addEventListener("scroll", f, { passive: true });
    return () => window.removeEventListener("scroll", f);
  }, []);

  const cells = [12, 13, 20, 21, 22, 27, 28, 29, 30, 35, 36, 37, 44, 45, 52];

  return (
    <section id="top" className="relative overflow-hidden bg-ink text-ink-foreground">
      <div className="absolute inset-0 bg-glow" />
      <div className="absolute inset-0 grid-lines opacity-60" />
      <div
        ref={ref}
        className="pointer-events-none absolute right-0 top-24 hidden grid-cols-8 md:grid"
      >
        {Array.from({ length: 64 }).map((_, i) => (
          <div
            key={i}
            className={`h-12 w-12 ${cells.includes(i) ? "pixel bg-accent" : ""}`}
            style={{ animationDelay: `${(i % 7) * 400}ms` }}
          />
        ))}
      </div>

      <div className="relative mx-auto max-w-7xl px-5 pb-10 pt-36 md:px-8 md:pt-44">
        <div className="grid gap-10 md:grid-cols-2">
          <R>
            <p className="max-w-md text-lg leading-snug text-ink-muted md:text-xl">
              Got an investment tip, WhatsApp message, or high-yield offer? Paste it or upload it.
              Ruko scores the scam risk with machine learning and verifies registration against 6,583+
              SEBI entities before your money moves.
            </p>
            <a href="#check" className={`${btnLight} mt-8`}>
              ■ Check an offer <Arrow />
            </a>
          </R>
          <R d={200} className="hidden md:flex md:justify-end md:pt-10">
            <p className="label-mono leading-relaxed text-ink-muted">
              ✦ Pause.
              <br />
              &nbsp;&nbsp;&nbsp;&nbsp;Verify.
              <br />
              &nbsp;&nbsp;Then invest. +
            </p>
          </R>
        </div>

        <div className="mt-20 flex flex-wrap items-end gap-x-6 md:mt-28">
          <h1 className="font-pixel text-[24vw] font-bold leading-[0.78] tracking-tight md:text-[18vw] lg:text-[15rem]">
            RUKO<span className="blink text-accent">_</span>
          </h1>
          <p className="pb-2 text-4xl font-light tracking-tight md:text-6xl">
            Stop. Check.
            <br />
            Stay safe.
          </p>
        </div>
      </div>

      <div className="relative overflow-hidden border-t border-ink-border py-2.5">
        <div className="marquee flex w-max gap-12 label-mono text-ink-muted">
          {Array.from({ length: 8 }).map((_, i) => (
            <span key={i}>
              <span className="text-accent">✦</span> Guaranteed returns are illegal · Verify SEBI
              registration · Report cyber fraud immediately on 1930
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

function Check({
  lang,
  onResult,
  injectedText,
}: {
  lang: string;
  onResult: (r: CheckResult) => void;
  injectedText?: string;
}) {
  const [text, setText] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (injectedText) {
      setText(injectedText);
      setSelectedFile(null);
      setFileType(null);
      setErrorMsg(null);
    }
  }, [injectedText]);

  const ups = [
    { k: "image", label: "Screenshot", accept: "image/png,image/jpeg,image/webp", hint: "PNG, JPG" },
    { k: "voice", label: "Voice note", accept: "audio/mp3,audio/wav,audio/m4a,audio/ogg", hint: "MP3, M4A" },
    { k: "video", label: "Video Reel", accept: "video/mp4,video/quicktime,video/webm", hint: "MP4, MOV" },
  ];

  const hasContent = text.trim().length > 0 || selectedFile !== null;

  const handleFileSelect = (key: string, file: File | undefined) => {
    if (!file) return;
    setSelectedFile(file);
    setFileType(key);
    setErrorMsg(null);
  };

  const handleRunCheck = async () => {
    if (!hasContent || loading) return;
    setLoading(true);
    setErrorMsg(null);

    try {
      let result: CheckResult;
      if (selectedFile) {
        result = await checkMedia(selectedFile, lang);
      } else {
        result = await checkText(text.trim(), lang);
      }
      onResult(result);
      const resEl = document.getElementById("result");
      if (resEl) {
        resEl.scrollIntoView({ behavior: "smooth" });
      }
    } catch (err: any) {
      console.error("Check failed:", err);
      setErrorMsg(
        err.message ||
          "Could not analyze media file. Please paste the message text directly into the box for instant model analysis."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="mx-auto max-w-7xl px-5 py-24 md:px-8 md:py-32">
      <SecHead
        id="check"
        n="01"
        label="Investment scam check"
        title={
          <>
            <span className="text-muted-foreground">/</span> Show us the message.
            <br />
            We'll show you the risk.
          </>
        }
      />

      <div className="mt-14 grid border border-border md:grid-cols-12">
        <R className="border-b border-border p-6 md:col-span-7 md:border-b-0 md:border-r md:p-8">
          <div className="flex items-center justify-between">
            <label htmlFor="msg" className="label-mono text-muted-foreground">
              // 001 · Paste message, SMS, or Telegram tip
            </label>
            {text && (
              <button
                onClick={() => setText("")}
                className="label-mono text-xs text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            )}
          </div>

          <textarea
            id="msg"
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              setErrorMsg(null);
            }}
            rows={8}
            placeholder={
              'e.g. "Join our VIP Telegram group. Guaranteed 35% monthly returns on BankNifty tips! Pay registration fee Rs 5,000 to trade@ybl right now..."'
            }
            className="mt-4 w-full resize-none bg-transparent text-xl leading-snug outline-none placeholder:text-muted-foreground/60"
          />

          <div className="mt-2 h-px w-full bg-border">
            <div
              className="h-px bg-accent transition-all duration-500"
              style={{ width: `${Math.min(100, text.length / 2)}%` }}
            />
          </div>

          {errorMsg && (
            <div className="mt-4 border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              <strong>Notice:</strong> {errorMsg}
            </div>
          )}
        </R>

        <div className="flex flex-col md:col-span-5">
          {ups.map((u, i) => (
            <R key={u.k} d={i * 100} className="border-b border-border">
              <label
                className={`group flex cursor-pointer items-center justify-between gap-4 p-6 transition-colors hover:bg-secondary ${
                  fileType === u.k && selectedFile ? "bg-secondary" : ""
                }`}
              >
                <div>
                  <span className="label-mono text-muted-foreground">// 00{i + 2}</span>
                  <p
                    className={`mt-1 text-lg ${
                      fileType === u.k && selectedFile ? "text-accent font-medium" : ""
                    }`}
                  >
                    {u.label}
                  </p>
                  <p className="truncate text-sm text-muted-foreground max-w-[200px]">
                    {fileType === u.k && selectedFile ? selectedFile.name : u.hint}
                  </p>
                </div>
                <span className="grid h-10 w-10 shrink-0 place-items-center border border-border text-lg transition-all group-hover:border-foreground group-hover:bg-primary group-hover:text-primary-foreground">
                  {fileType === u.k && selectedFile ? "✓" : "+"}
                </span>
                <input
                  type="file"
                  accept={u.accept}
                  className="sr-only"
                  onChange={(e) => handleFileSelect(u.k, e.target.files?.[0])}
                />
              </label>
            </R>
          ))}

          <div className="dot-grid flex flex-1 items-end p-6">
            <button
              disabled={!hasContent || loading}
              onClick={handleRunCheck}
              className={`${btnDark} w-full`}
            >
              <span>
                {loading ? "■ Model Analyzing" : "■ Check now"}
                {loading && <span className="blink">_</span>}
              </span>
              <Arrow />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

function Result({ result, lang }: { result: CheckResult | null; lang: string }) {
  const [speaking, setSpeaking] = useState(false);

  // Default fallback if user has not run check yet
  const res: CheckResult = result ?? {
    request_id: "demo-sample",
    language: "en",
    verdict: "strong_red_flags",
    score: 0.95,
    reasons: [
      {
        code: "guaranteed_returns",
        severity: "high",
        text: "Promises guaranteed or risk-free returns. No genuine investment can guarantee profit.",
        evidence: "Guaranteed 35% monthly returns",
        source: "rule",
      },
      {
        code: "upfront_payment_request",
        severity: "high",
        text: "Demands upfront registration fees before allowing participation.",
        evidence: "Pay registration fee Rs 5,000",
        source: "rule",
      },
      {
        code: "personal_upi_payment",
        severity: "high",
        text: "Directs payment to a personal UPI handle instead of an authorized broker account.",
        evidence: "trade@ybl",
        source: "rule",
      },
      {
        code: "model_high_risk",
        severity: "high",
        text: "Machine learning classifier identified strong linguistic patterns found in known investment fraud.",
        evidence: "guaranteed, profit, upitoken, vip",
        source: "model",
      },
    ],
    note: "Do not pay or share OTP/PIN. Check with an official source.",
    disclaimer:
      "Ruko is an automated educational tool for scam detection. It is not financial advice.",
    text: "Sample: Guaranteed 35% monthly returns. Send Rs 5,000 to trade@ybl now!",
    source: "text",
    input_source: "text",
    model: {
      available: true,
      score: 0.951,
      top_words: ["guaranteed", "upitoken", "monthly", "vip"],
      calming_words: [],
    },
  };

  const riskPct = Math.round(res.score * 100);

  const verdictLabel =
    res.verdict === "strong_red_flags"
      ? "LIKELY SCAM"
      : res.verdict === "cannot_verify"
      ? "CAUTION / UNVERIFIED"
      : res.verdict === "out_of_scope"
      ? "ADVICE QUERY"
      : "NO RED FLAGS";

  const toneClass =
    res.verdict === "strong_red_flags"
      ? "bg-destructive"
      : res.verdict === "cannot_verify"
      ? "bg-warning"
      : res.verdict === "out_of_scope"
      ? "bg-cyan-500"
      : "bg-success";

  const handleReadAloud = async () => {
    if (speaking) {
      if ("speechSynthesis" in window) speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }

    try {
      setSpeaking(true);
      const speakRes = await speakVerdict(res.verdict, lang);

      if (speakRes.audio_url) {
        const audio = new Audio(speakRes.audio_url);
        audio.onended = () => setSpeaking(false);
        audio.onerror = () => setSpeaking(false);
        await audio.play();
        return;
      }

      // Browser Web Speech fallback
      if ("speechSynthesis" in window) {
        const textToSpeak = speakRes.text || res.note;
        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        utterance.lang = speakRes.lang_code || (lang === "hi" ? "hi-IN" : lang === "gu" ? "gu-IN" : "en-IN");
        utterance.onend = () => setSpeaking(false);
        utterance.onerror = () => setSpeaking(false);
        speechSynthesis.speak(utterance);
      } else {
        setSpeaking(false);
      }
    } catch (err) {
      console.warn("Read aloud error, using fallback SpeechSynthesis:", err);
      if ("speechSynthesis" in window) {
        const u = new SpeechSynthesisUtterance(res.note);
        u.onend = () => setSpeaking(false);
        speechSynthesis.speak(u);
      } else {
        setSpeaking(false);
      }
    }
  };

  return (
    <section className="bg-ink text-ink-foreground">
      <div className="mx-auto max-w-7xl px-5 py-24 md:px-8 md:py-32">
        <R>
          <div
            id="result"
            className="flex items-center gap-3 label-mono text-ink-muted scroll-mt-24"
          >
            <span>[N.02/05]</span>
            <span className="h-px w-8 bg-ink-border" />
            <span>&gt; Analysis result {result ? "· live backend" : "· sample"}</span>
            <span className="h-px flex-1 bg-ink-border" />
          </div>
        </R>

        <div key={res.request_id} className="mt-12 grid gap-12 md:grid-cols-12">
          <R className="md:col-span-5">
            <p className="label-mono text-ink-muted">Verdict & Risk Assessment</p>
            <p className="mt-3 font-pixel text-6xl font-bold leading-none md:text-7xl lg:text-8xl">
              {verdictLabel}
            </p>

            <div className="mt-10 flex items-end justify-between border-b border-ink-border pb-3">
              <span className="label-mono text-ink-muted">ML Model Risk Score</span>
              <span className="text-5xl tracking-tight">
                {riskPct}
                <span className="text-xl text-ink-muted">/100</span>
              </span>
            </div>

            <div
              className="mt-4 grid grid-cols-20 gap-1"
              style={{ gridTemplateColumns: "repeat(20, 1fr)" }}
            >
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={i}
                  className={`h-6 transition-all duration-500 ${
                    i < riskPct / 5 ? toneClass : "bg-ink-border"
                  }`}
                  style={{ transitionDelay: `${i * 35}ms` }}
                />
              ))}
            </div>

            <div className="mt-8 border border-ink-border p-4 bg-ink/50">
              <p className="label-mono text-accent text-xs">// Model Diagnostic</p>
              <div className="mt-2 text-sm text-ink-muted leading-relaxed">
                <p><strong>Status:</strong> {res.model?.available ? "Active ML Classifier" : "Heuristic Rules"}</p>
                {res.model?.top_words && res.model.top_words.length > 0 && (
                  <p className="mt-1">
                    <strong>High-risk terms:</strong>{" "}
                    <span className="font-mono text-destructive">
                      {res.model.top_words.slice(0, 4).join(", ")}
                    </span>
                  </p>
                )}
              </div>
            </div>

            <p className="mt-6 text-lg leading-snug text-ink-muted">{res.note}</p>

            <div className="mt-8 flex flex-wrap gap-4">
              <button onClick={handleReadAloud} className={btnLight}>
                {speaking ? "■ Stop speaking" : "▷ Read aloud"} <Arrow />
              </button>
              <a
                href="#pause"
                className="inline-flex items-center gap-2 border border-ink-border px-4 py-3 label-mono text-ink-foreground hover:bg-ink-foreground hover:text-ink transition-colors"
              >
                ◷ Pause 24h
              </a>
            </div>
          </R>

          <div className="md:col-span-7">
            <p className="label-mono text-ink-muted">
              Identified Red Flags · {res.reasons.length}
            </p>
            <div className="mt-4 border-t border-ink-border">
              {res.reasons.length === 0 ? (
                <div className="py-8 text-ink-muted">
                  No explicit red-flag rules triggered for this message.
                </div>
              ) : (
                res.reasons.map((flag, i) => (
                  <R key={flag.code + i} d={i * 80}>
                    <div className="group grid grid-cols-[auto_1fr] gap-5 border-b border-ink-border py-5 transition-colors hover:bg-ink-foreground/5">
                      <span className="label-mono text-accent">
                        // 00{i + 1} [{flag.source.toUpperCase()}]
                      </span>
                      <div>
                        <p className="text-xl font-medium">{flag.text}</p>
                        {flag.evidence && (
                          <p className="mt-2 font-mono text-sm text-destructive">
                            Matched: &ldquo;{flag.evidence}&rdquo;
                          </p>
                        )}
                      </div>
                    </div>
                  </R>
                ))
              )}
            </div>

            {res.text && (
              <R d={300}>
                <p className="mt-10 label-mono text-ink-muted">Analyzed Message Text</p>
                <blockquote className="mt-4 border border-ink-border p-6 font-mono text-sm leading-relaxed text-ink-muted">
                  &ldquo;{res.text}&rdquo;
                </blockquote>
              </R>
            )}

            <p className="mt-6 text-xs text-ink-muted/70 leading-relaxed">{res.disclaimer}</p>
          </div>
        </div>
      </div>
    </section>
  );
}

const SEARCH_SUGGESTIONS = [
  "Zerodha",
  "Groww",
  "Angel One",
  "Upstox",
  "ICICI Securities",
  "HDFC Securities",
  "Kotak Securities",
  "Motilal Oswal",
  "5paisa",
  "Sharekhan",
];

function Sebi() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<RegistryMatch[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setSearched(false);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const resp = await lookupRegistry(query.trim());
        setResults(resp.matches);
        setSelectedIndex(0);
        setSearched(true);
      } catch (err) {
        console.error("Registry lookup failed:", err);
      } finally {
        setLoading(false);
      }
    }, 280);

    return () => clearTimeout(timer);
  }, [query]);

  const selectedItem = results[selectedIndex] ?? null;

  return (
    <section className="mx-auto max-w-7xl px-5 py-24 md:px-8 md:py-32">
      <SecHead
        id="sebi"
        n="03"
        label="SEBI Intermediary Verification"
        title={
          <>
            Is your adviser <span className="font-mono text-accent">[SEBI registered]</span>?
          </>
        }
      />

      <div className="mt-12 border-y border-border bg-secondary py-4" aria-label="Names people search for">
        <div className="mx-auto mb-3 flex max-w-7xl items-center gap-3 px-5 label-mono text-muted-foreground md:px-8">
          <span className="h-2 w-2 bg-accent" aria-hidden="true" />
          <span>Quick search 6,583+ official SEBI intermediaries</span>
          <span className="ml-auto hidden sm:inline">Instant local snapshot (0ms) ↗</span>
        </div>
        <div className="flex flex-wrap gap-2 px-5 md:px-8">
          {SEARCH_SUGGESTIONS.map((name) => (
            <button
              key={name}
              onClick={() => setQuery(name)}
              className="border border-border bg-background px-3 py-1.5 label-mono text-xs transition-colors hover:border-accent hover:text-accent"
            >
              {name}
            </button>
          ))}
        </div>
      </div>

      <R d={100} className="mt-10">
        <div className="flex items-center gap-3 border-b-2 border-foreground pb-3 transition-colors focus-within:border-accent">
          <span className="label-mono text-muted-foreground">&gt;</span>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type broker/adviser name or SEBI reg no (e.g. INZ000031633, Zerodha, Groww)"
            className="w-full bg-transparent text-2xl outline-none placeholder:text-muted-foreground/60 md:text-3xl"
          />
          {loading && <span className="label-mono text-sm text-accent blink">Searching...</span>}
        </div>
      </R>

      <div className="mt-10 grid border border-border md:grid-cols-2">
        <div className="border-b border-border md:border-b-0 md:border-r">
          <p className="border-b border-border px-6 py-3 label-mono text-muted-foreground flex justify-between">
            <span>Official SEBI matches</span>
            <span>{results.length} found</span>
          </p>

          {searched && results.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <p className="text-lg">No SEBI intermediary found matching &ldquo;{query}&rdquo;</p>
              <p className="mt-2 text-sm text-destructive font-mono">
                WARNING: Unregistered entity. Do not send funds or follow stock tips.
              </p>
            </div>
          ) : results.length === 0 ? (
            <div className="p-8 text-muted-foreground">
              Search above or tap one of the quick suggestions to inspect verified SEBI credentials.
            </div>
          ) : (
            results.map((item, i) => (
              <button
                key={item.reg_no + i}
                onClick={() => setSelectedIndex(i)}
                className={`flex w-full items-center justify-between gap-4 border-b border-border px-6 py-5 text-left transition-colors last:border-b-0 hover:bg-secondary ${
                  selectedIndex === i ? "bg-secondary" : ""
                }`}
              >
                <div>
                  <p className="text-lg font-medium">{item.name}</p>
                  <p className="font-mono text-sm text-muted-foreground">{item.reg_no}</p>
                </div>
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    item.status.toLowerCase() === "active" ? "bg-success" : "bg-destructive"
                  }`}
                />
              </button>
            ))
          )}
        </div>

        <div className="dot-grid p-6 md:p-8">
          <p className="label-mono text-muted-foreground">Registration Verification Card</p>
          {selectedItem ? (
            <div>
              <dl className="mt-6 divide-y divide-border bg-background border border-border">
                <div className="flex justify-between gap-4 p-4">
                  <dt className="label-mono text-muted-foreground">Entity Name</dt>
                  <dd className="text-right font-medium">{selectedItem.name}</dd>
                </div>
                <div className="flex justify-between gap-4 p-4">
                  <dt className="label-mono text-muted-foreground">SEBI Reg. No</dt>
                  <dd className="text-right font-mono text-accent">{selectedItem.reg_no}</dd>
                </div>
                <div className="flex justify-between gap-4 p-4">
                  <dt className="label-mono text-muted-foreground">Category</dt>
                  <dd className="text-right">{selectedItem.category}</dd>
                </div>
                <div className="flex justify-between gap-4 p-4">
                  <dt className="label-mono text-muted-foreground">Match Score</dt>
                  <dd className="text-right font-mono">{selectedItem.similarity}%</dd>
                </div>
              </dl>

              <div
                className={`mt-6 flex items-center justify-between px-5 py-4 label-mono text-primary-foreground ${
                  selectedItem.status.toLowerCase() === "active" ? "bg-success" : "bg-destructive"
                }`}
              >
                <span>Registration Status</span>
                <span>✓ {selectedItem.status.toUpperCase()} SEBI INTERMEDIARY</span>
              </div>
            </div>
          ) : (
            <div className="mt-6 border border-dashed border-border p-8 text-center text-muted-foreground">
              Select an entity from the list to view its registered SEBI certificate information.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function Pause({ verdict, lang }: { verdict: string; lang: string }) {
  const [amt, setAmt] = useState(50000);
  const [checked, setChecked] = useState<number[]>([]);
  const [plan, setPlan] = useState<PausePlanResponse | null>(null);

  useEffect(() => {
    const fetchPlan = async () => {
      try {
        const p = await getPausePlan({
          verdict: (verdict as any) || "strong_red_flags",
          amount: amt,
          monthlyExpenses: 25000,
          language: lang,
        });
        setPlan(p);
      } catch (err) {
        console.warn("Failed to load pause plan from backend:", err);
      }
    };
    fetchPlan();
  }, [verdict, amt, lang]);

  const questions =
    plan?.decision_questions || [
      "Would I still invest if no one was rushing me?",
      "Can I find this adviser on the official SEBI site myself?",
      "Could I afford to lose all of this money?",
    ];

  const handleShare = async () => {
    const shareText =
      plan?.share_text ||
      `I am pausing for 24 hours before transferring ₹${amt.toLocaleString(
        "en-IN"
      )}. Can you check this investment offer with me? — via Ruko`;

    if (navigator.share) {
      try {
        await navigator.share({ text: shareText });
      } catch {
        /* user cancelled */
      }
    } else if (plan?.share_link) {
      window.open(plan.share_link, "_blank");
    } else {
      window.open(`https://wa.me/?text=${encodeURIComponent(shareText)}`, "_blank");
    }
  };

  const handleRemind = () => {
    if (plan?.calendar_data_uri) {
      const a = document.createElement("a");
      a.href = plan.calendar_data_uri;
      a.download = "ruko-cooling-off-reminder.ics";
      a.click();
      return;
    }

    // Fallback ICS generator
    const d = new Date(Date.now() + 864e5).toISOString().replace(/[-:]|\.\d{3}/g, "");
    const ics = `BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nDTSTART:${d}\nDTEND:${d}\nSUMMARY:Ruko: Revisit investment decision\nDESCRIPTION:24-hour cooling-off reminder: Verify claimed adviser with SEBI.\nEND:VEVENT\nEND:VCALENDAR`;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([ics], { type: "text/calendar" }));
    a.download = "ruko-reminder.ics";
    a.click();
  };

  return (
    <section className="border-y border-border bg-secondary">
      <div className="mx-auto max-w-7xl px-5 py-24 md:px-8 md:py-32">
        <SecHead
          id="pause"
          n="04"
          label="24-Hour Cooling-Off Pause"
          title={
            <>
              Wait <span className="font-pixel font-bold">24:00:00</span>
              <br />
              before you transfer a single rupee.
            </>
          }
        />

        <div className="mt-14 grid gap-12 md:grid-cols-2">
          <div>
            <R>
              <p className="max-w-md text-lg text-muted-foreground">
                Scammers rely on manufactured urgency. Genuine market opportunities will still be
                there tomorrow. Reflect honestly:
              </p>
            </R>

            <div className="mt-8 border-t border-border">
              {questions.map((q, i) => {
                const on = checked.includes(i);
                return (
                  <R key={q} d={i * 80}>
                    <button
                      onClick={() =>
                        setChecked((c) => (on ? c.filter((x) => x !== i) : [...c, i]))
                      }
                      className="flex w-full items-center gap-5 border-b border-border py-5 text-left transition-colors hover:text-accent"
                    >
                      <span
                        className={`grid h-6 w-6 shrink-0 place-items-center border text-xs transition-all ${
                          on
                            ? "border-accent bg-accent text-accent-foreground"
                            : "border-foreground"
                        }`}
                      >
                        {on && "✓"}
                      </span>
                      <span className="text-xl">{q}</span>
                    </button>
                  </R>
                );
              })}
            </div>
          </div>

          <R d={150}>
            <div className="border border-border bg-background p-6 md:p-8">
              <p className="label-mono text-muted-foreground">Potential Loss Arithmetic</p>
              <p className="mt-4 text-6xl tracking-tight md:text-7xl font-bold">
                ₹{amt.toLocaleString("en-IN")}
              </p>

              <input
                type="range"
                min={5000}
                max={1000000}
                step={5000}
                value={amt}
                onChange={(e) => setAmt(+e.target.value)}
                className="mt-6 w-full accent-accent"
                aria-label="Amount"
              />

              <p className="mt-4 text-muted-foreground">
                {plan?.loss_arithmetic?.sentence ||
                  `≈ ${Math.round(amt / 25000)} months of an average Indian household's living expenses.`}
              </p>

              <div className="mt-8 grid gap-3 sm:grid-cols-2">
                <button onClick={handleShare} className={btnDark}>
                  ↗ Share with family <Arrow />
                </button>
                <button
                  onClick={handleRemind}
                  className="group inline-flex items-center justify-between gap-4 border border-foreground px-5 py-3.5 label-mono transition-colors hover:bg-primary hover:text-primary-foreground"
                >
                  ◷ Remind in 24h (.ics) <Arrow />
                </button>
              </div>
            </div>
          </R>
        </div>
      </div>
    </section>
  );
}

function Recovery({ lang }: { lang: string }) {
  const [steps, setSteps] = useState<RecoveryChecklistStep[]>([]);

  useEffect(() => {
    const fetchRecovery = async () => {
      try {
        const data = await getRecoveryResources(lang);
        setSteps(data.checklist);
      } catch (err) {
        console.warn("Using fallback recovery checklist:", err);
        setSteps([
          {
            step: 1,
            priority: "immediate",
            action: "Call National Cyber Crime Helpline 1930",
            description: "Call immediately to freeze financial transaction trails.",
            contact: "1930",
            verify: true,
          },
          {
            step: 2,
            priority: "immediate",
            action: "Notify Bank Fraud Cell",
            description: "Request transaction recall and account freeze.",
            contact: "Bank Customer Care",
            verify: true,
          },
          {
            step: 3,
            priority: "within_24h",
            action: "File Complaint on Cybercrime Portal",
            description: "Submit screenshots and UTR reference numbers on cybercrime.gov.in.",
            contact: "https://cybercrime.gov.in",
            verify: true,
          },
          {
            step: 4,
            priority: "if_sebi_claimed",
            action: "File Grievance on SEBI SCORES",
            description: "Report impersonation of SEBI intermediaries directly to the regulator.",
            contact: "https://scores.sebi.gov.in",
            verify: true,
          },
        ]);
      }
    };
    fetchRecovery();
  }, [lang]);

  return (
    <section className="mx-auto max-w-7xl px-5 py-24 md:px-8 md:py-32">
      <SecHead
        id="recovery"
        n="05"
        label="Emergency Fraud Recovery"
        title={
          <>
            Already transferred money?{" "}
            <span className="text-muted-foreground">Act in the golden hour.</span>
          </>
        }
      />

      <div className="mt-14 grid border-l border-t border-border sm:grid-cols-2 lg:grid-cols-4">
        {steps.map((st, i) => {
          const isHelpline = st.contact === "1930";
          const isUrl = st.contact.startsWith("http");

          return (
            <R key={st.step} d={i * 100} className="border-b border-r border-border">
              <div
                className={`group flex h-full min-h-72 flex-col p-6 transition-colors ${
                  isHelpline
                    ? "bg-destructive text-destructive-foreground"
                    : "hover:bg-primary hover:text-primary-foreground"
                }`}
              >
                <span className="label-mono opacity-70">// STEP 00{st.step}</span>
                <p className={`mt-6 font-pixel font-bold leading-none ${isHelpline ? "text-6xl" : "text-4xl"}`}>
                  {isHelpline ? "1930" : `0${st.step}`}
                </p>
                <p className="mt-auto pt-6 text-xl font-medium">{st.action}</p>
                <p className="mt-2 text-sm opacity-80 leading-relaxed">{st.description}</p>

                <div className="mt-6">
                  {isHelpline ? (
                    <a
                      href="tel:1930"
                      className="inline-flex items-center gap-2 label-mono bg-destructive-foreground text-destructive px-3 py-2 text-sm font-bold"
                    >
                      Call 1930 Now <Arrow />
                    </a>
                  ) : isUrl ? (
                    <a
                      href={st.contact}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 label-mono border-b border-current pb-1"
                    >
                      Visit Official Portal <Arrow />
                    </a>
                  ) : (
                    <span className="label-mono text-xs opacity-75">{st.contact}</span>
                  )}
                </div>
              </div>
            </R>
          );
        })}
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="relative overflow-hidden bg-card/60 text-foreground border-t border-border">
      <div className="absolute inset-0 grid-lines opacity-20" />
      <div className="relative mx-auto flex max-w-7xl flex-col gap-10 px-5 pb-8 pt-16 md:px-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 border-b border-border pb-8">
          <RukoLogo size={36} />
          <div className="flex flex-wrap items-center gap-6 label-mono text-xs text-muted-foreground">
            <Link to="/" className="hover:text-foreground transition-colors">
              Checker
            </Link>
            <Link to="/model-stats" className="hover:text-cyan-400 text-cyan-500 font-semibold transition-colors">
              Model Thresholds & Diagnostics
            </Link>
            <a href="#sebi" className="hover:text-foreground transition-colors">
              SEBI Registry
            </a>
            <a href="#recovery" className="hover:text-foreground transition-colors">
              Recovery 1930
            </a>
          </div>
        </div>
        <p className="font-pixel text-[24vw] font-bold leading-[0.75] md:text-[14rem] text-muted/30 select-none">
          RUKO
        </p>
        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-border/80 pt-6 label-mono text-muted-foreground text-xs">
          <span className="flex items-center gap-2">
            © 2026 Ruko AI · Retail Investor Protection Architecture
          </span>
          <span>
            Calibrated Model Threshold 0.410 · 6,583+ Offline SEBI Registry Intermediaries
          </span>
        </div>
      </div>
    </footer>
  );
}

function Index() {
  const [lang, setLang] = useState("en");
  const [checkResult, setCheckResult] = useState<CheckResult | null>(null);
  const [injectedText, setInjectedText] = useState<string>("");

  useReveal();

  return (
    <main className="min-h-screen bg-background text-foreground transition-colors duration-300">
      <Nav lang={lang} onLangChange={setLang} />
      <Hero />
      <ContinuousThreatStream />
      <ScamThreatCarousel
        onSelectSample={(sample) => {
          setInjectedText(sample);
          const checkEl = document.getElementById("check");
          if (checkEl) checkEl.scrollIntoView({ behavior: "smooth" });
        }}
      />
      <Check lang={lang} onResult={setCheckResult} injectedText={injectedText} />
      <Result result={checkResult} lang={lang} />
      <Sebi />
      <Pause verdict={checkResult?.verdict || "strong_red_flags"} lang={lang} />
      <Recovery lang={lang} />
      <Footer />
    </main>
  );
}
