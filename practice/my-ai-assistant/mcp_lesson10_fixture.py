"""Lesson 10 fixture: direct local function calls; NOT an MCP session."""
import argparse
from mcp_lesson10_logic import add_numbers, find_notice, public_notice, lesson_prompt


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lesson 10 fixture; no MCP SDK needed")
    parser.add_argument("action", choices=("list", "add", "search", "resource", "prompt"))
    parser.add_argument("--a", type=int, default=12)
    parser.add_argument("--b", type=int, default=30)
    parser.add_argument("--query", default="과제 제출")
    parser.add_argument("--topic", default="MCP")
    args = parser.parse_args(argv)
    print("[FIXTURE] 함수 직접 실행. MCP 프로토콜 통신 아님, model_api_calls=0")
    try:
        if args.action == "list":
            print("[TOOLS] add_numbers, find_notice")
            print("[RESOURCES] lesson10://public-notice")
            print("[PROMPTS] explain_topic")
        elif args.action == "add":
            print("[RESULT]", add_numbers(args.a, args.b))
        elif args.action == "search":
            print("[RESULT]", find_notice(args.query))
        elif args.action == "resource":
            print("[RESOURCE]", public_notice())
        else:
            print("[PROMPT]", lesson_prompt(args.topic))
        return 0
    except ValueError as exc:
        print(f"설정 오류: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
