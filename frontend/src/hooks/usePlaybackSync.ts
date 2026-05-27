import { useEffect, useState } from "react";

import type { LineOut } from "../api/types";

interface Args {
  lines: LineOut[];
  offsetMs: number;
  getCurrentTimeMs: () => number;
}

/**
 * rAF loop reading current playback time and returning the index of the
 * active lyric line. ``offsetMs`` shifts the playback clock — positive
 * means "lyrics arrive earlier."
 */
export function usePlaybackSync({ lines, offsetMs, getCurrentTimeMs }: Args): number {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (lines.length === 0) return;
    let raf = 0;
    const tick = () => {
      const t = getCurrentTimeMs() + offsetMs;
      // Binary search for the last line whose start <= t.
      let lo = 0;
      let hi = lines.length - 1;
      let found = 0;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        if (lines[mid].start_ms <= t) {
          found = mid;
          lo = mid + 1;
        } else {
          hi = mid - 1;
        }
      }
      setActiveIndex((prev) => (prev === found ? prev : found));
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [lines, offsetMs, getCurrentTimeMs]);

  return activeIndex;
}
