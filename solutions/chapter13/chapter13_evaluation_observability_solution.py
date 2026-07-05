"""Chapter 13 미니 프로젝트 정답 예시

멀티 에이전트 실행 결과 평가·관찰성 리포트 만들기 예시입니다.
프로젝트 루트에서 다음 명령으로 실행할 수 있습니다.

    python solutions/chapter13/chapter13_evaluation_observability_solution.py

생성 파일:
    outputs/chapter13/agent_runs.jsonl
    outputs/chapter13/evaluation_results.csv
    outputs/chapter13/evaluation_report.md

특징:
- 외부 LLM API를 호출하지 않습니다.
- Python 표준 라이브러리만 사용합니다.
- Chapter 12의 멀티 에이전트 실행 결과와 유사한 state를 시뮬레이션합니다.
"""

from __future__ import annotations

import csv
import json
import re
import time
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "chapter13"
LOG_PATH = OUTPUT_DIR / "agent_runs.jsonl"
RESULT_CSV_PATH = OUTPUT_DIR / "evaluation_results.csv"
REPORT_PATH = OUTPUT_DIR / "evaluation_report.md"

MAX_TOTAL_SCORE = 25
FAIL_SCORE_THRESHOLD = 18

SAMPLE_TASKS = [
    {
        "id": "eval_001",
        "title": "수업 공지 안내문 평가",
        "user_request": "수업 공지와 과제 조건을 종합해 학생 안내문을 작성해 주세요.",
        "required_sections": ["제출 항목", "제출 형식", "마감일", "평가 기준"],
        "expected_keywords": ["확인 필요", "학생", "제출"],
    },
    {
        "id": "eval_002",
        "title": "기말 프로젝트 조건 정리 평가",
        "user_request": "기말 프로젝트 제출 조건을 정리하고 누락된 내용은 확인 필요라고 표시해 주세요.",
        "required_sections": ["제출 항목", "제출 형식", "마감일", "평가 기준"],
        "expected_keywords": ["기말 프로젝트", "확인 필요", "제출"],
    },
    {
        "id": "eval_003",
        "title": "짧은 개념 설명 평가",
        "user_request": "멀티 에이전트가 무엇인지 짧게 설명해 주세요.",
        "required_sections": ["개념", "예시"],
        "expected_keywords": ["역할", "협업", "에이전트"],
    },
]

FAILURE_TYPES = {
    "none": "실패 없음",
    "planning_error": "Planner가 필요한 작업 계획을 만들지 못함",
    "retrieval_error": "Researcher가 필요한 근거를 충분히 찾지 못함",
    "writing_error": "Writer가 최종 답변을 만들지 못했거나 형식이 부족함",
    "review_error": "Reviewer feedback이 없거나 의미 있는 검토가 부족함",
    "safety_error": "최종 답변에 민감정보 또는 위험한 내용이 포함됨",
    "runtime_error": "실행 중 예외 또는 시스템 오류가 발생함",
    "quality_regression": "점수 기준을 충족하지 못함",
}

SENSITIVE_PATTERNS = [
    r"api[_-]?key\s*=",
    r"secret\s*=",
    r"token\s*=",
    r"password\s*=",
    r"sk-[A-Za-z0-9_-]{10,}",
]


# -----------------------------------------------------------------------------
# Trace log
# -----------------------------------------------------------------------------


def now_iso() -> str:
    """현재 시각을 ISO 문자열로 반환합니다."""
    return datetime.now().isoformat(timespec="seconds")


