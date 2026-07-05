"""
Chapter 12 Reviewer Agent

Writer Agent가 만든 초안을 검토하고 개선 feedback을 생성합니다.
"""

from __future__ import annotations

from shared_state import MultiAgentState


REQUIRED_NOTICE_ITEMS = ["제출 항목", "제출 형식", "마감일", "평가 기준"]


def review_draft(user_request: str, research_notes: list[str], draft_answer: str) -> list[str]:
    """초안의 누락, 형식, 근거 문제를 규칙 기반으로 검토합니다."""
    feedback = []

    if not draft_answer.strip():
        return ["초안이 비어 있습니다."]

    if len(research_notes) < 2:
        feedback.append("research_notes가 부족합니다. 근거 또는 확인 항목을 보강해야 합니다.")

    if any(keyword in user_request for keyword in ["학생", "안내문", "공지", "과제", "제출"]):
        for item in REQUIRED_NOTICE_ITEMS:
            if item not in draft_answer and item not in "\n".join(research_notes):
                feedback.append(f"{item}이 명확히 정리되어 있지 않습니다.")

    if "확인 필요" not in draft_answer:
        feedback.append("불확실한 항목은 '확인 필요'로 표시하는 것이 좋습니다.")

    if len(draft_answer) > 1800:
        feedback.append("답변이 길 수 있으므로 학생용 안내문은 더 간결하게 줄이는 것이 좋습니다.")

    if not feedback:
        feedback.append("초안이 사용자 요청을 충족합니다.")

    return feedback


def has_actionable_feedback(feedback: list[str]) -> bool:
    """수정이 필요한 feedback이 있는지 확인합니다."""
    return any("충족합니다" not in item for item in feedback)


def reviewer_agent(state: MultiAgentState) -> MultiAgentState:
    """Reviewer Agent 실행 함수입니다."""
    state["review_feedback"] = review_draft(
        user_request=state.get("user_request", ""),
        research_notes=state.get("research_notes", []),
        draft_answer=state.get("draft_answer", ""),
    )
    return state