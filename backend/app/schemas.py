from pydantic import BaseModel, EmailStr


class AuthIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ConversationOut(BaseModel):
    id: int
    title: str
    summary: str | None = None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str


class ChatIn(BaseModel):
    message: str
    conversation_id: int | None = None
    use_web: bool = False
    use_rag: bool = True


class ChatOut(BaseModel):
    conversation_id: int
    answer: str
    title: str
    summary: str | None = None


class MemoryIn(BaseModel):
    content: str
