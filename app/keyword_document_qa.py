from document_prompt import (
    build_document_prompt,
    find_relevant_paragraphs,
    read_text_file,
)
from gemini_client import ask_gemini


def main() -> None:
    document = read_text_file("data/course_notice.txt")
    question = input("질문을 입력하세요: ").strip()

    relevant_paragraphs = find_relevant_paragraphs(document, question)
    context = "\n\n".join(relevant_paragraphs)

    if not context:
        context = "관련 문단을 찾지 못했습니다."

    prompt = build_document_prompt(context, question)
    answer = ask_gemini(prompt)

    print("\n선택된 문단:")
    print(context)
    print("\n답변:")
    print(answer)


if __name__ == "__main__":
    main()