def generate_trace_id(prefix: str = "run") -> str:
    """한 번의 실행을 구분하기 위한 trace_id를 생성합니다."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"{prefix}_{timestamp}_{suffix}"


def make_log_event(
    trace_id: str,
    step: str,
    agent_name: str,
    status: str,
    latency_ms: int,
    input_keys: list[str],
    output_keys: list[str],
    message: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """JSONL로 저장할 로그 이벤트를 생성합니다."""
    return {
        "timestamp": now_iso(),
        "trace_id": trace_id,
        "step": step,
        "agent_name": agent_name,
        "status": status,
        "latency_ms": latency_ms,
        "input_keys": input_keys,
        "output_keys": output_keys,
        "message": message,
        "extra": extra or {},
    }


def write_log_event(event: dict[str, Any]) -> None:
    """로그 이벤트를 JSONL 파일에 한 줄로 추가합니다."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def run_logged_step(
    state: dict[str, Any],
    step: str,
    agent_name: str,
    func: Callable[[dict[str, Any]], dict[str, Any]],
    input_keys: list[str],
    output_keys: list[str],
) -> dict[str, Any]:
    """함수 실행 시간을 측정하고 성공 또는 실패 로그를 남깁니다."""
    start = time.perf_counter()
    trace_id = state["trace_id"]

    try:
        state = func(state)
        latency_ms = int((time.perf_counter() - start) * 1000)
        event = make_log_event(
            trace_id=trace_id,
            step=step,
            agent_name=agent_name,
            status="success",
            latency_ms=latency_ms,
            input_keys=input_keys,
            output_keys=output_keys,
            message=f"{agent_name} 실행 완료",
        )
        state.setdefault("logs", []).append(event)
        write_log_event(event)
        return state
    except Exception as error:
        latency_ms = int((time.perf_counter() - start) * 1000)
        event = make_log_event(
            trace_id=trace_id,
            step=step,
            agent_name=agent_name,
            status="failed",
            latency_ms=latency_ms,
            input_keys=input_keys,
            output_keys=output_keys,
            message=str(error),
            extra={"error_type": type(error).__name__},
        )
        state.setdefault("logs", []).append(event)
        state["error"] = str(error)
        write_log_event(event)
        return state


# -----------------------------------------------------------------------------
# Simulated multi-agent workflow
# -----------------------------------------------------------------------------


def planner_agent(state: dict[str, Any]) -> dict[str, Any]:
    """사용자 요청을 작업 계획으로 분해합니다."""
    user_request = state.get("user_request", "")
    plan = ["요청 의도 파악", "필요 정보 정리", "초안 작성", "검토", "최종 답변 확정"]

    if "공지" in user_request or "과제" in user_request or "프로젝트" in user_request:
        plan.insert(1, "제출 항목, 제출 형식, 마감일, 평가 기준 확인")

    if "짧게" in user_request:
        plan.append("답변을 간결하게 유지")

    state["plan"] = list(dict.fromkeys(plan))
    return state


def researcher_agent(state: dict[str, Any]) -> dict[str, Any]:
    """요청 처리에 필요한 근거와 확인 항목을 정리합니다."""
    user_request = state.get("user_request", "")
    notes = []

    if "프로젝트" in user_request:
        notes.extend([
            "기말 프로젝트 제출 항목은 구현 결과물과 발표 자료입니다.",
            "마감일과 세부 제출 방식은 확인 필요로 표시합니다.",
            "평가 기준은 완성도, 설명력, 수업 기술 활용도로 나눌 수 있습니다.",
        ])
    elif "멀티 에이전트" in user_request:
        notes.extend([
            "멀티 에이전트는 여러 역할의 에이전트가 협업하는 구조입니다.",
            "예시는 Planner, Researcher, Writer, Reviewer 역할 분담입니다.",
        ])
    else:
        notes.extend([
            "학생 안내문에는 제출 항목, 제출 형식, 마감일, 평가 기준이 포함되어야 합니다.",
            "확정되지 않은 내용은 확인 필요라고 표시합니다.",
            "학생이 바로 이해할 수 있도록 항목별로 정리합니다.",
        ])

    state["research_notes"] = notes
    return state


