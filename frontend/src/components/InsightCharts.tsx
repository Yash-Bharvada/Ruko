import { useState, useEffect, useRef, type FC } from "react";
import {
  getInsights,
  type InsightChart,
  type InsightsResponse,
  type CheckResult,
} from "../lib/api";

interface Props {
  result: CheckResult;
}

// ─── Individual Chart Components ─────────────────────────────────────────────

const DonutChart: FC<{ chart: InsightChart; visible: boolean }> = ({ chart, visible }) => {
  const total = chart.data.reduce((s, d) => s + d.value, 0);
  const size = 120;
  const r = 44;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * r;

  let offset = 0;
  const segments = chart.data.map((d) => {
    const pct = d.value / total;
    const seg = { ...d, offset, pct, dash: pct * circumference, gap: (1 - pct) * circumference };
    offset += pct;
    return seg;
  });

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative">
        <svg
          width={size}
          height={size}
          className={`transition-all duration-700 ${visible ? "opacity-100" : "opacity-0"}`}
        >
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke="currentColor"
            strokeWidth="10"
            className="text-secondary/60"
          />
          {segments.map((seg, i) => (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={r}
              fill="none"
              stroke={seg.color || chart.color}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={`${visible ? seg.dash : 0} ${circumference}`}
              strokeDashoffset={-seg.offset * circumference + circumference * 0.25}
              style={{ transition: `stroke-dasharray 0.8s ease ${i * 150}ms` }}
            />
          ))}
          <text
            x={cx}
            y={cy + 5}
            textAnchor="middle"
            className="fill-foreground font-mono text-xs font-bold"
          >
            {Math.round(segments[0]?.pct * 100 || 0)}%
          </text>
        </svg>
      </div>
      <div className="flex flex-wrap justify-center gap-x-3 gap-y-1">
        {chart.data.map((d, i) => (
          <span
            key={i}
            className="flex items-center gap-1 label-mono text-[10px] text-muted-foreground"
          >
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{ backgroundColor: d.color || chart.color }}
            />
            {d.label}
          </span>
        ))}
      </div>
    </div>
  );
};

