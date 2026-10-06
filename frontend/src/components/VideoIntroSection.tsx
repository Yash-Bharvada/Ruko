import { useEffect, useRef, useState } from "react";
import { ChevronDown, Moon, Sun } from "lucide-react";
import { useTheme } from "../lib/theme";
import { ThemeSyncedVideo } from "./ThemeSyncedVideo";

interface VideoIntroSectionProps {
  onScrollDown?: () => void;
  totalFrames?: number;
  fps?: number;
}

export function VideoIntroSection({ onScrollDown }: VideoIntroSectionProps) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  const sectionRef = useRef<HTMLElement | null>(null);
  const [scrollY, setScrollY] = useState(0);

  // Parallax / smooth scale effect based on scroll position
  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const smoothScrollToLanding = () => {
    if (onScrollDown) {
      onScrollDown();
      return;
    }
    const landingEl = document.getElementById("landing-content");
    if (landingEl) {
      landingEl.scrollIntoView({ behavior: "smooth" });
    } else {
      window.scrollTo({ top: window.innerHeight, behavior: "smooth" });
    }
  };

  // Wheel intercept for ultra-smooth first scroll down
  useEffect(() => {
    let isNavigating = false;

    const handleWheel = (e: WheelEvent) => {
      if (window.scrollY < 20 && e.deltaY > 25 && !isNavigating) {
        isNavigating = true;
        smoothScrollToLanding();
        setTimeout(() => {
          isNavigating = false;
        }, 1000);
      }
    };

    window.addEventListener("wheel", handleWheel, { passive: true });
    return () => window.removeEventListener("wheel", handleWheel);
  }, []);

  // Compute smooth parallax opacity & scale
  const progress = Math.min(
    1,
    Math.max(0, scrollY / (typeof window !== "undefined" ? window.innerHeight : 800)),
  );
  const scale = 1 - progress * 0.08;
  const opacity = 1 - progress * 0.95;

  return (
    <section
      ref={sectionRef}
      className={`relative h-screen w-screen max-w-full overflow-hidden flex items-center justify-center select-none transition-colors duration-500 ${
        isDark ? "bg-[#0b0f17]" : "bg-[#ebeef2]"
      }`}
    >
      {/* Top right minimal theme switcher */}
      <div className="absolute top-6 right-6 z-30">
        <button
          onClick={toggleTheme}
          aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
          title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
          className={`flex items-center gap-2 rounded-full border px-4 py-2 font-mono text-xs backdrop-blur-md transition-all duration-300 active:scale-95 ${
            isDark
              ? "border-cyan-500/40 bg-slate-950/80 text-cyan-300 hover:border-cyan-400 hover:bg-slate-900 shadow-xl shadow-cyan-950/50"
              : "border-slate-300/90 bg-white/90 text-slate-800 hover:border-slate-400 hover:bg-white shadow-lg shadow-slate-300/40"
          }`}
        >
          {isDark ? (
            <>
              <Sun className="h-3.5 w-3.5 text-amber-400 animate-spin-slow" />
              <span className="font-semibold">LIGHT MODE</span>
            </>
          ) : (
            <>
              <Moon className="h-3.5 w-3.5 text-indigo-600" />
              <span className="font-semibold">DARK MODE</span>
            </>
          )}
        </button>
      </div>

      {/* Main Full-Bleed Video Container with Smooth Parallax */}
      <div
        className="absolute inset-0 w-full h-full flex items-center justify-center transition-transform duration-100 ease-out"
        style={{
          transform: `scale(${scale})`,
          opacity: opacity,
        }}
      >
        <ThemeSyncedVideo
          lightSrc="/videos/light.mp4"
          darkSrc="/videos/dark.mp4"
          crossfadeDurationMs={450}
          className="w-full h-full object-cover"
          containerClassName="relative w-full h-full"
        />

        {/* Soft edge gradient to blend smoothly at the bottom */}
        <div
          className={`pointer-events-none absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t transition-opacity duration-500 ${
            isDark
              ? "from-[#0b0f17] to-transparent opacity-80"
              : "from-[#ebeef2] to-transparent opacity-80"
          }`}
        />
      </div>

      {/* Subtle Scroll Cue at the bottom */}
      <button
        onClick={smoothScrollToLanding}
        aria-label="Scroll to explore website"
        className="group absolute bottom-8 z-20 flex flex-col items-center gap-2 cursor-pointer outline-none transition-all duration-300 hover:translate-y-1"
        style={{ opacity: Math.max(0, 1 - progress * 2) }}
      >
        <span
          className={`font-mono text-[11px] font-semibold tracking-widest uppercase transition-colors ${
            isDark
              ? "text-slate-400 group-hover:text-cyan-400"
              : "text-slate-600 group-hover:text-slate-950"
          }`}
        >
          SCROLL TO EXPLORE
        </span>
        <div
          className={`flex h-9 w-9 items-center justify-center rounded-full border backdrop-blur-md transition-all duration-300 ${
            isDark
              ? "border-cyan-500/30 bg-slate-900/80 text-cyan-400 shadow-lg shadow-cyan-950/50 group-hover:border-cyan-400 group-hover:bg-cyan-500 group-hover:text-slate-950"
              : "border-slate-300 bg-white/90 text-slate-800 shadow-md group-hover:border-slate-400 group-hover:bg-slate-900 group-hover:text-white"
          }`}
        >
          <ChevronDown className="h-4 w-4 animate-bounce" />
        </div>
      </button>
    </section>
  );
}
