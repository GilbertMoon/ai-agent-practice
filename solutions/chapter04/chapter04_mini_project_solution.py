"""Chapter 04 미니 프로젝트 정답 예시

수업 공지 문서 기반 Q&A 챗봇입니다.
프로젝트 루트에서 다음 명령으로 실행할 수 있습니다.

    python solutions/chapter04/chapter04_mini_project_solution.py

주의:
- .env 파일에 GEMINI_API_KEY가 설정되어 있어야 합니다.
- .env 파일은 GitHub에 올리지 않습니다.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
DATA_FILE = PROJECT_ROOT / "data" / "course_notice.txt"
LOG_FILE = PROJECT_ROOT / "outputs" / "chapter04_document_qa_log.md"

# solutions/chapter04 폴더에서 실행해도 app 폴더의 공통 함수를 불러올 수 있도록 설정합니다.
sys.path.append(str(APP_DIR))
os.chdir(PROJECT_ROOT)

from document_prompt import (  # noqa: E402
    build_document_prompt,
    find_relevant_paragraphs,
    read_text_file,
)
from gemini_client import ask_gemini  # noqa: E402


def build_context(document: str, question: str) -> tuple[str, list[str]]:
    """질문과 관련 있는 문단을 찾아 context를 만듭니다."""
    relevant_paragraphs = find_relevant_paragraphs(document, question, top_k=3)

    if not relevant_paragraphs:
        return "관련 문단을 찾지 못했습니다.", []

    context = "\n\n".join(relevant_paragraphs)
    return context, relevant_paragraphs


def save_log(question: str, context: str, answer: str) -> None:
    """질문, 선택된 문단, 답변을 Markdown 로그 파일로 저장합니다."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_text = f"""
## {now}

### 질문

{question}

### 선택된 문단

```text
{context}
```

### 답변

{answer}

---
"""

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(log_text)


def answer_question(document: str, question: str) -> tuple[str, str]:
    """문서에서 관련 문단을 찾고 Gemini로 답변을 생성합니다."""
    context, _ = build_context(document, question)
    prompt = build_document_prompt(context, question)
    answer = ask_gemini(prompt)
    return context, answer


def main() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"문서 파일을 찾을 수 없습니다: {DATA_FILE}\n"
            "data/course_notice.txt 파일을 먼저 준비하세요."
        )

    document = read_text_file(str(DATA_FILE))

    print("문서 기반 Q&A 프로그램")
    print("종료하려면 exit를 입력하세요.")
    print()

    while True:
        question = input("질문: ").strip()

        if question.lower() in {"exit", "quit", "q"}:
            print("프로그램을 종료합니다.")
            break

        if not question:
            print("질문을 입력하세요.")
            continue

        context, answer = answer_question(document, question)

        print("\n선택된 문단:")
        print(context)
        print("\n답변:")
        print(answer)
        print()

        save_log(question, context, answer)
        print(f"로그 저장 위치: {LOG_FILE}")
        print("-" * 60)


if __name__ == "__main__":
    main()
