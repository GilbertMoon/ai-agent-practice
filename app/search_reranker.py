from chroma_client import get_chroma_collection
from embedding_client import embed_text

DEFAULT_QUESTION = "오류 질문을 할 때 무엇을 함께 공유해야 하나요?"
VECTOR_TOP_K = 10
FINAL_TOP_K = 3

KEYWORD_WEIGHT = 0.2
SECTION_MATCH_WEIGHT = 0.3
DISTANCE_PENALTY_WEIGHT = 0.1

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


def normalize_text(text: str) -> str:
    """검색 점수 계산을 위해 문자열을 정규화합니다."""
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


def prepare_question_for_embedding(question: str) -> str:
    """질문 임베딩에 사용할 입력 문장을 만듭니다."""
    return f"question: {question}"


def format_metadata(metadata: dict) -> str:
    """검색 결과 metadata를 보기 좋게 문자열로 변환합니다."""
    return "\n".join(
        [
            f"source: {metadata.get('source', '-')}",
            f"section: {metadata.get('section', '-')}",
            f"paragraph_id: {metadata.get('paragraph_id', '-')}",
            f"chunk_index: {metadata.get('chunk_index', '-')}",
            f"strategy: {metadata.get('strategy', '-')}",
        ]
    )


def get_vector_candidates(question: str, top_k: int = VECTOR_TOP_K) -> list[dict]:
    """Chroma vector search로 1차 후보 chunk를 가져옵니다."""
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

    candidates = []

    for chunk_id, document, metadata, distance in zip(
        ids,
        documents,
        metadatas,
        distances,
    ):
        candidates.append(
            {
                "id": chunk_id,
                "document": document,
                "metadata": metadata or {},
                "distance": float(distance),
            }
        )

    return candidates


def rerank_candidates(question: str, candidates: list[dict]) -> list[dict]:
    """1차 검색 후보를 규칙 기반 점수로 다시 정렬합니다."""
    keywords = extract_keywords(question)

    reranked_items = []

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

        reranked_items.append(
            {
                "id": item["id"],
                "document": item["document"],
                "metadata": item["metadata"],
                "distance": item["distance"],
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

    return reranked_items


def search_with_reranking(question: str, final_top_k: int = FINAL_TOP_K) -> list[dict]:
    """vector search 후보를 가져온 뒤 reranking을 적용합니다."""
    candidates = get_vector_candidates(question, top_k=VECTOR_TOP_K)
    reranked_items = rerank_candidates(question, candidates)

    return reranked_items[:final_top_k]


def print_search_results(question: str, results: list[dict]) -> None:
    """reranking 결과를 출력합니다."""
    keywords = extract_keywords(question)
    target_section = infer_target_section(question)

    print("=" * 70)
    print("[검색 방식] vector search + rule-based reranking")
    print(f"[질문] {question}")
    print(f"[추출 키워드] {keywords}")
    print(f"[추정 section] {target_section or '-'}")
    print(f"[1차 vector 후보 수] {VECTOR_TOP_K}")
    print(f"[최종 출력 수] {FINAL_TOP_K}")
    print("=" * 70)

    if not results:
        print("검색 결과가 없습니다.")
        return

    for rank, item in enumerate(results, start=1):
        print(f"\n[검색 결과 {rank}]")
        print(f"chunk_id: {item['id']}")
        print(f"distance: {item['distance']}")
        print(f"vector_score: {item['vector_score']}")
        print(f"keyword_score: {item['keyword_score']}")
        print(f"section_match_score: {item['section_match_score']}")
        print(f"rerank_score: {item['rerank_score']}")
        print(format_metadata(item["metadata"]))
        print()
        print(item["document"])
        print("-" * 70)


def main() -> None:
    question = input(f"질문을 입력하세요 [{DEFAULT_QUESTION}]: ").strip()

    if not question:
        question = DEFAULT_QUESTION

    print("\nreranking 검색을 시작합니다.")
    print("Chapter 7에서 chunk 인덱싱이 먼저 완료되어 있어야 합니다.")
    print("1차 vector search 후보를 가져온 뒤 규칙 기반 점수로 다시 정렬합니다.")
    print()

    results = search_with_reranking(question, final_top_k=FINAL_TOP_K)
    print_search_results(question, results)


if __name__ == "__main__":
    main()
