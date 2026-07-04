import os

from dotenv import load_dotenv
from google import genai

DEFAULT_MODEL = "gemini-3.5-flash"


def load_model_name() -> str:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL_NAME", DEFAULT_MODEL)

    if not api_key or api_key == "your_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY가 설정되어 있지 않습니다. "
            ".env 파일을 만들고 실제 Gemini API Key를 입력하세요."
        )

    return model


def ask_gemini(prompt: str) -> str:
    model = load_model_name()
    client = genai.Client()

    interaction = client.interactions.create(
        model=model,
        input=prompt,
    )

    return interaction.output_text