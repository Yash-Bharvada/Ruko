import { useEffect, useRef, useState, useCallback } from "react";
import { Play, Pause, RotateCcw, Sparkles, ShieldCheck, Zap } from "lucide-react";
import { frameCache } from "../lib/frameCache";

interface VideoFramePlayerProps {
  totalFrames?: number;
  fps?: number;
  framePathPrefix?: string;
  className?: string;
  autoPlay?: boolean;
}

export function VideoFramePlayer({
  totalFrames = 240,
  fps = 24,
  framePathPrefix = "/frames/frame_",
  className = "",
  autoPlay = true,
}: VideoFramePlayerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [currentFrame, setCurrentFrame] = useState(1);
  const [loadedCount, setLoadedCount] = useState(() => frameCache.loadedCount || 0);
  const [isReady, setIsReady] = useState(() => frameCache.isReady || frameCache.loadedCount >= 15);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [isHovered, setIsHovered] = useState(false);

  // Store preloaded image instances
  const imagesRef = useRef<HTMLImageElement[]>(
    frameCache.images.length > 0 ? frameCache.images : [],
  );
  const currentFrameRef = useRef(1);
  const isPlayingRef = useRef(autoPlay);
  const animFrameIdRef = useRef<number | null>(null);
  const lastFrameTimeRef = useRef<number>(0);
  const speedRef = useRef(1);

  isPlayingRef.current = isPlaying;
  speedRef.current = playbackSpeed;

  // Format frame number to 4 digits: frame_0001.jpg
  const getFrameUrl = useCallback(
    (index: number) => {
      const padded = String(index).padStart(4, "0");
      return `${framePathPrefix}${padded}.jpg`;
    },
    [framePathPrefix],
  );

  // Preload frames if not already populated by SiteLoader
  useEffect(() => {
    if (frameCache.images && frameCache.images.length >= totalFrames) {
      imagesRef.current = frameCache.images;
      setLoadedCount(frameCache.images.length);
      setIsReady(true);
      return;
    }

    let isMounted = true;
    const images: HTMLImageElement[] = [];
    let loaded = 0;

    for (let i = 1; i <= totalFrames; i++) {
      const img = new Image();
      img.src = getFrameUrl(i);
      img.onload = () => {
        if (!isMounted) return;
        loaded++;
        setLoadedCount(loaded);
        if (loaded === 15 || loaded === totalFrames) {
          setIsReady(true);
        }
      };
      images.push(img);
    }

    imagesRef.current = images;
    frameCache.images = images;

    return () => {
      isMounted = false;
    };
  }, [totalFrames, getFrameUrl]);

  // Draw specific frame onto canvas
  const drawFrame = useCallback((frameIdx: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = imagesRef.current[frameIdx - 1];
    if (img && img.complete && img.naturalWidth > 0) {
      if (canvas.width !== img.naturalWidth || canvas.height !== img.naturalHeight) {
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    }
  }, []);

  // Continuous animation loop using requestAnimationFrame
  useEffect(() => {
    const frameInterval = 1000 / (fps * speedRef.current);

    const loop = (timestamp: number) => {
      if (!lastFrameTimeRef.current) lastFrameTimeRef.current = timestamp;
      const elapsed = timestamp - lastFrameTimeRef.current;
      const targetInterval = 1000 / (fps * speedRef.current);

      if (isPlayingRef.current && elapsed >= targetInterval) {
        lastFrameTimeRef.current = timestamp - (elapsed % targetInterval);
        let nextFrame = currentFrameRef.current + 1;
        if (nextFrame > totalFrames) {
          nextFrame = 1; // Continuous seamless looping
        }
        currentFrameRef.current = nextFrame;
        setCurrentFrame(nextFrame);
        drawFrame(nextFrame);
      }

      animFrameIdRef.current = requestAnimationFrame(loop);
    };

    animFrameIdRef.current = requestAnimationFrame(loop);

    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, [fps, totalFrames, drawFrame]);

  // Render first frame when available
  useEffect(() => {
    if (isReady && currentFrame === 1) {
      drawFrame(1);
    }
  }, [isReady, drawFrame, currentFrame]);

  const handleTogglePlay = () => {
    setIsPlaying((prev) => !prev);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const frame = parseInt(e.target.value, 10);
    currentFrameRef.current = frame;
    setCurrentFrame(frame);
    drawFrame(frame);
  };

  const progressPercent = ((currentFrame / totalFrames) * 100).toFixed(1);
  const loadPercent = Math.min(100, Math.round((loadedCount / totalFrames) * 100));

  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border border-cyan-500/30 bg-slate-950/80 shadow-2xl shadow-cyan-950/40 backdrop-blur-xl transition-all duration-300 hover:border-cyan-400/60 ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Background glow effects */}
      <div className="pointer-events-none absolute -left-20 -top-20 h-64 w-64 rounded-full bg-cyan-500/15 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 -right-20 h-64 w-64 rounded-full bg-indigo-500/15 blur-3xl" />

      {/* Top Cybernetic Status Header */}
      <div className="flex items-center justify-between border-b border-border/60 bg-slate-900/60 px-4 py-2.5 text-xs">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          <span className="font-mono text-[11px] font-semibold tracking-wider text-cyan-400 uppercase">
            RUKO AI LIVE ENGINE
          </span>
          <span className="rounded bg-cyan-500/10 px-1.5 py-0.5 font-mono text-[10px] text-cyan-300">
            24 FPS CONTINUOUS
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="hidden sm:inline-flex items-center gap-1 font-mono text-[11px] text-slate-400">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
            FRAME {String(currentFrame).padStart(3, "0")}/{totalFrames}
          </span>
          {loadPercent < 100 && (
            <span className="font-mono text-[10px] text-amber-400">BUFFERING {loadPercent}%</span>
          )}
        </div>
      </div>

      {/* Main Canvas Viewport */}
      <div className="relative aspect-[16/9] w-full overflow-hidden bg-slate-950 flex items-center justify-center">
        {/* Loading placeholder before first frame loads */}
        {!isReady && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-slate-950 text-cyan-400">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
            <p className="font-mono text-xs tracking-wider text-cyan-300/80">
              PRELOADING HIGH-RES FRAMES ({loadPercent}%)...
            </p>
          </div>
        )}

        <canvas
          ref={canvasRef}
          className="h-full w-full object-contain transition-opacity duration-300"
          style={{ opacity: isReady ? 1 : 0 }}
        />

        {/* Scan line overlay effect */}
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%)] bg-[length:100%_4px] opacity-20" />

        {/* Floating Quick Action Overlay */}
        <div className="pointer-events-none absolute bottom-4 left-4 right-4 flex items-center justify-between">
          <div className="pointer-events-auto rounded-lg border border-white/10 bg-black/60 px-3 py-1.5 backdrop-blur-md">
            <p className="flex items-center gap-1.5 font-mono text-[11px] text-slate-200">
              <Zap className="h-3 w-3 text-cyan-400" />
              <span>Real-Time Multi-Modal Scam Interceptor</span>
            </p>
          </div>

          <div className="pointer-events-auto flex items-center gap-1.5">
            <button
              onClick={() => {
                const nextSpeed =
                  playbackSpeed === 1
                    ? 1.5
                    : playbackSpeed === 1.5
                      ? 2
                      : playbackSpeed === 2
                        ? 0.5
                        : 1;
                setPlaybackSpeed(nextSpeed);
              }}
              title="Playback speed"
              className="rounded-md border border-white/15 bg-black/70 px-2 py-1 font-mono text-[10px] text-cyan-300 hover:bg-black/90 hover:text-white transition-colors"
            >
              {playbackSpeed}x
            </button>
            <button
              onClick={handleTogglePlay}
              aria-label={isPlaying ? "Pause frame animation" : "Play frame animation"}
              className="flex h-7 w-7 items-center justify-center rounded-md border border-white/15 bg-black/70 text-white hover:bg-cyan-500 hover:text-black transition-colors"
            >
              {isPlaying ? (
                <Pause className="h-3.5 w-3.5" />
              ) : (
                <Play className="h-3.5 w-3.5 fill-current" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Scrub & Control bar */}
      <div className="border-t border-border/60 bg-slate-900/80 px-4 py-2.5 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <button
            onClick={handleTogglePlay}
            className="text-slate-300 hover:text-cyan-400 transition-colors"
            aria-label={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 fill-current" />}
          </button>

          {/* Interactive Frame Scrubber */}
          <div className="relative flex-1 flex items-center">
            <input
              type="range"
              min={1}
              max={totalFrames}
              value={currentFrame}
              onChange={handleSeek}
              aria-label="Frame scrubber"
              className="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-800 accent-cyan-400 outline-none transition-all hover:h-2"
            />
          </div>

          <button
            onClick={() => {
              currentFrameRef.current = 1;
              setCurrentFrame(1);
              drawFrame(1);
            }}
            title="Reset to frame 1"
            className="text-slate-400 hover:text-cyan-400 transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>

          <div className="font-mono text-[11px] text-slate-400 min-w-[3.5rem] text-right">
            {progressPercent}%
          </div>
        </div>
      </div>
    </div>
  );
}
