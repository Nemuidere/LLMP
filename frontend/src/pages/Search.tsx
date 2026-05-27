import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import type { AutocompleteHit } from "../api/types";
import { useDebounced } from "../hooks/useDebounced";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const debounced = useDebounced(q, 300);
  const navigate = useNavigate();
  const [ingesting, setIngesting] = useState(false);

  const { data, isFetching } = useQuery({
    queryKey: ["autocomplete", debounced],
    queryFn: () => api.autocomplete(debounced),
    enabled: debounced.trim().length >= 2,
  });

  async function pick(hit: AutocompleteHit) {
    setIngesting(true);
    try {
      const res = await api.ingest({
        lrclib_id: hit.lrclib_id,
        artist: hit.artist_name,
        title: hit.track_name,
      });
      navigate(`/song/${res.song_id}`);
    } finally {
      setIngesting(false);
    }
  }

  return (
    <section className="mx-auto flex w-full max-w-2xl flex-col gap-6 px-6 py-16">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-slate-100">Find a song</h1>
        <p className="text-sm text-slate-400">
          Search by artist or title. We&apos;ll pull synced lyrics from LRCLIB.
        </p>
      </div>

      <div className="relative">
        <input
          autoFocus
          type="text"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="e.g. Кино — Группа крови"
          className="w-full rounded-xl border border-ink-700/80 bg-ink-900/60 px-4 py-3 text-base text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-accent-400/70 focus:ring-2 focus:ring-accent-400/20"
        />
        {isFetching && (
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-slate-500">
            searching…
          </span>
        )}
      </div>

      <AutocompleteList hits={data ?? []} disabled={ingesting} onPick={pick} />
    </section>
  );
}

function AutocompleteList({
  hits,
  onPick,
  disabled,
}: {
  hits: AutocompleteHit[];
  onPick: (h: AutocompleteHit) => void;
  disabled: boolean;
}) {
  // Light fade-in when results change.
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    setVisible(false);
    const id = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(id);
  }, [hits]);

  if (!hits.length) return null;

  return (
    <ul
      className={`flex flex-col gap-2 transition-opacity duration-300 ease-out-soft ${
        visible ? "opacity-100" : "opacity-0"
      }`}
    >
      {hits.map((h) => (
        <li key={h.lrclib_id}>
          <button
            disabled={disabled}
            onClick={() => onPick(h)}
            className="group flex w-full items-center justify-between rounded-lg border border-ink-800/80 bg-ink-900/40 px-4 py-3 text-left transition-all hover:border-accent-400/40 hover:bg-ink-800/70 disabled:cursor-wait disabled:opacity-50"
          >
            <div className="min-w-0">
              <div className="truncate text-sm font-medium text-slate-100">
                {h.track_name}
              </div>
              <div className="truncate text-xs text-slate-400">
                {h.artist_name}
                {h.album_name ? ` · ${h.album_name}` : ""}
              </div>
            </div>
            {h.duration && (
              <span className="ml-4 shrink-0 font-mono text-xs text-slate-500">
                {formatDuration(h.duration)}
              </span>
            )}
          </button>
        </li>
      ))}
    </ul>
  );
}

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}
