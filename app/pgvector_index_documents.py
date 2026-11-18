"""
Chapter 06 문단 인덱싱

data/course_notice.txt를 문단으로 나누고,
각 문단의 임베딩을 PostgreSQL pgvector 테이블에 저장합니다.
"""

from document_prompt import read_text_file, split_paragraphs
from embedding_client import embed_text
from pgvector_client import TABLE_NAME, ensure_table, get_connection, to_vector_literal

DATA_FILE = "data/course_notice.txt"
SOURCE_NAME = "course_notice.txt"


def prepare_document(content: str, title: str = SOURCE_NAME) -> str:
    """문단을 검색 대상 문서 임베딩 입력 형식으로 변환합니다."""
    return f"title: {title} | text: {content}"


def build_rows(paragraphs: list[str]) -> list[tuple]:
    """문단 목록을 테이블에 저장할 행 목록으로 바꿉니다."""
    rows = []

    for index, paragraph in enumerate(paragraphs, start=1):
        doc_id = f"course_notice_{index}"
        embedding = embed_text(prepare_document(paragraph))
        rows.append((doc_id, SOURCE_NAME, index, paragraph, to_vector_literal(embedding)))

    return rows


def main() -> None:
    document = read_text_file(DATA_FILE)
    paragraphs = split_paragraphs(document)
    rows = build_rows(paragraphs)

    with get_connection() as conn:
        ensure_table(conn)

        with conn.cursor() as cur:
            # 같은 id가 이미 있으면 새 내용과 새 임베딩으로 덮어씁니다(upsert).
            cur.executemany(
                f"""
                INSERT INTO {TABLE_NAME} (id, source, paragraph_id, content, embedding)
                VALUES (%s, %s, %s, %s, %s::vector)
                ON CONFLICT (id) DO UPDATE SET
                    source = EXCLUDED.source,
                    paragraph_id = EXCLUDED.paragraph_id,
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    updated_at = now()
                """,
                rows,
            )

            # 문서에서 사라진 문단은 테이블에서도 지웁니다.
            current_ids = [row[0] for row in rows]
            cur.execute(
                f"DELETE FROM {TABLE_NAME} WHERE source = %s AND NOT (id = ANY(%s))",
                (SOURCE_NAME, current_ids),
            )
            deleted = cur.rowcount

    print(f"pgvector 인덱싱 완료: {len(rows)}개 문단")
    print(f"삭제된 이전 문단: {deleted}개")


if __name__ == "__main__":
    main()
