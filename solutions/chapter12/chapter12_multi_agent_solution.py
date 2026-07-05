"""
Chapter 12 Mini Project Solution

역할 분담형 수업 공지 분석·안내문 작성 에이전트 예제입니다.
이 파일 하나만 실행해도 Planner, Researcher, Writer, Reviewer, Coordinator 흐름을 확인할 수 있습니다.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = BASE_DIR / "collaboration.log"
DEFAULT_USER_REQUEST = "이번 주 수업 공지와 과제 조건을 종합해서 학생들에게 보낼 안내문을 작성해 주세요."


MultiAgentState = dict[str, Any]


def now_iso() -> str:
    """현재 시각을 ISO 문자열로 반환합니다."""
    return datetime.now().isoformat(timespec="seconds")


def create_initial_state(user_request: str, memory_context: str = "") -> MultiAgentState:
    """멀티 에이전트가 공유할 초기 state를 생성합니다."""
    return {
        "user_request": user_request,
        "memory_context": memory_context,
        "plan": [],
        "research_notes": [],
        "draft_answer": "",
        "review_feedback": [],
        "final_answer": "",
        "revision_count": 0,
        "logs": [],
        "error": None,
    }


def summarize_state(state: MultiAgentState) -> dict[str, Any]:
    """실행 결과를 짧게 요약합니다."""
    return {
        "user_request": state.get("user_request", ""),
        "plan_count": len(state.get("plan", [])),
        "research_note_count": len(state.get("research_notes", [])),
        "has_draft_answer": bool(state.get("draft_answer")),
        "review_feedback_count": len(state.get("review_feedback", [])),
        "has_final_answer": bool(state.get("final_answer")),
        "revision_count": state.get("revision_count", 0),
        "log_count": len(state.get("logs", [])),
        "error": state.get("error"),
    }


def log_agent_step(
    state: MultiAgentState,
    agent_name: str,
    input_keys: list[str],
    output_keys: list[str],
    status: str = "success",
    message: str = "",
    write_file: bool = True,
) -> MultiAgentState:
    """state와 JSONL 파일에 agent 실행 로그를 남깁니다."""
    event = {
        "timestamp": now_iso(),
        "agent_name": agent_name,
        "input_keys": input_keys,
        "output_keys": output_keys,
        "status": status,
        "message": message,
    }
    state.setdefault("logs", []).append(event)

    if write_file:
        with LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, ensure_ascii=False) + "\n")

    return state


def planner_agent(state: MultiAgentState) -> MultiAgentState:
    """사용자 요청을 실행 가능한 작업 단계로 나눕니다."""
    request = state.get("user_request", "")
    plan = [
        "사용자 요청 의도 파악",
        "수업 공지와 과제 조건 분리",
        "제출 항목, 제출 형식, 마감일 확인",
        "필요한 정보와 확인 필요 항목 정리",
        "학생 안내문 초안 작성",
        "누락 항목과 표현을 검토",
    ]

    if "평가" in request:
        plan.append("평가 기준을 별도 항목으로 정리")
    if "프로젝트" in request:
        plan.append("프로젝트 제출 조건과 산출물을 구분")
    if "짧게" in request:
        plan.append("간결한 설명 형식으로 정리")

    state["plan"] = plan
    return state


def researcher_agent(state: MultiAgentState) -> MultiAgentState:
    """요청과 plan을 기준으로 안내문에 필요한 근거와 확인 사항을 정리합니다."""
    request = state.get("user_request", "")
    notes = [
        f"요청 요약: {request}",
        "과제 요구사항, 평가 기준, 제출 방법을 확인해야 합니다.",
        "공지 대상, 핵심 안내사항, 일정, 유의사항을 확인해야 합니다.",
        "확정되지 않은 정보는 확인 필요로 표시합니다.",
    ]

    if "제출" in request:
        notes.append("제출물, 제출 형식, 제출 위치를 구분해 안내해야 합니다.")
    if "마감" in request or "조건" in request:
        notes.append("마감일과 조건은 학생 혼동을 줄이기 위해 별도 항목으로 작성합니다.")
    if "멀티 에이전트" in request:
        notes.append("멀티 에이전트는 여러 역할의 agent가 shared state를 통해 협업하는 구조입니다.")

    state["research_notes"] = notes
    return state


def writer_agent(state: MultiAgentState) -> MultiAgentState:
    """plan과 research_notes를 바탕으로 답변 초안을 작성합니다."""
    notes = state.get("research_notes", [])
    plan = state.get("plan", [])

    state["draft_answer"] = (
        "안녕하세요. 아래와 같이 안내드립니다.\n\n"
        "## 1. 핵심 안내\n"
        "학생들이 혼동하지 않도록 주요 조건을 항목별로 정리합니다.\n\n"
        "## 2. 확인된 내용\n"
        + "\n".join(f"- {note}" for note in notes)
        + "\n\n## 3. 진행 단계\n"
        + "\n".join(f"- {item}" for item in plan[:5])
        + "\n\n## 4. 확인 필요\n"
        "- 제출 항목: 확인 필요\n"
        "- 마감일: 확인 필요\n"
        "- 평가 기준: 확인 필요"
    )
    return state


def reviewer_agent(state: MultiAgentState) -> MultiAgentState:
    """초안을 검토하고 수정이 필요한 부분을 feedback으로 남깁니다."""
    draft = state.get("draft_answer", "")
    feedback = []

    if "확인 필요" in draft:
        feedback.append("확인 필요 항목은 최종 답변에서도 명확히 표시하세요.")
    if "## 1." not in draft:
        feedback.append("답변을 섹션별로 나누어 가독성을 높이세요.")
    if not feedback:
        feedback.append("큰 문제는 없으며 최종 답변으로 사용할 수 있습니다.")

    state["review_feedback"] = feedback
    return state


def has_actionable_feedback(feedback: list[str]) -> bool:
    """수정이 필요한 feedback인지 판단합니다."""
    if not feedback:
        return False
    return any("표시" in item or "나누어" in item or "수정" in item for item in feedback)


def revise_answer(state: MultiAgentState) -> MultiAgentState:
    """Reviewer feedback을 반영해 초안을 수정합니다."""
    feedback = state.get("review_feedback", [])
    if not has_actionable_feedback(feedback):
        return state

    draft = state.get("draft_answer", "")
    revision_text = "\n\n## 5. 검토 반영\n" + "\n".join(f"- {item}" for item in feedback)
    state["draft_answer"] = draft + revision_text
    state["revision_count"] = int(state.get("revision_count", 0)) + 1
    return state


def finalize_answer(state: MultiAgentState) -> MultiAgentState:
    """최종 답변을 확정합니다."""
    state["final_answer"] = state.get("draft_answer", "")
    return state


def run_coordinator(state: MultiAgentState, write_log: bool = True, max_review_rounds: int = 1) -> MultiAgentState:
    """Planner → Researcher → Writer → Reviewer → Revision → Final 흐름을 제어합니다."""
    state = planner_agent(state)
    state = log_agent_step(state, "Planner Agent", ["user_request"], ["plan"], message="작업 계획 생성 완료", write_file=write_log)

    state = researcher_agent(state)
    state = log_agent_step(state, "Researcher Agent", ["user_request", "plan"], ["research_notes"], message="정보와 근거 정리 완료", write_file=write_log)

    state = writer_agent(state)
    state = log_agent_step(state, "Writer Agent", ["plan", "research_notes"], ["draft_answer"], message="답변 초안 작성 완료", write_file=write_log)

    for _ in range(max_review_rounds):
        state = reviewer_agent(state)
        state = log_agent_step(state, "Reviewer Agent", ["draft_answer"], ["review_feedback"], message="초안 검토 완료", write_file=write_log)
        if not has_actionable_feedback(state.get("review_feedback", [])):
            break
        state = revise_answer(state)
        state = log_agent_step(state, "Writer Agent", ["draft_answer", "review_feedback"], ["draft_answer"], message="검토 의견 반영 완료", write_file=write_log)

    state = finalize_answer(state)
    state = log_agent_step(state, "Coordinator", ["draft_answer"], ["final_answer"], message="최종 답변 확정 완료", write_file=write_log)
    return state


def run_multi_agent_workflow(user_request: str = DEFAULT_USER_REQUEST, memory_context: str = "", write_log: bool = True) -> MultiAgentState:
    """사용자 요청을 멀티 에이전트 workflow로 처리합니다."""
    state = create_initial_state(user_request=user_request, memory_context=memory_context)
    return run_coordinator(state, write_log=write_log)


def main() -> None:
    """샘플 요청으로 workflow를 실행합니다."""
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    state = run_multi_agent_workflow(DEFAULT_USER_REQUEST, write_log=True)

    print("Chapter 12 Mini Project Solution")
    print("=" * 70)
    print("[상태 요약]")
    print(json.dumps(summarize_state(state), ensure_ascii=False, indent=2))
    print("\n[최종 답변]")
    print(state.get("final_answer", ""))
    print(f"\n[로그 파일]\n{LOG_PATH}")


if __name__ == "__main__":
    main()
