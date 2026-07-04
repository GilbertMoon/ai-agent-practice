from document_prompt import build_document_prompt, read_text_file, split_paragraphs
from embedding_search import build_embedded_paragraphs, search_similar_paragraphs
from gemini_client import ask_gemini


def main() -> None:
    document = read_text_file("data/course_notice.txt")
    paragraphs = split_paragraphs(document)
    embedded_paragraphs = build_embedded_paragraphs(paragraphs)

    question = input("질문을 입력하세요: ").strip()
    search_results = search_similar_paragraphs(question, embedded_paragraphs, top_k=3)
    context = "\n\n".join(item["text"] for item in search_results)

    prompt = build_document_prompt(context, question)
    answer = ask_gemini(prompt)

    print("\n검색된 관련 문단:")
    for item in search_results:
        print(f"점수: {item['score']:.4f}")
        print(item["text"])
        print()

    print("답변:")
    print(answer)


if __name__ == "__main__":
    main()