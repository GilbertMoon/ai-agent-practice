import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

from prompt_template import make_tutor_prompt


OUTPUT_PATH = Path("outputs") / "chapter03_prompt_compare.md"


def load_settings() -> tuple[str, str]:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL_NAME")

    if not api_key or api_key == "your_api_key_here":
        raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인하세요.")

    if not model:
        raise ValueError("GEMINI_MODEL_NAME이 설정되어 있지 않습니다. .env 파일을 확인하세요.")

    return api_key, model


def create_client() -> tuple[genai.Client, str]:
    api_key, model = load_settings()
    client = genai.Client(api_key=api_key)
    return client, model


def ask_gemini(client: genai.Client, model: str, prompt: str) -> str:
    interaction = client.interactions.create(
        model=model,
        input=prompt,
    )
    return interaction.output_text


def build_basic_prompt(topic: str) -> str:
    return f"{topic} 설명해 줘."


def save_result(topic: str, basic_prompt: str, basic_answer: str, improved_prompt: str, improved_answer: str) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# Chapter 3 프롬프트 비교 결과

## 비교 주제

{topic}

## 기본 프롬프트

```text
{basic_prompt}
```

## 기본 프롬프트 응답

{basic_answer}

## 개선 프롬프트

```text
{improved_prompt}
```

## 개선 프롬프트 응답

{improved_answer}

## 비교 체크리스트

- 설명이 구체적인가?
- 초보자에게 적절한가?
- 출력 형식이 안정적인가?
- 실무 예시가 포함되었는가?
"""

    OUTPUT_PATH.write_text(content, encoding="utf-8")


def main() -> None:
    client, model = create_client()

    topic = input("비교할 주제를 입력하세요 [AI Agent]: ").strip()
    if not topic:
        topic = "AI Agent"

    basic_prompt = build_basic_prompt(topic)
    improved_prompt = make_tutor_prompt(topic)

    print(f"사용 모델: {model}")
    print("기본 프롬프트로 응답을 생성합니다.")
    basic_answer = ask_gemini(client, model, basic_prompt)

    print("개선 프롬프트로 응답을 생성합니다.")
    improved_answer = ask_gemini(client, model, improved_prompt)

    save_result(topic, basic_prompt, basic_answer, improved_prompt, improved_answer)

    print("결과 저장 완료:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
