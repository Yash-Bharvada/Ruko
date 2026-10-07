import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import {
  Sparkles,
  ArrowLeft,
  FileText,
  GitFork,
  Video,
  BookOpen,
  Info,
  AlertTriangle,
  ShieldCheck,
  RotateCcw,
} from "lucide-react";
import RukoLogo from "../components/RukoLogo";
import ThemeToggle from "../components/ThemeToggle";
import { DocExplanation, KeyPoint, Step, GlossaryItem, explainDocument } from "@/lib/api";
import { getExplainStrings } from "@/lib/explainStrings";
import { ExplainDropzone } from "@/components/explain/ExplainDropzone";
import { ExplainReasonCard } from "@/components/explain/ExplainReasonCard";
import { FlowGraphRenderer, TimelineRenderer } from "@/components/explain/DiagramRenderer";
import { VideoExplainer } from "@/components/explain/VideoExplainer";
import { toast } from "sonner";

export const Route = createFileRoute("/explain")({
  head: () => ({
    meta: [
      { title: "Ruko AI — Explain Financial Documents" },
      {
        name: "description",
        content:
          "Transform complex financial terms, loan agreements, circulars, and investment proposals into plain-language summaries, interactive flowcharts, timelines, and browser-rendered explainer videos.",
      },
      { property: "og:title", content: "Ruko AI — Document Explainer" },
    ],
  }),
  component: ExplainPage,
});

