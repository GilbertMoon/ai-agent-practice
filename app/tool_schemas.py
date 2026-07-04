import json
from typing import Any


SEARCH_COURSE_POLICY_DECLARATION: dict[str, Any] = {
    "name": "search_course_policy",
    "description": (
        "수업 운영 정책 문서에서 사용자 질문과 관련 있는 chunk를 "
        "vector search로 검색합니다. 과제, 보안, GitHub 제출, 오류 질문, "
        "미니 프로젝트 안내처럼 의미 기반 검색이 필요한 질문에 사용합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "검색할 사용자 질문입니다.",
            },
            "top_k": {
                "type": "integer",
                "description": "가져올 검색 결과 개수입니다. 기본값은 3입니다.",
            },
        },
        "required": ["question"],
    },
}


FILTER_COURSE_POLICY_BY_SECTION_DECLARATION: dict[str, Any] = {
    "name": "filter_course_policy_by_section",
    "description": (
        "수업 운영 정책 문서에서 특정 section metadata에 해당하는 chunk만 "
        "대상으로 검색합니다. 사용자가 보안 안내, 과제 제출 정책, 오류 질문 방법처럼 "
        "특정 섹션을 명시했을 때 사용합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "검색할 사용자 질문입니다.",
            },
            "section": {
                "type": "string",
                "description": (
                    "검색 범위를 제한할 section 이름입니다. "
                    "예: 4. API Key 보안 정책, 5. 과제 제출 정책, "
                    "6. GitHub 제출 기준, 7. 오류 질문 방법"
                ),
            },
            "top_k": {
                "type": "integer",
                "description": "가져올 검색 결과 개수입니다. 기본값은 3입니다.",
            },
        },
        "required": ["question", "section"],
    },
}


SEARCH_COURSE_POLICY_BY_KEYWORD_DECLARATION: dict[str, Any] = {
    "name": "search_course_policy_by_keyword",
    "description": (
        "수업 운영 정책 문서에서 특정 키워드가 본문에 포함된 chunk를 검색합니다. "
        "GitHub, README.md, 오류, 제출처럼 특정 단어 포함 여부가 중요한 질문에 사용합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "chunk 본문에서 찾을 키워드입니다.",
            },
            "question": {
                "type": "string",
                "description": "검색 의도를 나타내는 사용자 질문입니다.",
            },
            "top_k": {
                "type": "integer",
                "description": "가져올 검색 결과 개수입니다. 기본값은 3입니다.",
            },
        },
        "required": ["keyword"],
    },
}


GET_CHAPTER_SUMMARY_DECLARATION: dict[str, Any] = {
    "name": "get_chapter_summary",
    "description": (
        "특정 Chapter의 핵심 학습 내용을 요약합니다. "
        "사용자가 Chapter 7 또는 Chapter 8에서 배운 내용을 복습하려고 할 때 사용합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "chapter": {
                "type": "string",
                "description": "요약할 Chapter 번호입니다. 예: chapter07, chapter08",
            },
            "detail_level": {
                "type": "string",
                "description": "요약 수준입니다. brief 또는 detailed 중 하나를 사용합니다.",
                "enum": ["brief", "detailed"],
            },
        },
        "required": ["chapter"],
    },
}


TOOL_DECLARATIONS: list[dict[str, Any]] = [
    SEARCH_COURSE_POLICY_DECLARATION,
    FILTER_COURSE_POLICY_BY_SECTION_DECLARATION,
    SEARCH_COURSE_POLICY_BY_KEYWORD_DECLARATION,
    GET_CHAPTER_SUMMARY_DECLARATION,
]


def get_tool_declarations() -> list[dict[str, Any]]:
    """LLM에 전달할 function declaration 목록을 반환합니다."""
    return TOOL_DECLARATIONS


def get_tool_names() -> list[str]:
    """등록된 tool 이름 목록을 반환합니다."""
    return [tool["name"] for tool in TOOL_DECLARATIONS]


def get_tool_declaration_by_name(tool_name: str) -> dict[str, Any] | None:
    """tool 이름으로 function declaration을 조회합니다."""
    for tool in TOOL_DECLARATIONS:
        if tool["name"] == tool_name:
            return tool

    return None


def print_tool_declarations() -> None:
    """function declaration 목록을 보기 좋게 출력합니다."""
    print("등록된 Function Declaration 목록")
    print("=" * 70)

    for index, tool in enumerate(TOOL_DECLARATIONS, start=1):
        print(f"\n[{index}] {tool['name']}")
        print(f"description: {tool['description']}")
        print("parameters:")
        print(
            json.dumps(
                tool["parameters"],
                ensure_ascii=False,
                indent=2,
            )
        )


def main() -> None:
    print_tool_declarations()

    print("\n사용 가능한 tool 이름:")
    for tool_name in get_tool_names():
        print(f"- {tool_name}")


if __name__ == "__main__":
    main()
