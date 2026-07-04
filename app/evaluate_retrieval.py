from pathlib import Path

from chroma_client import get_chroma_collection
from embedding_client import embed_text

OUTPUT_FILE = "outputs/chapter08_search_strategy_comparison.md"
TOP_K = 3

EVAL_CASES = [
    {
        "question": "민감 정보는 어디에 저장해야 하나요?",
        "expected_section": "4. API Key 보안 정책",
        "expected_keywords": [".env", "API Key", "GitHub"],
    },
    {
        "question": "GitHub 제출 기준은 무엇인가요?",
        "expected_section": "6. GitHub 제출 기준",
        "expected_keywords": ["GitHub", "커밋", "푸시"],
    },
    {
        "question": "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
        "expected_section": "7. 오류 질문 방법",
        "expected_keywords": ["오류", "명령어", "에러 메시지"],
    },
    {
        "question": "미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?",
        "expected_section": "12. 미니 프로젝트 결과물",
        "expected_keywords": ["미니 프로젝트", "검색 결과 비교 로그", "chunk"],
    },
]


def prepare_question_for_embedding(question: str) -> str:
    """질문 임베딩에 사용할 입력 문장을 만듭니다."""
    return f"question: {question}"


def normalize_text(text: str) -> str:
    """간단한 평가를 위해 문자열을 소문자 기준으로 정규화합니다."""
    return text.lower().replace("\n", " ")


def search_vector(question: str, top_k: int = TOP_K) -> list[dict]:
    """Chroma vector search로 top_k 검색 결과를 가져옵니다."""
    collection = get_chroma_collection()
    question_embedding = embed_text(prepare_question_for_embedding(question))

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

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
                "document": document,
                "metadata": metadata or {},
                "distance": round(float(distance), 4),
            }
        )

    return rows


def count_keyword_matches(document: str, expected_keywords: list[str]) -> int:
    """검색 결과 본문에 기대 키워드가 몇 개 포함되어 있는지 계산합니다."""
    normalized_document = normalize_text(document)

    count = 0

    for keyword in expected_keywords:
        if normalize_text(keyword) in normalized_document:
            count += 1

    return count


def is_section_match(result_section: str, expected_section: str) -> bool:
    """검색 결과 section이 기대 section과 일치하는지 확인합니다."""
    if not result_section or not expected_section:
        return False

    return result_section == expected_section


def score_relevance(result: dict, eval_case: dict) -> int:
    """
    검색 결과 관련성을 0~2점으로 평가합니다.

    2점: 기대 section이 일치하거나 기대 키워드가 2개 이상 포함됨
    1점: 기대 키워드가 1개 포함됨
    0점: 기대 section과 키워드 모두 관련성이 낮음
    """
    metadata = result["metadata"]
    document = result["document"]

    section = metadata.get("section", "")
    expected_section = eval_case["expected_section"]
    expected_keywords = eval_case["expected_keywords"]

    keyword_matches = count_keyword_matches(document, expected_keywords)

    if is_section_match(section, expected_section):
        return 2

    if keyword_matches >= 2:
        return 2

    if keyword_matches == 1:
        return 1

    return 0


def score_sufficiency(result: dict, relevance_score: int) -> int:
    """
    근거 충분성을 0~2점으로 평가합니다.

    2점: 관련성이 높고 본문 길이가 충분함
    1점: 일부 관련은 있으나 근거가 짧거나 제한적임
    0점: 관련성이 낮아 근거로 사용하기 어려움
    """
    document_length = len(result["document"].strip())

    if relevance_score == 2 and document_length >= 80:
        return 2

    if relevance_score >= 1:
        return 1

    return 0


def score_evidence(result: dict) -> int:
    """
    근거 표시 가능성을 0~2점으로 평가합니다.

    source, section, chunk_id가 모두 있으면 2점,
    일부만 있으면 1점,
    거의 없으면 0점으로 평가합니다.
    """
    metadata = result["metadata"]

    has_source = bool(metadata.get("source"))
    has_section = bool(metadata.get("section"))
    has_chunk_id = bool(result.get("chunk_id"))

    count = sum([has_source, has_section, has_chunk_id])

    if count == 3:
        return 2

    if count >= 1:
        return 1

    return 0


