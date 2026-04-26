"""모델 정보 라우터"""
from fastapi import APIRouter
from services.ai_service import get_available_models

router = APIRouter()

@router.get("/")
async def list_models():
    return get_available_models()
