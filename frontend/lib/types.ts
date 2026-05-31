export type VideoId = "A" | "B";

export interface VideoMetadata {
  video_id: VideoId;
  platform: string;
  url: string;
  title?: string | null;
  creator?: string | null;
  follower_count?: number | null;
  views?: number | null;
  likes?: number | null;
  comments?: number | null;
  hashtags: string[];
  upload_date?: string | null;
  duration_seconds?: number | null;
  engagement_rate?: number | null;
  transcript_preview?: string | null;
  hook_preview?: string | null;
}

export interface IngestResponse {
  session_id: string;
  videos: VideoMetadata[];
  chunk_count: number;
}

export interface ChatSource {
  video_id: string;
  chunk_index: number;
  snippet: string;
  platform?: string | null;
  is_hook?: boolean;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
}
