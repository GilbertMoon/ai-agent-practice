"""
Chapter 11 Memory Retriever

사용자 질문과 관련 있는 장기 메모리를 keyword 기반으로 검색합니다.
"""

try:
    from .memory_schema import MemoryItem, create_memory_item, memory_to_text
except ImportError:
    from memory_schema import MemoryItem, create_memory_item, memory_to_text


DEFAULT_TOP_K = 3
IMPORTANT_CATEGORIES = {"project_state", "user_preference"}


def normalize_text(text: str) -> str:
    """검색 비교를 위해 문자열을 소문자로 정리합니다."""
    return text.strip().lower()


def tokenize(text: str) -> set[str]:
    """문자열을 공백 기준 keyword 집합으로 변환합니다."""
    normalized_text = normalize_text(text)
    return {term for term in normalized_text.split() if term}


def score_memory(query: str, memory: MemoryItem) -> int:
    """질문과 메모리의 관련도를 점수로 계산합니다."""
    query_terms = tokenize(query)
    content = normalize_text(memory.get("content", ""))
    category = memory.get("category", "")
    importance = int(memory.get("importance", 1))

    score = 0

    for term in query_terms:
        if term in content:
            score += 2

    if category in IMPORTANT_CATEGORIES:
        score += 1

    score += importance
    return score


def retrieve_memory(
    query: str,
    memories: list[MemoryItem],
    top_k: int = DEFAULT_TOP_K,
) -> list[MemoryItem]:
    """질문과 관련도가 높은 메모리 top_k개를 반환합니다."""
    scored_memories: list[tuple[int, MemoryItem]] = []

    for memory in memories:
        score = score_memory(query, memory)
        if score > 0:
            scored_memories.append((score, memory))

    scored_memories.sort(key=lambda item: item[0], reverse=True)
    return [memory for score, memory in scored_memories[:top_k]]


def build_memory_context(memories: list[MemoryItem]) -> str:
    """검색된 메모리 목록을 LLM 입력용 context 문자열로 변환합니다."""
    if not memories:
        return ""

    lines: list[str] = []

    for memory in memories:
        category = memory.get("category", "unknown")
        content = memory.get("content", "")
        lines.append(f"- [{category}] {content}")

    return "\n".join(lines)


def main() -> None:
    """memory retrieval 동작을 간단히 확인합니다."""
    memories = [
        create_memory_item(
            category="project_state",
            content="사용자는 Chapter 11 원고 초안 작성을 진행 중이다.",
            source="conversation",
            importance=3,
        ),
        create_memory_item(
            category="user_preference",
            content="사용자는 짧고 실행 중심의 설명을 선호한다.",
            source="conversation",
            importance=4,
        ),
        create_memory_item(
            category="course_context",
            content="이번 장에서는 AI 에이전트의 메모리 구조를 다룬다.",
            source="manual",
            importance=2,
        ),
    ]

    query = "Chapter 11 원고 작성 상태 알려줘"
    retrieved_memories = retrieve_memory(query, memories, top_k=2)
    memory_context = build_memory_context(retrieved_memories)

    print(f"[query] {query}")

    print("\n[retrieved memories]")
    for memory in retrieved_memories:
        print(memory_to_text(memory))

    print("\n[memory context]")
    print(memory_context)


if __name__ == "__main__":
    main()