import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai


DEFAULT_MODEL = "gemini-flash-lite-latest"
DEFAULT_MODE = "tutor"
MIN_QUESTION_LENGTH = 5
LOG_FILE_PATH = Path("outputs") / "chat_log.txt"

EXIT_COMMANDS = {"exit", "quit"}
VALID_MODES = {"tutor", "concise", "summary"}

BASE_SYSTEM_INSTRUCTIONS = (
    "당신은 AI Agent Engineering을 처음 배우는 학습자를 위한 친절한 AI 튜터입니다. "
    "답변은 한국어로 작성하고, 초보자도 이해할 수 있도록 쉽게 설명하세요."
)

MODE_INSTRUCTIONS = {
    "tutor": (
        "친절한 튜터 스타일로 설명하세요. "
        "핵심 정의를 먼저 제시하고, 필요한 경우 쉬운 예시를 포함하세요."
    ),
    "concise": (
        "핵심만 간단히 답변하세요. "
        "가능하면 3줄 이내로 정리하세요."
    ),
    "summary": (
        "질문에 대한 답변을 반드시 한 문장으로 요약하세요. "
        "불필요한 설명은 생략하세요."
    ),
}


def load_settings() -> tuple[str, str]:
    """.env 파일에서 Gemini API Key와 모델명을 읽어옵니다."""
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL_NAME", DEFAULT_MODEL)

    if not api_key or api_key == "your_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY가 설정되어 있지 않습니다. "
            ".env 파일을 만들고 실제 Gemini API Key를 입력하세요."
        )

    return api_key, model


def create_client() -> tuple[genai.Client, str]:
    """Gemini 클라이언트와 모델명을 생성합니다."""
    api_key, model = load_settings()
    client = genai.Client(api_key=api_key)
    return client, model


def build_input(question: str, mode: str) -> str:
    """역할 지시문, 답변 모드, 사용자 질문을 하나의 입력으로 구성합니다."""
    mode_instruction = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS[DEFAULT_MODE])

    return (
        f"{BASE_SYSTEM_INSTRUCTIONS}\n"
        f"{mode_instruction}\n\n"
        f"사용자 질문:\n{question}"
    )


def ask_llm(client: genai.Client, model: str, question: str, mode: str) -> str:
    """사용자 질문을 Gemini API에 전달하고 응답 텍스트를 반환합니다."""
    interaction = client.interactions.create(
        model=model,
        input=build_input(question, mode),
    )

    return interaction.output_text


def is_valid_question(question: str) -> bool:
    """질문이 너무 짧은지 확인합니다."""
    return len(question.strip()) >= MIN_QUESTION_LENGTH


def save_chat_log(question: str, answer: str, mode: str) -> None:
    """질문과 응답을 outputs/chat_log.txt 파일에 저장합니다."""
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with LOG_FILE_PATH.open("a", encoding="utf-8") as file:
        file.write("=" * 80 + "\n")
        file.write(f"시간: {timestamp}\n")
        file.write(f"모드: {mode}\n")
        file.write(f"질문: {question}\n")
        file.write("응답:\n")
        file.write(answer.strip() + "\n")


def print_help() -> None:
    """콘솔 프로그램 사용 방법을 출력합니다."""
    print("\n사용 방법")
    print("- 질문을 입력하면 Gemini가 답변합니다.")
    print("- 종료하려면 exit 또는 quit를 입력하세요.")
    print("- 도움말을 다시 보려면 help를 입력하세요.")
    print("- 답변 모드를 바꾸려면 mode tutor, mode concise, mode summary 중 하나를 입력하세요.")
    print("  예: mode summary")
    print("- 질문과 응답은 outputs/chat_log.txt 파일에 자동 저장됩니다.")


def print_current_mode(mode: str) -> None:
    """현재 답변 모드를 설명합니다."""
    descriptions = {
        "tutor": "친절한 튜터 스타일",
        "concise": "짧고 간결한 답변 스타일",
        "summary": "한 줄 요약 스타일",
    }
    print(f"현재 답변 모드: {mode} - {descriptions.get(mode, '알 수 없음')}")


def handle_mode_command(command: str, current_mode: str) -> str:
    """mode 명령어를 처리하고 새 모드를 반환합니다."""
    parts = command.lower().split()

    if len(parts) != 2:
        print("모드 변경 형식이 올바르지 않습니다. 예: mode summary")
        return current_mode

    new_mode = parts[1]

    if new_mode not in VALID_MODES:
        print("지원하지 않는 모드입니다. 사용 가능 모드: tutor, concise, summary")
        return current_mode

    print(f"답변 모드를 {new_mode}로 변경했습니다.")
    print_current_mode(new_mode)
    return new_mode


def print_friendly_error(error: Exception) -> None:
    """API 호출 오류를 학습자가 이해하기 쉬운 메시지로 출력합니다."""
    error_message = str(error)
    lowered = error_message.lower()

    print("\nGemini API 호출 중 문제가 발생했습니다.")

    if "api key" in lowered or "apikey" in lowered:
        print("API Key 설정을 확인해 주세요. .env 파일의 GEMINI_API_KEY 값이 올바른지 확인해야 합니다.")
    elif "quota" in lowered or "rate" in lowered or "limit" in lowered:
        print("API 사용량 제한 또는 호출 제한에 걸렸을 수 있습니다. 잠시 후 다시 시도해 보세요.")
    elif "model" in lowered:
        print("모델명 설정을 확인해 주세요. .env 파일의 GEMINI_MODEL_NAME 값이 올바른지 확인해야 합니다.")
    elif "network" in lowered or "connection" in lowered or "timeout" in lowered:
        print("네트워크 연결 상태를 확인한 뒤 다시 실행해 보세요.")
    else:
        print("일시적인 오류일 수 있습니다. 설정과 네트워크 상태를 확인한 뒤 다시 시도해 보세요.")

    print("\n원본 오류 메시지:")
    print(error_message)


def main() -> None:
    """Gemini 기반 콘솔 질의응답 프로그램의 시작점입니다."""
    try:
        client, model = create_client()
    except Exception as error:
        print("초기 설정 중 오류가 발생했습니다.")
        print(error)
        return

    current_mode = DEFAULT_MODE

    print("Gemini 질문 응답 콘솔 프로그램 - Chapter 2 정답 코드")
    print(f"사용 모델: {model}")
    print_current_mode(current_mode)
    print("종료하려면 exit 또는 quit를 입력하세요.")
    print("도움말을 보려면 help를 입력하세요.")

    while True:
        user_input = input("\n질문을 입력하세요: ").strip()

        if not user_input:
            print("질문을 입력해 주세요.")
            continue

        lowered_input = user_input.lower()

        if lowered_input in EXIT_COMMANDS:
            print("프로그램을 종료합니다.")
            break

        if lowered_input == "help":
            print_help()
            continue

        if lowered_input.startswith("mode"):
            current_mode = handle_mode_command(user_input, current_mode)
            continue

        if not is_valid_question(user_input):
            print(f"질문이 너무 짧습니다. 최소 {MIN_QUESTION_LENGTH}자 이상으로 입력해 주세요.")
            continue

        try:
            answer = ask_llm(client, model, user_input, current_mode)
            print("\n응답:")
            print(answer)
            save_chat_log(user_input, answer, current_mode)
            print(f"\n대화 내용이 {LOG_FILE_PATH}에 저장되었습니다.")
        except Exception as error:
            print_friendly_error(error)


if __name__ == "__main__":
    main()
