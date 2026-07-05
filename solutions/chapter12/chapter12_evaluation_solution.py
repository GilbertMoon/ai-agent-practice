"""
Chapter 12 Evaluation Solution

chapter12_multi_agent_solution.py를 여러 sample task로 실행하고 CSV 평가 결과를 생성합니다.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from chapter12_multi_agent_solution import run_multi_agent_workflow


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_CSV = BASE_DIR / "multi_agent_evaluation.csv"

SAMPLE_TASKS: list[dict[str, Any]] = [
    {
        "id": "task_001",
        "title": "학생 안내문 작성",
        "user_request": "이번 주 수업 공지와 과제 조건을 종합해서 학생들에게 보낼 안내문을 작성해 주세요.",
        "expected_agents": ["Planner Agent", "Researcher Agent", "Writer Agent", "Reviewer Agent"],
    },
    {
        "id": "task_002",
        "title": "기말 프로젝트 제출 조건 정리",
        "user_request": "기말 프로젝트 제출 조건을 정리하고, 누락된 내용이 있으면 확인 필요라고 표시해 주세요.",
        "expected_agents": ["Planner Agent", "Researcher Agent", "Writer Agent", "Reviewer Agent"],
    },
    {
        "id": "task_003",
        "title": "평가 기준 포함 안내",
        "user_request": "학생들이 혼동하지 않도록 제출물, 제출 형식, 마감일, 평가 기준을 나누어 안내해 주세요.",
        "expected_agents": ["Planner Agent", "Researcher Agent", "Writer Agent", "Reviewer Agent"],
    },
    {
        "id": "task_004",
        "title": "간단 개념 설명",
        "user_request": "멀티 에이전트가 무엇인지 짧게 설명해 주세요.",
        "expected_agents": ["Planner Agent", "Researcher Agent", "Writer Agent", "Reviewer Agent"],
    },
]


def evaluate_state(task: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """workflow state를 평가 row로 변환합니다."""
    logs = state.get("logs", [])
    expected_agents = set(task.get("expected_agents", []))
    actual_agents = {log.get("agent_name") for log in logs}

    return {
        "task_id": task.get("id"),
        "title": task.get("title"),
        "plan_exists": int(bool(state.get("plan"))),
        "plan_count": len(state.get("plan", [])),
        "research_notes_count": len(state.get("research_notes", [])),
        "draft_exists": int(bool(state.get("draft_answer"))),
        "review_feedback_count": len(state.get("review_feedback", [])),
        "final_answer_exists": int(bool(state.get("final_answer"))),
        "revision_applied": int(int(state.get("revision_count", 0)) > 0),
        "log_count": len(logs),
        "expected_agent_coverage": int(expected_agents.issubset(actual_agents)),
        "error": state.get("error"),
    }


def save_csv(rows: list[dict[str, Any]], path: Path = OUTPUT_CSV) -> None:
    """평가 결과를 CSV 파일로 저장합니다."""
    if not rows:
        return

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """sample task 기반 평가를 실행합니다."""
    rows = []
    for task in SAMPLE_TASKS:
        state = run_multi_agent_workflow(task["user_request"], write_log=False)
        rows.append(evaluate_state(task, state))

    save_csv(rows)

    print("Chapter 12 Multi-Agent Evaluation Solution")
    print(f"total: {len(rows)}")
    print(f"saved: {OUTPUT_CSV}")

    for row in rows:
        print("-" * 70)
        print(f"task_id: {row['task_id']}")
        print(f"title: {row['title']}")
        print(f"plan_count: {row['plan_count']}")
        print(f"research_notes_count: {row['research_notes_count']}")
        print(f"review_feedback_count: {row['review_feedback_count']}")
        print(f"final_answer_exists: {row['final_answer_exists']}")
        print(f"expected_agent_coverage: {row['expected_agent_coverage']}")


if __name__ == "__main__":
    main()
