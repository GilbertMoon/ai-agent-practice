"""
Chapter 12 Collaboration Logger

멀티 에이전트 협업 과정을 state와 파일에 기록합니다.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from shared_state import MultiAgentState, now_iso


DEFAULT_LOG_PATH = "collaboration.log"


def load_log_path() -> Path:
    """환경 변수에서 collaboration log 경로를 읽습니다."""
    load_dotenv()
    return Path(os.getenv("COLLABORATION_LOG_PATH", DEFAULT_LOG_PATH))


def build_log_event(
    agent_name: str,
    input_keys: list[str],
    output_keys: list[str],
    status: str = "success",
    message: str = "",
) -> dict[str, Any]:
    """agent 실행 로그 이벤트를 생성합니다."""
    return {
        "timestamp": now_iso(),
        "agent_name": agent_name,
        "input_keys": input_keys,
        "output_keys": output_keys,
        "status": status,
        "message": message,
    }


def append_log_to_state(state: MultiAgentState, event: dict[str, Any]) -> MultiAgentState:
    """state 내부 logs에 이벤트를 추가합니다."""
    logs = state.get("logs", [])
    logs.append(event)
    state["logs"] = logs
    return state


def append_log_to_file(event: dict[str, Any], path: Path | None = None) -> None:
    """로그 이벤트를 JSON Lines 파일에 저장합니다."""
    log_path = path or load_log_path()
    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def log_agent_step(
    state: MultiAgentState,
    agent_name: str,
    input_keys: list[str],
    output_keys: list[str],
    status: str = "success",
    message: str = "",
    write_file: bool = True,
) -> MultiAgentState:
    """state와 파일에 agent 실행 로그를 남깁니다."""
    event = build_log_event(
        agent_name=agent_name,
        input_keys=input_keys,
        output_keys=output_keys,
        status=status,
        message=message,
    )
    append_log_to_state(state, event)

    if write_file:
        append_log_to_file(event)

    return state