# 3D Print Research Agent - 프로젝트 상태

## 프로젝트 개요
3D 프린팅 품질 예측 및 최적 파라미터 추천을 위한 Autonomous Research Agent (RAG 2.0 / Agentic RAG)

## 기술 스택
- **Backend**: FastAPI + LangGraph + Gemini 1.5 Flash
- **Frontend**: React + Vite + TypeScript
- **배포**: Cloudflare Pages (프론트엔드) + Render (백엔드 예정)

## 현재 완료된 작업
- [x] LangGraph 워크플로우 구현 (nodes.py, workflow.py)
- [x] Gemini API로 전환 완료 (기존 Anthropic/OpenAI에서 변경)
- [x] 프론트엔드 개발 및 Cloudflare Pages 배포: https://3d-print-agent.pages.dev
- [x] GitHub 저장소 연동: https://github.com/todo0157/YML_LLM
- [x] render.yaml 배포 설정 파일 생성

---

## 다음 작업: Render 백엔드 배포

### 1단계: API 키 준비

**Gemini API 키 (무료):**
1. https://aistudio.google.com/apikey 접속
2. Google 계정 로그인
3. "Create API Key" 클릭
4. 키 복사 (AIzaSy... 형식)

**Tavily API 키 (무료 1000회/월):**
1. https://tavily.com 접속
2. 회원가입 후 API Key 발급

### 2단계: Render 배포

1. https://render.com 접속 후 GitHub 계정으로 로그인
2. "New +" → "Web Service" 클릭
3. "Connect a repository" → GitHub 연결
4. `todo0157/YML_LLM` 선택
5. 설정:
   - **Name**: `3d-print-agent-api`
   - **Region**: Singapore (한국과 가까움)
   - **Branch**: main
   - **Root Directory**: (비워둠)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
6. "Environment" 섹션에서 환경 변수 추가:
   - `GOOGLE_API_KEY` = (발급받은 Gemini API 키)
   - `TAVILY_API_KEY` = (발급받은 Tavily API 키)
7. "Create Web Service" 클릭

배포 완료되면 `https://3d-print-agent-api.onrender.com` 형태의 URL이 생성됩니다.

### 3단계: 프론트엔드 연결

배포된 백엔드 URL을 프론트엔드 설정에 입력하면 됩니다.
- 현재 프론트엔드: https://3d-print-agent.pages.dev
- 프론트엔드의 설정 패널(톱니바퀴 아이콘)에서 API Endpoint를 Render URL로 변경

---

## 무료 플랜 제한사항
- **Render Free**: 15분 비활성 시 슬립 모드 (첫 요청 시 30초 정도 웨이크업 대기)
- **Gemini Free**: 15 RPM, 1일 ~1500 요청
- **Tavily Free**: 월 1000회 검색

## 주요 파일 구조
```
3d-print-research-agent/
├── src/
│   ├── api/main.py          # FastAPI 서버
│   ├── graph/
│   │   ├── nodes.py         # LangGraph 노드 (Gemini 사용)
│   │   ├── workflow.py      # 워크플로우 정의
│   │   ├── state.py         # 상태 정의
│   │   └── prompts.py       # 프롬프트 템플릿
│   └── tools/
│       ├── tavily_search.py # 웹 검색
│       └── knowledge_base.py # 내장 지식베이스
├── frontend/                 # React 프론트엔드
├── render.yaml              # Render 배포 설정
├── requirements.txt         # Python 의존성
└── .env.example             # 환경변수 템플릿
```
