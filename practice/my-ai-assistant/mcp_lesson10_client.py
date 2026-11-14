"""Lesson 10 real MCP client: launches bundled read-only stdio server.

Unlike fixture, this uses an actual MCP SDK session but NOT an LLM/API.
"""
from __future__ import annotations
import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERVER = ROOT / "mcp_lesson10_server.py"
RESOURCE_URI = "lesson10://public-notice"
ALLOW = {"add_numbers", "find_notice"}


async def run(action: str, a: int, b: int, query: str, topic: str) -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], cwd=str(ROOT))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            if action == "list":
                result = await session.list_tools()
                print("[MCP_TOOLS] " + ", ".join(t.name for t in result.tools))
                return
            if action == "add":
                result = await session.call_tool("add_numbers", arguments={"a": a, "b": b})
                print("[MCP_CALL] add_numbers")
                print("[MCP_RESULT] " + str(result.structuredContent or result.content))
                return
            if action == "search":
                result = await session.call_tool("find_notice", arguments={"query": query})
                print("[MCP_CALL] find_notice")
                print("[MCP_RESULT] " + str(result.structuredContent or result.content))
                return
            if action == "resource":
                result = await session.read_resource(RESOURCE_URI)
                print("[MCP_RESOURCE] " + RESOURCE_URI)
                for item in result.contents:
                    if hasattr(item, "text"):
                        print(item.text)
                return
            result = await session.get_prompt("explain_topic", arguments={"topic": topic})
            print("[MCP_PROMPT] explain_topic")
            for message in result.messages:
                if hasattr(message.content, "text"):
                    print(message.content.text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lesson 10 local stdio MCP client")
    parser.add_argument("action", choices=("list", "add", "search", "resource", "prompt"))
    parser.add_argument("--a", type=int, default=12)
    parser.add_argument("--b", type=int, default=30)
    parser.add_argument("--query", default="과제 제출")
    parser.add_argument("--topic", default="MCP")
    args = parser.parse_args(argv)
    try:
        if args.action == "add" and (abs(args.a) > 100000 or abs(args.b) > 100000):
            raise ValueError("정수 범위 초과")
        if args.action == "search" and not 1 <= len(args.query.strip()) <= 100:
            raise ValueError("검색어 길이는 1~100자입니다.")
        if args.action == "prompt" and not 1 <= len(args.topic.strip()) <= 80:
            raise ValueError("topic 길이는 1~80자입니다.")
        asyncio.run(run(args.action, args.a, args.b, args.query, args.topic))
        print("[MCP] 실제 로컬 서버 통신 완료; model_api_calls=0")
        return 0
    except ValueError as exc:
        print(f"설정 오류: {exc}")
        return 2
    except ImportError:
        print("설정 오류: MCP SDK가 없습니다. requirements-lesson10.txt를 설치하세요.")
        return 2
    except Exception as exc:
        print(f"실행 오류: {type(exc).__name__} (비밀정보 비표시)")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
