"""Chapter 10 미니 프로젝트 정답 예시

주제: 상태 기반 수업 공지 Q&A 에이전트 만들기

이 답안은 Chapter 10의 핵심 요구사항을 하나의 정답 파일로 정리한 예시입니다.
기존 solutions 폴더 구조에 맞춰 `solutions/chapter10/` 아래에 배치합니다.

포함 기능:
1. AgentState 정의
2. 사용자 질문 분석
3. route 결정
4. 검색 route에서 tool 실행
5. 검색 결과 평가
6. fallback 처리
7. 답변 생성
8. 실행 로그 저장
9. 평가 CSV 저장
10. 실행 결과 Markdown 리포트 생성

실행:
    python solutions/chapter10/chapter10_state_workflow_mini_project_solution.py

생성 파일:
    outputs/chapter10_state_workflow_logs.jsonl
    outputs/chapter10_state_workflow_evaluation.csv
    outputs/chapter10_state_workflow_report.md
"""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
LOG_PATH = OUTPUT_DIR / "chapter10_state_workflow_logs.jsonl"
EVAL_CSV_PATH = OUTPUT_DIR / "chapter10_state_workflow_evaluation.csv"
REPORT_PATH = OUTPUT_DIR / "chapter10_state_workflow_report.md"
COURSE_POLICY_PATH = DATA_DIR / "course_policy_long.txt"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

try:
    from tool_dispatcher import safe_dispatch_function_call  # type: ignore  # noqa: E402
except Exception:  # pragma: no cover - 실습 환경에 따라 Chapter 9 dispatcher가 없을 수 있음
    safe_dispatch_function_call = None


# -----------------------------------------------------------------------------
# 1. AgentState 정의
# -----------------------------------------------------------------------------


class AgentState(TypedDict, total=False):
    user_question: str
    rewritten_question: str | None
    route: str | None
    route_reason: str | None
    selected_tool: str | None
    tool_arguments: dict[str, Any]
    tool_result: dict[str, Any]
    retrieved_results: list[dict[str, Any]]
    retrieval_status: str | None
    result_count: int
    needs_fallback: bool
    answer: str | None
    error: str | None
    logs: list[dict[str, Any]]


def create_initial_state(user_question: str) -> AgentState:
    """사용자 질문으로 초기 state를 생성합니다."""
    return {
        "user_question": user_question,
        "rewritten_question": None,
        "route": None,
        "route_reason": None,
        "selected_tool": None,
        "tool_arguments": {},
        "tool_result": {},
        "retrieved_results": [],
        "retrieval_status": None,
        "result_count": 0,
        "needs_fallback": False,
        "answer": None,
        "error": None,
        "logs": [],
    }


def summarize_state(state: AgentState) -> dict[str, Any]:
    """출력용으로 state 핵심 필드만 요약합니다."""
    return {
        "user_question": state.get("user_question"),
        "rewritten_question": state.get("rewritten_question"),
        "route": state.get("route"),
        "route_reason": state.get("route_reason"),
        "selected_tool": state.get("selected_tool"),
        "result_count": state.get("result_count"),
        "retrieval_status": state.get("retrieval_status"),
        "needs_fallback": state.get("needs_fallback"),
        "has_answer": bool(state.get("answer")),
        "error": state.get("error"),
        "log_count": len(state.get("logs", [])),
    }


# -----------------------------------------------------------------------------
# 2. Router
# -----------------------------------------------------------------------------


SEARCH_KEYWORDS = [
    "공지",
    "제출",
    "미니 프로젝트",
    "보안",
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
    "에이전트",
    "워크플로우",
    "workflow",
    "agent",
]


def decide_route(question: str) -> tuple[str, str]:
    """질문을 보고 workflow route를 결정합니다."""
    normalized = question.strip()

    if not normalized:
        return "clarification", "질문이 비어 있어 추가 질문이 필요합니다."

    if any(keyword.lower() in normalized.lower() for keyword in SEARCH_KEYWORDS):
        return "search", "수업 공지나 제출 안내 검색이 필요한 질문입니다."

    if any(keyword.lower() in normalized.lower() for keyword in CONCEPT_KEYWORDS):
        return "direct_answer", "일반 개념 설명으로 답변할 수 있는 질문입니다."

    return "direct_answer", "명확한 검색 단서가 없어 일반 답변 경로를 선택했습니다."


