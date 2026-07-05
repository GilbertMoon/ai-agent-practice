"""
Chapter 12 Planner Agent

사용자 요청을 하위 작업으로 분해하고 실행 계획을 만듭니다.
"""

from __future__ import annotations

from shared_state import MultiAgentState


DEFAULT_PLAN = [
    "사용자 요청 의도 파악",
    "필요한 정보와 조건 정리",
    "학생용 안내문 초안 작성",
    "누락·오류 검토",
    "검토 의견 반영 후 최종 답변 생성",
]


def build_plan(user_request: str) -> list[str]:
    """사용자 요청에 따라 간단한 작업 계획을 생성합니다."""
    plan = DEFAULT_PLAN.copy()

    if any(keyword in user_request for keyword in ["공지", "수업", "과제", "제출"]):
        plan.insert(1, "수업 공지, 과제 조건, 제출 형식, 마감일 확인")

    if any(keyword in user_request for keyword in ["평가", "채점", "기준"]):
        plan.insert(-2, "평가 기준과 감점 조건 확인")

    if any(keyword in user_request for keyword in ["표", "정리", "항목"]):
        plan.insert(-2, "항목별로 구조화해 표 또는 목록 형태로 정리")

    return list(dict.fromkeys(plan))


def planner_agent(state: MultiAgentState) -> MultiAgentState:
    """Planner Agent 실행 함수입니다."""
    user_request = state.get("user_request", "")
    state["plan"] = build_plan(user_request)
    return state