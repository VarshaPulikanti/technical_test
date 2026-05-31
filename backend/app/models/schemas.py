from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class IngestRequest(BaseModel):
    youtube_url: HttpUrl = Field(..., description="YouTube video URL (Video A)")
    instagram_url: HttpUrl = Field(..., description="Instagram Reel URL (Video B)")


class VideoMetadata(BaseModel):
    video_id: Literal["A", "B"]
    platform: str
    url: str
    title: str | None = None
    creator: str | None = None
    follower_count: int | None = None
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    hashtags: list[str] = Field(default_factory=list)
    upload_date: str | None = None
    duration_seconds: float | None = None
    engagement_rate: float | None = None
    transcript_preview: str | None = None


class IngestResponse(BaseModel):
    session_id: str
    videos: list[VideoMetadata]
    chunk_count: int


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatSource(BaseModel):
    video_id: str
    chunk_index: int
    snippet: str
    platform: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]


class SessionState(BaseModel):
    session_id: str
    videos: list[VideoMetadata]
    chunk_count: int
