"""Chapter 05 미니 프로젝트 정답 예시

임베딩 기반 수업 공지 검색 Q&A 프로그램입니다.
프로젝트 루트에서 다음 명령으로 실행할 수 있습니다.

    python solutions/chapter05/chapter05_embedding_document_qa_solution.py

주의:
- .env 파일에 GEMINI_API_KEY가 설정되어 있어야 합니다.
- .env 파일은 GitHub에 올리지 않습니다.
- 문단 임베딩은 app/embedding_client.py의 로컬 임베딩 모델을 사용합니다.
- Gemini API는 검색된 문단을 근거로 최종 답변을 생성할 때 사용합니다.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
DATA_FILE = PROJECT_ROOT / "data" / "course_notice.txt"
LOG_FILE = PROJECT_ROOT / "outputs" / "chapter05_embedding_search_log.md"

# solutions/chapter05 폴더에서 실행해도 app 폴더의 공통 함수를 불러올 수 있도록 설정합니다.
sys.path.append(str(APP_DIR))
os.chdir(PROJECT_ROOT)

from document_prompt import build_document_prompt, read_text_file, split_paragraphs  # noqa: E402
from embedding_search import build_embedded_paragraphs, search_similar_paragraphs  # noqa: E402
from gemini_client import ask_gemini  # noqa: E402


def format_context(search_results: list[dict]) -> str:
    """검색 결과 문단을 프롬프트 context로 변환합니다."""
    return "\n\n".join(item["text"] for item in search_results)


def save_log(question: str, search_results: list[dict], answer: str) -> None:
    """질문, 검색 결과, 답변을 Markdown 로그 파일로 저장합니다."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result_lines = []

    for item in search_results:
        result_lines.append(f"- 문단 {item['id']} / 점수 {item['score']:.4f}\n  {item['text']}")

    log_text = f"""
## {now}

### 질문

{question}

### 검색 결과

{chr(10).join(result_lines)}

### 답변

{answer}

---
"""

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(log_text)


def main() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"문서 파일을 찾을 수 없습니다: {DATA_FILE}\n"
            "data/course_notice.txt 파일을 먼저 준비하세요."
        )

    document = read_text_file(str(DATA_FILE))
    paragraphs = split_paragraphs(document)

    print("임베딩 기반 문서 Q&A 프로그램")
    print("문단 임베딩을 생성하는 중입니다. 잠시 기다려 주세요.")
    embedded_paragraphs = build_embedded_paragraphs(paragraphs)
    print("문단 임베딩 생성 완료")
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

        search_results = search_similar_paragraphs(question, embedded_paragraphs, top_k=3)
        context = format_context(search_results)
        prompt = build_document_prompt(context, question)
        answer = ask_gemini(prompt)

        print("\n[검색된 관련 문단]")
        for item in search_results:
            print(f"문단 {item['id']} / 점수: {item['score']:.4f}")
            print(item["text"])
            print()

        print("[답변]")
        print(answer)
        print()

        save_log(question, search_results, answer)
        print(f"로그 저장 위치: {LOG_FILE}")
        print("-" * 60)


if __name__ == "__main__":
    main()
