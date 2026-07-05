"""
Chapter 12 Shared State

멀티 에이전트가 공유할 state 구조와 초기화 함수를 정의합니다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict


class MultiAgentState(TypedDict, total=False):
    """멀티 에이전트 협업 과정에서 공유되는 state입니다."""

    user_request: str
    plan: list[str]
    research_notes: list[str]
    draft_answer: str
    review_feedback: list[str]
    final_answer: str
    revision_count: int
    memory_context: str
    logs: list[dict[str, Any]]
    error: str | None


def now_iso() -> str:
    """현재 시각을 ISO 문자열로 반환합니다."""
    return datetime.now().isoformat(timespec="seconds")


def create_initial_state(user_request: str, memory_context: str = "") -> MultiAgentState:
    """사용자 요청으로 초기 shared state를 생성합니다."""
    return {
        "user_request": user_request.strip(),
        "plan": [],
        "research_notes": [],
        "draft_answer": "",
        "review_feedback": [],
        "final_answer": "",
        "revision_count": 0,
        "memory_context": memory_context.strip(),
        "logs": [],
        "error": None,
    }


def summarize_state(state: MultiAgentState) -> dict[str, Any]:
    """shared state의 핵심 결과만 요약합니다."""
    return {
        "user_request": state.get("user_request", ""),
        "plan_count": len(state.get("plan", [])),
        "research_note_count": len(state.get("research_notes", [])),
        "has_draft_answer": bool(state.get("draft_answer")),
        "review_feedback_count": len(state.get("review_feedback", [])),
        "has_final_answer": bool(state.get("final_answer")),
        "revision_count": state.get("revision_count", 0),
        "log_count": len(state.get("logs", [])),
        "error": state.get("error"),
    }