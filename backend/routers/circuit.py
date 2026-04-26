"""
회로기판 설계 라우터
- AI로 회로 설명 → KiCad 넷리스트 생성
- 회로도 이미지 분석
- 부품 추천 및 SPICE 시뮬레이션 스크립트 생성
"""

import os
import uuid
import json
import base64
import logging
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)
OUTPUT_DIR = "/data/generated/circuits"
os.makedirs(OUTPUT_DIR, exist_ok=True)


class CircuitRequest(BaseModel):
    description: str           # 자연어 회로 설명
    circuit_type: str = "general"  # general / amplifier / power / mcu / sensor


CIRCUIT_SYSTEM_PROMPT = """당신은 전문 전자공학자이자 회로 설계 전문가입니다.
KiCad, Eagle, Altium Designer에 익숙하며 아날로그/디지털 회로, 전원 설계, 
임베디드 시스템, PCB 레이아웃에 전문 지식을 갖고 있습니다.

회로 설명을 받으면 다음을 제공하세요:
1. 회로 개요 및 동작 원리
2. 필요 부품 목록 (부품명, 값, 패키지)
3. KiCad 호환 넷리스트 (Spice 형식)
4. PCB 레이아웃 주의사항
5. 테스트 방법

넷리스트는 반드시 ```netlist ... ``` 코드 블록으로 감싸주세요."""


@router.post("/design")
async def design_circuit(req: CircuitRequest):
    """자연어 설명으로 회로 설계"""
    from services.ai_service import _claude_client, _gemini_model

    prompt = f"""다음 회로를 설계해주세요:

회로 타입: {req.circuit_type}
설명: {req.description}

전문적인 회로 설계 문서를 작성해주세요."""

    # Claude 우선, 없으면 Gemini
    result_text = ""

    if _claude_client:
        response = await _claude_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            system=CIRCUIT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        result_text = response.content[0].text
    elif _gemini_model:
        import google.generativeai as genai
        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction=CIRCUIT_SYSTEM_PROMPT
        )
        response = await model.generate_content_async(prompt)
        result_text = response.text
    else:
        return JSONResponse(status_code=400, content={"error": "AI API 키가 필요합니다."})

    # 넷리스트 추출
    netlist = _extract_netlist(result_text)
    netlist_file = None

    if netlist:
        filename = f"circuit_{uuid.uuid4()}.net"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w") as f:
            f.write(netlist)
        netlist_file = f"/generated/circuits/{filename}"

    return {
        "design": result_text,
        "netlist_file": netlist_file,
        "circuit_type": req.circuit_type,
    }


@router.post("/analyze-image")
async def analyze_circuit_image(image: UploadFile = File(...)):
    """회로도 이미지 분석"""
    from services.ai_service import _claude_client

    if not _claude_client:
        return JSONResponse(status_code=400, content={"error": "Claude API 키 필요"})

    image_data = await image.read()
    img_b64 = base64.b64encode(image_data).decode()

    response = await _claude_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=CIRCUIT_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": image.content_type, "data": img_b64}
                },
                {
                    "type": "text",
                    "text": """이 회로도를 분석해주세요:
1. 회로의 목적과 기능
2. 주요 부품 목록
3. 신호 흐름
4. 잠재적 문제점 또는 개선 사항
5. 이 회로의 넷리스트 (가능하면)"""
                }
            ]
        }]
    )

    return {"analysis": response.content[0].text}


@router.get("/components/suggest")
async def suggest_components(
    function: str,
    voltage: float = 5.0,
    current_ma: float = 100.0
):
    """기능 기반 부품 추천"""
    from services.ai_service import _claude_client

    if not _claude_client:
        return JSONResponse(status_code=400, content={"error": "Claude API 키 필요"})

    prompt = f"""다음 조건에 맞는 전자 부품을 추천해주세요:
- 기능: {function}
- 동작 전압: {voltage}V
- 최대 전류: {current_ma}mA

추천 부품을 JSON 형식으로 제공해주세요:
{{
  "primary": [부품 목록],
  "alternatives": [대안 부품],
  "notes": "주의사항"
}}"""

    response = await _claude_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        text = response.content[0].text
        # JSON 추출 시도
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass

    return {"raw": response.content[0].text}


def _extract_netlist(text: str) -> str:
    """텍스트에서 넷리스트 추출"""
    import re
    match = re.search(r'```netlist\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    # SPICE 형식 시도
    match = re.search(r'```spice\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    return ""
