from chroma_client import get_chroma_collection

DEFAULT_QUESTION = "GitHub 제출 기준은 무엇인가요?"
TOP_K = 5

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
    """간단한 keyword search를 위해 문자열을 정규화합니다."""
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
    """문서 본문에 키워드가 포함된 횟수를 기준으로 점수를 계산합니다."""
    normalized_document = normalize_text(document)
    score = 0

    for keyword in keywords:
        normalized_keyword = normalize_text(keyword)
        score += normalized_document.count(normalized_keyword)

    return score


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


def load_all_chunks() -> list[dict]:
    """Chroma collection에 저장된 모든 chunk를 가져옵니다."""
    collection = get_chroma_collection()

    results = collection.get(
        include=["documents", "metadatas"],
    )

    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    chunk_items = []

    for chunk_id, document, metadata in zip(ids, documents, metadatas):
        chunk_items.append(
            {
                "id": chunk_id,
                "document": document,
                "metadata": metadata or {},
            }
        )

    return chunk_items


def search_by_keyword(question: str, top_k: int = TOP_K) -> list[dict]:
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
                "id": item["id"],
                "document": item["document"],
                "metadata": item["metadata"],
                "keyword_score": score,
            }
        )

    scored_items.sort(
        key=lambda item: (
            item["keyword_score"],
            item["metadata"].get("source", ""),
            item["id"],
        ),
        reverse=True,
    )

    return scored_items[:top_k]


def print_search_results(question: str, results: list[dict]) -> None:
    """keyword search 결과를 출력합니다."""
    keywords = extract_keywords(question)

    print("=" * 70)
    print("[검색 방식] keyword search")
    print(f"[질문] {question}")
    print(f"[추출 키워드] {keywords}")
    print(f"[top_k] {TOP_K}")
    print("=" * 70)

    if not results:
        print("검색 결과가 없습니다.")
        print("질문에 포함된 키워드가 chunk 본문에 직접 등장하지 않을 수 있습니다.")
        return

    for rank, item in enumerate(results, start=1):
        print(f"\n[검색 결과 {rank}]")
        print(f"chunk_id: {item['id']}")
        print(f"keyword_score: {item['keyword_score']}")
        print(format_metadata(item["metadata"]))
        print()
        print(item["document"])
        print("-" * 70)


def main() -> None:
    question = input(f"질문을 입력하세요 [{DEFAULT_QUESTION}]: ").strip()

    if not question:
        question = DEFAULT_QUESTION

    print("\nkeyword search를 시작합니다.")
    print("Chapter 7에서 chunk 인덱싱이 먼저 완료되어 있어야 합니다.")
    print("keyword search는 의미가 아니라 실제 단어 포함 여부를 기준으로 검색합니다.")
    print()

    results = search_by_keyword(question, top_k=TOP_K)
    print_search_results(question, results)


if __name__ == "__main__":
    main()
