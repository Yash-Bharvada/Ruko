import { useEffect, useState } from "react";
import { frameCache } from "../lib/frameCache";

interface SiteLoaderProps {
  totalFrames?: number;
  framePathPrefix?: string;
  onLoaded?: (images: HTMLImageElement[]) => void;
}

export function SiteLoader({
  totalFrames = 240,
  framePathPrefix = "/frames/frame_",
  onLoaded,
}: SiteLoaderProps) {
  const [loadedCount, setLoadedCount] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  const [isFadingOut, setIsFadingOut] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const images: HTMLImageElement[] = [];
    let count = 0;

    frameCache.totalFrames = totalFrames;
    frameCache.images = images;

    const handleSingleLoad = () => {
      if (!isMounted) return;
      count++;
      setLoadedCount(count);
      frameCache.loadedCount = count;

      if (count >= totalFrames) {
        frameCache.isReady = true;
        if (onLoaded) {
          onLoaded(images);
        }
        // Brief pause so user sees 100% completion before smooth fade
        setTimeout(() => {
          if (!isMounted) return;
          setIsFadingOut(true);
          setTimeout(() => {
            if (!isMounted) return;
            setIsCompleted(true);
          }, 600);
        }, 350);
      }
    };

    // Preload all frames
    for (let i = 1; i <= totalFrames; i++) {
      const img = new Image();
      const padded = String(i).padStart(4, "0");
      img.src = `${framePathPrefix}${padded}.jpg`;
      img.onload = handleSingleLoad;
      img.onerror = handleSingleLoad; // prevent getting permanently stuck if an image fails
      images.push(img);
    }

    // Safety fallback timeout: unveil after 2.5s to keep navigation snappy
    const fallbackTimer = setTimeout(() => {
      if (!isMounted) return;
      if (count < totalFrames) {
        if (onLoaded) onLoaded(images);
        setIsFadingOut(true);
        setTimeout(() => setIsCompleted(true), 500);
      }
    }, 2500);

    return () => {
      isMounted = false;
      clearTimeout(fallbackTimer);
    };
  }, [totalFrames, framePathPrefix, onLoaded]);

  if (isCompleted) {
    return null;
  }

  const progressPercent = Math.min(100, Math.round((loadedCount / totalFrames) * 100));

  return (
    <div
      className={`fixed inset-0 z-[9999] flex flex-col items-center justify-between bg-slate-950 px-6 py-12 text-slate-100 transition-opacity duration-500 selection:bg-cyan-500 selection:text-slate-950 ${
        isFadingOut ? "opacity-0 pointer-events-none" : "opacity-100"
      }`}
      aria-live="polite"
      aria-label="Loading site assets"
    >
      {/* Background cyber grid & ambiance glow */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(6,182,212,0.12)_0%,transparent_70%)]" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:48px_48px]" />

      {/* Top Cybernetic Status Indicator */}
      <div className="relative z-10 flex w-full max-w-5xl items-center justify-between border-b border-cyan-500/20 pb-4 label-mono text-xs text-muted-foreground">
        <div className="flex items-center gap-2 text-cyan-400">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-500" />
          </span>
          <span className="font-semibold tracking-wider uppercase font-mono text-[11px]">
            SYSTEM INITIALIZING
          </span>
        </div>
        <div className="font-mono text-[11px] text-cyan-400/80">[STAGE 01/01 · VISUAL ASSETS]</div>
      </div>

      {/* Center: Tetrominos Animation */}
      <div className="relative z-10 flex flex-1 flex-col items-center justify-center my-auto">
        <div className="tetrominos-container">
          <div className="tetrominos">
            <div className="tetromino box1" />
            <div className="tetromino box2" />
            <div className="tetromino box3" />
            <div className="tetromino box4" />
          </div>
        </div>
      </div>

      {/* Bottom Section: RUKO Branding & Frame Loading Progress Bar */}
      <div className="relative z-10 flex w-full max-w-md flex-col items-center gap-4 text-center">
        {/* RUKO Brand Heading in Website UI Style */}
        <div className="flex items-baseline justify-center gap-2">
          <h1 className="font-pixel text-5xl font-bold tracking-tight text-white md:text-6xl">
            RUKO<span className="blink text-cyan-400">_</span>
          </h1>
        </div>

        <p className="label-mono text-xs tracking-wider text-slate-400">STOP · CHECK · STAY SAFE</p>

        {/* Loading Progress Bar Container */}
        <div className="w-full space-y-2 mt-2">
          {/* Progress Track */}
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-900 border border-cyan-500/30 shadow-inner">
            <div
              className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-teal-400 to-cyan-300 transition-all duration-150 ease-out shadow-[0_0_12px_rgba(6,182,212,0.8)]"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {/* Frame Progress Metrics */}
          <div className="flex items-center justify-between label-mono text-[11px] text-muted-foreground px-1">
            <span className="text-cyan-400 font-mono">
              LOADING FRAMES: {loadedCount} / {totalFrames}
            </span>
            <span className="font-mono font-semibold text-slate-200">{progressPercent}%</span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[10px] label-mono text-slate-500 pt-2">
          <span>6,583+ SEBI ENTITIES</span>
          <span>·</span>
          <span>CALIBRATED ML 0.410</span>
          <span>·</span>
          <span>24 FPS LIVE ENGINE</span>
        </div>
      </div>
    </div>
  );
}
