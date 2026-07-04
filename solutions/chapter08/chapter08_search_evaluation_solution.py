from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from chroma_client import get_chroma_collection
from embedding_client import embed_text

OUTPUT_FILE = PROJECT_ROOT / "outputs" / "chapter08_search_strategy_comparison.md"

DEFAULT_TOP_K = 3
VECTOR_CANDIDATE_K = 10
KEYWORD_WEIGHT = 0.2
SECTION_MATCH_WEIGHT = 0.3
DISTANCE_PENALTY_WEIGHT = 0.1

STOPWORDS = {
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "에",
    "에서",
    "으로",
    "로",
    "와",
    "과",
    "의",
    "도",
    "만",
    "좀",
    "수",
    "것",
    "무엇",
    "어떤",
    "어디",
    "어떻게",
    "하나요",
    "인가요",
    "알려줘",
    "찾아줘",
}

SECTION_HINTS = {
    "보안": "4. API Key 보안 정책",
    "api": "4. API Key 보안 정책",
    "key": "4. API Key 보안 정책",
    "과제": "5. 과제 제출 정책",
    "제출": "5. 과제 제출 정책",
    "github": "6. GitHub 제출 기준",
    "오류": "7. 오류 질문 방법",
    "에러": "7. 오류 질문 방법",
    "질문": "7. 오류 질문 방법",
    "미니": "12. 미니 프로젝트 결과물",
    "프로젝트": "12. 미니 프로젝트 결과물",
}

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


def normalize_text(text: str) -> str:
    """검색과 평가에 사용할 문자열을 간단히 정규화합니다."""
    return text.lower().replace("\n", " ")


def extract_keywords(question: str) -> list[str]:
    """질문에서 간단한 키워드 목록을 추출합니다."""
    cleaned = (
        question.replace("?", " ")
        .replace(".", " ")
        .replace(",", " ")
        .replace(":", " ")
        .replace(";", " ")
        .replace("(", " ")
        .replace(")", " ")
    )

    keywords = []

    for token in cleaned.split():
        token = token.strip()

        if not token:
            continue

        if token in STOPWORDS:
            continue

        if len(token) <= 1:
            continue

        keywords.append(token)

    return keywords


def keyword_score(keywords: list[str], document: str) -> int:
    """chunk 본문에 키워드가 포함된 횟수를 기준으로 점수를 계산합니다."""
    normalized_document = normalize_text(document)
    score = 0

    for keyword in keywords:
        normalized_keyword = normalize_text(keyword)
        score += normalized_document.count(normalized_keyword)

    return score


def distance_to_score(distance: float) -> float:
    """Chroma distance 값을 점수로 변환합니다."""
    return 1 / (1 + float(distance))


def prepare_question_for_embedding(question: str) -> str:
    """질문 임베딩에 사용할 입력 문장을 만듭니다."""
    return f"question: {question}"


def infer_target_section(question: str) -> str | None:
    """질문에 포함된 단어를 기준으로 예상 section을 추정합니다."""
    normalized_question = normalize_text(question)

    for hint, section in SECTION_HINTS.items():
        if hint in normalized_question:
            return section

    return None


def section_match_score(question: str, metadata: dict) -> float:
    """질문에서 추정한 section과 검색 결과 section이 일치하면 가산점을 줍니다."""
    target_section = infer_target_section(question)

    if not target_section:
        return 0.0

    result_section = metadata.get("section", "")

    if result_section == target_section:
        return 1.0

    if target_section in result_section or result_section in target_section:
        return 0.5

    return 0.0


