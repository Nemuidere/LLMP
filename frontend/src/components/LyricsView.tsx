import { useEffect, useMemo, useRef } from "react";

import type { LineOut } from "../api/types";
import LyricLine from "./LyricLine";

interface Props {
  lines: LineOut[];
  activeIndex: number;
  fontScale: number;
  showRomaji: boolean;
}

// Per-line slot height (in rem) at 1× font. The slot scales with the
// font so the three visible lines don't overlap when the user enlarges
// text.
const SLOT_BASE_REM = 7;
const WINDOW = 4; // how many lines above/below the active one we keep mounted

export default function LyricsView({ lines, activeIndex, fontScale, showRomaji }: Props) {
  const slot = SLOT_BASE_REM * fontScale;
  const containerHeight = slot * 3;

  // Snap instantly when the user seeks the video by a large amount —
  // the 500ms slide is meant for natural line-to-line advances, not
  // 20-line jumps which look like a delayed crawl.
  const prevActiveRef = useRef(activeIndex);
  const isJump = Math.abs(activeIndex - prevActiveRef.current) > 2;
  useEffect(() => {
    prevActiveRef.current = activeIndex;
  }, [activeIndex]);

  const visible = useMemo(() => {
    const start = Math.max(0, activeIndex - WINDOW);
    const end = Math.min(lines.length, activeIndex + WINDOW + 1);
    const out: { line: LineOut; index: number }[] = [];
    for (let i = start; i < end; i++) out.push({ line: lines[i], index: i });
    return out;
  }, [lines, activeIndex]);

  return (
    <div
      className="relative overflow-hidden rounded-2xl border border-ink-800/60 bg-ink-900/40"
      style={{ height: `${containerHeight}rem` }}
    >
      <div
        className="pointer-events-none absolute inset-x-0 top-0 z-10 bg-gradient-to-b from-ink-900/90 to-transparent"
        style={{ height: `${slot * 0.9}rem` }}
      />
      <div
        className="pointer-events-none absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-ink-900/90 to-transparent"
        style={{ height: `${slot * 0.9}rem` }}
      />

      <div
        className={`absolute inset-x-0 top-0 ${
          isJump ? "" : "transition-transform duration-500 ease-out-soft"
        }`}
        style={{
          // Place the active line at the vertical centre of the box:
          // the active child sits at y=activeIndex*slot in inner coords,
          // and we want its centre at container y=1.5*slot.
          // → translateY = (1 - activeIndex) * slot.
          transform: `translateY(${(1 - activeIndex) * slot}rem)`,
        }}
      >
        {visible.map(({ line, index }) => (
          <div
            key={line.line_index}
            className="absolute inset-x-0 flex items-center justify-center"
            style={{
              top: `${index * slot}rem`,
              height: `${slot}rem`,
            }}
          >
            <LyricLine
              line={line}
              isActive={index === activeIndex}
              distance={index - activeIndex}
              fontScale={fontScale}
              showRomaji={showRomaji}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
