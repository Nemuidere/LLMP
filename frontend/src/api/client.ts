import type {
  AutocompleteHit,
  IngestRequest,
  IngestResponse,
  LibraryEntry,
  SongOut,
  StatusResponse,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  autocomplete: (q: string) =>
    request<AutocompleteHit[]>(`/api/songs/autocomplete?q=${encodeURIComponent(q)}`),
  ingest: (payload: IngestRequest) =>
    request<IngestResponse>("/api/songs/ingest", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  status: (songId: number) => request<StatusResponse>(`/api/songs/${songId}/status`),
  song: (songId: number) => request<SongOut>(`/api/songs/${songId}`),
  reingest: (songId: number) =>
    request<StatusResponse>(`/api/songs/${songId}/reingest`, { method: "POST" }),
  library: () => request<LibraryEntry[]>("/api/songs"),
  deleteSong: async (songId: number) => {
    const res = await fetch(`/api/songs/${songId}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`delete failed: ${res.status}`);
  },
  ankiPreview: (language: string, songIds: number[]) =>
    request<{ language: string; count: number; sample: string[] }>("/api/anki/preview", {
      method: "POST",
      body: JSON.stringify({ language, song_ids: songIds }),
    }),
  ankiExport: async (language: string, songIds: number[]): Promise<Blob> => {
    const res = await fetch("/api/anki/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language, song_ids: songIds }),
    });
    if (!res.ok) {
      const body = await res.text().catch(() => "");
      throw new Error(`${res.status}: ${body.slice(0, 200)}`);
    }
    return res.blob();
  },
};
