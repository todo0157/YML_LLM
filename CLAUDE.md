# 3D Print Research Agent - 프로젝트 상태

## 프로젝트 개요
3D 프린팅 품질 예측 및 최적 파라미터 추천을 위한 Autonomous Research Agent (RAG 2.0 / Agentic RAG)

## 기술 스택
- **Backend**: FastAPI + LangGraph + Gemini 2.0 Flash
- **Frontend**: React + Vite + TypeScript
- **배포**: Cloudflare Pages (프론트엔드) + Render (백엔드)

## 배포 URL
- **프론트엔드**: https://3d-print-agent.pages.dev
- **백엔드 API**: https://yml-llm.onrender.com
- **GitHub**: https://github.com/todo0157/YML_LLM

### 환경변수 (Render에 설정됨)
- `GOOGLE_API_KEY`: Gemini API 키
- `TAVILY_API_KEY`: Tavily 웹 검색 API 키

## 현재 상태 (2026-02-13)

### 완료된 작업
- [x] LangGraph 워크플로우 구현 (nodes.py, workflow.py)
- [x] 프론트엔드 개발 및 Cloudflare Pages 배포
- [x] GitHub 저장소 연동
- [x] Render 백엔드 배포
- [x] 프론트엔드-백엔드 연결 (.env.production)
- [x] 디버그 엔드포인트 추가 (/debug/models)

### 진행 중인 작업
- [ ] Gemini API 모델 연동 수정 필요

## 중요: Gemini API 모델 이슈

### 문제
- `gemini-1.5-flash`, `gemini-pro` 등 구버전 모델은 더 이상 사용 불가
- API 에러: "models/xxx is not found for API version v1beta"

### 해결 방법
`/debug/models` 엔드포인트에서 사용 가능한 모델 확인 후 변경

### 사용 가능한 모델 (2026-02-13 확인)
```
gemini-2.5-flash       # 최신 추천
gemini-2.5-pro
gemini-2.0-flash       # 현재 설정됨
gemini-2.0-flash-lite
gemini-flash-latest
```

### 사용 불가 모델 (deprecated)
```
gemini-1.5-flash      # 404 NOT_FOUND
gemini-1.5-pro
gemini-pro
gemini-2.0-flash-exp
```

### 모델 변경 방법
`src/graph/nodes.py`의 `call_gemini` 함수에서 model 파라미터 수정:
```python
response = await client.aio.models.generate_content(
    model="gemini-2.0-flash",  # 여기 변경
    contents=prompt
)
```

## 패키지 의존성

### 사용 중
- `google-genai>=1.0.0` - 새 Google AI SDK (권장)

### 사용하지 않음 (deprecated)
- `google-generativeai` - 구버전, 더 이상 지원 안 함

## 주요 파일 구조
```
3d-print-research-agent/
├── src/
│   ├── api/main.py          # FastAPI 서버 + 디버그 엔드포인트
│   ├── graph/
│   │   ├── nodes.py         # LangGraph 노드 (Gemini 사용) ⚠️ 모델명 여기서 변경
│   │   ├── workflow.py      # 워크플로우 정의
│   │   ├── state.py         # 상태 정의
│   │   └── prompts.py       # 프롬프트 템플릿
│   └── tools/
│       ├── tavily_search.py # 웹 검색
│       └── knowledge_base.py # 내장 지식베이스
├── frontend/                 # React 프론트엔드
│   └── .env.production      # Render 백엔드 URL 설정
├── render.yaml              # Render 배포 설정
├── requirements.txt         # Python 의존성
└── runtime.txt              # Python 버전 (3.11.9)
```

## 디버그 엔드포인트
- `GET /debug/models` - 사용 가능한 Gemini 모델 목록 확인

## Render 배포 참고사항
- **Python 버전**: 3.11.9 (runtime.txt에 지정)
- **캐시 문제 시**: Render Dashboard > Settings > "Clear build cache & deploy"
- **환경변수**: Render Dashboard > Environment에서 설정
- **무료 플랜**: 15분 비활성 시 슬립 모드 (첫 요청 시 ~30초 대기)

## 무료 플랜 제한사항
- **Render Free**: 15분 비활성 시 슬립 모드
- **Gemini Free**: 15 RPM, 1일 ~1500 요청
- **Tavily Free**: 월 1000회 검색

## 다음 작업
1. Render에서 재배포하여 `gemini-2.0-flash` 모델 적용 확인
2. 정상 동작 확인 후 프론트엔드 테스트

---

## Session Update (2026-02-17)

### What was done in this chat
- Started frontend and backend locally for debugging.
- Installed missing Python dependencies from `requirements.txt` (including `langgraph`, `google-genai`).
- Updated backend env validation in `run.py`:
  - from `ANTHROPIC_API_KEY` to `GOOGLE_API_KEY`
  - kept `TAVILY_API_KEY`
- Updated Gemini call path in `src/graph/nodes.py`:
  - default model uses `GEMINI_MODEL` env var (default `gemini-2.5-flash`)
  - added fallback sequence: `gemini-2.0-flash` -> `gemini-flash-latest`
  - model `NOT_FOUND` errors now automatically try fallback model
- Configured frontend API endpoint for deployed backend via local config:
  - `frontend/.env.local` -> `VITE_API_ENDPOINT=https://yml-llm.onrender.com`

### Root cause timeline (500 errors)
- Initial error: connection refused (`ERR_CONNECTION_REFUSED`) because backend process was not running.
- Next error: Render `/research` returned `500` with model not found
  - `models/gemini-1.5-flash is not found`
- After redeploy/key update: Render `/health` and `/debug/models` work, but `/research` still fails with
  - `429 RESOURCE_EXHAUSTED` (Gemini quota/rate limit exhausted)

### Current status
- Frontend: running and reachable.
- Render backend:
  - `/health` = OK
  - `/debug/models` = OK
  - `/research` = FAIL (429 quota exhaustion from Gemini provider)

### Next steps for tomorrow
1. Verify active Google project quota/billing and Gemini usage limits for the key used in Render.
2. If needed, switch Render `GOOGLE_API_KEY` to a project with available quota.
3. Re-test `POST /research` after quota recovery or key switch.
4. If quota issues are frequent, add graceful 429 handling/message in API and frontend UI.
