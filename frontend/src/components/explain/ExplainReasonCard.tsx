import React from "react";
import {
  AlertTriangle,
  AlertCircle,
  Info,
  ShieldCheck,
  ShieldAlert,
  Building2,
} from "lucide-react";
import { DocExplanation } from "@/lib/api";
import { getExplainStrings } from "@/lib/explainStrings";

interface ExplainReasonCardProps {
  explanation: DocExplanation;
  language?: string;
}

export const ExplainReasonCard: React.FC<ExplainReasonCardProps> = ({
  explanation,
  language = "en",
}) => {
  const strings = getExplainStrings(language);
  const flags = explanation.ruko_flags || [];
  const registry = explanation.registry;

  if (flags.length === 0 && !registry) {
    return null;
  }

  return (
    <div className="space-y-4 my-6">
      {/* Registry Match Card */}
      {registry && (
        <div
          className={`p-4 rounded-xl border backdrop-blur-sm transition-all ${
            registry.status === "found_in_snapshot" || registry.matches?.length > 0
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-950 dark:text-emerald-100"
              : "bg-amber-500/10 border-amber-500/30 text-amber-950 dark:text-amber-100"
          }`}
        >
          <div className="flex items-start gap-3">
            {registry.status === "found_in_snapshot" ||
            (registry.matches && registry.matches.length > 0) ? (
              <ShieldCheck className="w-6 h-6 text-emerald-500 shrink-0 mt-0.5" />
            ) : (
              <ShieldAlert className="w-6 h-6 text-amber-500 shrink-0 mt-0.5" />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-sm">
                  {registry.matches && registry.matches.length > 0
                    ? "SEBI Registered Match Found"
                    : "SEBI Registration Unverified"}
                </span>
                {registry.matches?.[0]?.category && (
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-secondary/80 border text-foreground">
                    {registry.matches[0].category}
                  </span>
                )}
                {registry.matches?.[0]?.status && (
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                      registry.matches[0].status.toLowerCase() === "active"
                        ? "bg-emerald-500/20 text-emerald-700 dark:text-emerald-300"
                        : "bg-amber-500/20 text-amber-700 dark:text-amber-300"
                    }`}
                  >
                    {registry.matches[0].status}
                  </span>
                )}
              </div>

              {registry.matches?.[0]?.name && (
                <div className="mt-1 flex items-center gap-1.5 text-sm font-medium text-foreground">
                  <Building2 className="w-4 h-4 opacity-70" />
                  <span>{registry.matches[0].name}</span>
                  {registry.matches[0].reg_no && (
                    <span className="text-xs text-muted-foreground font-mono">
                      ({registry.matches[0].reg_no})
                    </span>
                  )}
                </div>
              )}

              {registry.snapshot_date && (
                <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">
                  Verified against dated SEBI intermediary snapshot ({registry.snapshot_date}).
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Red Flags / Crosscheck Warnings */}
      {flags.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <h3 className="text-sm font-semibold tracking-wide uppercase text-foreground/80">
              {strings.redFlagsDetectedTitle || "Potential Red Flags Identified"} ({flags.length})
            </h3>
          </div>

          <div className="grid gap-3 sm:grid-cols-1">
            {flags.map((flag: Reason, idx) => {
              const sev = (flag.severity || "medium").toLowerCase();
              const isHigh = sev === "high" || sev === "critical";
              const isMed = sev === "medium";

              const borderClass = isHigh
                ? "border-red-500/40 bg-red-500/5 hover:border-red-500/60"
                : isMed
                  ? "border-amber-500/40 bg-amber-500/5 hover:border-amber-500/60"
                  : "border-blue-500/40 bg-blue-500/5 hover:border-blue-500/60";

              const badgeClass = isHigh
                ? "bg-red-500/15 text-red-700 dark:text-red-300 border-red-500/30"
                : isMed
                  ? "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30"
                  : "bg-blue-500/15 text-blue-700 dark:text-blue-300 border-blue-500/30";

              const messageText = flag.text || flag.message || "";
              const flagTitle = flag.code
                ? flag.code.replace(/_/g, " ").toUpperCase()
                : flag.title || "Red Flag";

              return (
                <div
                  key={flag.id || flag.code || idx}
                  className={`p-4 rounded-xl border transition-all ${borderClass}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      {isHigh ? (
                        <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
                      ) : isMed ? (
                        <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                      ) : (
                        <Info className="w-4 h-4 text-blue-500 shrink-0" />
                      )}
                      <span className="text-sm font-semibold text-foreground">{flagTitle}</span>
                    </div>

                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-semibold border capitalize ${badgeClass}`}
                    >
                      {flag.severity || "medium"}
                    </span>
                  </div>

                  {messageText && (
                    <p className="mt-2 text-sm text-foreground/90 leading-relaxed">{messageText}</p>
                  )}

                  {flag.evidence && (
                    <div className="mt-2.5 p-2 rounded-md bg-background/60 border text-xs text-muted-foreground font-mono">
                      <span className="font-semibold text-foreground/70 not-mono mr-1">
                        Evidence:
                      </span>
                      &ldquo;{flag.evidence}&rdquo;
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
