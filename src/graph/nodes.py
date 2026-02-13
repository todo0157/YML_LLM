"""
LangGraph 노드 구현 - Gemini 버전 (google-genai 패키지 사용)
"""
import json
import os
from typing import Any
from google import genai

from .state import AgentState, ResearchPlan, SearchResult, ParameterRecommendation
from .prompts import (
    QUERY_PARSER_PROMPT,
    EVALUATOR_PROMPT,
    SYNTHESIZER_PROMPT,
    REFINER_PROMPT,
    FINAL_RESPONSE_TEMPLATE
)

# Gemini API 클라이언트
_client = None


def get_client():
    """Gemini API 클라이언트 반환"""
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    return _client


async def call_gemini(prompt: str) -> str:
    """Gemini API 비동기 호출"""
    client = get_client()
    response = await client.aio.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt,
        config={
            "temperature": 0,
            "max_output_tokens": 4096,
        }
    )
    return response.text


async def parse_query(state: AgentState) -> dict[str, Any]:
    """사용자 쿼리 분석 및 연구 계획 수립"""
    combined_prompt = f"""{QUERY_PARSER_PROMPT}

분석할 질문: {state['original_query']}"""

    response_text = await call_gemini(combined_prompt)

    try:
        content = response_text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        plan_data = json.loads(content.strip())
        research_plan = ResearchPlan(**plan_data)
    except Exception as e:
        research_plan = ResearchPlan(
            main_query=state['original_query'],
            sub_queries=[state['original_query']],
            search_strategies=["web", "kb"]
        )

    return {
        "research_plan": research_plan,
        "iteration_count": 0,
        "is_sufficient": False,
        "errors": []
    }


async def web_search(state: AgentState) -> dict[str, Any]:
    """웹 검색 수행"""
    from src.tools.tavily_search import search_3d_printing_web

    results = []
    plan = state.get("research_plan")

    if not plan:
        return {"web_results": [], "errors": ["No research plan"]}

    try:
        for query in plan.sub_queries[:3]:
            search_results = await search_3d_printing_web(query)
            for r in search_results:
                results.append(SearchResult(
                    source="web",
                    url=r.get("url", ""),
                    title=r.get("title", ""),
                    content=r.get("content", ""),
                    relevance_score=r.get("score", 0.5)
                ))
    except Exception as e:
        return {"web_results": [], "errors": [f"Web search error: {str(e)}"]}

    return {"web_results": results}


async def kb_search(state: AgentState) -> dict[str, Any]:
    """자체 지식베이스 검색"""
    from src.tools.knowledge_base import KnowledgeBase

    results = []
    plan = state.get("research_plan")

    if not plan:
        return {"kb_results": []}

    try:
        kb = KnowledgeBase()

        if plan.material_type:
            material_results = kb.get_material_guide(plan.material_type)
            if material_results:
                results.append(SearchResult(
                    source="kb",
                    url="internal://material_guide",
                    title=f"{plan.material_type} 가이드",
                    content=material_results,
                    relevance_score=0.9
                ))

        if plan.defect_type:
            defect_results = kb.get_defect_solution(plan.defect_type)
            if defect_results:
                results.append(SearchResult(
                    source="kb",
                    url="internal://defect_guide",
                    title=f"{plan.defect_type} 해결 가이드",
                    content=defect_results,
                    relevance_score=0.9
                ))

        similar_experiments = kb.search_similar_experiments(
            material=plan.material_type,
            defect=plan.defect_type
        )
        for exp in similar_experiments:
            results.append(SearchResult(
                source="kb",
                url=f"internal://experiment/{exp.get('experiment_id', 'unknown')}",
                title=f"실험 데이터: {exp.get('experiment_id', '')}",
                content=json.dumps(exp, ensure_ascii=False),
                relevance_score=0.85
            ))
    except Exception as e:
        return {"kb_results": [], "errors": [f"KB search error: {str(e)}"]}

    return {"kb_results": results}


