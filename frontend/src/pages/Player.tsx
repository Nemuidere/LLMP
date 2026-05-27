import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import LyricsView from "../components/LyricsView";
import SyncControls from "../components/SyncControls";
import YouTubePlayer, { type PlayerHandle } from "../components/YouTubePlayer";
import { useFontScale } from "../hooks/useFontScale";
import { usePlaybackSync } from "../hooks/usePlaybackSync";

export default function PlayerPage() {
  const { songId } = useParams();
  const id = Number(songId);
  const playerRef = useRef<PlayerHandle | null>(null);
  const [localOffsetMs, setLocalOffsetMs] = useState(0);
  const [reingesting, setReingesting] = useState(false);
  const font = useFontScale();
  const queryClient = useQueryClient();

  // Poll status until ingestion finishes, then fetch full song.
  const { data: status } = useQuery({
    queryKey: ["status", id],
    queryFn: () => api.status(id),
    refetchInterval: (q) =>
      q.state.data && q.state.data.status === "ingesting" ? 1500 : false,
    enabled: Number.isFinite(id),
  });

  const ready = status?.status === "ready";

  const { data: song } = useQuery({
    queryKey: ["song", id],
    queryFn: () => api.song(id),
    enabled: ready,
  });

  // Apply community offset to local offset on first load.
  useEffect(() => {
    if (song) setLocalOffsetMs(song.effective_offset_ms);
  }, [song]);

  const activeIndex = usePlaybackSync({
    lines: song?.lines ?? [],
    offsetMs: localOffsetMs,
    getCurrentTimeMs: () => playerRef.current?.getCurrentTimeMs() ?? 0,
  });

  async function reingest() {
    setReingesting(true);
    try {
      await api.reingest(id);
      queryClient.invalidateQueries({ queryKey: ["status", id] });
      queryClient.invalidateQueries({ queryKey: ["song", id] });
    } finally {
      setReingesting(false);
    }
  }

  if (!Number.isFinite(id)) {
    return <Centered>Invalid song id.</Centered>;
  }
  if (status?.status === "failed") {
    return (
      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center gap-4 px-6 py-16 text-center">
        <p className="text-sm text-rose-300">
          Ingestion failed: {status.error ?? "unknown error"}
        </p>
        <button
          onClick={reingest}
          disabled={reingesting}
          className="rounded-md border border-accent-400/40 bg-accent-400/10 px-4 py-2 text-sm text-accent-200 transition hover:bg-accent-400/20 disabled:opacity-50"
        >
          {reingesting ? "retrying…" : "retry ingest"}
        </button>
      </div>
    );
  }
  if (!ready || !song) {
    return <Centered>Preparing lyrics…</Centered>;
  }

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-6 py-8">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">{song.title}</h1>
          <p className="text-sm text-slate-400">{song.artist}</p>
        </div>
        <div className="flex items-center gap-3">
          {!song.is_topic_match && song.youtube_video_id && (
            <span className="rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-xs text-amber-200">
              Best-guess YouTube match — sync may need adjustment
            </span>
          )}
          <button
            onClick={reingest}
            disabled={reingesting}
            title="Re-run ingestion (e.g. if the YouTube video is wrong)"
            className="rounded-md border border-ink-700 bg-ink-800/70 px-3 py-1 text-xs text-slate-300 transition hover:border-accent-400/40 hover:text-accent-200 disabled:opacity-50"
          >
            {reingesting ? "re-ingesting…" : "wrong video?"}
          </button>
        </div>
      </header>

      <YouTubePlayer ref={playerRef} videoId={song.youtube_video_id} />

      <LyricsView
        lines={song.lines}
        activeIndex={activeIndex}
        fontScale={font.scale}
      />

      <SyncControls
        offsetMs={localOffsetMs}
        onChange={setLocalOffsetMs}
        onSave={async (ms) => {
          const r = await api.submitOffset(id, ms);
          return r.effective_offset_ms;
        }}
        font={font}
      />
    </div>
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-1 items-center justify-center text-sm text-slate-400">
      {children}
    </div>
  );
}
