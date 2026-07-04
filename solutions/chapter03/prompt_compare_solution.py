"""Chapter 3 mini project solution: compare basic and improved prompts.

Run from the project root:
    python solutions/chapter03/prompt_compare_solution.py

This script uses the same .env settings as the previous chapters.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DEFAULT_MODEL = "gemini-flash-lite-latest"
DEFAULT_TOPIC = "AI Agent"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

try:
    from prompt_template import make_tutor_prompt
except ImportError as error:
    raise ImportError(
        "app/prompt_template.py 파일을 먼저 작성해야 합니다. "
        "Chapter 3의 '프롬프트 템플릿 함수 만들기' 실습을 확인하세요."
    ) from error


CHECKLIST = [
    "설명이 구체적인가?",
    "초보자에게 적절한가?",
    "요청한 길이 조건을 지키는가?",
    "출력 형식이 안정적인가?",
    "실무 예시가 포함되었는가?",
]


def load_settings() -> tuple[str, str]:
    """Load Gemini API settings from .env."""
    load_dotenv(PROJECT_ROOT / ".env")

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL_NAME", DEFAULT_MODEL)

    if not api_key or api_key == "your_api_key_here":
        raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인하세요.")

    return api_key, model


def create_client() -> tuple[genai.Client, str]:
    api_key, model = load_settings()
    client = genai.Client(api_key=api_key)
    return client, model


def build_basic_prompt(topic: str) -> str:
    """Create a short baseline prompt."""
    return f"{topic} 설명해 줘."


def ask_gemini(client: genai.Client, model: str, prompt: str) -> str:
    interaction = client.interactions.create(
        model=model,
        input=prompt,
    )
    return interaction.output_text


def print_checklist() -> None:
    print("\n[비교 체크리스트]")
    for item in CHECKLIST:
        print(f"- {item}")


def build_markdown_report(
    topic: str,
    model: str,
    basic_prompt: str,
    basic_answer: str,
    improved_prompt: str,
    improved_answer: str,
) -> str:
    checklist_text = "\n".join(f"- {item}" for item in CHECKLIST)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# Chapter 3 미니 프로젝트 결과

## 실행 정보

- 비교 주제: {topic}
- 사용 모델: {model}
- 생성 시각: {created_at}

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

{checklist_text}

## 결과 해석

기본 프롬프트는 짧고 빠르게 질문할 수 있지만, 답변 길이와 구조가 일정하지 않을 수 있습니다.  
개선 프롬프트는 역할, 맥락, 작업, 제약조건, 출력 형식을 명확히 지정하기 때문에 더 구조화된 응답을 얻기 쉽습니다.
"""


def save_report(content: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "chapter03_prompt_compare_solution.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> None:
    try:
        client, model = create_client()
    except Exception as error:
        print("초기 설정 중 오류가 발생했습니다.")
        print(error)
        return

    topic = input(f"비교할 주제를 입력하세요 [{DEFAULT_TOPIC}]: ").strip() or DEFAULT_TOPIC

    basic_prompt = build_basic_prompt(topic)
    improved_prompt = make_tutor_prompt(topic)

    print("\n[기본 프롬프트]")
    print(basic_prompt)

    print("\n[개선 프롬프트]")
    print(improved_prompt)

    try:
        basic_answer = ask_gemini(client, model, basic_prompt)
        improved_answer = ask_gemini(client, model, improved_prompt)
    except Exception as error:
        print("\nGemini API 호출 중 오류가 발생했습니다.")
        print(error)
        return

    print("\n[기본 프롬프트 응답]")
    print(basic_answer)

    print("\n[개선 프롬프트 응답]")
    print(improved_answer)

    print_checklist()

    report = build_markdown_report(
        topic=topic,
        model=model,
        basic_prompt=basic_prompt,
        basic_answer=basic_answer,
        improved_prompt=improved_prompt,
        improved_answer=improved_answer,
    )
    output_path = save_report(report)
    print(f"\n미니 프로젝트 결과를 {output_path} 파일에 저장했습니다.")


if __name__ == "__main__":
    main()
