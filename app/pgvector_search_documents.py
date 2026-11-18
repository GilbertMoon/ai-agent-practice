"""
Chapter 06 pgvector 문단 검색

질문을 임베딩한 뒤 pgvector의 코사인 거리 연산자 <=>로
가장 가까운 문단을 찾습니다.
"""

from embedding_client import embed_text
from pgvector_client import TABLE_NAME, get_connection, to_vector_literal


def prepare_query(question: str) -> str:
    """질문을 검색용 임베딩 입력 형식으로 변환합니다."""
    return f"task: search result | query: {question}"


def search_documents(question: str, top_k: int = 3) -> list[dict]:
    """질문과 코사인 거리가 가장 가까운 문단 top_k개를 반환합니다."""
    query_vector = to_vector_literal(embed_text(prepare_query(question)))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, source, paragraph_id, content,
                       embedding <=> %s::vector AS distance
                FROM {TABLE_NAME}
                ORDER BY distance
                LIMIT %s
                """,
                (query_vector, top_k),
            )
            rows = cur.fetchall()

    items = []
    for doc_id, source, paragraph_id, content, distance in rows:
        items.append(
            {
                "id": doc_id,
                "document": content,
                "metadata": {"source": source, "paragraph_id": paragraph_id},
                "distance": float(distance),
            }
        )

    return items


def print_search_results(search_results: list[dict]) -> None:
    print("\n검색된 관련 문단:")

    if not search_results:
        print("검색 결과가 없습니다. 먼저 python app/pgvector_index_documents.py를 실행하세요.")
        return

    for item in search_results:
        metadata = item["metadata"]
        print(f"문단 ID: {item['id']}")
        print(f"출처: {metadata['source']}")
        print(f"문단 번호: {metadata['paragraph_id']}")
        print(f"distance: {item['distance']:.4f}")
        print(item["document"])
        print()


def main() -> None:
    print("pgvector 문서 검색 프로그램")
    print("검색 전에 python app/pgvector_index_documents.py를 먼저 실행해야 합니다.")
    print()

    question = input("질문을 입력하세요: ").strip()

    if not question:
        print("질문이 입력되지 않았습니다.")
        return

    search_results = search_documents(question, top_k=3)
    print_search_results(search_results)


if __name__ == "__main__":
    main()
