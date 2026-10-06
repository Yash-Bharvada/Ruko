import { useEffect, useRef, useState, useCallback } from "react";
import { useTheme } from "../lib/theme";

export interface ThemeSyncedVideoProps {
  lightSrc?: string;
  darkSrc?: string;
  className?: string;
  containerClassName?: string;
  autoPlay?: boolean;
  loop?: boolean;
  crossfadeDurationMs?: number;
  onProgress?: (progress: number) => void;
}

export function ThemeSyncedVideo({
  lightSrc = "/videos/light.mp4",
  darkSrc = "/videos/dark.mp4",
  className = "w-full h-full object-cover",
  containerClassName = "relative w-full h-full flex items-center justify-center overflow-hidden",
  autoPlay = true,
  loop = true,
  crossfadeDurationMs = 450,
  onProgress,
}: ThemeSyncedVideoProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const lightVideoRef = useRef<HTMLVideoElement | null>(null);
  const darkVideoRef = useRef<HTMLVideoElement | null>(null);

  const [isLightReady, setIsLightReady] = useState(false);
  const [isDarkReady, setIsDarkReady] = useState(false);
  const isTransitioningRef = useRef(false);
  const activeThemeRef = useRef(theme);

  activeThemeRef.current = theme;

  // Synchronize both video elements to the exact normalized progress
  const syncVideos = useCallback((source: "light" | "dark", target: "light" | "dark") => {
    const sourceVideo = source === "light" ? lightVideoRef.current : darkVideoRef.current;
    const targetVideo = target === "light" ? lightVideoRef.current : darkVideoRef.current;

    if (!sourceVideo || !targetVideo) return;
    if (sourceVideo.duration && targetVideo.duration) {
      const progress = sourceVideo.currentTime / sourceVideo.duration;
      const targetTime = progress * targetVideo.duration;
      // Avoid micro-jitter if drift is negligible (<30ms)
      if (Math.abs(targetVideo.currentTime - targetTime) > 0.03) {
        targetVideo.currentTime = targetTime;
      }
    }
  }, []);

  // Initial playback setup
  useEffect(() => {
    const lightVid = lightVideoRef.current;
    const darkVid = darkVideoRef.current;

    if (!lightVid || !darkVid) return;

    const handleCanPlayLight = () => {
      setIsLightReady(true);
      if (autoPlay) {
        lightVid.play().catch(() => {});
      }
    };

    const handleCanPlayDark = () => {
      setIsDarkReady(true);
      if (autoPlay) {
        darkVid.play().catch(() => {});
      }
    };

    lightVid.addEventListener("canplay", handleCanPlayLight);
    darkVid.addEventListener("canplay", handleCanPlayDark);

    // If already loaded
    if (lightVid.readyState >= 3) setIsLightReady(true);
    if (darkVid.readyState >= 3) setIsDarkReady(true);

    if (autoPlay) {
      lightVid.play().catch(() => {});
      darkVid.play().catch(() => {});
    }

    return () => {
      lightVid.removeEventListener("canplay", handleCanPlayLight);
      darkVid.removeEventListener("canplay", handleCanPlayDark);
    };
  }, [autoPlay]);

  // Handle Theme Change with seamless Bidirectional Transition
  useEffect(() => {
    const activeVid = isDark ? darkVideoRef.current : lightVideoRef.current;
    const prevVid = isDark ? lightVideoRef.current : darkVideoRef.current;

    if (!activeVid || !prevVid) return;

    isTransitioningRef.current = true;

    // 1. Calculate active normalized timeline progress
    if (prevVid.duration && activeVid.duration) {
      const progress = prevVid.currentTime / prevVid.duration || 0;
      activeVid.currentTime = progress * activeVid.duration;
    }

    // 2. Ensure target video is playing
    activeVid.play().catch(() => {});
    prevVid.play().catch(() => {});

    // 3. Mark transition complete after crossfade duration
    const timer = setTimeout(() => {
      isTransitioningRef.current = false;
      // Resync once transition stabilizes
      if (isDark) {
        syncVideos("dark", "light");
      } else {
        syncVideos("light", "dark");
      }
    }, crossfadeDurationMs);

    return () => clearTimeout(timer);
  }, [theme, isDark, crossfadeDurationMs, syncVideos]);

  // Maintain periodic drift check between the two videos (e.g. every 2 seconds)
  useEffect(() => {
    const interval = setInterval(() => {
      if (isTransitioningRef.current) return;
      if (isDark) {
        syncVideos("dark", "light");
      } else {
        syncVideos("light", "dark");
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isDark, syncVideos]);

  // Track progress if listener requested
  const handleTimeUpdate = () => {
    if (!onProgress) return;
    const vid = isDark ? darkVideoRef.current : lightVideoRef.current;
    if (vid && vid.duration) {
      onProgress(vid.currentTime / vid.duration);
    }
  };

  return (
    <div className={containerClassName}>
      {/* Light Mode Video Layer */}
      <video
        ref={lightVideoRef}
        src={lightSrc}
        muted
        playsInline
        loop={loop}
        autoPlay={autoPlay}
        preload="auto"
        onTimeUpdate={!isDark ? handleTimeUpdate : undefined}
        className={`absolute inset-0 select-none pointer-events-none transition-opacity ease-in-out ${className}`}
        style={{
          opacity: isDark ? 0 : 1,
          transitionDuration: `${crossfadeDurationMs}ms`,
          zIndex: isDark ? 1 : 2,
        }}
      />

      {/* Dark Mode Video Layer */}
      <video
        ref={darkVideoRef}
        src={darkSrc}
        muted
        playsInline
        loop={loop}
        autoPlay={autoPlay}
        preload="auto"
        onTimeUpdate={isDark ? handleTimeUpdate : undefined}
        className={`absolute inset-0 select-none pointer-events-none transition-opacity ease-in-out ${className}`}
        style={{
          opacity: isDark ? 1 : 0,
          transitionDuration: `${crossfadeDurationMs}ms`,
          zIndex: isDark ? 2 : 1,
        }}
      />
    </div>
  );
}
