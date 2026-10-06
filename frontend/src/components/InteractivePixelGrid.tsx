import { useState, useRef, useEffect } from "react";
import { useTheme } from "../lib/theme";

interface InteractivePixelGridProps {
  className?: string;
}

export function InteractivePixelGrid({ className = "" }: InteractivePixelGridProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const containerRef = useRef<HTMLDivElement | null>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  // Active pattern cell indices (the "cheques" / robot pixel art pattern)
  const activeCells = new Set([12, 13, 20, 21, 22, 27, 28, 29, 30, 35, 36, 37, 44, 45, 52]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  const handleMouseLeave = () => {
    setMousePos(null);
    setHoveredIndex(null);
  };

  // 8x8 = 64 cells
  const cellSize = 48; // px
  const cols = 8;

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`relative grid grid-cols-8 gap-1 p-2 select-none cursor-crosshair rounded-xl transition-all duration-300 ${className}`}
      style={{ width: "fit-content" }}
    >
      {/* Interactive Cursor Spotlight Glow */}
      {mousePos && (
        <div
          className="pointer-events-none absolute -inset-2 rounded-2xl transition-opacity duration-200"
          style={{
            background: isDark
              ? `radial-gradient(160px circle at ${mousePos.x}px ${mousePos.y}px, rgba(6, 182, 212, 0.18), transparent 70%)`
              : `radial-gradient(160px circle at ${mousePos.x}px ${mousePos.y}px, rgba(14, 165, 233, 0.14), transparent 70%)`,
          }}
        />
      )}

      {Array.from({ length: 64 }).map((_, i) => {
        const isActive = activeCells.has(i);
        const col = i % cols;
        const row = Math.floor(i / cols);

        // Center coordinates of this cell
        const cellCenterX = col * (cellSize + 4) + cellSize / 2;
        const cellCenterY = row * (cellSize + 4) + cellSize / 2;

        let proximityGlow = 0;
        if (mousePos) {
          const dx = mousePos.x - cellCenterX;
          const dy = mousePos.y - cellCenterY;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            proximityGlow = Math.max(0, 1 - dist / 120);
          }
        }

        const isDirectHover = hoveredIndex === i;

        return (
          <div
            key={i}
            onMouseEnter={() => setHoveredIndex(i)}
            className="relative h-11 w-11 rounded-[6px] transition-all duration-200 ease-out"
            style={{
              // Active cells base background
              backgroundColor: isActive
                ? isDark
                  ? isDirectHover
                    ? "rgba(6, 182, 212, 0.95)"
                    : proximityGlow > 0
                      ? `rgba(6, 182, 212, ${0.55 + proximityGlow * 0.35})`
                      : "rgba(6, 182, 212, 0.55)"
                  : isDirectHover
                    ? "rgba(2, 132, 199, 0.95)"
                    : proximityGlow > 0
                      ? `rgba(2, 132, 199, ${0.5 + proximityGlow * 0.35})`
                      : "rgba(2, 132, 199, 0.5)"
                : isDirectHover
                  ? isDark
                    ? "rgba(6, 182, 212, 0.25)"
                    : "rgba(14, 165, 233, 0.2)"
                  : proximityGlow > 0
                    ? isDark
                      ? `rgba(6, 182, 212, ${proximityGlow * 0.12})`
                      : `rgba(14, 165, 233, ${proximityGlow * 0.08})`
                    : "transparent",

              // Subtle borders
              border: isActive
                ? isDark
                  ? `1px solid rgba(6, 182, 212, ${0.4 + proximityGlow * 0.4})`
                  : `1px solid rgba(2, 132, 199, ${0.4 + proximityGlow * 0.4})`
                : proximityGlow > 0 || isDirectHover
                  ? isDark
                    ? `1px solid rgba(6, 182, 212, ${proximityGlow * 0.25})`
                    : `1px solid rgba(14, 165, 233, ${proximityGlow * 0.2})`
                  : isDark
                    ? "1px solid rgba(255, 255, 255, 0.02)"
                    : "1px solid rgba(0, 0, 0, 0.03)",

              // Glow Box Shadow
              boxShadow: isDirectHover
                ? isDark
                  ? "0 0 16px rgba(6, 182, 212, 0.65), inset 0 0 8px rgba(255, 255, 255, 0.3)"
                  : "0 0 14px rgba(2, 132, 199, 0.5), inset 0 0 8px rgba(255, 255, 255, 0.4)"
                : isActive && proximityGlow > 0
                  ? isDark
                    ? `0 0 ${8 + proximityGlow * 12}px rgba(6, 182, 212, ${0.2 + proximityGlow * 0.35})`
                    : `0 0 ${6 + proximityGlow * 10}px rgba(2, 132, 199, ${0.15 + proximityGlow * 0.3})`
                  : "none",

              transform: isDirectHover
                ? "scale(1.08)"
                : proximityGlow > 0
                  ? `scale(${1 + proximityGlow * 0.04})`
                  : "scale(1)",
            }}
          />
        );
      })}
    </div>
  );
}
