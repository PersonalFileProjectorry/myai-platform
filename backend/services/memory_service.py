"""
자기학습 메모리 시스템
- ChromaDB: 벡터 검색 (의미 기반 기억)
- SQLite: 대화 이력 저장
- 자동 학습: 대화에서 지식 추출 및 저장
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# 전역 클라이언트
_chroma_client = None
_collection = None
_embedder = None


async def init_memory():
    """메모리 시스템 초기화"""
    global _chroma_client, _collection, _embedder

    try:
        chroma_url = os.getenv("CHROMA_URL", "http://chromadb:8001")
        host, port = chroma_url.replace("http://", "").split(":")

        _chroma_client = chromadb.HttpClient(
            host=host,
            port=int(port),
            settings=Settings(anonymized_telemetry=False)
        )

        # 컬렉션 생성 또는 가져오기
        _collection = _chroma_client.get_or_create_collection(
            name="myai_memory",
            metadata={"description": "MyAI 자기학습 메모리"}
        )

        # 임베딩 모델 (로컬, 무료)
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info(f"✅ 메모리 시스템 초기화 완료 (저장된 기억: {_collection.count()}개)")

    except Exception as e:
        logger.warning(f"⚠️ ChromaDB 연결 실패: {e} - 메모리 없이 실행")


async def save_conversation(
    session_id: str,
    user_msg: str,
    ai_msg: str,
    provider: str,
    model: str,
    rating: Optional[int] = None,
):
    """대화를 메모리에 저장 (자기학습의 핵심)"""
    if not _collection or not _embedder:
        return

    try:
        # 대화 쌍을 하나의 기억으로 저장
        memory_text = f"Q: {user_msg}\nA: {ai_msg}"
        embedding = _embedder.encode(memory_text).tolist()

        memory_id = str(uuid.uuid4())
        metadata = {
            "session_id": session_id,
            "provider": provider,
            "model": model,
            "timestamp": datetime.utcnow().isoformat(),
            "rating": rating or 0,
            "user_msg_preview": user_msg[:100],
        }

        _collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[memory_text],
            metadatas=[metadata],
        )

        # 높은 평점 대화는 파인튜닝 데이터셋으로 저장
        if rating and rating >= 4:
            await _save_to_finetune_dataset(user_msg, ai_msg, provider)

        logger.debug(f"💾 기억 저장: {memory_id[:8]}... (provider={provider})")

    except Exception as e:
        logger.error(f"메모리 저장 오류: {e}")


async def search_memory(query: str, n_results: int = 5, provider_filter: str = None) -> str:
    """쿼리와 유사한 과거 대화 검색 (RAG)"""
    if not _collection or not _embedder:
        return ""

    try:
        embedding = _embedder.encode(query).tolist()
        where = {"provider": provider_filter} if provider_filter else None

        results = _collection.query(
            query_embeddings=[embedding],
            n_results=min(n_results, max(_collection.count(), 1)),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        if not results["documents"][0]:
            return ""

        context_parts = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            if dist < 1.2:  # 유사도 임계값
                ts = meta.get("timestamp", "")[:10]
                pv = meta.get("provider", "")
                context_parts.append(f"[{ts} - {pv}]\n{doc}")

        return "\n\n".join(context_parts[:3]) if context_parts else ""

    except Exception as e:
        logger.error(f"메모리 검색 오류: {e}")
        return ""


async def get_memory_stats() -> dict:
    """메모리 통계"""
    if not _collection:
        return {"status": "offline", "count": 0}

    try:
        count = _collection.count()
        return {
            "status": "online",
            "total_memories": count,
            "embedding_model": "all-MiniLM-L6-v2",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def _save_to_finetune_dataset(user_msg: str, ai_msg: str, provider: str):
    """우수한 대화를 파인튜닝 데이터셋으로 저장"""
    dataset_path = "/data/sqlite/finetune_dataset.jsonl"
    os.makedirs(os.path.dirname(dataset_path), exist_ok=True)

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "provider": provider,
        "messages": [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": ai_msg},
        ],
    }

    with open(dataset_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
