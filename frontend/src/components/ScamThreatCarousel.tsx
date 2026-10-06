import { useState, useRef, useEffect, type FC } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Flame,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  ArrowUpRight,
  TrendingDown,
  Eye,
} from "lucide-react";

export interface ScamSample {
  id: string;
  category: string;
  tag: string;
  title: string;
  sampleText: string;
  riskScore: number;
  verdict: "strong_red_flags" | "cannot_verify" | "no_red_flags_found";
  redFlags: string[];
  victimImpact: string;
  language: string;
}

export const THREAT_SAMPLES: ScamSample[] = [
  {
    id: "scam_da_01",
    category: "Digital Arrest",
    tag: "POLICE IMPERSONATION",
    title: "Fake NCB & Mumbai Police Cyber Cell Notice",
    sampleText:
      "CRITICAL NOTICE: Narcotics Control Bureau & Mumbai Police Cyber Cell. A courier from Taiwan containing 150g MDMA was seized in your name. Connect immediately on Skype id: ncb_officer_mumbai to record statement or police team will arrest within 2 hours.",
    riskScore: 99.4,
    verdict: "strong_red_flags",
    redFlags: [
      "Urgent 2-hour arrest threat",
      "Skype video interrogation demand",
      "Money transfer for police clearance",
    ],
    victimImpact: "Average loss ₹14.5 Lakhs",
    language: "EN / HI",
  },
  {
    id: "scam_invest_01",
    category: "Investment Fraud",
    tag: "SEBI IMPERSONATION",
    title: "Guaranteed 400% Intraday Jackpot Calls",
    sampleText:
      "Exclusive SEBI Certified Stock Advisory! 99.5% accuracy in intraday BankNifty jackpot calls. Guaranteed 400% profit in 15 days. VIP membership fee ₹5,000 to upi: profitcalls@icici.",
    riskScore: 98.7,
    verdict: "strong_red_flags",
    redFlags: [
      "Illegal guaranteed returns",
      "Fake SEBI certificate",
      "Personal UPI payment requested",
    ],
    victimImpact: "Average loss ₹3.2 Lakhs",
    language: "EN",
  },
  {
    id: "scam_task_01",
    category: "Task Fraud",
    tag: "WORK FROM HOME",
    title: "YouTube Video Likes & Hotel Rating Payout",
    sampleText:
      "Earn ₹3,000 - ₹8,000 daily from home! Simply like YouTube videos and submit screenshot. Daily payment via Google Pay/PhonePe. Join Telegram HR manager: t.me/youtube_task_payouts",
    riskScore: 97.5,
    verdict: "strong_red_flags",
    redFlags: [
      "Unrealistic high pay for trivial tasks",
      "Telegram channel diversion",
      "Pre-paid deposit demand",
    ],
    victimImpact: "Average loss ₹1.8 Lakhs",
    language: "EN / HI",
  },
  {
    id: "scam_ipo_01",
    category: "Pre-IPO Scam",
    tag: "INSTITUTIONAL ALLOTMENT",
    title: "Tata Technologies & Swiggy 50% Off Pool",
    sampleText:
      "Pre-IPO Institutional Allotment guaranteed for Tata Technologies and Swiggy at 50% discount! Minimum investment ₹25,000. Send fund to institutional pool account upi: preipo@ybl.",
    riskScore: 96.8,
    verdict: "strong_red_flags",
    redFlags: [
      "Fictitious unlisted discount",
      "Institutional quota for retail",
      "Unregulated UPI transfer",
    ],
    victimImpact: "Average loss ₹5.0 Lakhs",
    language: "EN",
  },
  {
    id: "scam_bill_01",
    category: "Utility Phishing",
    tag: "POWER DISCONNECTION",
    title: "Urgent Electricity Meter Bill Disconnection",
    sampleText:
      "Dear Consumer, your electricity power will be disconnected tonight at 9:30 PM from the sub-station because your previous month bill was not updated. Please immediately contact electric officer at 9876543210 or install BillPay.apk.",
    riskScore: 95.2,
    verdict: "strong_red_flags",
    redFlags: [
      "Immediate same-day power cutoff threat",
      "Personal phone number instead of official desk",
      "Malicious APK installation prompt",
    ],
    victimImpact: "Bank account compromise via SMS forwarder",
    language: "EN / Hinglish",
  },
  {
    id: "legit_sip_01",
    category: "Legitimate Advisory",
    tag: "GENUINE TRANSACTION",
    title: "Standard Monthly Mutual Fund SIP Confirmation",
    sampleText:
      "Dear Investor, your monthly SIP of INR 5,000 in Parag Parikh Flexi Cap Fund has been successfully processed via Mandate HDFC Bank on 03-Oct. Your NAV allotment is 82.410. Check CAS on CAMS online.",
    riskScore: 3.4,
    verdict: "no_red_flags_found",
    redFlags: [
      "None — Valid AMC & CAMS confirmation",
      "No urgent payment links",
      "Standard official disclosure",
    ],
    victimImpact: "Safe & verified investment",
    language: "EN",
  },
  {
    id: "legit_broker_01",
    category: "Registered Broker",
    tag: "REGULATED ENTITY",
    title: "Zerodha / SEBI Compliant Quarterly Settlement",
    sampleText:
      "Zerodha: As per SEBI quarterly settlement mandate, unutilized funds of ₹12,450 in your trading account have been credited to your primary bank account ending with 4821 via NEFT. Reference: UTIB26090184.",
    riskScore: 2.8,
    verdict: "no_red_flags_found",
    redFlags: [
      "None — Statutory regulatory compliance",
      "Official broker settlement format",
      "Funds refunded to user",
    ],
    victimImpact: "Safe & verified broker communication",
    language: "EN",
  },
];

