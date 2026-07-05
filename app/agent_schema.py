"""
Chapter 12 Agent Schema

멀티 에이전트 구조에서 사용할 AgentSpec을 정의합니다.
"""

from __future__ import annotations

from typing import Literal, TypedDict


AgentRole = Literal["planner", "researcher", "writer", "reviewer"]


class AgentSpec(TypedDict):
    """agent의 이름, 역할, 목표, 입출력 key를 정의합니다."""

    name: str
    role: AgentRole
    goal: str
    input_keys: list[str]
    output_keys: list[str]


def create_agent_spec(
    name: str,
    role: AgentRole,
    goal: str,
    input_keys: list[str],
    output_keys: list[str],
) -> AgentSpec:
    """AgentSpec 객체를 생성합니다."""
    return {
        "name": name,
        "role": role,
        "goal": goal,
        "input_keys": input_keys,
        "output_keys": output_keys,
    }


def get_default_agent_specs() -> list[AgentSpec]:
    """Chapter 12 기본 agent 목록을 반환합니다."""
    return [
        create_agent_spec(
            name="Planner Agent",
            role="planner",
            goal="사용자 요청을 하위 작업으로 나누고 실행 순서를 정합니다.",
            input_keys=["user_request"],
            output_keys=["plan"],
        ),
        create_agent_spec(
            name="Researcher Agent",
            role="researcher",
            goal="필요한 정보와 근거를 수집해 research_notes로 정리합니다.",
            input_keys=["user_request", "plan", "memory_context"],
            output_keys=["research_notes"],
        ),
        create_agent_spec(
            name="Writer Agent",
            role="writer",
            goal="plan과 research_notes를 바탕으로 사용자용 답변 초안을 작성합니다.",
            input_keys=["user_request", "plan", "research_notes", "review_feedback"],
            output_keys=["draft_answer", "final_answer"],
        ),
        create_agent_spec(
            name="Reviewer Agent",
            role="reviewer",
            goal="초안을 검토하고 누락·오류·형식 문제를 feedback으로 정리합니다.",
            input_keys=["user_request", "research_notes", "draft_answer"],
            output_keys=["review_feedback"],
        ),
    ]


def format_agent_spec(spec: AgentSpec) -> str:
    """AgentSpec을 사람이 읽기 쉬운 문자열로 변환합니다."""
    return (
        f"{spec['name']} ({spec['role']})\n"
        f"- goal: {spec['goal']}\n"
        f"- input_keys: {', '.join(spec['input_keys'])}\n"
        f"- output_keys: {', '.join(spec['output_keys'])}"
    )