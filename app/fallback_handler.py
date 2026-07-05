"""
Chapter 10 Fallback Handler

검색 실패 또는 오류 상황에서 사용할 대체 응답을 만듭니다.
"""

try:
    from .state_schema import AgentState
except ImportError:
    from state_schema import AgentState


def build_fallback_answer(state: AgentState) -> str:
    """state 상태에 맞는 fallback 답변을 생성합니다."""
    retrieval_status = state.get("retrieval_status")
    error = state.get("error")

    if retrieval_status == "error":
        return (
            "검색 도구 실행 중 오류가 발생했습니다. "
            "잠시 후 다시 시도하거나 질문을 더 구체적으로 입력해 주세요."
            f"\n\n오류 요약: {error}"
        )

    if retrieval_status == "empty":
        return (
            "관련 근거를 찾지 못했습니다. "
            "공지 문서에 포함된 주제인지 확인하거나 질문을 더 구체적으로 입력해 주세요."
        )

    return "현재 질문에 대해 충분한 근거를 찾지 못했습니다. 질문을 더 구체적으로 입력해 주세요."


def fallback_step(state: AgentState) -> AgentState:
    """fallback이 필요한 경우 대체 답변을 state에 저장합니다."""
    if not state.get("needs_fallback"):
        return state

    state["answer"] = build_fallback_answer(state)
    return state