async def paper_search(state: AgentState) -> dict[str, Any]:
    """학술 논문 검색"""
    from src.tools.tavily_search import search_3d_printing_papers

    results = []
    plan = state.get("research_plan")

    if not plan:
        return {"paper_results": []}

    if "paper" not in plan.search_strategies:
        return {"paper_results": []}

    try:
        query_parts = []
        if plan.material_type:
            query_parts.append(plan.material_type)
        if plan.defect_type:
            query_parts.append(plan.defect_type)
        query_parts.append("FDM optimization")

        query = " ".join(query_parts)
        paper_results = await search_3d_printing_papers(query)

        for r in paper_results:
            results.append(SearchResult(
                source="paper",
                url=r.get("url", ""),
                title=r.get("title", ""),
                content=r.get("content", ""),
                relevance_score=r.get("score", 0.5)
            ))
    except Exception as e:
        return {"paper_results": [], "errors": [f"Paper search error: {str(e)}"]}

    return {"paper_results": results}


async def evaluate_results(state: AgentState) -> dict[str, Any]:
    """검색 결과 충분성 평가"""
    all_results = (
        state.get("web_results", []) +
        state.get("kb_results", []) +
        state.get("paper_results", []) +
        state.get("community_results", [])
    )

    if not all_results:
        return {
            "is_sufficient": False,
            "confidence_score": 0.0,
            "missing_info": ["검색 결과 없음"],
            "iteration_count": state.get("iteration_count", 0) + 1
        }

    results_summary = "\n\n".join([
        f"[{r.source}] {r.title}\n{r.content[:300]}..."
        for r in all_results[:10]
    ])

    combined_prompt = f"""{EVALUATOR_PROMPT}

질문: {state['original_query']}

수집된 정보 ({len(all_results)}개):
{results_summary}"""

    response_text = await call_gemini(combined_prompt)

    try:
        content = response_text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        eval_data = json.loads(content.strip())
        is_sufficient = eval_data.get("is_sufficient", False)
        confidence = eval_data.get("confidence", 0.5)
        missing = eval_data.get("missing", [])
    except:
        is_sufficient = len(all_results) >= 5
        confidence = min(len(all_results) * 0.1, 0.8)
        missing = []

    return {
        "is_sufficient": is_sufficient,
        "confidence_score": confidence,
        "missing_info": missing,
        "iteration_count": state.get("iteration_count", 0) + 1
    }


async def refine_query(state: AgentState) -> dict[str, Any]:
    """쿼리 재구성"""
    missing_info = state.get("missing_info", [])
    plan = state.get("research_plan")

    if not plan:
        return {}

    prompt = REFINER_PROMPT.format(missing_info=", ".join(missing_info))

    combined_prompt = f"""{prompt}

원래 질문: {state['original_query']}
현재 쿼리들: {plan.sub_queries}"""

    response_text = await call_gemini(combined_prompt)

    try:
        content = response_text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        new_data = json.loads(content.strip())
        new_queries = new_data.get("new_queries", [])

        updated_plan = ResearchPlan(
            main_query=plan.main_query,
            sub_queries=plan.sub_queries + new_queries,
            search_strategies=plan.search_strategies,
            material_type=plan.material_type,
            defect_type=plan.defect_type,
            parameters_mentioned=plan.parameters_mentioned
        )
        return {"research_plan": updated_plan}
    except:
        return {}


async def synthesize(state: AgentState) -> dict[str, Any]:
    """수집된 정보 종합 및 추론"""
    all_results = (
        state.get("web_results", []) +
        state.get("kb_results", []) +
        state.get("paper_results", []) +
        state.get("community_results", [])
    )

    sorted_results = sorted(all_results, key=lambda x: x.relevance_score, reverse=True)

    results_text = "\n\n".join([
        f"[{r.source}] (관련도: {r.relevance_score:.2f})\nURL: {r.url}\n{r.content}"
        for r in sorted_results[:15]
    ])

    combined_prompt = f"""{SYNTHESIZER_PROMPT}

질문: {state['original_query']}

수집된 정보:
{results_text}"""

    response_text = await call_gemini(combined_prompt)

    try:
        content = response_text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        synth_data = json.loads(content.strip())
        synthesized = synth_data.get("synthesis", "")
        recommendations = [
            ParameterRecommendation(**r)
            for r in synth_data.get("recommendations", [])
        ]
    except Exception as e:
        synthesized = response_text
        recommendations = []

    return {
        "synthesized_knowledge": synthesized,
        "recommendations": recommendations,
    }


