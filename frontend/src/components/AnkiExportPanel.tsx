import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import type { LibraryEntry } from "../api/types";

interface Props {
  language: string;
  languageLabel: string;
  songs: LibraryEntry[];
  onClose: () => void;
}

export default function AnkiExportPanel({ language, languageLabel, songs, onClose }: Props) {
  const eligible = useMemo(() => songs.filter((s) => s.ingestion_status === "ready"), [songs]);
  const [selected, setSelected] = useState<Set<number>>(
    () => new Set(eligible.map((s) => s.id)),
  );
  const [preview, setPreview] = useState<{ count: number; sample: string[] } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const songIds = useMemo(() => [...selected], [selected]);

  useEffect(() => {
    let cancelled = false;
    api
      .ankiPreview(language, songIds)
      .then((r) => {
        if (!cancelled) setPreview({ count: r.count, sample: r.sample });
      })
      .catch(() => {
        if (!cancelled) setPreview(null);
      });
    return () => {
      cancelled = true;
    };
  }, [language, songIds]);

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function setAll(on: boolean) {
    setSelected(on ? new Set(eligible.map((s) => s.id)) : new Set());
  }

  async function download() {
    setBusy(true);
    setError(null);
    try {
      const blob = await api.ankiExport(language, songIds);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `llmp-${language}.apkg`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-lg border border-accent-400/30 bg-ink-900/60 p-4 text-sm">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-accent-200">
            Export {languageLabel} to Anki
          </div>
          <div className="text-xs text-slate-500">
            Pick which songs to include. We drop short / grammatical filler and require a
            dictionary gloss.
          </div>
        </div>
        <button
          onClick={onClose}
          className="rounded-md border border-ink-700 bg-ink-800/70 px-2 py-1 text-xs text-slate-400 hover:text-slate-200"
        >
          close
        </button>
      </div>

      {eligible.length === 0 ? (
        <p className="text-xs text-slate-500">
          No ready songs in this language yet. Wait for ingestion to finish.
        </p>
      ) : (
        <>
          <div className="mb-2 flex items-center gap-3 text-xs text-slate-400">
            <button
              onClick={() => setAll(true)}
              className="text-accent-300 hover:text-accent-200"
            >
              all
            </button>
            <span className="text-slate-600">·</span>
            <button
              onClick={() => setAll(false)}
              className="text-accent-300 hover:text-accent-200"
            >
              none
            </button>
            <span className="ml-auto text-slate-500">
              {selected.size}/{eligible.length} selected
            </span>
          </div>

          <ul className="mb-3 flex max-h-48 flex-col gap-1 overflow-y-auto pr-1">
            {eligible.map((s) => (
              <li key={s.id}>
                <label className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-ink-800/60">
                  <input
                    type="checkbox"
                    checked={selected.has(s.id)}
                    onChange={() => toggle(s.id)}
                    className="h-3 w-3 accent-accent-400"
                  />
                  <span className="min-w-0 flex-1 truncate text-xs text-slate-200">
                    {s.title}
                  </span>
                  <span className="truncate text-[11px] text-slate-500">{s.artist}</span>
                </label>
              </li>
            ))}
          </ul>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-xs text-slate-400">
              {preview ? (
                <>
                  <span className="text-slate-200">{preview.count}</span> cards
                  {preview.sample.length > 0 && (
                    <span className="ml-2 text-slate-500">
                      e.g. {preview.sample.slice(0, 5).join(", ")}
                    </span>
                  )}
                </>
              ) : (
                <span className="text-slate-500">counting…</span>
              )}
            </div>
            <button
              onClick={download}
              disabled={busy || selected.size === 0 || preview?.count === 0}
              className="rounded-md border border-accent-400/40 bg-accent-400/10 px-3 py-1.5 text-xs font-medium text-accent-200 transition hover:bg-accent-400/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy ? "building…" : "Download .apkg"}
            </button>
          </div>

          {error && <p className="mt-2 text-xs text-rose-300">{error}</p>}
        </>
      )}
    </div>
  );
}
