"""
AI 모델 서비스 - Claude / Gemini / Ollama / GPT 통합 라우터
각 모델을 독립적으로 관리하며 충돌 없이 병렬 사용 가능
"""

import os
import asyncio
import logging
from typing import AsyncGenerator, Optional
from enum import Enum

import anthropic
import google.generativeai as genai
import ollama as ollama_client
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    CLAUDE  = "claude"
    GEMINI  = "gemini"
    OLLAMA  = "ollama"
    GPT     = "gpt"        # 선택 (API 키 있을 때만)


# ── 클라이언트 초기화 ─────────────────────────────────────────

def _init_claude():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if key:
        return anthropic.AsyncAnthropic(api_key=key)
    return None

def _init_gemini():
    key = os.getenv("GEMINI_API_KEY", "")
    if key:
        genai.configure(api_key=key)
        return genai.GenerativeModel("gemini-2.0-flash")
    return None

def _init_gpt():
    key = os.getenv("OPENAI_API_KEY", "")
    if key:
        return AsyncOpenAI(api_key=key)
    return None

_claude_client  = _init_claude()
_gemini_model   = _init_gemini()
_gpt_client     = _init_gpt()
_ollama_url     = os.getenv("OLLAMA_URL", "http://ollama:11434")


# ── 모델 가용성 확인 ─────────────────────────────────────────

def get_available_models() -> dict:
    """현재 사용 가능한 모델 목록 반환"""
    available = {}

    if _claude_client:
        available["claude"] = {
            "name": "Claude (Anthropic)",
            "models": ["claude-sonnet-4-5", "claude-haiku-4-5"],
            "features": ["코딩", "분석", "회로설계", "이미지인식"],
            "status": "active"
        }

    if _gemini_model:
        available["gemini"] = {
            "name": "Gemini (Google)",
            "models": ["gemini-2.0-flash", "gemini-1.5-pro"],
            "features": ["검색", "멀티모달", "번역"],
            "status": "active"
        }

    if _gpt_client:
        available["gpt"] = {
            "name": "GPT (OpenAI)",
            "models": ["gpt-4o-mini", "gpt-4o"],
            "features": ["범용", "코딩"],
            "status": "active"
        }

    # Ollama 로컬 모델 (항상 포함 시도)
    try:
        import httpx
        resp = httpx.get(f"{_ollama_url}/api/tags", timeout=3)
        if resp.status_code == 200:
            local_models = [m["name"] for m in resp.json().get("models", [])]
            available["ollama"] = {
                "name": "Ollama (로컬 - 무료)",
                "models": local_models if local_models else ["llama3:8b", "mistral:7b"],
                "features": ["완전무료", "프라이버시", "오프라인"],
                "status": "active" if local_models else "no_models"
            }
    except Exception:
        available["ollama"] = {
            "name": "Ollama (로컬 - 무료)",
            "models": [],
            "features": ["완전무료", "프라이버시", "오프라인"],
            "status": "offline"
        }

    return available


# ── 공통 메시지 구조 ─────────────────────────────────────────

def _build_system_prompt(provider: str, extra_context: str = "") -> str:
    """각 모델에 맞는 시스템 프롬프트 생성"""
    base = """당신은 MyAI Platform의 전문 AI 어시스턴트입니다.
반드시 한국어로만 답변하세요. 영어 질문도 무조건 한국어로 답변하세요.

## 핵심 전문 분야
1. **전자회로 설계**: KiCad, Eagle, Altium - 회로도 분석, 넷리스트 생성, 부품 추천
2. **PCB 설계**: 레이어 구성, 부품 배치, 라우팅, DRC 규칙, 임피던스 매칭
3. **임베디드 시스템**: Arduino, STM32, ESP32, Raspberry Pi 펌웨어
4. **코딩**: Python, C/C++, JavaScript, VHDL, Verilog 완벽 지원
5. **블록 다이어그램**: Node-RED, Simulink, 시스템 아키텍처 분석
6. **SPICE 시뮬레이션**: LTspice, ngspice 회로 시뮬레이션

## 이미지 분석 시
- PCB 이미지: 부품 식별, 레이어 분석, 연결 추적
- 회로도: 동작 원리, 부품값, 개선점 제안
- 블록 다이어그램: 데이터 흐름, 로직 분석, 최적화 제안
- 코드 스크린샷: 버그 찾기, 리팩토링, 성능 개선

항상 구체적인 코드와 회로 예시를 제공하세요."""

    if extra_context:
        base += f"\n\n[관련 기억/컨텍스트]\n{extra_context}"
    base += """

## 다이어그램 생성 규칙
회로도나 Node-RED 블록도 요청시 반드시 아래 JSON 형식을 답변 안에 포함하세요.

Node-RED 예시:
````json
{
  "type": "nodered",
  "title": "온도 모니터링",
  "nodes": [
    {"id":"1","name":"온도센서","type":"inject","x":0,"y":0},
    {"id":"2","name":"데이터처리","type":"function","x":2.5,"y":0},
    {"id":"3","name":"MQTT전송","type":"mqtt out","x":5,"y":0}
  ],
  "connections": [
    {"from":"1","to":"2"},
    {"from":"2","to":"3"}
  ]
}
````

회로도 예시:
````json
{
  "type": "circuit",
  "title": "LED 제어회로",
  "components": [
    {"id":"VCC","type":"power","value":"5V","x":1,"y":5},
    {"id":"R1","type":"resistor","value":"330Ω","x":3,"y":5},
    {"id":"LED1","type":"led","value":"적색","x":5,"y":5},
    {"id":"GND","type":"ground","value":"0V","x":7,"y":5}
  ],
  "connections": [
    {"from":"VCC","to":"R1"},
    {"from":"R1","to":"LED1"},
    {"from":"LED1","to":"GND"}
  ]
}
```"""

    return base


