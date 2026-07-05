"""
Chapter 11 Chat CLI with Memory

대화 기록, 최근 context, 장기 메모리를 함께 사용하는 간단한 CLI입니다.
"""

import os
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

try:
    from .conversation_store import append_message, clear_history, load_history
    from .context_builder import build_recent_context
    from .memory_retriever import build_memory_context, retrieve_memory
    from .memory_store import clear_memories, load_memories
except ImportError:
    from conversation_store import append_message, clear_history, load_history
    from context_builder import build_recent_context
    from memory_retriever import build_memory_context, retrieve_memory
    from memory_store import clear_memories, load_memories

try:
    from .memory_updater import update_memory_from_conversation
except ImportError:
    try:
        from memory_updater import update_memory_from_conversation
    except ImportError:
        update_memory_from_conversation = None


HELP_TEXT = """
사용 가능한 명령:
/history        최근 대화 보기
/memory         저장된 메모리 보기
/clear          대화 기록 초기화
/clear-memory   장기 메모리 초기화
/help           도움말 보기
/exit           종료
""".strip()

EXIT_COMMANDS = {"/exit", "/quit", "exit", "quit"}
DEFAULT_MODEL = "gemini-1.5-flash"


SYSTEM_PROMPT = """
당신은 대화 기록과 장기 메모리를 참고해 답변하는 AI 에이전트입니다.

규칙:
- 사용자의 현재 질문에 직접 답변합니다.
- 최근 대화 context와 장기 메모리가 있으면 참고하되, 억지로 언급하지 않습니다.
- 민감정보, API Key, 비밀번호, 토큰은 저장하거나 다시 출력하지 않습니다.
- 답변은 한국어로 작성합니다.
- 실습용 CLI이므로 너무 길지 않게 핵심 중심으로 답변합니다.
""".strip()


def load_environment() -> None:
    """환경 변수를 로드합니다."""
    if load_dotenv is not None:
        load_dotenv()


def get_llm_model() -> str:
    """사용할 Gemini 모델명을 환경 변수에서 읽습니다."""
    load_environment()
    return (
        os.getenv("GEMINI_MODEL_NAME")
        or os.getenv("GEMINI_MODEL")
        or DEFAULT_MODEL
    )


def get_gemini_api_key() -> str | None:
    """Gemini API Key를 환경 변수에서 읽습니다."""
    load_environment()
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def get_gemini_client() -> Any | None:
    """Gemini client를 생성합니다."""
    if genai is None:
        return None

    api_key = get_gemini_api_key()

    if not api_key:
        return None

    return genai.Client(api_key=api_key)


def format_memory_item(memory: dict) -> str:
    """memory 항목을 CLI 출력용 문자열로 변환합니다."""
    category = memory.get("category", "unknown")
    content = memory.get("content", "")
    importance = memory.get("importance", 1)
    source = memory.get("source", "unknown")
    return f"[{category}] {content} (importance={importance}, source={source})"


def print_history(limit: int = 10) -> None:
    """최근 대화 기록을 출력합니다."""
    messages = load_history()

    if not messages:
        print("저장된 대화 기록이 없습니다.")
        return

    print("\n[최근 대화 기록]")

    for message in messages[-limit:]:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        print(f"{role}: {content}")


def print_memories() -> None:
    """저장된 장기 메모리를 출력합니다."""
    memories = load_memories()

    if not memories:
        print("저장된 메모리가 없습니다.")
        return

    print("\n[저장된 메모리]")

    for memory in memories:
        print(format_memory_item(memory))


def print_help() -> None:
    """CLI 도움말을 출력합니다."""
    print(HELP_TEXT)


