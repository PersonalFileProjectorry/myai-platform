"""
채팅 API 라우터
- SSE(Server-Sent Events)로 스트리밍 응답
- 자동 메모리 검색 + 저장
- 이미지 업로드 지원
"""

import uuid
import json
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from services.ai_service import route_to_model, get_available_models
from services.memory_service import save_conversation, search_memory
from services.database import get_db, Conversation, Session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/stream")
async def chat_stream(
    session_id: str      = Form(...),
    provider:   str      = Form(...),           # claude / gemini / ollama / gpt
    model:      str      = Form(...),
    message:    str      = Form(...),
    use_memory: bool     = Form(True),          # 자기학습 메모리 사용 여부
    image:      Optional[UploadFile] = File(None),
    db:         AsyncSession = Depends(get_db),
):
    """스트리밍 채팅 - SSE 방식"""

    # 이미지 읽기
    image_data = None
    if image:
        image_data = await image.read()

    # 세션의 이전 대화 불러오기
    result = await db.execute(
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .order_by(desc(Conversation.created_at))
        .limit(20)
    )
    history = list(reversed(result.scalars().all()))
    messages = [{"role": h.role, "content": h.content} for h in history]
    messages.append({"role": "user", "content": message})

    # 자기학습 메모리에서 관련 컨텍스트 검색
    context = ""
    if use_memory:
        context = await search_memory(message, n_results=3)

    # 유저 메시지 저장
    user_conv = Conversation(
        id=str(uuid.uuid4()),
        session_id=session_id,
        provider=provider,
        model=model,
        role="user",
        content=message,
    )
    db.add(user_conv)
    await db.commit()

    async def generate():
        full_response = []

        try:
            async for chunk in route_to_model(provider, messages, model, context, image_data):
                full_response.append(chunk)
                # SSE 형식
                data = json.dumps({"type": "chunk", "content": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"

        except Exception as e:
            logger.error(f"스트리밍 오류: {e}")
            err_data = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {err_data}\n\n"

        finally:
            # AI 응답 저장
            ai_text = "".join(full_response)
            if ai_text:
                ai_conv = Conversation(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    provider=provider,
                    model=model,
                    role="assistant",
                    content=ai_text,
                )
                async with db.begin():
                    db.add(ai_conv)

                # 자기학습 메모리에 저장
                await save_conversation(session_id, message, ai_text, provider, model)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/sessions")
async def get_sessions(db: AsyncSession = Depends(get_db)):
    """세션 목록"""
    result = await db.execute(
        select(Session).order_by(desc(Session.updated_at)).limit(50)
    )
    sessions = result.scalars().all()
    return [{"id": s.id, "title": s.title, "provider": s.provider,
             "model": s.model, "created_at": str(s.created_at)} for s in sessions]


@router.post("/sessions")
async def create_session(
    provider: str,
    model: str,
    title: str = "새 대화",
    db: AsyncSession = Depends(get_db),
):
    """새 세션 생성"""
    session = Session(
        id=str(uuid.uuid4()),
        title=title,
        provider=provider,
        model=model,
    )
    db.add(session)
    await db.commit()
    return {"id": session.id, "title": session.title}


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    """세션의 대화 이력"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .order_by(Conversation.created_at)
    )
    convs = result.scalars().all()
    return [{"role": c.role, "content": c.content,
             "provider": c.provider, "model": c.model,
             "created_at": str(c.created_at)} for c in convs]


@router.post("/sessions/{conv_id}/rate")
async def rate_message(conv_id: str, rating: int, db: AsyncSession = Depends(get_db)):
    """메시지 평점 (자기학습에 사용)"""
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if conv:
        conv.rating = rating
        await db.commit()
    return {"status": "ok"}