def is_search_route(route: str | None) -> bool:
    return route == "search"


def is_direct_answer_route(route: str | None) -> bool:
    return route == "direct_answer"


def is_clarification_route(route: str | None) -> bool:
    return route == "clarification"


# -----------------------------------------------------------------------------
# 3. 검색 도구 실행
# -----------------------------------------------------------------------------


DEFAULT_TOP_K = 3


def read_course_policy() -> str:
    """로컬 샘플 문서를 읽습니다."""
    if not COURSE_POLICY_PATH.exists():
        return ""
    return COURSE_POLICY_PATH.read_text(encoding="utf-8")


def split_sections(document: str) -> list[dict[str, str]]:
    """Markdown 섹션 단위로 문서를 나눕니다."""
    sections: list[dict[str, str]] = []
    current_title = "문서 시작"
    current_lines: list[str] = []

    for line in document.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append(
                    {
                        "section": current_title,
                        "content": "\n".join(current_lines).strip(),
                    }
                )
            current_title = line.replace("## ", "", 1).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append(
            {
                "section": current_title,
                "content": "\n".join(current_lines).strip(),
            }
        )

    return sections


def tokenize(text: str) -> set[str]:
    """간단한 keyword 검색용 token 집합을 만듭니다."""
    tokens = re.findall(r"[A-Za-z0-9가-힣]+", text.lower())
    stopwords = {"은", "는", "이", "가", "을", "를", "에", "에서", "으로", "로", "와", "과", "의", "도", "만", "좀"}
    return {token for token in tokens if token not in stopwords and len(token) >= 2}


