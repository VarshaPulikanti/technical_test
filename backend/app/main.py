"""FastAPI backend — ingest two URLs, embed transcripts, stream RAG chat."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse, IngestRequest, IngestResponse, SessionState
from app.services import rag, session_store, vector_store
from app.services.video_fetcher import fetch_video

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API ready")
    yield


app = FastAPI(title="Creator RAG Compare", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/ingest", response_model=IngestResponse)
def ingest(body: IngestRequest):
    session_id = vector_store.new_session_id()
    youtube_url = str(body.youtube_url)
    instagram_url = str(body.instagram_url)

    try:
        meta_a, transcript_a = fetch_video(youtube_url, "A")
        meta_b, transcript_b = fetch_video(instagram_url, "B")
    except Exception as exc:
        logger.exception("Ingest failed")
        raise HTTPException(status_code=400, detail=f"Could not fetch videos: {exc}") from exc

    videos = [meta_a, meta_b]
    transcripts = {"A": transcript_a, "B": transcript_b}

    try:
        chunk_count = vector_store.chunk_and_store(session_id, transcripts, videos)
    except Exception as exc:
        logger.exception("Embedding failed")
        raise HTTPException(status_code=500, detail=f"Vector store error: {exc}") from exc

    session_store.save_session(
        session_store.SessionRecord(session_id=session_id, videos=videos, chunk_count=chunk_count)
    )

    return IngestResponse(session_id=session_id, videos=videos, chunk_count=chunk_count)


@app.get("/api/session/{session_id}", response_model=SessionState)
def get_session(session_id: str):
    record = session_store.get_session(session_id)
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionState(
        session_id=record.session_id,
        videos=record.videos,
        chunk_count=record.chunk_count,
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    record = session_store.get_session(body.session_id)
    if not record:
        raise HTTPException(status_code=404, detail="Session not found — run ingest first")

    answer, sources = rag.chat_sync(body.session_id, body.message, record.videos)
    return ChatResponse(answer=answer, sources=sources)


@app.post("/api/chat/stream")
async def chat_stream(body: ChatRequest):
    record = session_store.get_session(body.session_id)
    if not record:
        raise HTTPException(status_code=404, detail="Session not found — run ingest first")

    async def event_generator():
        async for line in rag.stream_chat(body.session_id, body.message, record.videos):
            yield line

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
