"""
Chapter 07 청킹 전략 비교

네 가지 청킹 전략으로 같은 문서를 pgvector 테이블에 저장한 뒤,
같은 질문에 대한 전략별 top 1 검색 결과를 비교합니다.
"""

from pathlib import Path

from chunk_utils import split_paragraphs_to_chunks, split_sections_to_chunks
from document_prompt import read_text_file, split_paragraphs
from embedding_client import embed_text
from pgvector_chunk_store import ensure_chunk_table, save_chunks, search_chunks_by_vector
from pgvector_client import get_connection

DATA_FILE = "data/course_policy_long.txt"
SOURCE_NAME = Path(DATA_FILE).name
OUTPUT_FILE = "outputs/chapter07_chunking_comparison.md"
TOP_K = 3

# paragraph: 문단 하나를 chunk 하나로 저장합니다.
# 나머지: section 본문을 이어 붙인 뒤 chunk_size/chunk_overlap 기준으로 나눕니다.
STRATEGIES = [
    {"name": "paragraph", "unit": "paragraph", "chunk_size": 2000, "chunk_overlap": 0},
    {"name": "size300_overlap0", "unit": "section", "chunk_size": 300, "chunk_overlap": 0},
    {"name": "size300_overlap50", "unit": "section", "chunk_size": 300, "chunk_overlap": 50},
    {"name": "size500_overlap100", "unit": "section", "chunk_size": 500, "chunk_overlap": 100},
]

EVAL_QUESTIONS = [
    "과제 제출 기한은 언제인가요?",
    "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
    "미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?",
]


def prepare_text_for_embedding(text: str, metadata: dict) -> str:
    return (
        f"source: {metadata['source']} | "
        f"section: {metadata['section']} | "
        f"paragraph_id: {metadata['paragraph_id']} | "
        f"chunk_index: {metadata['chunk_index']} | "
        f"text: {text}"
    )


def prepare_question_for_embedding(question: str) -> str:
    return f"question: {question}"


def build_strategy_chunks(strategy: dict) -> list[dict]:
    document = read_text_file(DATA_FILE)
    paragraphs = split_paragraphs(document)

    splitter = split_paragraphs_to_chunks if strategy["unit"] == "paragraph" else split_sections_to_chunks

    return splitter(
        paragraphs=paragraphs,
        source=SOURCE_NAME,
        chunk_size=strategy["chunk_size"],
        chunk_overlap=strategy["chunk_overlap"],
    )


def index_strategy(conn, strategy: dict) -> int:
    chunk_items = build_strategy_chunks(strategy)
    embeddings = [
        embed_text(prepare_text_for_embedding(item["text"], item["metadata"]))
        for item in chunk_items
    ]
    save_chunks(conn, strategy["name"], chunk_items, embeddings)
    return len(chunk_items)


def get_first_result_summary(results: list[dict]) -> dict:
    if not results:
        return {
            "chunk_id": "-",
            "section": "-",
            "distance": "-",
            "text": "검색 결과 없음",
        }

    first = results[0]
    return {
        "chunk_id": first["chunk_id"],
        "section": first["metadata"]["section"],
        "distance": round(first["distance"], 4),
        "text": first["text"].replace("\n", " ")[:120],
    }


def write_comparison_report(rows: list[dict]) -> None:
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Chapter 7 청킹 전략별 검색 결과 비교",
        "",
        f"입력 문서: `{DATA_FILE}`",
        f"검색 결과 수: top {TOP_K}",
        "",
        "| 질문 | 전략 | top 1 chunk_id | section | distance | top 1 text 요약 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for row in rows:
        lines.append(
            "| {question} | {strategy} | {chunk_id} | {section} | {distance} | {text} |".format(
                **row
            )
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = []

    with get_connection() as conn:
        ensure_chunk_table(conn)

        print("청킹 전략별 인덱싱을 시작합니다.")
        for strategy in STRATEGIES:
            count = index_strategy(conn, strategy)
            print(f"{strategy['name']}: {count}개 chunk 저장")

        print("\n청킹 전략별 검색 결과를 비교합니다.")
        for question in EVAL_QUESTIONS:
            print(f"\n질문: {question}")
            question_embedding = embed_text(prepare_question_for_embedding(question))

            for strategy in STRATEGIES:
                results = search_chunks_by_vector(conn, question_embedding, strategy["name"], TOP_K)
                summary = get_first_result_summary(results)
                rows.append({"question": question, "strategy": strategy["name"], **summary})

                print(
                    f"- {strategy['name']}: "
                    f"chunk_id={summary['chunk_id']}, "
                    f"distance={summary['distance']}"
                )

    write_comparison_report(rows)
    print(f"\n비교 결과 저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
