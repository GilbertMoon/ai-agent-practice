from chroma_client import get_chroma_collection
from embedding_client import embed_text

DEFAULT_QUESTION = "GitHub라는 단어가 포함된 안내를 찾아줘."
TOP_K = 3

FILTER_KEYWORDS = [
    "GitHub",
    "오류",
    "README.md",
    "제출",
    "보안",
]


def prepare_question_for_embedding(question: str) -> str:
    """질문 임베딩에 사용할 입력 문장을 만듭니다."""
    return f"question: {question}"


def format_metadata(metadata: dict) -> str:
    """검색 결과 metadata를 보기 좋게 문자열로 변환합니다."""
    return "\n".join(
        [
            f"source: {metadata.get('source', '-')}",
            f"section: {metadata.get('section', '-')}",
            f"paragraph_id: {metadata.get('paragraph_id', '-')}",
            f"chunk_index: {metadata.get('chunk_index', '-')}",
            f"strategy: {metadata.get('strategy', '-')}",
        ]
    )


def search_with_document_filter(
    question: str,
    keyword: str,
    top_k: int = TOP_K,
) -> dict:
    """chunk 본문에 keyword가 포함된 문서만 대상으로 검색합니다."""
    collection = get_chroma_collection()
    question_embedding = embed_text(prepare_question_for_embedding(question))

    return collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        where_document={"$contains": keyword},
        include=["documents", "metadatas", "distances"],
    )


def print_search_results(
    keyword: str,
    question: str,
    results: dict,
) -> None:
    """document text filter 검색 결과를 출력합니다."""
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    print("=" * 70)
    print(f"[본문 키워드 조건] {keyword}")
    print(f"[where_document 조건] {{'$contains': '{keyword}'}}")
    print(f"[질문] {question}")
    print(f"[top_k] {TOP_K}")
    print("=" * 70)

    if not ids:
        print("검색 결과가 없습니다.")
        print()
        return

    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances),
        start=1,
    ):
        print(f"\n[검색 결과 {rank}]")
        print(f"chunk_id: {chunk_id}")
        print(format_metadata(metadata))
        print(f"distance: {distance}")
        print()
        print(document)
        print("-" * 70)


def main() -> None:
    question = input(f"질문을 입력하세요 [{DEFAULT_QUESTION}]: ").strip()

    if not question:
        question = DEFAULT_QUESTION

    print("\ndocument text filtering 검색을 시작합니다.")
    print("Chapter 7에서 chunk 인덱싱이 먼저 완료되어 있어야 합니다.")
    print("본문 키워드가 실제 chunk에 포함된 경우에만 검색 대상이 됩니다.")
    print()

    for keyword in FILTER_KEYWORDS:
        results = search_with_document_filter(
            question=question,
            keyword=keyword,
            top_k=TOP_K,
        )

        print_search_results(
            keyword=keyword,
            question=question,
            results=results,
        )


if __name__ == "__main__":
    main()
