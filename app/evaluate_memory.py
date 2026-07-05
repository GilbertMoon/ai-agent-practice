"""
Chapter 11 Memory Evaluation

대화형 에이전트의 memory 사용 여부를 간단한 기준으로 평가합니다.
"""

import csv
import json
from pathlib import Path
from typing import Any, TypedDict, cast

try:
    from .context_builder import build_recent_context
    from .memory_retriever import retrieve_memory
    from .memory_safety import is_safe_memory
    from .memory_updater import should_create_memory
except ImportError:
    from context_builder import build_recent_context
    from memory_retriever import retrieve_memory
    from memory_safety import is_safe_memory
    from memory_updater import should_create_memory


DATA_FILE = Path("data") / "sample_conversations.json"
OUTPUT_FILE = Path("outputs") / "memory_evaluation.csv"


class EvaluationMessage(TypedDict):
    role: str
    content: str


class EvaluationCase(TypedDict, total=False):
    id: str
    messages: list[EvaluationMessage]
    expected_memory_use: bool
    expected_sensitive_block: bool


class EvaluationResult(TypedDict):
    conversation_id: str
    used_recent_context: bool
    retrieved_memory_count: int
    saved_memory_count: int
    blocked_sensitive_memory: bool
    has_answer: bool
    passed: bool


SAMPLE_EVALUATION_DATA: list[EvaluationCase] = [
    {
        "id": "conv_001",
        "messages": [
            {"role": "user", "content": "미니 프로젝트 결과물을 알려 주세요."},
            {"role": "assistant", "content": "보고서와 코드가 필요합니다."},
            {"role": "user", "content": "그럼 제출 형식도 알려 주세요."},
        ],
        "expected_memory_use": True,
        "expected_sensitive_block": False,
    },
    {
        "id": "conv_002",
        "messages": [
            {"role": "user", "content": "앞으로 답변은 짧게 해 주세요. 이 선호를 기억해 주세요."},
            {"role": "assistant", "content": "네, 짧고 핵심 위주로 답변하겠습니다."},
        ],
        "expected_memory_use": True,
        "expected_sensitive_block": False,
    },
    {
        "id": "conv_003",
        "messages": [
            {"role": "user", "content": "내 API Key는 abc123입니다."},
            {"role": "assistant", "content": "민감정보는 저장하지 않는 것이 좋습니다."},
        ],
        "expected_memory_use": False,
        "expected_sensitive_block": True,
    },
]


SAMPLE_MEMORIES: list[dict[str, Any]] = [
    {
        "id": "mem_001",
        "category": "project_state",
        "content": "사용자는 Chapter 11 원고 초안 작성을 진행 중이다.",
        "source": "manual",
        "created_at": "2026-07-05T18:00:00",
        "updated_at": "2026-07-05T18:00:00",
        "importance": 3,
    },
    {
        "id": "mem_002",
        "category": "user_preference",
        "content": "사용자는 짧고 실행 중심의 설명을 선호한다.",
        "source": "manual",
        "created_at": "2026-07-05T18:00:00",
        "updated_at": "2026-07-05T18:00:00",
        "importance": 4,
    },
    {
        "id": "mem_003",
        "category": "course_context",
        "content": "미니 프로젝트 제출물은 PDF 보고서와 소스 코드 폴더를 포함한다.",
        "source": "manual",
        "created_at": "2026-07-05T18:00:00",
        "updated_at": "2026-07-05T18:00:00",
        "importance": 4,
    },
]


