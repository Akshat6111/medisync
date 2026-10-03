import { useEffect, useState } from "react";

const KEY = "medisync_theme";

export function useTheme() {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const saved = (typeof window !== "undefined" ? window.localStorage.getItem(KEY) : null) as
      | "light"
      | "dark"
      | null;
    const initial = saved ?? "light";
    setTheme(initial);
    document.documentElement.classList.toggle("dark", initial === "dark");
  }, []);

  const toggle = () => {
    setTheme((t) => {
      const next = t === "light" ? "dark" : "light";
      document.documentElement.classList.toggle("dark", next === "dark");
      if (typeof window !== "undefined") window.localStorage.setItem(KEY, next);
      return next;
    });
  };

  return { theme, toggle };
}
