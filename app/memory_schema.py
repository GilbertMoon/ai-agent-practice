"""
Chapter 11 Memory Schema

장기 메모리에 저장할 MemoryItem 구조와 생성 함수를 정의합니다.
"""

from datetime import datetime
from typing import Literal, TypedDict
from uuid import uuid4


MemoryCategory = Literal[
    "project_state",
    "user_preference",
    "course_context",
    "task_decision",
]

MemorySource = Literal[
    "conversation",
    "user_input",
    "system",
    "manual",
]


class MemoryItem(TypedDict, total=False):
    """장기 메모리 항목 한 건을 표현하는 구조입니다."""

    id: str
    category: MemoryCategory
    content: str
    source: MemorySource
    created_at: str
    updated_at: str
    importance: int


def get_current_timestamp() -> str:
    """현재 시간을 ISO 형식 문자열로 반환합니다."""
    return datetime.now().isoformat(timespec="seconds")


def create_memory_id() -> str:
    """메모리 항목 ID를 생성합니다."""
    return f"mem_{uuid4().hex[:8]}"


def normalize_importance(importance: int) -> int:
    """importance 값을 1~5 범위로 보정합니다."""
    if importance < 1:
        return 1

    if importance > 5:
        return 5

    return importance


def create_memory_item(
    category: MemoryCategory,
    content: str,
    source: MemorySource = "conversation",
    importance: int = 3,
) -> MemoryItem:
    """MemoryItem 객체를 생성합니다."""
    now = get_current_timestamp()

    return {
        "id": create_memory_id(),
        "category": category,
        "content": content.strip(),
        "source": source,
        "created_at": now,
        "updated_at": now,
        "importance": normalize_importance(importance),
    }


def update_memory_content(memory: MemoryItem, content: str) -> MemoryItem:
    """기존 메모리의 내용을 수정하고 updated_at을 갱신합니다."""
    updated_memory = memory.copy()
    updated_memory["content"] = content.strip()
    updated_memory["updated_at"] = get_current_timestamp()
    return updated_memory


def memory_to_text(memory: MemoryItem) -> str:
    """MemoryItem을 사람이 읽기 쉬운 문자열로 변환합니다."""
    return (
        f"[{memory.get('category')}] "
        f"{memory.get('content')} "
        f"(importance={memory.get('importance')}, source={memory.get('source')})"
    )


def main() -> None:
    """MemoryItem 스키마 동작을 간단히 확인합니다."""
    memory = create_memory_item(
        category="project_state",
        content="사용자는 Chapter 11 원고 초안 작성을 진행 중이다.",
        source="conversation",
        importance=3,
    )

    print(memory)
    print(memory_to_text(memory))


if __name__ == "__main__":
    main()