def query_vector(
    question: str,
    top_k: int = DEFAULT_TOP_K,
    where: dict | None = None,
    where_document: dict | None = None,
) -> list[dict]:
    """Chroma vector search를 실행하고 결과를 공통 형식으로 변환합니다."""
    collection = get_chroma_collection()
    question_embedding = embed_text(prepare_question_for_embedding(question))

    query_args = {
        "query_embeddings": [question_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }

    if where:
        query_args["where"] = where

    if where_document:
        query_args["where_document"] = where_document

    results = collection.query(**query_args)

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


def load_all_chunks() -> list[dict]:
    """Chroma collection에 저장된 모든 chunk를 가져옵니다."""
    collection = get_chroma_collection()
    results = collection.get(include=["documents", "metadatas"])

    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    chunk_items = []

    for chunk_id, document, metadata in zip(ids, documents, metadatas):
        chunk_items.append(
            {
                "rank": 0,
                "chunk_id": chunk_id,
                "document": document,
                "metadata": metadata or {},
                "distance": "-",
            }
        )

    return chunk_items


def search_by_keyword(question: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """질문 키워드를 기준으로 chunk를 검색합니다."""
    keywords = extract_keywords(question)
    chunk_items = load_all_chunks()
    scored_items = []

    for item in chunk_items:
        score = keyword_score(keywords, item["document"])

        if score <= 0:
            continue

        scored_items.append(
            {
                **item,
                "keyword_score": score,
            }
        )

    scored_items.sort(
        key=lambda item: (
            item["keyword_score"],
            item["metadata"].get("source", ""),
            item["chunk_id"],
        ),
        reverse=True,
    )

    selected = scored_items[:top_k]

    for rank, item in enumerate(selected, start=1):
        item["rank"] = rank

    return selected


def search_hybrid(question: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """vector score와 keyword score를 결합해 검색 결과를 정렬합니다."""
    keywords = extract_keywords(question)
    candidates = query_vector(question, top_k=VECTOR_CANDIDATE_K)
    scored_items = []

    for item in candidates:
        vector_score = distance_to_score(float(item["distance"]))
        k_score = keyword_score(keywords, item["document"])
        hybrid_score = vector_score + KEYWORD_WEIGHT * k_score

        scored_items.append(
            {
                **item,
                "vector_score": round(vector_score, 4),
                "keyword_score": k_score,
                "hybrid_score": round(hybrid_score, 4),
            }
        )

    scored_items.sort(
        key=lambda item: (
            item["hybrid_score"],
            item["keyword_score"],
            item["vector_score"],
        ),
        reverse=True,
    )

    selected = scored_items[:top_k]

    for rank, item in enumerate(selected, start=1):
        item["rank"] = rank

    return selected


def search_with_reranking(question: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """1차 vector search 후보를 가져온 뒤 규칙 기반 점수로 다시 정렬합니다."""
    keywords = extract_keywords(question)
    candidates = query_vector(question, top_k=VECTOR_CANDIDATE_K)
    reranked_items = []

    for item in candidates:
        vector_score = distance_to_score(float(item["distance"]))
        k_score = keyword_score(keywords, item["document"])
        s_score = section_match_score(question, item["metadata"])
        distance_penalty = float(item["distance"]) * DISTANCE_PENALTY_WEIGHT

        rerank_score = (
            vector_score
            + KEYWORD_WEIGHT * k_score
            + SECTION_MATCH_WEIGHT * s_score
            - distance_penalty
        )

        reranked_items.append(
            {
                **item,
                "vector_score": round(vector_score, 4),
                "keyword_score": k_score,
                "section_match_score": s_score,
                "rerank_score": round(rerank_score, 4),
            }
        )

    reranked_items.sort(
        key=lambda item: (
            item["rerank_score"],
            item["section_match_score"],
            item["keyword_score"],
            item["vector_score"],
        ),
        reverse=True,
    )

    selected = reranked_items[:top_k]

    for rank, item in enumerate(selected, start=1):
        item["rank"] = rank

    return selected


def run_strategy(strategy_name: str, eval_case: dict) -> list[dict]:
    """전략 이름에 따라 검색 함수를 실행합니다."""
    question = eval_case["question"]

    if strategy_name == "vector_top1":
        return query_vector(question, top_k=1)

    if strategy_name == "vector_top3":
        return query_vector(question, top_k=3)

    if strategy_name == "vector_top5":
        return query_vector(question, top_k=5)

    if strategy_name == "metadata_filter":
        return query_vector(
            question,
            top_k=DEFAULT_TOP_K,
            where={"section": eval_case["expected_section"]},
        )

    if strategy_name == "document_filter":
        keyword = eval_case["expected_keywords"][0]
        return query_vector(
            question,
            top_k=DEFAULT_TOP_K,
            where_document={"$contains": keyword},
        )

    if strategy_name == "keyword":
        return search_by_keyword(question, top_k=DEFAULT_TOP_K)

    if strategy_name == "hybrid":
        return search_hybrid(question, top_k=DEFAULT_TOP_K)

    if strategy_name == "reranking":
        return search_with_reranking(question, top_k=DEFAULT_TOP_K)

    raise ValueError(f"지원하지 않는 검색 전략입니다: {strategy_name}")


def count_keyword_matches(document: str, expected_keywords: list[str]) -> int:
    """검색 결과 본문에 기대 키워드가 몇 개 포함되어 있는지 계산합니다."""
    normalized_document = normalize_text(document)
    count = 0

    for keyword in expected_keywords:
        if normalize_text(keyword) in normalized_document:
            count += 1

    return count


def score_relevance(result: dict, eval_case: dict) -> int:
    """검색 결과 관련성을 0~2점으로 평가합니다."""
    metadata = result["metadata"]
    document = result["document"]
    section = metadata.get("section", "")
    expected_section = eval_case["expected_section"]
    keyword_matches = count_keyword_matches(document, eval_case["expected_keywords"])

    if section == expected_section:
        return 2

    if keyword_matches >= 2:
        return 2

    if keyword_matches == 1:
        return 1

    return 0


def score_sufficiency(result: dict, relevance_score: int) -> int:
    """근거 충분성을 0~2점으로 평가합니다."""
    document_length = len(result["document"].strip())

    if relevance_score == 2 and document_length >= 80:
        return 2

    if relevance_score >= 1:
        return 1

    return 0


def score_evidence(result: dict) -> int:
    """근거 표시 가능성을 0~2점으로 평가합니다."""
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


def evaluate_strategy_result(strategy_name: str, eval_case: dict, results: list[dict]) -> dict:
    """하나의 질문과 하나의 검색 전략 결과를 평가합니다."""
    question = eval_case["question"]

    if not results:
        return {
            "question": question,
            "strategy": strategy_name,
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
    top3_contains_answer = 1 if any(row["relevance"] >= 2 for row in evaluated_results[:3]) else 0

    if top1["relevance"] >= 2:
        comment = "top 1 결과가 질문에 직접 답할 가능성이 높음"
    elif top3_contains_answer:
        comment = "정답 근거가 top 3 안에는 있으나 top 1은 아님"
    else:
        comment = "top 3 안에 충분한 정답 근거가 부족함"

    return {
        "question": question,
        "strategy": strategy_name,
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
    """검색 전략별 평가 결과를 Markdown 파일로 저장합니다."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Chapter 8 검색 전략별 RAG 품질 비교 실험",
        "",
        "이 파일은 `solutions/chapter08/chapter08_search_evaluation_solution.py` 실행 결과입니다.",
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
        "## 검색 전략별 평가 요약",
        "",
        "| 질문 | 전략 | 기대 section | top1 관련성 | top3 포함 | 근거 충분성 | 근거 표시 | top1 chunk_id | top1 section | distance | 코멘트 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in evaluation_rows:
        lines.append(
            "| {question} | {strategy} | {expected_section} | {top1_relevance} | {top3_contains_answer} | {top1_sufficiency} | {evidence_score} | {top1_chunk_id} | {top1_section} | {top1_distance} | {comment} |".format(
                **row
            )
        )

    lines.extend(["", "## 상세 검색 결과", ""])

    for row in evaluation_rows:
        lines.append(f"### 질문: {row['question']} / 전략: {row['strategy']}")
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

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    strategies = [
        "vector_top1",
        "vector_top3",
        "vector_top5",
        "metadata_filter",
        "document_filter",
        "keyword",
        "hybrid",
        "reranking",
    ]

    print("Chapter 8 검색 전략별 RAG 품질 비교 실험을 시작합니다.")
    print("Chapter 7에서 chunk 인덱싱이 먼저 완료되어 있어야 합니다.")
    print()

    evaluation_rows = []

    for eval_case in EVAL_CASES:
        print(f"질문: {eval_case['question']}")

        for strategy in strategies:
            results = run_strategy(strategy, eval_case)
            row = evaluate_strategy_result(strategy, eval_case, results)
            evaluation_rows.append(row)

            print(
                f"- {strategy}: "
                f"top1={row['top1_relevance']}, "
                f"top3={row['top3_contains_answer']}, "
                f"chunk={row['top1_chunk_id']}"
            )

        print("-" * 70)

    write_report(evaluation_rows)

    print(f"\n검색 전략별 평가 결과 저장 완료: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
