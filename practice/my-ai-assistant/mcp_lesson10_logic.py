"""Lesson 10 safe read-only MCP business logic.

This module deliberately has no dependency on MCP or any model/provider.
The server uses these functions; fixture and unit tests call them directly.
"""
from __future__ import annotations
from document_qa import DEFAULT_DOC, read_document, retrieve


def add_numbers(a: int, b: int) -> dict[str, int]:
    if type(a) is not int or type(b) is not int:
        raise ValueError("두 값은 정수여야 합니다.")
    if abs(a) > 100000 or abs(b) > 100000:
        raise ValueError("허용 범위는 각 정수 절댓값 100000 이하입니다.")
    return {"sum": a + b}


def find_notice(query: str) -> dict:
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 100:
        raise ValueError("검색어는 1~100자 문자열이어야 합니다.")
    results = retrieve(read_document(DEFAULT_DOC), query.strip(), DEFAULT_DOC.name, top_k=1)
    if not results:
        return {"found": False, "source": DEFAULT_DOC.name}
    item = results[0]
    return {"found": True, "source": item.source, "section": item.section, "text": item.text}


def public_notice() -> str:
    # Fixed teaching document only; not a generic filesystem reader.
    return read_document(DEFAULT_DOC)


def lesson_prompt(topic: str) -> str:
    if not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 80:
        raise ValueError("topic은 1~80자 문자열이어야 합니다.")
    return f"다음 주제를 초보자에게 쉬운 한국어로 세 문장으로 설명해 주세요: {topic.strip()}"
