import json
from typing import Any, Callable

from search_tools import (
    filter_course_policy_by_section,
    get_chapter_summary,
    search_course_policy,
    search_course_policy_by_keyword,
)
from tool_schemas import get_tool_declarations


ToolFunction = Callable[..., dict[str, Any]]


TOOL_REGISTRY: dict[str, ToolFunction] = {
    "search_course_policy": search_course_policy,
    "filter_course_policy_by_section": filter_course_policy_by_section,
    "search_course_policy_by_keyword": search_course_policy_by_keyword,
    "get_chapter_summary": get_chapter_summary,
}


def get_registered_tool_names() -> list[str]:
    """Tool Registry에 등록된 tool 이름 목록을 반환합니다."""
    return list(TOOL_REGISTRY.keys())


def get_registered_tool_function(tool_name: str) -> ToolFunction | None:
    """tool 이름으로 실제 실행 함수를 조회합니다."""
    return TOOL_REGISTRY.get(tool_name)


def is_tool_registered(tool_name: str) -> bool:
    """tool 이름이 Tool Registry에 등록되어 있는지 확인합니다."""
    return tool_name in TOOL_REGISTRY


def validate_tool_arguments(tool_name: str, arguments: dict[str, Any]) -> None:
    """
    Function Declaration의 required 정보를 기준으로 필수 인자가 있는지 확인합니다.

    이 함수는 간단한 검증만 수행합니다.
    실제 서비스에서는 타입 검증, enum 검증, 범위 검증 등을 더 엄격하게 처리할 수 있습니다.
    """
    declarations = get_tool_declarations()
    declaration = None

    for item in declarations:
        if item["name"] == tool_name:
            declaration = item
            break

    if declaration is None:
        raise ValueError(f"Function Declaration을 찾을 수 없습니다: {tool_name}")

    required_fields = declaration.get("parameters", {}).get("required", [])

    missing_fields = [
        field
        for field in required_fields
        if field not in arguments or arguments[field] in (None, "")
    ]

    if missing_fields:
        raise ValueError(
            f"필수 인자가 누락되었습니다. tool={tool_name}, missing={missing_fields}"
        )


def execute_registered_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    tool 이름과 arguments를 받아 Tool Registry에 등록된 실제 함수를 실행합니다.
    """
    tool_function = get_registered_tool_function(tool_name)

    if tool_function is None:
        raise ValueError(f"등록되지 않은 tool입니다: {tool_name}")

    validate_tool_arguments(tool_name, arguments)

    return tool_function(**arguments)


def get_tool_registry_summary() -> list[dict[str, Any]]:
    """Tool Registry와 Function Declaration 연결 상태를 요약합니다."""
    declarations = get_tool_declarations()
    registered_names = set(get_registered_tool_names())

    summary = []

    for declaration in declarations:
        tool_name = declaration["name"]

        summary.append(
            {
                "name": tool_name,
                "registered": tool_name in registered_names,
                "description": declaration.get("description", ""),
                "required": declaration.get("parameters", {}).get("required", []),
            }
        )

    return summary


def print_tool_registry_summary() -> None:
    """Tool Registry 상태를 보기 좋게 출력합니다."""
    print("Tool Registry 등록 상태")
    print("=" * 70)

    for item in get_tool_registry_summary():
        status = "등록됨" if item["registered"] else "미등록"

        print(f"\nTool: {item['name']}")
        print(f"Status: {status}")
        print(f"Required: {item['required']}")
        print(f"Description: {item['description']}")


def print_tool_result(result: dict[str, Any]) -> None:
    """tool 실행 결과를 보기 좋게 출력합니다."""
    print("\nTool 실행 결과")
    print("=" * 70)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    """
    Tool Registry 단독 실행 테스트입니다.

    Chapter 7 chunk 인덱싱이 먼저 완료되어 있어야 검색 tool이 정상 동작합니다.
    """
    print_tool_registry_summary()

    print("\n등록된 tool 실행 테스트")
    print("=" * 70)

    examples = [
        {
            "tool_name": "search_course_policy",
            "arguments": {
                "question": "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
                "top_k": 2,
            },
        },
        {
            "tool_name": "filter_course_policy_by_section",
            "arguments": {
                "question": "민감 정보는 어디에 저장해야 하나요?",
                "section": "4. API Key 보안 정책",
                "top_k": 2,
            },
        },
        {
            "tool_name": "search_course_policy_by_keyword",
            "arguments": {
                "keyword": "GitHub",
                "question": "GitHub 제출 기준을 알려줘.",
                "top_k": 2,
            },
        },
        {
            "tool_name": "get_chapter_summary",
            "arguments": {
                "chapter": "chapter08",
                "detail_level": "brief",
            },
        },
    ]

    for example in examples:
        tool_name = example["tool_name"]
        arguments = example["arguments"]

        print(f"\n실행 tool: {tool_name}")
        result = execute_registered_tool(tool_name, arguments)
        print_tool_result(result)


if __name__ == "__main__":
    main()
