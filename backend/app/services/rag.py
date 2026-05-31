"""LangChain RAG with session memory, streaming, and source citations."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from app.config import settings
from app.models.schemas import ChatSource, VideoMetadata
from app.services.vector_store import get_retriever
from app.services.video_fetcher import metadata_context_json

# in-process memory keyed by session_id (fine for demo; swap Redis for multi-instance)
_session_histories: dict[str, list] = {}


def _get_history(session_id: str) -> list:
    if session_id not in _session_histories:
        _session_histories[session_id] = []
    return _session_histories[session_id]


def _history_factory(session_id: str):
    def get_session_history(_: str):
        from langchain_community.chat_message_histories import ChatMessageHistory

        history = ChatMessageHistory()
        for msg in _get_history(session_id):
            history.add_message(msg)
        return history

    return get_session_history


def _build_chain(session_id: str, videos: list[VideoMetadata]):
    llm = ChatOpenAI(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
        streaming=True,
    )
    retriever = get_retriever(session_id)

    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question, "
        "formulate a standalone question for retrieval. "
        "Do not answer — only reformulate if needed."
    )
    contextualize_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_prompt)

    facts = metadata_context_json(videos)
    qa_system = f"""You are a creator analytics assistant comparing two short-form videos (A = YouTube, B = Instagram Reel).

Use the retrieved transcript chunks AND the structured metadata below. Always ground answers in data.
When comparing hooks, focus on the first ~5 seconds of transcript content.
For engagement questions, use engagement_rate_percent from metadata when available.
Cite sources inline like [Video A, chunk 3] or [Video B, chunk 1] matching chunk_index in context.

Structured metadata (views, likes, engagement, creator, hashtags, dates):
{facts}
"""

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return RunnableWithMessageHistory(
        rag_chain,
        _history_factory(session_id),
        input_messages_key="input",
        history_messages_key="chat_history",
    )


def _docs_to_sources(docs: list[Document]) -> list[ChatSource]:
    sources: list[ChatSource] = []
    seen: set[tuple[str, int]] = set()
    for doc in docs:
        meta = doc.metadata or {}
        vid = str(meta.get("video_id", "?"))
        idx = int(meta.get("chunk_index", 0))
        key = (vid, idx)
        if key in seen:
            continue
        seen.add(key)
        snippet = doc.page_content[:240] + ("…" if len(doc.page_content) > 240 else "")
        sources.append(
            ChatSource(
                video_id=vid,
                chunk_index=idx,
                snippet=snippet,
                platform=meta.get("platform"),
            )
        )
    return sources


async def stream_chat(
    session_id: str,
    message: str,
    videos: list[VideoMetadata],
) -> AsyncIterator[str]:
    chain = _build_chain(session_id, videos)
    config = {"configurable": {"session_id": session_id}}

    full_answer = ""
    prev_len = 0
    source_docs: list[Document] = []

    # astream yields cumulative "answer" from the retrieval chain when LLM streams
    async for chunk in chain.astream({"input": message}, config=config):
        if isinstance(chunk, dict):
            if chunk.get("context"):
                source_docs = list(chunk["context"])
            answer = chunk.get("answer")
            if answer and isinstance(answer, str) and len(answer) > prev_len:
                delta = answer[prev_len:]
                prev_len = len(answer)
                full_answer = answer
                yield json.dumps({"type": "token", "content": delta}) + "\n"

    if not full_answer:
        # token-level fallback via events API
        async for event in chain.astream_events(
            {"input": message},
            config=config,
            version="v2",
        ):
            if event.get("event") == "on_chat_model_stream":
                piece = event.get("data", {}).get("chunk")
                if piece and getattr(piece, "content", None):
                    full_answer += piece.content
                    yield json.dumps({"type": "token", "content": piece.content}) + "\n"
            elif event.get("event") == "on_chain_end":
                output = event.get("data", {}).get("output") or {}
                if isinstance(output, dict) and output.get("context"):
                    source_docs = list(output["context"])

    _get_history(session_id).append(HumanMessage(content=message))
    _get_history(session_id).append(AIMessage(content=full_answer))

    sources = _docs_to_sources(source_docs)
    yield json.dumps({"type": "sources", "sources": [s.model_dump() for s in sources]}) + "\n"
    yield json.dumps({"type": "done"}) + "\n"


def chat_sync(session_id: str, message: str, videos: list[VideoMetadata]) -> tuple[str, list[ChatSource]]:
    chain = _build_chain(session_id, videos)
    config = {"configurable": {"session_id": session_id}}
    result = chain.invoke({"input": message}, config=config)
    answer = result.get("answer", "")
    context = result.get("context") or []
    sources = _docs_to_sources(context)
    _get_history(session_id).append(HumanMessage(content=message))
    _get_history(session_id).append(AIMessage(content=answer))
    return answer, sources
