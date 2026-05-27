import { useState } from "react";

import type { TokenOut } from "../api/types";
import TokenTooltip from "./TokenTooltip";

interface Props {
  token: TokenOut;
  active: boolean;
}

export default function WordToken({ token, active }: Props) {
  const [open, setOpen] = useState(false);
  if (!token.is_word) {
    return <span className="text-slate-500">{token.surface}</span>;
  }
  // For Japanese tokens with a hiragana reading, render the surface
  // as <ruby> with <rt> furigana. Browsers without ruby support fall
  // back to displaying the rt text in parentheses; modern browsers
  // render it stacked above. Translation-line tier already exists,
  // so no romaji here.
  const inner = token.reading ? (
    <ruby>
      {token.surface}
      <rt className="text-[0.55em] font-normal tracking-tight text-slate-300">
        {token.reading}
      </rt>
    </ruby>
  ) : (
    token.surface
  );

  return (
    <span
      className="relative inline-block cursor-help"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
      tabIndex={0}
    >
      <span
        className={`rounded px-0.5 transition-colors ${
          active
            ? "hover:bg-accent-400/15 hover:text-accent-200"
            : "hover:bg-ink-700/60 hover:text-slate-100"
        }`}
      >
        {inner}
      </span>
      {open && <TokenTooltip token={token} />}
    </span>
  );
}
