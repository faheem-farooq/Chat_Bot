# Learning Chatbot

A small full-stack chatbot for studying the moving parts:

- Next.js + React frontend
- FastAPI backend
- PostgreSQL with `pgvector`
- Login with JWT
- Chat history
- Manual memory
- RAG over uploaded `.txt`, `.md`, or `.csv` files
- Optional web search using DuckDuckGo instant answers
- Browser voice input
- Image analysis through a Groq vision model

## Run with Docker

```bash
cp .env.example .env
# edit .env and add your Groq key
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs

## Deploy on Vercel

Recommended: deploy the frontend to Vercel and the FastAPI backend to a separate service (Render, Railway, Fly, or a Docker host). Vercel works best when the project root is the Next.js app.

Options:

- Fast: Set the Vercel Project Root to `frontend` (Project Settings → General → Root Directory) and let Vercel detect the Next.js app. No `vercel.json` change required.
- Alternative (monorepo routing): this repo includes a simple `vercel.json` that builds the `frontend` folder directly. If you prefer this, keep the repo-level `vercel.json`.

Environment variables you will need on Vercel or your backend host:

```bash
GROQ_API_KEY=your_groq_key
JWT_SECRET=use-a-long-random-secret
DATABASE_URL=postgresql+psycopg://user:password@host:5432/database
CORS_ORIGIN=https://your-vercel-domain.vercel.app
```

Notes:

- The backend should be reachable from the frontend via `NEXT_PUBLIC_API_URL` if it is deployed to another host. Example: `NEXT_PUBLIC_API_URL=https://my-backend.example.com`.
- For production use a hosted PostgreSQL (Neon/Supabase/Vercel Postgres). The local SQLite fallback is only for learning.

## Run locally

For the simplest local learning run, the backend uses `backend/dev.db` SQLite by default. Docker still uses PostgreSQL with `pgvector`.

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
# edit backend/.env and add GROQ_API_KEY
uvicorn app.main:app --reload
```

If you want local PostgreSQL instead of SQLite, set this in `backend/.env`:

```bash
DATABASE_URL=postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Where to study each concept

- Auth: `backend/app/auth.py` and auth routes in `backend/app/main.py`
- Database models: `backend/app/models.py`
- RAG chunking and embeddings: `backend/app/rag.py`
- Groq calls: `backend/app/groq.py`
- Web search: `backend/app/web_search.py`
- Frontend API calls: `frontend/lib/api.ts`
- Main UI: `frontend/app/page.tsx`

## Notes

The RAG embeddings are intentionally simple hash embeddings. They are not state-of-the-art, but they keep the project cheap, local, and easy to understand. Later, you can swap `embed_text()` for a real embedding model without changing the rest of the RAG flow.
