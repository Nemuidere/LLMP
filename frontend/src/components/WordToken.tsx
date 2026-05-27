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
        {token.surface}
      </span>
      {open && <TokenTooltip token={token} />}
    </span>
  );
}
