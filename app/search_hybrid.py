from chroma_client import get_chroma_collection
from embedding_client import embed_text

DEFAULT_QUESTION = "오류 질문을 할 때 무엇을 함께 공유해야 하나요?"
VECTOR_TOP_K = 10
FINAL_TOP_K = 3
KEYWORD_WEIGHT = 0.2

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
    """간단한 검색 점수 계산을 위해 문자열을 정규화합니다."""
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


def distance_to_vector_score(distance: float) -> float:
    """Chroma distance 값을 vector score로 변환합니다."""
    return 1 / (1 + float(distance))


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


def vector_search_candidates(question: str, top_k: int = VECTOR_TOP_K) -> list[dict]:
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


def hybrid_search(question: str, final_top_k: int = FINAL_TOP_K) -> list[dict]:
    """vector score와 keyword score를 결합해 hybrid search 결과를 만듭니다."""
    keywords = extract_keywords(question)
    candidates = vector_search_candidates(question, top_k=VECTOR_TOP_K)

    scored_items = []

    for item in candidates:
        vector_score = distance_to_vector_score(item["distance"])
        k_score = keyword_score(keywords, item["document"])
        hybrid_score = vector_score + KEYWORD_WEIGHT * k_score

        scored_items.append(
            {
                "id": item["id"],
                "document": item["document"],
                "metadata": item["metadata"],
                "distance": item["distance"],
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

    return scored_items[:final_top_k]


def print_search_results(question: str, results: list[dict]) -> None:
    """hybrid search 결과를 출력합니다."""
    keywords = extract_keywords(question)

    print("=" * 70)
    print("[검색 방식] hybrid search")
    print(f"[질문] {question}")
    print(f"[추출 키워드] {keywords}")
    print(f"[vector 후보 수] {VECTOR_TOP_K}")
    print(f"[최종 출력 수] {FINAL_TOP_K}")
    print(f"[keyword weight] {KEYWORD_WEIGHT}")
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
        print(f"hybrid_score: {item['hybrid_score']}")
        print(format_metadata(item["metadata"]))
        print()
        print(item["document"])
        print("-" * 70)


def main() -> None:
    question = input(f"질문을 입력하세요 [{DEFAULT_QUESTION}]: ").strip()

    if not question:
        question = DEFAULT_QUESTION

    print("\nhybrid search를 시작합니다.")
    print("Chapter 7에서 chunk 인덱싱이 먼저 완료되어 있어야 합니다.")
    print("vector score와 keyword score를 함께 사용해 검색 결과를 정렬합니다.")
    print()

    results = hybrid_search(question, final_top_k=FINAL_TOP_K)
    print_search_results(question, results)


if __name__ == "__main__":
    main()
