import os

from dotenv import load_dotenv
from google import genai

EMBEDDING_MODEL = "gemini-embedding-2"


def get_api_key() -> str:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key == "your_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY가 설정되어 있지 않습니다. "
            ".env 파일을 만들고 실제 Gemini API Key를 입력하세요."
        )

    return api_key


def embed_text(text: str) -> list[float]:
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )

    return result.embeddings[0].values