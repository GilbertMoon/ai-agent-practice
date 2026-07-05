"""
Chapter 12 Multi-Agent Evaluation

sample_tasks.json을 기준으로 멀티 에이전트 협업 결과와 중간 산출물을 평가합니다.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from multi_agent_workflow import run_multi_agent_workflow


DEFAULT_SAMPLE_PATH = Path("data/sample_tasks.json")
DEFAULT_OUTPUT_CSV = "multi_agent_evaluation.csv"


def load_output_csv_path() -> Path:
    """환경 변수에서 평가 CSV 경로를 읽습니다."""
    load_dotenv()
    return Path(os.getenv("MULTI_AGENT_EVALUATION_CSV", DEFAULT_OUTPUT_CSV))


def load_sample_tasks(path: Path = DEFAULT_SAMPLE_PATH) -> list[dict]:
    """평가용 task 목록을 읽습니다."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_state(task: dict, state: dict) -> dict:
    """workflow state를 평가 row로 변환합니다."""
    plan = state.get("plan", [])
    research_notes = state.get("research_notes", [])
    draft = state.get("draft_answer", "")
    feedback = state.get("review_feedback", [])
    final = state.get("final_answer", "")
    logs = state.get("logs", [])

    expected_agents = set(task.get("expected_agents", []))
    actual_agents = {log.get("agent_name") for log in logs}

    return {
        "task_id": task.get("id"),
        "title": task.get("title"),
        "plan_exists": int(bool(plan)),
        "plan_count": len(plan),
        "research_notes_count": len(research_notes),
        "draft_exists": int(bool(draft)),
        "review_feedback_count": len(feedback),
        "final_answer_exists": int(bool(final)),
        "revision_applied": int(int(state.get("revision_count", 0)) > 0),
        "log_count": len(logs),
        "expected_agent_coverage": int(expected_agents.issubset(actual_agents)),
        "error": state.get("error"),
    }


def save_csv(rows: list[dict], output_path: Path) -> None:
    """평가 결과를 CSV 파일로 저장합니다."""
    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """sample tasks 기반 평가를 실행합니다."""
    tasks = load_sample_tasks()
    rows = []

    for task in tasks:
        state = run_multi_agent_workflow(task["user_request"], write_log=False)
        rows.append(evaluate_state(task, state))

    output_path = load_output_csv_path()
    save_csv(rows, output_path)

    print("Chapter 12 Multi-Agent Evaluation")
    print(f"total: {len(rows)}")
    print(f"saved: {output_path}")

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