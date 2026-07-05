"""
Chapter 15 Tool Registry

최종 프로젝트에서 사용할 수 있는 간단한 도구들을 등록합니다.
"""

from __future__ import annotations

from typing import Callable


def summarize_text(tool_input: dict) -> dict:
    text = tool_input.get("text", "")
    summary = text.strip().replace("\n", " ")[:220]
    return {"status": "success", "tool": "summarize_text", "result": f"요약: {summary}"}


def draft_email(tool_input: dict) -> dict:
    request = tool_input.get("request", "")
    body = (
        "안녕하세요.\n\n"
        f"요청하신 내용에 대해 아래와 같이 안내드립니다.\n\n{request}\n\n"
        "확인 후 의견 부탁드립니다.\n\n감사합니다."
    )
    return {"status": "success", "tool": "draft_email", "result": body}


def extract_action_items(tool_input: dict) -> dict:
    text = tool_input.get("text", "")
    candidates = [line.strip("-• ") for line in text.splitlines() if line.strip()]
    actions = candidates[:5] or ["추가 확인이 필요한 작업을 정리합니다."]
    return {"status": "success", "tool": "extract_action_items", "result": actions}


TOOLS: dict[str, Callable[[dict], dict]] = {
    "summarize_text": summarize_text,
    "draft_email": draft_email,
    "extract_action_items": extract_action_items,
}


def choose_tool(user_request: str) -> str | None:
    lowered = user_request.lower()
    if "메일" in lowered or "email" in lowered:
        return "draft_email"
    if "액션" in lowered or "할 일" in lowered or "action" in lowered:
        return "extract_action_items"
    if "요약" in lowered or "summary" in lowered:
        return "summarize_text"
    return None


def run_if_needed(user_request: str, context: str) -> dict | None:
    tool_name = choose_tool(user_request)
    if not tool_name:
        return None
    tool = TOOLS[tool_name]
    return tool({"request": user_request, "text": context})