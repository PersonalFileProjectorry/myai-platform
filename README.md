# ⚡ MyAI Platform

> **개인용 AI 허브** — Claude · Gemini · Ollama · GPT를 하나의 인터페이스로

---

## 📐 아키텍처

```
사용자 브라우저
     │
     ▼
[Nginx :80]  ←→  [React Frontend :3000]
     │
     ▼
[FastAPI Backend :8000]
     ├── Claude API    (Anthropic - Pro)
     ├── Gemini API    (Google - 무료)
     ├── Ollama        (로컬 - 완전 무료) ──→ RTX 4070 Super
     └── GPT API       (OpenAI - 선택)
           │
     ┌─────┴──────┐
     ▼            ▼
[ChromaDB]    [SQLite]
 벡터 메모리   대화 이력
 (자기학습)
```

---

## 🖥️ 시스템 요구사항

| 항목 | 권장 | 현재 사양 |
|------|------|-----------|
| GPU  | NVIDIA RTX 3070+ | RTX 4070 Super ✅ |
| VRAM | 8GB+  | 12GB ✅ |
| RAM  | 16GB+ | 32GB ✅ |
| 저장소| 100GB+ | 930GB ✅ |

---

## 🚀 빠른 시작

### 1단계 - 클론 및 설정

```bash
# 프로젝트 디렉터리로 이동
cd myai

# 초기 설정 (API 키 입력 포함)
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 2단계 - API 키 설정 (.env 파일)

```env
ANTHROPIC_API_KEY=sk-ant-...   # console.anthropic.com
GEMINI_API_KEY=AIzaSy...       # aistudio.google.com/app/apikey
OPENAI_API_KEY=                # 선택사항 (나중에 추가)
```

### 3단계 - 실행

```bash
docker compose up -d
```

브라우저에서 **http://localhost** 접속 🎉

---

## 🤖 사용 가능한 모델

### ☁️ API 모델

| 모델 | 제공사 | 무료 | 특징 |
|------|--------|------|------|
| claude-sonnet-4-5 | Anthropic | ❌ Pro | 최고 성능, 회로설계 |
| claude-haiku-4-5 | Anthropic | ❌ | 빠름, 저렴 |
| gemini-2.0-flash | Google | ✅ | 무료, 빠름 |
| gemini-1.5-pro | Google | ✅ (제한) | 멀티모달 |
| gpt-4o-mini | OpenAI | ❌ | 선택사항 |

### 🏠 로컬 모델 (Ollama - 완전 무료)

```bash
# 모델 추가 (RTX 4070 Super 권장)
./scripts/add_model.sh

# 직접 추가
docker exec myai-ollama ollama pull llama3:8b       # 범용 (5GB VRAM)
docker exec myai-ollama ollama pull codellama:13b   # 코딩 (8GB VRAM)
docker exec myai-ollama ollama pull qwen2.5:7b      # 한국어 (5GB VRAM)
docker exec myai-ollama ollama pull mistral:7b      # 빠름 (4GB VRAM)
```

---

## 🧠 자기학습 시스템

대화할수록 AI가 당신의 패턴을 학습합니다:

1. **저장**: 모든 대화 → ChromaDB 벡터 DB 자동 저장
2. **검색**: 새 질문 → 유사한 과거 대화 자동 검색
3. **적용**: 관련 기억을 컨텍스트로 추가하여 응답
4. **학습 데이터**: ⭐ 4점 이상 평점 대화 → 파인튜닝 데이터셋 축적

### 메모리 확인

```
http://localhost:8000/api/memory/stats
http://localhost:8000/api/memory/search?q=회로설계
```

---

## 🔌 회로기판 설계 기능

```
http://localhost:8000/api/circuit/design
```

- 자연어로 회로 설명 → KiCad 넷리스트 자동 생성
- 회로도 이미지 업로드 → 부품 분석
- 부품 추천 (전압/전류 기반)

**예시 프롬프트:**
- "5V → 3.3V LDO 레귤레이터 회로 설계해줘"
- "ATmega328P 기반 온도 측정 회로"
- "H브리지 모터 드라이버 (2A, 12V)"

---

## 💻 코드 실행 기능

Docker 샌드박스에서 안전하게 실행:

| 언어 | 지원 |
|------|------|
| Python 3.11 | ✅ |
| JavaScript (Node 20) | ✅ |
| TypeScript | ✅ |
| C / C++ | ✅ |
| Rust | ✅ |
| Bash | ✅ |

---

## 🖼️ 이미지 기능

| 기능 | 백엔드 | 비용 |
|------|--------|------|
| 이미지 생성 | Stability AI API | 무료 크레딧 |
| 이미지 생성 (로컬) | AUTOMATIC1111 SD WebUI | 무료 |
| 이미지 분석 | Claude Vision | API 비용 |
| 회로도 분석 | Claude Vision | API 비용 |

### 로컬 Stable Diffusion 설정

```bash
# AUTOMATIC1111 WebUI (별도 설치)
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
cd stable-diffusion-webui
python webui.py --api --listen
```

---

## 🛠️ 유용한 명령어

```bash
# 서비스 상태 확인
docker compose ps

# 로그 보기
docker compose logs -f backend     # 백엔드
docker compose logs -f ollama      # Ollama

# 재시작
docker compose restart backend

# 모두 중지
docker compose down

# 메모리 초기화 (주의!)
docker compose down -v

# GPU 사용량 모니터링
nvidia-smi -l 1

# Ollama 모델 목록
docker exec myai-ollama ollama list
```

---

## 📡 API 엔드포인트

```
GET  /api/models/                         # 사용 가능한 모델 목록
POST /api/chat/stream                     # 스트리밍 채팅
GET  /api/chat/sessions                   # 세션 목록
POST /api/chat/sessions                   # 새 세션
GET  /api/chat/sessions/{id}/messages     # 대화 이력
GET  /api/memory/stats                    # 메모리 통계
GET  /api/memory/search?q=키워드          # 메모리 검색
POST /api/images/generate                 # 이미지 생성
POST /api/images/analyze                  # 이미지 분석
POST /api/code/run                        # 코드 실행
POST /api/circuit/design                  # 회로 설계
POST /api/circuit/analyze-image          # 회로도 분석

# 대화형 API 문서
http://localhost:8000/docs
```

---

## 🔮 향후 계획

- [ ] 파인튜닝 파이프라인 (Unsloth + LoRA)
- [ ] 음성 입출력 (Whisper + TTS)
- [ ] 웹 검색 통합
- [ ] KiCad 직접 연동
- [ ] SPICE 시뮬레이션 자동화
- [ ] 모바일 앱 (PWA)

---

## ⚠️ 주의사항

- **API 비용**: Claude/Gemini API는 토큰당 과금됩니다
- **VRAM**: 여러 Ollama 모델 동시 로드 시 12GB 초과 주의
- **HDD**: 로컬 모델은 모델당 4~40GB 용량 필요
- **보안**: `.env` 파일을 절대 공개 저장소에 올리지 마세요
