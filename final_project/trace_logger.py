from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from config import settings


SENSITIVE_KEYS = {"api_key", "apikey", "token", "secret", "password", "authorization"}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def create_trace_id(prefix: str = "agentops") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    return f"{prefix}_{timestamp}_{suffix}"


def mask_sensitive_data(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***MASKED***" if str(key).lower() in SENSITIVE_KEYS else mask_sensitive_data(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [mask_sensitive_data(item) for item in value]

    return value


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_jsonl(path: Path, event: dict[str, Any]) -> None:
    if not settings.enable_trace_log:
        return

    ensure_parent_dir(path)
    safe_event = mask_sensitive_data(event)

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(safe_event, ensure_ascii=False) + "\n")


def build_log_event(
    trace_id: str,
    step: str,
    status: str,
    message: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "timestamp": now_iso(),
        "trace_id": trace_id,
        "step": step,
        "status": status,
        "message": message,
        "extra": extra or {},
    }


def log_step(
    trace_id: str,
    step: str,
    status: str,
    message: str,
    extra: dict[str, Any] | None = None,
) -> None:
    write_jsonl(
        settings.agent_log_path,
        build_log_event(trace_id, step, status, message, extra),
    )