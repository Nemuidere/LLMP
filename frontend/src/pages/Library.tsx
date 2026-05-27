import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import AnkiExportPanel from "../components/AnkiExportPanel";
import { api } from "../api/client";
import type { LibraryEntry } from "../api/types";

const LANGUAGE_LABEL: Record<string, string> = {
  ru: "Russian",
  ja: "Japanese",
};

type SortKey = "recent" | "title" | "artist";

const SORT_LABEL: Record<SortKey, string> = {
  recent: "Recently added",
  title: "Title (A→Z)",
  artist: "Artist (A→Z)",
};

export default function LibraryPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["library"],
    queryFn: api.library,
  });

  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("recent");

  async function remove(id: number) {
    await api.deleteSong(id);
    queryClient.invalidateQueries({ queryKey: ["library"] });
  }

  const { ru, ja, other } = useMemo(() => {
    const q = query.trim().toLowerCase();
    const matches = (s: LibraryEntry) =>
      q === "" ||
      s.title.toLowerCase().includes(q) ||
      s.artist.toLowerCase().includes(q);

    const cmp = (a: LibraryEntry, b: LibraryEntry) => {
      if (sort === "title") return a.title.localeCompare(b.title);
      if (sort === "artist") return a.artist.localeCompare(b.artist);
      // recent: API returns updated_at desc already; keep that ordering.
      return 0;
    };

    const ru: LibraryEntry[] = [];
    const ja: LibraryEntry[] = [];
    const other: LibraryEntry[] = [];
    for (const s of data ?? []) {
      if (!matches(s)) continue;
      if (s.language === "ru") ru.push(s);
      else if (s.language === "ja") ja.push(s);
      else other.push(s);
    }
    if (sort !== "recent") {
      ru.sort(cmp);
      ja.sort(cmp);
      other.sort(cmp);
    }
    return { ru, ja, other };
  }, [data, query, sort]);

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
        <>
          <div className="flex flex-wrap items-center gap-3">
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter by title or artist…"
              className="min-w-0 flex-1 rounded-md border border-ink-700 bg-ink-900/60 px-3 py-1.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-accent-400/40 focus:outline-none"
            />
            <label className="flex items-center gap-2 text-xs text-slate-400">
              sort
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value as SortKey)}
                className="rounded-md border border-ink-700 bg-ink-900/60 px-2 py-1 text-xs text-slate-200 focus:border-accent-400/40 focus:outline-none"
              >
                {(Object.keys(SORT_LABEL) as SortKey[]).map((k) => (
                  <option key={k} value={k}>
                    {SORT_LABEL[k]}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <LanguageColumn
              language="ru"
              title={LANGUAGE_LABEL.ru}
              songs={ru}
              onDelete={remove}
            />
            <LanguageColumn
              language="ja"
              title={LANGUAGE_LABEL.ja}
              songs={ja}
              onDelete={remove}
            />
            {other.length > 0 && (
              <LanguageColumn
                language={null}
                title="Other"
                songs={other}
                onDelete={remove}
              />
            )}
          </div>
        </>
      )}
    </section>
  );
}

function LanguageColumn({
  language,
  title,
  songs,
  onDelete,
}: {
  language: string | null;
  title: string;
  songs: LibraryEntry[];
  onDelete: (id: number) => void;
}) {
  const [exportOpen, setExportOpen] = useState(false);
  const canExport = language === "ru" || language === "ja";
  const hasReady = songs.some((s) => s.ingestion_status === "ready");

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          {title}
          <span className="rounded-full border border-ink-700 bg-ink-800/60 px-2 py-0.5 text-[10px] font-normal normal-case tracking-normal text-slate-500">
            {songs.length}
          </span>
        </h2>
        {canExport && hasReady && (
          <button
            onClick={() => setExportOpen((v) => !v)}
            className={`rounded-md border px-2 py-0.5 text-[10px] uppercase tracking-wider transition ${
              exportOpen
                ? "border-accent-400/40 bg-accent-400/10 text-accent-200"
                : "border-ink-700 bg-ink-800/60 text-slate-400 hover:border-accent-400/40 hover:text-accent-200"
            }`}
            title="Build an Anki .apkg deck from these songs"
          >
            anki
          </button>
        )}
      </div>

      {canExport && exportOpen && (
        <AnkiExportPanel
          language={language}
          languageLabel={title}
          songs={songs}
          onClose={() => setExportOpen(false)}
        />
      )}

      {songs.length === 0 ? (
        <p className="rounded-lg border border-dashed border-ink-800/80 bg-ink-900/20 p-4 text-xs text-slate-500">
          No matches.
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
