"""
Chapter 07 chunk 인덱싱

긴 문서를 section 단위로 묶어 chunk로 나누고, 각 chunk의 임베딩을 pgvector 테이블에 저장합니다.
"""

from pathlib import Path

from chunk_utils import split_sections_to_chunks
from document_prompt import read_text_file, split_paragraphs
from embedding_client import embed_text
from pgvector_chunk_store import CHUNK_TABLE_NAME, ensure_chunk_table, save_chunks
from pgvector_client import get_connection

DATA_FILE = "data/course_policy_long.txt"
SOURCE_NAME = Path(DATA_FILE).name
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
STRATEGY = f"size{CHUNK_SIZE}_overlap{CHUNK_OVERLAP}"


def prepare_document_for_embedding(chunk_text: str, metadata: dict) -> str:
    """임베딩 입력에 본문과 기본 metadata를 함께 넣습니다."""
    return (
        f"source: {metadata['source']} | "
        f"section: {metadata['section']} | "
        f"paragraph_id: {metadata['paragraph_id']} | "
        f"chunk_index: {metadata['chunk_index']} | "
        f"text: {chunk_text}"
    )


def main() -> None:
    document = read_text_file(DATA_FILE)
    paragraphs = split_paragraphs(document)

    chunk_items = split_sections_to_chunks(
        paragraphs=paragraphs,
        source=SOURCE_NAME,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    if not chunk_items:
        print("인덱싱할 chunk가 없습니다.")
        return

    embeddings = [
        embed_text(prepare_document_for_embedding(item["text"], item["metadata"]))
        for item in chunk_items
    ]

    with get_connection() as conn:
        ensure_chunk_table(conn)
        deleted = save_chunks(conn, STRATEGY, chunk_items, embeddings)

    print("Chapter 7 chunk 인덱싱 완료")
    print(f"문서: {DATA_FILE}")
    print(f"테이블: {CHUNK_TABLE_NAME}")
    print(f"strategy: {STRATEGY}")
    print(f"chunk_size: {CHUNK_SIZE}")
    print(f"chunk_overlap: {CHUNK_OVERLAP}")
    print(f"저장된 chunk 수: {len(chunk_items)}")
    print(f"삭제된 이전 chunk 수: {deleted}")


if __name__ == "__main__":
    main()
