"""
MyAI Platform - Backend Entry Point
개인용 AI 허브 백엔드 (Claude + Gemini + Ollama + GPT)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from routers import chat, models, memory, images, code, circuit, diagram
from services.database import init_db
from services.memory_service import init_memory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 실행"""
    logger.info("🚀 MyAI Platform 시작 중...")
    await init_db()
    await init_memory()
    logger.info("✅ 모든 서비스 초기화 완료")
    yield
    logger.info("🛑 MyAI Platform 종료")


app = FastAPI(
    title="MyAI Platform",
    description="개인용 AI 허브 - Claude, Gemini, Ollama 통합",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:80", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat.router,    prefix="/api/chat",    tags=["💬 채팅"])
app.include_router(models.router,  prefix="/api/models",  tags=["🤖 모델"])
app.include_router(memory.router,  prefix="/api/memory",  tags=["🧠 메모리"])
app.include_router(images.router,  prefix="/api/images",  tags=["🖼️ 이미지"])
app.include_router(code.router,    prefix="/api/code",    tags=["💻 코드실행"])
app.include_router(circuit.router, prefix="/api/circuit", tags=["🔌 회로설계"])

# 생성된 파일 서빙
os.makedirs("/data/generated", exist_ok=True)
app.mount("/generated", StaticFiles(directory="/data/generated"), name="generated")


@app.get("/")
async def root():
    return {
        "name": "MyAI Platform",
        "version": "1.0.0",
        "status": "running",
        "models": ["claude", "gemini", "ollama", "gpt (optional)"]
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
app.include_router(diagram.router, prefix="/api/diagram", tags=["📊 다이어그램"])