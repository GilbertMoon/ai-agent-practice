import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tool_dispatcher import safe_dispatch_function_call
from tool_schemas import get_tool_declarations


MODEL_NAME = "gemini-2.0-flash"
DEFAULT_QUESTION = "오류 질문을 할 때 무엇을 함께 공유해야 하나요?"


def create_gemini_client() -> genai.Client:
    """Gemini API client를 생성합니다."""
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY가 설정되어 있지 않습니다. "
            "프로젝트 루트의 .env 파일을 확인하세요."
        )

    return genai.Client(api_key=api_key)


def build_system_instruction() -> str:
    """Tool Calling 기반 Q&A를 위한 system instruction을 만듭니다."""
    return """
당신은 AI Agent Engineering 수업 도우미입니다.

사용자의 질문이 수업 운영 정책, 과제, 보안, GitHub 제출, 오류 질문,
Chapter 7/8 복습과 관련되어 있으면 적절한 tool을 선택하세요.

tool 실행 결과를 받은 뒤에는 반드시 tool 결과에 근거해서 한국어로 답변하세요.
근거가 부족하면 추측하지 말고, 확인 가능한 범위만 답변하세요.
답변 끝에는 가능하면 source, section, chunk_id를 간단히 표시하세요.
""".strip()


def request_function_call(client: genai.Client, question: str) -> Any:
    """
    1차 interaction입니다.

    사용자 질문과 Function Declaration을 모델에 전달하고,
    모델이 function_call을 선택하는지 확인합니다.
    """
    tool_declarations = get_tool_declarations()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=build_system_instruction(),
            tools=[
                types.Tool(
                    function_declarations=tool_declarations,
                )
            ],
        ),
    )

    return response


def extract_first_function_call(response: Any) -> dict[str, Any] | None:
    """Gemini 응답에서 첫 번째 function_call을 추출합니다."""
    candidates = getattr(response, "candidates", []) or []

    for candidate in candidates:
        content = getattr(candidate, "content", None)

        if not content:
            continue

        parts = getattr(content, "parts", []) or []

        for part in parts:
            function_call = getattr(part, "function_call", None)

            if not function_call:
                continue

            return {
                "name": function_call.name,
                "args": dict(function_call.args or {}),
            }

    return None


def extract_text_response(response: Any) -> str:
    """Gemini 응답에서 text part를 모아 하나의 문자열로 반환합니다."""
    text_parts = []
    candidates = getattr(response, "candidates", []) or []

    for candidate in candidates:
        content = getattr(candidate, "content", None)

        if not content:
            continue

        parts = getattr(content, "parts", []) or []

        for part in parts:
            text = getattr(part, "text", None)

            if text:
                text_parts.append(text)

    return "\n".join(text_parts).strip()


def get_first_model_content(response: Any) -> Any | None:
    """2차 interaction에 전달할 1차 모델 응답 content를 가져옵니다."""
    candidates = getattr(response, "candidates", []) or []

    if not candidates:
        return None

    return getattr(candidates[0], "content", None)


def build_function_response_part(
    function_call: dict[str, Any],
    dispatch_response: dict[str, Any],
) -> Any:
    """
    tool 실행 결과를 모델에 다시 전달할 function_response part로 변환합니다.

    OpenAI Responses API에서는 function_result에 call_id를 연결하는 방식이 자주 쓰입니다.
    Gemini에서는 function_call.name에 대응되는 function_response를 Content part로 전달합니다.
    """
    tool_name = function_call["name"]

    response_payload = {
        "tool_name": tool_name,
        "is_success": dispatch_response.get("is_success"),
        "error": dispatch_response.get("error"),
        "result": dispatch_response.get("result"),
    }

    try:
        return types.Part.from_function_response(
            name=tool_name,
            response=response_payload,
        )

    except AttributeError:
        return types.Part(
            function_response=types.FunctionResponse(
                name=tool_name,
                response=response_payload,
            )
        )


def request_final_answer(
    client: genai.Client,
    question: str,
    first_response: Any,
    function_call: dict[str, Any],
    dispatch_response: dict[str, Any],
) -> Any:
    """
    2차 interaction입니다.

    Python tool 실행 결과를 function_response로 모델에 다시 전달하고,
    최종 자연어 답변을 생성합니다.
    """
    first_model_content = get_first_model_content(first_response)
    function_response_part = build_function_response_part(
        function_call=function_call,
        dispatch_response=dispatch_response,
    )

    contents = [question]

    if first_model_content is not None:
        contents.append(first_model_content)

    contents.append(
        types.Content(
            role="tool",
            parts=[function_response_part],
        )
    )

    final_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=build_system_instruction(),
            tools=[
                types.Tool(
                    function_declarations=get_tool_declarations(),
                )
            ],
        ),
    )

    return final_response


def run_tool_calling_round(question: str) -> dict[str, Any]:
    """
    Function Calling 전체 흐름을 한 번 실행합니다.

    처리 순서:
    1. 사용자 질문을 모델에 전달한다.
    2. 모델이 function_call을 반환하는지 확인한다.
    3. function_call을 Tool Dispatcher로 실행한다.
    4. tool 실행 결과를 function_response로 모델에 다시 전달한다.
    5. 최종 자연어 답변을 받는다.
    """
    client = create_gemini_client()

    first_response = request_function_call(
        client=client,
        question=question,
    )

    function_call = extract_first_function_call(first_response)

    if function_call is None:
        text_answer = extract_text_response(first_response)

        return {
            "question": question,
            "used_tool": False,
            "function_call": None,
            "dispatch_response": None,
            "final_answer": text_answer,
        }

    dispatch_response = safe_dispatch_function_call(function_call)

    final_response = request_final_answer(
        client=client,
        question=question,
        first_response=first_response,
        function_call=function_call,
        dispatch_response=dispatch_response,
    )

    final_answer = extract_text_response(final_response)

    return {
        "question": question,
        "used_tool": True,
        "function_call": function_call,
        "dispatch_response": dispatch_response,
        "final_answer": final_answer,
    }


def print_round_result(result: dict[str, Any]) -> None:
    """Function Result 전달 흐름 실행 결과를 보기 좋게 출력합니다."""
    print("=" * 70)
    print("Function Result를 모델에 다시 전달하기")
    print("=" * 70)
    print(f"질문: {result['question']}")
    print(f"tool 사용 여부: {result['used_tool']}")
    print()

    if result["function_call"]:
        print("[1차 interaction: function_call]")
        print(json.dumps(result["function_call"], ensure_ascii=False, indent=2))
        print()

    if result["dispatch_response"]:
        print("[Python tool 실행 결과]")
        print(json.dumps(result["dispatch_response"], ensure_ascii=False, indent=2))
        print()

    print("[2차 interaction: 최종 답변]")
    print(result["final_answer"])
    print()


def main() -> None:
    """
    function_result_response.py 단독 실행 예제입니다.

    실행 전 준비:
    1. .env에 GEMINI_API_KEY 설정
    2. Chapter 7 chunk 인덱싱 완료
    """
    question = input(f"질문을 입력하세요 [{DEFAULT_QUESTION}]: ").strip()

    if not question:
        question = DEFAULT_QUESTION

    print()
    print("1차 interaction → tool 실행 → function result 전달 → 최종 답변 생성을 시작합니다.")
    print()

    result = run_tool_calling_round(question)
    print_round_result(result)


if __name__ == "__main__":
    main()
