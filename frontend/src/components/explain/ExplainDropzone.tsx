import React, { useState, useRef } from "react";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Sparkles,
  Shield,
  Globe2,
} from "lucide-react";
import { getExplainStrings } from "@/lib/explainStrings";
import { getSampleExplanation } from "@/lib/__fixtures__/explain.sample";
import { DocExplanation } from "@/lib/api";

interface ExplainDropzoneProps {
  onExplain: (formData: FormData, selectedLang: string) => Promise<void>;
  onSampleSelect: (sample: DocExplanation, lang: string) => void;
  isLoading: boolean;
  language: string;
  onLanguageChange: (lang: string) => void;
}

const SAMPLE_TEXT_DOC = `NOTICE: High Yield Investment Program (HYIP) Guaranteed Growth Scheme 2026
Issuer: Apex Wealth Creators Pvt Ltd (CIN: U65999MH2022PTC123456)
Investment Structure:
1. Minimum Commitment: INR 50,000 for a tenure of 180 days.
2. Return Rate: Guaranteed 4.5% daily return with automatic weekly compounding.
3. Withdrawal Terms: Lock-in period of 30 days. 5% processing fee on premature redemption.
4. Referral Bonus: 10% direct commission on onboarding sub-tier investors.
5. Regulatory Note: Processing applied under Multi-State Cooperative Society rules. Not registered as SEBI Alternative Investment Fund.`;

