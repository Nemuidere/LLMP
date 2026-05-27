import type { TokenOut } from "../api/types";

interface Props {
  token: TokenOut;
}

export default function TokenTooltip({ token }: Props) {
  return (
    <span
      role="tooltip"
      className="pointer-events-none absolute left-1/2 top-full z-50 mt-2 w-72 -translate-x-1/2 rounded-lg border border-ink-700 bg-ink-950 p-3 text-left text-sm shadow-xl shadow-black/60"
    >
      <span className="block font-cyr text-base font-semibold text-white">
        {token.lemma}
      </span>
      <span className="mt-0.5 block text-xs uppercase tracking-wide text-slate-400">
        {[token.pos, token.grammar].filter(Boolean).join(" · ") || "—"}
      </span>
      <span className="mt-2 block text-slate-200">
        {token.definition_en ?? <span className="italic text-slate-500">no definition</span>}
      </span>
    </span>
  );
}
