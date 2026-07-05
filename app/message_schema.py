"""
Chapter 11 Message Schema

대화 기록을 일관된 구조로 저장하기 위한 메시지 스키마입니다.
"""

from datetime import datetime
from typing import Literal, TypedDict


MessageRole = Literal["user", "assistant", "system"]


class Message(TypedDict):
    """대화 메시지 한 건을 표현하는 기본 구조입니다."""

    role: MessageRole
    content: str
    timestamp: str


def get_current_timestamp() -> str:
    """현재 시간을 ISO 형식 문자열로 반환합니다."""
    return datetime.now().isoformat(timespec="seconds")


def create_message(role: MessageRole, content: str) -> Message:
    """role과 content를 받아 Message 객체를 생성합니다."""
    return {
        "role": role,
        "content": content,
        "timestamp": get_current_timestamp(),
    }


def create_user_message(content: str) -> Message:
    """사용자 메시지를 생성합니다."""
    return create_message("user", content)


def create_assistant_message(content: str) -> Message:
    """assistant 메시지를 생성합니다."""
    return create_message("assistant", content)


def create_system_message(content: str) -> Message:
    """system 메시지를 생성합니다."""
    return create_message("system", content)


def message_to_text(message: Message) -> str:
    """메시지를 사람이 읽기 쉬운 문자열로 변환합니다."""
    return f"[{message['timestamp']}] {message['role']}: {message['content']}"


def main() -> None:
    """메시지 스키마 동작을 간단히 확인합니다."""
    messages = [
        create_system_message("당신은 수업 안내를 돕는 AI 에이전트입니다."),
        create_user_message("미니 프로젝트 제출 형식을 알려 주세요."),
        create_assistant_message("미니 프로젝트는 실행 코드와 설명 문서를 함께 제출합니다."),
    ]

    for message in messages:
        print(message_to_text(message))


if __name__ == "__main__":
    main()