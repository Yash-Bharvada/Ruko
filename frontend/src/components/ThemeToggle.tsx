import type { FC } from "react";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "../lib/theme";

export const ThemeToggle: FC<{ className?: string }> = ({ className = "" }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      className={`relative inline-flex items-center justify-center h-9 w-9 rounded-md border border-border bg-card/60 backdrop-blur text-foreground transition-all hover:border-accent hover:text-accent active:scale-95 focus:outline-none ${className}`}
      title={`Toggle ${theme === "dark" ? "light" : "dark"} mode`}
    >
      {theme === "dark" ? (
        <Sun className="h-4 w-4 text-cyan-400 transition-transform duration-300 hover:rotate-90" />
      ) : (
        <Moon className="h-4 w-4 text-slate-700 transition-transform duration-300 hover:-rotate-12" />
      )}
    </button>
  );
};

export default ThemeToggle;
