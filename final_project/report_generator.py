from __future__ import annotations

from config import settings
from schemas import AgentResponse


def generate_report(response: AgentResponse) -> str:
    lines = [
        "# AgentOps Latest Report",
        "",
        f"- status: {response.status}",
        f"- trace_id: {response.trace_id}",
        f"- source_count: {len(response.sources)}",
        f"- backlog_count: {len(response.backlog_items)}",
        "",
        "## Final Answer",
        "",
        response.final_answer,
        "",
    ]

    if response.evaluation:
        lines.extend(
            [
                "## Evaluation",
                "",
                f"- total_score: {response.evaluation.total_score}/25",
                f"- failure_type: {response.evaluation.failure_type}",
                f"- comment: {response.evaluation.comment}",
                "",
            ]
        )

    if response.sources:
        lines.extend(["## Sources", ""])
        for source in response.sources:
            lines.append(f"- {source.path} (score={source.score})")
        lines.append("")

    if response.backlog_items:
        lines.extend(["## Improvement Backlog", ""])
        for item in response.backlog_items:
            lines.append(f"- {item.issue_id}: {item.improvement} ({item.priority})")
        lines.append("")

    return "\n".join(lines)


def save_latest_report(response: AgentResponse) -> None:
    settings.latest_report_path.parent.mkdir(parents=True, exist_ok=True)
    settings.latest_report_path.write_text(generate_report(response), encoding="utf-8")


def read_latest_report() -> str:
    if not settings.latest_report_path.exists():
        return "아직 생성된 리포트가 없습니다."

    return settings.latest_report_path.read_text(encoding="utf-8")