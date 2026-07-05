"""
Chapter 11 Memory Updater

새 대화에서 장기 메모리에 저장할 만한 정보를 선별하고 저장합니다.
"""

try:
    from .memory_schema import MemoryCategory, MemoryItem, memory_to_text
    from .memory_store import add_memory, clear_memories, load_memories
except ImportError:
    from memory_schema import MemoryCategory, MemoryItem, memory_to_text
    from memory_store import add_memory, clear_memories, load_memories


MEMORY_SIGNALS = [
    "기억",
    "기억해",
    "선호",
    "좋아합니다",
    "싫어합니다",
    "다음 작업",
    "결정",
    "완료",
    "진행 중",
    "규칙",
]

SENSITIVE_SIGNALS = [
    "api key",
    "apikey",
    "비밀번호",
    "password",
    "token",
    "토큰",
    "주민등록번호",
    "계좌번호",
    "카드번호",
]

CATEGORY_KEYWORDS: dict[MemoryCategory, list[str]] = {
    "project_state": ["진행", "완료", "작성 중", "구현", "수정", "프로젝트"],
    "user_preference": ["선호", "좋아합니다", "싫어합니다", "짧게", "자세히", "스타일"],
    "course_context": ["수업", "강의", "과제", "시험", "학생", "챕터"],
    "task_decision": ["결정", "다음 작업", "방향", "정했습니다", "진행하기로"],
}


def normalize_text(text: str) -> str:
    """비교하기 쉽도록 문자열을 정리합니다."""
    return text.strip().lower()


def contains_sensitive_info(text: str) -> bool:
    """저장하면 안 되는 민감정보 신호가 있는지 확인합니다."""
    normalized_text = normalize_text(text)
    return any(signal in normalized_text for signal in SENSITIVE_SIGNALS)


def should_create_memory(user_message: str, assistant_message: str) -> bool:
    """대화가 장기 메모리로 저장할 만한 내용인지 판단합니다."""
    text = f"{user_message}\n{assistant_message}"

    if contains_sensitive_info(text):
        return False

    return any(signal in text for signal in MEMORY_SIGNALS)


def infer_category(user_message: str, assistant_message: str) -> MemoryCategory:
    """대화 내용을 보고 memory category를 추정합니다."""
    text = f"{user_message}\n{assistant_message}"

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "project_state"


def estimate_importance(user_message: str, assistant_message: str) -> int:
    """대화 내용의 중요도를 1~5 범위로 추정합니다."""
    text = f"{user_message}\n{assistant_message}"

    if "반드시" in text or "꼭" in text or "기억해" in text:
        return 5

    if "결정" in text or "다음 작업" in text or "선호" in text:
        return 4

    if "완료" in text or "진행 중" in text:
        return 3

    return 2


def build_memory_content(user_message: str, assistant_message: str) -> str:
    """저장할 memory content 문장을 만듭니다."""
    user_message = user_message.strip()
    assistant_message = assistant_message.strip()

    if "기억" in user_message or "선호" in user_message:
        return user_message

    return f"사용자: {user_message} / assistant: {assistant_message}"


def update_memory_from_conversation(
    user_message: str,
    assistant_message: str,
) -> MemoryItem | None:
    """한 번의 user/assistant 대화를 검토해 필요하면 memory로 저장합니다."""
    if not should_create_memory(user_message, assistant_message):
        return None

    content = build_memory_content(user_message, assistant_message)
    category = infer_category(user_message, assistant_message)
    importance = estimate_importance(user_message, assistant_message)

    return add_memory(
        category=category,
        content=content,
        source="conversation",
        importance=importance,
    )


def update_memories_from_pairs(
    conversation_pairs: list[tuple[str, str]],
) -> list[MemoryItem]:
    """여러 개의 user/assistant 대화 쌍을 검토해 memory 후보를 저장합니다."""
    created_memories: list[MemoryItem] = []

    for user_message, assistant_message in conversation_pairs:
        memory = update_memory_from_conversation(user_message, assistant_message)

        if memory is not None:
            created_memories.append(memory)

    return created_memories


def print_created_memories(memories: list[MemoryItem]) -> None:
    """이번 실행에서 새로 저장된 memory를 출력합니다."""
    if not memories:
        print("새로 저장된 메모리가 없습니다.")
        return

    for memory in memories:
        print(memory_to_text(memory))


def main() -> None:
    """memory update step 동작을 간단히 확인합니다."""
    clear_memories()

    conversation_pairs = [
        (
            "앞으로 답변은 짧고 실행 중심으로 해 주세요. 이 선호를 기억해 주세요.",
            "네, 앞으로 짧고 실행 중심으로 답변하겠습니다.",
        ),
        (
            "오늘 날씨가 좋네요.",
            "네, 산책하기 좋은 날씨입니다.",
        ),
        (
            "Chapter 11에서는 memory store까지 완료했습니다.",
            "좋습니다. 다음 작업은 memory update step을 정리하면 됩니다.",
        ),
        (
            "API Key는 abc123입니다.",
            "민감정보는 저장하지 않는 것이 좋습니다.",
        ),
    ]

    created_memories = update_memories_from_pairs(conversation_pairs)

    print("[새로 저장된 메모리]")
    print_created_memories(created_memories)

    print("\n[전체 메모리 개수]")
    print(len(load_memories()))


if __name__ == "__main__":
    main()