from document_prompt import build_document_prompt, read_text_file
from gemini_client import ask_gemini


def main() -> None:
    document = read_text_file("data/course_notice.txt")
    question = input("질문을 입력하세요: ").strip()

    prompt = build_document_prompt(document, question)
    answer = ask_gemini(prompt)

    print("\n답변:")
    print(answer)


if __name__ == "__main__":
    main()