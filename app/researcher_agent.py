"""
Chapter 12 Researcher Agent

사용자 요청과 plan을 바탕으로 필요한 정보와 근거를 정리합니다.
현재 버전은 외부 API 호출 없이 규칙 기반 research_notes를 생성합니다.
"""

from __future__ import annotations

import re

from shared_state import MultiAgentState


KEYWORD_HINTS = {
    "제출": "제출 항목, 제출 형식, 마감일을 확인해야 합니다.",
    "과제": "과제 요구사항, 평가 기준, 제출 방법을 확인해야 합니다.",
    "공지": "공지 대상, 핵심 안내사항, 일정, 유의사항을 확인해야 합니다.",
    "평가": "평가 항목과 감점 기준을 분리해 정리해야 합니다.",
    "마감": "마감일과 지각 제출 처리 기준을 확인해야 합니다.",
    "README": "README 포함 여부와 작성 항목을 확인해야 합니다.",
}


def extract_keywords(text: str) -> list[str]:
    """간단한 한글/영문 keyword를 추출합니다."""
    tokens = re.findall(r"[가-힣A-Za-z0-9_]+", text)
    return [token for token in tokens if len(token) >= 2]


def build_research_notes(user_request: str, plan: list[str], memory_context: str = "") -> list[str]:
    """요청, 계획, memory context를 바탕으로 research notes를 생성합니다."""
    notes = [f"요청 요약: {user_request}"]

    if plan:
        notes.append("작업 계획에서 확인한 주요 단계: " + " / ".join(plan[:4]))

    matched_hints = []
    for keyword, hint in KEYWORD_HINTS.items():
        if keyword in user_request:
            matched_hints.append(hint)

    if matched_hints:
        notes.extend(matched_hints)
    else:
        notes.append("명시된 조건이 부족하면 확인 필요 항목으로 표시해야 합니다.")

    if memory_context:
        notes.append("memory_context 참고: " + memory_context[:300])

    keywords = extract_keywords(user_request)
    if keywords:
        notes.append("추출 keyword: " + ", ".join(keywords[:8]))

    return notes


def researcher_agent(state: MultiAgentState) -> MultiAgentState:
    """Researcher Agent 실행 함수입니다."""
    user_request = state.get("user_request", "")
    plan = state.get("plan", [])
    memory_context = state.get("memory_context", "")
    state["research_notes"] = build_research_notes(user_request, plan, memory_context)
    return state