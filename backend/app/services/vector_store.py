"""Chunk transcripts, embed with OpenAI, persist in Chroma per session."""

from __future__ import annotations

import uuid
from typing import Any

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.models.schemas import VideoMetadata
from app.services.transcript_utils import hook_snippet


def _collection_name(session_id: str) -> str:
    safe = session_id.replace("-", "_")
    return f"session_{safe}"


def chunk_and_store(
    session_id: str,
    transcripts: dict[str, str],
    videos: list[VideoMetadata],
) -> int:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    platform_by_id = {v.video_id: v.platform for v in videos}
    duration_by_id = {v.video_id: v.duration_seconds for v in videos}
    docs: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for video_id, text in transcripts.items():
        if not text.strip():
            continue
        chunks = splitter.split_text(text)
        hook_text = hook_snippet(text, duration_by_id.get(video_id))
        for idx, chunk in enumerate(chunks):
            is_hook = idx == 0 or (hook_text and hook_text[:40] in chunk[: max(len(chunk), 40)])
            docs.append(chunk)
            metadatas.append(
                {
                    "session_id": session_id,
                    "video_id": video_id,
                    "chunk_index": idx,
                    "platform": platform_by_id.get(video_id, "unknown"),
                    "is_hook": is_hook,
                }
            )

    if not docs:
        return 0

    embeddings = OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )

    Chroma.from_texts(
        texts=docs,
        embedding=embeddings,
        metadatas=metadatas,
        collection_name=_collection_name(session_id),
        persist_directory=settings.chroma_persist_dir,
    )
    return len(docs)


def get_retriever(session_id: str, k: int = 6):
    embeddings = OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )
    store = Chroma(
        collection_name=_collection_name(session_id),
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )
    return store.as_retriever(search_kwargs={"k": k})


def new_session_id() -> str:
    return str(uuid.uuid4())