interface ScamThreatCarouselProps {
  onSelectSample?: (text: string) => void;
}

export const ScamThreatCarousel: FC<ScamThreatCarouselProps> = ({ onSelectSample }) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const touchStartX = useRef<number>(0);
  const touchEndX = useRef<number>(0);

  const total = THREAT_SAMPLES.length;

  const nextSlide = () => {
    setActiveIndex((prev) => (prev + 1) % total);
  };

  const prevSlide = () => {
    setActiveIndex((prev) => (prev - 1 + total) % total);
  };

  // Auto-scroll effect when not hovered
  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(nextSlide, 5000);
    return () => clearInterval(interval);
  }, [isPaused, total]);

  // Handle touch gestures for mobile phones
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0]?.clientX ?? 0;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    touchEndX.current = e.touches[0]?.clientX ?? 0;
  };

  const handleTouchEnd = () => {
    const diff = touchStartX.current - touchEndX.current;
    if (diff > 50) {
      nextSlide();
    } else if (diff < -50) {
      prevSlide();
    }
  };

  const current = THREAT_SAMPLES[activeIndex] || THREAT_SAMPLES[0]!;

  return (
    <div className="relative w-full overflow-hidden py-12 md:py-16">
      {/* Header with live cyber pulse */}
      <div className="mx-auto max-w-7xl px-5 md:px-8 mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 label-mono text-cyan-400 bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/30">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
            </span>
            <span>LIVE SCAM RADAR · 3D CAROUSEL</span>
          </div>
          <h3 className="mt-3 text-2xl md:text-4xl font-normal tracking-tight text-foreground">
            Real threat vectors detected by{" "}
            <span className="font-mono font-semibold text-cyan-400">Ruko AI</span>
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Swipe or use arrows to inspect how Ruko categorizes, scores, and stops real-life scams.
          </p>
        </div>

        {/* Navigation controls */}
        <div className="flex items-center gap-3">
          <div className="label-mono text-xs text-muted-foreground">
            <span className="text-foreground font-semibold font-mono">
              {String(activeIndex + 1).padStart(2, "0")}
            </span>{" "}
            / {String(total).padStart(2, "0")}
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={prevSlide}
              aria-label="Previous scam card"
              className="p-2 rounded-md border border-border bg-card/80 hover:bg-card hover:border-cyan-500/50 text-foreground transition-all active:scale-95"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={nextSlide}
              aria-label="Next scam card"
              className="p-2 rounded-md border border-border bg-card/80 hover:bg-card hover:border-cyan-500/50 text-foreground transition-all active:scale-95"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Interactive 3D Perspective Card Carousel Container */}
      <div
        ref={containerRef}
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        className="mx-auto max-w-7xl px-5 md:px-8 select-none"
      >
        <div className="relative rounded-2xl border border-border bg-card/80 backdrop-blur-xl p-6 md:p-10 shadow-2xl transition-all duration-500 overflow-hidden">
          {/* Subtle neon gradient corner */}
          <div
            className="absolute -right-20 -top-20 w-80 h-80 rounded-full blur-3xl pointer-events-none opacity-20"
            style={{
              backgroundColor: current.riskScore > 50 ? "rgb(239, 68, 68)" : "rgb(16, 185, 129)",
            }}
          />

          <div className="relative z-10 flex flex-col justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2.5 mb-4">
                <span className="label-mono px-2.5 py-1 rounded text-xs font-semibold uppercase tracking-wider bg-secondary border border-border text-foreground">
                  {current.category}
                </span>
                <span
                  className={`label-mono px-2.5 py-1 rounded text-xs font-semibold uppercase tracking-wider border ${
                    current.riskScore > 50
                      ? "border-red-500/40 bg-red-500/10 text-red-400"
                      : "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                  }`}
                >
                  {current.tag}
                </span>
                <span className="label-mono text-xs text-muted-foreground ml-auto">
                  LANGUAGE: {current.language}
                </span>
              </div>

              <h4 className="text-xl md:text-3xl font-semibold text-foreground tracking-tight mb-4">
                {current.title}
              </h4>

              {/* The verbatim scam message box */}
              <div className="relative rounded-xl border border-border bg-background/90 p-4 md:p-6 mb-6 font-mono text-xs md:text-sm text-foreground/90 leading-relaxed shadow-inner">
                <div className="absolute top-2 right-3 label-mono text-[10px] text-muted-foreground uppercase">
                  Raw Intercepted Scam Text
                </div>
                <p className="mt-2 italic font-sans text-sm md:text-base text-foreground">
                  &ldquo;{current.sampleText}&rdquo;
                </p>
              </div>

              {/* Detected Red Flags list */}
              <div className="space-y-2 mb-6">
                <div className="label-mono text-xs text-muted-foreground font-semibold uppercase tracking-wider">
                  Extracted Danger Signals:
                </div>
                <div className="grid sm:grid-cols-3 gap-3">
                  {current.redFlags.map((flag, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2 text-xs md:text-sm text-muted-foreground bg-secondary/50 p-2.5 rounded-lg border border-border"
                    >
                      <span
                        className={`font-mono mt-0.5 font-bold ${current.riskScore > 50 ? "text-red-400" : "text-emerald-400"}`}
                      >
                        {current.riskScore > 50 ? "✖" : "✔"}
                      </span>
                      <span>{flag}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Action row */}
            <div className="pt-4 border-t border-border flex flex-wrap items-center justify-between gap-4">
              <div className="text-xs text-muted-foreground flex items-center gap-1.5 font-mono">
                <Flame className="w-4 h-4 text-amber-400" />
                <span>{current.victimImpact}</span>
              </div>

              {onSelectSample && (
                <button
                  onClick={() => onSelectSample(current.sampleText)}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-500 text-slate-950 font-semibold text-xs label-mono hover:bg-cyan-400 active:scale-95 transition-all shadow-lg shadow-cyan-500/20"
                >
                  <span>Test This In Checker</span>
                  <ArrowUpRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Carousel Dot Indicators */}
          <div className="mt-8 pt-6 border-t border-border flex items-center justify-center gap-2">
            {THREAT_SAMPLES.map((_, i) => (
              <button
                key={i}
                onClick={() => setActiveIndex(i)}
                aria-label={`Go to slide ${i + 1}`}
                className={`h-2 rounded-full transition-all duration-300 ${
                  activeIndex === i ? "w-8 bg-cyan-400" : "w-2 bg-border hover:bg-muted-foreground"
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScamThreatCarousel;
