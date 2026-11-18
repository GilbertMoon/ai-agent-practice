"""Chapter 06 미니 프로젝트 정답 예시

PostgreSQL + pgvector 기반 수업 공지 RAG 챗봇입니다.
프로젝트 루트에서 다음 명령으로 실행할 수 있습니다.

    python solutions/chapter06/chapter06_pgvector_rag_solution.py

사전 준비:
    pip install -r requirements.txt
    로컬 PostgreSQL에 pgvector 확장이 설치되어 있어야 합니다.

주의:
- .env 파일에 GEMINI_API_KEY와 DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD가 설정되어 있어야 합니다.
- .env 파일은 GitHub에 올리지 않습니다. 벡터 데이터는 PostgreSQL 서버에 저장되므로 프로젝트 폴더에 DB 파일이 생기지 않습니다.
- 문단 임베딩과 질문 임베딩은 app/embedding_client.py의 로컬 임베딩 모델(384차원)을 사용합니다.
- Gemini API는 검색된 문단을 근거로 최종 답변을 생성할 때 사용합니다.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
DATA_FILE = PROJECT_ROOT / "data" / "course_notice.txt"
TABLE_NAME = "course_notice_paragraphs"
EMBEDDING_DIMENSION = 384

# solutions/chapter06 폴더에서 실행해도 app 폴더의 공통 함수를 불러올 수 있도록 설정합니다.
sys.path.append(str(APP_DIR))
os.chdir(PROJECT_ROOT)

from document_prompt import build_document_prompt, read_text_file, split_paragraphs  # noqa: E402
from embedding_client import embed_text  # noqa: E402
from gemini_client import ask_gemini  # noqa: E402


def prepare_query(question: str) -> str:
    """질문을 검색용 임베딩 입력 형식으로 변환합니다."""
    return f"task: search result | query: {question}"


def prepare_document(content: str, title: str = "course_notice.txt") -> str:
    """문단을 검색 대상 문서 임베딩 입력 형식으로 변환합니다."""
    return f"title: {title} | text: {content}"


def to_vector_literal(values: list[float]) -> str:
    """Python 숫자 리스트를 pgvector 입력 형식으로 바꿉니다."""
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def get_connection() -> psycopg.Connection:
    """.env의 접속 정보로 로컬 PostgreSQL에 연결합니다."""
    load_dotenv()
    missing = [key for key in ("DB_NAME", "DB_USER", "DB_PASSWORD") if not os.getenv(key)]
    if missing:
        raise ValueError(f".env 파일에 PostgreSQL 접속 정보가 없습니다: {', '.join(missing)}")

    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )


def ensure_table(conn: psycopg.Connection) -> None:
    """pgvector 확장과 문단 저장 테이블을 준비합니다."""
    with conn.cursor() as cur:
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


def index_course_notice() -> None:
    """course_notice.txt 문단을 pgvector 테이블에 저장합니다."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"문서 파일을 찾을 수 없습니다: {DATA_FILE}\n"
            "data/course_notice.txt 파일을 먼저 준비하세요."
        )

    paragraphs = split_paragraphs(read_text_file(str(DATA_FILE)))
    rows = []
    for index, paragraph in enumerate(paragraphs, start=1):
        embedding = embed_text(prepare_document(paragraph))
        rows.append((f"course_notice_{index}", DATA_FILE.name, index, paragraph, to_vector_literal(embedding)))

    with get_connection() as conn:
        ensure_table(conn)
        with conn.cursor() as cur:
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
            cur.execute(
                f"DELETE FROM {TABLE_NAME} WHERE source = %s AND NOT (id = ANY(%s))",
                (DATA_FILE.name, [row[0] for row in rows]),
            )

    print(f"pgvector 인덱싱 완료: {len(rows)}개 문단")


def search_documents(question: str, top_k: int = 3) -> list[dict]:
    """질문과 코사인 거리가 가장 가까운 문단을 pgvector에서 검색합니다."""
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

    return [
        {
            "id": doc_id,
            "document": content,
            "metadata": {"source": source, "paragraph_id": paragraph_id},
            "distance": float(distance),
        }
        for doc_id, source, paragraph_id, content, distance in rows
    ]


def build_context(search_results: list[dict]) -> str:
    """검색 결과를 RAG 프롬프트 context로 변환합니다."""
    context_parts = []

    for item in search_results:
        metadata = item["metadata"]
        context_parts.append(
            f"[문단 {metadata['paragraph_id']}, source={metadata['source']}, "
            f"distance={item['distance']:.4f}]\n{item['document']}"
        )

    return "\n\n".join(context_parts)


def answer_question(question: str) -> tuple[list[dict], str]:
    """pgvector 검색 결과를 근거로 질문에 답변합니다."""
    search_results = search_documents(question, top_k=3)
    context = build_context(search_results)
    prompt = build_document_prompt(context, question)
    answer = ask_gemini(prompt)
    return search_results, answer


def print_search_results(search_results: list[dict]) -> None:
    """검색 결과를 보기 좋게 출력합니다."""
    print("\n[검색된 관련 문단]")

    if not search_results:
        print("검색 결과가 없습니다. 문서 인덱싱 상태를 확인하세요.")
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
    print("pgvector 기반 문서 Q&A 프로그램")
    print(f"사용 문서: {DATA_FILE.relative_to(PROJECT_ROOT)}")
    print(f"저장 테이블: {TABLE_NAME}")
    print()

    index_course_notice()
    print("종료하려면 exit를 입력하세요.")
    print()

    while True:
        question = input("질문: ").strip()

        if question.lower() in {"exit", "quit", "q"}:
            print("프로그램을 종료합니다.")
            break

        if not question:
            print("질문을 입력하세요.")
            continue

        search_results, answer = answer_question(question)
        print_search_results(search_results)

        print("[답변]")
        print(answer)
        print("-" * 60)


if __name__ == "__main__":
    main()
