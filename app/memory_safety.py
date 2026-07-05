"""
Chapter 11 Memory Safety

장기 메모리에 저장하기 전에 민감정보와 저장 금지 내용을 검사합니다.
"""

import re

try:
    from .memory_schema import MemoryCategory, MemoryItem, memory_to_text
    from .memory_store import add_memory, clear_memories, load_memories
except ImportError:
    from memory_schema import MemoryCategory, MemoryItem, memory_to_text
    from memory_store import add_memory, clear_memories, load_memories


SENSITIVE_KEYWORDS = [
    "api key",
    "apikey",
    "secret",
    "token",
    "password",
    "private key",
    "비밀번호",
    "패스워드",
    "토큰",
    "시크릿",
    "주민등록번호",
    "계좌번호",
    "카드번호",
]

DO_NOT_STORE_SIGNALS = [
    "기억하지 마",
    "저장하지 마",
    "메모리에 저장하지 마",
    "forget this",
    "do not remember",
    "do not store",
]

LONG_DIGIT_PATTERN = re.compile(r"\d{4,}[- ]?\d{4,}[- ]?\d{4,}[- ]?\d*")
EMAIL_PATTERN = re.compile(r"[\w.%-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"01[016789][- ]?\d{3,4}[- ]?\d{4}")


def normalize_text(text: str) -> str:
    """안전 검사를 위해 문자열을 소문자로 정리합니다."""
    return text.strip().lower()


def has_sensitive_keyword(content: str) -> bool:
    """민감정보를 암시하는 keyword가 포함되어 있는지 확인합니다."""
    lower = normalize_text(content)
    return any(keyword in lower for keyword in SENSITIVE_KEYWORDS)


def has_long_digit_sequence(content: str) -> bool:
    """카드번호, 계좌번호처럼 긴 숫자열이 있는지 확인합니다."""
    digit_count = sum(ch.isdigit() for ch in content)

    if digit_count >= 12:
        return True

    return bool(LONG_DIGIT_PATTERN.search(content))


def has_personal_contact(content: str) -> bool:
    """이메일이나 휴대폰 번호처럼 개인 연락처가 포함되어 있는지 확인합니다."""
    return bool(EMAIL_PATTERN.search(content) or PHONE_PATTERN.search(content))


def user_requested_not_to_store(content: str) -> bool:
    """사용자가 저장하지 말라고 한 표현이 있는지 확인합니다."""
    lower = normalize_text(content)
    return any(signal in lower for signal in DO_NOT_STORE_SIGNALS)


def is_safe_memory(content: str) -> bool:
    """memory content를 저장해도 되는지 검사합니다."""
    if not content.strip():
        return False

    if user_requested_not_to_store(content):
        return False

    if has_sensitive_keyword(content):
        return False

    if has_long_digit_sequence(content):
        return False

    if has_personal_contact(content):
        return False

    return True


def get_memory_safety_reason(content: str) -> str:
    """저장 가능 여부를 설명하는 메시지를 반환합니다."""
    if not content.strip():
        return "빈 내용은 메모리에 저장하지 않습니다."

    if user_requested_not_to_store(content):
        return "사용자가 저장하지 말라고 요청한 내용입니다."

    if has_sensitive_keyword(content):
        return "민감정보 keyword가 포함되어 있습니다."

    if has_long_digit_sequence(content):
        return "긴 숫자열이 포함되어 있어 민감정보일 수 있습니다."

    if has_personal_contact(content):
        return "개인 연락처로 보이는 정보가 포함되어 있습니다."

    return "저장 가능한 메모리입니다."


def filter_safe_memories(memories: list[MemoryItem]) -> list[MemoryItem]:
    """MemoryItem 목록에서 안전한 항목만 반환합니다."""
    safe_memories: list[MemoryItem] = []

    for memory in memories:
        content = memory.get("content", "")

        if is_safe_memory(content):
            safe_memories.append(memory)

    return safe_memories


def safe_add_memory(
    category: MemoryCategory,
    content: str,
    source: str = "conversation",
    importance: int = 3,
) -> MemoryItem | None:
    """안전 검사를 통과한 경우에만 memory store에 저장합니다."""
    if not is_safe_memory(content):
        print(f"저장하지 않음: {get_memory_safety_reason(content)}")
        return None

    return add_memory(
        category=category,
        content=content,
        source=source,
        importance=importance,
    )


def print_safety_check(content: str) -> None:
    """content 안전 검사 결과를 출력합니다."""
    result = "저장 가능" if is_safe_memory(content) else "저장 불가"
    reason = get_memory_safety_reason(content)
    print(f"[{result}] {content}")
    print(f"- 이유: {reason}")


def main() -> None:
    """memory safety guardrail 동작을 간단히 확인합니다."""
    clear_memories()

    candidates = [
        "사용자는 짧고 실행 중심의 설명을 선호한다.",
        "내 API Key는 abc123입니다.",
        "이 내용은 기억하지 마세요.",
        "사용자는 Chapter 11 memory safety 파트를 작성 중이다.",
        "연락처는 010-1234-5678입니다.",
    ]

    print("[메모리 안전 검사]")

    for content in candidates:
        print_safety_check(content)

    print("\n[안전한 메모리만 저장]")

    for content in candidates:
        safe_add_memory(
            category="project_state",
            content=content,
            source="conversation",
            importance=3,
        )

    print("\n[저장된 메모리]")

    for memory in load_memories():
        print(memory_to_text(memory))


if __name__ == "__main__":
    main()