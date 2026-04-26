"""
이미지 생성 + 처리 라우터
- Stability AI API (선택, 무료 크레딧)
- 로컬 Stable Diffusion (AUTOMATIC1111 WebUI)
- 이미지 분석 (Claude Vision / Gemini Vision)
"""

import os
import uuid
import base64
import logging
import httpx
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger(__name__)

STABILITY_KEY = os.getenv("STABILITY_API_KEY", "")
SD_WEBUI_URL  = os.getenv("SD_WEBUI_URL", "http://host.docker.internal:7860")  # A1111 로컬
OUTPUT_DIR    = "/data/generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.post("/generate")
async def generate_image(
    prompt:          str = Form(...),
    negative_prompt: str = Form(""),
    width:           int = Form(1024),
    height:          int = Form(1024),
    steps:           int = Form(20),
    backend:         str = Form("auto"),  # auto / stability / sdwebui
):
    """이미지 생성 (Stability AI 또는 로컬 SD)"""

    # 백엔드 자동 선택
    if backend == "auto":
        backend = "stability" if STABILITY_KEY else "sdwebui"

    if backend == "stability" and STABILITY_KEY:
        return await _generate_stability(prompt, negative_prompt, width, height, steps)
    elif backend == "sdwebui":
        return await _generate_sdwebui(prompt, negative_prompt, width, height, steps)
    else:
        return JSONResponse(
            status_code=400,
            content={
                "error": "이미지 생성 백엔드가 설정되지 않았습니다.",
                "hint": "STABILITY_API_KEY를 설정하거나 AUTOMATIC1111 WebUI를 실행하세요.",
                "sd_install": "https://github.com/AUTOMATIC1111/stable-diffusion-webui",
            }
        )


async def _generate_stability(prompt, negative_prompt, width, height, steps):
    """Stability AI API로 생성"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={"authorization": f"Bearer {STABILITY_KEY}", "accept": "image/*"},
            data={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "output_format": "png",
            },
            timeout=60,
        )

    if response.status_code != 200:
        return JSONResponse(status_code=500, content={"error": response.text})

    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(response.content)

    return {"url": f"/generated/{filename}", "backend": "stability"}


async def _generate_sdwebui(prompt, negative_prompt, width, height, steps):
    """로컬 AUTOMATIC1111 WebUI로 생성"""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{SD_WEBUI_URL}/sdapi/v1/txt2img",
                json={
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg_scale": 7,
                },
            )

        data = response.json()
        img_b64 = data["images"][0]
        img_bytes = base64.b64decode(img_b64)

        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(img_bytes)

        return {"url": f"/generated/{filename}", "backend": "sdwebui"}

    except httpx.ConnectError:
        return JSONResponse(
            status_code=503,
            content={
                "error": "AUTOMATIC1111 WebUI에 연결할 수 없습니다.",
                "hint": "SD WebUI를 --api 옵션으로 실행하세요: python webui.py --api",
            }
        )


@router.post("/analyze")
async def analyze_image(image: UploadFile = File(...)):
    """이미지 분석 (Claude Vision 사용)"""
    image_data = await image.read()
    img_b64 = base64.b64encode(image_data).decode()

    from services.ai_service import _claude_client
    if not _claude_client:
        return JSONResponse(status_code=400, content={"error": "Claude API 키 필요"})

    response = await _claude_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": image.content_type, "data": img_b64}
                },
                {
                    "type": "text",
                    "text": "이 이미지를 분석해주세요. 회로기판이라면 부품과 연결을 설명하고, 코드라면 내용을 설명해주세요."
                }
            ]
        }]
    )
    return {"analysis": response.content[0].text}
