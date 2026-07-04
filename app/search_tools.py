from chroma_client import get_chroma_collection
from embedding_client import embed_text


DEFAULT_TOP_K = 3

CHAPTER_SUMMARIES = {
    "chapter07": {
        "brief": (
            "Chapter 7은 긴 문서를 chunk 단위로 나누고, "
            "chunk_size, chunk_overlap, metadata 설계를 통해 "
            "RAG 검색 품질을 개선하는 내용을 다룹니다."
        ),
        "detailed": (
            "Chapter 7에서는 Chapter 6의 Chroma 기반 RAG 구조를 유지하면서 "
            "문서를 문단 단위가 아니라 chunk 단위로 저장하는 방법을 학습합니다. "
            "chunk_size와 chunk_overlap을 조정하고, source, section, paragraph_id, "
            "chunk_index 같은 metadata를 함께 저장합니다. 또한 청킹 전략별 검색 결과를 "
            "비교하면서 좋은 chunking 전략이 RAG 검색 품질에 어떤 영향을 주는지 확인합니다."
        ),
    },
    "chapter08": {
        "brief": (
            "Chapter 8은 top_k, metadata filtering, document filtering, "
            "keyword search, hybrid search, reranking, 검색 품질 평가를 다룹니다."
        ),
        "detailed": (
            "Chapter 8에서는 Chapter 7에서 만든 chunk collection을 재사용하여 "
            "검색 전략을 고도화합니다. top_k 값을 조정하고, metadata filtering과 "
            "document text filtering으로 검색 범위를 제한합니다. 또한 keyword search, "
            "hybrid search, reranking을 구현하고, 검색 결과와 RAG 답변 품질을 평가하는 "
            "간단한 평가표를 작성합니다."
        ),
    },
}


def prepare_question_for_embedding(question: str) -> str:
    """질문 임베딩에 사용할 입력 문장을 만듭니다."""
    return f"question: {question}"


def format_search_result(
    chunk_id: str,
    document: str,
    metadata: dict,
    distance: float | str,
    rank: int,
) -> dict:
    """Chroma 검색 결과를 tool 응답에 사용하기 좋은 dict로 변환합니다."""
    return {
        "rank": rank,
        "chunk_id": chunk_id,
        "source": metadata.get("source", "-"),
        "section": metadata.get("section", "-"),
        "paragraph_id": metadata.get("paragraph_id", "-"),
        "chunk_index": metadata.get("chunk_index", "-"),
        "strategy": metadata.get("strategy", "-"),
        "distance": distance,
        "text": document,
    }


def search_course_policy(question: str, top_k: int = DEFAULT_TOP_K) -> dict:
    """
    수업 운영 정책 문서에서 사용자 질문과 관련 있는 chunk를 vector search로 검색합니다.
    """
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

    search_results = []

    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances),
        start=1,
    ):
        search_results.append(
            format_search_result(
                chunk_id=chunk_id,
                document=document,
                metadata=metadata or {},
                distance=round(float(distance), 4),
                rank=rank,
            )
        )

    return {
        "tool_name": "search_course_policy",
        "question": question,
        "top_k": top_k,
        "result_count": len(search_results),
        "results": search_results,
    }


def filter_course_policy_by_section(
    question: str,
    section: str,
    top_k: int = DEFAULT_TOP_K,
) -> dict:
    """
    특정 section metadata에 해당하는 chunk만 대상으로 vector search를 수행합니다.
    """
    collection = get_chroma_collection()
    question_embedding = embed_text(prepare_question_for_embedding(question))

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        where={"section": section},
        include=["documents", "metadatas", "distances"],
    )

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    search_results = []

    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances),
        start=1,
    ):
        search_results.append(
            format_search_result(
                chunk_id=chunk_id,
                document=document,
                metadata=metadata or {},
                distance=round(float(distance), 4),
                rank=rank,
            )
        )

    return {
        "tool_name": "filter_course_policy_by_section",
        "question": question,
        "section": section,
        "top_k": top_k,
        "result_count": len(search_results),
        "results": search_results,
    }


def search_course_policy_by_keyword(
    keyword: str,
    question: str = "",
    top_k: int = DEFAULT_TOP_K,
) -> dict:
    """
    chunk 본문에 특정 keyword가 포함된 문서만 검색합니다.
    """
    collection = get_chroma_collection()

    if question:
        query_text = question
    else:
        query_text = keyword

    question_embedding = embed_text(prepare_question_for_embedding(query_text))

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        where_document={"$contains": keyword},
        include=["documents", "metadatas", "distances"],
    )

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    search_results = []

    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances),
        start=1,
    ):
        search_results.append(
            format_search_result(
                chunk_id=chunk_id,
                document=document,
                metadata=metadata or {},
                distance=round(float(distance), 4),
                rank=rank,
            )
        )

    return {
        "tool_name": "search_course_policy_by_keyword",
        "keyword": keyword,
        "question": question,
        "top_k": top_k,
        "result_count": len(search_results),
        "results": search_results,
    }


