# 3D Print Research Agent - 프로젝트 상태

## 프로젝트 개요
3D 프린팅 품질 예측 및 최적 파라미터 추천을 위한 Autonomous Research Agent (RAG 2.0 / Agentic RAG)

## 기술 스택
- **Backend**: FastAPI + LangGraph + Gemini 1.5 Flash
- **Frontend**: React + Vite + TypeScript
- **배포**: Cloudflare Pages (프론트엔드) + Render (백엔드)

## 배포 완료 ✅

### 라이브 URL
- **프론트엔드**: https://3d-print-agent.pages.dev
- **백엔드 API**: https://yml-llm.onrender.com
- **GitHub**: https://github.com/todo0157/YML_LLM

### 환경변수 (Render에 설정됨)
- `GOOGLE_API_KEY`: Gemini API 키
- `TAVILY_API_KEY`: Tavily 웹 검색 API 키

## 완료된 작업
- [x] LangGraph 워크플로우 구현 (nodes.py, workflow.py)
- [x] Gemini API로 전환 완료
- [x] 프론트엔드 개발 및 Cloudflare Pages 배포
- [x] GitHub 저장소 연동
- [x] render.yaml 배포 설정 파일 생성
- [x] Render 백엔드 배포
- [x] 프론트엔드-백엔드 연결 (.env.production)

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
│   └── .env.production      # Render 백엔드 URL 설정
├── render.yaml              # Render 배포 설정
├── requirements.txt         # Python 의존성
└── .env.example             # 환경변수 템플릿
```

## 사용 방법
1. https://3d-print-agent.pages.dev 접속
2. 3D 프린팅 관련 질문 입력 (예: "PETG stringing 해결 방법")
3. AI가 웹 검색 + 지식베이스를 조회하여 답변 생성

## 참고
- 첫 요청 시 Render 서버 웨이크업으로 30초 정도 대기 필요
- 수동 설정 필요 시: 설정(⚙️) → API 엔드포인트에 https://yml-llm.onrender.com 입력
