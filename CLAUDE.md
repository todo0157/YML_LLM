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

---

## Session Update (2026-02-18)

### What was done in this session
- 로컬 서버 실행 시도
- Python 경로 문제 해결: `C:\Users\thf56\AppData\Local\Programs\Python\Python313\python.exe` 사용
- 프론트엔드 `.env.local` 수정: `VITE_API_ENDPOINT=http://localhost:8000` (로컬 테스트용)
- 백엔드 서버 실행 성공 (포트 8000)
- 프론트엔드 서버 실행 성공 (포트 5175)

### 발견된 문제
- 백엔드 `/research` 엔드포인트 500 에러 발생
- 원인: **GOOGLE_API_KEY가 유효하지 않음** (만료 또는 삭제됨)
- 에러 메시지: `400 INVALID_ARGUMENT. API Key not found. Please pass a valid API key.`

### 다음 세션에서 할 작업
1. [Google AI Studio](https://aistudio.google.com/apikey)에서 새 GOOGLE_API_KEY 발급
2. `.env` 파일에 새 API 키 설정
3. 백엔드 서버 재시작
4. 로컬 테스트 진행 (프론트엔드 -> 백엔드 -> Gemini API)
5. 정상 동작 확인 후 Render 환경변수도 업데이트

### 로컬 서버 실행 명령어
```bash
# 백엔드 (포트 8000)
cd 3d-print-research-agent
C:\Users\thf56\AppData\Local\Programs\Python\Python313\python.exe run.py server

# 프론트엔드 (Vite)
cd 3d-print-research-agent/frontend
npm run dev
```

### 현재 설정 상태
- `frontend/.env.local`: `VITE_API_ENDPOINT=http://localhost:8000` (로컬 테스트용)
- `frontend/.env.production`: `VITE_API_ENDPOINT=https://yml-llm.onrender.com` (배포용)

---

## Session Update (2026-02-19)

### 완료된 작업
- [x] 새 GOOGLE_API_KEY 발급 및 `.env` 설정 완료
- [x] 로컬 백엔드 서버 시작 및 테스트 성공 (포트 8000)
- [x] 로컬 프론트엔드 서버 시작 성공 (포트 5173)
- [x] Gemini API 연동 확인 (45개 모델 사용 가능)
- [x] `/research` API 테스트 성공 (PLA, ABS 온도 분석 완료)
- [x] Render 환경변수 `GOOGLE_API_KEY` 업데이트 및 재배포
- [x] Render 백엔드 정상 동작 확인 (`/health`, `/debug/models`, `/research` 모두 OK)
- [x] UI 깨짐 문제 수정 (긴 URL 줄바꿈 처리)

### UI 수정 내용
**문제**: 참고 소스 URL이 너무 길어서 레이아웃 깨짐

**수정 파일**:
1. `frontend/src/App.css`:
   - `.message-content`에 `word-break: break-word` 추가
   - `.sources a`, `.message-content a`에 `word-break: break-all` 추가
2. `frontend/src/App.tsx`:
   - ReactMarkdown에 커스텀 링크 컴포넌트 추가 (40자 초과 시 truncate)

### 현재 상태
| 구성 요소 | 상태 | URL |
|-----------|------|-----|
| Render 백엔드 | ✅ 정상 | https://yml-llm.onrender.com |
| Cloudflare 프론트엔드 | ✅ 정상 | https://3d-print-agent.pages.dev |
| Gemini API | ✅ 연결됨 | 45개 모델 사용 가능 |
| /research API | ✅ 성공 | 정상 응답 |

### 다음 세션에서 할 작업
1. **CSV 데이터를 Knowledge Base에 추가**
   - 사용자의 3D 프린팅 실험 데이터 (수십 개)
   - CSV → JSON 변환 스크립트 작성
   - `data/sample_experiments.json`에 추가
2. Cloudflare Pages 재배포 (UI 수정 반영)

### Knowledge Base 데이터 형식 참고
```json
{
  "experiment_id": "EXP_XXX",
  "material": {"type": "PLA", "brand": "브랜드명"},
  "parameters": {
    "nozzle_temp": 210,
    "bed_temp": 60,
    "layer_height": 0.2,
    "print_speed": 60,
    "retraction_distance": 5.0,
    "retraction_speed": 45,
    "fan_speed": 100
  },
  "result": {
    "quality_score": 8,
    "defects": ["stringing"],
    "notes": "실험 결과 메모"
  },
  "optimized_params": {
    "nozzle_temp": 200,
    "reason": "최적화 이유"
  }
}
```

### 로컬 서버 실행 명령어
```bash
# 백엔드 (포트 8000)
cd 3d-print-research-agent
C:\Users\thf56\AppData\Local\Programs\Python\Python313\python.exe run.py server

# 프론트엔드 (Vite)
cd 3d-print-research-agent/frontend
npm run dev
```

---

## Session Update (2026-02-20)

### Cloudflare Workers 전환 완료!

**Render 백엔드 → Cloudflare Pages Functions로 전환**

### 변경된 아키텍처
| 구성 요소 | 이전 | 이후 |
|-----------|------|------|
| 백엔드 | Render (Python/FastAPI) | Cloudflare Pages Functions (TypeScript) |
| 프론트엔드 | Cloudflare Pages | Cloudflare Pages (동일) |
| API 경로 | https://yml-llm.onrender.com/research | /api/research (같은 도메인) |

### 장점
- **슬립 모드 없음**: Render 무료 플랜의 15분 비활성 슬립 문제 해결
- **빠른 응답**: 전세계 엣지에서 실행
- **단일 도메인**: CORS 설정 불필요
- **무료**: Cloudflare Workers 무료 플랜 사용

### 새로 추가된 파일
```
frontend/
├── lib/                       # 새로 추가 - 공유 로직
│   ├── types.ts               # TypeScript 타입 정의
│   ├── gemini.ts              # Gemini API 클라이언트
│   ├── tavily.ts              # Tavily 검색 API
│   ├── knowledge-base.ts      # 지식베이스 (Python → TS 변환)
│   ├── prompts.ts             # 프롬프트 템플릿
│   └── workflow.ts            # 워크플로우 (LangGraph → 직접 구현)
├── functions/                 # 새로 추가 - API 핸들러
│   └── api/
│       ├── health.ts          # GET /api/health
│       ├── research.ts        # POST /api/research
│       └── materials/
│           ├── index.ts       # GET /api/materials
│           └── [material].ts  # GET /api/materials/:material
├── wrangler.toml              # Cloudflare 설정 (업데이트)
├── tsconfig.worker.json       # Workers용 TypeScript 설정
└── .dev.vars                  # 로컬 개발용 환경변수 (git ignored)
```

### 로컬 테스트 결과
```bash
# 헬스 체크
curl http://localhost:8788/api/health
# 응답: {"status":"healthy"}

# 연구 API
curl -X POST http://localhost:8788/api/research -d '{"query": "PLA 최적 온도"}'
# 응답: 상세한 파라미터 추천 (성공!)
```

### 배포 방법
```bash
cd frontend

# 1. 빌드
npm run build

# 2. 배포 (Cloudflare 로그인 필요)
npm run deploy
```

### Cloudflare 환경변수 설정 (필수!)
Cloudflare Dashboard > Pages > 3d-print-agent > Settings > Environment variables:
- `GOOGLE_API_KEY`: Gemini API 키
- `TAVILY_API_KEY`: Tavily 웹 검색 API 키

### 로컬 개발 명령어
```bash
cd frontend
npm install
npm run preview   # Wrangler로 로컬 테스트
```

### 다음 작업
1. CSV 데이터를 Knowledge Base에 추가

---

## Session Update (2026-02-20 오후)

### 완료된 작업

#### 1. 성능 최적화
- LLM 호출 3회 → 1회로 최적화
- 쿼리 분석을 로컬 키워드 매칭으로 대체 (LLM 호출 제거)
- 웹 검색 결과 수 축소 (5개 → 3개)

#### 2. 출처 인용 기능 구현
- **문장별 클릭 가능한 하이퍼링크**: 웹 출처가 있는 문장 클릭 시 해당 사이트로 이동
- **지식베이스 출처 표시**: `[PLA 가이드]` 형식으로 표시
- rehype-raw 패키지 추가하여 HTML 렌더링 지원

#### 3. UI 스타일 추가
- `.source-link`: 클릭 가능한 출처 문장 (파란색 + 점선 밑줄)
- `.kb-source`: 지식베이스 출처 (회색 이탤릭)

### 기술 변경 사항

**workflow.ts 변경:**
```typescript
// 문장을 HTML 링크로 변환
<a href="url" target="_blank" class="source-link">클릭 가능한 문장</a>
<span class="kb-source">[지식베이스 출처]</span>
```

**App.tsx 변경:**
```typescript
import rehypeRaw from 'rehype-raw'

<ReactMarkdown rehypePlugins={[rehypeRaw]}>
  {message.content}
</ReactMarkdown>
```

**App.css 추가:**
```css
.source-link {
  color: var(--primary);
  border-bottom: 1px dashed var(--primary);
  cursor: pointer;
}

.kb-source {
  font-style: italic;
  color: var(--text-muted);
}
```

### 새로 설치된 패키지
- `rehype-raw`: ReactMarkdown에서 HTML 태그 렌더링 지원

### 배포 URL
- **프로덕션**: https://3d-print-agent.pages.dev
- **GitHub**: https://github.com/todo0157/YML_LLM

### 로컬 테스트 명령어
```bash
cd frontend
npm install
npm run build
npx wrangler pages dev dist --port 8788
# 브라우저: http://localhost:8788
```
