import { useEffect, useLayoutEffect, useRef, useState } from "react";

import type { LineOut } from "../api/types";
import LyricLine from "./LyricLine";

interface Props {
  lines: LineOut[];
  activeIndex: number;
  fontScale: number;
  showRomaji: boolean;
}

// Nominal viewport height, expressed as N lines' worth of space at 1×
// font. This only sizes the visible box and the fade masks; the lyric
// lines themselves flow at their natural (measured) heights so long,
// wrapped, or furigana-tall lines push their neighbours apart instead
// of overlapping a fixed-height slot.
const SLOT_BASE_REM = 7;
const VIEWPORT_LINES = 3;

export default function LyricsView({ lines, activeIndex, fontScale, showRomaji }: Props) {
  const slot = SLOT_BASE_REM * fontScale;
  const containerHeight = slot * VIEWPORT_LINES;

  const viewportRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<HTMLDivElement>(null);

  const [translateY, setTranslateY] = useState(0);
  // Skip the transition on the very first positioning so the track doesn't
  // visibly slide in from the top on mount.
  const [animate, setAnimate] = useState(false);

  // Snap instantly when the user seeks the video by a large amount — the
  // 500ms slide is meant for natural line-to-line advances, not 20-line
  // jumps which would look like a delayed crawl.
  const prevActiveRef = useRef(activeIndex);
  const isJump = Math.abs(activeIndex - prevActiveRef.current) > 2;
  useEffect(() => {
    prevActiveRef.current = activeIndex;
  }, [activeIndex]);

  // Anchor for centring: clamp so we always have a valid target even before
  // playback has produced a real active index.
  const anchorIndex =
    lines.length > 0 ? Math.min(Math.max(activeIndex, 0), lines.length - 1) : 0;

  // After layout, measure the active line's real position and centre it in
  // the viewport. Runs before paint (useLayoutEffect) so there's no flash.
  // Depends on everything that can change a line's height: font scale and
  // the romaji tier both do.
  useLayoutEffect(() => {
    const viewport = viewportRef.current;
    const active = activeRef.current;
    if (!viewport || !active) return;
    const activeCenter = active.offsetTop + active.offsetHeight / 2;
    setTranslateY(viewport.clientHeight / 2 - activeCenter);
  }, [anchorIndex, fontScale, showRomaji, lines]);

  // Enable the slide transition only after the first paint.
  useEffect(() => {
    setAnimate(true);
  }, []);

  return (
    <div
      ref={viewportRef}
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
        className={`absolute inset-x-0 top-0 flex flex-col items-center ${
          animate && !isJump ? "transition-transform duration-500 ease-out-soft" : ""
        }`}
        style={{
          transform: `translateY(${translateY}px)`,
          rowGap: `${1.5 * fontScale}rem`,
        }}
      >
        {lines.map((line, index) => (
          <div
            key={line.line_index}
            ref={index === anchorIndex ? activeRef : undefined}
            className="w-full"
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
