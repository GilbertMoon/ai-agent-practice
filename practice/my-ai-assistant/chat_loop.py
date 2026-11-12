"""Lesson 02 — repeated CLI questions, using the shared client from main.py.

Each question is independent. Persistent context arrives in Lesson 11.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

from main import ChatClient, load_local_env, make_client

EXIT_WORDS = {"exit", "quit"}
HELP_WORDS = {"help", "도움말"}


def serve(
    client: ChatClient,
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> None:
    write("My AI Assistant — 대화 실습")
    write("질문을 입력하세요. 종료: exit/quit, 도움말: help")
    write("현재 버전에서는 각 질문을 독립적으로 처리합니다.")
    while True:
        try:
            question = read("\n질문> ").strip()
        except (EOFError, KeyboardInterrupt):
            write("\n대화를 종료합니다.")
            return
        if question.lower() in EXIT_WORDS:
            write("대화를 종료합니다.")
            return
        if question.lower() in HELP_WORDS:
            write("질문을 입력하면 응답합니다. 빈 질문은 보내지 않습니다. 종료: exit/quit")
            continue
        if not question:
            write("질문을 입력해 주세요.")
            continue
        try:
            reply = client.ask(question)
        except Exception as exc:
            # Credentials and untrusted SDK error messages should not be echoed.
            write(f"요청을 처리하지 못했습니다. 오류 유형: {type(exc).__name__}")
            continue
        write(f"\n답변> {reply.text}")
        if reply.measurement_mode == "live":
            write(
                "사용량> "
                f"model={reply.model}, input={reply.input_tokens}, "
                f"output={reply.output_tokens}, cached_input={reply.cached_input_tokens}"
            )
        else:
            write("현재 Mock 모드: 실제 API 호출·토큰 측정 없음")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lesson 02 My AI Assistant chat loop")
    parser.add_argument("--mode", choices=("mock", "live"), default="mock")
    args = parser.parse_args(argv)
    try:
        if args.mode == "live":
            load_local_env()
        client = make_client(args.mode)
    except (ValueError, RuntimeError) as exc:
        print(f"설정 오류: {exc}", file=sys.stderr)
        return 2
    serve(client)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
