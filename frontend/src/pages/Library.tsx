import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import type { LibraryEntry } from "../api/types";

const LANGUAGE_LABEL: Record<string, string> = {
  ru: "Russian",
  ja: "Japanese",
};

export default function LibraryPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["library"],
    queryFn: api.library,
  });

  async function remove(id: number) {
    await api.deleteSong(id);
    queryClient.invalidateQueries({ queryKey: ["library"] });
  }

  const { ru, ja, other } = useMemo(() => {
    const ru: LibraryEntry[] = [];
    const ja: LibraryEntry[] = [];
    const other: LibraryEntry[] = [];
    for (const s of data ?? []) {
      if (s.language === "ru") ru.push(s);
      else if (s.language === "ja") ja.push(s);
      else other.push(s);
    }
    return { ru, ja, other };
  }, [data]);

  return (
    <section className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-6 py-12">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Library</h1>
          <p className="text-sm text-slate-400">Previously ingested songs.</p>
        </div>
        <Link
          to="/"
          className="rounded-md border border-ink-700 bg-ink-800/70 px-3 py-1.5 text-xs text-slate-200 transition hover:border-accent-400/40 hover:text-accent-200"
        >
          + Add a song
        </Link>
      </div>

      {isLoading && <p className="text-sm text-slate-400">Loading…</p>}

      {!isLoading && data?.length === 0 && (
        <p className="rounded-lg border border-ink-800/60 bg-ink-900/40 p-6 text-sm text-slate-400">
          Nothing here yet. <Link to="/" className="text-accent-300 underline">Search for a song</Link> to get started.
        </p>
      )}

      {!isLoading && data && data.length > 0 && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <LanguageColumn title={LANGUAGE_LABEL.ru} songs={ru} onDelete={remove} />
          <LanguageColumn title={LANGUAGE_LABEL.ja} songs={ja} onDelete={remove} />
          {other.length > 0 && (
            <LanguageColumn title="Other" songs={other} onDelete={remove} />
          )}
        </div>
      )}
    </section>
  );
}

function LanguageColumn({
  title,
  songs,
  onDelete,
}: {
  title: string;
  songs: LibraryEntry[];
  onDelete: (id: number) => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <h2 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
        {title}
        <span className="rounded-full border border-ink-700 bg-ink-800/60 px-2 py-0.5 text-[10px] font-normal normal-case tracking-normal text-slate-500">
          {songs.length}
        </span>
      </h2>
      {songs.length === 0 ? (
        <p className="rounded-lg border border-dashed border-ink-800/80 bg-ink-900/20 p-4 text-xs text-slate-500">
          None yet.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {songs.map((s) => (
            <LibraryRow key={s.id} song={s} onDelete={() => onDelete(s.id)} />
          ))}
        </ul>
      )}
    </div>
  );
}

function LibraryRow({ song, onDelete }: { song: LibraryEntry; onDelete: () => void }) {
  const statusBadge =
    song.ingestion_status === "ready"
      ? null
      : (
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wider ${
            song.ingestion_status === "failed"
              ? "border border-rose-400/30 bg-rose-400/10 text-rose-200"
              : "border border-amber-400/30 bg-amber-400/10 text-amber-200"
          }`}
        >
          {song.ingestion_status}
        </span>
      );

  return (
    <li className="flex items-center justify-between gap-4 rounded-lg border border-ink-800/80 bg-ink-900/40 px-4 py-3 transition-colors hover:border-accent-400/30">
      <Link to={`/song/${song.id}`} className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <div className="truncate text-sm font-medium text-slate-100">{song.title}</div>
          {statusBadge}
        </div>
        <div className="truncate text-xs text-slate-400">{song.artist}</div>
      </Link>
      <button
        onClick={(e) => {
          e.preventDefault();
          if (confirm(`Remove "${song.title}" from your library?`)) onDelete();
        }}
        className="rounded-md border border-ink-700 bg-ink-800/70 px-2 py-1 text-xs text-slate-400 transition hover:border-rose-400/40 hover:text-rose-300"
        title="Delete song"
      >
        delete
      </button>
    </li>
  );
}
