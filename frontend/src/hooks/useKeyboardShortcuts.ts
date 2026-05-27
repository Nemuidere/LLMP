import { useEffect } from "react";

interface Handlers {
  togglePlay: () => void;
  seekDeltaMs: (delta: number) => void;
  syncDeltaMs: (delta: number) => void;
  fontDelta: (delta: number) => void;
}

/**
 * Player-page keybindings:
 *   space      → play/pause
 *   ← / →      → seek ±5s
 *   shift+← →  → seek ±15s
 *   [ / ]      → sync ±100ms (fine)
 *   shift+[ ]  → sync ±500ms (coarse)
 *   + / −      → font scale up/down
 *
 * Ignored when the user is typing into an input/textarea.
 */
export function useKeyboardShortcuts({
  togglePlay,
  seekDeltaMs,
  syncDeltaMs,
  fontDelta,
}: Handlers): void {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      if (target) {
        const tag = target.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA" || target.isContentEditable) return;
      }

      switch (e.key) {
        case " ":
        case "Spacebar":
          e.preventDefault();
          togglePlay();
          break;
        case "ArrowLeft":
          e.preventDefault();
          seekDeltaMs((e.shiftKey ? -15 : -5) * 1000);
          break;
        case "ArrowRight":
          e.preventDefault();
          seekDeltaMs((e.shiftKey ? 15 : 5) * 1000);
          break;
        case "[":
          e.preventDefault();
          syncDeltaMs(e.shiftKey ? -500 : -100);
          break;
        case "]":
          e.preventDefault();
          syncDeltaMs(e.shiftKey ? 500 : 100);
          break;
        case "+":
        case "=":
          e.preventDefault();
          fontDelta(0.1);
          break;
        case "-":
        case "_":
          e.preventDefault();
          fontDelta(-0.1);
          break;
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [togglePlay, seekDeltaMs, syncDeltaMs, fontDelta]);
}
