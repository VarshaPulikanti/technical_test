# Creator Compare — technical screening project

I built a full-stack RAG app that ingests **one YouTube video (A)** and **one Instagram Reel (B)**, pulls real metadata + transcripts, indexes chunks in **ChromaDB**, and lets a creator chat with **LangChain** over both — streaming answers, chunk citations, and multi-turn memory.

Repo: https://github.com/VarshaPulikanti/technical_test

## Requirements mapping

| Requirement | How it's done |
|-------------|----------------|
| YouTube + Instagram URLs | `/api/ingest` validates platform; A = YouTube, B = Instagram |
| Transcript + metadata | `yt-dlp` + `youtube-transcript-api`; IG captions via subtitle URLs when available |
| Engagement rate | `(likes + comments) / views × 100` computed on ingest |
| Chunk + embed + vector DB | LangChain splitter → OpenAI embeddings → **ChromaDB**, every chunk tagged `video_id` A or B |
| RAG chat | LangChain history-aware retriever + retrieval chain |
| Stream + cite + memory | `POST /api/chat/stream` (NDJSON); sources show video + chunk (+ hook flag); session history |
| Frontend | Next.js — two video cards + chat panel |

## Why this stack

- **FastAPI** — async streaming without much boilerplate.
- **LangChain** — required; history-aware retrieval + stuff chain is enough for this scope (LangGraph if we add tool-routing later).
- **ChromaDB (persisted)** — $0 for the demo; same metadata schema ports to Qdrant/Pinecone when we hit ~1k creators/day.
- **text-embedding-3-small** — cheap, good enough for short captions.
- **gpt-4o-mini** — analytics Q&A at ~20× lower cost than 4o; bump model only if answers get sloppy.

### At ~1000 creators/day

- **Cost driver** = ingest (2 embeds per creator per batch). Cache vectors + metadata by video URL hash so re-ingest is skipped.
- **~4k–12k embed calls/day** on small model → tens of USD/day, not hundreds, if we don't re-embed unchanged transcripts.
- **Chat** — cap retrieval `k=6`, stream mini model, store session history in **Redis** once we run multiple API replicas.
- **What I'd change at 10k+ creators:** managed Qdrant/Pinecone, Postgres for metrics (engagement doesn't need an LLM), queue workers for ingest (Celery/SQS).

## Run locally

**Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # add OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Open http://localhost:3000 → paste **real** YouTube + Instagram URLs → **Ingest & index** → use chat starters.

See [DEMO.md](./DEMO.md) for the Loom walkthrough.

## API

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/ingest` | `{ youtube_url, instagram_url }` |
| GET | `/api/session/{id}` | Cards data + chunk count |
| POST | `/api/chat/stream` | NDJSON: `token`, `sources`, `done` |

## Layout

```
backend/app/services/   ingestion, Chroma, LangChain RAG
frontend/               Next.js UI
```

## Env

Copy `backend/.env.example` → `backend/.env` and `frontend/.env.example` → `frontend/.env.local`.

---

Built by Varsha Pulikanti for the engineer technical screen.
