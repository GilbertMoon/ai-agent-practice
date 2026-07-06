from chroma_client import get_chroma_collection
from embedding_client import embed_text

DEFAULT_QUESTION = "GitHub 관련 안내를 찾아줘."
TOP_K = 3
FILTER_KEYWORDS = ["GitHub", "오류", "제출", "보안"]


def prepare_question_for_embedding(question: str) -> str:
    return f"question: {question}"


def search_without_filter(question: str, top_k: int = TOP_K) -> dict:
    collection = get_chroma_collection()
    question_embedding = embed_text(prepare_question_for_embedding(question))

    return collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )


def search_with_document_filter(question: str, keyword: str, top_k: int = TOP_K) -> dict:
    collection = get_chroma_collection()
    question_embedding = embed_text(prepare_question_for_embedding(question))

    return collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        where_document={"$contains": keyword},
        include=["documents", "metadatas", "distances"],
    )


def print_results(title: str, results: dict) -> None:
    print("=" * 80)
    print(title)

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not ids:
        print("검색 결과가 없습니다.")
        return

    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances), start=1
    ):
        metadata = metadata or {}
        print(f"\n[{rank}] {chunk_id}")
        print(f"section: {metadata.get('section', '-')}")
        print(f"source: {metadata.get('source', '-')}")
        print(f"distance: {float(distance):.4f}")
        print(document.replace("\n", " ")[:250])


def main() -> None:
    question = input(f"질문을 입력하세요 [{DEFAULT_QUESTION}]: ").strip()
    if not question:
        question = DEFAULT_QUESTION

    print_results("필터 없이 검색", search_without_filter(question))

    for keyword in FILTER_KEYWORDS:
        results = search_with_document_filter(question, keyword)
        print_results(f"본문 키워드 필터 검색: {keyword}", results)


if __name__ == "__main__":
    main()
