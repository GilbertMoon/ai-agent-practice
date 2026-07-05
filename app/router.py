"""
Chapter 10 Router

사용자 질문을 보고 workflow route를 결정합니다.
"""

SEARCH_KEYWORDS = [
    "공지",
    "제출",
    "미니 프로젝트",
    "보안",
    "API Key",
    "api key",
    "GitHub",
    "깃허브",
    "오류",
    "에러",
    "과제",
    "질문",
    "결과물",
    "파일",
]

CONCEPT_KEYWORDS = [
    "RAG",
    "LLM",
    "임베딩",
    "벡터",
    "Tool Calling",
    "툴 콜링",
    "에이전트",
    "워크플로우",
]


def contains_any_keyword(text: str, keywords: list[str]) -> bool:
    """문자열에 키워드 목록 중 하나라도 포함되어 있는지 확인합니다."""
    lowered_text = text.lower()
    return any(keyword.lower() in lowered_text for keyword in keywords)


def decide_route(question: str) -> tuple[str, str]:
    """사용자 질문을 보고 workflow route를 결정합니다."""
    normalized = question.strip()

    if not normalized:
        return "clarification", "질문이 비어 있어 추가 질문이 필요합니다."

    if contains_any_keyword(normalized, SEARCH_KEYWORDS):
        return "search", "수업 공지나 제출 안내 검색이 필요한 질문입니다."

    if contains_any_keyword(normalized, CONCEPT_KEYWORDS):
        return "direct_answer", "일반 개념 설명으로 답변할 수 있는 질문입니다."

    return "direct_answer", "명확한 검색 단서가 없어 일반 답변 경로를 선택했습니다."


def is_search_route(route: str) -> bool:
    return route == "search"


def is_direct_answer_route(route: str) -> bool:
    return route == "direct_answer"


def is_clarification_route(route: str) -> bool:
    return route == "clarification"


if __name__ == "__main__":
    examples = [
        "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
        "RAG가 무엇인가요?",
        "",
    ]

    for question in examples:
        route, reason = decide_route(question)
        print("=" * 70)
        print(f"질문: {question!r}")
        print(f"route: {route}")
        print(f"reason: {reason}")