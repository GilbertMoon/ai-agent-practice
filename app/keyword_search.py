from chroma_client import get_chroma_collection

DEFAULT_QUESTION = "GitHub 제출 기준은 무엇인가요?"
TARGET_SOURCE = "course_policy_long.txt"
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


def load_indexed_chunks() -> list[dict]:
    collection = get_chroma_collection()
    results = collection.get(include=["documents", "metadatas"])

    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    rows = []
    for chunk_id, document, metadata in zip(ids, documents, metadatas):
        metadata = metadata or {}

        if metadata.get("source") != TARGET_SOURCE:
            continue

        rows.append(
            {
                "id": chunk_id,
                "document": document,
                "metadata": metadata,
            }
        )

    return rows


def search_by_keyword(question: str, top_k: int = TOP_K) -> list[dict]:
    keywords = extract_keywords(question)
    rows = []

    if not keywords:
        return rows

    for item in load_indexed_chunks():
        score = keyword_score(keywords, item["document"])
        if score > 0:
            rows.append({**item, "keyword_score": score})

    rows.sort(key=lambda item: (-item["keyword_score"], item["id"]))
    return rows[:top_k]


def print_results(question: str, rows: list[dict]) -> None:
    keywords = extract_keywords(question)

    print(f"질문: {question}")
    print(f"추출 키워드: {keywords}")

    if not rows:
        print("검색 결과가 없습니다.")
        return

    for rank, row in enumerate(rows, start=1):
        metadata = row["metadata"]
        print(f"\n[{rank}] {row['id']}")
        print(f"keyword_score: {row['keyword_score']}")
        print(f"section: {metadata.get('section', '-')}")
        print(f"source: {metadata.get('source', '-')}")
        print(row["document"].replace("\n", " ")[:300])


def main() -> None:
    question = input(f"질문을 입력하세요 [{DEFAULT_QUESTION}]: ").strip()
    if not question:
        question = DEFAULT_QUESTION

    rows = search_by_keyword(question)
    print_results(question, rows)


if __name__ == "__main__":
    main()
