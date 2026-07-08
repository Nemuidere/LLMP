import { useLayoutEffect, useRef, useState, type CSSProperties, type RefObject } from "react";
import { createPortal } from "react-dom";

import type { TokenOut } from "../api/types";

interface Props {
  token: TokenOut;
  anchorRef: RefObject<HTMLElement>;
}

// Gap between the word and the tooltip, and the min margin we keep from
// the viewport edges when clamping/flipping.
const GAP = 8;
const MARGIN = 8;

export default function TokenTooltip({ token, anchorRef }: Props) {
  const tipRef = useRef<HTMLSpanElement>(null);
  // Start hidden so the first paint doesn't flash at (0,0) before the
  // layout effect measures and positions it.
  const [style, setStyle] = useState<CSSProperties>({ visibility: "hidden" });

  useLayoutEffect(() => {
    const anchor = anchorRef.current;
    const tip = tipRef.current;
    if (!anchor || !tip) return;

    const a = anchor.getBoundingClientRect();
    const t = tip.getBoundingClientRect();

    // Horizontal: centre on the word, then clamp inside the viewport.
    const centerX = a.left + a.width / 2;
    const left = Math.max(
      MARGIN,
      Math.min(centerX - t.width / 2, window.innerWidth - t.width - MARGIN),
    );

    // Vertical: prefer below the word; flip above if it would overflow the
    // bottom and there's more room up top.
    let top = a.bottom + GAP;
    const overflowsBottom = top + t.height > window.innerHeight - MARGIN;
    const fitsAbove = a.top - GAP - t.height > MARGIN;
    if (overflowsBottom && fitsAbove) {
      top = a.top - GAP - t.height;
    }

    setStyle({ top, left, visibility: "visible" });
  }, [anchorRef, token]);

  return createPortal(
    <span
      ref={tipRef}
      role="tooltip"
      style={style}
      className="pointer-events-none fixed z-50 w-72 rounded-lg border border-ink-700 bg-ink-950 p-3 text-left text-sm shadow-xl shadow-black/60"
    >
      <span className="block font-cyr text-base font-semibold text-white">
        {token.lemma}
        {token.reading && (
          <span className="ml-2 align-middle text-xs font-normal text-slate-400">
            ({token.reading})
          </span>
        )}
      </span>
      <span className="mt-0.5 block text-xs uppercase tracking-wide text-slate-400">
        {[token.pos, token.grammar].filter(Boolean).join(" · ") || "—"}
      </span>
      <span className="mt-2 block text-slate-200">
        {token.definition_en ?? <span className="italic text-slate-500">no definition</span>}
      </span>
    </span>,
    document.body,
  );
}
