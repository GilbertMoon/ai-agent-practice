from chroma_client import get_chroma_collection
from embedding_client import embed_text

DEFAULT_QUESTION = "과제 제출 기한은 언제인가요?"
TOP_K_VALUES = [1, 3, 5]


def prepare_question_for_embedding(question: str) -> str:
    return f"question: {question}"


def search_chunks(question: str, top_k: int) -> list[dict]:
    collection = get_chroma_collection()
    query_embedding = embed_text(prepare_question_for_embedding(question))
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    rows = []
    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances),
        start=1,
    ):
        rows.append(
            {
                "rank": rank,
                "chunk_id": chunk_id,
                "document": document,
                "metadata": metadata or {},
                "distance": float(distance),
            }
        )
    return rows


def print_rows(top_k: int, rows: list[dict]) -> None:
    print(f"\n[top_k={top_k}]")
    for row in rows:
        metadata = row["metadata"]
        print(f"{row['rank']}. {row['chunk_id']}")
        print(f"section: {metadata.get('section', '-')}")
        print(f"distance: {row['distance']:.4f}")
        print(row["document"][:200])
        print("-" * 60)


def main() -> None:
    question = input(f"질문을 입력하세요 [{DEFAULT_QUESTION}]: ").strip()
    if not question:
        question = DEFAULT_QUESTION

    for top_k in TOP_K_VALUES:
        rows = search_chunks(question, top_k)
        print_rows(top_k, rows)


if __name__ == "__main__":
    main()