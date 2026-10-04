import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "dark" | "light";

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (t: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: "dark",
  toggleTheme: () => {},
  setTheme: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem("ruko-theme") as Theme | null;
        if (saved === "light" || saved === "dark") return saved;
      } catch (_) {}
    }
    return "dark";
  });

  const applyTheme = (t: Theme) => {
    if (typeof document === "undefined") return;
    const root = document.documentElement;
    const body = document.body;
    if (t === "dark") {
      root.classList.add("dark");
      root.classList.remove("light");
      root.setAttribute("data-theme", "dark");
      if (body) {
        body.classList.add("dark");
        body.classList.remove("light");
      }
    } else {
      root.classList.remove("dark");
      root.classList.add("light");
      root.setAttribute("data-theme", "light");
      if (body) {
        body.classList.remove("dark");
        body.classList.add("light");
      }
    }
  };

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const setTheme = (t: Theme) => {
    setThemeState(t);
    try {
      localStorage.setItem("ruko-theme", t);
    } catch (_) {}
    applyTheme(t);
  };

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
