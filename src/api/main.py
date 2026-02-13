"""
FastAPI 서버
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import json
import asyncio
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

from src.graph.workflow import run_research, run_research_stream
from src.tools.knowledge_base import KnowledgeBase

app = FastAPI(
    title="3D Printing Autonomous Research Agent",
    description="자율적으로 웹을 검색하고 최적의 3D 프린팅 파라미터를 추천합니다",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 지식베이스 초기화
kb = KnowledgeBase()


class ResearchQuery(BaseModel):
    """연구 요청 모델"""
    query: str = Field(..., description="3D 프린팅 관련 질문")
    material: Optional[str] = Field(None, description="재료 타입 (PLA, ABS, PETG 등)")
    current_params: Optional[dict] = Field(None, description="현재 파라미터 설정")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "PETG로 출력 중 stringing이 심합니다. 온도 240도입니다.",
                "material": "PETG",
                "current_params": {
                    "nozzle_temp": 240,
                    "print_speed": 50
                }
            }
        }


class ResearchResponse(BaseModel):
    """연구 응답 모델"""
    response: str
    sources: list[str] = []
    success: bool = True
    error: Optional[str] = None


class MaterialGuideResponse(BaseModel):
    """재료 가이드 응답"""
    material: str
    guide: Optional[str]
    found: bool


class DefectGuideResponse(BaseModel):
    """결함 가이드 응답"""
    defect: str
    guide: Optional[str]
    found: bool


@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "name": "3D Printing Research Agent",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy"}


@app.post("/research", response_model=ResearchResponse)
async def research(query: ResearchQuery):
    """
    3D 프린팅 최적 파라미터 연구

    웹 검색, 지식베이스, 학술 자료를 종합하여
    최적의 파라미터를 추천합니다.
    """
    try:
        # 쿼리 강화 (재료, 파라미터 정보 추가)
        enhanced_query = query.query
        if query.material:
            enhanced_query = f"[재료: {query.material}] {enhanced_query}"
        if query.current_params:
            params_str = ", ".join([f"{k}={v}" for k, v in query.current_params.items()])
            enhanced_query = f"{enhanced_query} (현재 설정: {params_str})"

        # 연구 실행
        response = await run_research(enhanced_query)

        return ResearchResponse(
            response=response,
            sources=[],  # TODO: 소스 추출
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/stream")
async def research_stream(query: ResearchQuery):
    """
    스트리밍 연구 (실시간 진행 상태 확인)
    """
    async def generate():
        try:
            enhanced_query = query.query
            if query.material:
                enhanced_query = f"[재료: {query.material}] {enhanced_query}"

            async for event in run_research_stream(enhanced_query):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)  # 클라이언트 버퍼링 방지

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@app.get("/materials", response_model=list[str])
async def list_materials():
    """지원하는 재료 목록"""
    return list(kb.material_guides.keys())


@app.get("/materials/{material}", response_model=MaterialGuideResponse)
async def get_material_guide(material: str):
    """특정 재료의 가이드 조회"""
    guide = kb.get_material_guide(material)
    return MaterialGuideResponse(
        material=material.upper(),
        guide=guide,
        found=guide is not None
    )


@app.get("/defects", response_model=list[str])
async def list_defects():
    """알려진 결함 유형 목록"""
    return list(kb.defect_guides.keys())


@app.get("/defects/{defect}", response_model=DefectGuideResponse)
async def get_defect_guide(defect: str):
    """특정 결함의 해결 가이드 조회"""
    guide = kb.get_defect_solution(defect)
    return DefectGuideResponse(
        defect=defect,
        guide=guide,
        found=guide is not None
    )


@app.get("/experiments")
async def list_experiments():
    """저장된 실험 데이터 목록"""
    return kb.experiments


@app.post("/experiments")
async def add_experiment(experiment: dict):
    """새 실험 데이터 추가"""
    kb.add_experiment(experiment)
    return {"success": True, "message": "실험 데이터가 추가되었습니다."}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
