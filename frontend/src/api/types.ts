export interface AutocompleteHit {
  lrclib_id: number;
  track_name: string;
  artist_name: string;
  album_name: string | null;
  duration: number | null;
}

export interface IngestRequest {
  lrclib_id: number;
  artist: string;
  title: string;
  force?: boolean;
}

export interface IngestResponse {
  song_id: number;
  status: "ingesting" | "ready" | "failed";
}

export interface StatusResponse {
  song_id: number;
  status: "ingesting" | "ready" | "failed";
  error: string | null;
}

export interface TokenOut {
  surface: string;
  lemma: string;
  pos: string | null;
  grammar: string | null;
  is_word: boolean;
  definition_en: string | null;
}

export interface LineOut {
  line_index: number;
  start_ms: number;
  original_text: string;
  transliteration: string;
  translation: string | null;
  tokens: TokenOut[];
}

export interface SongOut {
  id: number;
  artist: string;
  title: string;
  language: string;
  youtube_video_id: string | null;
  is_topic_match: boolean;
  ingestion_status: "ingesting" | "ready" | "failed";
  effective_offset_ms: number;
  lines: LineOut[];
}

export interface OffsetSubmitResponse {
  song_id: number;
  effective_offset_ms: number;
  submission_count: number;
}
