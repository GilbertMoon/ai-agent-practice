"""
Chapter 15 Memory Store

최종 프로젝트에서 사용할 간단한 session memory를 관리합니다.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class MemoryStore:
    """session_id 기준으로 대화 이벤트를 메모리에 저장합니다."""

    def __init__(self) -> None:
        self.sessions: dict[str, list[dict[str, Any]]] = {}

    def load(self, session_id: str | None) -> list[dict[str, Any]]:
        """session_id에 해당하는 메모리 목록을 반환합니다."""
        if not session_id:
            return []
        return deepcopy(self.sessions.get(session_id, []))

    def append(self, session_id: str | None, event: dict[str, Any]) -> None:
        """session_id에 새 이벤트를 추가합니다."""
        if not session_id:
            return
        self.sessions.setdefault(session_id, []).append(deepcopy(event))

    def clear(self, session_id: str | None = None) -> None:
        """특정 session 또는 전체 메모리를 삭제합니다."""
        if session_id is None:
            self.sessions.clear()
            return
        self.sessions.pop(session_id, None)

    def count(self, session_id: str | None) -> int:
        """session_id에 저장된 이벤트 개수를 반환합니다."""
        return len(self.load(session_id))


memory_store = MemoryStore()


if __name__ == "__main__":
    sample_session_id = "demo-session"

    memory_store.append(
        sample_session_id,
        {
            "user_request": "회의 내용을 요약해 주세요.",
            "trace_id": "trace-001",
        },
    )

    print(memory_store.load(sample_session_id))