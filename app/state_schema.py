"""
Chapter 10 Agent State Schema

에이전트 워크플로우에서 공유할 state 구조를 정의합니다.
"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """상태 기반 수업 공지 Q&A 에이전트의 공통 state입니다."""

    user_question: str
    rewritten_question: str | None
    route: str | None
    route_reason: str | None
    selected_tool: str | None
    tool_arguments: dict[str, Any]
    tool_result: dict[str, Any]
    retrieved_results: list[dict[str, Any]]
    retrieval_status: str | None
    result_count: int
    needs_fallback: bool
    answer: str | None
    error: str | None
    logs: list[dict[str, Any]]


def create_initial_state(user_question: str) -> AgentState:
    """사용자 질문으로 초기 state를 생성합니다."""
    return {
        "user_question": user_question,
        "rewritten_question": None,
        "route": None,
        "route_reason": None,
        "selected_tool": None,
        "tool_arguments": {},
        "tool_result": {},
        "retrieved_results": [],
        "retrieval_status": None,
        "result_count": 0,
        "needs_fallback": False,
        "answer": None,
        "error": None,
        "logs": [],
    }


def summarize_state(state: AgentState) -> dict[str, Any]:
    """출력용으로 state의 핵심 필드만 요약합니다."""
    return {
        "user_question": state.get("user_question"),
        "rewritten_question": state.get("rewritten_question"),
        "route": state.get("route"),
        "route_reason": state.get("route_reason"),
        "selected_tool": state.get("selected_tool"),
        "result_count": state.get("result_count", 0),
        "retrieval_status": state.get("retrieval_status"),
        "needs_fallback": state.get("needs_fallback", False),
        "answer": state.get("answer"),
        "error": state.get("error"),
    }