"""
Chapter 07 chunk 검색

질문을 임베딩한 뒤, 기본 전략(size300_overlap50)의 chunk 중
코사인 거리가 가장 가까운 chunk를 pgvector에서 찾습니다.
"""

from embedding_client import embed_text
from pgvector_chunk_index_documents import STRATEGY
from pgvector_chunk_store import search_chunks_by_vector
from pgvector_client import get_connection

DEFAULT_QUESTION = "과제 제출 기한은 언제인가요?"
TOP_K = 3


def prepare_question_for_embedding(question: str) -> str:
    """질문 임베딩에 사용할 입력 문장을 만듭니다."""
    return f"question: {question}"


def format_metadata(metadata: dict) -> str:
    """검색 결과 metadata를 보기 좋게 문자열로 변환합니다."""
    return "\n".join(
        [
            f"source: {metadata['source']}",
            f"section: {metadata['section']}",
            f"paragraph_id: {metadata['paragraph_id']}",
            f"chunk_index: {metadata['chunk_index']}",
        ]
    )


def search_chunks(question: str, top_k: int = TOP_K) -> None:
    question_embedding = embed_text(prepare_question_for_embedding(question))

    with get_connection() as conn:
        results = search_chunks_by_vector(conn, question_embedding, STRATEGY, top_k)

    if not results:
        print("검색 결과가 없습니다. 먼저 python app/pgvector_chunk_index_documents.py를 실행하세요.")
        return

    print(f"질문: {question}")
    print(f"strategy: {STRATEGY}")
    print(f"top_k: {top_k}")
    print()

    for rank, item in enumerate(results, start=1):
        print(f"[검색 결과 {rank}]")
        print(f"chunk_id: {item['chunk_id']}")
        print(format_metadata(item["metadata"]))
        print(f"distance: {item['distance']:.4f}")
        print()
        print(item["text"])
        print("-" * 60)


def main() -> None:
    question = input(f"질문을 입력하세요 [{DEFAULT_QUESTION}]: ").strip()

    if not question:
        question = DEFAULT_QUESTION

    search_chunks(question)


if __name__ == "__main__":
    main()
