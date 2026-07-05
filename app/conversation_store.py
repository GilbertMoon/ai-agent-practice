"""
Chapter 11 Conversation Store

대화 기록을 JSON 파일로 저장하고 불러오는 모듈입니다.
"""

import json
from pathlib import Path
from typing import Any, cast

from message_schema import Message, MessageRole, create_message, message_to_text


HISTORY_FILE = Path("outputs") / "conversation_history.json"


def ensure_output_dir() -> None:
    """대화 기록을 저장할 outputs 폴더를 생성합니다."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def is_valid_message(data: Any) -> bool:
    """JSON에서 읽어 온 값이 Message 구조와 맞는지 확인합니다."""
    if not isinstance(data, dict):
        return False

    if data.get("role") not in ("user", "assistant", "system"):
        return False

    if not isinstance(data.get("content"), str):
        return False

    if not isinstance(data.get("timestamp"), str):
        return False

    return True


def load_history() -> list[Message]:
    """저장된 대화 기록을 불러옵니다."""
    if not HISTORY_FILE.exists():
        return []

    with HISTORY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        return []

    messages: list[Message] = []

    for item in data:
        if is_valid_message(item):
            messages.append(cast(Message, item))

    return messages


def save_history(messages: list[Message]) -> None:
    """대화 기록을 JSON 파일로 저장합니다."""
    ensure_output_dir()

    with HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(messages, file, ensure_ascii=False, indent=2)


def append_message(role: MessageRole, content: str) -> list[Message]:
    """새 메시지를 대화 기록에 추가하고 전체 기록을 다시 저장합니다."""
    messages = load_history()
    messages.append(create_message(role, content))
    save_history(messages)
    return messages


def clear_history() -> None:
    """대화 기록을 초기화합니다."""
    save_history([])


def print_history() -> None:
    """저장된 대화 기록을 화면에 출력합니다."""
    messages = load_history()

    if not messages:
        print("저장된 대화 기록이 없습니다.")
        return

    for message in messages:
        print(message_to_text(message))


def main() -> None:
    """conversation store 동작을 간단히 확인합니다."""
    append_message("user", "오늘 수업에서 무엇을 배웠나요?")
    append_message("assistant", "오늘은 대화 기록을 JSON 파일로 저장하는 방법을 배웠습니다.")

    print_history()


if __name__ == "__main__":
    main()