"""Lightweight in-memory session registry (metadata + ingest status)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.schemas import VideoMetadata


@dataclass
class SessionRecord:
    session_id: str
    videos: list[VideoMetadata] = field(default_factory=list)
    chunk_count: int = 0


_sessions: dict[str, SessionRecord] = {}


def save_session(record: SessionRecord) -> None:
    _sessions[record.session_id] = record


def get_session(session_id: str) -> SessionRecord | None:
    return _sessions.get(session_id)


def list_sessions() -> list[str]:
    return list(_sessions.keys())
