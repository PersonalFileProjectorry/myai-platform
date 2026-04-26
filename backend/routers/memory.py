"""메모리/자기학습 라우터"""
from fastapi import APIRouter
from services.memory_service import get_memory_stats, search_memory

router = APIRouter()

@router.get("/stats")
async def memory_stats():
    return await get_memory_stats()

@router.get("/search")
async def memory_search(q: str, n: int = 5):
    results = await search_memory(q, n_results=n)
    return {"query": q, "results": results}
