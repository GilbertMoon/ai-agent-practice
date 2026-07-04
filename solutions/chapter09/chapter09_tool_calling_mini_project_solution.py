"""
Chapter 9 미니 프로젝트 답안

주제: Tool Calling 기반 검색 Q&A Agent 만들기

이 답안은 Chapter 9에서 만든 구성 요소를 하나로 연결합니다.

포함 기능:
1. 여러 tool 목록 확인
2. 질문 유형에 따른 function_call 생성
3. arguments 검증 및 Tool Dispatcher 실행
4. tool 실행 결과 기반 최종 답변 생성
5. tool 실행 로그 저장
6. 실행 결과 리포트 생성

실행 전 준비:
- Chapter 7 chunk 인덱싱 완료
  python app/chunk_index_documents.py

실행:
  python solutions/chapter09/chapter09_tool_calling_mini_project_solution.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
LOG_PATH = OUTPUT_DIR / "chapter09_tool_calling_mini_project_logs.jsonl"
REPORT_PATH = OUTPUT_DIR / "chapter09_tool_calling_mini_project_report.md"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from tool_dispatcher import safe_dispatch_function_call  # noqa: E402
from tool_registry import get_registered_tool_names  # noqa: E402
from tool_schemas import get_tool_declarations  # noqa: E402


DEFAULT_QUESTIONS = [
    "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
    "API Key 보안 정책만 기준으로 설명해 주세요.",
    "GitHub라는 단어가 들어간 제출 기준을 알려주세요.",
    "Chapter 8 내용을 간단히 요약해 주세요.",
]

SENSITIVE_PATTERNS = [
    r"(?i)api[_-]?key",
    r"(?i)secret",
    r"(?i)token",
    r"(?i)password",
    r"(?i)\.env",
    r"(?i)gemini_api_key",
    r"(?i)openai_api_key",
    r"[A-Za-z]:\\\\[^\s]+",
    r"/home/[^\s]+",
    r"/mnt/data/[^\s]+",
]


# -----------------------------------------------------------------------------
# 1. 공통 유틸리티
# -----------------------------------------------------------------------------


def now_iso() -> str:
    """현재 시각을 ISO 8601 문자열로 반환합니다."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_output_dir() -> None:
    """outputs 디렉터리를 생성합니다."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_text(text: str) -> str:
    """민감정보로 보이는 문자열을 마스킹합니다."""
    sanitized = text

    for pattern in SENSITIVE_PATTERNS:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized)

    return sanitized


def sanitize_value(value: Any) -> Any:
    """dict/list/string 내부의 민감정보를 재귀적으로 마스킹합니다."""
    if isinstance(value, str):
        return sanitize_text(value)

    if isinstance(value, list):
        return [sanitize_value(item) for item in value]

    if isinstance(value, dict):
        return {
            sanitize_text(str(key)): sanitize_value(item)
            for key, item in value.items()
        }

    return value


def to_json(value: Any) -> str:
    """한글이 깨지지 않는 JSON 문자열을 만듭니다."""
    return json.dumps(value, ensure_ascii=False, indent=2)


# -----------------------------------------------------------------------------
# 2. Tool 목록 확인
# -----------------------------------------------------------------------------


def get_tool_summary() -> list[dict[str, Any]]:
    """Function Declaration과 Tool Registry 연결 상태를 요약합니다."""
    declarations = get_tool_declarations()
    registered_tool_names = set(get_registered_tool_names())

    summary = []

    for declaration in declarations:
        tool_name = declaration["name"]
        parameters = declaration.get("parameters", {})

        summary.append(
            {
                "name": tool_name,
                "registered": tool_name in registered_tool_names,
                "description": declaration.get("description", ""),
                "required": parameters.get("required", []),
            }
        )

    return summary


def print_tool_summary() -> None:
    """현재 사용 가능한 tool 목록을 출력합니다."""
    print("=" * 80)
    print("Chapter 9 Mini Project - Tool 목록")
    print("=" * 80)

    for item in get_tool_summary():
        status = "등록됨" if item["registered"] else "미등록"
        print(f"- {item['name']} ({status})")
        print(f"  required: {item['required']}")
        print(f"  description: {item['description']}")
        print()


# -----------------------------------------------------------------------------
# 3. Function Call 생성
# -----------------------------------------------------------------------------


def select_function_call_by_rule(question: str) -> dict[str, Any]:
    """
    질문을 보고 사용할 tool을 선택합니다.

    실제 서비스에서는 LLM이 function_call을 생성하지만,
    미니 프로젝트 답안에서는 실행 안정성을 위해 규칙 기반 선택도 함께 제공합니다.
    """
    lowered = question.lower()

    if "chapter 8" in lowered or "chapter08" in lowered or "챕터 8" in question:
        return {
            "name": "get_chapter_summary",
            "args": {
                "chapter": "chapter08",
                "detail_level": "brief",
            },
        }

    if "api key" in lowered or "보안" in question or "민감" in question:
        return {
            "name": "filter_course_policy_by_section",
            "args": {
                "question": question,
                "section": "4. API Key 보안 정책",
                "top_k": 3,
            },
        }

    if "github" in lowered or "깃허브" in question:
        return {
            "name": "search_course_policy_by_keyword",
            "args": {
                "keyword": "GitHub",
                "question": question,
                "top_k": 3,
            },
        }

    return {
        "name": "search_course_policy",
        "args": {
            "question": question,
            "top_k": 3,
        },
    }


# -----------------------------------------------------------------------------
# 4. Tool 실행 결과 해석
# -----------------------------------------------------------------------------


def get_result_count(dispatch_response: dict[str, Any] | None) -> int | None:
    """Tool Dispatcher 응답에서 검색 결과 개수를 추출합니다."""
    if not isinstance(dispatch_response, dict):
        return None

    result = dispatch_response.get("result")

    if not isinstance(result, dict):
        return None

    if "result_count" in result:
        return result["result_count"]

    results = result.get("results")

    if isinstance(results, list):
        return len(results)

    return None


def get_error_summary(dispatch_response: dict[str, Any] | None) -> str | None:
    """Tool Dispatcher 오류 정보를 안전하게 요약합니다."""
    if not isinstance(dispatch_response, dict):
        return None

    error = dispatch_response.get("error")

    if not error:
        return None

    return sanitize_text(json.dumps(error, ensure_ascii=False))


def build_final_answer(question: str, dispatch_response: dict[str, Any]) -> str:
    """tool 실행 결과를 바탕으로 최종 답변을 구성합니다."""
    if not dispatch_response.get("is_success"):
        error_summary = get_error_summary(dispatch_response)
        return (
            "요청하신 질문을 처리하는 중 tool 실행 오류가 발생했습니다.\n"
            "내부 정보는 노출하지 않고, 안전한 오류 요약만 표시합니다.\n"
            f"오류 요약: {error_summary}"
        )

    tool_name = dispatch_response.get("tool_name")
    result = dispatch_response.get("result", {})

    if not isinstance(result, dict):
        return "tool 실행 결과 형식이 올바르지 않습니다."

    if "summary" in result:
        return (
            f"질문: {question}\n\n"
            f"선택된 tool: {tool_name}\n\n"
            f"답변:\n{result['summary']}"
        )

    search_results = result.get("results", [])

    if not search_results:
        return (
            f"질문: {question}\n\n"
            f"선택된 tool: {tool_name}\n\n"
            "검색 결과를 찾지 못했습니다. 질문을 더 구체적으로 작성해 주세요."
        )

    lines = [
        f"질문: {question}",
        "",
        f"선택된 tool: {tool_name}",
        f"검색 결과 수: {len(search_results)}",
        "",
        "답변 근거:",
    ]

    for index, item in enumerate(search_results[:3], start=1):
        source = item.get("source", "-")
        section = item.get("section", "-")
        chunk_id = item.get("chunk_id", "-")
        text = item.get("text", "").strip().replace("\n", " ")

        if len(text) > 220:
            text = text[:220] + "..."

        lines.append(f"{index}. source={source}, section={section}, chunk_id={chunk_id}")
        lines.append(f"   {text}")

    lines.append("")
    lines.append("위 근거를 기준으로 답변을 작성하면 됩니다.")

    return "\n".join(lines)


# -----------------------------------------------------------------------------
# 5. 로그 기록
# -----------------------------------------------------------------------------


def build_log_record(
    question: str,
    function_call: dict[str, Any],
    dispatch_response: dict[str, Any],
    final_answer: str,
) -> dict[str, Any]:
    """Tool Calling 실행 로그 record를 만듭니다."""
    return sanitize_value(
        {
            "timestamp": now_iso(),
            "user_question": question,
            "selected_tool": function_call.get("name"),
            "arguments": function_call.get("args", {}),
            "result_count": get_result_count(dispatch_response),
            "has_error": not bool(dispatch_response.get("is_success")),
            "error_summary": get_error_summary(dispatch_response),
            "final_answer_preview": final_answer[:300],
        }
    )


def append_log(record: dict[str, Any]) -> None:
    """JSON Lines 형식으로 로그를 저장합니다."""
    ensure_output_dir()

    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


# -----------------------------------------------------------------------------
# 6. 미니 프로젝트 실행
# -----------------------------------------------------------------------------


def run_one_question(question: str) -> dict[str, Any]:
    """질문 하나에 대해 mini project 전체 흐름을 실행합니다."""
    function_call = select_function_call_by_rule(question)
    dispatch_response = safe_dispatch_function_call(function_call)
    final_answer = build_final_answer(question, dispatch_response)

    log_record = build_log_record(
        question=question,
        function_call=function_call,
        dispatch_response=dispatch_response,
        final_answer=final_answer,
    )
    append_log(log_record)

    return {
        "question": question,
        "function_call": function_call,
        "dispatch_response": sanitize_value(dispatch_response),
        "final_answer": sanitize_text(final_answer),
        "log_record": log_record,
    }


def run_demo_questions() -> list[dict[str, Any]]:
    """기본 예제 질문을 순서대로 실행합니다."""
    results = []

    for question in DEFAULT_QUESTIONS:
        result = run_one_question(question)
        results.append(result)

    return results


# -----------------------------------------------------------------------------
# 7. 리포트 생성
# -----------------------------------------------------------------------------


def format_result_for_report(result: dict[str, Any], index: int) -> str:
    """질문별 실행 결과를 Markdown 문자열로 변환합니다."""
    function_call = result["function_call"]
    dispatch_response = result["dispatch_response"]

    lines = [
        f"## {index}. 질문 실행 결과",
        "",
        f"**질문**: {result['question']}",
        "",
        "**선택된 function_call**",
        "",
        "```json",
        json.dumps(function_call, ensure_ascii=False, indent=2),
        "```",
        "",
        "**Tool Dispatcher 실행 요약**",
        "",
        f"- 성공 여부: {dispatch_response.get('is_success')}",
        f"- tool_name: {dispatch_response.get('tool_name')}",
        f"- result_count: {get_result_count(dispatch_response)}",
        f"- error: {get_error_summary(dispatch_response)}",
        "",
        "**최종 답변**",
        "",
        "```text",
        result["final_answer"],
        "```",
        "",
    ]

    return "\n".join(lines)


def write_report(results: list[dict[str, Any]]) -> None:
    """Chapter 9 미니 프로젝트 실행 리포트를 Markdown으로 저장합니다."""
    ensure_output_dir()

    lines = [
        "# Chapter 9 미니 프로젝트 답안 실행 리포트",
        "",
        f"생성 시각: {now_iso()}",
        "",
        "## 프로젝트 목표",
        "",
        "Tool Calling 기반 검색 Q&A Agent를 구성하고, 여러 tool 중 적절한 tool을 선택한 뒤 실행 결과를 바탕으로 답변을 생성합니다.",
        "",
        "## 사용한 구성 요소",
        "",
        "- Function Declaration",
        "- Tool Registry",
        "- Argument Validator",
        "- Tool Dispatcher",
        "- Tool 실행 로그",
        "- 검색 결과 기반 최종 답변 생성",
        "",
        "## 등록된 Tool 목록",
        "",
    ]

    for item in get_tool_summary():
        status = "등록됨" if item["registered"] else "미등록"
        lines.append(f"- `{item['name']}`: {status}")

    lines.extend(
        [
            "",
            "## 로그 파일",
            "",
            f"- `{LOG_PATH.relative_to(PROJECT_ROOT)}`",
            "",
        ]
    )

    for index, result in enumerate(results, start=1):
        lines.append(format_result_for_report(result, index))

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


# -----------------------------------------------------------------------------
# 8. 출력
# -----------------------------------------------------------------------------


def print_result(result: dict[str, Any]) -> None:
    """실행 결과를 콘솔에 출력합니다."""
    function_call = result["function_call"]
    dispatch_response = result["dispatch_response"]

    print("=" * 80)
    print("Chapter 9 Mini Project 실행 결과")
    print("=" * 80)
    print(f"질문: {result['question']}")
    print(f"선택된 tool: {function_call.get('name')}")
    print(f"arguments: {json.dumps(function_call.get('args', {}), ensure_ascii=False)}")
    print(f"성공 여부: {dispatch_response.get('is_success')}")
    print(f"result_count: {get_result_count(dispatch_response)}")
    print()
    print("[최종 답변]")
    print(result["final_answer"])
    print()


def main() -> None:
    """Chapter 9 미니 프로젝트 답안 실행 진입점입니다."""
    print_tool_summary()

    print("실행 모드를 선택하세요.")
    print("1. 예제 질문 전체 실행")
    print("2. 직접 질문 입력")
    print()

    mode = input("선택 [1]: ").strip() or "1"

    if mode == "1":
        results = run_demo_questions()

        for result in results:
            print_result(result)

        write_report(results)
        print(f"리포트 저장 완료: {REPORT_PATH}")
        print(f"로그 저장 완료: {LOG_PATH}")

    elif mode == "2":
        question = input("질문을 입력하세요: ").strip()

        if not question:
            print("질문이 비어 있어 기본 질문을 실행합니다.")
            question = DEFAULT_QUESTIONS[0]

        result = run_one_question(question)
        print_result(result)
        write_report([result])
        print(f"리포트 저장 완료: {REPORT_PATH}")
        print(f"로그 저장 완료: {LOG_PATH}")

    else:
        print("지원하지 않는 모드입니다. 1 또는 2를 입력하세요.")


if __name__ == "__main__":
    main()