def writer_agent(state: dict[str, Any]) -> dict[str, Any]:
    """research_notes를 바탕으로 답변 초안을 작성합니다."""
    user_request = state.get("user_request", "")

    if "멀티 에이전트" in user_request:
        draft = (
            "개념: 멀티 에이전트는 하나의 작업을 여러 역할의 에이전트가 나누어 처리하는 구조입니다.\n"
            "예시: Planner가 계획을 만들고, Researcher가 정보를 정리하며, Writer가 답변을 작성하고, "
            "Reviewer가 품질을 점검합니다."
        )
    else:
        draft = (
            "학생 안내문\n"
            "- 제출 항목: 과제 또는 프로젝트 결과물\n"
            "- 제출 형식: ipynb, pdf, ppt 등 수업에서 지정한 형식\n"
            "- 마감일: 확인 필요\n"
            "- 평가 기준: 완성도, 요구사항 충족도, 설명력\n"
            "- 확인 필요: 세부 파일명과 제출 채널"
        )

    state["draft_answer"] = draft
    return state


def reviewer_agent(state: dict[str, Any]) -> dict[str, Any]:
    """초안의 누락 항목과 개선점을 검토합니다."""
    draft = state.get("draft_answer", "")
    task = state.get("task", {})
    feedback = []

    for section in task.get("required_sections", []):
        if section not in draft:
            feedback.append(f"'{section}' 항목이 명확하지 않습니다.")

    for keyword in task.get("expected_keywords", []):
        if keyword not in draft:
            feedback.append(f"'{keyword}' 키워드가 포함되지 않았습니다.")

    if not feedback:
        feedback.append("초안이 요구사항을 충족합니다.")

    state["review_feedback"] = feedback
    return state


def revise_answer(state: dict[str, Any]) -> dict[str, Any]:
    """review feedback을 반영해 최종 답변을 보강합니다."""
    draft = state.get("draft_answer", "")
    feedback = state.get("review_feedback", [])

    actionable_feedback = [item for item in feedback if "충족합니다" not in item]
    if not actionable_feedback:
        state["final_answer"] = draft
        state["revision_count"] = 0
        return state

    revision_note = "\n\n보완 사항\n" + "\n".join(f"- {item}" for item in actionable_feedback)
    state["final_answer"] = draft + revision_note
    state["revision_count"] = 1
    return state


def run_simulated_workflow(task: dict[str, Any]) -> dict[str, Any]:
    """Chapter 12 workflow와 유사한 실행 state를 생성합니다."""
    state = {
        "trace_id": generate_trace_id(),
        "task": task,
        "task_id": task["id"],
        "user_request": task["user_request"],
        "logs": [],
        "error": None,
    }

    state = run_logged_step(state, "planner", "Planner Agent", planner_agent, ["user_request"], ["plan"])
    state = run_logged_step(state, "researcher", "Researcher Agent", researcher_agent, ["user_request", "plan"], ["research_notes"])
    state = run_logged_step(state, "writer", "Writer Agent", writer_agent, ["research_notes"], ["draft_answer"])
    state = run_logged_step(state, "reviewer", "Reviewer Agent", reviewer_agent, ["draft_answer"], ["review_feedback"])
    state = run_logged_step(state, "revision", "Writer Agent", revise_answer, ["draft_answer", "review_feedback"], ["final_answer"])

    return state


# -----------------------------------------------------------------------------
# Rule-based evaluation
# -----------------------------------------------------------------------------


def clamp_score(value: float, min_score: int = 0, max_score: int = 5) -> int:
    """점수를 0~5 사이 정수로 보정합니다."""
    return max(min_score, min(max_score, round(value)))


def score_to_percent(score: int, max_score: int = MAX_TOTAL_SCORE) -> float:
    """점수를 백분율로 변환합니다."""
    return round((score / max_score) * 100, 2) if max_score else 0.0


def has_sensitive_content(text: str) -> bool:
    """민감정보로 보이는 문자열이 포함되어 있는지 검사합니다."""
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in SENSITIVE_PATTERNS)


def count_keyword_matches(text: str, keywords: list[str]) -> int:
    """답변에 포함된 기대 키워드 수를 계산합니다."""
    return sum(1 for keyword in keywords if keyword and keyword in text)


def check_required_sections(final_answer: str, required_sections: list[str]) -> dict[str, bool]:
    """필수 섹션 포함 여부를 검사합니다."""
    return {section: section in final_answer for section in required_sections}


