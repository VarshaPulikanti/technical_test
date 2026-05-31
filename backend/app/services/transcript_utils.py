"""VTT parsing and hook extraction (first ~5s of speech)."""

from __future__ import annotations

import re

import httpx


def parse_vtt(raw: str) -> str:
    lines: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("WEBVTT") or "-->" in line:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        clean = re.sub(r"<[^>]+>", "", line)
        if clean:
            lines.append(clean)
    return " ".join(lines).strip()


def fetch_subtitle_from_info(info: dict) -> str:
    """Download captions when yt-dlp exposes a subtitle URL (common on IG/YT)."""
    for key in ("subtitles", "automatic_captions"):
        pool = info.get(key) or {}
        for lang in ("en", "en-US", "en-GB", "en-orig", "a.en"):
            for track in pool.get(lang) or []:
                url = track.get("url")
                if not url:
                    continue
                try:
                    resp = httpx.get(url, timeout=25, follow_redirects=True)
                    resp.raise_for_status()
                    text = resp.text
                    if "WEBVTT" in text[:30] or track.get("ext") == "vtt":
                        parsed = parse_vtt(text)
                    else:
                        parsed = parse_vtt(text) if "-->" in text else text
                    if parsed.strip():
                        return parsed.strip()
                except Exception:
                    continue
    return ""


def hook_snippet(transcript: str, duration_seconds: float | None) -> str:
    """Approximate spoken content in the first 5 seconds."""
    words = transcript.split()
    if not words:
        return ""
    if duration_seconds and duration_seconds > 0:
        # scale word count to ~5s of total runtime
        ratio = min(5.0 / duration_seconds, 0.35)
        count = max(8, int(len(words) * ratio))
    else:
        count = 25
    return " ".join(words[:count])