function ExplainPage() {
  const [language, setLanguage] = useState<string>("en");
  const [explanation, setExplanation] = useState<DocExplanation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<
    "summary" | "diagrams" | "video" | "glossary" | "details"
  >("summary");
  const [glossarySearch, setGlossarySearch] = useState("");

  const strings = getExplainStrings(language);

  // Clear document state on unmount (zero client persistence)
  useEffect(() => {
    return () => {
      setExplanation(null);
    };
  }, []);

  const handleExplain = async (formData: FormData, selectedLang: string) => {
    setIsLoading(true);
    setLanguage(selectedLang);
    try {
      const result = await explainDocument(formData);
      setExplanation(result);
      setActiveTab("summary");
      toast.success("Document analyzed and explained successfully!");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to analyze document.";
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSampleSelect = (sample: DocExplanation, lang: string) => {
    setLanguage(lang);
    setExplanation(sample);
    setActiveTab("summary");
    toast.info(`Loaded sample explanation in ${lang.toUpperCase()}`);
  };

  const handleReset = () => {
    setExplanation(null);
    setActiveTab("summary");
  };

  const glossaryList = explanation?.glossary || [];
  const filteredGlossary = glossaryList.filter((g: GlossaryItem) => {
    const termStr = (g.term || "").toLowerCase();
    const meaningStr = (g.meaning || g.simple_explanation || "").toLowerCase();
    const q = glossarySearch.toLowerCase();
    return termStr.includes(q) || meaningStr.includes(q);
  });

  const hasAnyDiagram = Boolean(
    (explanation?.diagrams?.flowchart?.nodes && explanation.diagrams.flowchart.nodes.length > 0) ||
    (explanation?.diagrams?.money_flow?.nodes &&
      explanation.diagrams.money_flow.nodes.length > 0) ||
    (explanation?.diagrams?.timeline && explanation.diagrams.timeline.length > 0),
  );

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans transition-colors duration-300">
      {/* Top Navigation */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-background/80 border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="flex items-center gap-2 hover:opacity-90 transition-opacity">
              <RukoLogo className="h-8 w-auto" />
            </Link>

            <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
              <Link
                to="/"
                className="px-3 py-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors"
              >
                Fraud Check
              </Link>
              <Link
                to="/explain"
                className="px-3 py-1.5 rounded-lg text-primary bg-primary/10 font-semibold"
              >
                Explain Document
              </Link>
              <Link
                to="/model-stats"
                className="px-3 py-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors"
              >
                Model Stats
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border bg-secondary/50 text-foreground hover:bg-secondary transition-all"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back to Check
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {!explanation ? (
          /* Dropzone & Document Input View */
          <div className="space-y-8 animate-in fade-in duration-300">
            <div className="text-center max-w-2xl mx-auto space-y-3">
              <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold tracking-wide uppercase">
                <Sparkles className="w-3.5 h-3.5" />
                Plain-Language Financial Intelligence
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
                Understand Any Financial Document
              </h1>
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                Upload investment circulars, loan agreements, mutual fund terms, or notices. Get
                verified plain-language breakdowns, interactive visual flowcharts, and
                browser-narrated videos in English, हिन्दी, and ગુજરાતી.
              </p>
            </div>

            <ExplainDropzone
              onExplain={handleExplain}
              onSampleSelect={handleSampleSelect}
              isLoading={isLoading}
              language={language}
              onLanguageChange={setLanguage}
            />

            {/* Privacy & Safety Guarantees */}
            <div className="grid sm:grid-cols-3 gap-4 max-w-3xl mx-auto pt-6 text-center">
              <div className="p-4 rounded-2xl border bg-card/40">
                <ShieldCheck className="w-5 h-5 text-emerald-500 mx-auto mb-2" />
                <h4 className="text-xs font-bold text-foreground">Zero Client Storage</h4>
                <p className="text-[11px] text-muted-foreground mt-1">
                  No documents are cached or stored on your device or browser.
                </p>
              </div>
              <div className="p-4 rounded-2xl border bg-card/40">
                <GitFork className="w-5 h-5 text-primary mx-auto mb-2" />
                <h4 className="text-xs font-bold text-foreground">Visual Diagram Engine</h4>
                <p className="text-[11px] text-muted-foreground mt-1">
                  Deterministic graph & timeline generation from verified facts.
                </p>
              </div>
              <div className="p-4 rounded-2xl border bg-card/40">
                <Video className="w-5 h-5 text-indigo-500 mx-auto mb-2" />
                <h4 className="text-xs font-bold text-foreground">In-Browser Video</h4>
                <p className="text-[11px] text-muted-foreground mt-1">
                  1280×720 video synthesized directly in browser with no server disk writes.
                </p>
              </div>
            </div>
          </div>
        ) : (
          /* Explanation Results View */
          <div className="space-y-6 animate-in fade-in duration-300">
            {/* Top Bar with Document Title & Reset */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl border bg-card/80 backdrop-blur-md shadow-sm">
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
                    {explanation.doc_type_guess ||
                      explanation.document_type ||
                      "Financial Document"}
                  </span>
                  <span className="text-xs font-medium text-muted-foreground font-mono">
                    ID: {explanation.request_id || "req_live"}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-secondary border uppercase">
                    {explanation.language || language}
                  </span>
                </div>
                <h2 className="text-xl sm:text-2xl font-extrabold text-foreground tracking-tight">
                  Document Analysis & Explanation
                </h2>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleReset}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border bg-secondary/80 hover:bg-secondary text-foreground text-xs font-bold transition-all shadow-sm active:scale-98 cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>New Document</span>
                </button>
              </div>
            </div>

            {/* Disclaimer Banner */}
            <div className="p-3.5 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-950 dark:text-amber-200 text-xs flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
              <div className="flex-1 leading-relaxed">
                <span className="font-bold">
                  {strings.disclaimerTitle || "Educational Notice & Disclaimer"}:
                </span>{" "}
                {explanation.disclaimer ||
                  "Ruko is an automated educational tool for scam detection. It is not financial advice, legal advice, or a guarantee of safety. Always verify independently with official regulators such as SEBI."}
              </div>
            </div>

            {/* Degraded Notice (Only when degraded items exist) */}
            {explanation.degraded && explanation.degraded.length > 0 && (
              <div className="p-3.5 rounded-xl border border-blue-500/30 bg-blue-500/10 text-blue-950 dark:text-blue-200 text-xs flex items-start gap-2.5">
                <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <span className="font-bold">Notice:</span>{" "}
                  {explanation.degraded.includes("advice_filtered")
                    ? "Certain advice-oriented expressions were neutralized to maintain strictly objective reporting. "
                    : ""}
                  {explanation.degraded.includes("llm_unavailable")
                    ? "LLM service was temporarily unavailable; fallback text extraction was used. "
                    : ""}
                  {explanation.degraded.includes("truncated")
                    ? "Document was truncated to meet size limits. "
                    : ""}
                  Analysis remains grounded in document text.
                </div>
              </div>
            )}

            {/* Red Flags & Crosscheck Card */}
            <ExplainReasonCard explanation={explanation} language={language} />

            {/* Navigation Tabs */}
            <div className="flex items-center gap-2 border-b border-border pb-1 overflow-x-auto">
              <button
                onClick={() => setActiveTab("summary")}
                className={`flex items-center gap-2 px-4 py-2.5 border-b-2 text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === "summary"
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                }`}
              >
                <FileText className="w-4 h-4" />
                <span>{strings.tabSummary || "Summary"}</span>
              </button>

              <button
                onClick={() => setActiveTab("diagrams")}
                className={`flex items-center gap-2 px-4 py-2.5 border-b-2 text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === "diagrams"
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                }`}
              >
                <GitFork className="w-4 h-4" />
                <span>{strings.tabDiagrams || "Diagrams"}</span>
              </button>

              {explanation.storyboard && explanation.storyboard.length > 0 && (
                <button
                  onClick={() => setActiveTab("video")}
                  className={`flex items-center gap-2 px-4 py-2.5 border-b-2 text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                    activeTab === "video"
                      ? "border-primary text-primary"
                      : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                  }`}
                >
                  <Video className="w-4 h-4" />
                  <span>{strings.tabVideo || "Video"}</span>
                </button>
              )}

              {glossaryList.length > 0 && (
                <button
                  onClick={() => setActiveTab("glossary")}
                  className={`flex items-center gap-2 px-4 py-2.5 border-b-2 text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                    activeTab === "glossary"
                      ? "border-primary text-primary"
                      : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                  }`}
                >
                  <BookOpen className="w-4 h-4" />
                  <span>
                    {strings.tabGlossary || "Glossary"} ({glossaryList.length})
                  </span>
                </button>
              )}

              <button
                onClick={() => setActiveTab("details")}
                className={`flex items-center gap-2 px-4 py-2.5 border-b-2 text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === "details"
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                }`}
              >
                <Info className="w-4 h-4" />
                <span>{strings.tabDetails || "Details"}</span>
              </button>
            </div>

            {/* TAB CONTENTS */}

            {/* 1. Summary Tab */}
            {activeTab === "summary" && (
              <div className="space-y-6">
                {/* Executive Summary Card */}
                <div className="p-6 rounded-2xl border bg-card/80 backdrop-blur-md space-y-3 shadow-sm">
                  <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                    <FileText className="w-4 h-4 text-primary" />
                    <span>Executive Summary</span>
                  </h3>
                  <p className="text-sm sm:text-base text-foreground/90 leading-relaxed font-normal whitespace-pre-wrap">
                    {explanation.summary}
                  </p>
                </div>

                {/* Key Points */}
                {explanation.key_points && explanation.key_points.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
                      {strings.keyTakeaways || "Key Obligations & Clauses"} (
                      {explanation.key_points.length})
                    </h3>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {explanation.key_points.map((kp: KeyPoint, idx) => (
                        <div
                          key={kp.id || idx}
                          className="p-4 rounded-xl border bg-card/60 hover:bg-card/90 transition-all space-y-2"
                        >
                          <div className="flex items-center gap-2">
                            <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center shrink-0">
                              {idx + 1}
                            </span>
                            {kp.category && (
                              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-secondary text-muted-foreground capitalize">
                                {kp.category}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-foreground/90 font-medium leading-relaxed">
                            {kp.text || kp.point}
                          </p>
                          {kp.evidence && (
                            <p className="text-xs text-muted-foreground font-mono bg-background/60 p-2 rounded border">
                              &ldquo;{kp.evidence}&rdquo;
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Steps */}
                {explanation.steps && explanation.steps.length > 0 && (
                  <div className="space-y-3 pt-2">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
                      {strings.actionableSteps || "Action Steps & Process"} (
                      {explanation.steps.length})
                    </h3>
                    <div className="space-y-3">
                      {explanation.steps.map((step: Step, idx) => (
                        <div
                          key={idx}
                          className="p-4 rounded-xl border bg-card/60 flex items-start gap-4 transition-all"
                        >
                          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold text-sm flex items-center justify-center shrink-0">
                            {step.order || step.step_number || idx + 1}
                          </div>
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center justify-between gap-2">
                              <h4 className="text-sm font-bold text-foreground">
                                {step.title || `Step ${idx + 1}`}
                              </h4>
                              {step.deadline && (
                                <span className="text-xs text-amber-600 dark:text-amber-400 font-medium">
                                  Deadline: {step.deadline}
                                </span>
                              )}
                            </div>
                            <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                              {step.text || step.description}
                            </p>
                            {step.evidence && (
                              <p className="text-xs text-muted-foreground font-mono bg-background/50 p-2 rounded border mt-2">
                                Quote: &ldquo;{step.evidence}&rdquo;
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 2. Diagrams Tab */}
            {activeTab === "diagrams" && (
              <div className="space-y-8">
                {explanation.diagrams?.flowchart && (
                  <FlowGraphRenderer
                    graph={explanation.diagrams.flowchart}
                    title={strings.flowchartTitle || "Process Flowchart"}
                  />
                )}

                {explanation.diagrams?.money_flow && (
                  <FlowGraphRenderer
                    graph={explanation.diagrams.money_flow}
                    title={strings.moneyFlowTitle || "Money & Payment Flow"}
                  />
                )}

                {explanation.diagrams?.timeline && (
                  <TimelineRenderer
                    items={explanation.diagrams.timeline}
                    title={strings.timelineTitle || "Important Milestones & Dates"}
                  />
                )}

                {!hasAnyDiagram && (
                  <div className="p-8 text-center rounded-2xl border bg-card/40 text-muted-foreground">
                    <p className="text-sm">
                      {strings.noDiagramsAvailable || "Diagram data unavailable for this document."}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* 3. Video Tab */}
            {activeTab === "video" && (
              <VideoExplainer explanation={explanation} language={language} />
            )}

            {/* 4. Glossary Tab */}
            {activeTab === "glossary" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between gap-4 flex-wrap">
                  <h3 className="text-base font-bold text-foreground">
                    Financial Glossary ({filteredGlossary.length})
                  </h3>
                  <input
                    type="text"
                    value={glossarySearch}
                    onChange={(e) => setGlossarySearch(e.target.value)}
                    placeholder="Search terms..."
                    className="px-3 py-1.5 rounded-lg border bg-background text-xs focus:ring-2 focus:ring-primary w-64 shadow-sm"
                  />
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  {filteredGlossary.map((item: GlossaryItem, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl border bg-card/70 hover:bg-card space-y-2 transition-all"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-bold text-sm text-primary">{item.term}</span>
                        {item.term_devanagari && (
                          <span className="text-xs text-muted-foreground font-medium">
                            {item.term_devanagari}
                          </span>
                        )}
                        {item.term_gujarati && (
                          <span className="text-xs text-muted-foreground font-medium">
                            {item.term_gujarati}
                          </span>
                        )}
                      </div>
                      <p className="text-xs sm:text-sm text-foreground/90 leading-relaxed">
                        {item.meaning || item.simple_explanation}
                      </p>
                      {(item.evidence || item.context_in_doc) && (
                        <p className="text-xs text-muted-foreground italic border-t pt-2">
                          Evidence: &ldquo;{item.evidence || item.context_in_doc}&rdquo;
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 5. Details Tab */}
            {activeTab === "details" && (
              <div className="space-y-6">
                <div className="grid sm:grid-cols-2 gap-4">
                  <div className="p-5 rounded-2xl border bg-card/70 space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Document Metadata
                    </h4>
                    <dl className="space-y-2 text-xs">
                      <div className="flex justify-between py-1 border-b">
                        <dt className="text-muted-foreground">Document Type</dt>
                        <dd className="font-semibold text-foreground">
                          {explanation.doc_type_guess || explanation.document_type || "General"}
                        </dd>
                      </div>
                      <div className="flex justify-between py-1 border-b">
                        <dt className="text-muted-foreground">Language</dt>
                        <dd className="font-semibold text-foreground uppercase">
                          {explanation.language || language}
                        </dd>
                      </div>
                      <div className="flex justify-between py-1 border-b">
                        <dt className="text-muted-foreground">Request ID</dt>
                        <dd className="font-mono text-muted-foreground">
                          {explanation.request_id || "N/A"}
                        </dd>
                      </div>
                      <div className="flex justify-between py-1">
                        <dt className="text-muted-foreground">Generated Scenes</dt>
                        <dd className="font-semibold text-foreground">
                          {explanation.storyboard?.length || 0}
                        </dd>
                      </div>
                    </dl>
                  </div>

                  <div className="p-5 rounded-2xl border bg-card/70 space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Analysis Confidence & Quality
                    </h4>
                    <div className="flex justify-between text-xs font-semibold py-1 border-b">
                      <span className="text-muted-foreground">OCR Quality</span>
                      <span className="font-mono capitalize text-foreground">
                        {explanation.ocr_quality || "N/A"}
                      </span>
                    </div>

                    {explanation.confidence_notes && explanation.confidence_notes.length > 0 && (
                      <div className="p-3 rounded-lg bg-secondary/50 border text-xs text-muted-foreground leading-relaxed space-y-1">
                        <span className="font-semibold text-foreground block">
                          Notes & Observations:
                        </span>
                        {explanation.confidence_notes.map((note, idx) => (
                          <p key={idx}>• {note}</p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border/40 py-6 mt-12 bg-background/50">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-muted-foreground space-y-1">
          <p>© {new Date().getFullYear()} Ruko AI. Indian Financial Protection Engine.</p>
          <p className="text-[11px] text-muted-foreground/70">
            Automated explanatory analysis for educational awareness. Not certified legal or
            investment advice.
          </p>
        </div>
      </footer>
    </div>
  );
}
