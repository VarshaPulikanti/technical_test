"use client";

import type { VideoMetadata } from "@/lib/types";

function fmt(n: number | null | undefined): string {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

interface Props {
  video: VideoMetadata;
  label: string;
}

export function VideoCard({ video, label }: Props) {
  const embedUrl =
    video.platform === "youtube" && video.url.includes("watch?v=")
      ? video.url.replace("watch?v=", "embed/").split("&")[0]
      : null;

  return (
    <article className="card">
      <header className="card-header">
        <span className="badge">{label}</span>
        <span className="platform">{video.platform}</span>
      </header>

      {embedUrl ? (
        <iframe
          className="embed"
          src={embedUrl}
          title={video.title || label}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      ) : (
        <a className="link-preview" href={video.url} target="_blank" rel="noreferrer">
          Open {video.platform} reel →
        </a>
      )}

      <h2 className="title">{video.title || "Untitled"}</h2>
      <p className="creator">
        {video.creator || "Unknown creator"}
        {video.follower_count != null && (
          <span> · {fmt(video.follower_count)} followers</span>
        )}
      </p>

      <dl className="stats">
        <div>
          <dt>Views</dt>
          <dd>{fmt(video.views)}</dd>
        </div>
        <div>
          <dt>Likes</dt>
          <dd>{fmt(video.likes)}</dd>
        </div>
        <div>
          <dt>Comments</dt>
          <dd>{fmt(video.comments)}</dd>
        </div>
        <div>
          <dt>Engagement</dt>
          <dd title="(likes + comments) / views × 100">
            {video.engagement_rate != null
              ? `${video.engagement_rate.toFixed(2)}%`
              : "—"}
          </dd>
        </div>
        <div>
          <dt>Duration</dt>
          <dd>
            {video.duration_seconds != null
              ? `${Math.round(video.duration_seconds)}s`
              : "—"}
          </dd>
        </div>
        <div>
          <dt>Uploaded</dt>
          <dd>{video.upload_date || "—"}</dd>
        </div>
      </dl>

      {video.hashtags.length > 0 && (
        <p className="tags">{video.hashtags.map((t) => `#${t}`).join(" ")}</p>
      )}

      {video.hook_preview && (
        <p className="preview">
          <strong>Hook (~5s):</strong> {video.hook_preview}
        </p>
      )}

      {video.transcript_preview && (
        <p className="preview">{video.transcript_preview}</p>
      )}
    </article>
  );
}
