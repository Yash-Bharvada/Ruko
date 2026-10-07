import type { FC } from "react";

interface RukoLogoProps {
  size?: number;
  showText?: boolean;
  showBadge?: boolean;
  className?: string;
  glow?: boolean;
}

export const RukoLogo: FC<RukoLogoProps> = ({
  size = 32,
  showText = true,
  showBadge = true,
  className = "",
  glow = true,
}) => {
  return (
    <div className={`inline-flex items-center gap-3 select-none ${className}`}>
      <div className="relative flex items-center justify-center group">
        {/* Ambient neon backdrop glow */}
        {glow && (
          <div
            className="absolute inset-0 rounded-full blur-md opacity-70 group-hover:opacity-100 transition-opacity duration-500"
            style={{
              background:
                "radial-gradient(circle, rgba(0,229,255,0.6) 0%, rgba(0,140,255,0.15) 70%, transparent 100%)",
              transform: "scale(1.2)",
            }}
          />
        )}

        {/* Real Rupee Badge Image */}
        <div
          className="relative rounded-full overflow-hidden border border-cyan-400/40 shadow-lg shadow-cyan-500/20 transition-transform duration-300 group-hover:scale-105"
          style={{ width: `${size}px`, height: `${size}px` }}
        >
          <img
            src="/ruko-logo.png"
            alt="Ruko Shield Emblem"
            className="w-full h-full object-cover"
          />
        </div>
      </div>

      {showText && (
        <div className="flex items-center gap-1.5 leading-none">
          <span className="text-xl md:text-2xl font-bold tracking-tight text-foreground font-mono">
            RUKO
          </span>
          {showBadge && (
            <span className="label-mono text-[9px] px-1.5 py-0.5 rounded border border-cyan-500/40 bg-cyan-500/10 text-cyan-400 font-semibold tracking-wider">
              AI
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default RukoLogo;
