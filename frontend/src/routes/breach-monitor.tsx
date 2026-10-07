import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect, Fragment } from "react";
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Lock,
  PhoneCall,
  MessageSquare,
  CheckCircle2,
  RefreshCw,
  ArrowLeft,
  Info,
  EyeOff,
  Database,
  KeyRound,
  Volume2,
  VolumeX,
  Sparkles,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import RukoLogo from "../components/RukoLogo";
import ThemeToggle from "../components/ThemeToggle";
import {
  BreachCheckResult,
  checkBreachExposure,
  startPhoneVerification,
  verifyPhoneCode,
  requestBreachAlertCall,
} from "@/lib/api";
import { BREACH_STRINGS } from "@/lib/breachStrings";
import { toast } from "sonner";

export const Route = createFileRoute("/breach-monitor")({
  head: () => ({
    meta: [
      { title: "Ruko — Breach Exposure Monitor" },
      {
        name: "description",
        content:
          "Stateless breach exposure check for personal email and credential monitoring. Zero data stored, zero persistence.",
      },
    ],
  }),
  component: BreachMonitorPage,
});

function BreachMonitorPage() {
  const [lang, setLang] = useState<"en" | "hi" | "gu">("en");
  const t = BREACH_STRINGS[lang];

  // Search State
  const [email, setEmail] = useState("");
  const [consent, setConsent] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [result, setResult] = useState<BreachCheckResult | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const PAGE_SIZE = 15;

  // Phone Verification & Voice Alert State (Stateless)
  const [phone, setPhone] = useState("");
  const [phoneConsent, setPhoneConsent] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [sendingChannel, setSendingChannel] = useState<"sms" | "call" | null>(null);
  const [codeSentNotice, setCodeSentNotice] = useState<string | null>(null);
  const [smsUnavailable, setSmsUnavailable] = useState(false);
  const [trialNotice, setTrialNotice] = useState<string | null>(null);
  const [rateLimitNotice, setRateLimitNotice] = useState<string | null>(null);

  const [verificationCode, setVerificationCode] = useState("");
  const [isVerifyingCode, setIsVerifyingCode] = useState(false);
  const [phoneToken, setPhoneToken] = useState<string | null>(null);
  const [voiceOptIn, setVoiceOptIn] = useState(false);
  const [isPlacingAlert, setIsPlacingAlert] = useState(false);
  const [alertFeedback, setAlertFeedback] = useState<{
    status: string;
    message: string;
    script?: string | null | undefined;
    hint?: string | null | undefined;
  } | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Clear all states on unmount to guarantee zero client persistence
  useEffect(() => {
    return () => {
      setEmail("");
      setConsent(false);
      setResult(null);
      setPhone("");
      setPhoneConsent(false);
      setVerificationCode("");
      setPhoneToken(null);
      setAlertFeedback(null);
      setCodeSentNotice(null);
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handlePlayScript = (scriptText: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) {
      toast.error("Web Speech API is not supported in this environment.");
      return;
    }

    if (isPlayingAudio) {
      window.speechSynthesis.cancel();
      setIsPlayingAudio(false);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(scriptText);
    utterance.lang = "en-IN";
    utterance.rate = 0.95;

    utterance.onend = () => {
      setIsPlayingAudio(false);
    };
    utterance.onerror = () => {
      setIsPlayingAudio(false);
    };

    setIsPlayingAudio(true);
    window.speechSynthesis.speak(utterance);
  };

  const handleBreachCheck = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      toast.error(t.form.emailRequired);
      return;
    }
    if (!consent) {
      toast.error(t.form.consentRequired);
      return;
    }

    setIsChecking(true);
    setScanError(null);
    setResult(null);
    setCurrentPage(1);

    try {
      const res = await checkBreachExposure({ email: email.trim(), consent });
      if (res.status === "scan_unavailable") {
        setScanError(t.results.scanUnavailable);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setScanError(err.message || t.results.scanUnavailable);
      toast.error(err.message || t.results.scanUnavailable);
    } finally {
      setIsChecking(false);
    }
  };

  const handleStartPhoneVerification = async (channel: "sms" | "call") => {
    if (!phone.trim()) {
      toast.error("Please enter a valid phone number with country code (e.g. +91 9876543210).");
      return;
    }
    if (!phoneConsent) {
      toast.error("Consent is required to receive a verification OTP.");
      return;
    }

    setIsSendingCode(true);
    setSendingChannel(channel);
    setAlertFeedback(null);
    setSmsUnavailable(false);
    setTrialNotice(null);
    setRateLimitNotice(null);

    try {
      const res = await startPhoneVerification({
        phone: phone.trim(),
        consent: phoneConsent,
        channel,
      });

      if (res.status === "sms_unavailable_try_call") {
        setSmsUnavailable(true);
        toast.info(t.voiceAlert.smsUnavailableNotice);
      } else {
        const notice = channel === "sms" ? t.voiceAlert.smsSentNotice : t.voiceAlert.callInitiatedNotice;
        setCodeSentNotice(notice);
        toast.success(notice);
      }
    } catch (err: any) {
      const msg = err.message || "";
      if (msg.includes("pre-approved") || msg.includes("trial") || msg.includes("number_not_verified_for_trial")) {
        setTrialNotice(t.voiceAlert.trialNotice);
        toast.error(t.voiceAlert.trialNotice);
      } else if (msg.includes("rate_limit") || msg.includes("Too many")) {
        setRateLimitNotice(t.voiceAlert.rateLimitNotice);
        toast.error(t.voiceAlert.rateLimitNotice);
      } else if (channel === "sms") {
        setSmsUnavailable(true);
        toast.info(t.voiceAlert.smsUnavailableNotice);
      } else {
        toast.error(msg || "Verification dispatch failed.");
      }
    } finally {
      setIsSendingCode(false);
      setSendingChannel(null);
    }
  };

  const handleVerifyPhoneCode = async () => {
    const codeToVerify = verificationCode.trim();
    if (!codeToVerify || codeToVerify.length < 4 || codeToVerify.length > 8) {
      toast.error(t.voiceAlert.invalidCodeNotice);
      return;
    }

    setIsVerifyingCode(true);
    // Clear the code input after each attempt as per guardrails
    setVerificationCode("");

    try {
      const res = await verifyPhoneCode({
        phone: phone.trim(),
        code: codeToVerify,
      });
      setPhoneToken(res.phone_token);
      toast.success("Phone verified successfully!");
    } catch (err: any) {
      toast.error(err.message || t.voiceAlert.invalidCodeNotice);
    } finally {
      setIsVerifyingCode(false);
    }
  };

  const handlePlaceAlertCall = async () => {
    if (!phoneToken) {
      toast.error("Phone verification required first.");
      return;
    }
    if (!voiceOptIn) {
      toast.error("Please check the opt-in box to authorize emergency voice alert calls.");
      return;
    }

    setIsPlacingAlert(true);
    setAlertFeedback(null);

    try {
      const res = await requestBreachAlertCall({
        phone: phone.trim(),
        phone_token: phoneToken,
        voice_opt_in: voiceOptIn,
        exposures_high_risk_new: result ? result.high_risk_count > 0 : true,
      });
      setAlertFeedback({
        status: res.status,
        message: res.message,
        script: res.script ?? null,
        hint: res.hint ?? null,
      });
      if (res.status === "simulated") {
        toast.info("Simulated alert generated.");
      } else if (res.call_placed) {
        toast.success(t.voiceAlert.alertSuccess);
      } else {
        toast.info(res.message);
      }
    } catch (err: any) {
      setAlertFeedback({ status: "error", message: err.message || t.voiceAlert.alertRejected });
      toast.error(err.message || t.voiceAlert.alertRejected);
    } finally {
      setIsPlacingAlert(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors mr-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </Link>
            <RukoLogo size={28} />
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-950/70 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800/60">
              Stateless Shield
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Language Selector */}
            <div className="flex rounded-lg border border-slate-200 dark:border-slate-800 p-0.5 bg-slate-100 dark:bg-slate-900 text-xs font-medium">
              <button
                type="button"
                onClick={() => setLang("en")}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  lang === "en"
                    ? "bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                English
              </button>
              <button
                type="button"
                onClick={() => setLang("hi")}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  lang === "hi"
                    ? "bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                हिंदी
              </button>
              <button
                type="button"
                onClick={() => setLang("gu")}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  lang === "gu"
                    ? "bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                ગુજરાતી
              </button>
            </div>

            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Page Hero */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-400 text-xs font-medium border border-emerald-200 dark:border-emerald-800">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>{t.dataSafetyBadge}</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
            {t.title}
          </h1>
          <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
            {t.subtitle}
          </p>
        </div>

        {/* DATA SAFETY BANNER (Strict 4 Pillars Requirement) */}
        <div className="rounded-2xl border border-emerald-200 dark:border-emerald-800/80 bg-emerald-50/50 dark:bg-emerald-950/20 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-emerald-900 dark:text-emerald-200 flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span>Core Privacy Guarantees</span>
            </h2>
            <span className="text-xs text-emerald-700 dark:text-emerald-400 font-medium">
              Zero Disk / Zero DB
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="flex items-center gap-2.5 p-2.5 rounded-lg bg-white/80 dark:bg-slate-900/80 border border-emerald-100 dark:border-emerald-900/40 text-slate-800 dark:text-slate-200">
              <EyeOff className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span className="font-medium">{t.safetyPillars.minimalCollection}</span>
            </div>
            <div className="flex items-center gap-2.5 p-2.5 rounded-lg bg-white/80 dark:bg-slate-900/80 border border-emerald-100 dark:border-emerald-900/40 text-slate-800 dark:text-slate-200">
              <KeyRound className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span className="font-medium">{t.safetyPillars.noCredentials}</span>
            </div>
            <div className="flex items-center gap-2.5 p-2.5 rounded-lg bg-white/80 dark:bg-slate-900/80 border border-emerald-100 dark:border-emerald-900/40 text-slate-800 dark:text-slate-200">
              <Lock className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span className="font-medium">{t.safetyPillars.noRawLeaks}</span>
            </div>
            <div className="flex items-center gap-2.5 p-2.5 rounded-lg bg-white/80 dark:bg-slate-900/80 border border-emerald-100 dark:border-emerald-900/40 text-slate-800 dark:text-slate-200">
              <Database className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span className="font-medium">{t.safetyPillars.inMemoryOnly}</span>
            </div>
          </div>

          <div className="text-xs text-slate-600 dark:text-slate-400 pt-1 border-t border-emerald-100 dark:border-emerald-900/40 italic">
            {t.dataSafetyNotice}
          </div>
        </div>

        {/* Data Safety Explainer Box */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-3 shadow-xs">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Info className="w-4 h-4 text-indigo-500" />
            <span>{t.explainer.title}</span>
          </h3>
          <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-1.5 list-disc list-inside">
            <li>{t.explainer.collected}</li>
            <li>{t.explainer.why}</li>
            <li>{t.explainer.providers}</li>
            <li>{t.explainer.noStorage}</li>
            <li className="font-semibold text-slate-800 dark:text-slate-200">{t.explainer.neverAsk}</li>
          </ul>
        </div>

        {/* SEARCH FORM */}
        <section className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-5">
          <form onSubmit={handleBreachCheck} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="breach-email" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                {t.form.emailLabel}
              </label>
              <input
                id="breach-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t.form.emailPlaceholder}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 text-sm"
                required
              />
            </div>

            <div className="flex items-start gap-3 pt-1">
              <input
                id="breach-consent"
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-1 h-4 w-4 rounded-sm border-slate-300 dark:border-slate-700 text-indigo-600 focus:ring-indigo-500"
                required
              />
              <label htmlFor="breach-consent" className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed select-none">
                {t.form.consentCheckbox}
              </label>
            </div>

            <button
              type="submit"
              disabled={isChecking || !consent || !email.trim()}
              className="w-full py-3 px-4 rounded-xl font-medium text-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-xs flex items-center justify-center gap-2"
            >
              {isChecking ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>{t.form.scanningButton}</span>
                </>
              ) : (
                <>
                  <ShieldAlert className="w-4 h-4" />
                  <span>{t.form.submitButton}</span>
                </>
              )}
            </button>
          </form>
        </section>

        {/* SCAN ERROR / SCAN UNAVAILABLE */}
        {scanError && (
          <div className="rounded-xl border border-amber-200 dark:border-amber-800/80 bg-amber-50 dark:bg-amber-950/30 p-4 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0" />
              <div className="text-xs text-amber-800 dark:text-amber-200 font-medium">
                {scanError}
              </div>
            </div>
            <button
              type="button"
              onClick={handleBreachCheck}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-600 hover:bg-amber-700 text-white transition-colors shrink-0"
            >
              {t.results.retryButton}
            </button>
          </div>
        )}

        {/* RESULTS SECTION */}
        {result && (
          <section className="space-y-6">
            {/* Degraded Alert */}
            {result.degraded && result.degraded.length > 0 && (
              <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/20 p-3 text-xs text-amber-800 dark:text-amber-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
                <span>{t.results.degradedWarning}</span>
              </div>
            )}

            {/* Summary Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 flex flex-col justify-between">
                <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  {t.results.totalExposures}
                </div>
                <div className="text-2xl font-bold text-slate-900 dark:text-slate-50 mt-2">
                  {result.total_exposures}
                </div>
                {result.is_demo && (
                  <span className="inline-block mt-2 text-[10px] font-semibold text-purple-700 dark:text-purple-300 bg-purple-100 dark:bg-purple-950/60 px-2 py-0.5 rounded-sm w-fit">
                    {t.results.demoBadge}
                  </span>
                )}
              </div>

              <div className="rounded-xl border border-red-200 dark:border-red-900/60 bg-red-50/40 dark:bg-red-950/20 p-4 flex flex-col justify-between">
                <div className="text-xs font-medium text-red-700 dark:text-red-400">
                  {t.results.highRiskCount}
                </div>
                <div className="text-2xl font-bold text-red-600 dark:text-red-400 mt-2">
                  {result.high_risk_count}
                </div>
                <span className="text-[10px] text-red-600 dark:text-red-400 mt-2">
                  Passwords, Tokens & Auth
                </span>
              </div>

              <div className="rounded-xl border border-amber-200 dark:border-amber-900/60 bg-amber-50/40 dark:bg-amber-950/20 p-4 flex flex-col justify-between">
                <div className="text-xs font-medium text-amber-700 dark:text-amber-400">
                  {t.results.financialCount}
                </div>
                <div className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-2">
                  {result.financial_exposure_count}
                </div>
                <span className="text-[10px] text-amber-600 dark:text-amber-400 mt-2">
                  Cards & Banking Records
                </span>
              </div>
            </div>

            {/* Clean Result State */}
            {result.total_exposures === 0 && (
              <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 text-center space-y-3">
                <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto" />
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  {t.results.cleanTitle}
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 max-w-md mx-auto">
                  {t.results.cleanDesc}
                </p>
              </div>
            )}

            {/* Exposures List (Paginated in 15 per page) */}
            {result.exposures.length > 0 && (() => {
              const totalPages = Math.ceil(result.exposures.length / PAGE_SIZE);
              const safeCurrentPage = Math.min(Math.max(currentPage, 1), totalPages);
              const startIndex = (safeCurrentPage - 1) * PAGE_SIZE;
              const paginatedExposures = result.exposures.slice(startIndex, startIndex + PAGE_SIZE);

              const handlePageChange = (p: number) => {
                setCurrentPage(p);
                const el = document.getElementById("exposures-list-header");
                if (el) {
                  el.scrollIntoView({ behavior: "smooth", block: "start" });
                }
              };

              return (
                <div className="space-y-4">
                  <div
                    id="exposures-list-header"
                    className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200/80 dark:border-slate-800/80 pb-3"
                  >
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                        {t.results.foundTitle} ({result.exposures.length})
                      </h3>
                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        Showing {startIndex + 1}–{Math.min(startIndex + PAGE_SIZE, result.exposures.length)} of {result.exposures.length} incident records
                      </div>
                    </div>

                    {totalPages > 1 && (
                      <div className="text-xs text-slate-600 dark:text-slate-300 font-medium bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full border border-slate-200 dark:border-slate-700">
                        Page {safeCurrentPage} of {totalPages}
                      </div>
                    )}
                  </div>

                  {paginatedExposures.map((exp, idx) => (
                    <div
                      key={`${safeCurrentPage}-${idx}`}
                      className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4 shadow-xs"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <h4 className="text-base font-bold text-slate-900 dark:text-slate-100">
                            {exp.breach_name}
                          </h4>
                          <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                            Approx. Exposure Date: {exp.breach_date || "Unknown"} • Provider: {exp.provider}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {exp.financial_exposure && (
                            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-100 dark:bg-rose-950/70 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800">
                              {t.results.financialWarningBadge}
                            </span>
                          )}

                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                              exp.risk_level === "HIGH"
                                ? "bg-red-100 dark:bg-red-950/80 text-red-700 dark:text-red-300 border border-red-300 dark:border-red-800"
                                : exp.risk_level === "MEDIUM"
                                ? "bg-amber-100 dark:bg-amber-950/80 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800"
                                : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700"
                            }`}
                          >
                            {exp.risk_level} RISK
                          </span>
                        </div>
                      </div>

                      {/* Categories */}
                      <div>
                        <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                          {t.results.categoriesLabel}:
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {exp.exposure_categories.map((cat, cIdx) => (
                            <span
                              key={cIdx}
                              className="px-2 py-0.5 rounded-md text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                            >
                              {cat}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Remediation & Recommended Actions */}
                      {exp.remediation && exp.remediation.length > 0 && (
                        <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-950/50 border border-slate-100 dark:border-slate-800 space-y-2">
                          <div className="text-xs font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5 text-indigo-500" />
                            <span>{t.results.recommendedActions}:</span>
                          </div>
                          <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-1 list-disc list-inside">
                            {exp.remediation.map((step, sIdx) => (
                              <li key={sIdx}>{step}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {exp.notes && (
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 italic">
                          Note: {exp.notes}
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Pagination Controls */}
                  {totalPages > 1 && (
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        Page {safeCurrentPage} of {totalPages} ({PAGE_SIZE} per page)
                      </div>

                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => handlePageChange(safeCurrentPage - 1)}
                          disabled={safeCurrentPage <= 1}
                          className="px-2.5 py-1.5 rounded-lg text-xs font-medium border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                        >
                          <ChevronLeft className="w-3.5 h-3.5" />
                          <span>Previous</span>
                        </button>

                        <div className="flex items-center gap-1">
                          {Array.from({ length: totalPages }, (_, i) => i + 1)
                            .filter(p => p === 1 || p === totalPages || Math.abs(p - safeCurrentPage) <= 2)
                            .map((p, idx, arr) => {
                              const prev = arr[idx - 1];
                              const hasGap = prev && p - prev > 1;
                              return (
                                <Fragment key={p}>
                                  {hasGap && (
                                    <span className="px-1 text-slate-400 text-xs">...</span>
                                  )}
                                  <button
                                    type="button"
                                    onClick={() => handlePageChange(p)}
                                    className={`w-7 h-7 rounded-lg text-xs font-semibold flex items-center justify-center transition-colors ${
                                      p === safeCurrentPage
                                        ? "bg-indigo-600 text-white shadow-xs"
                                        : "border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                                    }`}
                                  >
                                    {p}
                                  </button>
                                </Fragment>
                              );
                            })}
                        </div>

                        <button
                          type="button"
                          onClick={() => handlePageChange(safeCurrentPage + 1)}
                          disabled={safeCurrentPage >= totalPages}
                          className="px-2.5 py-1.5 rounded-lg text-xs font-medium border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                        >
                          <span>Next</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}
          </section>
        )}

        {/* VOICE ALERT SECTION (OPTIONAL) */}
        <section className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-5">
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <PhoneCall className="w-4 h-4 text-indigo-500" />
              <span>{t.voiceAlert.sectionTitle}</span>
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              {t.voiceAlert.sectionDesc}
            </p>
          </div>

          <div className="space-y-4">
            {/* Step 1: Input Phone & Trigger Verification Call or SMS */}
            {!phoneToken ? (
              <div className="space-y-3">
                <div className="space-y-1.5">
                  <label htmlFor="breach-phone" className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    {t.voiceAlert.phoneLabel}
                  </label>
                  <input
                    id="breach-phone"
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder={t.voiceAlert.phonePlaceholder}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-xs text-slate-900 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="flex items-start gap-2.5">
                  <input
                    id="phone-consent"
                    type="checkbox"
                    checked={phoneConsent}
                    onChange={(e) => setPhoneConsent(e.target.checked)}
                    className="mt-0.5 h-3.5 w-3.5 rounded-sm border-slate-300 dark:border-slate-700 text-indigo-600"
                  />
                  <label htmlFor="phone-consent" className="text-[11px] text-slate-500 dark:text-slate-400 select-none">
                    I consent to receiving an automated phone call or SMS with my verification code. No phone number will be stored.
                  </label>
                </div>

                {/* Verification Dispatch Buttons: SMS and Call */}
                <div className="flex flex-wrap gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => handleStartPhoneVerification("sms")}
                    disabled={isSendingCode || !phoneConsent || !phone.trim()}
                    className="flex-1 min-w-[140px] px-3.5 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-1.5"
                  >
                    {isSendingCode && sendingChannel === "sms" ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <MessageSquare className="w-3.5 h-3.5" />
                    )}
                    <span>{t.voiceAlert.sendSmsButton}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleStartPhoneVerification("call")}
                    disabled={isSendingCode || !phoneConsent || !phone.trim()}
                    className="flex-1 min-w-[140px] px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white dark:bg-slate-800 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-1.5"
                  >
                    {isSendingCode && sendingChannel === "call" ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <PhoneCall className="w-3.5 h-3.5" />
                    )}
                    <span>{t.voiceAlert.callCodeButton}</span>
                  </button>
                </div>

                {/* SMS Unavailable Notice -> Suggest Call */}
                {smsUnavailable && (
                  <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/80 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
                    <span>{t.voiceAlert.smsUnavailableNotice}</span>
                  </div>
                )}

                {/* Trial Limitation Notice */}
                {trialNotice && (
                  <div className="p-3 rounded-lg bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/80 text-xs text-indigo-800 dark:text-indigo-300 flex items-start gap-2">
                    <Info className="w-4 h-4 shrink-0 text-indigo-600 dark:text-indigo-400 mt-0.5" />
                    <span>{trialNotice}</span>
                  </div>
                )}

                {/* Rate Limit Notice */}
                {rateLimitNotice && (
                  <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/80 text-xs text-rose-800 dark:text-rose-300 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400 mt-0.5" />
                    <span>{rateLimitNotice}</span>
                  </div>
                )}

                {/* Success Notice / Code Entry */}
                {codeSentNotice && (
                  <div className="pt-2 p-3.5 rounded-lg bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/40 space-y-2.5">
                    <div className="text-xs text-indigo-800 dark:text-indigo-300 font-medium">
                      {codeSentNotice}
                    </div>

                    <label htmlFor="verification-code" className="block text-xs font-medium text-indigo-900 dark:text-indigo-200">
                      {t.voiceAlert.codeInputLabel}
                    </label>
                    <div className="flex gap-2">
                      <input
                        id="verification-code"
                        type="text"
                        maxLength={8}
                        value={verificationCode}
                        onChange={(e) => setVerificationCode(e.target.value)}
                        placeholder={t.voiceAlert.codeInputPlaceholder}
                        className="flex-1 px-3 py-2 rounded-lg border border-indigo-200 dark:border-indigo-800 bg-white dark:bg-slate-900 text-xs font-mono text-center tracking-widest text-slate-900 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                      />
                      <button
                        type="button"
                        onClick={handleVerifyPhoneCode}
                        disabled={isVerifyingCode || verificationCode.length < 4}
                        className="px-4 py-2 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        {isVerifyingCode ? t.voiceAlert.verifyingCode : t.voiceAlert.verifyCodeButton}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* Step 2: Phone is Verified -> Enable Alert Call Trigger */
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-3 py-2 rounded-lg border border-emerald-200 dark:border-emerald-800">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{t.voiceAlert.phoneVerifiedBadge} (Stateless Token Issued)</span>
                </div>

                <div className="flex items-start gap-2.5">
                  <input
                    id="voice-opt-in"
                    type="checkbox"
                    checked={voiceOptIn}
                    onChange={(e) => setVoiceOptIn(e.target.checked)}
                    className="mt-0.5 h-3.5 w-3.5 rounded-sm border-slate-300 dark:border-slate-700 text-indigo-600"
                  />
                  <label htmlFor="voice-opt-in" className="text-xs text-slate-700 dark:text-slate-300 select-none">
                    {t.voiceAlert.optInCheckbox}
                  </label>
                </div>

                <button
                  type="button"
                  onClick={handlePlaceAlertCall}
                  disabled={isPlacingAlert || !voiceOptIn}
                  className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-xs flex items-center justify-center gap-2"
                >
                  {isPlacingAlert ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>{t.voiceAlert.sendingAlert}</span>
                    </>
                  ) : (
                    <>
                      <PhoneCall className="w-3.5 h-3.5" />
                      <span>{t.voiceAlert.sendAlertButton}</span>
                    </>
                  )}
                </button>

                {alertFeedback && (
                  <div className="space-y-3">
                    <div
                      className={`p-3 rounded-lg text-xs font-medium border ${
                        alertFeedback.status === "ok"
                          ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800"
                          : alertFeedback.status === "simulated"
                          ? "bg-purple-50 dark:bg-purple-950/40 text-purple-800 dark:text-purple-300 border-purple-200 dark:border-purple-800"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700"
                      }`}
                    >
                      {alertFeedback.message}
                    </div>

                    {/* Simulated Alert Card (Demo Mode or live calls unavailable fallback) */}
                    {(alertFeedback.status === "simulated" || (alertFeedback.hint === "live_calls_unavailable" && alertFeedback.script)) && alertFeedback.script && (
                      <div className="rounded-xl border border-purple-200 dark:border-purple-800/80 bg-purple-50/60 dark:bg-purple-950/30 p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-purple-800 dark:text-purple-300 bg-purple-100 dark:bg-purple-900/60 px-2.5 py-1 rounded-md border border-purple-200 dark:border-purple-800">
                            <Sparkles className="w-3.5 h-3.5" />
                            <span>{t.voiceAlert.simulatedBadge}</span>
                          </span>
                          <span className="text-[11px] text-purple-700 dark:text-purple-400 italic">
                            Browser Web Speech
                          </span>
                        </div>

                        <p className="text-xs text-slate-600 dark:text-slate-400">
                          {t.voiceAlert.simulatedDesc}
                        </p>

                        <blockquote className="text-xs font-mono text-slate-800 dark:text-slate-200 bg-white/80 dark:bg-slate-900/80 p-3 rounded-lg border border-purple-100 dark:border-purple-900/40 leading-relaxed whitespace-pre-wrap">
                          "{alertFeedback.script}"
                        </blockquote>

                        <button
                          type="button"
                          onClick={() => handlePlayScript(alertFeedback.script!)}
                          className="px-3.5 py-2 rounded-lg text-xs font-semibold bg-purple-600 hover:bg-purple-700 text-white transition-colors flex items-center gap-1.5 shadow-xs"
                        >
                          {isPlayingAudio ? (
                            <>
                              <VolumeX className="w-3.5 h-3.5" />
                              <span>{t.voiceAlert.stopAlertButton}</span>
                            </>
                          ) : (
                            <>
                              <Volume2 className="w-3.5 h-3.5" />
                              <span>{t.voiceAlert.playAlertButton}</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Quiet Hours Warning */}
            <div className="text-[11px] text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/40 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
              {t.voiceAlert.quietHoursNotice}
            </div>
          </div>
        </section>

        {/* Attribution & Transparency Footer */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400 border-t border-slate-200/80 dark:border-slate-800/80 pt-4 px-1 pb-6">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
            <span>Zero-disk in-memory processing • Verified Breach Intelligence</span>
          </div>
          <a
            href="https://leakcheck.io"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
          >
            <span>Powered by</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300 hover:underline">LeakCheck</span>
            <ExternalLink className="w-3 h-3 ml-0.5" />
          </a>
        </div>
      </main>
    </div>
  );
}
