# 3D Print Research Agent - 프로젝트 현황 리포트

**작성일**: 2026-02-20
**버전**: 2.0 (Cloudflare Workers 전환 완료)

---

## 1. 프로젝트 개요

3D 프린팅 품질 예측 및 최적 파라미터 추천을 위한 **Autonomous Research Agent**입니다.
사용자의 질문에 대해 웹 검색, 내장 지식베이스, LLM을 활용하여 실용적인 답변을 제공합니다.

### 주요 기능
- 3D 프린팅 파라미터 최적화 추천 (온도, 속도, 리트랙션 등)
- 재료별 가이드 제공 (PLA, ABS, PETG, TPU)
- 결함 해결 방법 안내 (stringing, warping, layer adhesion 등)
- 웹 검색 기반 최신 정보 수집
- 출처 인용이 포함된 신뢰성 있는 답변

---

## 2. 시스템 아키텍처

### 현재 구조 (v2.0 - Cloudflare Workers)

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloudflare Pages                         │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │   React Frontend    │ ←→ │   Pages Functions (API)     │ │
│  │   (Vite + TS)       │    │   TypeScript                │ │
│  └─────────────────────┘    └──────────────┬──────────────┘ │
└─────────────────────────────────────────────┼───────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
            ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
            │  Gemini API  │         │  Tavily API  │         │ Knowledge    │
            │  (LLM)       │         │  (웹 검색)    │         │ Base (내장)  │
            └──────────────┘         └──────────────┘         └──────────────┘
```

### 이전 구조 (v1.0 - 레거시, 미사용)

```
Frontend (Cloudflare Pages) ←→ Backend (Render - Python/FastAPI)
```

---

## 3. 디렉토리 구조

```
3d-print-research-agent/
│
├── frontend/                          # 프론트엔드 + 백엔드 (통합)
│   ├── src/                           # React 애플리케이션
│   │   ├── App.tsx                    # 메인 컴포넌트
│   │   ├── App.css                    # 스타일 (다크/라이트 모드)
│   │   ├── main.tsx                   # 엔트리 포인트
│   │   └── index.css                  # 전역 스타일
│   │
│   ├── functions/                     # Cloudflare Pages Functions (API)
│   │   ├── api/
│   │   │   ├── health.ts              # GET /api/health
│   │   │   ├── research.ts            # POST /api/research (메인 API)
│   │   │   └── materials/
│   │   │       ├── index.ts           # GET /api/materials
│   │   │       └── [material].ts      # GET /api/materials/:material
│   │   │
│   │   └── lib/                       # 핵심 로직
│   │       ├── types.ts               # TypeScript 타입 정의
│   │       ├── gemini.ts              # Gemini API 클라이언트
│   │       ├── tavily.ts              # Tavily 웹 검색 API
│   │       ├── knowledge-base.ts      # 내장 지식베이스
│   │       ├── prompts.ts             # LLM 프롬프트 템플릿
│   │       └── workflow.ts            # 연구 워크플로우 (핵심)
│   │
│   ├── index.html                     # HTML 템플릿
│   ├── package.json                   # NPM 의존성
│   ├── wrangler.toml                  # Cloudflare 설정
│   ├── vite.config.ts                 # Vite 빌드 설정
│   └── tsconfig.*.json                # TypeScript 설정
│
├── src/                               # [레거시] Python 백엔드 (미사용)
│   ├── api/main.py                    # FastAPI 서버
│   ├── graph/                         # LangGraph 워크플로우
│   └── tools/                         # 도구 (검색, 지식베이스)
│
├── data/
│   └── sample_experiments.json        # 샘플 실험 데이터
│
├── CLAUDE.md                          # Claude Code 세션 노트
├── report.md                          # 이 파일
└── requirements.txt                   # [레거시] Python 의존성
```

---

## 4. 핵심 컴포넌트 설명

### 4.1 워크플로우 (`workflow.ts`)

연구 에이전트의 핵심 로직을 담당합니다.

**실행 흐름:**
```
1. parseQueryLocal()     → 쿼리 분석 (로컬 키워드 매칭, LLM 호출 없음)
2. performSearch()       → 웹 + 지식베이스 병렬 검색
3. synthesizeOnce()      → LLM 종합 및 추천 생성 (단일 호출)
4. validateRecommendations() → 파라미터 범위 검증
5. generateOutput()      → 마크다운 응답 생성
```

**최적화 내용:**
| 항목 | v1.0 | v2.0 |
|------|------|------|
| LLM 호출 | 3회 | **1회** |
| 반복 루프 | 최대 3회 | 없음 |
| 쿼리 분석 | LLM | 로컬 키워드 매칭 |

### 4.2 지식베이스 (`knowledge-base.ts`)

내장된 3D 프린팅 지식을 제공합니다.

**재료 가이드:**
- PLA: 190-220°C, 베드 50-65°C
- ABS: 230-260°C, 베드 90-110°C, 인클로저 권장
- PETG: 220-250°C, 베드 70-85°C
- TPU: 220-240°C, 베드 40-60°C

**결함 해결:**
- Stringing, Warping, Layer Adhesion
- Under/Over Extrusion
- Clogging, Elephant Foot, Z-Banding

### 4.3 Gemini 클라이언트 (`gemini.ts`)

Google Gemini API와 통신합니다.

```typescript
// 모델 우선순위 (폴백 지원)
const MODELS = [
  'gemini-2.0-flash',      // 기본
  'gemini-2.5-flash',      // 폴백 1
  'gemini-flash-latest'    // 폴백 2
];
```

### 4.4 프론트엔드 (`App.tsx`)

React 기반 채팅 인터페이스입니다.

**주요 기능:**
- 실시간 대화 UI
- 마크다운 렌더링 (테이블, 링크 포함)
- 다크/라이트 모드 자동 전환
- 연결 상태 표시
- 예시 질문 클릭

---

## 5. API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/health` | 서버 상태 확인 |
| POST | `/api/research` | 연구 질의 처리 |
| GET | `/api/materials` | 재료 목록 조회 |
| GET | `/api/materials/:material` | 특정 재료 가이드 |

