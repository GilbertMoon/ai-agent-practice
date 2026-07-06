import os

from dotenv import load_dotenv
from google import genai

DEFAULT_MODEL = "gemini-flash-lite-latest"


def load_settings() -> tuple[str, str]:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL_NAME", DEFAULT_MODEL)

    if not api_key or api_key == "your_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY가 설정되어 있지 않습니다. "
            ".env 파일을 만들고 실제 Gemini API Key를 입력하세요."
        )

    return api_key, model


def ask_gemini(prompt: str) -> str:
    api_key, model = load_settings()
    client = genai.Client(api_key=api_key)

    interaction = client.interactions.create(
        model=model,
        input=prompt,
    )

    return interaction.output_text
