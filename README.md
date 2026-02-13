# 3D Printing Autonomous Research Agent

자율적으로 웹을 검색하고 최적의 3D 프린팅 파라미터를 추천하는 AI 에이전트입니다.

## 특징

- **Agentic RAG**: 단순 검색이 아닌 자율적 연구 수행
- **다중 소스 검색**: 웹, 학술 논문, 커뮤니티, 내부 지식베이스
- **반복적 개선**: 정보가 부족하면 자동으로 쿼리 재구성 후 재검색
- **신뢰도 점수**: 각 추천에 대한 신뢰도와 출처 제공
- **3D 프린팅 특화**: 재료별/결함별 전문 가이드 내장

## 아키텍처

```
User Query
    │
    ▼
┌─────────────┐
│ Query Parser│ ─── 쿼리 분석 및 연구 계획
└──────┬──────┘
       │
   ┌───┴───┐
   ▼       ▼
┌─────┐ ┌─────┐ ┌─────┐
│ Web │ │ KB  │ │Paper│ ─── 병렬 검색
└──┬──┘ └──┬──┘ └──┬──┘
   └───────┼───────┘
           ▼
   ┌───────────────┐
   │ Evaluate      │ ─── 충분성 평가
   └───────┬───────┘
           │
    [부족] ┴ [충분]
           │
   ┌───────┼───────┐
   ▼       │       ▼
Refine     │   Synthesize ─── 정보 종합
   │       │       │
   └───────┘       ▼
               Validate ─── 검증
                   │
                   ▼
            Generate Output
```

## 설치

```bash
# 저장소 이동
cd 3d-print-research-agent

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 API 키 입력
```

## 필수 API 키

- **ANTHROPIC_API_KEY**: Claude API 키 (https://console.anthropic.com)
- **TAVILY_API_KEY**: Tavily 검색 API 키 (https://tavily.com)

## 사용법

### 1. CLI 모드 (단일 질문)

```bash
python run.py cli --query "PETG로 출력 중 stringing이 심합니다. 노즐 온도 240도입니다."
```

### 2. 대화형 모드

```bash
python run.py interactive
```

### 3. API 서버 모드

```bash
python run.py server --port 8000

# 또는 직접 실행
uvicorn src.api.main:app --reload
```

API 문서: http://localhost:8000/docs

### API 예시

```bash
# 연구 요청
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "PETG stringing 해결 방법",
    "material": "PETG",
    "current_params": {"nozzle_temp": 240}
  }'

# 재료 가이드 조회
curl "http://localhost:8000/materials/PETG"

# 결함 해결 가이드 조회
curl "http://localhost:8000/defects/stringing"
```

## 프로젝트 구조

```
3d-print-research-agent/
├── src/
│   ├── graph/
│   │   ├── state.py      # LangGraph 상태 정의
│   │   ├── nodes.py      # 그래프 노드 구현
│   │   ├── prompts.py    # 프롬프트 템플릿
│   │   └── workflow.py   # 워크플로우 조립
│   ├── tools/
│   │   ├── tavily_search.py   # 웹 검색
│   │   └── knowledge_base.py  # 내부 지식베이스
│   └── api/
│       └── main.py       # FastAPI 서버
├── data/
│   └── sample_experiments.json  # 샘플 실험 데이터
├── config/
│   └── settings.yaml     # 설정
├── run.py                # 실행 스크립트
├── requirements.txt
└── .env.example
```

## 지원 기능

### 재료
- PLA, ABS, PETG, TPU

### 결함 유형
- Stringing, Warping, Layer Adhesion
- Under/Over Extrusion, First Layer Issues

## 커스터마이징

### 자체 실험 데이터 추가

`data/sample_experiments.json` 에 실험 데이터 추가:

```json
{
  "experiment_id": "EXP_006",
  "material": {"type": "PETG", "brand": "..."},
  "parameters": {
    "nozzle_temp": 235,
    "bed_temp": 80,
    ...
  },
  "result": {
    "quality_score": 8,
    "defects": [],
    "notes": "..."
  }
}
```

### 재료/결함 가이드 확장

`src/tools/knowledge_base.py` 의 `material_guides`, `defect_guides` 수정

## 비용 예상

월 1,000 쿼리 기준:
- Claude API: ~$30-50
- Tavily API: ~$10-20
- **합계: ~$40-70/월**

## 라이선스

MIT License
