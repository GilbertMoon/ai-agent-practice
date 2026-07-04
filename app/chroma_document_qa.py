from chroma_index_documents import main as index_documents
from chroma_search_documents import search_documents, print_search_results
from document_prompt import build_document_prompt
from gemini_client import ask_gemini


def build_context(search_results: list[dict]) -> str:
    context_parts = []

    for item in search_results:
        metadata = item["metadata"] or {}
        source = metadata.get("source", "unknown")
        paragraph_id = metadata.get("paragraph_id", "unknown")
        distance = item["distance"]
        document = item["document"]

        context_parts.append(
            f"[문단 {paragraph_id}, source={source}, distance={distance:.4f}]\n{document}"
        )

    return "\n\n".join(context_parts)


def answer_question(question: str) -> tuple[list[dict], str]:
    search_results = search_documents(question, top_k=3)
    context = build_context(search_results)
    prompt = build_document_prompt(context, question)
    answer = ask_gemini(prompt)
    return search_results, answer


def main() -> None:
    print("Chroma 기반 문서 Q&A 프로그램")
    print("처음 실행하거나 문서가 바뀌었다면 문단 인덱싱을 먼저 수행합니다.")
    print()

    index_documents()

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

        search_results, answer = answer_question(question)
        print_search_results(search_results)

        print("[답변]")
        print(answer)
        print("-" * 60)


if __name__ == "__main__":
    main()
