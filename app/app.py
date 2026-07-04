import os
from dotenv import load_dotenv
from google import genai


QUESTION = "AI Agent Engineering을 한 문장으로 설명해 주세요."


def load_settings() -> tuple[str, str]:
    """.env 파일에서 Gemini API Key와 모델명을 읽습니다."""
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL_NAME")

    if not api_key or api_key == "your_api_key_here":
        raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인하세요.")

    if not model:
        raise ValueError("GEMINI_MODEL_NAME이 설정되어 있지 않습니다. .env 파일을 확인하세요.")

    return api_key, model


def main() -> None:
    api_key, model = load_settings()
    client = genai.Client(api_key=api_key)

    interaction = client.interactions.create(
        model=model,
        input=QUESTION,
    )

    print(f"사용 모델: {model}")
    print("Gemini 응답:")
    print(interaction.output_text)


if __name__ == "__main__":
    main()
