"""Pull transcripts + metadata from YouTube and Instagram via yt-dlp + youtube-transcript-api."""

from __future__ import annotations

import json
import re
from typing import Any

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from app.models.schemas import VideoMetadata
from app.services.transcript_utils import fetch_subtitle_from_info, hook_snippet


def _extract_youtube_id(url: str) -> str | None:
    patterns = [
        r"(?:v=|/shorts/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"embed/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _engagement_rate(views: int | None, likes: int | None, comments: int | None) -> float | None:
    if not views or views <= 0:
        return None
    likes = likes or 0
    comments = comments or 0
    return round(((likes + comments) / views) * 100, 4)


def _parse_hashtags(description: str | None, tags: list[str] | None) -> list[str]:
    found: list[str] = []
    if description:
        found.extend(re.findall(r"#(\w+)", description))
    if tags:
        for tag in tags:
            clean = tag.lstrip("#").strip()
            if clean and clean not in found:
                found.append(clean)
    return found[:30]


def _fetch_ytdlp_info(url: str) -> dict[str, Any]:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def _youtube_transcript(video_id: str) -> str:
    try:
        segments = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable):
        try:
            listing = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = listing.find_generated_transcript(["en"])
            segments = transcript.fetch()
        except Exception:
            return ""
    return " ".join(seg.get("text", "") for seg in segments).strip()


def _subtitle_from_ytdlp(info: dict[str, Any]) -> str:
    text = fetch_subtitle_from_info(info)
    if text:
        return text
    desc = info.get("description") or ""
    return desc.strip()


def platform_from_url(url: str) -> str:
    lower = url.lower()
    if "instagram.com" in lower:
        return "instagram"
    if "youtube.com" in lower or "youtu.be" in lower:
        return "youtube"
    return "unknown"


def fetch_video(url: str, video_id: str) -> tuple[VideoMetadata, str]:
    """Return metadata model + full transcript text."""
    info = _fetch_ytdlp_info(url)
    platform = platform_from_url(url)

    views = _safe_int(info.get("view_count"))
    likes = _safe_int(info.get("like_count"))
    comments = _safe_int(info.get("comment_count"))

    creator = info.get("uploader") or info.get("channel") or info.get("uploader_id")
    follower_count = _safe_int(info.get("channel_follower_count") or info.get("follower_count"))

    hashtags = _parse_hashtags(info.get("description"), info.get("tags"))
    upload_date = info.get("upload_date")
    if upload_date and len(upload_date) == 8:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"

    duration = info.get("duration")
    duration_seconds = float(duration) if duration is not None else None

    transcript = ""
    if platform == "youtube":
        yt_id = _extract_youtube_id(url) or info.get("id")
        if yt_id:
            transcript = _youtube_transcript(yt_id)
    if not transcript:
        transcript = _subtitle_from_ytdlp(info)
    if not transcript:
        # fallback: title + description often enough for short reels
        parts = [info.get("title") or "", info.get("description") or ""]
        transcript = "\n".join(p for p in parts if p).strip()

    engagement = _engagement_rate(views, likes, comments)
    hook = hook_snippet(transcript, duration_seconds)

    meta = VideoMetadata(
        video_id=video_id,  # type: ignore[arg-type]
        platform=platform,
        url=url,
        title=info.get("title"),
        creator=creator,
        follower_count=follower_count,
        views=views,
        likes=likes,
        comments=comments,
        hashtags=hashtags,
        upload_date=upload_date,
        duration_seconds=duration_seconds,
        engagement_rate=engagement,
        transcript_preview=(transcript[:280] + "…") if len(transcript) > 280 else transcript,
        hook_preview=hook or None,
    )
    return meta, transcript


def metadata_context_json(videos: list[VideoMetadata]) -> str:
    """Structured facts the LLM can use without retrieval."""
    payload = []
    for v in videos:
        payload.append(
            {
                "video_id": v.video_id,
                "platform": v.platform,
                "title": v.title,
                "creator": v.creator,
                "follower_count": v.follower_count,
                "views": v.views,
                "likes": v.likes,
                "comments": v.comments,
                "engagement_rate_percent": v.engagement_rate,
                "hashtags": v.hashtags,
                "upload_date": v.upload_date,
                "duration_seconds": v.duration_seconds,
                "hook_preview_first_5s": v.hook_preview,
                "url": v.url,
            }
        )
    return json.dumps(payload, indent=2)
