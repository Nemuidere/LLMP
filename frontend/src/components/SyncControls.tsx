import { useState } from "react";

interface Props {
  offsetMs: number;
  onChange: (ms: number) => void;
  onSave: (ms: number) => Promise<number>;
  font: {
    scale: number;
    increase: () => void;
    decrease: () => void;
    reset: () => void;
  };
}

export default function SyncControls({ offsetMs, onChange, onSave, font }: Props) {
  const [saving, setSaving] = useState(false);
  const [savedHint, setSavedHint] = useState<string | null>(null);

  function bump(delta: number) {
    onChange(offsetMs + delta);
  }

  async function save() {
    setSaving(true);
    setSavedHint(null);
    try {
      const effective = await onSave(offsetMs);
      setSavedHint(`saved · community offset = ${effective}ms`);
    } catch (e) {
      setSavedHint(`save failed: ${(e as Error).message.slice(0, 80)}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-ink-800/60 bg-ink-900/40 px-4 py-3 text-sm">
      <div className="flex items-center gap-2">
        <span className="mr-2 text-xs uppercase tracking-wider text-slate-500">sync</span>
        <Btn onClick={() => bump(-500)}>−500ms</Btn>
        <Btn onClick={() => bump(-100)}>−100ms</Btn>
        <span className="mx-2 min-w-[5ch] text-center font-mono text-slate-300">
          {offsetMs > 0 ? "+" : ""}
          {offsetMs}ms
        </span>
        <Btn onClick={() => bump(100)}>+100ms</Btn>
        <Btn onClick={() => bump(500)}>+500ms</Btn>
      </div>

      <div className="flex items-center gap-2">
        <span className="mr-2 text-xs uppercase tracking-wider text-slate-500">font</span>
        <Btn onClick={font.decrease}>A−</Btn>
        <span className="mx-1 min-w-[3ch] text-center font-mono text-slate-300">
          {font.scale.toFixed(1)}×
        </span>
        <Btn onClick={font.increase}>A+</Btn>
        <Btn onClick={font.reset}>reset</Btn>
      </div>

      <div className="flex items-center gap-3">
        {savedHint && <span className="text-xs text-slate-400">{savedHint}</span>}
        <button
          onClick={save}
          disabled={saving}
          className="rounded-md border border-accent-400/40 bg-accent-400/10 px-3 py-1.5 text-xs font-medium text-accent-200 transition hover:bg-accent-400/20 disabled:opacity-50"
        >
          {saving ? "saving…" : "save to community"}
        </button>
      </div>
    </div>
  );
}

function Btn({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className="rounded-md border border-ink-700/80 bg-ink-800/60 px-2.5 py-1 font-mono text-xs text-slate-200 transition hover:border-accent-400/40 hover:bg-ink-700"
    >
      {children}
    </button>
  );
}
