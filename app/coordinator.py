"""
Chapter 12 Coordinator

Planner → Researcher → Writer → Reviewer → Revision → Final 흐름을 제어합니다.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

try:
    from collaboration_logger import log_agent_step
except ModuleNotFoundError:
    def log_agent_step(state, agent_name, status="success", message="", **kwargs):
        return state

from planner_agent import planner_agent
from researcher_agent import researcher_agent
from reviewer_agent import has_actionable_feedback, reviewer_agent
from shared_state import MultiAgentState
from writer_agent import finalize_answer, revise_answer, writer_agent


DEFAULT_MAX_REVIEW_ROUNDS = 1


def load_max_review_rounds() -> int:
    """환경 변수에서 최대 review round를 읽습니다."""
    load_dotenv()
    return int(os.getenv("MAX_REVIEW_ROUNDS", DEFAULT_MAX_REVIEW_ROUNDS))


def run_planner_step(state: MultiAgentState, write_log: bool = True) -> MultiAgentState:
    """Planner step을 실행합니다."""
    state = planner_agent(state)
    return log_agent_step(
        state,
        agent_name="Planner Agent",
        input_keys=["user_request"],
        output_keys=["plan"],
        message="작업 계획 생성 완료",
        write_file=write_log,
    )


def run_researcher_step(state: MultiAgentState, write_log: bool = True) -> MultiAgentState:
    """Researcher step을 실행합니다."""
    state = researcher_agent(state)
    return log_agent_step(
        state,
        agent_name="Researcher Agent",
        input_keys=["user_request", "plan", "memory_context"],
        output_keys=["research_notes"],
        message="정보와 근거 정리 완료",
        write_file=write_log,
    )


def run_writer_step(state: MultiAgentState, write_log: bool = True) -> MultiAgentState:
    """Writer step을 실행합니다."""
    state = writer_agent(state)
    return log_agent_step(
        state,
        agent_name="Writer Agent",
        input_keys=["user_request", "plan", "research_notes"],
        output_keys=["draft_answer"],
        message="답변 초안 작성 완료",
        write_file=write_log,
    )


def run_reviewer_step(state: MultiAgentState, write_log: bool = True) -> MultiAgentState:
    """Reviewer step을 실행합니다."""
    state = reviewer_agent(state)
    return log_agent_step(
        state,
        agent_name="Reviewer Agent",
        input_keys=["user_request", "research_notes", "draft_answer"],
        output_keys=["review_feedback"],
        message="초안 검토 완료",
        write_file=write_log,
    )


def run_revision_step(state: MultiAgentState, write_log: bool = True) -> MultiAgentState:
    """Writer revision step을 실행합니다."""
    state = revise_answer(state)
    return log_agent_step(
        state,
        agent_name="Writer Agent",
        input_keys=["draft_answer", "review_feedback"],
        output_keys=["draft_answer"],
        message="검토 의견 반영 완료",
        write_file=write_log,
    )


def run_final_step(state: MultiAgentState, write_log: bool = True) -> MultiAgentState:
    """최종 답변 확정 step을 실행합니다."""
    state = finalize_answer(state)
    return log_agent_step(
        state,
        agent_name="Coordinator",
        input_keys=["draft_answer"],
        output_keys=["final_answer"],
        message="최종 답변 확정 완료",
        write_file=write_log,
    )


def run_coordinator(state: MultiAgentState, write_log: bool = True) -> MultiAgentState:
    """멀티 에이전트 실행 순서를 제어합니다."""
    max_rounds = load_max_review_rounds()

    state = run_planner_step(state, write_log=write_log)
    state = run_researcher_step(state, write_log=write_log)
    state = run_writer_step(state, write_log=write_log)

    for _ in range(max_rounds):
        state = run_reviewer_step(state, write_log=write_log)
        feedback = state.get("review_feedback", [])

        if not has_actionable_feedback(feedback):
            break

        state = run_revision_step(state, write_log=write_log)

    state = run_final_step(state, write_log=write_log)
    return state