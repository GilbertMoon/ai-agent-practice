import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tool_registry import get_registered_tool_names, is_tool_registered
from tool_schemas import get_tool_declarations


DEFAULT_QUESTION = "오류 질문을 할 때 무엇을 함께 공유해야 하나요?"


def create_gemini_client() -> genai.Client:
    """Gemini API client를 생성합니다."""
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key == "your_api_key_here":
        raise RuntimeError(
            "GEMINI_API_KEY가 설정되어 있지 않습니다. "
            "프로젝트 루트의 .env 파일을 확인하세요."
        )

    return genai.Client(api_key=api_key)


def load_model_name() -> str:
    """Function Calling 요청에 사용할 Gemini 모델 이름을 .env에서 가져옵니다."""
    load_dotenv()
    model_name = os.getenv("GEMINI_MODEL_NAME")

    if not model_name:
        raise RuntimeError(
            "GEMINI_MODEL_NAME이 설정되어 있지 않습니다. "
            "프로젝트 루트의 .env 파일을 확인하세요."
        )

    return model_name


def build_system_instruction() -> str:
    """Function Calling 판단을 위한 system instruction을 만듭니다."""
    return """
당신은 AI Agent Engineering 수업 도우미입니다.

사용자의 질문이 수업 운영 정책, 과제, 보안, GitHub 제출, 오류 질문,
Chapter 7/8 복습과 관련되어 있으면 적절한 tool을 선택하세요.

가능한 tool은 다음과 같습니다.

- search_course_policy
- filter_course_policy_by_section
- search_course_policy_by_keyword
- get_chapter_summary

tool 호출이 필요하지 않으면 일반 답변을 작성하세요.
""".strip()


def request_function_call(question: str) -> Any:
    """
    Gemini에게 질문을 보내고 function call step이 포함된 응답을 받습니다.

    이 함수는 tool을 실제 실행하지 않습니다.
    LLM이 어떤 tool을 호출하려고 하는지만 확인합니다.
    """
    client = create_gemini_client()
    tool_declarations = get_tool_declarations()

    response = client.models.generate_content(
        model=load_model_name(),
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=build_system_instruction(),
            tools=[
                types.Tool(
                    functionDeclarations=tool_declarations,
                )
            ],
        ),
    )

    return response


def part_to_dict(part: Any) -> dict[str, Any]:
    """Gemini response part를 보기 쉬운 dict로 변환합니다."""
    result = {
        "has_text": False,
        "text": None,
        "has_function_call": False,
        "function_call": None,
    }

    if getattr(part, "text", None):
        result["has_text"] = True
        result["text"] = part.text

    function_call = getattr(part, "function_call", None)

    if function_call:
        result["has_function_call"] = True
        result["function_call"] = {
            "name": function_call.name,
            "args": dict(function_call.args or {}),
        }

    return result


def extract_response_parts(response: Any) -> list[dict[str, Any]]:
    """Gemini response에서 text part와 function_call part를 추출합니다."""
    parts_summary = []

    candidates = getattr(response, "candidates", []) or []

    for candidate_index, candidate in enumerate(candidates, start=1):
        content = getattr(candidate, "content", None)

        if not content:
            continue

        parts = getattr(content, "parts", []) or []

        for part_index, part in enumerate(parts, start=1):
            part_dict = part_to_dict(part)
            part_dict["candidate_index"] = candidate_index
            part_dict["part_index"] = part_index
            parts_summary.append(part_dict)

    return parts_summary


def find_function_calls(parts_summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """응답 part 목록에서 function call만 추출합니다."""
    function_calls = []

    for part in parts_summary:
        if part["has_function_call"]:
            function_call = part["function_call"]
            tool_name = function_call["name"]

            function_calls.append(
                {
                    "candidate_index": part["candidate_index"],
                    "part_index": part["part_index"],
                    "name": tool_name,
                    "args": function_call["args"],
                    "registered": is_tool_registered(tool_name),
                }
            )

    return function_calls


def print_registered_tools() -> None:
    """현재 등록된 tool 이름 목록을 출력합니다."""
    print("등록된 Tool Registry 목록")
    print("=" * 70)

    for tool_name in get_registered_tool_names():
        print(f"- {tool_name}")

    print()


def print_function_call_summary(
    question: str,
    parts_summary: list[dict[str, Any]],
    function_calls: list[dict[str, Any]],
) -> None:
    """Function Call Step 해석 결과를 출력합니다."""
    print("Function Call Step 해석 결과")
    print("=" * 70)
    print(f"질문: {question}")
    print("=" * 70)
    print()

    if not parts_summary:
        print("응답 part를 찾지 못했습니다.")
        return

    print("[응답 Part 목록]")
    for part in parts_summary:
        print(
            f"- candidate={part['candidate_index']}, "
            f"part={part['part_index']}, "
            f"has_text={part['has_text']}, "
            f"has_function_call={part['has_function_call']}"
        )

        if part["has_text"]:
            print(f"  text: {part['text']}")

        if part["has_function_call"]:
            print(
                "  function_call: "
                + json.dumps(
                    part["function_call"],
                    ensure_ascii=False,
                    indent=2,
                )
            )

    print()
    print("[Function Call 해석]")

    if not function_calls:
        print("LLM이 function call을 요청하지 않았습니다.")
        print("이 경우 일반 텍스트 답변으로 처리할 수 있습니다.")
        return

    for call in function_calls:
        print(f"- tool name: {call['name']}")
        print(f"  arguments: {json.dumps(call['args'], ensure_ascii=False)}")
        print(f"  registry 등록 여부: {call['registered']}")

        if call["registered"]:
            print("  해석: 이 tool은 Tool Registry에 등록되어 있으므로 다음 단계에서 실행할 수 있습니다.")
        else:
            print("  해석: 이 tool은 Tool Registry에 등록되어 있지 않아 실행하면 안 됩니다.")


def main() -> None:
    print_registered_tools()

    question = input(f"질문을 입력하세요 [{DEFAULT_QUESTION}]: ").strip()

    if not question:
        question = DEFAULT_QUESTION

    print()
    print("Gemini에 Function Call 판단을 요청합니다.")
    print("이 단계에서는 tool을 실제 실행하지 않고, function call 요청만 해석합니다.")
    print()

    response = request_function_call(question)
    parts_summary = extract_response_parts(response)
    function_calls = find_function_calls(parts_summary)

    print_function_call_summary(
        question=question,
        parts_summary=parts_summary,
        function_calls=function_calls,
    )


if __name__ == "__main__":
    main()
