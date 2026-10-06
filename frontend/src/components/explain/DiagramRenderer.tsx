import React, { useId, useMemo, useState } from "react";
import dagre from "@dagrejs/dagre";
import type { FlowGraph, TimelineItem } from "../../lib/api";
import { Download, Calendar, HelpCircle, AlertCircle } from "lucide-react";

// Wrap text cleanly into multiple lines for SVG / Canvas rendering
export function wrapSvgText(text: string, maxCharsPerLine = 18): string[] {
  if (!text) return [""];
  const words = String(text).split(" ");
  const lines: string[] = [];
  let currentLine = "";

  for (const word of words) {
    if ((currentLine + " " + word).trim().length <= maxCharsPerLine) {
      currentLine = (currentLine + " " + word).trim();
    } else {
      if (currentLine) lines.push(currentLine);
      currentLine = word;
    }
  }
  if (currentLine) lines.push(currentLine);
  return lines.length > 0 ? lines : [text];
}

interface NodeLayout {
  id: string;
  label: string;
  kind: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface EdgeLayout {
  source: string;
  target: string;
  label?: string | null;
  points: { x: number; y: number }[];
}

export function computeDagreLayout(graph?: FlowGraph | null): {
  nodes: NodeLayout[];
  edges: EdgeLayout[];
  width: number;
  height: number;
} {
  if (!graph || !Array.isArray(graph.nodes) || graph.nodes.length === 0) {
    return { nodes: [], edges: [], width: 0, height: 0 };
  }

  const g = new dagre.graphlib.Graph();
  g.setGraph({
    rankdir: "TB",
    nodesep: 35,
    ranksep: 45,
    marginx: 30,
    marginy: 30,
  });
  g.setDefaultEdgeLabel(() => ({}));

  const nodeWidth = 170;
  const nodeHeight = 64;

  for (const node of graph.nodes) {
    if (!node || !node.id) continue;
    g.setNode(node.id, {
      width: node.kind === "decision" ? 180 : nodeWidth,
      height: node.kind === "decision" ? 72 : nodeHeight,
      label: node.label || node.id,
      kind: node.kind || "step",
    });
  }

  if (Array.isArray(graph.edges)) {
    for (const edge of graph.edges) {
      if (edge && edge.source && edge.target) {
        g.setEdge(edge.source, edge.target, { label: edge.label || "" });
      }
    }
  }

  try {
    dagre.layout(g);
  } catch (err) {
    console.warn("Dagre layout error:", err);
  }

  const nodes: NodeLayout[] = [];
  g.nodes().forEach((v) => {
    const n = g.node(v);
    if (n) {
      nodes.push({
        id: v,
        label: n.label || v,
        kind: (n as { kind?: string }).kind || "step",
        x: n.x,
        y: n.y,
        width: n.width,
        height: n.height,
      });
    }
  });

  const edges: EdgeLayout[] = [];
  g.edges().forEach((e) => {
    const edgeData = g.edge(e);
    if (edgeData) {
      edges.push({
        source: e.v,
        target: e.w,
        label: (edgeData as { label?: string }).label || null,
        points: edgeData.points || [],
      });
    }
  });

  const graphInfo = g.graph();
  const width = Math.max(360, (graphInfo?.width || 500) + 40);
  const height = Math.max(200, (graphInfo?.height || 300) + 40);

  return { nodes, edges, width, height };
}

// Convert SVG to PNG
export function downloadSvgAsPng(svgElement: SVGSVGElement, filename: string): void {
  try {
    const svgString = new XMLSerializer().serializeToString(svgElement);
    const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);
    const img = new Image();

    img.onload = () => {
      const canvas = document.createElement("canvas");
      const scale = 2;
      canvas.width = (svgElement.viewBox.baseVal.width || 600) * scale;
      canvas.height = (svgElement.viewBox.baseVal.height || 400) * scale;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.fillStyle = "#090d16";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        const pngUrl = canvas.toDataURL("image/png");
        const a = document.createElement("a");
        a.href = pngUrl;
        a.download = `${filename}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
      URL.revokeObjectURL(url);
    };
    img.src = url;
  } catch (e) {
    console.error("Failed to export SVG to PNG:", e);
  }
}

// Draw diagram directly on HTML5 2D canvas (for VideoExplainer)
export function drawFlowGraphToCanvas(
  ctx: CanvasRenderingContext2D,
  graph: FlowGraph,
  centerX: number,
  centerY: number,
  maxWidth: number,
  maxHeight: number,
  title?: string,
): void {
  const { nodes, edges, width, height } = computeDagreLayout(graph);
  if (width === 0 || height === 0 || nodes.length === 0) {
    ctx.fillStyle = "#94a3b8";
    ctx.font = "italic 16px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Diagram data unavailable for this document.", centerX, centerY);
    return;
  }

  // Draw title
  if (title || graph.title) {
    ctx.fillStyle = "#38bdf8";
    ctx.font = "bold 22px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(title || graph.title, centerX - maxWidth / 2 + 10, centerY - maxHeight / 2 + 25);
  }

  const scale = Math.min(1.0, (maxWidth - 40) / width, (maxHeight - 60) / height);
  const offsetX = centerX - (width * scale) / 2;
  const offsetY = centerY + 15 - (height * scale) / 2;

  ctx.save();
  ctx.translate(offsetX, offsetY);
  ctx.scale(scale, scale);

  // 1. Draw edges
  for (const edge of edges) {
    if (!edge.points || edge.points.length < 2) continue;
    ctx.beginPath();
    ctx.moveTo(edge.points[0].x, edge.points[0].y);
    for (let i = 1; i < edge.points.length; i++) {
      ctx.lineTo(edge.points[i].x, edge.points[i].y);
    }
    ctx.strokeStyle = "#475569";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Arrowhead
    const last = edge.points[edge.points.length - 1];
    const prev = edge.points[edge.points.length - 2];
    const angle = Math.atan2(last.y - prev.y, last.x - prev.x);
    ctx.beginPath();
    ctx.moveTo(last.x, last.y);
    ctx.lineTo(
      last.x - 10 * Math.cos(angle - Math.PI / 6),
      last.y - 10 * Math.sin(angle - Math.PI / 6),
    );
    ctx.lineTo(
      last.x - 10 * Math.cos(angle + Math.PI / 6),
      last.y - 10 * Math.sin(angle + Math.PI / 6),
    );
    ctx.closePath();
    ctx.fillStyle = "#38bdf8";
    ctx.fill();

    // Edge label
    if (edge.label) {
      const mid = edge.points[Math.floor(edge.points.length / 2)];
      ctx.fillStyle = "#94a3b8";
      ctx.font = "11px system-ui, -apple-system, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(edge.label, mid.x + 10, mid.y - 4);
    }
  }

  // 2. Draw nodes
  for (const node of nodes) {
    const x = node.x - node.width / 2;
    const y = node.y - node.height / 2;

    ctx.save();
    if (node.kind === "start" || node.kind === "end") {
      ctx.fillStyle = node.kind === "start" ? "#064e3b" : "#3b0764";
      ctx.strokeStyle = node.kind === "start" ? "#10b981" : "#c084fc";
      ctx.lineWidth = 2;
      roundRect(ctx, x, y, node.width, node.height, node.height / 2);
    } else if (node.kind === "money") {
      ctx.fillStyle = "#0c4a6e";
      ctx.strokeStyle = "#38bdf8";
      ctx.lineWidth = 2;
      roundRect(ctx, x, y, node.width, node.height, 10);
    } else if (node.kind === "decision") {
      ctx.fillStyle = "#78350f";
      ctx.strokeStyle = "#f59e0b";
      ctx.lineWidth = 2;
      roundRect(ctx, x, y, node.width, node.height, 12);
    } else {
      ctx.fillStyle = "#1e293b";
      ctx.strokeStyle = "#64748b";
      ctx.lineWidth = 1.5;
      roundRect(ctx, x, y, node.width, node.height, 8);
    }

    ctx.fillStyle = "#f8fafc";
    ctx.font = "bold 13px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const lines = wrapSvgText(node.label, 16);
    const lineHeight = 16;
    const startTextY = node.y - ((lines.length - 1) * lineHeight) / 2;
    lines.forEach((l, i) => {
      ctx.fillText(l, node.x, startTextY + i * lineHeight);
    });
    ctx.restore();
  }

  ctx.restore();
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
): void {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
}

interface FlowGraphRendererProps {
  graph?: FlowGraph | null;
  flowGraph?: FlowGraph | null;
  title?: string;
  downloadLabel?: string;
}

export const FlowGraphRenderer: React.FC<FlowGraphRendererProps> = (props) => {
  const targetGraph = props.graph || props.flowGraph;
  const title = props.title || targetGraph?.title || "Flow Diagram";
  const downloadLabel = props.downloadLabel || "Download PNG";
  const uniqueId = useId().replace(/:/g, "_");

  const { nodes, edges, width, height } = useMemo(
    () => computeDagreLayout(targetGraph),
    [targetGraph],
  );

  if (
    !targetGraph ||
    !Array.isArray(targetGraph.nodes) ||
    targetGraph.nodes.length === 0 ||
    nodes.length === 0
  ) {
    return (
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <h4 className="text-base font-semibold text-foreground pb-2">{title}</h4>
        <div className="p-6 rounded-xl border border-dashed text-center text-sm text-muted-foreground flex items-center justify-center gap-2">
          <AlertCircle className="w-4 h-4 text-muted-foreground" />
          <span>Diagram data unavailable for this document.</span>
        </div>
      </div>
    );
  }

  const handleDownload = () => {
    const svg = document.getElementById(`svg-${uniqueId}`) as SVGSVGElement | null;
    if (svg) {
      downloadSvgAsPng(svg, title.toLowerCase().replace(/\s+/g, "_"));
    }
  };

  const getNodeColors = (kind: string) => {
    switch (kind) {
      case "start":
        return {
          bg: "fill-emerald-950/80 dark:fill-emerald-950/90",
          border: "stroke-emerald-500",
          text: "fill-emerald-200",
        };
      case "end":
        return {
          bg: "fill-purple-950/80 dark:fill-purple-950/90",
          border: "stroke-purple-400",
          text: "fill-purple-200",
        };
      case "money":
        return {
          bg: "fill-cyan-950/80 dark:fill-cyan-950/90",
          border: "stroke-cyan-400",
          text: "fill-cyan-200",
        };
      case "party":
        return {
          bg: "fill-indigo-950/80 dark:fill-indigo-950/90",
          border: "stroke-indigo-400",
          text: "fill-indigo-200",
        };
      case "decision":
        return {
          bg: "fill-amber-950/80 dark:fill-amber-950/90",
          border: "stroke-amber-400",
          text: "fill-amber-200",
        };
      default:
        return {
          bg: "fill-slate-900/90 dark:fill-slate-900/90",
          border: "stroke-slate-600",
          text: "fill-slate-100",
        };
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-card p-5 md:p-6 shadow-md">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-border">
        <h4 className="text-base font-semibold text-foreground flex items-center gap-2">
          <span>{title}</span>
        </h4>
        <button
          onClick={handleDownload}
          className="inline-flex items-center gap-1.5 rounded-md border border-border bg-secondary/80 px-3 py-1.5 text-xs font-mono text-foreground hover:bg-secondary transition-all"
        >
          <Download className="w-3.5 h-3.5" />
          <span>{downloadLabel}</span>
        </button>
      </div>

      <div className="mt-4 overflow-x-auto rounded-xl bg-slate-950 p-4 flex justify-center">
        <svg
          id={`svg-${uniqueId}`}
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          className="max-w-full h-auto"
        >
          <defs>
            <marker
              id={`arrow-${uniqueId}`}
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8" />
            </marker>
          </defs>

          {/* Edges */}
          {edges.map((edge, idx) => {
            if (edge.points.length < 2) return null;
            const pathD = edge.points.reduce(
              (acc, p, i) => `${acc} ${i === 0 ? "M" : "L"} ${p.x} ${p.y}`,
              "",
            );
            const midPoint = edge.points[Math.floor(edge.points.length / 2)];

            return (
              <g key={idx} className="group">
                <path
                  d={pathD}
                  fill="none"
                  stroke="#475569"
                  strokeWidth="2"
                  markerEnd={`url(#arrow-${uniqueId})`}
                  className="transition-colors group-hover:stroke-cyan-400"
                />
                {edge.label && (
                  <text
                    x={midPoint.x + 10}
                    y={midPoint.y - 4}
                    textAnchor="middle"
                    fill="#94a3b8"
                    fontSize="11"
                    fontFamily="sans-serif"
                    className="select-none bg-slate-950"
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const colors = getNodeColors(node.kind);
            const lines = wrapSvgText(node.label, 17);
            const rx = node.kind === "start" || node.kind === "end" ? 22 : 8;

            return (
              <g
                key={node.id}
                transform={`translate(${node.x - node.width / 2}, ${node.y - node.height / 2})`}
              >
                <rect
                  width={node.width}
                  height={node.height}
                  rx={rx}
                  className={`${colors.bg} ${colors.border} transition-all`}
                  strokeWidth="1.75"
                />
                <text
                  x={node.width / 2}
                  y={node.height / 2 - ((lines.length - 1) * 15) / 2}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className={`${colors.text} font-medium text-xs select-none`}
                  fontFamily="sans-serif"
                >
                  {lines.map((l, i) => (
                    <tspan key={i} x={node.width / 2} dy={i === 0 ? 0 : 15}>
                      {l}
                    </tspan>
                  ))}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

interface TimelineRendererProps {
  items?: TimelineItem[] | null;
  timeline?: TimelineItem[] | null;
  title?: string;
  whereLabel?: string;
}

export const TimelineRenderer: React.FC<TimelineRendererProps> = (props) => {
  const rawItems = props.items || props.timeline;
  const title = props.title || "Important Milestones & Dates";
  const whereLabel = props.whereLabel || "Where in document?";
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  const toggle = (idx: number) => {
    setExpanded((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  if (!rawItems || !Array.isArray(rawItems) || rawItems.length === 0) {
    return (
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <h4 className="text-base font-semibold text-foreground pb-2">{title}</h4>
        <div className="p-6 rounded-xl border border-dashed text-center text-sm text-muted-foreground flex items-center justify-center gap-2">
          <AlertCircle className="w-4 h-4 text-muted-foreground" />
          <span>Diagram data unavailable for this document.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-border bg-card p-5 md:p-6 shadow-md">
      <h4 className="text-base font-semibold text-foreground flex items-center gap-2 pb-4 border-b border-border">
        <Calendar className="w-4 h-4 text-cyan-400" />
        <span>{title}</span>
      </h4>

      <div className="mt-6 relative pl-6 md:pl-8 space-y-6 before:absolute before:left-2.5 md:before:left-3.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-gradient-to-b before:from-cyan-500 before:via-blue-500 before:to-purple-500">
        {rawItems.map((it: TimelineItem, idx: number) => {
          const dateText =
            it.date_text ||
            (it as { time_reference?: string }).time_reference ||
            `Phase ${idx + 1}`;
          const labelText = it.label || (it as { event?: string }).event || "Milestone";
          const evidenceText = it.evidence || (it as { significance?: string }).significance;

          return (
            <div key={idx} className="relative group">
              {/* Timeline Dot */}
              <div className="absolute -left-[23px] md:-left-[27px] top-1.5 w-3.5 h-3.5 rounded-full border-2 border-cyan-400 bg-background group-hover:scale-125 transition-transform" />

              <div className="rounded-xl border border-border/80 bg-background/70 p-4 shadow-sm hover:border-cyan-500/40 transition-colors">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 font-semibold">
                    {dateText}
                  </span>
                  {evidenceText && (
                    <button
                      onClick={() => toggle(idx)}
                      className="text-[11px] font-mono text-muted-foreground hover:text-cyan-400 transition-colors underline cursor-pointer"
                    >
                      {expanded[idx] ? "Hide quote" : whereLabel}
                    </button>
                  )}
                </div>

                <p className="mt-2 text-sm font-medium text-foreground leading-snug font-sans">
                  {labelText}
                </p>

                {evidenceText && expanded[idx] && (
                  <div className="mt-2.5 rounded-lg bg-secondary/60 px-3 py-2 text-xs font-mono text-cyan-300 border border-border/60">
                    <span className="text-muted-foreground block text-[10px] uppercase font-sans">
                      Exact Source Evidence:
                    </span>
                    &ldquo;{evidenceText}&rdquo;
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
