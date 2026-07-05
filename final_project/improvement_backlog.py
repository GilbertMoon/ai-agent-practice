from __future__ import annotations

from config import settings
from schemas import BacklogItem, EvaluationResult


BACKLOG_RULES = {
    "retrieval_error": (
        "관련 문서 검색 품질이 낮습니다.",
        "문서 chunking, keyword 확장, 검색 기준을 개선합니다.",
        "high",
    ),
    "writing_error": (
        "답변이 충분히 완성되지 않았습니다.",
        "prompt template과 답변 구조를 개선합니다.",
        "medium",
    ),
    "safety_error": (
        "민감하거나 위험한 내용이 포함될 수 있습니다.",
        "민감정보 마스킹과 safety rule을 강화합니다.",
        "high",
    ),
    "quality_regression": (
        "전체 품질 점수가 낮습니다.",
        "평가 샘플을 추가하고 regression evaluation을 재실행합니다.",
        "medium",
    ),
}


def create_backlog_items(evaluation: EvaluationResult) -> list[BacklogItem]:
    if evaluation.failure_type == "none":
        return []

    problem, improvement, priority = BACKLOG_RULES.get(
        evaluation.failure_type,
        (
            "분류되지 않은 실패가 발생했습니다.",
            "trace log를 확인하고 실패 유형을 재정의합니다.",
            "low",
        ),
    )

    return [
        BacklogItem(
            issue_id=f"B-{evaluation.failure_type.upper()}",
            failure_type=evaluation.failure_type,
            problem=problem,
            improvement=improvement,
            priority=priority,  # type: ignore[arg-type]
        )
    ]


def save_backlog(items: list[BacklogItem]) -> None:
    if not items:
        return

    settings.backlog_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Improvement Backlog", ""]

    for item in items:
        lines.extend(
            [
                f"## {item.issue_id}",
                "",
                f"- failure_type: {item.failure_type}",
                f"- priority: {item.priority}",
                f"- problem: {item.problem}",
                f"- improvement: {item.improvement}",
                "",
            ]
        )

    settings.backlog_path.write_text("\n".join(lines), encoding="utf-8")