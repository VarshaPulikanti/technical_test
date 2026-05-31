# Loom demo script (fresh run — ~8–12 min)

Do this **live** on the call too — not a recording from an old session.

## Before recording

1. Turn off Cursor **Commit Attribution** and **PR Attribution** (Settings → Attribution).
2. `OPENAI_API_KEY` in `backend/.env`.
3. Pick two **public** URLs you tested in the last hour:
   - YouTube (Video A)
   - Instagram Reel (Video B)
4. Backend on `:8000`, frontend on `:3000`.

## On camera

1. **Ingest** — paste URLs, click ingest. Point at cards: views, likes, comments, **engagement %**, creator, followers, hashtags, duration, hook preview.
2. Ask the five required questions (use starter buttons). Show **streaming** text and **citations** (Video A/B + chunk).
3. **Memory** — ask: “Summarize what you already told me about Video B’s creator.”
4. **Cost / scale** (talk, don’t read):
   - Ingest + embed once per video; cache by URL hash.
   - Chroma local for demo → Qdrant/Pinecone at ~1k creators/day.
   - `text-embedding-3-small` + `gpt-4o-mini` for cost; 4o only if quality drops.
   - Chunk size 800 / overlap 120 — tuned for short-form captions.
5. What breaks at 10k users: in-memory chat history → Redis; single API box → horizontal workers + shared vector DB.

## Submission reply

```
1. Project URL: [deployed or http://localhost:3000]
2. Project Description: [2–3 sentences]
3. Loom URL: [link]
4. Github repo: https://github.com/VarshaPulikanti/technical_test
```
