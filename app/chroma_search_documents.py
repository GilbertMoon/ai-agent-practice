from chroma_client import get_chroma_collection
from embedding_client import embed_text


def prepare_query(question: str) -> str:
    return f"task: search result | query: {question}"


def search_documents(question: str, top_k: int = 3) -> list[dict]:
    collection = get_chroma_collection()
    query_embedding = embed_text(prepare_query(question))

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    items = []
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        items.append(
            {
                "id": doc_id,
                "document": document,
                "metadata": metadata,
                "distance": distance,
            }
        )

    return items


def print_search_results(search_results: list[dict]) -> None:
    print("\n검색된 관련 문단:")

    if not search_results:
        print("검색 결과가 없습니다. 먼저 python app/chroma_index_documents.py를 실행하세요.")
        return

    for item in search_results:
        metadata = item["metadata"] or {}
        print(f"문단 ID: {item['id']}")
        print(f"출처: {metadata.get('source', 'unknown')}")
        print(f"문단 번호: {metadata.get('paragraph_id', 'unknown')}")
        print(f"distance: {item['distance']:.4f}")
        print(item["document"])
        print()


def main() -> None:
    print("Chroma 문서 검색 프로그램")
    print("검색 전에 python app/chroma_index_documents.py를 먼저 실행해야 합니다.")
    print()

    question = input("질문을 입력하세요: ").strip()

    if not question:
        print("질문이 입력되지 않았습니다.")
        return

    search_results = search_documents(question, top_k=3)
    print_search_results(search_results)


if __name__ == "__main__":
    main()