def evaluate_state(state: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    """최종 답변과 중간 과정을 규칙 기반으로 평가합니다."""
    final_answer = state.get("final_answer", "")
    research_notes = state.get("research_notes", [])
    required_sections = task.get("required_sections", [])
    expected_keywords = task.get("expected_keywords", [])

    section_checks = check_required_sections(final_answer, required_sections)
    matched_keyword_count = count_keyword_matches(final_answer, expected_keywords)

    request_fulfillment = clamp_score((matched_keyword_count / len(expected_keywords)) * 5) if expected_keywords else 3
    groundedness = 5 if research_notes and any(note.split()[0] in final_answer for note in research_notes if note.split()) else 3
    completeness = sum(
        1
        for value in [
            state.get("plan"),
            state.get("research_notes"),
            state.get("draft_answer"),
            state.get("review_feedback"),
            state.get("final_answer"),
        ]
        if value
    )
    clarity = 5 if "\n" in final_answer and len(final_answer) <= 1200 else 3
    safety = 0 if has_sensitive_content(final_answer) else 5
    total_score = request_fulfillment + groundedness + completeness + clarity + safety

    row = {
        "task_id": task["id"],
        "title": task.get("title", ""),
        "trace_id": state["trace_id"],
        "has_final_answer": bool(final_answer),
        "required_section_score": sum(1 for passed in section_checks.values() if passed),
        "required_section_total": len(required_sections),
        "matched_keyword_count": matched_keyword_count,
        "expected_keyword_count": len(expected_keywords),
        "plan_exists": bool(state.get("plan")),
        "plan_count": len(state.get("plan", [])),
        "research_notes_count": len(research_notes),
        "draft_answer_exists": bool(state.get("draft_answer")),
        "review_feedback_count": len(state.get("review_feedback", [])),
        "revision_count": int(state.get("revision_count", 0)),
        "log_count": len(state.get("logs", [])),
        "runtime_error": state.get("error") or "",
        "has_sensitive_content": has_sensitive_content(final_answer),
        "request_fulfillment": request_fulfillment,
        "groundedness": groundedness,
        "completeness": completeness,
        "clarity": clarity,
        "safety": safety,
        "rubric_total_score": total_score,
        "rubric_percent": score_to_percent(total_score),
    }
    row["failure_type"] = classify_failure(row)
    row["failure_reason"] = describe_failure(row["failure_type"])
    row["status"] = "success" if row["failure_type"] == "none" else "failed"
    return row


# -----------------------------------------------------------------------------
# Failure classification and metrics
# -----------------------------------------------------------------------------


def classify_failure(row: dict[str, Any]) -> str:
    """평가 row를 실패 유형으로 분류합니다."""
    if row.get("runtime_error"):
        return "runtime_error"
    if row.get("has_sensitive_content"):
        return "safety_error"
    if not row.get("plan_exists"):
        return "planning_error"
    if int(row.get("research_notes_count", 0)) == 0:
        return "retrieval_error"
    if not row.get("has_final_answer"):
        return "writing_error"
    if int(row.get("review_feedback_count", 0)) == 0:
        return "review_error"
    if int(row.get("rubric_total_score", 0)) < FAIL_SCORE_THRESHOLD:
        return "quality_regression"
    return "none"


def describe_failure(failure_type: str) -> str:
    """실패 유형 설명을 반환합니다."""
    return FAILURE_TYPES.get(failure_type, "알 수 없는 실패 유형")


def summarize_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """평가 결과 전체를 운영 지표로 요약합니다."""
    total = len(rows)
    success_count = sum(1 for row in rows if row["status"] == "success")
    average_score = round(sum(row["rubric_total_score"] for row in rows) / total, 2) if total else 0
    average_latency = round(sum(read_trace_latency(row["trace_id"]) for row in rows) / total, 2) if total else 0
    failure_counts = Counter(row["failure_type"] for row in rows)

    return {
        "total_tasks": total,
        "success_count": success_count,
        "failed_count": total - success_count,
        "success_rate": round((success_count / total) * 100, 2) if total else 0,
        "average_score": average_score,
        "average_latency_ms": average_latency,
        "failure_counts": dict(failure_counts),
    }


def read_trace_latency(trace_id: str) -> int:
    """특정 trace_id에 해당하는 로그의 latency 합계를 계산합니다."""
    if not LOG_PATH.exists():
        return 0

    total_latency = 0
    with LOG_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            event = json.loads(line)
            if event.get("trace_id") == trace_id:
                total_latency += int(event.get("latency_ms", 0))
    return total_latency


# -----------------------------------------------------------------------------
# Save outputs
# -----------------------------------------------------------------------------


def reset_outputs() -> None:
    """이전 실행 결과를 정리합니다."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in [LOG_PATH, RESULT_CSV_PATH, REPORT_PATH]:
        if path.exists():
            path.unlink()


def save_csv(rows: list[dict[str, Any]]) -> None:
    """평가 결과를 CSV로 저장합니다."""
    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with RESULT_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_report(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> str:
    """Markdown 평가 리포트를 생성합니다."""
    lines = [
        "# Chapter 13 Evaluation Report",
        "",
        "## 1. Summary",
        "",
        f"- Total tasks: {metrics['total_tasks']}",
        f"- Success count: {metrics['success_count']}",
        f"- Failed count: {metrics['failed_count']}",
        f"- Success rate: {metrics['success_rate']}%",
        f"- Average score: {metrics['average_score']} / {MAX_TOTAL_SCORE}",
        f"- Average latency: {metrics['average_latency_ms']} ms",
        "",
        "## 2. Failure Types",
        "",
    ]

    for failure_type, count in metrics["failure_counts"].items():
        lines.append(f"- {failure_type}: {count} ({describe_failure(failure_type)})")

    lines.extend([
        "",
        "## 3. Task Results",
        "",
        "| task_id | title | status | score | failure_type | trace_id |",
        "| --- | --- | --- | ---: | --- | --- |",
    ])

    for row in rows:
        lines.append(
            f"| {row['task_id']} | {row['title']} | {row['status']} | "
            f"{row['rubric_total_score']} | {row['failure_type']} | {row['trace_id']} |"
        )

    lines.extend([
        "",
        "## 4. Improvement Notes",
        "",
        "- `quality_regression`이 발생한 task는 expected_keywords와 required_sections를 먼저 확인합니다.",
        "- `retrieval_error`가 많으면 Researcher Agent의 근거 수집 규칙을 보강합니다.",
        "- `review_error`가 많으면 Reviewer Agent의 체크리스트를 더 구체화합니다.",
        "- `agent_runs.jsonl`에서 같은 trace_id를 검색하면 한 번의 실행 흐름을 추적할 수 있습니다.",
    ])

    return "\n".join(lines)


def save_report(report: str) -> None:
    """Markdown 리포트를 저장합니다."""
    REPORT_PATH.write_text(report, encoding="utf-8")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def run_regression_evaluation(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """sample tasks 기반 회귀 평가를 실행합니다."""
    rows = []
    for task in tasks:
        state = run_simulated_workflow(task)
        rows.append(evaluate_state(state, task))
    return rows


def main() -> None:
    """Chapter 13 미니 프로젝트 정답 예시를 실행합니다."""
    reset_outputs()
    rows = run_regression_evaluation(SAMPLE_TASKS)
    metrics = summarize_metrics(rows)
    report = generate_report(rows, metrics)

    save_csv(rows)
    save_report(report)

    print("Chapter 13 Evaluation & Observability Solution")
    print(f"tasks: {len(rows)}")
    print(f"success_rate: {metrics['success_rate']}%")
    print(f"saved log: {LOG_PATH.relative_to(PROJECT_ROOT)}")
    print(f"saved csv: {RESULT_CSV_PATH.relative_to(PROJECT_ROOT)}")
    print(f"saved report: {REPORT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
