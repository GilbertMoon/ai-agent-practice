"""
Chapter 12 Writer Agent

plan과 research_notes를 바탕으로 사용자용 초안과 수정본을 작성합니다.
"""

from __future__ import annotations

from shared_state import MultiAgentState


DEFAULT_NOTICE_TEMPLATE = """
안녕하세요. 아래와 같이 안내드립니다.

## 1. 핵심 안내
{summary}

## 2. 확인된 내용
{notes}

## 3. 확인 필요 사항
{unknowns}
""".strip()


def build_summary(user_request: str) -> str:
    """사용자 요청을 안내문용 요약 문장으로 변환합니다."""
    if any(keyword in user_request for keyword in ["학생", "안내문", "공지"]):
        return "학생들이 혼동하지 않도록 주요 조건을 항목별로 정리합니다."

    if any(keyword in user_request for keyword in ["과제", "제출"]):
        return "과제 제출과 관련된 핵심 내용을 정리합니다."

    return "요청하신 내용을 바탕으로 핵심 사항을 정리합니다."


def format_notes(notes: list[str]) -> str:
    """research notes를 bullet list로 변환합니다."""
    if not notes:
        return "- 현재 확인된 근거가 부족합니다."
    return "\n".join(f"- {note}" for note in notes)


def detect_unknowns(notes: list[str]) -> list[str]:
    """research notes 기준으로 확인이 필요한 항목을 추정합니다."""
    joined = "\n".join(notes)
    unknowns = []

    for label in ["마감일", "제출 형식", "평가 기준", "제출 항목"]:
        if label not in joined:
            unknowns.append(f"{label}: 확인 필요")

    return unknowns


def build_draft_answer(state: MultiAgentState) -> str:
    """state를 바탕으로 draft answer를 생성합니다."""
    user_request = state.get("user_request", "")
    notes = state.get("research_notes", [])
    summary = build_summary(user_request)
    unknowns = detect_unknowns(notes)

    return DEFAULT_NOTICE_TEMPLATE.format(
        summary=summary,
        notes=format_notes(notes),
        unknowns="\n".join(f"- {item}" for item in unknowns) if unknowns else "- 현재 추가 확인이 필요한 항목은 없습니다.",
    )


def writer_agent(state: MultiAgentState) -> MultiAgentState:
    """Writer Agent 실행 함수입니다."""
    state["draft_answer"] = build_draft_answer(state)
    return state


def revise_answer(state: MultiAgentState) -> MultiAgentState:
    """Reviewer feedback을 반영해 draft_answer를 수정합니다."""
    draft = state.get("draft_answer", "")
    feedback = state.get("review_feedback", [])

    if not feedback:
        state["final_answer"] = draft
        return state

    revision_note = "\n\n## 4. 검토 반영 사항\n" + "\n".join(f"- {item}" for item in feedback)
    state["draft_answer"] = draft + revision_note
    state["revision_count"] = int(state.get("revision_count", 0)) + 1
    return state


def finalize_answer(state: MultiAgentState) -> MultiAgentState:
    """최종 답변을 확정합니다."""
    state["final_answer"] = state.get("draft_answer", "")
    return state