"""
Chapter 11 Memory Store

장기 메모리를 JSON 파일로 저장하고 불러오는 모듈입니다.
"""

import json
from pathlib import Path
from typing import Any, cast

try:
    from .memory_schema import MemoryCategory, MemoryItem, create_memory_item, memory_to_text
except ImportError:
    from memory_schema import MemoryCategory, MemoryItem, create_memory_item, memory_to_text


MEMORY_FILE = Path("outputs") / "memory_store.json"


def ensure_output_dir() -> None:
    """메모리 파일을 저장할 outputs 폴더를 생성합니다."""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def is_valid_memory_item(data: Any) -> bool:
    """JSON에서 읽어 온 값이 MemoryItem 구조와 맞는지 확인합니다."""
    if not isinstance(data, dict):
        return False

    if not isinstance(data.get("id"), str):
        return False

    if data.get("category") not in (
        "project_state",
        "user_preference",
        "course_context",
        "task_decision",
    ):
        return False

    if not isinstance(data.get("content"), str):
        return False

    if data.get("source") not in ("conversation", "user_input", "system", "manual"):
        return False

    if not isinstance(data.get("created_at"), str):
        return False

    if not isinstance(data.get("updated_at"), str):
        return False

    if not isinstance(data.get("importance"), int):
        return False

    return True


def load_memories() -> list[MemoryItem]:
    """저장된 장기 메모리 목록을 불러옵니다."""
    if not MEMORY_FILE.exists():
        return []

    with MEMORY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        return []

    memories: list[MemoryItem] = []

    for item in data:
        if is_valid_memory_item(item):
            memories.append(cast(MemoryItem, item))

    return memories


def save_memories(memories: list[MemoryItem]) -> None:
    """장기 메모리 목록을 JSON 파일로 저장합니다."""
    ensure_output_dir()

    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(memories, file, ensure_ascii=False, indent=2)


def add_memory(
    category: MemoryCategory,
    content: str,
    source: str = "conversation",
    importance: int = 3,
) -> MemoryItem:
    """새 메모리를 추가하고 추가된 MemoryItem을 반환합니다."""
    memories = load_memories()
    memory = create_memory_item(
        category=category,
        content=content,
        source=source,  # type: ignore[arg-type]
        importance=importance,
    )
    memories.append(memory)
    save_memories(memories)
    return memory


def find_memories_by_category(category: MemoryCategory) -> list[MemoryItem]:
    """특정 category에 해당하는 메모리만 조회합니다."""
    memories = load_memories()
    return [memory for memory in memories if memory.get("category") == category]


def search_memories(keyword: str) -> list[MemoryItem]:
    """content에 keyword가 포함된 메모리를 검색합니다."""
    memories = load_memories()
    normalized_keyword = keyword.strip().lower()

    if not normalized_keyword:
        return []

    return [
        memory
        for memory in memories
        if normalized_keyword in memory.get("content", "").lower()
    ]


def clear_memories() -> None:
    """저장된 장기 메모리를 모두 삭제합니다."""
    save_memories([])


def print_memories(memories: list[MemoryItem] | None = None) -> None:
    """메모리 목록을 화면에 출력합니다."""
    if memories is None:
        memories = load_memories()

    if not memories:
        print("저장된 메모리가 없습니다.")
        return

    for memory in memories:
        print(memory_to_text(memory))


def main() -> None:
    """memory store 동작을 간단히 확인합니다."""
    add_memory(
        category="project_state",
        content="사용자는 Chapter 11 원고 초안 작성을 진행 중이다.",
        source="conversation",
        importance=3,
    )

    add_memory(
        category="user_preference",
        content="사용자는 짧고 실행 중심의 설명을 선호한다.",
        source="conversation",
        importance=4,
    )

    print("[전체 메모리]")
    print_memories()

    print("\n[project_state 메모리]")
    print_memories(find_memories_by_category("project_state"))


if __name__ == "__main__":
    main()