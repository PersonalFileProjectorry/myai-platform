"""SQLite 데이터베이스 - 대화 이력, 세션 관리"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, String, Text, Integer, DateTime, Float
from sqlalchemy.sql import func
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:////data/sqlite/myai.db")
# sqlite:// → sqlite+aiosqlite://
if DATABASE_URL.startswith("sqlite:///"):
    DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

os.makedirs("/data/sqlite", exist_ok=True)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    id          = Column(String, primary_key=True)
    session_id  = Column(String, index=True)
    provider    = Column(String)          # claude / gemini / ollama / gpt
    model       = Column(String)
    role        = Column(String)          # user / assistant
    content     = Column(Text)
    rating      = Column(Integer, default=0)
    created_at  = Column(DateTime, server_default=func.now())


class Session(Base):
    __tablename__ = "sessions"

    id          = Column(String, primary_key=True)
    title       = Column(String, default="새 대화")
    provider    = Column(String)
    model       = Column(String)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())


async def init_db():
    """테이블 생성"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ 데이터베이스 초기화 완료")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