async def validate(state: AgentState) -> dict[str, Any]:
    """추천 검증"""
    VALID_RANGES = {
        "노즐 온도": (180, 300),
        "nozzle_temp": (180, 300),
        "베드 온도": (40, 120),
        "bed_temp": (40, 120),
        "출력 속도": (10, 200),
        "print_speed": (10, 200),
        "레이어 높이": (0.05, 0.5),
        "layer_height": (0.05, 0.5),
        "Retraction 거리": (0.5, 10),
        "retraction_distance": (0.5, 10),
        "Retraction 속도": (10, 100),
        "retraction_speed": (10, 100),
    }

    validated_recommendations = []
    for rec in state.get("recommendations", []):
        try:
            value_str = rec.recommended_value
            for unit in ["°C", "mm/s", "mm", "%"]:
                value_str = value_str.replace(unit, "")
            value_str = value_str.strip().split("-")[0]
            value = float(value_str)

            param_range = VALID_RANGES.get(rec.parameter)

            if param_range:
                if param_range[0] <= value <= param_range[1]:
                    validated_recommendations.append(rec)
                else:
                    rec.confidence *= 0.5
                    rec.reasoning += f" (주의: 일반적 범위 {param_range[0]}-{param_range[1]} 벗어남)"
                    validated_recommendations.append(rec)
            else:
                validated_recommendations.append(rec)
        except:
            validated_recommendations.append(rec)

    return {"recommendations": validated_recommendations}


async def generate_output(state: AgentState) -> dict[str, Any]:
    """최종 응답 생성"""
    recommendations = state.get("recommendations", [])
    all_results = (
        state.get("web_results", []) +
        state.get("kb_results", []) +
        state.get("paper_results", [])
    )

    unique_sources = []
    seen_urls = set()
    for r in all_results:
        if r.url and r.url not in seen_urls and not r.url.startswith("internal://"):
            unique_sources.append(r.url)
            seen_urls.add(r.url)
    unique_sources = unique_sources[:8]

    if recommendations:
        rec_table = "| 파라미터 | 현재값 | 추천값 | 신뢰도 |\n"
        rec_table += "|----------|--------|--------|--------|\n"
        for rec in recommendations:
            current = rec.current_value or "N/A"
            rec_table += f"| {rec.parameter} | {current} | {rec.recommended_value} | {rec.confidence:.0%} |\n"
    else:
        rec_table = "추천을 생성할 수 없습니다."

    detailed = "\n\n".join([
        f"**{r.parameter}**: {r.reasoning}"
        for r in recommendations[:5]
    ])

    sources_formatted = "\n".join([
        f"[{i+1}] {url}"
        for i, url in enumerate(unique_sources)
    ])

    final_response = FINAL_RESPONSE_TEMPLATE.format(
        synthesis=state.get("synthesized_knowledge", "분석 중..."),
        confidence=state.get("confidence_score", 0),
        recommendations_table=rec_table,
        detailed_reasoning=detailed or "상세 설명 없음",
        additional_tips="- 필라멘트 건조 권장\n- 베드 레벨링 확인",
        sources=sources_formatted or "소스 없음",
        num_sources=len(all_results),
        iterations=state.get("iteration_count", 1)
    )

    return {
        "final_response": final_response,
        "sources_cited": unique_sources
    }


def should_continue_research(state: AgentState) -> str:
    """추가 검색 필요 여부 결정"""
    if state.get("is_sufficient", False):
        return "synthesize"
    elif state.get("iteration_count", 0) >= 3:
        return "synthesize"
    else:
        return "refine"