# ── Claude 스트리밍 ──────────────────────────────────────────

async def stream_claude(
    messages: list[dict],
    model: str = "claude-sonnet-4-5",
    context: str = "",
    image_data: Optional[bytes] = None,
) -> AsyncGenerator[str, None]:
    if not _claude_client:
        yield "❌ Claude API 키가 설정되지 않았습니다."
        return

    # 이미지가 있으면 마지막 메시지에 추가
    api_messages = messages.copy()
    if image_data and api_messages:
        import base64
        last = api_messages[-1]
        if last["role"] == "user":
            api_messages[-1] = {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64.b64encode(image_data).decode()
                        }
                    },
                    {"type": "text", "text": last.get("content", "")}
                ]
            }

    try:
        async with _claude_client.messages.stream(
            model=model,
            max_tokens=4096,
            system=_build_system_prompt("claude", context),
            messages=api_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception as e:
        logger.error(f"Claude 오류: {e}")
        yield f"\n❌ Claude 오류: {str(e)}"


# ── Gemini 스트리밍 ──────────────────────────────────────────

async def stream_gemini(
    messages: list[dict],
    model: str = "gemini-2.0-flash",
    context: str = "",
    image_data: Optional[bytes] = None,
) -> AsyncGenerator[str, None]:
    if not _gemini_model:
        yield "❌ Gemini API 키가 설정되지 않았습니다."
        return

    try:
        gemini = genai.GenerativeModel(
            model,
            system_instruction=_build_system_prompt("gemini", context)
        )

        # 대화 히스토리 변환
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        chat = gemini.start_chat(history=history)

        # 마지막 메시지 (이미지 포함 가능)
        last_content = messages[-1]["content"] if messages else ""
        parts = []

        if image_data:
            import PIL.Image
            import io
            img = PIL.Image.open(io.BytesIO(image_data))
            parts.append(img)

        parts.append(last_content)

        response = await chat.send_message_async(parts, stream=True)
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        logger.error(f"Gemini 오류: {e}")
        yield f"\n❌ Gemini 오류: {str(e)}"


# ── Ollama 스트리밍 (로컬, 완전 무료) ───────────────────────

async def stream_ollama(
    messages: list[dict],
    model: str = "llama3:8b",
    context: str = "",
) -> AsyncGenerator[str, None]:
    try:
        system_msg = {"role": "system", "content": _build_system_prompt("ollama", context)}
        full_messages = [system_msg] + messages

        client = ollama_client.AsyncClient(host=_ollama_url)
        async for chunk in await client.chat(
            model=model,
            messages=full_messages,
            stream=True
        ):
            if chunk.get("message", {}).get("content"):
                yield chunk["message"]["content"]

    except ollama_client.ResponseError as e:
        if "model" in str(e).lower():
            yield f"⚠️ 모델 '{model}'이 없습니다. 아래 명령어로 다운로드하세요:\n```\ndocker exec myai-ollama ollama pull {model}\n```"
        else:
            yield f"❌ Ollama 오류: {str(e)}"
    except Exception as e:
        logger.error(f"Ollama 오류: {e}")
        yield f"❌ Ollama 연결 오류: {str(e)}"


# ── GPT 스트리밍 (선택) ──────────────────────────────────────

async def stream_gpt(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    context: str = "",
    image_data: Optional[bytes] = None,
) -> AsyncGenerator[str, None]:
    if not _gpt_client:
        yield "⚠️ OpenAI API 키가 없습니다. .env 파일에 OPENAI_API_KEY를 추가하세요."
        return

    try:
        system_msg = {"role": "system", "content": _build_system_prompt("gpt", context)}
        api_messages = [system_msg] + messages

        if image_data:
            import base64
            last = api_messages[-1]
            if last["role"] == "user":
                api_messages[-1] = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": last.get("content", "")},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(image_data).decode()}"
                            }
                        }
                    ]
                }

        stream = await _gpt_client.chat.completions.create(
            model=model,
            messages=api_messages,
            stream=True,
            max_tokens=4096,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        logger.error(f"GPT 오류: {e}")
        yield f"❌ GPT 오류: {str(e)}"


# ── 통합 라우터 ──────────────────────────────────────────────

async def route_to_model(
    provider: str,
    messages: list[dict],
    model: str,
    context: str = "",
    image_data: Optional[bytes] = None,
) -> AsyncGenerator[str, None]:
    """provider 이름에 따라 적절한 모델로 라우팅"""
    if provider == "claude":
        async for chunk in stream_claude(messages, model, context, image_data):
            yield chunk
    elif provider == "gemini":
        async for chunk in stream_gemini(messages, model, context, image_data):
            yield chunk
    elif provider == "ollama":
        async for chunk in stream_ollama(messages, model, context):
            yield chunk
    elif provider == "gpt":
        async for chunk in stream_gpt(messages, model, context, image_data):
            yield chunk
    else:
        yield f"❌ 알 수 없는 모델: {provider}"