def ensure_output_dir() -> None:
    """평가 결과를 저장할 outputs 폴더를 생성합니다."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_evaluation_data(path: Path = DATA_FILE) -> list[EvaluationCase]:
    """평가 데이터를 JSON 파일에서 읽습니다.

    파일이 없으면 실습용 샘플 데이터를 사용합니다.
    """
    if not path.exists():
        return SAMPLE_EVALUATION_DATA

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        return SAMPLE_EVALUATION_DATA

    return cast(list[EvaluationCase], data)


def get_last_user_message(messages: list[EvaluationMessage]) -> str:
    """대화 목록에서 마지막 user 메시지를 반환합니다."""
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")

    return ""


def get_last_assistant_message(messages: list[EvaluationMessage]) -> str:
    """대화 목록에서 마지막 assistant 메시지를 반환합니다."""
    for message in reversed(messages):
        if message.get("role") == "assistant":
            return message.get("content", "")

    return ""


def create_answer(user_question: str, recent_context: str, retrieved_memory_count: int) -> str:
    """평가용 더미 답변을 생성합니다.

    실제 평가에서는 이 부분을 LLM 답변 생성 결과로 교체할 수 있습니다.
    """
    if not user_question.strip():
        return ""

    if retrieved_memory_count > 0:
        return f"관련 메모리를 참고해 답변합니다: {user_question}"

    if recent_context:
        return f"최근 대화 맥락을 참고해 답변합니다: {user_question}"

    return f"질문을 확인했습니다: {user_question}"


def count_saved_memory_candidates(messages: list[EvaluationMessage]) -> int:
    """대화에서 장기 메모리로 저장될 후보 수를 계산합니다."""
    saved_count = 0

    for index in range(len(messages) - 1):
        current_message = messages[index]
        next_message = messages[index + 1]

        if current_message.get("role") != "user":
            continue

        if next_message.get("role") != "assistant":
            continue

        user_message = current_message.get("content", "")
        assistant_message = next_message.get("content", "")

        if should_create_memory(user_message, assistant_message):
            saved_count += 1

    return saved_count


def has_blocked_sensitive_memory(messages: list[EvaluationMessage]) -> bool:
    """민감정보 후보가 안전 검사에서 차단되었는지 확인합니다."""
    for message in messages:
        content = message.get("content", "")

        if content and not is_safe_memory(content):
            return True

    return False


def evaluate_case(evaluation_case: EvaluationCase) -> EvaluationResult:
    """단일 평가 케이스를 실행하고 결과를 반환합니다."""
    conversation_id = evaluation_case.get("id", "unknown")
    messages = evaluation_case.get("messages", [])
    expected_memory_use = evaluation_case.get("expected_memory_use", False)
    expected_sensitive_block = evaluation_case.get("expected_sensitive_block", False)

    user_question = get_last_user_message(messages)
    recent_context = build_recent_context(cast(Any, messages), limit=4)
    retrieved_memories = retrieve_memory(
        query=user_question,
        memories=cast(Any, SAMPLE_MEMORIES),
        top_k=3,
    )
    saved_memory_count = count_saved_memory_candidates(messages)
    blocked_sensitive_memory = has_blocked_sensitive_memory(messages)
    answer = create_answer(
        user_question=user_question,
        recent_context=recent_context,
        retrieved_memory_count=len(retrieved_memories),
    )

    used_recent_context = bool(recent_context)
    has_answer = bool(answer.strip())

    passed = True

    if expected_memory_use and saved_memory_count == 0 and len(retrieved_memories) == 0:
        passed = False

    if expected_sensitive_block and not blocked_sensitive_memory:
        passed = False

    if not has_answer:
        passed = False

    return {
        "conversation_id": conversation_id,
        "used_recent_context": used_recent_context,
        "retrieved_memory_count": len(retrieved_memories),
        "saved_memory_count": saved_memory_count,
        "blocked_sensitive_memory": blocked_sensitive_memory,
        "has_answer": has_answer,
        "passed": passed,
    }


def evaluate_all(cases: list[EvaluationCase]) -> list[EvaluationResult]:
    """전체 평가 케이스를 실행합니다."""
    return [evaluate_case(evaluation_case) for evaluation_case in cases]


def save_results(results: list[EvaluationResult], path: Path = OUTPUT_FILE) -> None:
    """평가 결과를 CSV 파일로 저장합니다."""
    ensure_output_dir()

    fieldnames = [
        "conversation_id",
        "used_recent_context",
        "retrieved_memory_count",
        "saved_memory_count",
        "blocked_sensitive_memory",
        "has_answer",
        "passed",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def print_results(results: list[EvaluationResult]) -> None:
    """평가 결과를 화면에 출력합니다."""
    print("[memory evaluation results]")

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"{result['conversation_id']}: {status} "
            f"recent_context={result['used_recent_context']}, "
            f"retrieved={result['retrieved_memory_count']}, "
            f"saved={result['saved_memory_count']}, "
            f"blocked_sensitive={result['blocked_sensitive_memory']}, "
            f"has_answer={result['has_answer']}"
        )

    passed_count = sum(1 for result in results if result["passed"])
    total_count = len(results)
    print(f"\npassed: {passed_count}/{total_count}")
    print(f"saved to: {OUTPUT_FILE}")


def main() -> None:
    """memory 평가를 실행합니다."""
    cases = load_evaluation_data()
    results = evaluate_all(cases)
    save_results(results)
    print_results(results)


if __name__ == "__main__":
    main()