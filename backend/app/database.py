from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    if settings.database_url.startswith("postgresql"):
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    from . import models

    Base.metadata.create_all(bind=engine)
    ensure_conversation_summary_column()


def ensure_conversation_summary_column():
    inspector = inspect(engine)
    if "conversations" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("conversations")}
    if "summary" in columns:
        return

    statement = "ALTER TABLE conversations ADD COLUMN summary TEXT"
    if settings.database_url.startswith("postgresql"):
        statement = "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS summary TEXT"

    with engine.begin() as conn:
        conn.execute(text(statement))