const BarChart: FC<{ chart: InsightChart; visible: boolean }> = ({ chart, visible }) => {
  const max = Math.max(...chart.data.map((d) => d.value));
  return (
    <div className="flex flex-col gap-2.5 w-full">
      {chart.data.map((d, i) => (
        <div key={i} className="space-y-1">
          <div className="flex justify-between items-baseline">
            <span className="label-mono text-[10px] text-muted-foreground truncate max-w-[70%]">
              {d.label}
            </span>
            <span className="label-mono text-[10px] font-bold" style={{ color: chart.color }}>
              {d.value}%
            </span>
          </div>
          <div className="h-2 w-full rounded-full bg-secondary/60 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: visible ? `${(d.value / max) * 100}%` : "0%",
                background: `linear-gradient(90deg, ${chart.color}aa, ${chart.color})`,
                transitionDelay: `${i * 100}ms`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

const GaugeChart: FC<{ chart: InsightChart; visible: boolean }> = ({ chart, visible }) => {
  const val = chart.data[0]?.value ?? 0;
  const angle = visible ? -135 + (val / 100) * 270 : -135;
  const color = val >= 80 ? "#ef4444" : val >= 41 ? "#f97316" : "#22c55e";

  const arcPath = (start: number, end: number, r: number, w: number) => {
    const a1 = ((start - 90) * Math.PI) / 180;
    const a2 = ((end - 90) * Math.PI) / 180;
    const x1 = 60 + r * Math.cos(a1),
      y1 = 60 + r * Math.sin(a1);
    const x2 = 60 + r * Math.cos(a2),
      y2 = 60 + r * Math.sin(a2);
    const large = end - start > 180 ? 1 : 0;
    return `M${x1},${y1} A${r},${r} 0 ${large},1 ${x2},${y2}`;
  };

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="120" height="72" viewBox="0 0 120 75">
        <path
          d={arcPath(-135, 135, 44, 10)}
          fill="none"
          stroke="currentColor"
          strokeWidth="10"
          strokeLinecap="round"
          className="text-secondary/60"
        />
        <path
          d={arcPath(-135, -135 + (visible ? val : 0) * 2.7, 44, 10)}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          style={{ transition: "d 1s ease" }}
        />
        <g
          transform={`translate(60,60) rotate(${angle})`}
          style={{ transition: "transform 1s ease" }}
        >
          <line
            x1="0"
            y1="0"
            x2="0"
            y2="-32"
            stroke={color}
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          <circle cx="0" cy="0" r="4" fill={color} />
        </g>
        <text
          x="60"
          y="68"
          textAnchor="middle"
          className="fill-foreground font-mono font-bold text-lg"
        >
          {val}%
        </text>
      </svg>
      <div className="flex justify-between w-full px-2 label-mono text-[10px] text-muted-foreground">
        <span>0%</span>
        <span>Safe</span>
        <span>100%</span>
      </div>
    </div>
  );
};

const ChartCard: FC<{ chart: InsightChart; delay: number }> = ({ chart, delay }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(t);
  }, [delay]);

  return (
    <div
      ref={ref}
      className={`rounded-2xl border border-border bg-background p-5 shadow-lg transition-all duration-500 hover:shadow-xl hover:border-cyan-500/30
        ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className="flex items-center justify-between mb-4">
        <h4 className="label-mono text-xs font-semibold text-foreground uppercase tracking-wider">
          {chart.title}
        </h4>
        <span
          className="w-2 h-2 rounded-full animate-pulse"
          style={{ backgroundColor: chart.color }}
        />
      </div>

      <div className="flex justify-center mb-4">
        {chart.type === "donut" && <DonutChart chart={chart} visible={visible} />}
        {chart.type === "bar" && <BarChart chart={chart} visible={visible} />}
        {chart.type === "gauge" && <GaugeChart chart={chart} visible={visible} />}
      </div>

      <p className="label-mono text-[10px] text-muted-foreground leading-relaxed border-t border-border/60 pt-3">
        {chart.insight}
      </p>
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────

const riskColors = {
  critical: {
    bg: "bg-red-500/10",
    border: "border-red-500/40",
    text: "text-red-400",
    dot: "#ef4444",
  },
  high: {
    bg: "bg-orange-500/10",
    border: "border-orange-500/40",
    text: "text-orange-400",
    dot: "#f97316",
  },
  medium: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/40",
    text: "text-amber-400",
    dot: "#eab308",
  },
  low: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/40",
    text: "text-emerald-400",
    dot: "#22c55e",
  },
};

export const InsightCharts: FC<Props> = ({ result }) => {
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);

    getInsights(result)
      .then((data) => {
        if (!cancelled) {
          setInsights(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(true);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [result.request_id]);

  const rc = riskColors[insights?.risk_level ?? "high"];

  return (
    <section className="mt-10 rounded-2xl border border-border/80 bg-card/50 p-6 md:p-8 shadow-xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-border">
        <div>
          <div className="flex items-center gap-2 label-mono text-xs text-muted-foreground mb-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            AI · Groq Llama 3.3-70b Analysis
          </div>
          <h3 className="text-xl font-bold text-foreground tracking-tight">
            Suggestive Insight Charts
          </h3>
        </div>
        {insights && (
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border ${rc.bg} ${rc.border}`}
          >
            <span
              className="w-2 h-2 rounded-full animate-pulse"
              style={{ backgroundColor: rc.dot }}
            />
            <span className={`label-mono text-xs font-bold uppercase ${rc.text}`}>
              {insights.risk_level} risk
            </span>
          </div>
        )}
      </div>

      {/* Loading skeleton */}
      {loading && (
        <div className="mt-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="h-4 w-4 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
            <span className="label-mono text-xs text-muted-foreground">
              Generating AI insights with Groq…
            </span>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="rounded-2xl border border-border/60 bg-background/50 p-5 animate-pulse"
                style={{ height: "220px" }}
              >
                <div className="h-3 w-24 bg-secondary rounded mb-4" />
                <div className="h-24 w-24 rounded-full bg-secondary/60 mx-auto mb-4" />
                <div className="h-2 w-full bg-secondary/40 rounded" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="mt-6 rounded-xl border border-border/60 bg-secondary/30 p-6 text-center">
          <span className="label-mono text-xs text-muted-foreground">
            AI insights temporarily unavailable. Core scan results are above.
          </span>
        </div>
      )}

      {/* Insights */}
      {insights && !loading && (
        <div className="mt-6 space-y-6">
          {/* Summary */}
          <div className={`rounded-xl border p-4 ${rc.bg} ${rc.border}`}>
            <p className={`text-sm leading-relaxed font-medium ${rc.text}`}>
              <strong>AI Summary:</strong> {insights.summary}
            </p>
          </div>

          {/* Charts grid */}
          <div className="grid gap-4 sm:grid-cols-3">
            {insights.charts.map((chart, i) => (
              <ChartCard key={chart.title} chart={chart} delay={i * 150} />
            ))}
          </div>

          {/* Action items */}
          {insights.action_items.length > 0 && (
            <div className="rounded-xl border border-border bg-background p-5">
              <div className="label-mono text-xs font-semibold text-foreground uppercase mb-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
                Recommended Actions
              </div>
              <ol className="space-y-2">
                {insights.action_items.map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-foreground">
                    <span className="shrink-0 flex items-center justify-center w-5 h-5 rounded-full border border-border label-mono text-[10px] text-muted-foreground font-bold mt-0.5">
                      {i + 1}
                    </span>
                    {item}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Confidence note */}
          <p className="label-mono text-[10px] text-muted-foreground/60 text-center">
            {insights.confidence_note}
          </p>
        </div>
      )}
    </section>
  );
};

export default InsightCharts;