def handle_command(command: str) -> bool:
    """명령어를 처리합니다. 계속 실행할지 여부를 반환합니다."""
    normalized_command = command.strip().lower()

    if normalized_command in EXIT_COMMANDS:
        print("대화를 종료합니다.")
        return False

    if normalized_command == "/help":
        print_help()
        return True

    if normalized_command == "/history":
        print_history()
        return True

    if normalized_command == "/memory":
        print_memories()
        return True

    if normalized_command == "/clear":
        clear_history()
        print("대화 기록을 초기화했습니다.")
        return True

    if normalized_command == "/clear-memory":
        clear_memories()
        print("장기 메모리를 초기화했습니다.")
        return True

    print("알 수 없는 명령입니다. /help를 입력해 사용 가능한 명령을 확인하세요.")
    return True


def build_llm_prompt(user_message: str, recent_context: str, memory_context: str) -> str:
    """Gemini에 전달할 프롬프트를 구성합니다."""
    context_sections: list[str] = []

    if recent_context:
        context_sections.append(f"[최근 대화 context]\n{recent_context}")

    if memory_context:
        context_sections.append(f"[관련 장기 메모리]\n{memory_context}")

    context_text = "\n\n".join(context_sections)

    return f"""
{SYSTEM_PROMPT}

다음 정보를 참고해 사용자의 질문에 답변하세요.

{context_text if context_text else "참고할 context나 memory가 아직 없습니다."}

[현재 사용자 질문]
{user_message}
""".strip()


def generate_answer(user_message: str, recent_context: str, memory_context: str) -> str:
    """Gemini API를 호출해 답변을 생성합니다."""
    client = get_gemini_client()

    if client is None:
        return (
            "LLM을 호출할 수 없습니다.\n"
            "google-genai 패키지 설치 여부와 GEMINI_API_KEY 환경 변수를 확인해 주세요."
        )

    prompt = build_llm_prompt(
        user_message=user_message,
        recent_context=recent_context,
        memory_context=memory_context,
    )

    try:
        config = None

        if types is not None:
            config = types.GenerateContentConfig(
                temperature=0.3,
            )

        response = client.models.generate_content(
            model=get_llm_model(),
            contents=prompt,
            config=config,
        )
    except Exception as error:
        return f"LLM 호출 중 오류가 발생했습니다: {error}"

    answer = getattr(response, "text", None)

    if not answer:
        return "LLM이 빈 응답을 반환했습니다."

    return answer.strip()


def save_memory_if_needed(user_message: str, assistant_message: str) -> None:
    """필요한 경우 대화 내용을 장기 메모리로 저장합니다."""
    if update_memory_from_conversation is None:
        return

    memory = update_memory_from_conversation(user_message, assistant_message)

    if memory is not None:
        print("\n[memory saved]")
        print(format_memory_item(memory))


def run_chat_turn(user_message: str) -> str:
    """사용자 입력 1건에 대해 context 구성, 답변 생성, 기록 저장을 수행합니다."""
    history = load_history()
    recent_context = build_recent_context(history, limit=6)
    memories = load_memories()
    retrieved_memories = retrieve_memory(user_message, memories, top_k=3)
    memory_context = build_memory_context(retrieved_memories)

    assistant_message = generate_answer(
        user_message=user_message,
        recent_context=recent_context,
        memory_context=memory_context,
    )

    append_message("user", user_message)
    append_message("assistant", assistant_message)
    save_memory_if_needed(user_message, assistant_message)

    return assistant_message


def run_chat_loop() -> None:
    """대화형 CLI를 실행합니다."""
    print("Chapter 11 Memory Chat CLI")
    print("명령어 목록을 보려면 /help를 입력하세요.")
    print("종료하려면 /exit를 입력하세요.\n")

    while True:
        user_input = input("사용자> ").strip()

        if not user_input:
            continue

        if user_input.startswith("/") or user_input.lower() in EXIT_COMMANDS:
            should_continue = handle_command(user_input)

            if not should_continue:
                break

            print()
            continue

        assistant_message = run_chat_turn(user_input)
        print(f"에이전트> {assistant_message}\n")


def main() -> None:
    """프로그램 진입점입니다."""
    run_chat_loop()


if __name__ == "__main__":
    main()