from pathlib import Path

from chroma_client import get_chroma_collection
from embedding_client import embed_text

OUTPUT_FILE = "outputs/chapter08_search_evaluation.md"
TARGET_SOURCE = "course_policy_long.txt"
TOP_K = 3

EVAL_CASES = [
    {
        "question": "민감 정보는 어디에 저장해야 하나요?",
        "expected_section": "4. 보안 정책",
        "expected_keywords": ["인증", "정보", "로컬", "공개"],
    },
    {
        "question": "GitHub 제출 기준은 무엇인가요?",
        "expected_section": "6. GitHub 제출 기준",
        "expected_keywords": ["GitHub", "커밋", "푸시"],
    },
    {
        "question": "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
        "expected_section": "7. 오류 질문 방법",
        "expected_keywords": ["오류", "명령어", "메시지"],
    },
    {
        "question": "미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?",
        "expected_section": "12. 미니 프로젝트 결과물",
        "expected_keywords": ["미니", "프로젝트", "검색", "로그"],
    },
]


def prepare_question_for_embedding(question: str) -> str:
    return f"question: {question}"


def normalize_text(text: str) -> str:
    return text.lower().replace("\n", " ")


def search_vector(question: str, top_k: int = TOP_K) -> list[dict]:
    collection = get_chroma_collection()
    question_embedding = embed_text(prepare_question_for_embedding(question))

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        where={"source": TARGET_SOURCE},
        include=["documents", "metadatas", "distances"],
    )

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    rows = []
    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances), start=1
    ):
        rows.append(
            {
                "rank": rank,
                "chunk_id": chunk_id,
                "document": document,
                "metadata": metadata or {},
                "distance": round(float(distance), 4),
            }
        )

    return rows


def count_keyword_matches(document: str, keywords: list[str]) -> int:
    text = normalize_text(document)
    return sum(1 for keyword in keywords if normalize_text(keyword) in text)


def score_relevance(result: dict, eval_case: dict) -> int:
    section = result["metadata"].get("section", "")
    expected_section = eval_case["expected_section"]
    keyword_matches = count_keyword_matches(
        result["document"],
        eval_case["expected_keywords"],
    )

    if section == expected_section and keyword_matches >= 1:
        return 2

    if section == expected_section or keyword_matches >= 2:
        return 2

    if keyword_matches == 1:
        return 1

    return 0


def score_sufficiency(result: dict, relevance_score: int) -> int:
    document_length = len(result["document"].strip())

    if relevance_score == 2 and document_length >= 80:
        return 2

    if relevance_score >= 1:
        return 1

    return 0


def evaluate_question(eval_case: dict) -> dict:
    results = search_vector(eval_case["question"])

    if not results:
        return {
            "question": eval_case["question"],
            "expected_section": eval_case["expected_section"],
            "top1_relevance": 0,
            "top3_contains_answer": 0,
            "top1_sufficiency": 0,
            "top1_chunk_id": "-",
            "top1_section": "-",
            "top1_distance": "-",
            "comment": "검색 결과 없음",
        }

    for row in results:
        row["relevance"] = score_relevance(row, eval_case)
        row["sufficiency"] = score_sufficiency(row, row["relevance"])

    top1 = results[0]
    top3_contains_answer = 1 if any(row["relevance"] >= 2 for row in results) else 0

    if top1["relevance"] >= 2:
        comment = "top1 적합"
    elif top3_contains_answer:
        comment = "top3 안에 근거 있음"
    else:
        comment = "근거 부족"

    return {
        "question": eval_case["question"],
        "expected_section": eval_case["expected_section"],
        "top1_relevance": top1["relevance"],
        "top3_contains_answer": top3_contains_answer,
        "top1_sufficiency": top1["sufficiency"],
        "top1_chunk_id": top1["chunk_id"],
        "top1_section": top1["metadata"].get("section", "-"),
        "top1_distance": top1["distance"],
        "comment": comment,
    }


def write_report(rows: list[dict]) -> None:
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Chapter 8 검색 품질 평가표",
        "",
        f"검색 대상 source: `{TARGET_SOURCE}`",
        f"검색 결과 수: top {TOP_K}",
        "",
        "## 평가 기준",
        "",
        "- top1 관련성: 2점이면 top1 결과가 질문에 직접 관련 있음",
        "- top3 포함: 1이면 top3 안에 답변 근거가 있음",
        "- 근거 충분성: 2점이면 top1 chunk만으로 답변 근거가 충분함",
        "",
        "| 질문 | 기대 section | top1 관련성 | top3 포함 | 근거 충분성 | top1 chunk_id | top1 section | distance | 코멘트 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in rows:
        lines.append(
            "| {question} | {expected_section} | {top1_relevance} | {top3_contains_answer} | {top1_sufficiency} | {top1_chunk_id} | {top1_section} | {top1_distance} | {comment} |".format(
                **row
            )
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = [evaluate_question(eval_case) for eval_case in EVAL_CASES]

    for row in rows:
        print(row)

    write_report(rows)
    print(f"저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
