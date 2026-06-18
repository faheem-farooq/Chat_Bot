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
