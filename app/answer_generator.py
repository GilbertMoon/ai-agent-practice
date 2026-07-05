"""
Chapter 10 Answer Generator

검색 결과 또는 일반 개념 질문에 대한 답변을 생성합니다.
초기 버전은 API 호출 없이 템플릿 기반으로 동작합니다.
"""

try:
    from .state_schema import AgentState
except ImportError:
    from state_schema import AgentState


def generate_answer_from_results(state: AgentState) -> str:
    """검색 결과를 바탕으로 근거 기반 답변을 생성합니다."""
    results = state.get("retrieved_results", [])

    if not results:
        return "관련 근거를 찾지 못했습니다."

    first = results[0]
    content = str(first.get("content", "")).strip()
    source = first.get("source", "unknown")
    section = first.get("section", "unknown")
    chunk_id = first.get("chunk_id", "unknown")

    if len(content) > 700:
        content = content[:700].rstrip() + "..."

    return (
        "검색 결과에 따르면 다음 내용이 가장 관련 있습니다.\n\n"
        f"{content}\n\n"
        f"근거: source={source}, section={section}, chunk_id={chunk_id}"
    )


def generate_direct_answer(question: str) -> str:
    """검색이 필요하지 않은 일반 질문에 대한 간단한 답변을 생성합니다."""
    normalized = question.strip().lower()

    if "rag" in normalized:
        return (
            "RAG는 Retrieval-Augmented Generation의 약자로, "
            "외부 문서나 데이터에서 관련 근거를 검색한 뒤 그 내용을 바탕으로 답변을 생성하는 방식입니다. "
            "핵심은 LLM이 기억에만 의존하지 않고 검색 결과를 근거로 답변한다는 점입니다."
        )

    if "workflow" in normalized or "워크플로우" in normalized:
        return (
            "에이전트 워크플로우는 질문 분석, 경로 선택, 도구 실행, 결과 평가, 답변 생성처럼 "
            "여러 단계를 순서대로 실행하는 구조입니다. 각 단계의 중간 결과는 state에 저장합니다."
        )

    if "agent" in normalized or "에이전트" in normalized:
        return (
            "AI 에이전트는 단순히 답변만 생성하는 LLM 호출을 넘어, "
            "상태를 관리하고 도구를 사용하며 여러 단계를 거쳐 목표를 수행하는 실행 구조입니다."
        )

    return (
        "이 질문은 현재 공지 문서 검색 없이 일반 답변 경로로 처리되었습니다. "
        "공지, 제출, 보안, 오류, 미니 프로젝트와 관련된 질문은 검색 경로로 처리할 수 있습니다."
    )


def answer_step(state: AgentState) -> AgentState:
    """route와 검색 결과에 따라 최종 답변을 생성합니다."""
    if state.get("answer"):
        return state

    route = state.get("route")

    if route == "search":
        state["answer"] = generate_answer_from_results(state)
        return state

    if route == "direct_answer":
        state["answer"] = generate_direct_answer(state.get("user_question", ""))
        return state

    if route == "clarification":
        state["answer"] = "질문이 비어 있거나 불명확합니다. 알고 싶은 내용을 한 문장으로 입력해 주세요."
        return state

    state["answer"] = "처리 경로를 결정하지 못했습니다. 질문을 다시 입력해 주세요."
    return state