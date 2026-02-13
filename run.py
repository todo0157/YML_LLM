#!/usr/bin/env python
"""
3D Print Research Agent 실행 스크립트
"""
import asyncio
import argparse
import os
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()


async def run_cli(query: str):
    """CLI 모드로 실행"""
    from src.graph.workflow import run_research

    print("=" * 60)
    print("3D Printing Autonomous Research Agent")
    print("=" * 60)
    print(f"\n질문: {query}\n")
    print("연구 중...")
    print("-" * 60)

    try:
        response = await run_research(query)
        print(response)
    except Exception as e:
        print(f"오류 발생: {e}")
        raise


async def run_interactive():
    """대화형 모드"""
    from src.graph.workflow import run_research

    print("=" * 60)
    print("3D Printing Autonomous Research Agent")
    print("대화형 모드 (종료: 'exit' 또는 'quit')")
    print("=" * 60)

    while True:
        try:
            query = input("\n질문: ").strip()

            if query.lower() in ["exit", "quit", "q"]:
                print("종료합니다.")
                break

            if not query:
                continue

            print("\n연구 중...")
            print("-" * 60)

            response = await run_research(query)
            print(response)

        except KeyboardInterrupt:
            print("\n종료합니다.")
            break
        except Exception as e:
            print(f"오류: {e}")


def run_server(port: int = 8000):
    """API 서버 실행"""
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )


def check_env():
    """환경 변수 확인"""
    required = ["ANTHROPIC_API_KEY", "TAVILY_API_KEY"]
    missing = []

    for var in required:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print("필수 환경 변수가 설정되지 않았습니다:")
        for var in missing:
            print(f"  - {var}")
        print("\n.env 파일을 생성하거나 환경 변수를 설정하세요.")
        print("예시:")
        print('  export ANTHROPIC_API_KEY="your-key"')
        print('  export TAVILY_API_KEY="your-key"')
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="3D Printing Autonomous Research Agent"
    )
    parser.add_argument(
        "mode",
        choices=["cli", "interactive", "server"],
        help="실행 모드 선택"
    )
    parser.add_argument(
        "-q", "--query",
        type=str,
        help="CLI 모드에서 사용할 질문"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="서버 포트 (기본: 8000)"
    )

    args = parser.parse_args()

    # 환경 변수 확인
    if not check_env():
        sys.exit(1)

    if args.mode == "cli":
        if not args.query:
            print("CLI 모드에서는 --query 옵션이 필요합니다.")
            print("예: python run.py cli --query 'PETG stringing 해결 방법'")
            sys.exit(1)
        asyncio.run(run_cli(args.query))

    elif args.mode == "interactive":
        asyncio.run(run_interactive())

    elif args.mode == "server":
        print(f"서버를 시작합니다. http://localhost:{args.port}")
        print(f"API 문서: http://localhost:{args.port}/docs")
        run_server(args.port)


if __name__ == "__main__":
    main()
