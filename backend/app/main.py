import json

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import create_token, current_user, hash_password, verify_password
from .config import settings
from .database import get_db, init_db
from .groq import analyze_image, chat_completion
from .models import Conversation, Memory, Message, User
from .rag import add_document, search_documents
from .schemas import AuthIn, ChatIn, ChatOut, ConversationOut, MemoryIn, MessageOut, TokenOut
from .web_search import web_search


app = FastAPI(title="Learning Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/auth/register", response_model=TokenOut)
def register(data: AuthIn, db: Session = Depends(get_db)):
    exists = db.scalar(select(User).where(User.email == data.email))
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_token(user.id))


@app.post("/auth/login", response_model=TokenOut)
def login(data: AuthIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return TokenOut(access_token=create_token(user.id))


@app.get("/conversations", response_model=list[ConversationOut])
def conversations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    stmt = select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.id.desc())
    return list(db.scalars(stmt))


@app.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def messages(conversation_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if not conversation or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
    return list(db.scalars(stmt))


@app.get("/memories", response_model=list[str])
def memories(user: User = Depends(current_user), db: Session = Depends(get_db)):
    stmt = select(Memory.content).where(Memory.user_id == user.id).order_by(Memory.id.desc())
    return list(db.scalars(stmt))


@app.post("/memories")
def add_memory(data: MemoryIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.add(Memory(user_id=user.id, content=data.content))
    db.commit()
    return {"ok": True}


@app.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    text = raw.decode("utf-8", errors="ignore")
    count = add_document(db, user.id, file.filename or "uploaded.txt", text)
    return {"chunks_added": count}


@app.post("/chat", response_model=ChatOut)
async def chat(data: ChatIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conversation = db.get(Conversation, data.conversation_id) if data.conversation_id else None
    if conversation and conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not conversation:
        conversation = Conversation(user_id=user.id, title=data.message[:80] or "New chat")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    db.add(Message(conversation_id=conversation.id, role="user", content=data.message))
    db.commit()

    memory_text = "\n".join(
        db.scalars(select(Memory.content).where(Memory.user_id == user.id).order_by(Memory.id.desc()).limit(8))
    )
    recent = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.id.desc())
            .limit(10)
        )
    )
    recent.reverse()

    rag_chunks = search_documents(db, user.id, data.message) if data.use_rag else []
    web_snippets = await web_search(data.message) if data.use_web else []

    system = (
        "You are a helpful learning-project chatbot. Answer clearly and cite whether you used memory, "
        "documents, or web snippets when relevant.\n\n"
        f"Saved user memory:\n{memory_text or 'None'}\n\n"
        f"RAG document snippets:\n{format_chunks(rag_chunks)}\n\n"
        f"Web snippets:\n{format_snippets(web_snippets)}"
    )
    messages_for_llm = [{"role": "system", "content": system}]
    messages_for_llm += [{"role": msg.role, "content": msg.content} for msg in recent]

    answer = await chat_completion(messages_for_llm)
    db.add(
        Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            used_web=data.use_web,
            used_rag=bool(rag_chunks),
        )
    )
    db.commit()

    await update_conversation_summary(db, conversation)
    return ChatOut(
        conversation_id=conversation.id,
        answer=answer,
        title=conversation.title,
        summary=conversation.summary,
    )


@app.post("/image")
async def image(
    prompt: str = Form("Describe this image and answer any visible question."),
    file: UploadFile = File(...),
    user: User = Depends(current_user),
):
    content = await file.read()
    answer = await analyze_image(content, file.content_type or "image/png", prompt)
    return {"answer": answer}


def format_chunks(chunks) -> str:
    if not chunks:
        return "None"
    return "\n".join(f"- {chunk.source_name}: {chunk.content}" for chunk in chunks)


def format_snippets(snippets: list[str]) -> str:
    if not snippets:
        return "None"
    return "\n".join(f"- {snippet}" for snippet in snippets)


async def update_conversation_summary(db: Session, conversation: Conversation) -> None:
    messages = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.id)
            .limit(12)
        )
    )
    transcript = "\n".join(f"{message.role}: {message.content}" for message in messages)
    prompt = (
        "Create metadata for this chat. Return only JSON with keys title and summary. "
        "title must be 4 to 7 words. summary must be one short sentence.\n\n"
        f"{transcript}"
    )
    try:
        raw = await chat_completion(
            [
                {"role": "system", "content": "You summarize chats into compact JSON metadata."},
                {"role": "user", "content": prompt},
            ]
        )
        data = json.loads(raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```"))
        conversation.title = str(data.get("title") or conversation.title)[:120]
        conversation.summary = str(data.get("summary") or "")[:300] or None
        db.commit()
        db.refresh(conversation)
    except Exception:
        db.rollback()
