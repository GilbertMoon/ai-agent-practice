from chroma_client import get_chroma_collection
from embedding_client import embed_text

DEFAULT_QUESTION = "오류 질문을 할 때 무엇을 함께 공유해야 하나요?"
TARGET_SOURCE = "course_policy_long.txt"
VECTOR_TOP_K = 10
FINAL_TOP_K = 3

KEYWORD_WEIGHT = 0.2
SECTION_MATCH_WEIGHT = 0.3
DISTANCE_PENALTY_WEIGHT = 0.1

SECTION_HINTS = {
    "과제": "5. 과제 제출 정책",
    "제출": "5. 과제 제출 정책",
    "github": "6. GitHub 제출 기준",
    "깃허브": "6. GitHub 제출 기준",
    "오류": "7. 오류 질문 방법",
    "에러": "7. 오류 질문 방법",
    "질문": "7. 오류 질문 방법",
    "미니": "12. 미니 프로젝트 결과물",
    "프로젝트": "12. 미니 프로젝트 결과물",
}

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
    "무엇",
    "어떤",
    "어디",
    "어떻게",
    "하나요",
    "인가요",
    "알려줘",
    "찾아줘",
}


def normalize_text(text: str) -> str:
    return text.lower().replace("\n", " ")


def extract_keywords(question: str) -> list[str]:
    cleaned = question
    for char in "?.,:;()[]{}\"'":
        cleaned = cleaned.replace(char, " ")

    keywords = []
    for token in cleaned.split():
        token = token.strip()
        if token and token not in STOPWORDS and len(token) > 1:
            keywords.append(token)

    return keywords


def keyword_score(keywords: list[str], document: str) -> int:
    normalized_document = normalize_text(document)
    return sum(
        normalized_document.count(normalize_text(keyword))
        for keyword in keywords
    )


def distance_to_score(distance: float) -> float:
    return 1 / (1 + float(distance))


def infer_target_section(question: str) -> str | None:
    normalized_question = normalize_text(question)

    for hint, section in SECTION_HINTS.items():
        if hint in normalized_question:
            return section

    return None


def section_match_score(question: str, metadata: dict) -> float:
    target_section = infer_target_section(question)
    if not target_section:
        return 0.0

    section = metadata.get("section", "")

    if section == target_section:
        return 1.0

    if target_section in section or section in target_section:
        return 0.5

    return 0.0


def prepare_question_for_embedding(question: str) -> str:
    return f"question: {question}"


def get_vector_candidates(question: str, top_k: int = VECTOR_TOP_K) -> list[dict]:
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

    return [
        {
            "id": chunk_id,
            "document": document,
            "metadata": metadata or {},
            "distance": float(distance),
        }
        for chunk_id, document, metadata, distance in zip(
            ids, documents, metadatas, distances
        )
    ]


def rerank_candidates(question: str, candidates: list[dict]) -> list[dict]:
    keywords = extract_keywords(question)
    rows = []

    for item in candidates:
        vector_score = distance_to_score(item["distance"])
        k_score = keyword_score(keywords, item["document"])
        s_score = section_match_score(question, item["metadata"])
        distance_penalty = item["distance"] * DISTANCE_PENALTY_WEIGHT

        rerank_score = (
            vector_score
            + KEYWORD_WEIGHT * k_score
            + SECTION_MATCH_WEIGHT * s_score
            - distance_penalty
        )

        rows.append(
            {
                **item,
                "vector_score": vector_score,
                "keyword_score": k_score,
                "section_match_score": s_score,
                "distance_penalty": distance_penalty,
                "rerank_score": rerank_score,
            }
        )

    rows.sort(
        key=lambda item: (
            -item["rerank_score"],
            -item["section_match_score"],
            -item["keyword_score"],
            item["distance"],
        )
    )
    return rows


def print_candidates(title: str, rows: list[dict], top_k: int) -> None:
    print("=" * 80)
    print(title)

    if not rows:
        print("검색 결과가 없습니다.")
        return

    for rank, row in enumerate(rows[:top_k], start=1):
        metadata = row["metadata"]
        print(f"\n[{rank}] {row['id']}")
        print(f"section: {metadata.get('section', '-')}")
        print(f"distance: {row['distance']:.4f}")
        print(f"keyword_score: {row.get('keyword_score', '-')}")
        print(f"section_match_score: {row.get('section_match_score', '-')}")
        print(f"rerank_score: {row.get('rerank_score', '-')}")
        print(row["document"].replace("\n", " ")[:300])


def main() -> None:
    question = input(f"질문을 입력하세요 [{DEFAULT_QUESTION}]: ").strip()
    if not question:
        question = DEFAULT_QUESTION

    print(f"질문: {question}")
    print(f"추출 키워드: {extract_keywords(question)}")
    print(f"추정 section: {infer_target_section(question)}")

    vector_candidates = get_vector_candidates(question)
    reranked_rows = rerank_candidates(question, vector_candidates)

    print_candidates("1차 vector search 결과", vector_candidates, FINAL_TOP_K)
    print_candidates("reranking 이후 결과", reranked_rows, FINAL_TOP_K)


if __name__ == "__main__":
    main()
