"""
Chapter 07 pgvector chunk 저장소

chunk를 PostgreSQL pgvector 테이블에 저장하고 검색하는 공통 함수를 제공합니다.
Chapter 06의 pgvector_client.py(연결, 벡터 문자열 변환)를 그대로 재사용합니다.
"""

import psycopg

from pgvector_client import EMBEDDING_DIMENSION, to_vector_literal

CHUNK_TABLE_NAME = "course_policy_chunks"


def ensure_chunk_table(conn: psycopg.Connection) -> None:
    """chunk 저장 테이블이 없으면 만듭니다.

    같은 chunk ID라도 청킹 전략(strategy)이 다르면 다른 행이 되도록
    (strategy, id)를 함께 기본키로 사용합니다.
    """
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CHUNK_TABLE_NAME} (
                strategy TEXT NOT NULL,
                id TEXT NOT NULL,
                source TEXT NOT NULL,
                section TEXT NOT NULL,
                paragraph_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_size INTEGER NOT NULL,
                chunk_overlap INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector({EMBEDDING_DIMENSION}) NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                PRIMARY KEY (strategy, id)
            )
            """
        )
    conn.commit()


def save_chunks(
    conn: psycopg.Connection,
    strategy: str,
    chunk_items: list[dict],
    embeddings: list[list[float]],
) -> int:
    """한 전략의 chunk를 upsert하고, 문서에서 사라진 chunk는 삭제합니다.

    반환값은 삭제된 이전 chunk 수입니다.
    """
    rows = []
    for item, embedding in zip(chunk_items, embeddings):
        metadata = item["metadata"]
        rows.append(
            (
                strategy,
                item["id"],
                metadata["source"],
                metadata["section"],
                metadata["paragraph_id"],
                metadata["chunk_index"],
                metadata["chunk_size"],
                metadata["chunk_overlap"],
                item["text"],
                to_vector_literal(embedding),
            )
        )

    with conn.cursor() as cur:
        cur.executemany(
            f"""
            INSERT INTO {CHUNK_TABLE_NAME}
                (strategy, id, source, section, paragraph_id, chunk_index,
                 chunk_size, chunk_overlap, content, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
            ON CONFLICT (strategy, id) DO UPDATE SET
                source = EXCLUDED.source,
                section = EXCLUDED.section,
                paragraph_id = EXCLUDED.paragraph_id,
                chunk_index = EXCLUDED.chunk_index,
                chunk_size = EXCLUDED.chunk_size,
                chunk_overlap = EXCLUDED.chunk_overlap,
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                updated_at = now()
            """,
            rows,
        )

        sources = sorted({row[2] for row in rows})
        cur.execute(
            f"""
            DELETE FROM {CHUNK_TABLE_NAME}
            WHERE strategy = %s AND source = ANY(%s) AND NOT (id = ANY(%s))
            """,
            (strategy, sources, [row[1] for row in rows]),
        )
        deleted = cur.rowcount

    conn.commit()
    return deleted


def search_chunks_by_vector(
    conn: psycopg.Connection,
    question_embedding: list[float],
    strategy: str,
    top_k: int = 3,
) -> list[dict]:
    """한 전략의 chunk 중 질문과 코사인 거리가 가장 가까운 top_k개를 반환합니다."""
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT id, source, section, paragraph_id, chunk_index, content,
                   embedding <=> %s::vector AS distance
            FROM {CHUNK_TABLE_NAME}
            WHERE strategy = %s
            ORDER BY distance
            LIMIT %s
            """,
            (to_vector_literal(question_embedding), strategy, top_k),
        )
        rows = cur.fetchall()

    return [
        {
            "chunk_id": chunk_id,
            "text": content,
            "metadata": {
                "strategy": strategy,
                "source": source,
                "section": section,
                "paragraph_id": paragraph_id,
                "chunk_index": chunk_index,
            },
            "distance": float(distance),
        }
        for chunk_id, source, section, paragraph_id, chunk_index, content, distance in rows
    ]
