#!/bin/bash
# Ollama 모델 관리 스크립트
# RTX 4070 Super (12GB VRAM) 기준

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${CYAN}=== Ollama 모델 관리 (RTX 4070 Super 12GB) ===${NC}"
echo ""

# 현재 설치된 모델
echo "📦 현재 설치된 모델:"
docker exec myai-ollama ollama list 2>/dev/null || echo "  (Ollama가 실행중이지 않습니다)"
echo ""

# 권장 모델 목록
echo "🔧 RTX 4070 Super 권장 모델:"
echo ""
echo "  ┌─────────────────┬──────────┬───────────┬─────────────────────┐"
echo "  │ 모델            │ VRAM     │ 크기      │ 특징                │"
echo "  ├─────────────────┼──────────┼───────────┼─────────────────────┤"
echo "  │ llama3:8b       │ ~5GB     │ 4.7GB     │ 범용 ★ 권장        │"
echo "  │ llama3:70b-q4   │ ~10GB    │ 40GB      │ 고성능 (느림)       │"
echo "  │ mistral:7b      │ ~4GB     │ 4.1GB     │ 빠른 응답           │"
echo "  │ codellama:13b   │ ~8GB     │ 7.4GB     │ 코딩 특화 ★        │"
echo "  │ deepseek-r1:8b  │ ~5GB     │ 4.7GB     │ 추론 특화           │"
echo "  │ gemma2:9b       │ ~6GB     │ 5.4GB     │ Google 모델         │"
echo "  │ qwen2.5:7b      │ ~5GB     │ 4.4GB     │ 다국어 ★           │"
echo "  │ phi3:mini       │ ~2GB     │ 2.2GB     │ 초경량              │"
echo "  └─────────────────┴──────────┴───────────┴─────────────────────┘"
echo ""
echo "  ※ 동시 사용 주의: 두 모델 합산 VRAM이 12GB 초과하지 않게 하세요"
echo ""

read -p "설치할 모델명 입력 (예: codellama:13b, 엔터=건너뜀): " MODEL

if [ -n "$MODEL" ]; then
    echo -e "${CYAN}다운로드 중: $MODEL${NC}"
    docker exec myai-ollama ollama pull "$MODEL"
    echo -e "${GREEN}✓ $MODEL 설치 완료${NC}"
fi
