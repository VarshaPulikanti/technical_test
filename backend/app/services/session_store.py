"""Session registry — in-memory with JSON persistence across API restarts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings
from app.models.schemas import VideoMetadata

SESSIONS_FILE = Path(settings.chroma_persist_dir).parent / "sessions.json"


@dataclass
class SessionRecord:
    session_id: str
    videos: list[VideoMetadata] = field(default_factory=list)
    chunk_count: int = 0


_sessions: dict[str, SessionRecord] = {}


def _persist() -> None:
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        sid: {
            "session_id": rec.session_id,
            "videos": [v.model_dump() for v in rec.videos],
            "chunk_count": rec.chunk_count,
        }
        for sid, rec in _sessions.items()
    }
    SESSIONS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_sessions() -> None:
    if not SESSIONS_FILE.exists():
        return
    try:
        raw = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
        for sid, data in raw.items():
            videos = [VideoMetadata(**v) for v in data.get("videos", [])]
            _sessions[sid] = SessionRecord(
                session_id=data.get("session_id", sid),
                videos=videos,
                chunk_count=int(data.get("chunk_count", 0)),
            )
    except Exception:
        pass


def save_session(record: SessionRecord) -> None:
    _sessions[record.session_id] = record
    _persist()


def get_session(session_id: str) -> SessionRecord | None:
    return _sessions.get(session_id)


def list_sessions() -> list[str]:
    return list(_sessions.keys())
