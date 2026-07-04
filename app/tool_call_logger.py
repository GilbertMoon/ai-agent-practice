import json
from datetime import datetime
from pathlib import Path
from typing import Any

from argument_validator import sanitize_tool_output
from function_result_response import run_tool_calling_round

LOG_FILE_PATH = Path("outputs/tool_calls.jsonl")

DEFAULT_QUESTIONS = [
    "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
    "GitHub라는 단어가 들어간 제출 기준을 알려주세요.",
    "API Key 보안 정책만 기준으로 설명해 주세요.",
    "Chapter 8 내용을 간단히 요약해 주세요.",
]


def get_current_timestamp() -> str:
    """현재 시각을 ISO 8601 문자열로 반환합니다."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_log_directory() -> None:
    """로그 파일을 저장할 outputs 디렉터리를 생성합니다."""
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_selected_tool(result: dict[str, Any]) -> str | None:
    """Q&A 실행 결과에서 선택된 tool 이름을 가져옵니다."""
    function_call = result.get("function_call")
    if isinstance(function_call, dict):
        return function_call.get("name")

    dispatch_response = result.get("dispatch_response")
    if isinstance(dispatch_response, dict):
        return dispatch_response.get("tool_name")

    return None


def get_arguments(result: dict[str, Any]) -> dict[str, Any]:
    """Q&A 실행 결과에서 function call arguments를 가져옵니다."""
    function_call = result.get("function_call")
    if not isinstance(function_call, dict):
        return {}
    args = function_call.get("args", {})
    if not isinstance(args, dict):
        return {}
    return args


def get_result_count(result: dict[str, Any]) -> int | None:
    """tool 실행 결과에서 검색 결과 개수를 추출합니다."""
    dispatch_response = result.get("dispatch_response")
    if not isinstance(dispatch_response, dict):
        return None
    tool_result = dispatch_response.get("result")
    if not isinstance(tool_result, dict):
        return None
    if "result_count" in tool_result:
        return tool_result["result_count"]
    results = tool_result.get("results")
    if isinstance(results, list):
        return len(results)
    return None


def has_error(result: dict[str, Any]) -> bool:
    """tool 실행 중 오류가 있었는지 확인합니다."""
    dispatch_response = result.get("dispatch_response")
    if dispatch_response is None:
        return False
    if not isinstance(dispatch_response, dict):
        return True
    return not bool(dispatch_response.get("is_success", False))


def get_error_summary(result: dict[str, Any]) -> str | None:
    """tool 실행 오류 정보를 안전하게 요약합니다."""
    dispatch_response = result.get("dispatch_response")
    if not isinstance(dispatch_response, dict):
        return None
    error = dispatch_response.get("error")
    if not error:
        return None
    safe_error = sanitize_tool_output(error)
    return json.dumps(safe_error, ensure_ascii=False)


def build_log_record(result: dict[str, Any]) -> dict[str, Any]:
    """
    Q&A 실행 결과를 로그에 저장할 표준 record로 변환합니다.
    로그에 남기는 항목:
    - timestamp
    - user_question
    - selected_tool
    - arguments
    - result_count
    - error 여부
    """
    arguments = get_arguments(result)
    record = {
        "timestamp": get_current_timestamp(),
        "user_question": result.get("question"),
        "selected_tool": get_selected_tool(result),
        "arguments": sanitize_tool_output(arguments),
        "result_count": get_result_count(result),
        "has_error": has_error(result),
        "error_summary": get_error_summary(result),
    }
    return sanitize_tool_output(record)


def append_log_record(record: dict[str, Any]) -> None:
    """로그 record를 JSON Lines 형식으로 파일에 추가합니다."""
    ensure_log_directory()
    with LOG_FILE_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_question_with_logging(question: str) -> dict[str, Any]:
    """
    질문 하나를 실행하고 tool call 로그를 남깁니다.
    내부 흐름:
    1. run_tool_calling_round()로 Tool Calling Q&A 실행
    2. 실행 결과에서 로그 항목 추출
    3. outputs/tool_calls.jsonl에 JSON Lines 형식으로 저장
    4. 원래 실행 결과 반환
    """
    result = run_tool_calling_round(question)
    log_record = build_log_record(result)
    append_log_record(log_record)
    return result


def read_recent_logs(limit: int = 10) -> list[dict[str, Any]]:
    """최근 tool call 로그를 읽어 옵니다."""
    if not LOG_FILE_PATH.exists():
        return []
    lines = LOG_FILE_PATH.read_text(encoding="utf-8").splitlines()
    recent_lines = lines[-limit:]
    logs = []
    for line in recent_lines:
        if not line.strip():
            continue
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            logs.append(
                {
                    "timestamp": None,
                    "user_question": None,
                    "selected_tool": None,
                    "arguments": {},
                    "result_count": None,
                    "has_error": True,
                    "error_summary": "로그 파일의 JSON 형식이 올바르지 않습니다.",
                }
            )
    return logs


def print_log_record(record: dict[str, Any]) -> None:
    """로그 record 하나를 보기 좋게 출력합니다."""
    print("-" * 80)
    print(f"timestamp    : {record.get('timestamp')}")
    print(f"user_question: {record.get('user_question')}")
    print(f"selected_tool: {record.get('selected_tool')}")
    print(f"arguments    : {json.dumps(record.get('arguments'), ensure_ascii=False)}")
    print(f"result_count : {record.get('result_count')}")
    print(f"has_error    : {record.get('has_error')}")
    if record.get("error_summary"):
        print(f"error_summary: {record.get('error_summary')}")


def print_recent_logs(limit: int = 10) -> None:
    """최근 로그를 출력합니다."""
    logs = read_recent_logs(limit=limit)
    print("=" * 80)
    print(f"최근 Tool Call 로그 {len(logs)}개")
    print("=" * 80)
    if not logs:
        print("저장된 로그가 없습니다.")
        return
    for record in logs:
        print_log_record(record)
    print("-" * 80)


def print_qa_result(result: dict[str, Any]) -> None:
    """Q&A 실행 결과를 간단히 출력합니다."""
    print("=" * 80)
    print("Tool Calling Q&A 실행 결과")
    print("=" * 80)
    print(f"질문: {result.get('question')}")
    print(f"tool 사용 여부: {result.get('used_tool')}")
    print(f"선택된 tool: {get_selected_tool(result)}")
    print(f"result_count: {get_result_count(result)}")
    print(f"error 여부: {has_error(result)}")
    print()
    print("[최종 답변]")
    print(result.get("final_answer") or "최종 답변이 비어 있습니다.")
    print("=" * 80)
    print()


def run_demo_questions() -> None:
    """예제 질문을 실행하고 로그를 남깁니다."""
    for question in DEFAULT_QUESTIONS:
        result = run_question_with_logging(question)
        print_qa_result(result)
    print_recent_logs(limit=10)


def run_interactive_loop() -> None:
    """사용자 질문을 입력받아 실행하고 로그를 남깁니다."""
    print("Tool Call Logger를 시작합니다.")
    print("종료하려면 q 또는 quit를 입력하세요.")
    print()
    while True:
        question = input("질문을 입력하세요: ").strip()
        if question.lower() in {"q", "quit", "exit"}:
            print("Tool Call Logger를 종료합니다.")
            break
        if not question:
            print("질문이 비어 있습니다. 다시 입력해 주세요.")
            continue
        result = run_question_with_logging(question)
        print_qa_result(result)


def main() -> None:
    """
    tool_call_logger.py 실행 진입점입니다.
    실행 전 준비:
    1. .env에 GEMINI_API_KEY 설정
    2. Chapter 7 chunk 인덱싱 완료
    """
    print("실행 모드를 선택하세요.")
    print("1. 예제 질문 실행 후 로그 확인")
    print("2. 직접 질문 입력하며 로그 남기기")
    print("3. 최근 로그만 확인")
    print()
    mode = input("선택 [1]: ").strip()
    if not mode:
        mode = "1"
    if mode == "1":
        run_demo_questions()
    elif mode == "2":
        run_interactive_loop()
    elif mode == "3":
        print_recent_logs(limit=10)
    else:
        print("지원하지 않는 모드입니다. 1, 2, 3 중 하나를 입력하세요.")


if __name__ == "__main__":
    main()
