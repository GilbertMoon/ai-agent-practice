from chroma_client import get_chroma_collection
from embedding_client import embed_text

DEFAULT_QUESTION = "과제 제출 기한은 언제인가요?"
TOP_K = 3


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
        ]
    )


def search_chunks(question: str, top_k: int = TOP_K) -> None:
    collection = get_chroma_collection()
    question_embedding = embed_text(prepare_question_for_embedding(question))

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not ids:
        print("검색 결과가 없습니다.")
        return

    print(f"질문: {question}")
    print(f"top_k: {top_k}")
    print()

    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances),
        start=1,
    ):
        print(f"[검색 결과 {rank}]")
        print(f"chunk_id: {chunk_id}")
        print(format_metadata(metadata))
        print(f"distance: {distance}")
        print()
        print(document)
        print("-" * 60)


def main() -> None:
    question = input(f"질문을 입력하세요 [{DEFAULT_QUESTION}]: ").strip()

    if not question:
        question = DEFAULT_QUESTION

    search_chunks(question)


if __name__ == "__main__":
    main()