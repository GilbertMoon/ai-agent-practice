"""
Chapter 11 Context Builder

최근 대화 메시지를 LLM 입력에 사용할 context 문자열로 변환합니다.
"""

try:
    from .message_schema import Message, create_assistant_message, create_system_message, create_user_message
except ImportError:
    from message_schema import Message, create_assistant_message, create_system_message, create_user_message


DEFAULT_RECENT_MESSAGE_LIMIT = 6


def format_message_for_context(message: Message) -> str:
    """Message 한 건을 context에 넣기 쉬운 한 줄 문자열로 변환합니다."""
    role = message["role"]
    content = message["content"].strip()
    return f"{role}: {content}"


def get_recent_messages(messages: list[Message], limit: int = DEFAULT_RECENT_MESSAGE_LIMIT) -> list[Message]:
    """전체 메시지 목록에서 최근 limit개 메시지만 반환합니다."""
    if limit <= 0:
        return []

    return messages[-limit:]


def build_recent_context(messages: list[Message], limit: int = DEFAULT_RECENT_MESSAGE_LIMIT) -> str:
    """최근 메시지를 LLM에 전달할 context 문자열로 변환합니다."""
    recent_messages = get_recent_messages(messages, limit)
    lines: list[str] = []

    for message in recent_messages:
        lines.append(format_message_for_context(message))

    return "\n".join(lines)


def build_context_state(messages: list[Message], limit: int = DEFAULT_RECENT_MESSAGE_LIMIT) -> dict:
    """최근 context와 메시지 개수 정보를 state 형태로 반환합니다."""
    recent_messages = get_recent_messages(messages, limit)
    recent_context = build_recent_context(messages, limit)

    return {
        "recent_context": recent_context,
        "recent_message_count": len(recent_messages),
        "total_message_count": len(messages),
    }


def main() -> None:
    """최근 대화 context 생성 예시를 실행합니다."""
    messages = [
        create_system_message("당신은 수업 안내를 돕는 AI 에이전트입니다."),
        create_user_message("미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?"),
        create_assistant_message("보고서, 코드, 실행 결과, README가 필요합니다."),
        create_user_message("그럼 제출 형식도 알려 주세요."),
        create_assistant_message("PDF 보고서와 소스 코드 폴더를 함께 제출하면 됩니다."),
        create_user_message("파일명 규칙도 있나요?"),
        create_assistant_message("학번_이름_프로젝트명 형식을 권장합니다."),
    ]

    recent_context = build_recent_context(messages, limit=4)
    context_state = build_context_state(messages, limit=4)

    print("[최근 대화 context]")
    print(recent_context)

    print("\n[context state]")
    print(context_state)


if __name__ == "__main__":
    main()