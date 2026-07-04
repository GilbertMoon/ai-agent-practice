from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from chroma_client import get_chroma_collection
from chunk_utils import split_paragraphs_to_chunks
from document_prompt import read_text_file, split_paragraphs
from embedding_client import embed_text

DATA_FILE = PROJECT_ROOT / "data" / "course_policy_long.txt"
SOURCE_NAME = DATA_FILE.name
OUTPUT_FILE = PROJECT_ROOT / "outputs" / "chapter07_chunking_comparison.md"
TOP_K = 3

STRATEGIES = [
    {
        "name": "paragraph",
        "description": "문단 기반에 가깝게 큰 chunk size 사용",
        "chunk_size": 2000,
        "chunk_overlap": 0,
    },
    {
        "name": "size300_overlap0",
        "description": "300자 단위, overlap 없음",
        "chunk_size": 300,
        "chunk_overlap": 0,
    },
    {
        "name": "size300_overlap50",
        "description": "300자 단위, 50자 overlap",
        "chunk_size": 300,
        "chunk_overlap": 50,
    },
    {
        "name": "size500_overlap100",
        "description": "500자 단위, 100자 overlap",
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
        f"strategy: {metadata['strategy']} | "
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

    chunk_items = split_paragraphs_to_chunks(
        paragraphs=paragraphs,
        source=SOURCE_NAME,
        chunk_size=strategy["chunk_size"],
        chunk_overlap=strategy["chunk_overlap"],
    )

    for item in chunk_items:
        item["id"] = f"{strategy['name']}_{item['id']}"
        item["metadata"]["strategy"] = strategy["name"]
        item["metadata"]["strategy_description"] = strategy["description"]

    return chunk_items


def index_strategy(collection, strategy: dict) -> int:
    """특정 청킹 전략으로 생성한 chunk를 Chroma에 저장합니다."""
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
    """특정 전략으로 저장된 chunk만 대상으로 검색합니다."""
    question_embedding = embed_text(prepare_question_for_embedding(question))

    return collection.query(
        query_embeddings=[question_embedding],
        n_results=TOP_K,
        where={"strategy": strategy_name},
        include=["documents", "metadatas", "distances"],
    )


def get_top_results(results: dict) -> list[dict]:
    """Chroma 검색 결과를 보기 쉬운 dict 목록으로 변환합니다."""
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    rows = []

    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances),
        start=1,
    ):
        rows.append(
            {
                "rank": rank,
                "chunk_id": chunk_id,
                "source": metadata.get("source", "-"),
                "section": metadata.get("section", "-"),
                "paragraph_id": metadata.get("paragraph_id", "-"),
                "chunk_index": metadata.get("chunk_index", "-"),
                "distance": round(float(distance), 4),
                "text": document.replace("\n", " ")[:160],
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
            "- distance 값은 낮을수록 질문과 가까운 벡터로 볼 수 있습니다.",
            "- 하지만 distance만으로 검색 품질을 판단하지 않습니다.",
            "- 검색된 chunk가 실제로 질문에 답할 수 있는지 사람이 함께 확인해야 합니다.",
            "- chunk_size가 너무 크면 여러 주제가 섞일 수 있습니다.",
            "- chunk_size가 너무 작으면 답변에 필요한 맥락이 부족할 수 있습니다.",
            "- overlap은 chunk 경계에서 문장이 잘리는 문제를 줄이는 데 도움이 됩니다.",
        ]
    )

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    collection = get_chroma_collection()

    print("청킹 전략별 인덱싱을 시작합니다.")

    for strategy in STRATEGIES:
        count = index_strategy(collection, strategy)
        print(f"{strategy['name']}: {count}개 chunk 저장")

    comparison_rows = []

    print("\n청킹 전략별 검색 결과를 비교합니다.")

    for question in EVAL_QUESTIONS:
        print(f"\n질문: {question}")

        for strategy in STRATEGIES:
            strategy_name = strategy["name"]
            results = search_by_strategy(collection, question, strategy_name)
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

    write_comparison_report(comparison_rows)

    print(f"\n비교 결과 저장 완료: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
