import React, { useState, useEffect, useRef } from "react";
import {
  Play,
  Pause,
  Download,
  Loader2,
  RefreshCw,
  XCircle,
  Volume2,
  VolumeX,
  Sparkles,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Film,
} from "lucide-react";
import { DocExplanation } from "@/lib/api";
import { getExplainStrings } from "@/lib/explainStrings";
import {
  prepareSceneAudio,
  composeStoryboardVideo,
  CompositionProgress,
  renderSceneFrame,
} from "@/lib/videoComposer";

interface VideoExplainerProps {
  explanation: DocExplanation;
  language?: string;
}

export const VideoExplainer: React.FC<VideoExplainerProps> = ({ explanation, language = "en" }) => {
  const strings = getExplainStrings(language);
  const scenes = explanation.storyboard || [];

  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState<CompositionProgress | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [hasAudio, setHasAudio] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedSceneIndex, setSelectedSceneIndex] = useState(0);

  // Live interactive preview player state
  const [isPlayingLive, setIsPlayingLive] = useState(false);
  const liveCanvasRef = useRef<HTMLCanvasElement>(null);
  const liveAnimRef = useRef<number | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Draw current scene on live preview canvas
  useEffect(() => {
    const canvas = liveCanvasRef.current;
    if (!canvas || scenes.length === 0) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    renderSceneFrame(
      ctx,
      1280,
      720,
      scenes[selectedSceneIndex],
      explanation,
      selectedSceneIndex,
      scenes.length,
      1.0,
      (selectedSceneIndex + 1) / scenes.length,
    );
  }, [selectedSceneIndex, scenes, explanation]);

  // Clean up object URLs on unmount
  useEffect(() => {
    return () => {
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (liveAnimRef.current) {
        cancelAnimationFrame(liveAnimRef.current);
      }
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [videoUrl]);

  // Live scene autoplay with browser speech
  useEffect(() => {
    if (!isPlayingLive || scenes.length === 0) return;

    const currentScene = scenes[selectedSceneIndex];
    if (!currentScene) return;

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(
        currentScene.narration || currentScene.caption || "",
      );
      const langCode = language === "hi" ? "hi-IN" : language === "gu" ? "gu-IN" : "en-IN";
      utterance.lang = langCode;
      utterance.rate = 1.0;

      utterance.onend = () => {
        if (selectedSceneIndex < scenes.length - 1) {
          setSelectedSceneIndex((prev) => prev + 1);
        } else {
          setIsPlayingLive(false);
        }
      };

      utterance.onerror = () => {
        // Fallback delay
        const timer = setTimeout(() => {
          if (selectedSceneIndex < scenes.length - 1) {
            setSelectedSceneIndex((prev) => prev + 1);
          } else {
            setIsPlayingLive(false);
          }
        }, 3500);
        return () => clearTimeout(timer);
      };

      window.speechSynthesis.speak(utterance);
    } else {
      const timer = setTimeout(() => {
        if (selectedSceneIndex < scenes.length - 1) {
          setSelectedSceneIndex((prev) => prev + 1);
        } else {
          setIsPlayingLive(false);
        }
      }, 4000);
      return () => clearTimeout(timer);
    }

    return () => {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [isPlayingLive, selectedSceneIndex, scenes, language]);

  const handleGenerateVideo = async () => {
    if (scenes.length === 0) return;

    if (videoUrl) {
      URL.revokeObjectURL(videoUrl);
      setVideoUrl(null);
    }

    setIsGenerating(true);
    setErrorMessage(null);
    setIsPlayingLive(false);
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();

    setProgress({
      stage: "audio",
      sceneIndex: 0,
      totalScenes: scenes.length,
      percent: 5,
      message: "Preparing audio and scenes...",
    });

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const audioCtx = new (
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      )();

      const scenesWithAudio = await prepareSceneAudio(
        explanation.request_id || "req_" + Date.now(),
        scenes,
        language,
        audioCtx,
        (p) => setProgress(p),
        controller.signal,
      );

      const result = await composeStoryboardVideo(
        explanation,
        scenesWithAudio,
        (p) => setProgress(p),
        controller.signal,
      );

      setVideoUrl(result.objectUrl);
      setHasAudio(result.hasAudio);
      setIsGenerating(false);
      setProgress(null);
    } catch (err: unknown) {
      if ((err as Error)?.message?.includes("cancelled")) {
        setErrorMessage("Generation was cancelled.");
      } else {
        setErrorMessage(
          err instanceof Error ? err.message : "Failed to compose video. Please try again.",
        );
      }
      setIsGenerating(false);
      setProgress(null);
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsGenerating(false);
    setProgress(null);
  };

  const handleToggleLivePlay = () => {
    if (isPlayingLive) {
      setIsPlayingLive(false);
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    } else {
      setIsPlayingLive(true);
    }
  };

  if (scenes.length === 0) {
    return (
      <div className="p-8 text-center rounded-2xl border bg-card/50">
        <p className="text-muted-foreground">
          {strings.noDiagramsAvailable || "No storyboard scenes available."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Video Generation / Player Card */}
      <div className="rounded-2xl border bg-card/70 backdrop-blur-md p-6 shadow-sm">
        <div className="flex items-center justify-between gap-4 mb-4 flex-wrap">
          <div>
            <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              <span>{strings.tabVideo || "Video Explainer"}</span>
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              {scenes.length} Scenes • 1280×720 Browser Rendered • Zero Server Storage
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {!isGenerating && !videoUrl && (
              <button
                onClick={handleGenerateVideo}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold text-sm shadow-md hover:bg-primary/90 transition-all active:scale-98 cursor-pointer"
              >
                <Film className="w-4 h-4" />
                <span>{strings.composeVideoBtn || "Generate Video (.webm)"}</span>
              </button>
            )}

            {isGenerating && (
              <button
                onClick={handleCancel}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-destructive/10 text-destructive hover:bg-destructive/20 text-xs font-semibold transition-all cursor-pointer"
              >
                <XCircle className="w-4 h-4" />
                <span>{strings.cancelComposeBtn || "Cancel"}</span>
              </button>
            )}

            {videoUrl && !isGenerating && (
              <div className="flex items-center gap-2">
                <a
                  href={videoUrl}
                  download={`ruko-explanation-${explanation.request_id || "doc"}.webm`}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 text-xs font-semibold shadow-sm transition-all"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>{strings.downloadVideoBtn || "Download Video (.webm)"}</span>
                </a>
                <button
                  onClick={handleGenerateVideo}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs font-medium border transition-all cursor-pointer"
                  title="Re-generate video file"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Progress Bar Display */}
        {isGenerating && progress && (
          <div className="p-6 rounded-xl bg-secondary/30 border border-primary/20 space-y-3 my-4">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-foreground flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                {progress.message}
              </span>
              <span className="font-mono text-muted-foreground font-bold">{progress.percent}%</span>
            </div>

            <div className="w-full bg-secondary/80 rounded-full h-2.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-primary to-indigo-500 h-2.5 rounded-full transition-all duration-300"
                style={{ width: `${progress.percent}%` }}
              />
            </div>

            <p className="text-[11px] text-muted-foreground text-center">
              Rendering 1280×720 visual frames directly in browser memory...
            </p>
          </div>
        )}

        {/* Error Display */}
        {errorMessage && (
          <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-sm flex items-center gap-3 my-4">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Display: Downloaded / Encoded Video File Player */}
        {videoUrl ? (
          <div className="space-y-3">
            <div className="relative aspect-video rounded-xl overflow-hidden bg-black shadow-lg border">
              <video src={videoUrl} controls autoPlay className="w-full h-full object-contain" />
            </div>

            {!hasAudio && (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-800 dark:text-amber-300 flex items-center gap-2">
                <VolumeX className="w-4 h-4 shrink-0" />
                <span>Voice unavailable — captions-only video.</span>
              </div>
            )}
          </div>
        ) : (
          /* Live Interactive Canvas Scene Player */
          <div className="space-y-3">
            <div className="relative aspect-video rounded-xl overflow-hidden bg-black shadow-lg border flex items-center justify-center">
              <canvas
                ref={liveCanvasRef}
                width={1280}
                height={720}
                className="w-full h-full object-contain"
              />
            </div>

            {/* Interactive Player Controls */}
            <div className="flex items-center justify-between gap-3 p-3 rounded-xl bg-secondary/40 border">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedSceneIndex((prev) => Math.max(0, prev - 1))}
                  disabled={selectedSceneIndex === 0}
                  className="p-2 rounded-lg bg-background hover:bg-accent border disabled:opacity-40 transition-all cursor-pointer"
                  title="Previous Scene"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>

                <button
                  onClick={handleToggleLivePlay}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-bold transition-all active:scale-98 cursor-pointer"
                >
                  {isPlayingLive ? (
                    <>
                      <Pause className="w-4 h-4 fill-current" />
                      <span>Pause</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-current" />
                      <span>{strings.playLiveAudioBtn || "Play Live Voice & Scenes"}</span>
                    </>
                  )}
                </button>

                <button
                  onClick={() =>
                    setSelectedSceneIndex((prev) => Math.min(scenes.length - 1, prev + 1))
                  }
                  disabled={selectedSceneIndex === scenes.length - 1}
                  className="p-2 rounded-lg bg-background hover:bg-accent border disabled:opacity-40 transition-all cursor-pointer"
                  title="Next Scene"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              <div className="text-xs font-mono text-muted-foreground font-semibold">
                Scene {selectedSceneIndex + 1} of {scenes.length}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Storyboard Scenes Grid */}
      <div className="rounded-2xl border bg-card/50 p-6 space-y-4">
        <h4 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
          Storyboard Scenes ({scenes.length})
        </h4>

        <div className="grid gap-3 sm:grid-cols-2">
          {scenes.map((scene, idx) => (
            <div
              key={scene.scene_id || idx}
              onClick={() => setSelectedSceneIndex(idx)}
              className={`p-4 rounded-xl border text-left cursor-pointer transition-all ${
                selectedSceneIndex === idx
                  ? "bg-primary/10 border-primary/50 shadow-sm"
                  : "bg-background/60 hover:bg-accent/40 border-border/60"
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-primary/20 text-primary">
                  Scene {idx + 1}
                </span>
                <span className="text-[11px] font-mono text-muted-foreground uppercase">
                  {scene.visual?.type || "title"}
                </span>
              </div>
              <p className="text-xs text-foreground font-medium line-clamp-2">
                {scene.narration || scene.caption}
              </p>
              {scene.caption && (
                <p className="text-[11px] text-muted-foreground mt-1 line-clamp-1 italic">
                  "{scene.caption}"
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
