import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { RukoLogo } from "../components/RukoLogo";
import { ThemeToggle } from "../components/ThemeToggle";
import { ChatBot } from "../components/ChatBot";
import { InsightCharts } from "../components/InsightCharts";
import { VoiceInput } from "../components/VoiceInput";
import {
  checkText,
  checkMedia,
  checkUrl,
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

function useReveal() {}

const R = ({
  children,
  className = "",
}: {
  children: ReactNode;
  d?: number;
  className?: string;
}) => <div className={className}>{children}</div>;

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
    <path
      d="M7 6h10M7 10h8M9 6v8c0 0 6 0 6-4s-6-4-6-4l7 10"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
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

function Nav({ lang, onLangChange }: { lang: string; onLangChange: (l: string) => void }) {
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
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 border-b border-border/70 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/70 ${
        scrolled
          ? "shadow-lg shadow-black/10 dark:shadow-cyan-950/20 bg-background/90"
          : "shadow-sm"
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
            to="/explain"
            className="inline-flex items-center gap-1.5 rounded-md border border-primary/40 bg-primary/10 px-3 py-1 label-mono text-xs text-primary transition-all hover:bg-primary hover:text-primary-foreground font-semibold shadow-sm"
          >
            <span>✦ Explain Doc</span>
          </Link>
          <Link
            to="/model-stats"
            className="ml-2 inline-flex items-center gap-1.5 rounded-md border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 label-mono text-xs text-cyan-600 dark:text-cyan-400 transition-all hover:bg-cyan-500 hover:text-slate-950 font-semibold shadow-sm"
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
            to="/explain"
            onClick={() => setOpen(false)}
            className="border-b border-border/60 py-3 text-base font-medium text-primary flex items-center justify-between"
          >
            <span>Explain a Document</span>
            <span className="label-mono text-xs px-2 py-0.5 rounded bg-primary/20 font-mono">
              NEW
            </span>
          </Link>
          <Link
            to="/model-stats"
            onClick={() => setOpen(false)}
            className="border-b border-border/60 py-3 text-base font-medium text-cyan-600 dark:text-cyan-400 flex items-center justify-between"
          >
            <span>Model Thresholds & Stats</span>
            <span className="label-mono text-xs px-2 py-0.5 rounded bg-cyan-500/20 font-mono">
              0.410
            </span>
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
                  lang === o.code
                    ? "bg-primary text-primary-foreground border-primary"
                    : "border-border text-muted-foreground"
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
    <section
      id="top"
      className="relative overflow-hidden bg-background text-foreground transition-colors duration-300"
    >
      <div className="absolute inset-0 bg-glow pointer-events-none opacity-70" />
      <div className="absolute inset-0 grid-lines opacity-20 dark:opacity-40 pointer-events-none" />
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
            <p className="max-w-md text-lg leading-snug text-muted-foreground md:text-xl">
              Got an investment tip, WhatsApp message, or high-yield offer? Paste it or upload it.
              Ruko scores the scam risk with machine learning and verifies registration against
              6,583+ SEBI entities before your money moves.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a href="#check" className={btnDark}>
                ■ Check an offer <Arrow />
              </a>
              <Link
                to="/explain"
                className="group inline-flex items-center justify-between gap-3 border border-primary/40 bg-primary/10 px-5 py-3.5 label-mono text-primary transition-all hover:bg-primary hover:text-primary-foreground active:scale-[.98]"
              >
                <span>✦ Explain a Document</span>
                <span className="transition-transform group-hover:translate-x-0.5">→</span>
              </Link>
            </div>
          </R>
          <R d={200} className="hidden md:flex md:justify-end md:pt-10">
            <p className="label-mono leading-relaxed text-muted-foreground">
              ✦ Pause.
              <br />
              &nbsp;&nbsp;&nbsp;&nbsp;Verify.
              <br />
              &nbsp;&nbsp;Then invest. +
            </p>
          </R>
        </div>

        <div className="mt-20 flex flex-wrap items-end gap-x-6 md:mt-28">
          <h1 className="font-pixel text-[24vw] font-bold leading-[0.78] tracking-tight md:text-[18vw] lg:text-[15rem] text-foreground">
            RUKO<span className="blink text-accent">_</span>
          </h1>
          <p className="pb-2 text-4xl font-light tracking-tight md:text-6xl text-foreground">
            Stop. Check.
            <br />
            Stay safe.
          </p>
        </div>
      </div>

      <div className="relative overflow-hidden border-t border-border py-2.5">
        <div className="marquee flex w-max gap-12 label-mono text-muted-foreground">
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
  const [checkMode, setCheckMode] = useState<"message" | "reel">("message");
  const [text, setText] = useState("");
  const [reelUrl, setReelUrl] = useState("");
  const [amount, setAmount] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [ocrProgress, setOcrProgress] = useState<number | null>(null);

  useEffect(() => {
    if (injectedText) {
      if (injectedText.includes("instagram.com") || injectedText.includes("instagr.am")) {
        setCheckMode("reel");
        setReelUrl(injectedText);
      } else {
        setText(injectedText);
      }
      setSelectedFile(null);
      setFileType(null);
      setErrorMsg(null);
    }
  }, [injectedText]);

  const ups = [
    { k: "image", label: "Screenshot", accept: "image/png,image/jpeg,image/webp,image/*", hint: "PNG, JPG, WEBP" },
    { k: "voice", label: "Voice note", accept: "audio/mp3,audio/wav,audio/m4a,audio/ogg,audio/webm,audio/*", hint: "MP3, M4A, WAV, WEBM" },
    { k: "video", label: "Instagram Reel / Video", accept: "video/mp4,video/quicktime,video/webm,video/*", hint: "Reel MP4, MOV, WEBM" },
  ];

  const hasContent =
    checkMode === "reel"
      ? reelUrl.trim().length > 0
      : text.trim().length > 0 || selectedFile !== null;

  const handleFileSelect = (key: string, file: File | undefined) => {
    if (!file) return;
    setSelectedFile(file);
    setFileType(key);
    setErrorMsg(null);
    setOcrProgress(null);
  };

  const handleRunCheck = async () => {
    if (!hasContent || loading) return;
    setLoading(true);
    setErrorMsg(null);
    setOcrProgress(null);

    const parsedAmt = amount.trim() ? parseFloat(amount) : undefined;

    try {
      let result: CheckResult;
      if (checkMode === "reel") {
        result = await checkUrl(reelUrl.trim(), lang, parsedAmt);
      } else if (selectedFile) {
        result = await checkMedia(selectedFile, lang, parsedAmt, (p) => setOcrProgress(p));
      } else if (isReelUrl) {
        result = await checkUrl(text.trim(), lang, parsedAmt);
      } else {
        result = await checkText(text.trim(), lang, parsedAmt);
      }
      onResult(result);
      setOcrProgress(null);
      const resEl = document.getElementById("result");
      if (resEl) {
        resEl.scrollIntoView({ behavior: "smooth" });
      }
    } catch (err: any) {
      console.error("Check failed:", err);
      setErrorMsg(
        err.message ||
          (checkMode === "reel"
            ? "Could not analyze Instagram Reel. Verify the URL is public or try again."
            : "Could not analyze media file. Please paste the message text directly into the box for instant model analysis."),
      );
    } finally {
      setLoading(false);
      setOcrProgress(null);
    }
  };

  const isReelUrl = text.includes("instagram.com") || text.includes("instagr.am");

  const loadingLabel =
    ocrProgress !== null
      ? `Reading image text… ${ocrProgress}%`
      : loading && checkMode === "reel"
      ? "Extracting Reel Video & Audio…"
      : loading && selectedFile
      ? "Analyzing File…"
      : loading && isReelUrl
      ? "Extracting Reel Video & Audio…"
      : loading
      ? "Analyzing Message…"
      : checkMode === "reel"
      ? "Scan Instagram Reel for Fraud"
      : "Scan Message for Fraud";

  return (
    <section className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
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

      {/* Mode Switcher Tabs */}
      <div className="mt-10 flex flex-wrap items-center gap-2.5">
        <button
          type="button"
          onClick={() => {
            setCheckMode("message");
            setErrorMsg(null);
          }}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl label-mono text-xs font-semibold transition-all ${
            checkMode === "message"
              ? "bg-cyan-500/15 text-cyan-400 border border-cyan-500/50 shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-secondary/60 border border-border"
          }`}
        >
          <span>💬</span>
          <span>Message & Chat Check</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setCheckMode("reel");
            setErrorMsg(null);
          }}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl label-mono text-xs font-semibold transition-all ${
            checkMode === "reel"
              ? "bg-gradient-to-r from-pink-500/20 via-purple-500/20 to-cyan-500/20 text-pink-400 dark:text-pink-300 border border-pink-500/50 shadow-md shadow-pink-500/10"
              : "text-muted-foreground hover:text-foreground hover:bg-secondary/60 border border-border"
          }`}
        >
          <span>🎬</span>
          <span>Instagram Reel Scanner</span>
          <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-pink-500/25 text-pink-300 border border-pink-500/30">
            Dedicated URL
          </span>
        </button>
      </div>

      {checkMode === "reel" ? (
        /* Dedicated Instagram Reel Scanner View */
        <div className="mt-6 border border-pink-500/30 bg-card rounded-2xl overflow-hidden shadow-2xl transition-all">
          <div className="p-6 md:p-10 border-b border-border bg-gradient-to-r from-pink-500/10 via-purple-500/10 to-cyan-500/5">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
              <div className="max-w-2xl">
                <div className="inline-flex items-center gap-2 rounded-full border border-pink-500/40 bg-pink-500/10 px-3 py-1 label-mono text-xs text-pink-400 mb-3">
                  <span>🎬</span>
                  <span>DEDICATED REEL FRAUD SCANNER</span>
                </div>
                <h3 className="text-2xl md:text-3xl font-bold font-mono tracking-tight text-foreground">
                  Paste Instagram Reel URL
                </h3>
                <p className="mt-2 text-sm md:text-base text-muted-foreground leading-relaxed">
                  Paste any public Instagram Reel URL. Ruko fetches the video in-memory, transcribes
                  spoken audio via AI Speech-to-Text, runs OCR across on-screen video frames, and
                  audits the claims against SEBI registry records and 12 scam heuristics.
                </p>
              </div>

              {/* Ingestion Highlights */}
              <div className="flex flex-wrap md:flex-col gap-2 shrink-0">
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs label-mono border border-border bg-background/80 text-foreground">
                  <span>🎙</span> Voiceover STT Transcript
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs label-mono border border-border bg-background/80 text-foreground">
                  <span>📺</span> On-Screen Frames OCR
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs label-mono border border-border bg-background/80 text-foreground">
                  <span>🔒</span> 100% In-Memory (Zero Disk)
                </span>
              </div>
            </div>

            {/* Reel URL Input Box */}
            <div className="mt-8">
              <label
                htmlFor="reel-url"
                className="label-mono text-xs text-muted-foreground uppercase tracking-wider font-semibold"
              >
                // Instagram Reel URL
              </label>

              <div className="mt-2 relative flex items-center">
                <div className="absolute left-4 flex items-center pointer-events-none text-pink-400">
                  <svg
                    className="w-5 h-5"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
                  </svg>
                </div>

                <input
                  id="reel-url"
                  type="url"
                  value={reelUrl}
                  onChange={(e) => {
                    setReelUrl(e.target.value);
                    setErrorMsg(null);
                  }}
                  placeholder="https://www.instagram.com/reel/C8qL9XYZ123/ or https://instagr.am/..."
                  className="w-full rounded-xl border border-pink-500/40 bg-background px-4 py-4 pl-12 pr-28 text-sm md:text-base font-mono text-foreground outline-none transition-all focus:border-pink-500 focus:ring-2 focus:ring-pink-500/20 shadow-inner"
                />

                <div className="absolute right-3 flex items-center gap-2">
                  {reelUrl && (
                    <button
                      type="button"
                      onClick={() => setReelUrl("")}
                      className="px-2 py-1 text-xs label-mono text-muted-foreground hover:text-foreground"
                    >
                      Clear
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        const clip = await navigator.clipboard.readText();
                        if (clip) {
                          setReelUrl(clip.trim());
                          setErrorMsg(null);
                        }
                      } catch (err) {
                        console.warn("Clipboard access denied:", err);
                      }
                    }}
                    className="px-3 py-1.5 text-xs label-mono rounded-lg bg-secondary hover:bg-muted border border-border text-foreground transition-all active:scale-95"
                  >
                    Paste
                  </button>
                </div>
              </div>

              {/* Quick Sample Links */}
              <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                <span className="label-mono text-muted-foreground text-[11px]">Quick Samples:</span>
                <button
                  type="button"
                  onClick={() =>
                    setReelUrl("https://www.instagram.com/reel/C8qL9XYZ123_guaranteed_profit/")
                  }
                  className="px-2.5 py-1 rounded-md text-[11px] font-mono border border-border bg-secondary/40 text-muted-foreground hover:text-pink-400 hover:border-pink-500/40 transition-colors"
                >
                  Crypto 200% Profit Reel
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setReelUrl("https://www.instagram.com/reel/C9aB8XYZ456_vip_telegram_tips/")
                  }
                  className="px-2.5 py-1 rounded-md text-[11px] font-mono border border-border bg-secondary/40 text-muted-foreground hover:text-pink-400 hover:border-pink-500/40 transition-colors"
                >
                  Unregistered VIP Telegram Tips
                </button>
              </div>
            </div>

            {/* Optional Amount & Action Bar */}
            <div className="mt-8 pt-6 border-t border-border flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <label
                  htmlFor="reel-amt"
                  className="label-mono text-xs text-muted-foreground whitespace-nowrap font-medium"
                >
                  Amount mentioned in Reel (₹ Optional):
                </label>
                <div className="relative min-w-[140px] max-w-xs">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 font-mono text-sm text-muted-foreground">
                    ₹
                  </span>
                  <input
                    id="reel-amt"
                    type="number"
                    min="0"
                    step="500"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="e.g. 50000"
                    className="w-full rounded-md border border-border bg-background px-3 py-2 pl-7 text-sm font-mono text-foreground outline-none focus:border-pink-500"
                  />
                </div>
              </div>

              {/* Action Button */}
              <button
                type="button"
                disabled={!reelUrl.trim() || loading}
                onClick={handleRunCheck}
                className="inline-flex items-center justify-center gap-2 px-8 py-3 rounded-xl font-mono font-semibold text-sm transition-all shadow-xl active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-pink-600 via-purple-600 to-indigo-600 hover:from-pink-500 hover:via-purple-500 hover:to-indigo-500 text-white shadow-pink-500/25"
              >
                <span>
                  {loadingLabel}
                  {loading && <span className="blink">_</span>}
                </span>
                <Arrow />
              </button>
            </div>

            {errorMsg && (
              <div className="mt-5 border border-destructive/50 bg-destructive/10 p-3.5 text-sm text-destructive rounded-xl">
                <strong>Notice:</strong> {errorMsg}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Universal Message, Telegram Tip & File Upload Card */
        <div className="mt-6 grid border border-border bg-card rounded-2xl overflow-hidden shadow-lg md:grid-cols-12">
          <div className="border-b border-border p-6 md:col-span-7 md:border-b-0 md:border-r md:p-8 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between gap-2">
                <label
                  htmlFor="msg"
                  className="label-mono text-xs text-muted-foreground uppercase tracking-wider font-semibold"
                >
                  // 001 · Suspicious message, SMS, or Telegram tip
                </label>
                <div className="flex items-center gap-2">
                  <VoiceInput
                    lang={lang}
                    onTranscript={(t) => {
                      setText(t);
                      setErrorMsg(null);
                    }}
                  />
                  {text && (
                    <button
                      onClick={() => setText("")}
                      className="label-mono text-xs text-muted-foreground hover:text-foreground"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              <textarea
                id="msg"
                value={text}
                onChange={(e) => {
                  setText(e.target.value);
                  setErrorMsg(null);
                }}
                rows={7}
                placeholder="e.g. Paste a message, WhatsApp tip, or investment offer..."
                className="mt-4 w-full resize-none bg-transparent text-lg md:text-xl leading-snug outline-none placeholder:text-muted-foreground/50 text-foreground font-sans"
              />

              {isReelUrl && (
                <div className="mt-3 flex items-center justify-between gap-2 rounded-xl border border-pink-500/30 bg-pink-500/10 p-3 text-xs font-mono text-pink-400">
                  <div className="flex items-center gap-2">
                    <span>🎬</span>
                    <span>Instagram Reel Link Detected</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setCheckMode("reel");
                      setReelUrl(text.trim());
                    }}
                    className="px-2.5 py-1 rounded-lg bg-pink-500 text-white font-semibold hover:bg-pink-600 transition-all text-[11px]"
                  >
                    Open in Reel Scanner →
                  </button>
                </div>
              )}
            </div>

            <div className="mt-6 border-t border-border pt-4">
              <div className="flex flex-wrap items-center gap-3">
                <label
                  htmlFor="amt"
                  className="label-mono text-xs text-muted-foreground whitespace-nowrap font-medium"
                >
                  Amount involved (₹ Optional):
                </label>
                <div className="relative flex-1 min-w-[140px] max-w-xs">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 font-mono text-sm text-muted-foreground">
                    ₹
                  </span>
                  <input
                    id="amt"
                    type="number"
                    min="0"
                    step="500"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="e.g. 25000"
                    className="w-full rounded-md border border-border bg-background px-3 py-1.5 pl-7 text-sm font-mono text-foreground outline-none focus:border-cyan-400"
                  />
                </div>
                {amount && (
                  <button
                    type="button"
                    onClick={() => setAmount("")}
                    className="label-mono text-xs text-muted-foreground hover:text-foreground"
                  >
                    Clear
                  </button>
                )}
              </div>

              {errorMsg && (
                <div className="mt-4 border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive rounded-lg">
                  <strong>Notice:</strong> {errorMsg}
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-col md:col-span-5 bg-secondary/30">
            <div className="p-4 border-b border-border bg-secondary/50">
              <span className="label-mono text-xs text-muted-foreground uppercase tracking-wider font-semibold">
                // 002 · Or Upload Media Directly
              </span>
            </div>

            {ups.map((u, i) => (
              <div key={u.k} className="border-b border-border last:border-b-0">
                <label
                  className={`group flex cursor-pointer items-center justify-between gap-4 p-5 transition-colors hover:bg-secondary ${
                    fileType === u.k && selectedFile ? "bg-secondary" : ""
                  }`}
                >
                  <div>
                    <span className="label-mono text-xs text-muted-foreground">// 00{i + 2}</span>
                    <p
                      className={`mt-0.5 text-base font-medium ${
                        fileType === u.k && selectedFile ? "text-cyan-400" : "text-foreground"
                      }`}
                    >
                      {u.label}
                    </p>
                    <p className="truncate text-xs text-muted-foreground max-w-[200px]">
                      {fileType === u.k && selectedFile ? selectedFile.name : u.hint}
                    </p>
                  </div>
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-border text-base transition-all group-hover:border-foreground group-hover:bg-primary group-hover:text-primary-foreground">
                    {fileType === u.k && selectedFile ? "✓" : "+"}
                  </span>
                  <input
                    type="file"
                    accept={u.accept}
                    className="sr-only"
                    onChange={(e) => handleFileSelect(u.k, e.target.files?.[0])}
                  />
                </label>
              </div>
            ))}

            <div className="p-6 mt-auto">
              {/* Live OCR progress bar — visible only while scanning image text */}
              {ocrProgress !== null && (
                <div className="mb-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="label-mono text-[10px] text-cyan-400">
                      OCR · Extracting text from image
                    </span>
                    <span className="label-mono text-[10px] text-cyan-400 font-bold">
                      {ocrProgress}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300"
                      style={{ width: `${ocrProgress}%` }}
                    />
                  </div>
                </div>
              )}
              <button
                disabled={!hasContent || loading}
                onClick={handleRunCheck}
                className={`${btnDark} w-full rounded-lg justify-center shadow-lg shadow-cyan-500/10`}
              >
                <span>
                  {loadingLabel}
                  {loading && <span className="blink">_</span>}
                </span>
                <Arrow />
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function Result({
  result,
  lang,
  onRunSample,
}: {
  result: CheckResult | null;
  lang: string;
  onRunSample?: (sampleText: string) => void;
}) {
  const [speaking, setSpeaking] = useState(false);

  const handleReadAloud = async () => {
    if (!result) return;
    if (speaking) {
      if ("speechSynthesis" in window) speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }

    try {
      setSpeaking(true);
      const speakRes = await speakVerdict(result.verdict, lang);

      if (speakRes.audio_url) {
        const audio = new Audio(speakRes.audio_url);
        audio.onended = () => setSpeaking(false);
        audio.onerror = () => setSpeaking(false);
        await audio.play();
        return;
      }

      // Browser Web Speech fallback
      if ("speechSynthesis" in window) {
        const textToSpeak = speakRes.text || result.note;
        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        utterance.lang =
          speakRes.lang_code || (lang === "hi" ? "hi-IN" : lang === "gu" ? "gu-IN" : "en-IN");
        utterance.onend = () => setSpeaking(false);
        utterance.onerror = () => setSpeaking(false);
        speechSynthesis.speak(utterance);
      } else {
        setSpeaking(false);
      }
    } catch (err) {
      console.warn("Read aloud error, using fallback SpeechSynthesis:", err);
      if ("speechSynthesis" in window) {
        const u = new SpeechSynthesisUtterance(result.note);
        u.onend = () => setSpeaking(false);
        speechSynthesis.speak(u);
      } else {
        setSpeaking(false);
      }
    }
  };

  return (
    <section
      id="result"
      className="border-y border-border bg-card/70 py-20 md:py-28 text-foreground transition-colors"
    >
      <div className="mx-auto max-w-7xl px-5 md:px-8">
        <div className="flex items-center gap-3 label-mono text-muted-foreground scroll-mt-24">
          <span>[N.02/05]</span>
          <span className="h-px w-8 bg-border" />
          <span>&gt; Analysis report {result ? "· live scan completed" : "· ready to scan"}</span>
          <span className="h-px flex-1 bg-border" />
        </div>

        {/* If no check has been performed yet, show clear ready state */}
        {!result ? (
          <div className="mt-12 rounded-2xl border border-dashed border-border bg-background/50 p-8 md:p-14 text-center max-w-3xl mx-auto shadow-sm">
            <div className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 mb-5">
              <span className="text-2xl font-mono">✦</span>
            </div>
            <h3 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
              Awaiting Message Scan
            </h3>
            <p className="mt-3 text-sm md:text-base text-muted-foreground max-w-lg mx-auto leading-relaxed">
              Enter suspicious text, WhatsApp tip, or upload media above and click{" "}
              <strong className="text-foreground">"Scan Message for Fraud"</strong>. Ruko will
              evaluate red flags and extract payment requests.
            </p>

            {onRunSample && (
              <div className="mt-8 pt-6 border-t border-border flex flex-wrap items-center justify-center gap-3">
                <span className="label-mono text-xs text-muted-foreground">
                  Quick Test Samples:
                </span>
                <button
                  onClick={() =>
                    onRunSample(
                      "Guaranteed 400% profit in 15 days on BankNifty jackpot. Transfer ₹5000 to trade@ybl now",
                    )
                  }
                  className="px-3 py-1.5 rounded-md border border-border bg-card hover:border-cyan-500/50 hover:text-cyan-400 text-xs label-mono transition-all"
                >
                  BankNifty Scam (₹5,000)
                </button>
                <button
                  onClick={() =>
                    onRunSample(
                      "CRITICAL: Mumbai Police Cyber Cell. 150g MDMA was seized in your parcel. Connect on Skype id: police_mumbai within 2 hours",
                    )
                  }
                  className="px-3 py-1.5 rounded-md border border-border bg-card hover:border-cyan-500/50 hover:text-cyan-400 text-xs label-mono transition-all"
                >
                  Digital Arrest Notice
                </button>
                <button
                  onClick={() =>
                    onRunSample(
                      "Parag Parikh Flexi Cap Fund monthly SIP of INR 5,000 processed via HDFC Bank on 03-Oct. NAV allotment 82.410",
                    )
                  }
                  className="px-3 py-1.5 rounded-md border border-border bg-card hover:border-emerald-500/50 hover:text-emerald-400 text-xs label-mono transition-all"
                >
                  Legitimate Mutual Fund SIP
                </button>
              </div>
            )}
          </div>
        ) : (
          <>
            <div key={result.request_id} className="mt-12 grid gap-10 lg:grid-cols-12 items-start">
              {/* Left Column: Verdict, Risk Score, Guidance */}
              <div className="lg:col-span-5 rounded-2xl border border-border bg-background p-6 md:p-8 shadow-xl">
                <div className="flex items-center justify-between pb-4 border-b border-border">
                  <span className="label-mono text-xs text-muted-foreground font-semibold">
                    ANALYSIS VERDICT
                  </span>
                  <span className="label-mono text-[11px] font-mono text-muted-foreground">
                    ID: {result.request_id.slice(0, 8)}
                  </span>
                </div>

                {/* Prominent Verdict Banner */}
                <div
                  className={`mt-6 p-4 rounded-xl border flex items-center gap-3 ${
                    result.verdict === "strong_red_flags"
                      ? "border-red-500/40 bg-red-500/10 text-red-400"
                      : result.verdict === "cannot_verify"
                        ? "border-amber-500/40 bg-amber-500/10 text-amber-400"
                        : result.verdict === "out_of_scope"
                          ? "border-cyan-500/40 bg-cyan-500/10 text-cyan-400"
                          : "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                  }`}
                >
                  <div className="text-xl">
                    {result.verdict === "strong_red_flags"
                      ? "✖"
                      : result.verdict === "no_red_flags_found"
                        ? "✔"
                        : "✦"}
                  </div>
                  <div>
                    <div className="text-sm font-mono font-bold tracking-wider uppercase">
                      {result.verdict === "strong_red_flags"
                        ? "HIGH RISK · FINANCIAL SCAM DETECTED"
                        : result.verdict === "cannot_verify"
                          ? "CAUTION · UNVERIFIED / SUSPICIOUS OFFER"
                          : result.verdict === "out_of_scope"
                            ? "STOCK TIP QUERY · NOT FINANCIAL ADVICE"
                            : "SAFE · NO ACTIVE RED FLAGS DETECTED"}
                    </div>
                  </div>
                </div>

                {/* Risk Level Bar */}
                <div className="mt-8">
                  <div className="flex justify-between items-baseline mb-2">
                    <span className="label-mono text-xs text-muted-foreground font-semibold uppercase">
                      Calculated Risk Score
                    </span>
                    <span
                      className={`text-4xl font-bold font-mono ${
                        result.score >= 0.41 ? "text-red-400" : "text-emerald-400"
                      }`}
                    >
                      {Math.round(result.score * 100)}%
                    </span>
                  </div>
                  <div className="h-3 w-full rounded-full bg-secondary overflow-hidden border border-border p-0.5">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        result.score >= 0.41
                          ? "bg-gradient-to-r from-amber-500 to-red-500"
                          : "bg-gradient-to-r from-teal-400 to-emerald-500"
                      }`}
                      style={{ width: `${Math.max(5, Math.round(result.score * 100))}%` }}
                    />
                  </div>
                </div>

                {/* Honest Note */}
                <div className="mt-6 p-4 rounded-xl bg-secondary/50 border border-border">
                  <div className="label-mono text-xs text-muted-foreground font-semibold uppercase mb-1">
                    Honest Guidance Note
                  </div>
                  <p className="text-sm text-foreground leading-relaxed font-sans font-medium">
                    {result.note}
                  </p>
                </div>

                {/* Contextual Hint (e.g., Instagram link warning) */}
                {result.hint && (
                  <div className="mt-4 p-4 rounded-xl border border-amber-500/40 bg-amber-500/10 text-amber-300 text-xs leading-relaxed">
                    <strong>Notice:</strong> {result.hint}
                  </div>
                )}

                {/* Actions */}
                <div className="mt-8 flex flex-wrap gap-3 pt-6 border-t border-border">
                  <button
                    onClick={handleReadAloud}
                    className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 label-mono text-xs text-primary-foreground hover:opacity-90 active:scale-95 transition-all shadow"
                  >
                    <span>{speaking ? "■ Stop voice" : "▷ Listen to Verdict"}</span>
                  </button>
                  <a
                    href="#pause"
                    className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-border bg-card px-4 py-2.5 label-mono text-xs text-foreground hover:bg-secondary active:scale-95 transition-all"
                  >
                    <span>◷ 24h Cooling Pause</span>
                  </a>
                </div>
              </div>

              {/* Right Column: Identified Red Flags & Extracted Claims */}
              <div className="lg:col-span-7 space-y-6">
                {/* Extracted Red Flags Card */}
                <div className="rounded-2xl border border-border bg-background p-6 md:p-8 shadow-xl">
                  <div className="flex items-center justify-between pb-4 border-b border-border">
                    <span className="label-mono text-xs text-muted-foreground font-semibold uppercase">
                      Identified Red Flags ({result.reasons.length})
                    </span>
                    <span className="label-mono text-xs text-muted-foreground">
                      Rule & Pattern Analysis
                    </span>
                  </div>

                  <div className="mt-4 divide-y divide-border">
                    {result.reasons.length === 0 ? (
                      <div className="py-8 text-center text-muted-foreground text-sm">
                        No explicit red-flag rules were triggered by this communication.
                      </div>
                    ) : (
                      result.reasons.map((flag, i) => (
                        <div key={flag.code + i} className="py-4 first:pt-2 last:pb-0">
                          <div className="flex items-center gap-2 mb-1.5">
                            <span
                              className={`label-mono text-[10px] px-2 py-0.5 rounded font-semibold uppercase ${
                                flag.severity === "high"
                                  ? "bg-red-500/15 text-red-400 border border-red-500/30"
                                  : "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                              }`}
                            >
                              {flag.severity} RISK
                            </span>
                            <span className="label-mono text-[10px] text-muted-foreground">
                              [{flag.source.toUpperCase()}]
                            </span>
                          </div>
                          <p className="text-base font-medium text-foreground leading-snug">
                            {flag.text}
                          </p>
                          {flag.evidence && (
                            <div className="mt-2 rounded bg-secondary/60 px-3 py-1.5 font-mono text-xs text-red-400 border border-border">
                              Matched Evidence: &ldquo;{flag.evidence}&rdquo;
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Extracted Claims and Entities (UPI, Returns, Urgencies) */}
                {result.claims &&
                  (((result.claims.upi_ids?.length ?? 0) > 0) ||
                    ((result.claims.promised_returns?.length ?? 0) > 0) ||
                    ((result.claims.payment_requests?.length ?? 0) > 0)) && (
                    <div className="rounded-2xl border border-border bg-background p-6 shadow-xl">
                      <div className="label-mono text-xs text-muted-foreground font-semibold uppercase pb-3 border-b border-border">
                        Extracted Financial Claims & Entities
                      </div>
                      <div className="mt-4 grid sm:grid-cols-2 gap-4 text-xs">
                        {result.claims.upi_ids && result.claims.upi_ids.length > 0 && (
                          <div className="p-3 rounded-lg bg-secondary/50 border border-border">
                            <span className="text-muted-foreground label-mono uppercase">
                              Detected UPI Address:
                            </span>
                            <div className="mt-1 font-mono font-bold text-cyan-400 truncate">
                              {result.claims.upi_ids.join(", ")}
                            </div>
                          </div>
                        )}
                        {result.claims.promised_returns &&
                          result.claims.promised_returns.length > 0 && (
                            <div className="p-3 rounded-lg bg-secondary/50 border border-border">
                              <span className="text-muted-foreground label-mono uppercase">
                                Promised Return Rate:
                              </span>
                              <div className="mt-1 font-mono font-bold text-red-400">
                                {result.claims.promised_returns
                                  .map((r) => `${r.value}% ${r.period || ""}`)
                                  .join(", ")}
                              </div>
                            </div>
                          )}
                      </div>
                    </div>
                  )}


              {/* Analyzed Message or Reel Breakdown */}
              {result.source === "video" || result.speech_text || result.on_screen_text ? (
                <div className="rounded-xl border border-border bg-secondary/20 p-5 text-xs text-muted-foreground space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="label-mono uppercase font-semibold text-foreground flex items-center gap-1.5">
                      <span>🎬</span> Instagram Reel / Video Media Analysis
                    </span>
                    <span className="label-mono text-[10px] text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                      AUDIO + FRAMES EXTRACTED
                    </span>
                  </div>

                  {result.speech_text && (
                    <div>
                      <div className="label-mono text-[11px] text-cyan-400 font-semibold mb-1 flex items-center gap-1">
                        <span>🎙</span> Reel Spoken Audio Transcript:
                      </div>
                      <blockquote className="font-mono leading-relaxed italic bg-background p-3 rounded border border-border text-foreground/80">
                        &ldquo;{result.speech_text}&rdquo;
                      </blockquote>
                    </div>
                  )}

                  {result.on_screen_text && (
                    <div>
                      <div className="label-mono text-[11px] text-amber-400 font-semibold mb-1 flex items-center gap-1">
                        <span>📺</span> Reel On-Screen Frames OCR:
                      </div>
                      <blockquote className="font-mono leading-relaxed bg-background p-3 rounded border border-border text-foreground/80 whitespace-pre-line">
                        {result.on_screen_text}
                      </blockquote>
                    </div>
                  )}

                  {!result.speech_text && !result.on_screen_text && result.text && (
                    <div>
                      <div className="label-mono text-[11px] text-foreground font-semibold mb-1">
                        Combined Reel Content:
                      </div>
                      <blockquote className="font-mono leading-relaxed italic bg-background p-3 rounded border border-border text-foreground/80">
                        &ldquo;{result.text}&rdquo;
                      </blockquote>
                    </div>
                  )}
                </div>
              ) : result.text ? (
                <div className="rounded-xl border border-border bg-secondary/20 p-5 text-xs text-muted-foreground">
                  <div className="label-mono uppercase font-semibold mb-2 text-foreground">
                    Analyzed Message Transcript
                  </div>
                  <blockquote className="font-mono leading-relaxed italic bg-background p-3 rounded border border-border text-foreground/80">
                    &ldquo;{result.text}&rdquo;
                  </blockquote>
                </div>
              ) : null}

              {/* Disclaimer */}
              <p className="text-xs text-muted-foreground/80 leading-relaxed px-1">
                {result.disclaimer}
              </p>
            </div>
          </div>

          {/* AI Insight Charts — full-width below the two-column layout */}
          <InsightCharts result={result} />
        </>
        )}
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

      <div
        className="mt-12 border-y border-border bg-secondary py-4"
        aria-label="Names people search for"
      >
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

  const questions = plan?.decision_questions || [
    "Would I still invest if no one was rushing me?",
    "Can I find this adviser on the official SEBI site myself?",
    "Could I afford to lose all of this money?",
  ];

  const handleShare = async () => {
    const shareText =
      plan?.share_text ||
      `I am pausing for 24 hours before transferring ₹${amt.toLocaleString(
        "en-IN",
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
                      onClick={() => setChecked((c) => (on ? c.filter((x) => x !== i) : [...c, i]))}
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
                <p
                  className={`mt-6 font-pixel font-bold leading-none ${isHelpline ? "text-6xl" : "text-4xl"}`}
                >
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
            <Link
              to="/model-stats"
              className="hover:text-cyan-400 text-cyan-500 font-semibold transition-colors"
            >
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
        <p className="font-pixel text-[24vw] font-bold leading-[0.75] md:text-[14rem] text-foreground/20 dark:text-cyan-400/25 select-none tracking-wider transition-colors duration-300">
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
    <>
      <main className="min-h-screen bg-background text-foreground transition-colors duration-300">
        <Nav lang={lang} onLangChange={setLang} />
        <Hero />
        <Check lang={lang} onResult={setCheckResult} injectedText={injectedText} />
        <Result
          result={checkResult}
          lang={lang}
          onRunSample={(sample) => {
            setInjectedText(sample);
            const checkEl = document.getElementById("check");
            if (checkEl) checkEl.scrollIntoView({ behavior: "smooth" });
          }}
        />
        <Sebi />
        <Pause verdict={checkResult?.verdict || "strong_red_flags"} lang={lang} />
        <Recovery lang={lang} />
        <Footer />
      </main>
      {/* Floating AI Chat — always accessible, context-aware after scan */}
      <ChatBot scanResult={checkResult} />
    </>
  );
}
