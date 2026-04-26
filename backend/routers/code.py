"""
코드 실행 라우터 - Docker 샌드박스
Python, JavaScript, C/C++, Rust, Arduino 지원
"""

import asyncio
import tempfile
import os
import logging
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

TIMEOUT = 15  # 초


class CodeRequest(BaseModel):
    code:     str
    language: str = "python"


LANGUAGE_CONFIG = {
    "python":     {"image": "python:3.11-slim",   "cmd": "python /code/main.py",          "ext": "py"},
    "javascript": {"image": "node:20-slim",        "cmd": "node /code/main.js",            "ext": "js"},
    "typescript": {"image": "node:20-slim",        "cmd": "npx ts-node /code/main.ts",    "ext": "ts"},
    "c":          {"image": "gcc:latest",          "cmd": "gcc /code/main.c -o /code/a && /code/a", "ext": "c"},
    "cpp":        {"image": "gcc:latest",          "cmd": "g++ /code/main.cpp -o /code/a && /code/a", "ext": "cpp"},
    "rust":       {"image": "rust:slim",           "cmd": "cd /code && rustc main.rs -o a && ./a", "ext": "rs"},
    "bash":       {"image": "bash:latest",         "cmd": "bash /code/main.sh",            "ext": "sh"},
}


@router.post("/run")
async def run_code(req: CodeRequest):
    """코드를 Docker 샌드박스에서 안전하게 실행"""
    lang = req.language.lower()
    config = LANGUAGE_CONFIG.get(lang)

    if not config:
        return {
            "error": f"지원하지 않는 언어: {lang}",
            "supported": list(LANGUAGE_CONFIG.keys())
        }

    with tempfile.TemporaryDirectory() as tmpdir:
        # 코드 파일 저장
        code_file = os.path.join(tmpdir, f"main.{config['ext']}")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(req.code)

        # Docker 실행 (네트워크 차단, 메모리 제한)
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "256m",
            "--cpus", "0.5",
            "--read-only",
            "--tmpfs", "/tmp:size=64m",
            "-v", f"{tmpdir}:/code:ro",
            config["image"],
            "sh", "-c", config["cmd"],
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=TIMEOUT
            )

            return {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "return_code": proc.returncode,
                "language": lang,
            }

        except asyncio.TimeoutError:
            proc.kill()
            return {"error": f"⏱️ 실행 시간 초과 ({TIMEOUT}초)", "language": lang}
        except FileNotFoundError:
            # Docker가 없으면 직접 Python 실행 (Python만)
            if lang == "python":
                return await _run_python_direct(req.code)
            return {"error": "Docker가 설치되지 않았습니다."}


async def _run_python_direct(code: str) -> dict:
    """Docker 없을 때 Python 직접 실행 (fallback)"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        fname = f.name

    try:
        proc = await asyncio.create_subprocess_exec(
            "python", fname,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "return_code": proc.returncode,
            "language": "python",
            "note": "Docker 없이 직접 실행됨"
        }
    except asyncio.TimeoutError:
        return {"error": "⏱️ 실행 시간 초과"}
    finally:
        os.unlink(fname)
