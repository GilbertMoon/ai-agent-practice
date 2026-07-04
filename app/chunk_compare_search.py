from pathlib import Path

from chroma_client import get_chroma_collection
from chunk_utils import split_paragraphs_to_chunks
from document_prompt import read_text_file, split_paragraphs
from embedding_client import embed_text

DATA_FILE = "data/course_policy_long.txt"
SOURCE_NAME = Path(DATA_FILE).name
OUTPUT_FILE = "outputs/chapter07_chunking_comparison.md"
TOP_K = 3

STRATEGIES = [
    {"name": "paragraph", "chunk_size": 2000, "chunk_overlap": 0},
    {"name": "size300_overlap0", "chunk_size": 300, "chunk_overlap": 0},
    {"name": "size300_overlap50", "chunk_size": 300, "chunk_overlap": 50},
    {"name": "size500_overlap100", "chunk_size": 500, "chunk_overlap": 100},
]

EVAL_QUESTIONS = [
    "과제 제출 기한은 언제인가요?",
    "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
    "미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?",
]


def prepare_text_for_embedding(text: str, metadata: dict) -> str:
    return (
        f"strategy: {metadata['strategy']} | "
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

    chunk_items = split_paragraphs_to_chunks(
        paragraphs=paragraphs,
        source=SOURCE_NAME,
        chunk_size=strategy["chunk_size"],
        chunk_overlap=strategy["chunk_overlap"],
    )

    for item in chunk_items:
        item["id"] = f"{strategy['name']}_{item['id']}"
        item["metadata"]["strategy"] = strategy["name"]

    return chunk_items


def index_strategy(collection, strategy: dict) -> int:
    chunk_items = build_strategy_chunks(strategy)

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for item in chunk_items:
        text = item["text"]
        metadata = item["metadata"]
        embedding_input = prepare_text_for_embedding(text, metadata)

        ids.append(item["id"])
        documents.append(text)
        embeddings.append(embed_text(embedding_input))
        metadatas.append(metadata)

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(ids)


def search_by_strategy(collection, question: str, strategy_name: str) -> dict:
    question_embedding = embed_text(prepare_question_for_embedding(question))

    return collection.query(
        query_embeddings=[question_embedding],
        n_results=TOP_K,
        where={"strategy": strategy_name},
        include=["documents", "metadatas", "distances"],
    )


def get_first_result_summary(results: dict) -> dict:
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not ids:
        return {
            "chunk_id": "-",
            "section": "-",
            "distance": "-",
            "text": "검색 결과 없음",
        }

    return {
        "chunk_id": ids[0],
        "section": metadatas[0].get("section", "-"),
        "distance": round(float(distances[0]), 4),
        "text": documents[0].replace("\n", " ")[:120],
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
    collection = get_chroma_collection()

    print("청킹 전략별 인덱싱을 시작합니다.")
    for strategy in STRATEGIES:
        count = index_strategy(collection, strategy)
        print(f"{strategy['name']}: {count}개 chunk 저장")

    rows = []

    print("\n청킹 전략별 검색 결과를 비교합니다.")
    for question in EVAL_QUESTIONS:
        print(f"\n질문: {question}")

        for strategy in STRATEGIES:
            strategy_name = strategy["name"]
            results = search_by_strategy(collection, question, strategy_name)
            summary = get_first_result_summary(results)

            row = {
                "question": question,
                "strategy": strategy_name,
                **summary,
            }
            rows.append(row)

            print(
                f"- {strategy_name}: "
                f"chunk_id={summary['chunk_id']}, "
                f"distance={summary['distance']}"
            )

    write_comparison_report(rows)
    print(f"\n비교 결과 저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