export const ExplainDropzone: React.FC<ExplainDropzoneProps> = ({
  onExplain,
  onSampleSelect,
  isLoading,
  language,
  onLanguageChange,
}) => {
  const strings = getExplainStrings(language);
  const [activeTab, setActiveTab] = useState<"file" | "text">("file");
  const [file, setFile] = useState<File | null>(null);
  const [textInput, setTextInput] = useState("");
  const [includeStoryboard, setIncludeStoryboard] = useState(true);
  const [crosscheck, setCrosscheck] = useState(true);
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setValidationError(null);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValidationError(null);
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (f: File) => {
    const maxSizeBytes = 10 * 1024 * 1024; // 10MB
    if (f.size > maxSizeBytes) {
      setValidationError(strings.fileTooLargeError);
      setFile(null);
      return;
    }

    const ext = f.name.split(".").pop()?.toLowerCase();
    const validExtensions = ["pdf", "docx", "png", "jpg", "jpeg", "webp", "txt"];
    if (!ext || !validExtensions.includes(ext)) {
      setValidationError(strings.unsupportedFileError);
      setFile(null);
      return;
    }

    setFile(f);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    const formData = new FormData();
    formData.append("language", language);
    formData.append("include_storyboard", includeStoryboard ? "true" : "false");
    formData.append("crosscheck", crosscheck ? "true" : "false");

    if (activeTab === "file") {
      if (!file) {
        setValidationError(strings.emptyInputError);
        return;
      }
      formData.append("file", file);
    } else {
      if (!textInput.trim()) {
        setValidationError(strings.emptyInputError);
        return;
      }
      formData.append("text", textInput.trim());
    }

    await onExplain(formData, language);
  };

  const handleLoadSample = () => {
    const sample = getSampleExplanation(language);
    onSampleSelect(sample, language);
  };

  return (
    <div className="w-full max-w-3xl mx-auto rounded-3xl border bg-card/80 backdrop-blur-xl shadow-xl p-6 sm:p-8 space-y-6">
      {/* Header & Language Select */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2.5">
            <Sparkles className="w-6 h-6 text-primary" />
            {strings.pageTitle}
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">{strings.pageSubtitle}</p>
        </div>

        <div className="flex items-center gap-2">
          <Globe2 className="w-4 h-4 text-muted-foreground" />
          <select
            value={language}
            onChange={(e) => onLanguageChange(e.target.value)}
            className="px-3 py-1.5 rounded-lg border bg-background text-foreground text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-primary shadow-sm"
          >
            <option value="en">English (Default)</option>
            <option value="hi">हिन्दी (Hindi)</option>
            <option value="gu">ગુજરાતી (Gujarati)</option>
            <option value="hinglish">Hinglish</option>
            <option value="gujlish">Gujlish</option>
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 p-1 bg-secondary/50 rounded-xl border">
        <button
          type="button"
          onClick={() => setActiveTab("file")}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-bold transition-all ${
            activeTab === "file"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <UploadCloud className="w-4 h-4" />
          {strings.uploadTab}
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("text")}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-bold transition-all ${
            activeTab === "text"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <FileText className="w-4 h-4" />
          {strings.pasteTab}
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Upload Dropzone Tab */}
        {activeTab === "file" ? (
          <div>
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`relative flex flex-col items-center justify-center p-8 sm:p-10 border-2 border-dashed rounded-2xl cursor-pointer transition-all ${
                dragActive
                  ? "border-primary bg-primary/10 scale-[1.01]"
                  : file
                    ? "border-emerald-500/50 bg-emerald-500/5"
                    : "border-border hover:border-primary/50 bg-background/50 hover:bg-background/80"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.webp"
                onChange={handleFileChange}
              />

              {file ? (
                <div className="flex flex-col items-center text-center space-y-2">
                  <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-500 flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <span className="text-sm font-bold text-foreground">{file.name}</span>
                  <span className="text-xs text-muted-foreground font-mono">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </span>
                  <span className="text-[11px] text-primary hover:underline font-medium pt-1">
                    Click or drop another file to replace
                  </span>
                </div>
              ) : (
                <div className="flex flex-col items-center text-center space-y-2">
                  <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <div className="text-sm font-semibold text-foreground">
                    {strings.dragDropPrompt || strings.dropzoneTitle || "Drop your PDF, DOCX, or Image here, or click to browse"}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    PDF, DOCX, TXT, PNG, JPG, WEBP (Max 10 MB)
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Paste Text Tab */
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-foreground">Document Text</label>
              <button
                type="button"
                onClick={() => setTextInput(SAMPLE_TEXT_DOC)}
                className="text-[11px] text-primary font-medium hover:underline"
              >
                Insert Sample Investment Text
              </button>
            </div>
            <textarea
              rows={6}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Paste financial agreement, terms, mutual fund notice, IPO circular, or loan documentation..."
              className="w-full p-4 rounded-xl border bg-background/80 text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary shadow-inner font-mono resize-y"
            />
          </div>
        )}

        {/* Validation Error */}
        {validationError && (
          <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs font-medium flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{validationError}</span>
          </div>
        )}

        {/* Options */}
        <div className="grid sm:grid-cols-2 gap-3 pt-2">
          <label className="flex items-center gap-2.5 p-3 rounded-xl border bg-background/40 cursor-pointer hover:bg-background/80 transition-all">
            <input
              type="checkbox"
              checked={includeStoryboard}
              onChange={(e) => setIncludeStoryboard(e.target.checked)}
              className="rounded text-primary focus:ring-primary h-4 w-4"
            />
            <div className="text-xs">
              <span className="font-semibold block text-foreground">
                {strings.videoOptionLabel || strings.generateVideoStoryboard || "Generate Storyboard & Video Walkthrough"}
              </span>
              <span className="text-[11px] text-muted-foreground">
                {strings.videoOptionHint || strings.videoOptionDesc || "Creates scene narration and visual breakdown for video walkthrough"}
              </span>
            </div>
          </label>

          <label className="flex items-center gap-2.5 p-3 rounded-xl border bg-background/40 cursor-pointer hover:bg-background/80 transition-all">
            <input
              type="checkbox"
              checked={crosscheck}
              onChange={(e) => setCrosscheck(e.target.checked)}
              className="rounded text-primary focus:ring-primary h-4 w-4"
            />
            <div className="text-xs">
              <span className="font-semibold block text-foreground flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-primary inline" />
                {strings.crosscheckLabel || strings.crosscheckOption || "Also check this document for scam red flags"}
              </span>
              <span className="text-[11px] text-muted-foreground">
                {strings.crosscheckHint || strings.crosscheckOptionDesc || "Runs Ruko's 12 red-flag detectors and SEBI registry matching in parallel."}
              </span>
            </div>
          </label>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={isLoading}
            className="w-full sm:flex-1 py-3 px-6 rounded-xl bg-primary text-primary-foreground font-bold text-sm shadow-lg hover:bg-primary/90 disabled:opacity-50 transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-98"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{strings.analyzingDocument || strings.loadingReading || "Analyzing Document..."}</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>{strings.explainButton || strings.submitBtn || "Explain Document"}</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleLoadSample}
            disabled={isLoading}
            className="w-full sm:w-auto py-3 px-5 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs font-semibold border transition-all cursor-pointer whitespace-nowrap"
          >
            {strings.trySampleDemo || strings.trySampleBtn || "Try a sample loan agreement"}
          </button>
        </div>
      </form>
    </div>
  );
};
