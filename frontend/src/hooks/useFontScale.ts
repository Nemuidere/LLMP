import { useCallback, useEffect, useState } from "react";

const KEY = "llmp.lyricFontScale";
const MIN = 0.8;
const MAX = 1.6;
const STEP = 0.1;

export function useFontScale() {
  const [scale, setScale] = useState<number>(() => {
    const raw = typeof window !== "undefined" ? localStorage.getItem(KEY) : null;
    const n = raw ? Number(raw) : 1;
    return Number.isFinite(n) ? Math.min(MAX, Math.max(MIN, n)) : 1;
  });

  useEffect(() => {
    localStorage.setItem(KEY, String(scale));
  }, [scale]);

  const bump = useCallback(
    (delta: number) =>
      setScale((s) => Math.min(MAX, Math.max(MIN, Math.round((s + delta) * 10) / 10))),
    [],
  );

  return {
    scale,
    increase: () => bump(STEP),
    decrease: () => bump(-STEP),
    reset: () => setScale(1),
    min: MIN,
    max: MAX,
  };
}