def get_chapter_summary(
    chapter: str,
    detail_level: str = "brief",
) -> dict:
    """
    특정 Chapter의 핵심 내용을 요약합니다.
    """
    normalized_chapter = chapter.lower().strip()
    normalized_detail_level = detail_level.lower().strip()

    if normalized_detail_level not in {"brief", "detailed"}:
        normalized_detail_level = "brief"

    chapter_data = CHAPTER_SUMMARIES.get(normalized_chapter)

    if not chapter_data:
        return {
            "tool_name": "get_chapter_summary",
            "chapter": chapter,
            "detail_level": normalized_detail_level,
            "summary": "지원하지 않는 Chapter입니다. chapter07 또는 chapter08을 입력하세요.",
        }

    return {
        "tool_name": "get_chapter_summary",
        "chapter": normalized_chapter,
        "detail_level": normalized_detail_level,
        "summary": chapter_data[normalized_detail_level],
    }


def execute_tool(tool_name: str, arguments: dict) -> dict:
    """
    tool 이름과 arguments를 받아 실제 tool 함수를 실행합니다.
    """
    if tool_name == "search_course_policy":
        return search_course_policy(
            question=arguments["question"],
            top_k=arguments.get("top_k", DEFAULT_TOP_K),
        )

    if tool_name == "filter_course_policy_by_section":
        return filter_course_policy_by_section(
            question=arguments["question"],
            section=arguments["section"],
            top_k=arguments.get("top_k", DEFAULT_TOP_K),
        )

    if tool_name == "search_course_policy_by_keyword":
        return search_course_policy_by_keyword(
            keyword=arguments["keyword"],
            question=arguments.get("question", ""),
            top_k=arguments.get("top_k", DEFAULT_TOP_K),
        )

    if tool_name == "get_chapter_summary":
        return get_chapter_summary(
            chapter=arguments["chapter"],
            detail_level=arguments.get("detail_level", "brief"),
        )

    raise ValueError(f"지원하지 않는 tool입니다: {tool_name}")


def print_tool_result(result: dict) -> None:
    """tool 실행 결과를 보기 좋게 출력합니다."""
    print("=" * 70)
    print(f"tool_name: {result.get('tool_name')}")
    print("=" * 70)

    if "summary" in result:
        print(f"chapter: {result.get('chapter')}")
        print(f"detail_level: {result.get('detail_level')}")
        print()
        print(result["summary"])
        return

    print(f"question: {result.get('question', '-')}")
    print(f"keyword: {result.get('keyword', '-')}")
    print(f"section: {result.get('section', '-')}")
    print(f"top_k: {result.get('top_k')}")
    print(f"result_count: {result.get('result_count')}")
    print()

    for item in result.get("results", []):
        print(f"[검색 결과 {item['rank']}]")
        print(f"chunk_id: {item['chunk_id']}")
        print(f"source: {item['source']}")
        print(f"section: {item['section']}")
        print(f"paragraph_id: {item['paragraph_id']}")
        print(f"chunk_index: {item['chunk_index']}")
        print(f"strategy: {item['strategy']}")
        print(f"distance: {item['distance']}")
        print()
        print(item["text"])
        print("-" * 70)


def main() -> None:
    """
    search_tools.py 단독 실행 테스트용 예제입니다.
    Chapter 7 chunk 인덱싱이 먼저 완료되어 있어야 합니다.
    """
    examples = [
        {
            "tool_name": "search_course_policy",
            "arguments": {
                "question": "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
                "top_k": 2,
            },
        },
        {
            "tool_name": "filter_course_policy_by_section",
            "arguments": {
                "question": "민감 정보는 어디에 저장해야 하나요?",
                "section": "4. API Key 보안 정책",
                "top_k": 2,
            },
        },
        {
            "tool_name": "search_course_policy_by_keyword",
            "arguments": {
                "keyword": "GitHub",
                "question": "GitHub 제출 기준을 알려줘.",
                "top_k": 2,
            },
        },
        {
            "tool_name": "get_chapter_summary",
            "arguments": {
                "chapter": "chapter08",
                "detail_level": "brief",
            },
        },
    ]

    for example in examples:
        result = execute_tool(
            tool_name=example["tool_name"],
            arguments=example["arguments"],
        )
        print_tool_result(result)
        print()


if __name__ == "__main__":
    main()
