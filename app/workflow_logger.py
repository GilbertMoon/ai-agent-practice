"""
Chapter 10 Workflow Logger

워크플로우의 각 step 실행 결과를 state와 로그 파일에 기록합니다.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from state_schema import AgentState


DEFAULT_LOG_PATH = "workflow_runs.log"


def load_workflow_log_path() -> Path:
    """환경 변수에서 workflow 로그 경로를 읽습니다."""
    load_dotenv()
    return Path(os.getenv("WORKFLOW_LOG_PATH", DEFAULT_LOG_PATH))


def build_step_event(state: AgentState, step_name: str, note: str | None = None) -> dict[str, Any]:
    """현재 state를 바탕으로 step 로그 이벤트를 만듭니다."""
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "step_name": step_name,
        "route": state.get("route"),
        "selected_tool": state.get("selected_tool"),
        "result_count": state.get("result_count", 0),
        "retrieval_status": state.get("retrieval_status"),
        "needs_fallback": state.get("needs_fallback", False),
        "error": state.get("error"),
        "note": note,
    }


def append_log_to_state(state: AgentState, event: dict[str, Any]) -> AgentState:
    """state.logs에 이벤트를 추가합니다."""
    logs = state.setdefault("logs", [])
    logs.append(event)
    return state


def append_log_to_file(event: dict[str, Any]) -> None:
    """JSON Lines 형식으로 로그 파일에 이벤트를 추가합니다."""
    log_path = load_workflow_log_path()
    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def log_step(state: AgentState, step_name: str, note: str | None = None, write_file: bool = True) -> AgentState:
    """step 실행 결과를 state와 파일에 기록합니다."""
    event = build_step_event(state, step_name, note)
    append_log_to_state(state, event)

    if write_file:
        append_log_to_file(event)

    return state