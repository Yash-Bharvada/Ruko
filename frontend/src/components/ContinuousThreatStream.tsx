import type { FC } from "react";
import { AlertTriangle, CheckCircle, ShieldAlert, Zap } from "lucide-react";

interface ThreatItem {
  id: string;
  tag: string;
  badge: "SCAM" | "SAFE" | "PHISHING";
  snippet: string;
  risk: string;
  time: string;
}

const LIVE_THREATS: ThreatItem[] = [
  {
    id: "1",
    tag: "Digital Arrest",
    badge: "SCAM",
    snippet: "CBI Skype video notice: Pay ₹50k clearance bond immediately",
    risk: "99.4%",
    time: "2m ago",
  },
  {
    id: "2",
    tag: "SEBI Verified",
    badge: "SAFE",
    snippet: "Kotak Securities quarterly fund transfer compliance notice",
    risk: "1.2%",
    time: "5m ago",
  },
  {
    id: "3",
    tag: "Telegram Task",
    badge: "SCAM",
    snippet: "Earn ₹5,000/day by liking hotels. Transfer ₹2000 prepaid",
    risk: "97.5%",
    time: "8m ago",
  },
  {
    id: "4",
    tag: "Power Bill Phishing",
    badge: "PHISHING",
    snippet: "Power cut tonight at 9:30 PM. Download BillPay.apk immediately",
    risk: "95.2%",
    time: "11m ago",
  },
  {
    id: "5",
    tag: "Pre-IPO Fraud",
    badge: "SCAM",
    snippet: "Swiggy unlisted shares at 50% discount. Send funds to YBL UPI",
    risk: "96.8%",
    time: "14m ago",
  },
  {
    id: "6",
    tag: "Official SIP",
    badge: "SAFE",
    snippet: "HDFC Mutual Fund monthly SIP debit confirmation ₹5,000",
    risk: "2.1%",
    time: "18m ago",
  },
];

export const ContinuousThreatStream: FC = () => {
  return (
    <div className="relative w-full overflow-hidden border-y border-border bg-card/40 py-4 backdrop-blur-sm">
      <div className="flex w-max animate-marquee gap-6 hover:[animation-play-state:paused]">
        {/* Double array for seamless loop */}
        {[...LIVE_THREATS, ...LIVE_THREATS].map((item, idx) => (
          <div
            key={`${item.id}-${idx}`}
            className="flex items-center gap-3 rounded-lg border border-border/70 bg-card px-4 py-2 shadow-sm transition-all hover:border-cyan-500/50 hover:shadow-cyan-500/10"
          >
            <div className="flex items-center gap-1.5">
              {item.badge === "SAFE" ? (
                <CheckCircle className="h-4 w-4 text-emerald-400" />
              ) : item.badge === "PHISHING" ? (
                <AlertTriangle className="h-4 w-4 text-amber-400" />
              ) : (
                <ShieldAlert className="h-4 w-4 text-rose-500" />
              )}
              <span
                className={`label-mono text-[10px] font-bold px-1.5 py-0.5 rounded ${
                  item.badge === "SAFE"
                    ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                    : item.badge === "PHISHING"
                      ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                      : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                }`}
              >
                {item.badge}
              </span>
            </div>

            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground max-w-xs truncate">
                {item.snippet}
              </span>
              <div className="flex items-center gap-2 label-mono text-[10px] text-muted-foreground">
                <span>{item.tag}</span>
                <span>•</span>
                <span className={item.badge === "SAFE" ? "text-emerald-400" : "text-rose-400"}>
                  Risk: {item.risk}
                </span>
                <span>•</span>
                <span>{item.time}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ContinuousThreatStream;
