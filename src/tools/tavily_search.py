"""
Tavily 웹 검색 도구
"""
import os
from typing import Optional
from tavily import AsyncTavilyClient

# Tavily 클라이언트 초기화
_client: Optional[AsyncTavilyClient] = None


def get_tavily_client() -> AsyncTavilyClient:
    """Tavily 클라이언트 싱글톤"""
    global _client
    if _client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY 환경 변수가 설정되지 않았습니다.")
        _client = AsyncTavilyClient(api_key=api_key)
    return _client


async def search_3d_printing_web(
    query: str,
    max_results: int = 5
) -> list[dict]:
    """
    3D 프린팅 관련 웹 검색

    Args:
        query: 검색 쿼리
        max_results: 최대 결과 수

    Returns:
        검색 결과 리스트
    """
    client = get_tavily_client()

    # 도메인 특화 쿼리 강화
    enhanced_query = f"3D printing FDM {query}"

    try:
        response = await client.search(
            query=enhanced_query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=[
                "prusa3d.com",
                "help.prusa3d.com",
                "reddit.com/r/3Dprinting",
                "reddit.com/r/FixMyPrint",
                "all3dp.com",
                "simplify3d.com",
                "community.ultimaker.com",
                "matterhackers.com"
            ]
        )

        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "score": r.get("score", 0.5)
            })

        return results
    except Exception as e:
        print(f"Tavily search error: {e}")
        return []


async def search_3d_printing_papers(
    query: str,
    max_results: int = 3
) -> list[dict]:
    """
    3D 프린팅 관련 학술 논문 검색

    Args:
        query: 검색 쿼리
        max_results: 최대 결과 수

    Returns:
        논문 검색 결과
    """
    client = get_tavily_client()

    # 학술 사이트 대상 쿼리
    enhanced_query = f"FDM 3D printing {query} research paper"

    try:
        response = await client.search(
            query=enhanced_query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=[
                "arxiv.org",
                "ieee.org",
                "sciencedirect.com",
                "springer.com",
                "mdpi.com",
                "researchgate.net"
            ]
        )

        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "score": r.get("score", 0.5),
                "type": "academic"
            })

        return results
    except Exception as e:
        print(f"Tavily paper search error: {e}")
        return []


async def search_reddit_community(
    query: str,
    max_results: int = 5
) -> list[dict]:
    """
    Reddit 3D 프린팅 커뮤니티 검색

    Args:
        query: 검색 쿼리
        max_results: 최대 결과 수

    Returns:
        Reddit 검색 결과
    """
    client = get_tavily_client()

    enhanced_query = f"site:reddit.com/r/3Dprinting OR site:reddit.com/r/FixMyPrint {query}"

    try:
        response = await client.search(
            query=enhanced_query,
            search_depth="basic",
            max_results=max_results
        )

        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "score": r.get("score", 0.5),
                "type": "community"
            })

        return results
    except Exception as e:
        print(f"Reddit search error: {e}")
        return []
