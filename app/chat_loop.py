import os
from dotenv import load_dotenv
from google import genai


DEFAULT_MODEL = "gemini-flash-lite-latest"
SYSTEM_INSTRUCTIONS = (
    "당신은 AI Agent Engineering을 처음 배우는 학습자를 위한 친절한 AI 튜터입니다. "
    "답변은 한국어로 작성하고, 초보자도 이해할 수 있도록 쉽게 설명하세요. "
    "가능하면 핵심을 먼저 말하고, 필요한 경우 짧은 예시를 덧붙이세요."
)
EXIT_COMMANDS = {"exit", "quit"}


def load_settings() -> tuple[str, str]:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL_NAME", DEFAULT_MODEL)

    if not api_key or api_key == "your_api_key_here":
        raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인하세요.")

    return api_key, model


def create_client() -> tuple[genai.Client, str]:
    api_key, model = load_settings()
    client = genai.Client(api_key=api_key)
    return client, model


def build_input(question: str) -> str:
    return f"{SYSTEM_INSTRUCTIONS}\n\n사용자 질문:\n{question}"


def ask_llm(client: genai.Client, model: str, question: str) -> str:
    interaction = client.interactions.create(
        model=model,
        input=build_input(question),
    )

    return interaction.output_text


def print_help() -> None:
    print("\n사용 방법")
    print("- 질문을 입력하면 Gemini가 답변합니다.")
    print("- 종료하려면 exit 또는 quit를 입력하세요.")
    print("- 도움말을 다시 보려면 help를 입력하세요.")


def main() -> None:
    try:
        client, model = create_client()
    except Exception as error:
        print("초기 설정 중 오류가 발생했습니다.")
        print(error)
        return

    print("Gemini 질문 응답 콘솔 프로그램")
    print(f"사용 모델: {model}")
    print("종료하려면 exit 또는 quit를 입력하세요.")

    while True:
        user_input = input("\n질문을 입력하세요: ").strip()

        if not user_input:
            print("질문을 입력해 주세요.")
            continue

        if user_input.lower() in EXIT_COMMANDS:
            print("프로그램을 종료합니다.")
            break

        if user_input.lower() == "help":
            print_help()
            continue

        try:
            answer = ask_llm(client, model, user_input)
            print("\n응답:")
            print(answer)
        except Exception as error:
            print("\nGemini API 호출 중 오류가 발생했습니다.")
            print(error)


if __name__ == "__main__":
    main()
