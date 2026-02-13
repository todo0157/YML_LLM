"""
LangGraph 상태 정의
"""
from typing import TypedDict, Annotated, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class SearchResult(BaseModel):
    """검색 결과 모델"""
    source: str  # web, kb, paper, community
    url: str
    title: str = ""
    content: str
    relevance_score: float = 0.5
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True


class ResearchPlan(BaseModel):
    """연구 계획"""
    main_query: str
    sub_queries: list[str] = []
    search_strategies: list[Literal["web", "kb", "paper", "community"]] = ["web", "kb"]
    material_type: str | None = None
    defect_type: str | None = None
    parameters_mentioned: list[str] = []


class ParameterRecommendation(BaseModel):
    """파라미터 추천"""
    parameter: str
    current_value: str | None = None
    recommended_value: str
    confidence: float = 0.5
    sources: list[str] = []
    reasoning: str = ""


def merge_results(existing: list, new: list) -> list:
    """결과 병합 (중복 제거)"""
    if not existing:
        return new
    existing_urls = {r.url for r in existing if hasattr(r, 'url')}
    merged = list(existing)
    for item in new:
        if hasattr(item, 'url') and item.url not in existing_urls:
            merged.append(item)
    return merged


class AgentState(TypedDict):
    """LangGraph 에이전트 상태"""
    # 입력
    original_query: str

    # 계획
    research_plan: ResearchPlan | None

    # 검색 결과
    web_results: Annotated[list[SearchResult], merge_results]
    kb_results: Annotated[list[SearchResult], merge_results]
    paper_results: Annotated[list[SearchResult], merge_results]
    community_results: Annotated[list[SearchResult], merge_results]

    # 중간 상태
    iteration_count: int
    is_sufficient: bool
    confidence_score: float
    missing_info: list[str]

    # 추론 결과
    synthesized_knowledge: str
    recommendations: list[ParameterRecommendation]

    # 최종 출력
    final_response: str
    sources_cited: list[str]

    # 메타데이터
    errors: list[str]
