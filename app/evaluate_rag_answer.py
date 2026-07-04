from pathlib import Path

from chroma_client import get_chroma_collection
from embedding_client import embed_text
from gemini_client import ask_gemini as generate_text

OUTPUT_FILE = "outputs/chapter08_rag_evaluation.md"
TOP_K = 3

EVAL_CASES = [
    {
        "question": "민감 정보는 어디에 저장해야 하나요?",
        "expected_keywords": [".env", "API Key", "GitHub"],
    },
    {
        "question": "GitHub 제출 기준은 무엇인가요?",
        "expected_keywords": ["GitHub", "커밋", "푸시"],
    },
    {
        "question": "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
        "expected_keywords": ["오류", "명령어", "에러 메시지"],
    },
    {
        "question": "미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?",
        "expected_keywords": ["미니 프로젝트", "검색 결과 비교 로그", "chunk"],
    },
]


def prepare_question_for_embedding(question: str) -> str:
    """질문 임베딩에 사용할 입력 문장을 만듭니다."""
    return f"question: {question}"


def normalize_text(text: str) -> str:
    """간단한 평가를 위해 문자열을 정규화합니다."""
    return text.lower().replace("\n", " ")


def retrieve_context(question: str, top_k: int = TOP_K) -> list[dict]:
    """Chroma에서 질문과 관련 있는 context chunk를 검색합니다."""
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

    contexts = []

    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances),
        start=1,
    ):
        contexts.append(
            {
                "rank": rank,
                "chunk_id": chunk_id,
                "document": document,
                "metadata": metadata or {},
                "distance": round(float(distance), 4),
            }
        )

    return contexts


def build_context_text(contexts: list[dict]) -> str:
    """검색된 context 목록을 LLM에 전달하기 좋은 문자열로 변환합니다."""
    lines = []

    for item in contexts:
        metadata = item["metadata"]

        lines.append(f"[context {item['rank']}]")
        lines.append(f"chunk_id: {item['chunk_id']}")
        lines.append(f"source: {metadata.get('source', '-')}")
        lines.append(f"section: {metadata.get('section', '-')}")
        lines.append(f"distance: {item['distance']}")
        lines.append("content:")
        lines.append(item["document"])
        lines.append("")

    return "\n".join(lines)


def build_rag_prompt(question: str, contexts: list[dict]) -> str:
    """검색 context를 바탕으로 RAG 답변 생성을 위한 prompt를 만듭니다."""
    context_text = build_context_text(contexts)

    return f"""
당신은 수업 안내 문서를 기반으로 답변하는 AI 조교입니다.

아래 context에 있는 내용만 근거로 사용하세요.
context에 없는 내용은 추측하지 마세요.
답변은 한국어로 간결하게 작성하세요.
가능하면 답변 마지막에 근거 chunk_id와 section을 함께 표시하세요.

[질문]
{question}

[context]
{context_text}

[답변 작성 형식]
답변:
근거:
""".strip()


def generate_rag_answer(question: str, contexts: list[dict]) -> str:
    """검색 context를 바탕으로 Gemini 답변을 생성합니다."""
    prompt = build_rag_prompt(question, contexts)
    return generate_text(prompt)


def count_keyword_matches(text: str, expected_keywords: list[str]) -> int:
    """답변 또는 context에 기대 키워드가 몇 개 포함되어 있는지 계산합니다."""
    normalized_text = normalize_text(text)

    count = 0

    for keyword in expected_keywords:
        if normalize_text(keyword) in normalized_text:
            count += 1

    return count


def score_answer_relevance(answer: str, expected_keywords: list[str]) -> int:
    """
    답변 관련성을 0~2점으로 평가합니다.

    2점: 기대 키워드가 2개 이상 포함됨
    1점: 기대 키워드가 1개 포함됨
    0점: 기대 키워드가 거의 없음
    """
    matched_count = count_keyword_matches(answer, expected_keywords)

    if matched_count >= 2:
        return 2

    if matched_count == 1:
        return 1

    return 0


def score_faithfulness(answer: str, contexts: list[dict]) -> int:
    """
    답변 충실성을 0~2점으로 평가합니다.

    단순 평가 기준:
    - 답변에 포함된 핵심 표현이 context에도 나타나면 충실성이 높다고 봅니다.
    - 실제 프로젝트에서는 사람이 함께 확인해야 합니다.
    """
    context_text = normalize_text(build_context_text(contexts))
    answer_text = normalize_text(answer)

    if not answer_text.strip():
        return 0

    matched_chunks = 0

    for item in contexts:
        section = item["metadata"].get("section", "")
        chunk_id = item["chunk_id"]

        if section and normalize_text(section) in answer_text:
            matched_chunks += 1

        if chunk_id and normalize_text(chunk_id) in answer_text:
            matched_chunks += 1

    if matched_chunks >= 1:
        return 2

    answer_tokens = [token for token in answer_text.split() if len(token) >= 3]
    context_match_count = sum(1 for token in answer_tokens if token in context_text)

    if context_match_count >= 5:
        return 2

    if context_match_count >= 2:
        return 1

    return 0


