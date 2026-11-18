"""
Chapter 06 pgvector 클라이언트 유틸리티

로컬 PostgreSQL에 연결하고,
pgvector 확장과 course_notice_paragraphs 테이블을 준비합니다.
"""

import os

import psycopg
from dotenv import load_dotenv


TABLE_NAME = "course_notice_paragraphs"
EMBEDDING_DIMENSION = 384  # app/embedding_client.py 로컬 임베딩 모델의 출력 차원


def load_db_settings() -> dict:
    """.env 파일에서 PostgreSQL 접속 정보를 읽습니다."""
    load_dotenv()

    missing = [key for key in ("DB_NAME", "DB_USER", "DB_PASSWORD") if not os.getenv(key)]
    if missing:
        raise ValueError(
            f".env 파일에 PostgreSQL 접속 정보가 없습니다: {', '.join(missing)}\n"
            "DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD를 설정하세요."
        )

    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }


def get_connection() -> psycopg.Connection:
    """로컬 PostgreSQL에 연결합니다."""
    return psycopg.connect(**load_db_settings(), connect_timeout=5)


def to_vector_literal(values: list[float]) -> str:
    """Python 숫자 리스트를 pgvector 입력 형식 '[0.1,0.2,...]'로 바꿉니다."""
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def ensure_table(conn: psycopg.Connection) -> None:
    """pgvector 확장과 문단 저장 테이블이 없으면 만듭니다."""
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
        if cur.fetchone() is None:
            raise RuntimeError(
                "PostgreSQL 서버에 pgvector 확장이 설치되어 있지 않습니다.\n"
                "pgvector를 설치한 뒤 다시 실행하세요."
            )

        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                paragraph_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector({EMBEDDING_DIMENSION}) NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    conn.commit()


def count_paragraphs(conn: psycopg.Connection) -> int:
    """테이블에 저장된 문단 개수를 셉니다."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {TABLE_NAME}")
        return cur.fetchone()[0]


def main() -> None:
    """PostgreSQL 연결과 테이블 준비 상태를 간단히 확인합니다."""
    with get_connection() as conn:
        ensure_table(conn)

        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), extversion FROM pg_extension WHERE extname = 'vector'")
            database, version = cur.fetchone()

        print("pgvector 테이블 준비 완료")
        print(f"Database: {database}")
        print(f"pgvector version: {version}")
        print(f"Table name: {TABLE_NAME}")
        print(f"Paragraph count: {count_paragraphs(conn)}")


if __name__ == "__main__":
    main()
