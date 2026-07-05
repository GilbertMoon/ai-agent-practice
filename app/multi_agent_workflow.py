"""
Chapter 12 Multi-Agent Workflow

역할 분담형 멀티 에이전트 workflow를 실행합니다.
"""

from __future__ import annotations

import json

from coordinator import run_coordinator
from shared_state import MultiAgentState, create_initial_state, summarize_state


DEFAULT_USER_REQUEST = "이번 주 수업 공지와 과제 조건을 종합해서 학생들에게 보낼 안내문을 작성해 주세요."


def run_multi_agent_workflow(
    user_request: str,
    memory_context: str = "",
    write_log: bool = True,
) -> MultiAgentState:
    """사용자 요청을 멀티 에이전트 workflow로 처리합니다."""
    state = create_initial_state(user_request=user_request, memory_context=memory_context)
    return run_coordinator(state, write_log=write_log)


def main() -> None:
    """샘플 요청으로 workflow를 실행합니다."""
    state = run_multi_agent_workflow(DEFAULT_USER_REQUEST)

    print("Chapter 12 Multi-Agent Workflow")
    print("=" * 70)
    print("[상태 요약]")
    print(json.dumps(summarize_state(state), ensure_ascii=False, indent=2))
    print("\n[최종 답변]")
    print(state.get("final_answer", ""))


if __name__ == "__main__":
    main()