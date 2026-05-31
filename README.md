# Creator Compare — Full-Stack RAG (Technical Test)

Side-by-side **YouTube (Video A)** vs **Instagram Reel (Video B)** with dynamic metadata, transcript chunking, **ChromaDB** vectors, and a **LangChain** RAG chat that **streams** answers with **chunk citations** and **multi-turn memory**.

## What it does

1. Ingest two URLs (YouTube + Instagram — required).
2. Pull **transcript + metadata** (views, likes, comments, creator, followers, hashtags, date, duration) via **yt-dlp** + **youtube-transcript-api**.
3. Compute **engagement rate** = `(likes + comments) / views × 100`.
4. **Chunk** transcripts (800 chars / 120 overlap), **embed** with OpenAI `text-embedding-3-small`, store in **ChromaDB** with `video_id` ∈ `{A, B}` on every chunk.
5. Chat (LangChain history-aware retriever + stuff chain): compare engagement, hooks, creators, improvement ideas — **streaming NDJSON**, **sources**, **session memory**.

## Stack choices (and why)

| Layer | Choice | Reasoning |
|--------|--------|-----------|
| Frontend | Next.js 15 (React) | Fast dev, SSE-friendly fetch streaming, easy deploy to Vercel |
| Backend | FastAPI | Async streaming, typed APIs, low overhead |
| Orchestration | **LangChain** | Required; history-aware RAG + citation context out of the box |
| Embeddings | OpenAI `text-embedding-3-small` | Best cost/quality for short creator transcripts at scale |
| Vector DB | **ChromaDB** (local persist) | Zero hosted DB cost for screening; swap to Pinecone/Qdrant at ~1k creators/day with same metadata schema |
| LLM | `gpt-4o-mini` | ~20× cheaper than GPT-4o for analytics Q&A; upgrade path to 4o for complex reasoning |
| Transcripts | yt-dlp + youtube-transcript-api | No paid AssemblyAI needed for demo; IG falls back to description/title when captions missing |

### Scale / cost (@ ~1000 creators/day)

- **Ingest** is the expensive step (2 videos × embed once). Batch overnight, cache metadata + vectors keyed by `video_id` + content hash.
- **Chroma** on disk works for MVP; at 10k+ sessions use **Qdrant Cloud** or **Pinecone serverless** (~$50–150/mo) with namespaces per creator.
- **Embeddings**: ~2–6 chunks/video → ~4k embed calls/day → low tens of USD/day on small model; cache embeddings when transcript unchanged.
- **Chat**: stream `gpt-4o-mini`; cap `k=6` retrieval to control tokens; Redis for session memory when running >1 API replica.

**If I had to optimize further:** precompute engagement metrics in SQL/Postgres (no LLM), use RAG only for transcript/hook questions; route factual metrics questions to a structured tool.

## Quick start

### Prerequisites

- Python 3.11+
- Node 20+
- [OpenAI API key](https://platform.openai.com/api-keys)
- `ffmpeg` optional (yt-dlp uses it for some formats)

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# set OPENAI_API_KEY in .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Open http://localhost:3000 — paste a **real** YouTube URL and **Instagram Reel** URL, click **Ingest & index**, then use chat starters.

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/ingest` | `{ youtube_url, instagram_url }` |
| GET | `/api/session/{id}` | Session metadata |
| POST | `/api/chat/stream` | NDJSON stream: `token`, `sources`, `done` |
| POST | `/api/chat` | Non-streaming fallback |

## Project layout

```
backend/app/          FastAPI + LangChain + Chroma
frontend/             Next.js UI (cards + chat)
```

## Loom demo checklist

1. Fresh ingest with two public URLs (YT + IG).
2. Show cards: views, engagement %, creator, hashtags.
3. Ask all five sample questions — show streaming + citations.
4. Follow-up question to prove **memory**.
5. Explain cost/scaling trade-offs (see table above).

## Author

Varsha Pulikanti — technical screening submission.
