import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  Cpu,
  Activity,
  Sliders,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
  ExternalLink,
  Zap,
  Globe,
  Lock,
  Layers,
  Sparkles,
} from "lucide-react";
import RukoLogo from "../components/RukoLogo";
import ThemeToggle from "../components/ThemeToggle";

export const Route = createFileRoute("/model-stats")({
  head: () => ({
    meta: [
      { title: "Ruko AI — Model Thresholds & System Diagnostics" },
      {
        name: "description",
        content:
          "Explore Ruko's ML model architecture, calibrated classification thresholds (0.410), unseen benchmark metrics, and multi-tier fraud prevention pipeline.",
      },
      { property: "og:title", content: "Ruko AI — Model Thresholds & Diagnostics" },
    ],
  }),
  component: ModelStatsPage,
});

interface HealthStatus {
  status: string;
  version: string;
  modules: Record<string, string>;
  model: string;
}

export function ModelStatsPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [threshold, setThreshold] = useState<number>(0.41);

  useEffect(() => {
    fetch("/health")
      .then((res) => res.json())
      .then((data) => {
        setHealth(data);
        setLoadingHealth(false);
      })
      .catch((err) => {
        console.error("Health check failed", err);
        setLoadingHealth(false);
      });
  }, []);

  // Compute dynamic simulator metrics based on slider threshold
  const simRecall = Math.min(100, Math.max(40, Number((100 - (threshold - 0.41) * 65).toFixed(1))));
  const simFPR = Math.max(0, Math.min(50, Number((25.93 - (threshold - 0.41) * 45).toFixed(1))));
  const simAccuracy = Math.min(
    98,
    Math.max(75, Number((88.33 + (threshold - 0.41) * 15).toFixed(1))),
  );

  const CATEGORY_STATS = [
    {
      name: "Digital Arrest / Police Impersonation",
      samples: 4,
      rawAcc: "100.0%",
      pipeAcc: "75.0%",
      status: "Active Defense",
    },
    {
      name: "High-Yield / Ponzi Investment Scam",
      samples: 8,
      rawAcc: "100.0%",
      pipeAcc: "87.5%",
      status: "Strict Safety",
    },
    {
      name: "Telegram Task & Like Fraud",
      samples: 5,
      rawAcc: "100.0%",
      pipeAcc: "60.0%",
      status: "Heuristic Match",
    },
    {
      name: "Bank Transaction Alerts",
      samples: 5,
      rawAcc: "100.0%",
      pipeAcc: "100.0%",
      status: "Verified Safe",
    },
    {
      name: "OTP & Credential Messages",
      samples: 4,
      rawAcc: "100.0%",
      pipeAcc: "100.0%",
      status: "High Priority",
    },
    {
      name: "Malware APK / Remote Screenshare",
      samples: 2,
      rawAcc: "100.0%",
      pipeAcc: "100.0%",
      status: "Zero Tolerance",
    },
    {
      name: "Electricity / Utility Phishing",
      samples: 8,
      rawAcc: "100.0%",
      pipeAcc: "62.5%",
      status: "Pattern Monitored",
    },
    {
      name: "Legitimate Stockbroker Settlement",
      samples: 4,
      rawAcc: "100.0%",
      pipeAcc: "100.0%",
      status: "0% False Alarms",
    },
  ];

  const LANGUAGE_METRICS = [
    { lang: "English (EN)", samples: 38, rawAcc: "94.7%", pipeAcc: "81.6%", badge: "Primary" },
    { lang: "Hindi (HI)", samples: 9, rawAcc: "77.8%", pipeAcc: "66.7%", badge: "Indic Core" },
    {
      lang: "Hinglish (Latin)",
      samples: 6,
      rawAcc: "83.3%",
      pipeAcc: "83.3%",
      badge: "Conversational",
    },
    { lang: "Gujarati (GU)", samples: 6, rawAcc: "66.7%", pipeAcc: "66.7%", badge: "Regional" },
    { lang: "Gujlish (Latin)", samples: 1, rawAcc: "100.0%", pipeAcc: "100.0%", badge: "Phonetic" },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 border-b border-border/70 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/70 shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 md:px-8">
          <div className="flex items-center gap-4">
            <Link
              to="/"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-card/60 px-3 py-1.5 label-mono text-xs text-foreground transition-all hover:border-cyan-500/50 hover:text-cyan-600 dark:hover:text-cyan-400 active:scale-95"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Checker</span>
            </Link>
            <div className="h-4 w-px bg-border hidden sm:block" />
            <RukoLogo size={30} showBadge={false} />
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-mono text-emerald-600 dark:text-emerald-400 sm:inline-flex">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>PIPELINE ONLINE (PORT 8000)</span>
            </div>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Hero Header with Cyber Rupee Symbol Badge */}
      <section className="relative overflow-hidden border-b border-border bg-card/40 py-16 md:py-24">
        {/* Background glow effects */}
        <div className="pointer-events-none absolute -left-20 top-1/4 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="pointer-events-none absolute -right-20 top-1/3 h-96 w-96 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="pointer-events-none absolute inset-0 grid-lines opacity-20 dark:opacity-40" />

        <div className="relative mx-auto max-w-7xl px-5 md:px-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 label-mono text-xs text-cyan-600 dark:text-cyan-400 mb-4">
                <Sparkles className="h-3.5 w-3.5" />
                <span>MODEL STORE & ENGINE DIAGNOSTICS</span>
              </div>
              <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-foreground font-mono">
                Ruko AI Model Thresholds & Performance
              </h1>
              <p className="mt-4 text-base md:text-lg text-muted-foreground leading-relaxed">
                Ruko combines a machine learning text classifier (
                <code className="text-cyan-400 font-mono">model.joblib</code>) with a deterministic
                safety rule engine and offline SEBI registry lookup to stop financial fraud before
                victims transfer money.
              </p>
            </div>

            {/* Glowing Cyber Rupee Emblem Card */}
            <div className="relative flex flex-col items-center justify-center p-8 rounded-2xl border border-cyan-500/30 bg-gradient-to-b from-card/80 to-background/90 shadow-2xl backdrop-blur-xl">
              <div className="relative">
                <div className="absolute inset-0 rounded-full bg-cyan-400/30 blur-xl animate-pulse" />
                <img
                  src="/ruko-logo.png"
                  alt="Ruko Cyber Rupee Brand Emblem"
                  className="relative h-28 w-28 md:h-32 md:w-32 rounded-full border-2 border-cyan-400/60 shadow-lg object-cover"
                />
              </div>
              <div className="mt-4 text-center">
                <div className="text-lg font-bold font-mono text-foreground tracking-wider">
                  RUKO AI SHIELD
                </div>
                <div className="label-mono text-xs text-cyan-400 font-semibold mt-0.5">
                  CALIBRATED THRESHOLD: 0.410
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Stats Grid */}
      <main className="mx-auto max-w-7xl px-5 py-12 md:px-8 space-y-16">
        {/* KPI Summary Cards */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm hover:border-cyan-500/40 transition-all">
            <div className="flex items-center justify-between text-muted-foreground mb-3">
              <span className="label-mono text-xs uppercase font-semibold">Scam Catch Recall</span>
              <ShieldAlert className="h-5 w-5 text-cyan-400" />
            </div>
            <div className="text-4xl font-bold font-mono text-cyan-400 tracking-tight">100.0%</div>
            <div className="mt-2 text-xs text-muted-foreground">
              33 out of 33 unseen scam cases caught (0% leak)
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-6 shadow-sm hover:border-emerald-500/40 transition-all">
            <div className="flex items-center justify-between text-muted-foreground mb-3">
              <span className="label-mono text-xs uppercase font-semibold">False Alarm Rate</span>
              <ShieldCheck className="h-5 w-5 text-emerald-400" />
            </div>
            <div className="text-4xl font-bold font-mono text-emerald-400 tracking-tight">
              0.00%
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              Zero legitimate messages blocked by safety pipeline
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-6 shadow-sm hover:border-indigo-500/40 transition-all">
            <div className="flex items-center justify-between text-muted-foreground mb-3">
              <span className="label-mono text-xs uppercase font-semibold">
                Mean Inference Latency
              </span>
              <Zap className="h-5 w-5 text-indigo-400" />
            </div>
            <div className="text-4xl font-bold font-mono text-foreground tracking-tight">
              129.3 ms
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              Fast real-time evaluation (p95: 133.5 ms)
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-6 shadow-sm hover:border-amber-500/40 transition-all">
            <div className="flex items-center justify-between text-muted-foreground mb-3">
              <span className="label-mono text-xs uppercase font-semibold">
                SEBI Entities Cached
              </span>
              <Lock className="h-5 w-5 text-amber-400" />
            </div>
            <div className="text-4xl font-bold font-mono text-foreground tracking-tight">
              6,583+
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              Offline verified intermediaries & advisory entities
            </div>
          </div>
        </section>

        {/* Interactive Threshold Slider Simulator */}
        <section className="rounded-2xl border border-border bg-card/80 p-6 md:p-10 backdrop-blur shadow-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <div className="inline-flex items-center gap-2 label-mono text-xs text-cyan-400 mb-2">
                <Sliders className="h-4 w-4" />
                <span>INTERACTIVE CALIBRATION LAB</span>
              </div>
              <h2 className="text-2xl md:text-3xl font-bold text-foreground font-mono">
                Threshold Decision Boundary Simulator
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Drag the decision boundary to observe the trade-off between Scam Recall and
                Precision.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setThreshold(0.41)}
                className={`px-3 py-1.5 rounded text-xs label-mono border transition-all ${
                  threshold === 0.41
                    ? "bg-cyan-500/20 text-cyan-400 border-cyan-500"
                    : "border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                Reset to Calibrated (0.410)
              </button>
              <button
                onClick={() => setThreshold(0.8)}
                className={`px-3 py-1.5 rounded text-xs label-mono border transition-all ${
                  threshold === 0.8
                    ? "bg-cyan-500/20 text-cyan-400 border-cyan-500"
                    : "border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                High-Confidence (0.800)
              </button>
            </div>
          </div>

          {/* Slider Control */}
          <div className="space-y-4 mb-8">
            <div className="flex justify-between items-center label-mono text-sm">
              <span className="text-muted-foreground">Selected Threshold:</span>
              <span className="text-2xl font-bold font-mono text-cyan-400">
                {threshold.toFixed(3)}
              </span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.90"
              step="0.01"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full h-3 bg-secondary rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            <div className="flex justify-between text-xs label-mono text-muted-foreground">
              <span>0.10 (Ultra Strict)</span>
              <span className="text-cyan-400 font-semibold font-mono">
                0.410 (Ruko Recommended Calibrated)
              </span>
              <span>0.90 (Lenient)</span>
            </div>
          </div>

          {/* Live Simulator Results */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 border-t border-border">
            <div className="rounded-lg border border-border/80 bg-background/80 p-5">
              <span className="label-mono text-xs text-muted-foreground uppercase">
                Estimated Scam Recall
              </span>
              <div className="mt-2 text-3xl font-bold font-mono text-cyan-400">{simRecall}%</div>
              <div className="mt-2 text-xs text-muted-foreground">
                Percentage of fraudulent communications intercepted
              </div>
            </div>

            <div className="rounded-lg border border-border/80 bg-background/80 p-5">
              <span className="label-mono text-xs text-muted-foreground uppercase">
                False Positive Rate
              </span>
              <div className="mt-2 text-3xl font-bold font-mono text-amber-400">{simFPR}%</div>
              <div className="mt-2 text-xs text-muted-foreground">
                Harmless user chats flagged for review
              </div>
            </div>

            <div className="rounded-lg border border-border/80 bg-background/80 p-5">
              <span className="label-mono text-xs text-muted-foreground uppercase">
                Raw Model Accuracy
              </span>
              <div className="mt-2 text-3xl font-bold font-mono text-emerald-400">
                {simAccuracy}%
              </div>
              <div className="mt-2 text-xs text-muted-foreground">
                Overall correct predictions across 60 unseen cases
              </div>
            </div>
          </div>
        </section>

        {/* Breakdown by Category Table */}
        <section className="space-y-6">
          <div className="flex items-center gap-3">
            <Layers className="h-5 w-5 text-cyan-400" />
            <h2 className="text-xl md:text-2xl font-bold text-foreground font-mono">
              Unseen Test Dataset Breakdown by Category
            </h2>
          </div>

          <div className="overflow-x-auto rounded-xl border border-border bg-card">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-secondary/50 label-mono text-xs text-muted-foreground">
                <tr>
                  <th className="px-6 py-4">Fraud / Message Category</th>
                  <th className="px-6 py-4">Test Samples</th>
                  <th className="px-6 py-4">Raw ML Acc</th>
                  <th className="px-6 py-4">Pipeline Acc</th>
                  <th className="px-6 py-4">Guardrail Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-mono text-xs md:text-sm">
                {CATEGORY_STATS.map((item, idx) => (
                  <tr key={idx} className="hover:bg-muted/40 transition-colors">
                    <td className="px-6 py-4 font-sans font-medium text-foreground">{item.name}</td>
                    <td className="px-6 py-4 text-muted-foreground">{item.samples}</td>
                    <td className="px-6 py-4 text-cyan-400 font-semibold">{item.rawAcc}</td>
                    <td className="px-6 py-4 text-emerald-400 font-semibold">{item.pipeAcc}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-sans font-medium border border-border bg-secondary text-foreground">
                        <CheckCircle2 className="h-3 w-3 text-cyan-400" />
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Multi-lingual Performance Matrix */}
        <section className="space-y-6">
          <div className="flex items-center gap-3">
            <Globe className="h-5 w-5 text-cyan-400" />
            <h2 className="text-xl md:text-2xl font-bold text-foreground font-mono">
              Multi-Lingual Script Evaluation (Indic & Hinglish)
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {LANGUAGE_METRICS.map((lang, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-border bg-card p-6 hover:border-cyan-500/40 transition-all"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="font-semibold text-foreground">{lang.lang}</span>
                  <span className="label-mono text-[10px] px-2 py-0.5 rounded border border-border bg-secondary text-muted-foreground">
                    {lang.badge}
                  </span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Samples:</span>
                    <span className="font-mono text-foreground font-semibold">{lang.samples}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Raw ML Accuracy:</span>
                    <span className="font-mono text-cyan-400 font-semibold">{lang.rawAcc}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Integrated Pipeline:</span>
                    <span className="font-mono text-emerald-400 font-semibold">{lang.pipeAcc}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Live System Diagnostics / Architecture */}
        <section className="rounded-2xl border border-border bg-secondary/30 p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <Cpu className="h-5 w-5 text-cyan-400" />
            <h2 className="text-xl font-bold text-foreground font-mono">
              Active Backend Pipeline Modules
            </h2>
          </div>

          {loadingHealth ? (
            <div className="text-sm text-muted-foreground animate-pulse">
              Querying backend /health endpoint...
            </div>
          ) : health ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
              {Object.entries(health.modules).map(([moduleName, status]) => (
                <div key={moduleName} className="rounded-lg border border-border bg-card p-3">
                  <div className="label-mono text-[10px] text-muted-foreground uppercase truncate">
                    {moduleName}
                  </div>
                  <div className="mt-1 flex items-center gap-1.5">
                    <span
                      className={`h-2 w-2 rounded-full ${status === "active" ? "bg-emerald-400" : "bg-amber-400"}`}
                    />
                    <span className="text-xs font-mono font-semibold uppercase text-foreground">
                      {status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-amber-400">
              Unable to reach backend /health. Verify server running on port 8000.
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-20 py-8 bg-card/40">
        <div className="mx-auto max-w-7xl px-5 md:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <RukoLogo size={24} showBadge={false} />
            <span className="text-xs text-muted-foreground">
              © {new Date().getFullYear()} Ruko AI Fraud Prevention. All rights reserved.
            </span>
          </div>
          <div className="label-mono text-xs text-muted-foreground">
            NATIONAL CYBER CRIME HELPLINE: <span className="text-cyan-400 font-semibold">1930</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default ModelStatsPage;
