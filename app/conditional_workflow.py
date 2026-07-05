"""
Chapter 10 Conditional Workflow

route와 fallback 여부에 따라 필요한 step만 실행하는 조건 분기 workflow입니다.
"""

import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "app"

from .answer_generator import answer_step
from .fallback_handler import fallback_step
from .router import (
    decide_route,
    is_clarification_route,
    is_direct_answer_route,
    is_search_route,
)
from .state_schema import create_initial_state, summarize_state

try:
    from .workflow_logger import log_step
except ImportError:
    def log_step(state, step_name: str, write_file: bool = True):
        logs = state.setdefault("logs", [])
        logs.append({"step": step_name, "write_file": write_file})


def analyze_question_step(state):
    """사용자 질문을 정리하고 rewritten_question에 저장합니다."""
    question = state.get("user_question", "")
    state["rewritten_question"] = question.strip()
    return state


def route_question_step(state):
    """질문을 보고 workflow route를 결정합니다."""
    question = state.get("rewritten_question") or state.get("user_question", "")
    route, reason = decide_route(question)
    state["route"] = route
    state["route_reason"] = reason
    return state


def clarification_step(state):
    """질문이 비어 있거나 불명확할 때 clarification 답변을 생성합니다."""
    state["answer"] = "질문이 비어 있거나 불명확합니다. 알고 싶은 내용을 한 문장으로 입력해 주세요."
    return state


def evaluate_retrieval_step(state):
    """검색 결과가 충분한지 간단히 평가합니다."""
    if state.get("route") != "search":
        return state

    tool_result = state.get("tool_result", {})

    if isinstance(tool_result, dict) and not tool_result.get("is_success", True):
        state["retrieval_status"] = "error"
        state["needs_fallback"] = True
        error_info = tool_result.get("error")
        state["error"] = str(error_info if error_info is not None else tool_result)
        return state

    results = state.get("retrieved_results", [])

    if not results:
        state["retrieval_status"] = "empty"
        state["needs_fallback"] = True
        state["result_count"] = 0
    else:
        state["retrieval_status"] = "ok"
        state["needs_fallback"] = False
        state["result_count"] = len(results)

    return state


def search_step(state):
    """검색 route인 경우 workflow_steps.search_step을 지연 로딩해 실행합니다."""
    if state.get("route") != "search":
        return state

    try:
        from .workflow_steps import search_step as workflow_search_step
    except Exception as error:
        state["tool_result"] = {
            "is_success": False,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
        }
        state["retrieved_results"] = []
        state["result_count"] = 0
        return state

    try:
        return workflow_search_step(state)
    except Exception as error:
        state["tool_result"] = {
            "is_success": False,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
        }
        state["retrieved_results"] = []
        state["result_count"] = 0
        return state


SAMPLE_QUESTIONS = [
    "미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?",
    "보안 안내에서 민감 정보 저장 방법을 알려줘.",
    "RAG가 무엇인가요?",
    "",
]


def run_conditional_workflow(user_question: str, write_log: bool = True):
    """조건 분기 기반 workflow를 실행합니다."""
    state = create_initial_state(user_question)

    state = analyze_question_step(state)
    log_step(state, "analyze_question_step", write_file=write_log)

    state = route_question_step(state)
    log_step(state, "route_question_step", write_file=write_log)

    route = state.get("route")

    if is_search_route(route):
        state = search_step(state)
        log_step(state, "search_step", write_file=write_log)

        state = evaluate_retrieval_step(state)
        log_step(state, "evaluate_retrieval_step", write_file=write_log)

        if state.get("needs_fallback"):
            state = fallback_step(state)
            log_step(state, "fallback_step", write_file=write_log)
        else:
            state = answer_step(state)
            log_step(state, "answer_step", write_file=write_log)

    elif is_direct_answer_route(route):
        state = answer_step(state)
        log_step(state, "direct_answer_step", write_file=write_log)

    elif is_clarification_route(route):
        state = clarification_step(state)
        log_step(state, "clarification_step", write_file=write_log)

    else:
        state["error"] = f"알 수 없는 route입니다: {route}"
        state = fallback_step(state)
        log_step(state, "unknown_route_fallback_step", write_file=write_log)

    return state


def run_sample_questions() -> None:
    """샘플 질문으로 조건 분기 workflow를 실행합니다."""
    for question in SAMPLE_QUESTIONS:
        print("\n" + "=" * 80)
        print(f"질문: {question!r}")
        print("=" * 80)
        state = run_conditional_workflow(question)
        print(json.dumps(summarize_state(state), ensure_ascii=False, indent=2))


def main() -> None:
    """대화형으로 조건 분기 workflow를 실행합니다."""
    print("Chapter 10 Conditional Workflow")
    print("샘플 실행은 sample, 종료는 exit 또는 quit를 입력하세요.")

    while True:
        question = input("\n질문을 입력하세요: ").strip()
        if question.lower() in {"exit", "quit"}:
            print("프로그램을 종료합니다.")
            break

        if question == "sample":
            run_sample_questions()
            continue

        state = run_conditional_workflow(question)
        print("\n[최종 state 요약]")
        print(json.dumps(summarize_state(state), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()