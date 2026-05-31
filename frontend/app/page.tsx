"use client";

import { useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { VideoCard } from "@/components/VideoCard";
import { ingestVideos } from "@/lib/api";
import type { VideoMetadata } from "@/lib/types";
import { isInstagramReelUrl, isYouTubeUrl } from "@/lib/validate";

const DEFAULT_YT = "";
const DEFAULT_IG = "";

export default function Home() {
  const [youtubeUrl, setYoutubeUrl] = useState(DEFAULT_YT);
  const [instagramUrl, setInstagramUrl] = useState(DEFAULT_IG);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [videos, setVideos] = useState<VideoMetadata[]>([]);
  const [chunkCount, setChunkCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const runIngest = async () => {
    if (!isYouTubeUrl(youtubeUrl)) {
      setStatus("Video A must be a valid YouTube link");
      return;
    }
    if (!isInstagramReelUrl(instagramUrl)) {
      setStatus("Video B must be a valid Instagram Reel / post link");
      return;
    }

    setLoading(true);
    setStatus("Fetching metadata, transcripts, embedding chunks…");
    try {
      const data = await ingestVideos(youtubeUrl, instagramUrl);
      setSessionId(data.session_id);
      setVideos(data.videos);
      setChunkCount(data.chunk_count);
      setStatus(`Ready — ${data.chunk_count} chunks indexed for session ${data.session_id.slice(0, 8)}…`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Ingest failed");
    } finally {
      setLoading(false);
    }
  };

  const videoA = videos.find((v) => v.video_id === "A");
  const videoB = videos.find((v) => v.video_id === "B");

  return (
    <main className="page">
      <header className="hero">
        <h1>Video A vs B — Creator RAG</h1>
        <p>
          YouTube (A) + Instagram Reel (B) → transcripts, engagement metrics, vector search, streaming chat.
        </p>
      </header>

      <form
        className="ingest"
        onSubmit={(e) => {
          e.preventDefault();
          runIngest();
        }}
      >
        <input
          aria-label="YouTube URL"
          value={youtubeUrl}
          onChange={(e) => setYoutubeUrl(e.target.value)}
          placeholder="YouTube URL (Video A)"
        />
        <input
          aria-label="Instagram URL"
          value={instagramUrl}
          onChange={(e) => setInstagramUrl(e.target.value)}
          placeholder="Instagram Reel URL (Video B) — required"
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? "Ingesting…" : "Ingest & index"}
        </button>
      </form>

      {status && (
        <p className={`status ${status.includes("failed") || status.includes("Error") ? "error" : ""}`}>
          {status}
        </p>
      )}

      <div className="layout">
        {videoA ? (
          <VideoCard video={videoA} label="Video A" />
        ) : (
          <div className="card">
            <p className="empty">Video A card appears after ingest</p>
          </div>
        )}
        {videoB ? (
          <VideoCard video={videoB} label="Video B" />
        ) : (
          <div className="card">
            <p className="empty">Video B card appears after ingest</p>
          </div>
        )}
        <ChatPanel key={sessionId ?? "idle"} sessionId={sessionId} disabled={!sessionId} />
      </div>

      {chunkCount > 0 && (
        <p className="status" style={{ marginTop: "1rem" }}>
          Indexed {chunkCount} transcript chunks with video_id tags A/B in ChromaDB.
        </p>
      )}
    </main>
  );
}