def local_search_course_notice(question: str, top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
    """Chapter 9 dispatcher가 없을 때 사용하는 로컬 검색 대체 도구입니다."""
    document = read_course_policy()
    if not document:
        return {
            "error": "data/course_policy_long.txt 파일을 찾지 못했습니다.",
            "results": [],
        }

    query_terms = tokenize(question)
    rows = []

    for index, section in enumerate(split_sections(document), start=1):
        content = section["content"]
        section_terms = tokenize(content)
        score = len(query_terms & section_terms)

        # 자주 나오는 실습 질문에 대한 섹션 힌트 보정
        if "미니" in question or "프로젝트" in question or "결과물" in question:
            if "미니 프로젝트" in section["section"]:
                score += 5
        if "보안" in question or "민감" in question or "api" in question.lower():
            if "API Key 보안" in section["section"]:
                score += 5
        if "github" in question.lower() or "깃허브" in question:
            if "GitHub" in section["section"]:
                score += 5
        if "오류" in question or "에러" in question:
            if "오류 질문" in section["section"]:
                score += 5

        if score > 0:
            rows.append(
                {
                    "content": content,
                    "source": COURSE_POLICY_PATH.name,
                    "section": section["section"],
                    "chunk_id": f"section_{index}",
                    "score": score,
                }
            )

    rows.sort(key=lambda item: item["score"], reverse=True)
    return {
        "tool_name": "local_search_course_notice",
        "results": rows[:top_k],
        "result_count": len(rows[:top_k]),
    }


def normalize_dispatch_result(dispatch_response: dict[str, Any]) -> dict[str, Any]:
    """Chapter 9 dispatcher 응답을 Chapter 10 state 구조에 맞게 정리합니다."""
    if not isinstance(dispatch_response, dict):
        return {"error": "dispatcher 응답 형식이 올바르지 않습니다.", "results": []}

    if not dispatch_response.get("is_success", False):
        return {
            "error": dispatch_response.get("error", "dispatcher 실행 실패"),
            "results": [],
        }

    result = dispatch_response.get("result", {})
    if not isinstance(result, dict):
        return {"error": "dispatcher result 형식이 올바르지 않습니다.", "results": []}

    raw_results = result.get("results", [])
    normalized_results = []

    for item in raw_results:
        normalized_results.append(
            {
                "content": item.get("content") or item.get("text") or item.get("summary") or "",
                "source": item.get("source", "unknown"),
                "section": item.get("section", "unknown"),
                "chunk_id": item.get("chunk_id", "unknown"),
            }
        )

    return {
        "tool_name": dispatch_response.get("tool_name", "search_course_notice"),
        "results": normalized_results,
        "result_count": len(normalized_results),
    }


def run_search_tool(question: str, top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
    """Chapter 9 tool dispatcher를 우선 사용하고, 없으면 로컬 검색으로 대체합니다."""
    if safe_dispatch_function_call is not None:
        function_call = {
            "name": "search_course_policy",
            "args": {
                "question": question,
                "top_k": top_k,
            },
        }
        dispatch_response = safe_dispatch_function_call(function_call)
        normalized = normalize_dispatch_result(dispatch_response)

        if not normalized.get("error"):
            normalized["tool_name"] = "chapter09_dispatcher.search_course_policy"
            return normalized

    return local_search_course_notice(question, top_k=top_k)


# -----------------------------------------------------------------------------
# 4. Workflow Step
# -----------------------------------------------------------------------------


def analyze_question_step(state: AgentState) -> AgentState:
    """사용자 질문을 정리합니다."""
    question = state.get("user_question", "")
    state["rewritten_question"] = question.strip()
    return state


def route_question_step(state: AgentState) -> AgentState:
    """질문을 보고 route를 결정합니다."""
    question = state.get("rewritten_question") or state.get("user_question", "")
    route, reason = decide_route(question)
    state["route"] = route
    state["route_reason"] = reason
    return state


def search_step(state: AgentState) -> AgentState:
    """검색 route인 경우 검색 도구를 실행합니다."""
    if not is_search_route(state.get("route")):
        return state

    question = state.get("rewritten_question") or state.get("user_question", "")
    arguments = {
        "question": question,
        "top_k": DEFAULT_TOP_K,
    }
    tool_result = run_search_tool(question, top_k=DEFAULT_TOP_K)

    state["selected_tool"] = tool_result.get("tool_name", "search_course_notice")
    state["tool_arguments"] = arguments
    state["tool_result"] = tool_result
    state["retrieved_results"] = tool_result.get("results", []) if isinstance(tool_result, dict) else []
    state["result_count"] = len(state["retrieved_results"])
    return state


def evaluate_retrieval_step(state: AgentState) -> AgentState:
    """검색 결과가 충분한지 평가합니다."""
    if not is_search_route(state.get("route")):
        return state

    tool_result = state.get("tool_result", {})

    if isinstance(tool_result, dict) and tool_result.get("error"):
        state["retrieval_status"] = "error"
        state["needs_fallback"] = True
        state["error"] = str(tool_result.get("error"))
        return state

    results = state.get("retrieved_results", [])
    if not results:
        state["retrieval_status"] = "empty"
        state["needs_fallback"] = True
    else:
        state["retrieval_status"] = "ok"
        state["needs_fallback"] = False

    return state


def build_fallback_answer(state: AgentState) -> str:
    """상태에 맞는 fallback 답변을 생성합니다."""
    retrieval_status = state.get("retrieval_status")
    error = state.get("error")

    if retrieval_status == "error":
        return (
            "검색 도구 실행 중 오류가 발생했습니다. "
            "질문을 더 구체적으로 작성하거나 실습 데이터 파일을 확인해 주세요."
            f"\n\n오류 요약: {error}"
        )

    if retrieval_status == "empty":
        return "관련 근거를 찾지 못했습니다. 공지 문서에 포함된 주제인지 확인해 주세요."

    return "현재 질문에 대해 충분한 근거를 찾지 못했습니다. 질문을 더 구체적으로 입력해 주세요."


def fallback_step(state: AgentState) -> AgentState:
    """fallback이 필요한 경우 대체 답변을 저장합니다."""
    if state.get("needs_fallback"):
        state["answer"] = build_fallback_answer(state)
    return state


def generate_answer_from_results(state: AgentState) -> str:
    """검색 결과를 바탕으로 근거 기반 답변을 생성합니다."""
    results = state.get("retrieved_results", [])
    if not results:
        return "관련 근거를 찾지 못했습니다."

    first = results[0]
    content = str(first.get("content", "")).strip().replace("\n", " ")
    source = first.get("source", "unknown")
    section = first.get("section", "unknown")
    chunk_id = first.get("chunk_id", "unknown")

    if len(content) > 450:
        content = content[:450].rstrip() + "..."

    return (
        "검색 결과에 따르면 다음 내용이 가장 관련 있습니다.\n\n"
        f"{content}\n\n"
        f"근거: source={source}, section={section}, chunk_id={chunk_id}"
    )


def generate_direct_answer(question: str) -> str:
    """검색 없이 처리할 수 있는 개념 질문에 답합니다."""
    normalized = question.strip().lower()

    if "rag" in normalized:
        return (
            "RAG는 Retrieval-Augmented Generation의 약자로, "
            "관련 문서를 먼저 검색한 뒤 그 근거를 바탕으로 LLM이 답변을 생성하는 방식입니다."
        )

    if "workflow" in normalized or "워크플로우" in normalized:
        return (
            "에이전트 워크플로우는 질문 분석, 경로 선택, 도구 실행, 결과 평가, 답변 생성처럼 "
            "여러 단계를 순서대로 실행하고 중간 결과를 state에 저장하는 구조입니다."
        )

    if "agent" in normalized or "에이전트" in normalized:
        return "AI 에이전트는 상태를 관리하고 도구를 사용하며 여러 단계를 거쳐 목표를 수행하는 실행 구조입니다."

    return "이 질문은 일반 답변 경로로 처리되었습니다. 공지, 제출, 보안, 오류 관련 질문은 검색 경로로 처리됩니다."


def answer_step(state: AgentState) -> AgentState:
    """route와 검색 결과에 따라 최종 답변을 생성합니다."""
    if state.get("answer"):
        return state

    route = state.get("route")

    if route == "search":
        state["answer"] = generate_answer_from_results(state)
    elif route == "direct_answer":
        state["answer"] = generate_direct_answer(state.get("user_question", ""))
    elif route == "clarification":
        state["answer"] = "질문이 비어 있거나 불명확합니다. 알고 싶은 내용을 한 문장으로 입력해 주세요."
    else:
        state["answer"] = "처리 경로를 결정하지 못했습니다. 질문을 다시 입력해 주세요."

    return state


# -----------------------------------------------------------------------------
# 5. 로그와 실행 함수
# -----------------------------------------------------------------------------


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_value(value: Any) -> Any:
    """로그에 민감정보가 들어가지 않도록 간단히 마스킹합니다."""
    patterns = [r"(?i)api[_-]?key", r"(?i)secret", r"(?i)token", r"(?i)password", r"(?i)gemini_api_key"]

    if isinstance(value, str):
        sanitized = value
        for pattern in patterns:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized)
        return sanitized

    if isinstance(value, list):
        return [sanitize_value(item) for item in value]

    if isinstance(value, dict):
        return {sanitize_value(str(key)): sanitize_value(item) for key, item in value.items()}

    return value


def log_step(state: AgentState, step_name: str, write_file: bool = True) -> AgentState:
    """step 실행 로그를 state와 JSON Lines 파일에 기록합니다."""
    record = sanitize_value(
        {
            "timestamp": now_iso(),
            "step_name": step_name,
            "route": state.get("route"),
            "selected_tool": state.get("selected_tool"),
            "result_count": state.get("result_count"),
            "retrieval_status": state.get("retrieval_status"),
            "needs_fallback": state.get("needs_fallback"),
            "error": state.get("error"),
        }
    )

    logs = state.setdefault("logs", [])
    logs.append(record)

    if write_file:
        ensure_output_dir()
        with LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return state


def run_conditional_workflow(user_question: str, write_log: bool = True) -> AgentState:
    """조건 분기 기반 workflow를 실행합니다."""
    state = create_initial_state(user_question)

    state = analyze_question_step(state)
    log_step(state, "analyze_question_step", write_file=write_log)

    state = route_question_step(state)
    log_step(state, "route_question_step", write_file=write_log)

    route = state.get("route")

    if is_search_route(route):
        state = search_step(state)
        log_step(state, "search_step", write_file=write_log)

        state = evaluate_retrieval_step(state)
        log_step(state, "evaluate_retrieval_step", write_file=write_log)

        if state.get("needs_fallback"):
            state = fallback_step(state)
            log_step(state, "fallback_step", write_file=write_log)
        else:
            state = answer_step(state)
            log_step(state, "answer_step", write_file=write_log)

    elif is_direct_answer_route(route):
        state = answer_step(state)
        log_step(state, "direct_answer_step", write_file=write_log)

    elif is_clarification_route(route):
        state = answer_step(state)
        log_step(state, "clarification_step", write_file=write_log)

    return state


# -----------------------------------------------------------------------------
# 6. 평가와 리포트
# -----------------------------------------------------------------------------


SAMPLE_QUESTIONS = [
    {
        "id": "q01",
        "question": "미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?",
        "expected_route": "search",
    },
    {
        "id": "q02",
        "question": "보안 안내에서 민감 정보 저장 방법을 알려줘.",
        "expected_route": "search",
    },
    {
        "id": "q03",
        "question": "GitHub라는 단어가 포함된 안내를 찾아줘.",
        "expected_route": "search",
    },
    {
        "id": "q04",
        "question": "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
        "expected_route": "search",
    },
    {
        "id": "q05",
        "question": "RAG가 무엇인가요?",
        "expected_route": "direct_answer",
    },
]


def evaluate_question(item: dict[str, Any]) -> dict[str, Any]:
    """질문 1개에 대해 workflow 실행 결과를 평가합니다."""
    state = run_conditional_workflow(item["question"], write_log=False)
    expected_route = item.get("expected_route")
    actual_route = state.get("route")

    return {
        "id": item.get("id"),
        "question": item.get("question"),
        "expected_route": expected_route,
        "actual_route": actual_route,
        "route_correct": int(expected_route == actual_route),
        "selected_tool": state.get("selected_tool"),
        "result_count": state.get("result_count", 0),
        "retrieval_status": state.get("retrieval_status"),
        "needs_fallback": state.get("needs_fallback", False),
        "has_answer": int(bool(state.get("answer"))),
        "error": state.get("error"),
    }


def save_evaluation_csv(rows: list[dict[str, Any]]) -> None:
    """평가 결과를 CSV 파일로 저장합니다."""
    if not rows:
        return

    ensure_output_dir()
    fieldnames = list(rows[0].keys())

    with EVAL_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_report(states: list[AgentState], evaluation_rows: list[dict[str, Any]]) -> str:
    """실행 결과 Markdown 리포트를 생성합니다."""
    total = len(evaluation_rows)
    correct = sum(row["route_correct"] for row in evaluation_rows)

    lines = [
        "# Chapter 10 상태 기반 워크플로우 미니 프로젝트 실행 결과",
        "",
        f"- 실행 시각: {now_iso()}",
        f"- 평가 문항 수: {total}",
        f"- route 정답 수: {correct}/{total}",
        f"- 로그 파일: `{LOG_PATH.relative_to(PROJECT_ROOT)}`",
        f"- 평가 CSV: `{EVAL_CSV_PATH.relative_to(PROJECT_ROOT)}`",
        "",
        "## 질문별 결과",
        "",
    ]

    for index, state in enumerate(states, start=1):
        lines.extend(
            [
                f"### {index}. {state.get('user_question')}",
                "",
                f"- route: `{state.get('route')}`",
                f"- selected_tool: `{state.get('selected_tool')}`",
                f"- result_count: `{state.get('result_count')}`",
                f"- retrieval_status: `{state.get('retrieval_status')}`",
                f"- needs_fallback: `{state.get('needs_fallback')}`",
                "",
                "답변:",
                "",
                str(state.get("answer", "")),
                "",
            ]
        )

    return "\n".join(lines)


def save_report(states: list[AgentState], evaluation_rows: list[dict[str, Any]]) -> None:
    ensure_output_dir()
    REPORT_PATH.write_text(build_report(states, evaluation_rows), encoding="utf-8")


def run_demo() -> None:
    """미니 프로젝트 기본 질문을 실행하고 로그, 평가 CSV, 리포트를 저장합니다."""
    ensure_output_dir()

    if LOG_PATH.exists():
        LOG_PATH.unlink()

    states = []
    for item in SAMPLE_QUESTIONS:
        state = run_conditional_workflow(item["question"], write_log=True)
        states.append(state)

    evaluation_rows = [evaluate_question(item) for item in SAMPLE_QUESTIONS]
    save_evaluation_csv(evaluation_rows)
    save_report(states, evaluation_rows)

    print("Chapter 10 State Workflow Mini Project")
    print(f"questions: {len(SAMPLE_QUESTIONS)}")
    print(f"log: {LOG_PATH.relative_to(PROJECT_ROOT)}")
    print(f"evaluation: {EVAL_CSV_PATH.relative_to(PROJECT_ROOT)}")
    print(f"report: {REPORT_PATH.relative_to(PROJECT_ROOT)}")
    print()

    for state in states:
        print("-" * 80)
        print(json.dumps(summarize_state(state), ensure_ascii=False, indent=2))
        print("답변:")
        print(state.get("answer"))


if __name__ == "__main__":
    run_demo()
