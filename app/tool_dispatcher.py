import json
from typing import Any

from argument_validator import (
    ArgumentValidationError,
    validate_function_call,
)
from tool_registry import (
    execute_registered_tool,
    get_registered_tool_names,
    is_tool_registered,
)


class ToolDispatchError(RuntimeError):
    """Tool Dispatcher 실행 중 발생한 오류입니다."""


def build_success_response(
    tool_name: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """tool 실행 성공 응답을 표준 형식으로 만듭니다."""
    return {
        "is_success": True,
        "error": None,
        "tool_name": tool_name,
        "arguments": arguments,
        "result": result,
    }


def build_error_response(
    tool_name: str | None,
    arguments: dict[str, Any] | None,
    error: Exception,
) -> dict[str, Any]:
    """tool 실행 실패 응답을 표준 형식으로 만듭니다."""
    return {
        "is_success": False,
        "error": {
            "type": type(error).__name__,
            "message": str(error),
        },
        "tool_name": tool_name,
        "arguments": arguments or {},
        "result": None,
    }


def dispatch_function_call(function_call: dict[str, Any]) -> dict[str, Any]:
    """
    LLM이 생성한 function_call을 검증한 뒤 실제 tool 함수로 전달합니다.

    예상 입력 형식:
    {
        "name": "search_course_policy",
        "args": {
            "question": "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
            "top_k": 3
        }
    }

    처리 순서:
    1. function_call 구조 검증
    2. tool 이름 검증
    3. arguments 검증 및 기본값 보완
    4. Tool Registry에서 실제 함수 조회
    5. 실제 tool 함수 실행
    6. 실행 결과 반환
    """
    validated_call = validate_function_call(function_call)

    tool_name = validated_call["name"]
    arguments = validated_call["args"]

    if not is_tool_registered(tool_name):
        raise ToolDispatchError(
            f"Function Declaration에는 있지만 Tool Registry에는 등록되지 않은 tool입니다: {tool_name}"
        )

    result = execute_registered_tool(
        tool_name=tool_name,
        arguments=arguments,
    )

    return build_success_response(
        tool_name=tool_name,
        arguments=arguments,
        result=result,
    )


def safe_dispatch_function_call(function_call: dict[str, Any]) -> dict[str, Any]:
    """
    예외를 밖으로 던지지 않고 dispatch 결과를 dict로 반환합니다.

    실제 agent에서는 LLM이 잘못된 tool 이름이나 arguments를 만들 수 있으므로
    안전한 실행 래퍼를 두는 것이 좋습니다.
    """
    tool_name = None
    arguments = None

    if isinstance(function_call, dict):
        tool_name = function_call.get("name")
        arguments = function_call.get("args", {})

    try:
        return dispatch_function_call(function_call)

    except (ArgumentValidationError, ToolDispatchError, ValueError, RuntimeError) as error:
        return build_error_response(
            tool_name=tool_name,
            arguments=arguments,
            error=error,
        )


def dispatch_function_calls(function_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """여러 개의 function call을 순서대로 dispatch합니다."""
    responses = []

    for function_call in function_calls:
        response = safe_dispatch_function_call(function_call)
        responses.append(response)

    return responses


def print_dispatch_response(response: dict[str, Any]) -> None:
    """Tool Dispatcher 실행 결과를 보기 좋게 출력합니다."""
    print("=" * 70)

    if response["is_success"]:
        print("Tool Dispatch 성공")
    else:
        print("Tool Dispatch 실패")

    print("=" * 70)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    print()


def print_registered_tools() -> None:
    """현재 Tool Registry에 등록된 tool 목록을 출력합니다."""
    print("현재 등록된 tool 목록")
    print("=" * 70)

    for tool_name in get_registered_tool_names():
        print(f"- {tool_name}")

    print()


def main() -> None:
    """
    tool_dispatcher.py 단독 실행 테스트입니다.

    검색 tool을 실행하려면 Chapter 7 chunk 인덱싱이 먼저 완료되어 있어야 합니다.
    """
    print_registered_tools()

    examples = [
        {
            "name": "get_chapter_summary",
            "args": {
                "chapter": "chapter08",
                "detail_level": "brief",
            },
        },
        {
            "name": "search_course_policy",
            "args": {
                "question": "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
                "top_k": 2,
            },
        },
        {
            "name": "search_course_policy_by_keyword",
            "args": {
                "keyword": "GitHub",
                "question": "GitHub 제출 기준을 알려줘.",
            },
        },
        {
            "name": "get_chapter_summary",
            "args": {
                "chapter": "chapter08",
                "detail_level": "very_long",
            },
        },
        {
            "name": "search_course_policy",
            "args": {
                "top_k": 3,
            },
        },
        {
            "name": "unknown_tool",
            "args": {
                "question": "테스트 질문입니다.",
            },
        },
    ]

    responses = dispatch_function_calls(examples)

    for response in responses:
        print_dispatch_response(response)


if __name__ == "__main__":
    main()