def evaluate_question(eval_case: dict) -> dict:
    """하나의 질문에 대해 검색 결과를 평가합니다."""
    question = eval_case["question"]
    results = search_vector(question, top_k=TOP_K)

    if not results:
        return {
            "question": question,
            "expected_section": eval_case["expected_section"],
            "top1_relevance": 0,
            "top3_contains_answer": 0,
            "top1_sufficiency": 0,
            "evidence_score": 0,
            "top1_chunk_id": "-",
            "top1_section": "-",
            "top1_distance": "-",
            "comment": "검색 결과 없음",
            "results": [],
        }

    evaluated_results = []

    for result in results:
        relevance = score_relevance(result, eval_case)
        sufficiency = score_sufficiency(result, relevance)
        evidence = score_evidence(result)

        evaluated_results.append(
            {
                **result,
                "relevance": relevance,
                "sufficiency": sufficiency,
                "evidence": evidence,
            }
        )

    top1 = evaluated_results[0]
    top3_contains_answer = 1 if any(row["relevance"] >= 2 for row in evaluated_results) else 0

    if top1["relevance"] >= 2:
        comment = "top 1 결과가 질문에 직접 답할 가능성이 높음"
    elif top3_contains_answer:
        comment = "정답 근거가 top 3 안에는 있으나 top 1은 아님"
    else:
        comment = "top 3 안에 충분한 정답 근거가 부족함"

    return {
        "question": question,
        "expected_section": eval_case["expected_section"],
        "top1_relevance": top1["relevance"],
        "top3_contains_answer": top3_contains_answer,
        "top1_sufficiency": top1["sufficiency"],
        "evidence_score": top1["evidence"],
        "top1_chunk_id": top1["chunk_id"],
        "top1_section": top1["metadata"].get("section", "-"),
        "top1_distance": top1["distance"],
        "comment": comment,
        "results": evaluated_results,
    }


def write_report(evaluation_rows: list[dict]) -> None:
    """검색 품질 평가 결과를 Markdown 파일로 저장합니다."""
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Chapter 8 검색 품질 평가표",
        "",
        "이 파일은 `app/evaluate_retrieval.py` 실행 결과입니다.",
        "",
        f"검색 결과 수: top {TOP_K}",
        "",
        "## 평가 기준",
        "",
        "| 항목 | 의미 | 점수 |",
        "| --- | --- | --- |",
        "| top 1 관련성 | 첫 번째 검색 결과가 질문에 직접 답하는가? | 0~2 |",
        "| top 3 포함 여부 | 정답 근거가 top 3 안에 들어오는가? | 0 또는 1 |",
        "| 근거 충분성 | top 1 chunk만으로 답변 근거가 충분한가? | 0~2 |",
        "| 근거 표시 가능성 | source, section, chunk_id를 제시할 수 있는가? | 0~2 |",
        "",
        "## 질문별 평가 요약",
        "",
        "| 질문 | 기대 section | top1 관련성 | top3 포함 | 근거 충분성 | 근거 표시 | top1 chunk_id | top1 section | distance | 코멘트 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in evaluation_rows:
        lines.append(
            "| {question} | {expected_section} | {top1_relevance} | {top3_contains_answer} | {top1_sufficiency} | {evidence_score} | {top1_chunk_id} | {top1_section} | {top1_distance} | {comment} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## 상세 검색 결과",
            "",
        ]
    )

    for row in evaluation_rows:
        lines.append(f"### 질문: {row['question']}")
        lines.append("")
        lines.append(f"- 기대 section: `{row['expected_section']}`")
        lines.append(f"- 코멘트: {row['comment']}")
        lines.append("")
        lines.append("| rank | chunk_id | section | distance | 관련성 | 충분성 | 근거성 | text 요약 |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")

        for result in row["results"]:
            text_summary = result["document"].replace("\n", " ")[:120]
            lines.append(
                "| {rank} | {chunk_id} | {section} | {distance} | {relevance} | {sufficiency} | {evidence} | {text} |".format(
                    rank=result["rank"],
                    chunk_id=result["chunk_id"],
                    section=result["metadata"].get("section", "-"),
                    distance=result["distance"],
                    relevance=result["relevance"],
                    sufficiency=result["sufficiency"],
                    evidence=result["evidence"],
                    text=text_summary,
                )
            )

        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print("검색 품질 평가를 시작합니다.")
    print("Chapter 7에서 chunk 인덱싱이 먼저 완료되어 있어야 합니다.")
    print()

    evaluation_rows = []

    for eval_case in EVAL_CASES:
        row = evaluate_question(eval_case)
        evaluation_rows.append(row)

        print(f"질문: {row['question']}")
        print(f"- 기대 section: {row['expected_section']}")
        print(f"- top1 관련성: {row['top1_relevance']}")
        print(f"- top3 포함: {row['top3_contains_answer']}")
        print(f"- 근거 충분성: {row['top1_sufficiency']}")
        print(f"- 근거 표시: {row['evidence_score']}")
        print(f"- 코멘트: {row['comment']}")
        print("-" * 70)

    write_report(evaluation_rows)

    print(f"\n검색 품질 평가 결과 저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