### POST /api/research 요청/응답

**요청:**
```json
{
  "query": "PLA stringing 해결 방법",
  "material": "PLA",           // 선택
  "currentParams": {           // 선택
    "nozzle_temp": 210,
    "bed_temp": 60
  }
}
```

**응답:**
```json
{
  "response": "## 문제 분석\n\n...(마크다운)...",
  "sources": [],
  "success": true
}
```

---

## 6. 배포 정보

### 환경

| 항목 | 값 |
|------|-----|
| 플랫폼 | Cloudflare Pages |
| 프론트엔드 | React + Vite + TypeScript |
| 백엔드 | Cloudflare Pages Functions |
| LLM | Google Gemini 2.0 Flash |
| 검색 | Tavily API |

### URL

- **프로덕션**: https://3d-print-agent.pages.dev
- **GitHub**: https://github.com/todo0157/YML_LLM

### 환경변수 (Cloudflare에 설정)

```
GOOGLE_API_KEY=xxx    # Gemini API 키
TAVILY_API_KEY=xxx    # Tavily 검색 API 키
```

---

## 7. 로컬 개발

### 설치

```bash
cd frontend
npm install
```

### 개발 서버

```bash
# 프론트엔드만 (API 없음)
npm run dev

# 프론트엔드 + API (Wrangler)
npm run preview
```

### 환경변수 설정

`frontend/.dev.vars` 파일 생성:
```
GOOGLE_API_KEY=your-gemini-api-key
TAVILY_API_KEY=your-tavily-api-key
```

### 배포

```bash
npm run build
npm run deploy
```

---

## 8. 주요 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-02-20 | 2.0 | Cloudflare Workers 전환, LLM 최적화 (3→1), 출처 인용 추가 |
| 2026-02-19 | 1.5 | Gemini API 키 갱신, UI 레이아웃 수정 |
| 2026-02-17 | 1.1 | Gemini 모델 폴백 로직 추가 |
| 2026-02-13 | 1.0 | 초기 배포 (Render + Cloudflare Pages) |

---

## 9. 알려진 제한사항

1. **Tavily 무료 플랜**: 월 1,000회 검색 제한
2. **Gemini 무료 플랜**: 15 RPM, 일 1,500 요청 제한
3. **Cloudflare Workers**: CPU 시간 10ms (네트워크 I/O 제외)

---

## 10. 향후 계획

- [ ] CSV 실험 데이터를 지식베이스에 추가
- [ ] 사용자 피드백 수집 기능
- [ ] 다국어 지원 (영어)
- [ ] 이미지 분석 기능 (출력물 사진으로 문제 진단)

---

*이 리포트는 Claude Code에 의해 자동 생성되었습니다.*
