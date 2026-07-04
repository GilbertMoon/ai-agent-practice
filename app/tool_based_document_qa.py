import json
from typing import Any

from function_result_response import run_tool_calling_round

DEFAULT_QUESTIONS = [
    "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
    "GitHub 제출 기준을 알려주세요.",
    "API Key는 어디에 저장해야 하나요?",
    "Chapter 8에서는 무엇을 배웠나요?",
]


def format_function_call(function_call: dict[str, Any] | None) -> str:
    """function_call 정보를 보기 좋은 문자열로 변환합니다."""
    if function_call is None:
        return "사용된 function_call이 없습니다."

    return json.dumps(function_call, ensure_ascii=False, indent=2)


def format_dispatch_summary(dispatch_response: dict[str, Any] | None) -> str:
    """Tool Dispatcher 실행 결과를 요약합니다."""
    if dispatch_response is None:
        return "Tool Dispatcher가 실행되지 않았습니다."

    if not dispatch_response.get("is_success"):
        error = dispatch_response.get("error", {})
        return (
            "Tool 실행 실패\n"
            f"- error_type: {error.get('type')}\n"
            f"- message: {error.get('message')}"
        )

    result = dispatch_response.get("result", {})
    tool_name = dispatch_response.get("tool_name")
    result_count = result.get("result_count")

    if result_count is not None:
        return (
            "Tool 실행 성공\n"
            f"- tool_name: {tool_name}\n"
            f"- result_count: {result_count}"
        )

    return (
        "Tool 실행 성공\n"
        f"- tool_name: {tool_name}"
    )


def print_qa_result(result: dict[str, Any]) -> None:
    """검색 도구 기반 Q&A 실행 결과를 출력합니다."""
    print("=" * 80)
    print("검색 도구 기반 Q&A 결과")
    print("=" * 80)
    print(f"질문: {result['question']}")
    print(f"tool 사용 여부: {result['used_tool']}")
    print()
    print("[선택된 function_call]")
    print(format_function_call(result.get("function_call")))
    print()
    print("[Tool Dispatcher 실행 요약]")
    print(format_dispatch_summary(result.get("dispatch_response")))
    print()
    print("[최종 답변]")
    print(result.get("final_answer") or "최종 답변이 비어 있습니다.")
    print("=" * 80)
    print()


def run_single_question(question: str) -> dict[str, Any]:
    """
    질문 하나에 대해 검색 도구 기반 Q&A를 실행합니다.

    내부적으로 다음 흐름을 수행합니다.

    사용자 질문
    → Gemini가 필요한 tool 선택
    → function_call 생성
    → Tool Dispatcher 실행
    → function_response를 모델에 다시 전달
    → 최종 답변 생성
    """
    return run_tool_calling_round(question)


def run_demo_questions() -> None:
    """기본 예제 질문 여러 개를 순서대로 실행합니다."""
    for question in DEFAULT_QUESTIONS:
        result = run_single_question(question)
        print_qa_result(result)


def run_interactive_loop() -> None:
    """사용자가 직접 질문을 입력하는 간단한 Q&A 루프입니다."""
    print("검색 도구 기반 Q&A를 시작합니다.")
    print("종료하려면 q 또는 quit를 입력하세요.")
    print()

    while True:
        question = input("질문을 입력하세요: ").strip()

        if question.lower() in {"q", "quit", "exit"}:
            print("Q&A를 종료합니다.")
            break

        if not question:
            print("질문이 비어 있습니다. 다시 입력해 주세요.")
            continue

        result = run_single_question(question)
        print_qa_result(result)


def main() -> None:
    """
    tool_based_document_qa.py 실행 진입점입니다.

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
