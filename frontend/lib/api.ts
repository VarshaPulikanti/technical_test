import type { ChatSource, IngestResponse } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function ingestVideos(
  youtubeUrl: string,
  instagramUrl: string
): Promise<IngestResponse> {
  const res = await fetch(`${API}/api/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      youtube_url: youtubeUrl,
      instagram_url: instagramUrl,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Ingest failed (${res.status})`);
  }
  return res.json();
}

export type StreamEvent =
  | { type: "token"; content: string }
  | { type: "sources"; sources: ChatSource[] }
  | { type: "done" };

export async function* streamChat(
  sessionId: string,
  message: string
): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${API}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!res.ok || !res.body) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Chat failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.trim()) continue;
      yield JSON.parse(line) as StreamEvent;
    }
  }
  if (buffer.trim()) {
    yield JSON.parse(buffer) as StreamEvent;
  }
}