def score_evidence(answer: str, contexts: list[dict]) -> int:
    """
    근거 표시 가능성을 0~2점으로 평가합니다.

    답변에 chunk_id 또는 section이 표시되어 있으면 높은 점수를 줍니다.
    """
    normalized_answer = normalize_text(answer)

    has_chunk_id = any(
        normalize_text(item["chunk_id"]) in normalized_answer
        for item in contexts
    )

    has_section = any(
        normalize_text(item["metadata"].get("section", "")) in normalized_answer
        for item in contexts
        if item["metadata"].get("section")
    )

    if has_chunk_id and has_section:
        return 2

    if has_chunk_id or has_section:
        return 1

    return 0


def score_conciseness(answer: str) -> int:
    """
    답변 간결성을 0~2점으로 평가합니다.

    너무 짧거나 너무 길면 점수를 낮춥니다.
    """
    length = len(answer.strip())

    if 40 <= length <= 500:
        return 2

    if 10 <= length < 40 or 500 < length <= 900:
        return 1

    return 0


def evaluate_rag_answer(eval_case: dict) -> dict:
    """하나의 질문에 대해 검색, 답변 생성, 답변 평가를 수행합니다."""
    question = eval_case["question"]
    expected_keywords = eval_case["expected_keywords"]

    contexts = retrieve_context(question, top_k=TOP_K)

    if not contexts:
        return {
            "question": question,
            "answer": "검색 결과가 없어 답변을 생성하지 않았습니다.",
            "answer_relevance": 0,
            "faithfulness": 0,
            "evidence": 0,
            "conciseness": 0,
            "total_score": 0,
            "top_context": "-",
            "comment": "검색 결과 없음",
            "contexts": [],
        }

    answer = generate_rag_answer(question, contexts)

    answer_relevance = score_answer_relevance(answer, expected_keywords)
    faithfulness = score_faithfulness(answer, contexts)
    evidence = score_evidence(answer, contexts)
    conciseness = score_conciseness(answer)
    total_score = answer_relevance + faithfulness + evidence + conciseness

    if answer_relevance >= 2 and faithfulness >= 2:
        comment = "질문에 적절하고 context에 근거한 답변으로 보임"
    elif answer_relevance >= 1:
        comment = "일부 관련성은 있으나 근거성 또는 충실성 확인 필요"
    else:
        comment = "질문과 답변의 관련성이 낮아 보임"

    return {
        "question": question,
        "answer": answer,
        "answer_relevance": answer_relevance,
        "faithfulness": faithfulness,
        "evidence": evidence,
        "conciseness": conciseness,
        "total_score": total_score,
        "top_context": contexts[0]["chunk_id"],
        "comment": comment,
        "contexts": contexts,
    }


def write_report(evaluation_rows: list[dict]) -> None:
    """RAG 답변 품질 평가 결과를 Markdown 파일로 저장합니다."""
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Chapter 8 RAG 답변 품질 평가",
        "",
        "이 파일은 `app/evaluate_rag_answer.py` 실행 결과입니다.",
        "",
        f"검색 결과 수: top {TOP_K}",
        "",
        "## 평가 기준",
        "",
        "| 항목 | 의미 | 점수 |",
        "| --- | --- | --- |",
        "| 답변 관련성 | 질문에 맞게 답했는가? | 0~2 |",
        "| 충실성 | 검색된 context에 근거해 답했는가? | 0~2 |",
        "| 근거성 | 답변에 source, section, chunk_id가 포함되는가? | 0~2 |",
        "| 간결성 | 불필요하게 길지 않은가? | 0~2 |",
        "",
        "## 질문별 답변 품질 요약",
        "",
        "| 질문 | 답변 관련성 | 충실성 | 근거성 | 간결성 | 총점 | top context | 코멘트 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in evaluation_rows:
        lines.append(
            "| {question} | {answer_relevance} | {faithfulness} | {evidence} | {conciseness} | {total_score} | {top_context} | {comment} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## 상세 답변",
            "",
        ]
    )

    for row in evaluation_rows:
        lines.append(f"### 질문: {row['question']}")
        lines.append("")
        lines.append("#### 생성 답변")
        lines.append("")
        lines.append(row["answer"])
        lines.append("")
        lines.append("#### 검색 context")
        lines.append("")
        lines.append("| rank | chunk_id | section | distance | text 요약 |")
        lines.append("| --- | --- | --- | --- | --- |")

        for context in row["contexts"]:
            metadata = context["metadata"]
            text_summary = context["document"].replace("\n", " ")[:120]

            lines.append(
                "| {rank} | {chunk_id} | {section} | {distance} | {text} |".format(
                    rank=context["rank"],
                    chunk_id=context["chunk_id"],
                    section=metadata.get("section", "-"),
                    distance=context["distance"],
                    text=text_summary,
                )
            )

        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print("RAG 답변 품질 평가를 시작합니다.")
    print("Chapter 7에서 chunk 인덱싱이 먼저 완료되어 있어야 합니다.")
    print("Gemini 답변 생성을 사용하므로 .env 설정이 필요합니다.")
    print()

    evaluation_rows = []

    for eval_case in EVAL_CASES:
        row = evaluate_rag_answer(eval_case)
        evaluation_rows.append(row)

        print(f"질문: {row['question']}")
        print(f"- 답변 관련성: {row['answer_relevance']}")
        print(f"- 충실성: {row['faithfulness']}")
        print(f"- 근거성: {row['evidence']}")
        print(f"- 간결성: {row['conciseness']}")
        print(f"- 총점: {row['total_score']}")
        print(f"- 코멘트: {row['comment']}")
        print("-" * 70)

    write_report(evaluation_rows)

    print(f"\nRAG 답변 품질 평가 결과 저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
