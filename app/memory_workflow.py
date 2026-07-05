"""
Chapter 11 Memory Workflow

대화 기록, 최근 context, 장기 메모리 검색, memory update를 하나의 workflow로 연결합니다.
"""

from typing import Any, TypedDict

try:
    from .context_builder import build_recent_context
    from .conversation_store import append_message, load_history
    from .memory_retriever import build_memory_context, retrieve_memory
    from .memory_schema import MemoryItem, memory_to_text
    from .memory_store import load_memories
    from .memory_updater import update_memory_from_conversation
except ImportError:
    from context_builder import build_recent_context
    from conversation_store import append_message, load_history
    from memory_retriever import build_memory_context, retrieve_memory
    from memory_schema import MemoryItem, memory_to_text
    from memory_store import load_memories
    from memory_updater import update_memory_from_conversation


class MemoryWorkflowState(TypedDict, total=False):
    """memory workflow에서 사용하는 state 구조입니다."""

    user_question: str
    recent_context: str
    retrieved_memories: list[MemoryItem]
    memory_context: str
    answer: str
    memory_update_candidates: list[MemoryItem]
    memory_saved: list[MemoryItem]
    total_history_count: int
    total_memory_count: int


def generate_answer(
    user_question: str,
    recent_context: str,
    memory_context: str,
) -> str:
    """예제용 답변 생성 함수입니다.

    실제 서비스에서는 이 부분을 LLM 호출 또는 Chapter 10 workflow 실행으로 교체합니다.
    """
    if memory_context:
        return (
            f"질문을 확인했습니다: {user_question}\n"
            f"관련 메모리를 참고해 답변을 생성하겠습니다."
        )

    if recent_context:
        return (
            f"질문을 확인했습니다: {user_question}\n"
            f"최근 대화 흐름을 참고해 답변을 생성하겠습니다."
        )

    return f"질문을 확인했습니다: {user_question}"


def run_memory_workflow(user_question: str) -> MemoryWorkflowState:
    """사용자 질문을 받아 memory가 연결된 workflow를 실행합니다."""
    history = load_history()
    memories = load_memories()

    recent_context = build_recent_context(history, limit=4)
    retrieved_memories = retrieve_memory(user_question, memories, top_k=3)
    memory_context = build_memory_context(retrieved_memories)

    answer = generate_answer(
        user_question=user_question,
        recent_context=recent_context,
        memory_context=memory_context,
    )

    append_message("user", user_question)
    append_message("assistant", answer)

    saved_memory = update_memory_from_conversation(user_question, answer)
    update_candidates = [saved_memory] if saved_memory is not None else []
    memory_saved = update_candidates

    return {
        "user_question": user_question,
        "recent_context": recent_context,
        "retrieved_memories": retrieved_memories,
        "memory_context": memory_context,
        "answer": answer,
        "memory_update_candidates": update_candidates,
        "memory_saved": memory_saved,
        "total_history_count": len(history),
        "total_memory_count": len(memories),
    }


def print_workflow_state(state: MemoryWorkflowState) -> None:
    """workflow 실행 결과를 사람이 읽기 쉬운 형태로 출력합니다."""
    print("[user question]")
    print(state.get("user_question", ""))

    print("\n[recent context]")
    print(state.get("recent_context") or "최근 대화 context가 없습니다.")

    print("\n[retrieved memories]")
    retrieved_memories = state.get("retrieved_memories", [])
    if retrieved_memories:
        for memory in retrieved_memories:
            print(memory_to_text(memory))
    else:
        print("검색된 메모리가 없습니다.")

    print("\n[memory context]")
    print(state.get("memory_context") or "memory context가 없습니다.")

    print("\n[answer]")
    print(state.get("answer", ""))

    print("\n[memory saved]")
    saved_memories = state.get("memory_saved", [])
    if saved_memories:
        for memory in saved_memories:
            print(memory_to_text(memory))
    else:
        print("새로 저장된 메모리가 없습니다.")


def main() -> None:
    """memory workflow 동작을 간단히 확인합니다."""
    user_question = "Chapter 11 원고 작성 상태를 알려 주세요."
    state = run_memory_workflow(user_question)
    print_workflow_state(state)


if __name__ == "__main__":
    main()