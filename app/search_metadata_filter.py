from chroma_client import get_chroma_collection
from embedding_client import embed_text

DEFAULT_QUESTION = "보안 안내에서 민감 정보 저장 방법을 알려줘."
TOP_K = 3

FILTER_EXAMPLES = [
    {
        "name": "section_filter",
        "description": "section metadata가 보안 안내인 chunk만 검색",
        "where": {"section": "보안 안내"},
    },
    {
        "name": "source_filter",
        "description": "course_policy_long.txt 문서에서 온 chunk만 검색",
        "where": {"source": "course_policy_long.txt"},
    },
    {
        "name": "strategy_filter",
        "description": "size300_overlap50 전략으로 생성된 chunk만 검색",
        "where": {"strategy": "size300_overlap50"},
    },
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


def search_with_metadata_filter(
    question: str,
    where_filter: dict,
    top_k: int = TOP_K,
):
    """metadata filter 조건을 적용해 Chroma에서 관련 chunk를 검색합니다."""
    collection = get_chroma_collection()
    question_embedding = embed_text(prepare_question_for_embedding(question))

    return collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )


def print_search_results(
    title: str,
    description: str,
    question: str,
    where_filter: dict,
    results: dict,
) -> None:
    """metadata filter 검색 결과를 출력합니다."""
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    print("=" * 70)
    print(f"[필터 이름] {title}")
    print(f"[설명] {description}")
    print(f"[질문] {question}")
    print(f"[where 조건] {where_filter}")
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

    print("\nmetadata filtering 검색을 시작합니다.")
    print("Chapter 7에서 chunk 인덱싱이 먼저 완료되어 있어야 합니다.")
    print()

    for filter_example in FILTER_EXAMPLES:
        results = search_with_metadata_filter(
            question=question,
            where_filter=filter_example["where"],
            top_k=TOP_K,
        )

        print_search_results(
            title=filter_example["name"],
            description=filter_example["description"],
            question=question,
            where_filter=filter_example["where"],
            results=results,
        )


if __name__ == "__main__":
    main()
