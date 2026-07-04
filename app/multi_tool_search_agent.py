import json
from typing import Any

from function_result_response import run_tool_calling_round
from tool_registry import get_registered_tool_names
from tool_schemas import get_tool_declarations

DEFAULT_QUESTIONS = [
    "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
    "API Key 보안 정책만 기준으로 설명해 주세요.",
    "GitHub라는 단어가 들어간 제출 기준을 알려주세요.",
    "Chapter 8 내용을 간단히 요약해 주세요.",
]


def get_available_tool_summary() -> list[dict[str, Any]]:
    """현재 모델에 제공 가능한 tool 목록과 설명을 정리합니다."""
    declarations = get_tool_declarations()
    registered_tool_names = set(get_registered_tool_names())

    tool_summary = []

    for declaration in declarations:
        tool_name = declaration["name"]
        tool_summary.append(
            {
                "name": tool_name,
                "registered": tool_name in registered_tool_names,
                "description": declaration.get("description", ""),
                "required": declaration.get("parameters", {}).get("required", []),
            }
        )

    return tool_summary


def print_available_tools() -> None:
    """현재 제공되는 여러 검색 tool 목록을 출력합니다."""
    print("=" * 80)
    print("제공 가능한 검색 Tool 목록")
    print("=" * 80)

    for item in get_available_tool_summary():
        status = "등록됨" if item["registered"] else "미등록"
        print(f"- {item['name']}")
        print(f"  status: {status}")
        print(f"  required: {item['required']}")
        print(f"  description: {item['description']}")
        print()

    print("=" * 80)
    print()


def format_function_call(function_call: dict[str, Any] | None) -> str:
    """선택된 function_call을 보기 좋게 출력하기 위한 문자열로 변환합니다."""
    if function_call is None:
        return "선택된 function_call이 없습니다."
    return json.dumps(function_call, ensure_ascii=False, indent=2)


def extract_tool_result_summary(dispatch_response: dict[str, Any] | None) -> str:
    """tool 실행 결과를 짧게 요약합니다."""
    if dispatch_response is None:
        return "tool이 실행되지 않았습니다."

    if not dispatch_response.get("is_success"):
        error = dispatch_response.get("error", {})
        return (
            "tool 실행 실패\n"
            f"- error_type: {error.get('type')}\n"
            f"- message: {error.get('message')}"
        )

    tool_name = dispatch_response.get("tool_name")
    result = dispatch_response.get("result", {})
    result_count = result.get("result_count")

    lines = [
        "tool 실행 성공",
        f"- tool_name: {tool_name}",
    ]

    if result_count is not None:
        lines.append(f"- result_count: {result_count}")

    if result.get("summary"):
        lines.append(f"- summary: {result['summary']}")

    return "\n".join(lines)


def print_agent_result(result: dict[str, Any]) -> None:
    """여러 tool 기반 agent 실행 결과를 출력합니다."""
    print("=" * 80)
    print("Multi Tool Search Agent 실행 결과")
    print("=" * 80)
    print(f"질문: {result['question']}")
    print(f"tool 사용 여부: {result['used_tool']}")
    print()
    print("[LLM이 선택한 function_call]")
    print(format_function_call(result.get("function_call")))
    print()
    print("[Tool Dispatcher 실행 요약]")
    print(extract_tool_result_summary(result.get("dispatch_response")))
    print()
    print("[최종 답변]")
    print(result.get("final_answer") or "최종 답변이 비어 있습니다.")
    print("=" * 80)
    print()


def run_multi_tool_agent(question: str) -> dict[str, Any]:
    """
    여러 tool을 제공한 상태에서 질문 하나를 처리합니다.
    실제 tool 선택은 Gemini가 수행합니다.
    Python 코드는 모델이 선택한 function_call을 검증하고 실행합니다.
    """
    return run_tool_calling_round(question)


def run_demo_questions() -> None:
    """질문 유형별로 어떤 tool이 선택되는지 확인합니다."""
    print_available_tools()
    for question in DEFAULT_QUESTIONS:
        result = run_multi_tool_agent(question)
        print_agent_result(result)


def run_interactive_loop() -> None:
    """사용자가 직접 질문을 입력하며 여러 tool 선택을 확인합니다."""
    print_available_tools()
    print("Multi Tool Search Agent를 시작합니다.")
    print("종료하려면 q 또는 quit를 입력하세요.")
    print()

    while True:
        question = input("질문을 입력하세요: ").strip()
        if question.lower() in {"q", "quit", "exit"}:
            print("Multi Tool Search Agent를 종료합니다.")
            break
        if not question:
            print("질문이 비어 있습니다. 다시 입력해 주세요.")
            continue
        result = run_multi_tool_agent(question)
        print_agent_result(result)


def main() -> None:
    """
    multi_tool_search_agent.py 실행 진입점입니다.

    실행 전 준비:
    1. .env에 GEMINI_API_KEY 설정
    2. Chapter 7 chunk 인덱싱 완료
    """
    print("실행 모드를 선택하세요.")
    print("1. 예제 질문 실행")
    print("2. 직접 질문 입력")
    print()

    mode = input("선택 [1]: ").strip()
    if not mode:
        mode = "1"

    if mode == "1":
        run_demo_questions()
    elif mode == "2":
        run_interactive_loop()
    else:
        print("지원하지 않는 모드입니다. 1 또는 2를 입력하세요.")


if __name__ == "__main__":
    main()
