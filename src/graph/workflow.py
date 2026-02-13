"""
LangGraph 워크플로우 조립
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .nodes import (
    parse_query,
    web_search,
    kb_search,
    paper_search,
    evaluate_results,
    refine_query,
    synthesize,
    validate,
    generate_output,
    should_continue_research
)


def create_research_agent():
    """
    Autonomous Research Agent 그래프 생성

    Flow:
    1. parse_query: 쿼리 분석 및 연구 계획 수립
    2. web_search, kb_search, paper_search: 병렬 검색
    3. evaluate_results: 결과 충분성 평가
    4. (조건부) refine_query → 재검색 OR synthesize
    5. validate: 추천 검증
    6. generate_output: 최종 응답 생성
    """

    # 그래프 초기화
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("parse_query", parse_query)
    workflow.add_node("web_search", web_search)
    workflow.add_node("kb_search", kb_search)
    workflow.add_node("paper_search", paper_search)
    workflow.add_node("evaluate_results", evaluate_results)
    workflow.add_node("refine_query", refine_query)
    workflow.add_node("synthesize", synthesize)
    workflow.add_node("validate", validate)
    workflow.add_node("generate_output", generate_output)

    # 엔트리 포인트
    workflow.set_entry_point("parse_query")

    # parse_query 후 병렬 검색으로 분기
    # LangGraph에서는 동일 소스에서 여러 타겟으로 add_edge하면 병렬 실행
    workflow.add_edge("parse_query", "web_search")
    workflow.add_edge("parse_query", "kb_search")
    workflow.add_edge("parse_query", "paper_search")

    # 모든 검색 결과를 evaluate_results로 수렴
    workflow.add_edge("web_search", "evaluate_results")
    workflow.add_edge("kb_search", "evaluate_results")
    workflow.add_edge("paper_search", "evaluate_results")

    # 조건부 분기: 충분하면 synthesize, 아니면 refine
    workflow.add_conditional_edges(
        "evaluate_results",
        should_continue_research,
        {
            "refine": "refine_query",
            "synthesize": "synthesize"
        }
    )

    # refine 후 다시 검색 (web만 재실행)
    workflow.add_edge("refine_query", "web_search")

    # 합성 → 검증 → 출력 → 종료
    workflow.add_edge("synthesize", "validate")
    workflow.add_edge("validate", "generate_output")
    workflow.add_edge("generate_output", END)

    # 메모리 체크포인터 (대화 상태 유지)
    memory = MemorySaver()

    # 그래프 컴파일
    app = workflow.compile(checkpointer=memory)

    return app


# 전역 에이전트 인스턴스
_agent = None


def get_agent():
    """싱글톤 에이전트 반환"""
    global _agent
    if _agent is None:
        _agent = create_research_agent()
    return _agent


async def run_research(query: str, thread_id: str = "default") -> str:
    """
    연구 에이전트 실행

    Args:
        query: 사용자 질문
        thread_id: 세션 ID (대화 추적용)

    Returns:
        최종 응답 문자열
    """
    agent = get_agent()

    config = {"configurable": {"thread_id": thread_id}}

    initial_state: AgentState = {
        "original_query": query,
        "research_plan": None,
        "web_results": [],
        "kb_results": [],
        "paper_results": [],
        "community_results": [],
        "iteration_count": 0,
        "is_sufficient": False,
        "confidence_score": 0.0,
        "missing_info": [],
        "synthesized_knowledge": "",
        "recommendations": [],
        "final_response": "",
        "sources_cited": [],
        "errors": []
    }

    result = await agent.ainvoke(initial_state, config)

    return result.get("final_response", "응답을 생성할 수 없습니다.")


async def run_research_stream(query: str, thread_id: str = "default"):
    """
    연구 에이전트 스트리밍 실행

    Yields:
        각 노드 실행 상태
    """
    agent = get_agent()

    config = {"configurable": {"thread_id": thread_id}}

    initial_state: AgentState = {
        "original_query": query,
        "research_plan": None,
        "web_results": [],
        "kb_results": [],
        "paper_results": [],
        "community_results": [],
        "iteration_count": 0,
        "is_sufficient": False,
        "confidence_score": 0.0,
        "missing_info": [],
        "synthesized_knowledge": "",
        "recommendations": [],
        "final_response": "",
        "sources_cited": [],
        "errors": []
    }

    async for event in agent.astream_events(initial_state, config, version="v2"):
        event_type = event.get("event", "")

        if event_type == "on_chain_start":
            node_name = event.get("name", "unknown")
            yield {"type": "start", "node": node_name}

        elif event_type == "on_chain_end":
            output = event.get("data", {}).get("output", {})
            if "final_response" in output:
                yield {"type": "complete", "response": output["final_response"]}
