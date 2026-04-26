#!/bin/bash
# ============================================================
#  MyAI Platform - 초기 설정 스크립트
#  RTX 4070 Super 최적화
# ============================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║       MyAI Platform - 초기 설정          ║"
echo "║   Claude · Gemini · Ollama · GPT Hub     ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── 필수 도구 확인 ────────────────────────────────────────────
echo -e "${CYAN}[1/6] 필수 도구 확인...${NC}"

check_cmd() {
    if ! command -v "$1" &>/dev/null; then
        echo -e "${RED}✗ $1 이(가) 없습니다.${NC}"
        echo "  설치: $2"
        exit 1
    fi
    echo -e "${GREEN}✓ $1${NC}"
}

check_cmd docker  "https://docs.docker.com/get-docker/"
check_cmd "docker compose" "Docker Desktop 또는 docker-compose 설치"

# NVIDIA GPU 확인
if command -v nvidia-smi &>/dev/null; then
    GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
    echo -e "${GREEN}✓ GPU 감지: $GPU${NC}"
    NVIDIA_SUPPORT=true
else
    echo -e "${YELLOW}⚠ NVIDIA GPU를 찾을 수 없습니다. CPU 모드로 실행합니다.${NC}"
    NVIDIA_SUPPORT=false
fi

# ── 환경 변수 설정 ────────────────────────────────────────────
echo ""
echo -e "${CYAN}[2/6] 환경 변수 설정...${NC}"

if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠ .env 파일을 생성했습니다.${NC}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 필수: .env 파일에 API 키를 입력하세요:"
    echo ""
    echo "  ANTHROPIC_API_KEY=sk-ant-..."
    echo "    → https://console.anthropic.com/"
    echo ""
    echo "  GEMINI_API_KEY=AIzaSy..."
    echo "    → https://aistudio.google.com/app/apikey"
    echo ""
    echo "  OPENAI_API_KEY= (선택, 나중에 추가 가능)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    read -p "API 키를 지금 입력하시겠습니까? (y/n): " SETUP_KEYS

    if [[ "$SETUP_KEYS" == "y" ]]; then
        read -p "ANTHROPIC_API_KEY: " ANT_KEY
        read -p "GEMINI_API_KEY: "    GEM_KEY
        read -p "OPENAI_API_KEY (비워도 됨): " OAI_KEY

        sed -i "s|ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$ANT_KEY|" .env
        sed -i "s|GEMINI_API_KEY=.*|GEMINI_API_KEY=$GEM_KEY|"       .env
        [ -n "$OAI_KEY" ] && sed -i "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$OAI_KEY|" .env

        echo -e "${GREEN}✓ API 키 저장됨${NC}"
    fi
else
    echo -e "${GREEN}✓ .env 파일 존재${NC}"
fi

# GPU 없으면 docker-compose에서 GPU 설정 제거
if [ "$NVIDIA_SUPPORT" = false ]; then
    echo -e "${YELLOW}  GPU 설정을 비활성화합니다...${NC}"
    sed -i '/deploy:/,/capabilities: \[gpu\]/d' docker-compose.yml 2>/dev/null || true
fi

# ── 데이터 디렉터리 ───────────────────────────────────────────
echo ""
echo -e "${CYAN}[3/6] 데이터 디렉터리 생성...${NC}"
mkdir -p data/{chroma,sqlite,models,generated/circuits}
echo -e "${GREEN}✓ data/ 구조 생성됨${NC}"

# ── Docker 빌드 ───────────────────────────────────────────────
echo ""
echo -e "${CYAN}[4/6] Docker 이미지 빌드 중... (처음 실행시 5~10분 소요)${NC}"
docker compose build --parallel
echo -e "${GREEN}✓ 빌드 완료${NC}"

# ── 서비스 시작 ───────────────────────────────────────────────
echo ""
echo -e "${CYAN}[5/6] 서비스 시작 중...${NC}"
docker compose up -d
sleep 5

# ── Ollama 모델 다운로드 ──────────────────────────────────────
echo ""
echo -e "${CYAN}[6/6] Ollama 로컬 모델 설정...${NC}"
echo "RTX 4070 Super 12GB VRAM에서 실행 가능한 모델:"
echo ""
echo "  1) llama3:8b     (5GB VRAM) - 권장 ★"
echo "  2) mistral:7b    (4GB VRAM) - 빠름"
echo "  3) codellama:13b (8GB VRAM) - 코딩 특화"
echo "  4) 나중에 설정"
echo ""
read -p "다운로드할 모델 번호 (1-4): " MODEL_CHOICE

case $MODEL_CHOICE in
    1) OLLAMA_MODEL="llama3:8b" ;;
    2) OLLAMA_MODEL="mistral:7b" ;;
    3) OLLAMA_MODEL="codellama:13b" ;;
    *) OLLAMA_MODEL="" ;;
esac

if [ -n "$OLLAMA_MODEL" ]; then
    echo -e "${CYAN}  $OLLAMA_MODEL 다운로드 중... (모델 크기에 따라 시간이 걸립니다)${NC}"
    docker exec myai-ollama ollama pull $OLLAMA_MODEL
    echo -e "${GREEN}✓ $OLLAMA_MODEL 준비됨${NC}"
fi

# ── 완료 ─────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════╗"
echo "║          ✅ 설정 완료!                   ║"
echo "╠══════════════════════════════════════════╣"
echo "║  🌐 Web UI:  http://localhost            ║"
echo "║  📡 API:     http://localhost:8000       ║"
echo "║  📚 API 문서: http://localhost:8000/docs ║"
echo "║  🧠 ChromaDB: http://localhost:8001      ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "유용한 명령어:"
echo "  docker compose logs -f backend   # 백엔드 로그"
echo "  docker compose down              # 중지"
echo "  docker compose restart backend   # 재시작"
echo "  docker exec myai-ollama ollama pull <모델명>  # 모델 추가"
