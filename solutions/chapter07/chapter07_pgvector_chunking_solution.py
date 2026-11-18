"""Chapter 07 미니 프로젝트 정답 예시

네 가지 청킹 전략으로 data/course_policy_long.txt를 PostgreSQL pgvector 테이블
(course_policy_chunks)에 저장하고, 질문별 top 3 검색 결과와 간단한 관련성 점수를
outputs/chapter07_chunking_comparison.md로 저장합니다.

    python solutions/chapter07/chapter07_pgvector_chunking_solution.py

사전 준비: Chapter 06의 .env(DB_*) 설정과 pgvector 확장이 필요합니다.
관련성 점수는 키워드 기반 추정값이므로 최종 판단은 사람이 원문을 보고 합니다.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from chunk_utils import split_paragraphs_to_chunks, split_sections_to_chunks
from document_prompt import read_text_file, split_paragraphs
from embedding_client import embed_text
from pgvector_chunk_store import ensure_chunk_table, save_chunks, search_chunks_by_vector
from pgvector_client import get_connection

DATA_FILE = PROJECT_ROOT / "data" / "course_policy_long.txt"
SOURCE_NAME = DATA_FILE.name
OUTPUT_FILE = PROJECT_ROOT / "outputs" / "chapter07_chunking_comparison.md"
TOP_K = 3

STRATEGIES = [
    {
        "name": "paragraph",
        "unit": "paragraph",
        "description": "문단 하나를 chunk 하나로 사용",
        "chunk_size": 2000,
        "chunk_overlap": 0,
    },
    {
        "name": "size300_overlap0",
        "unit": "section",
        "description": "section 본문을 300자 단위로, overlap 없음",
        "chunk_size": 300,
        "chunk_overlap": 0,
    },
    {
        "name": "size300_overlap50",
        "unit": "section",
        "description": "section 본문을 300자 단위로, 50자 overlap",
        "chunk_size": 300,
        "chunk_overlap": 50,
    },
    {
        "name": "size500_overlap100",
        "unit": "section",
        "description": "section 본문을 500자 단위로, 100자 overlap",
        "chunk_size": 500,
        "chunk_overlap": 100,
    },
]

EVAL_QUESTIONS = [
    "API Key는 어디에 저장해야 하나요?",
    "과제 제출 기한은 언제인가요?",
    "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
    "미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?",
]


def prepare_text_for_embedding(text: str, metadata: dict) -> str:
    """chunk 본문과 metadata를 함께 사용해 임베딩 입력을 만듭니다."""
    return (
        f"source: {metadata['source']} | "
        f"section: {metadata['section']} | "
        f"paragraph_id: {metadata['paragraph_id']} | "
        f"chunk_index: {metadata['chunk_index']} | "
        f"text: {text}"
    )


def prepare_question_for_embedding(question: str) -> str:
    """질문 임베딩 입력을 만듭니다."""
    return f"question: {question}"


def build_strategy_chunks(strategy: dict) -> list[dict]:
    """하나의 청킹 전략에 따라 문서를 chunk 목록으로 변환합니다."""
    document = read_text_file(str(DATA_FILE))
    paragraphs = split_paragraphs(document)

    splitter = split_paragraphs_to_chunks if strategy["unit"] == "paragraph" else split_sections_to_chunks
    chunk_items = splitter(
        paragraphs=paragraphs,
        source=SOURCE_NAME,
        chunk_size=strategy["chunk_size"],
        chunk_overlap=strategy["chunk_overlap"],
    )

    return chunk_items


def index_strategy(conn, strategy: dict) -> int:
    """특정 청킹 전략으로 생성한 chunk를 pgvector 테이블에 저장합니다."""
    chunk_items = build_strategy_chunks(strategy)
    embeddings = [
        embed_text(prepare_text_for_embedding(item["text"], item["metadata"]))
        for item in chunk_items
    ]
    save_chunks(conn, strategy["name"], chunk_items, embeddings)
    return len(chunk_items)


def search_by_strategy(conn, question: str, strategy_name: str) -> list[dict]:
    """특정 전략으로 저장된 chunk만 대상으로 검색합니다(WHERE strategy = ...)."""
    question_embedding = embed_text(prepare_question_for_embedding(question))
    return search_chunks_by_vector(conn, question_embedding, strategy_name, TOP_K)


def get_top_results(results: list[dict]) -> list[dict]:
    """pgvector 검색 결과를 보기 쉬운 dict 목록으로 변환합니다."""
    rows = []

    for rank, item in enumerate(results, start=1):
        metadata = item["metadata"]
        rows.append(
            {
                "rank": rank,
                "chunk_id": item["chunk_id"],
                "source": metadata["source"],
                "section": metadata["section"],
                "paragraph_id": metadata["paragraph_id"],
                "chunk_index": metadata["chunk_index"],
                "distance": round(item["distance"], 4),
                "text": item["text"].replace("\n", " ")[:160],
            }
        )

    return rows


def estimate_relevance(question: str, text: str) -> int:
    """검색 결과의 관련성을 간단히 추정합니다. 실제 평가는 사람이 함께 확인합니다."""
    question_keywords = {
        "API Key": ["API Key", ".env", "GitHub"],
        "과제 제출": ["과제", "제출", "기한"],
        "오류 질문": ["오류", "에러", "명령어", "메시지"],
        "미니 프로젝트": ["미니 프로젝트", "결과물", "비교 로그"],
    }

    for key, keywords in question_keywords.items():
        if key in question:
            matched_count = sum(1 for keyword in keywords if keyword in text)
            if matched_count >= 2:
                return 2
            if matched_count == 1:
                return 1
            return 0

    return 1


def write_comparison_report(rows: list[dict]) -> None:
    """검색 비교 결과를 Markdown 파일로 저장합니다."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Chapter 7 청킹 전략별 검색 결과 비교",
        "",
        f"입력 문서: `{DATA_FILE.relative_to(PROJECT_ROOT)}`",
        f"검색 결과 수: top {TOP_K}",
        "",
        "## 비교 기준",
        "",
        "- 관련성 2점: 질문에 직접 답할 수 있는 chunk",
        "- 관련성 1점: 일부 관련은 있지만 근거가 부족한 chunk",
        "- 관련성 0점: 질문과 관련이 낮은 chunk",
        "",
        "## 전략별 검색 결과 요약",
        "",
        "| 질문 | 전략 | rank | chunk_id | section | distance | 관련성 | text 요약 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in rows:
        lines.append(
            "| {question} | {strategy} | {rank} | {chunk_id} | {section} | {distance} | {relevance} | {text} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## 해석 가이드",
            "",
            "- distance는 pgvector 코사인 거리(<=>)이며 낮을수록 질문과 가까운 벡터입니다.",
            "- 하지만 distance만으로 검색 품질을 판단하지 않습니다.",
            "- 검색된 chunk가 실제로 질문에 답할 수 있는지 사람이 함께 확인해야 합니다.",
            "- chunk_size가 너무 크면 여러 주제가 섞일 수 있습니다.",
            "- chunk_size가 너무 작으면 답변에 필요한 맥락이 부족할 수 있습니다.",
            "- overlap은 chunk 경계에서 문장이 잘리는 문제를 줄이는 데 도움이 됩니다.",
        ]
    )

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    conn = get_connection()
    ensure_chunk_table(conn)

    print("청킹 전략별 인덱싱을 시작합니다.")

    for strategy in STRATEGIES:
        count = index_strategy(conn, strategy)
        print(f"{strategy['name']}: {count}개 chunk 저장")

    comparison_rows = []

    print("\n청킹 전략별 검색 결과를 비교합니다.")

    for question in EVAL_QUESTIONS:
        print(f"\n질문: {question}")

        for strategy in STRATEGIES:
            strategy_name = strategy["name"]
            results = search_by_strategy(conn, question, strategy_name)
            top_results = get_top_results(results)

            if not top_results:
                print(f"- {strategy_name}: 검색 결과 없음")
                comparison_rows.append(
                    {
                        "question": question,
                        "strategy": strategy_name,
                        "rank": "-",
                        "chunk_id": "-",
                        "section": "-",
                        "distance": "-",
                        "relevance": 0,
                        "text": "검색 결과 없음",
                    }
                )
                continue

            first = top_results[0]
            print(
                f"- {strategy_name}: "
                f"chunk_id={first['chunk_id']}, "
                f"distance={first['distance']}"
            )

            for result in top_results:
                relevance = estimate_relevance(question, result["text"])

                comparison_rows.append(
                    {
                        "question": question,
                        "strategy": strategy_name,
                        "rank": result["rank"],
                        "chunk_id": result["chunk_id"],
                        "section": result["section"],
                        "distance": result["distance"],
                        "relevance": relevance,
                        "text": result["text"],
                    }
                )

    conn.close()
    write_comparison_report(comparison_rows)

    print(f"\n비교 결과 저장 완료: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
