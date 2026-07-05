"""
Chapter 10 Workflow Steps

상태 기반 수업 공지 Q&A 에이전트의 각 step을 정의합니다.
"""

import os
from typing import Any

from dotenv import load_dotenv

try:
    from .router import decide_route
    from .state_schema import AgentState
except ImportError:
    from router import decide_route
    from state_schema import AgentState


def load_dispatcher():
    """
    tool_dispatcher.py의 함수명이 버전에 따라 다를 수 있으므로
    dispatch_tool_call 또는 safe_dispatch_function_call 중 사용 가능한 함수를 불러옵니다.
    """
    try:
        from . import tool_dispatcher
    except ImportError:
        import tool_dispatcher

    if hasattr(tool_dispatcher, "dispatch_tool_call"):
        return tool_dispatcher.dispatch_tool_call

    if hasattr(tool_dispatcher, "safe_dispatch_function_call"):
        return tool_dispatcher.safe_dispatch_function_call

    raise ImportError(
        "tool_dispatcher.py에 dispatch_tool_call 또는 "
        "safe_dispatch_function_call 함수가 없습니다."
    )


dispatch_tool = load_dispatcher()

DEFAULT_TOP_K = 3


def load_default_top_k() -> int:
    """환경 변수에서 기본 top_k를 읽습니다."""
    load_dotenv()
    return int(os.getenv("DEFAULT_TOP_K", DEFAULT_TOP_K))


def analyze_question_step(state: AgentState) -> AgentState:
    """사용자 질문을 정리하고 rewritten_question에 저장합니다."""
    question = state.get("user_question", "")
    state["rewritten_question"] = question.strip()
    return state


def route_question_step(state: AgentState) -> AgentState:
    """질문을 보고 workflow route를 결정합니다."""
    question = state.get("rewritten_question") or state.get("user_question", "")
    route, reason = decide_route(question)

    state["route"] = route
    state["route_reason"] = reason

    return state


def search_step(state: AgentState) -> AgentState:
    """검색 route인 경우 tool dispatcher를 호출합니다."""
    if state.get("route") != "search":
        return state

    question = state.get("rewritten_question") or state.get("user_question", "")

    arguments = {
        "question": question,
        "top_k": load_default_top_k(),
    }

    function_call = {
        "name": "search_course_policy",
        "args": arguments,
    }

    dispatch_result = dispatch_tool(function_call)
    tool_result = dispatch_result.get("result", {}) if isinstance(dispatch_result, dict) else {}

    state["selected_tool"] = "search_course_policy"
    state["tool_arguments"] = arguments
    state["tool_result"] = dispatch_result
    state["retrieved_results"] = tool_result.get("results", []) if isinstance(tool_result, dict) else []
    state["result_count"] = len(state["retrieved_results"])

    return state


def evaluate_retrieval_step(state: AgentState) -> AgentState:
    """검색 결과가 충분한지 간단히 평가합니다."""
    if state.get("route") != "search":
        return state

    tool_result = state.get("tool_result", {})

    if isinstance(tool_result, dict) and not tool_result.get("is_success", True):
        state["retrieval_status"] = "error"
        state["needs_fallback"] = True
        state["error"] = str(tool_result.get("message") or tool_result.get("error_type"))
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


def choose_fallback_strategy(state: dict[str, Any]) -> str:
    """검색 평가 결과에 따라 fallback 전략을 반환합니다."""
    if state.get("retrieval_status") == "empty":
        return "clarify"

    if state.get("retrieval_status") == "error":
        return "retry_or_clarify"

    if state.get("needs_fallback"):
        return "broaden_search"

    return "use_answer_step"