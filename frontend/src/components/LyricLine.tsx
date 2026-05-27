import type { LineOut } from "../api/types";
import WordToken from "./WordToken";

interface Props {
  line: LineOut;
  isActive: boolean;
  distance: number;
  fontScale: number;
}

export default function LyricLine({ line, isActive, distance, fontScale }: Props) {
  // Three visible slots (active + one above + one below) stay bright.
  // Lines further than that fade via the top/bottom gradient overlays.
  const opacity = isActive ? 1 : Math.abs(distance) <= 1 ? 0.75 : 0.45;

  return (
    <div
      className="flex w-full max-w-3xl flex-col items-center gap-1 px-6 text-center transition-all duration-500 ease-out-soft"
      style={{
        opacity,
        transform: isActive ? "scale(1.02)" : "scale(1)",
      }}
    >
      <p
        className={`flex flex-wrap justify-center gap-x-1.5 font-cyr font-medium leading-snug ${
          isActive ? "text-white" : "text-slate-100"
        }`}
        style={{ fontSize: `${1.5 * fontScale}rem` }}
      >
        {line.tokens.length > 0 ? (
          line.tokens.map((t, i) => <WordToken key={i} token={t} active={isActive} />)
        ) : (
          <span>{line.original_text || "…"}</span>
        )}
      </p>

      <p
        className="font-mono leading-snug text-slate-300"
        style={{ fontSize: `${0.95 * fontScale}rem` }}
      >
        {line.transliteration}
      </p>

      {line.translation && (
        <p
          className="italic leading-snug text-accent-200"
          style={{ fontSize: `${1.05 * fontScale}rem` }}
        >
          {line.translation}
        </p>
      )}
    </div>
  );
}
