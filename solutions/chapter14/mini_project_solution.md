# Chapter 14 미니 프로젝트 솔루션

## 목표

FastAPI 기반 Agent API 서비스를 만들고 Docker로 실행합니다.

구현해야 할 기능은 다음과 같습니다.

```text
- /health endpoint
- /ready endpoint
- /settings endpoint
- /agent/run endpoint
- 요청/응답 schema 분리
- mock agent runner
- trace_id 생성
- request log와 agent run log 저장
- Dockerfile 작성
- compose.yaml 작성
- smoke_test.py 작성
```

## 권장 파일 구조

```text
ai-agent-practice/
├── app/
│   ├── app.py
│   ├── agent_runner.py
│   ├── config.py
│   ├── health_check.py
│   ├── logging_utils.py
│   ├── schemas.py
│   ├── smoke_test.py
│   ├── trace_middleware.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── compose.yaml
└── logs/
```

---

## 1. app/requirements.txt

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
pydantic-settings==2.5.2
httpx==0.27.2
```

---

## 2. app/config.py

```python
"""
Chapter 14 Service Config
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """서비스 설정입니다."""

    service_name: str = "Chapter 14 Agent API"
    environment: str = "local"
    enable_trace_log: bool = True
    log_path: Path = Path("logs/request_logs.jsonl")
    agent_run_log_path: Path = Path("logs/agent_runs.jsonl")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def to_public_dict(self) -> dict:
        """외부에 공개해도 되는 설정만 반환합니다."""
        return {
            "service_name": self.service_name,
            "environment": self.environment,
            "enable_trace_log": self.enable_trace_log,
            "log_path": str(self.log_path),
            "agent_run_log_path": str(self.agent_run_log_path),
        }


settings = Settings()
```

---

## 3. app/schemas.py

```python
"""
Chapter 14 API Schemas
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    """Agent 실행 요청 schema입니다."""

    user_request: str = Field(..., min_length=1, description="사용자 요청")
    session_id: str | None = Field(default=None, description="사용자 또는 대화 세션 ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


class AgentRunResponse(BaseModel):
    """Agent 실행 응답 schema입니다."""

    status: Literal["success", "failed"]
    trace_id: str
    final_answer: str
    latency_ms: int
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """오류 응답 schema입니다."""

    trace_id: str
    error_type: str
    message: str
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """health endpoint 응답 schema입니다."""

    status: str
    service: str


class ReadinessResponse(BaseModel):
    """ready endpoint 응답 schema입니다."""

    ready: bool
    checks: dict[str, bool]
```

---

## 4. app/logging_utils.py

```python
"""
Chapter 14 Logging Utilities
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


SENSITIVE_KEYS = {bytes.fromhex(item).decode() for item in [
    "6170695f6b6579",
    "6170696b6579",
    "746f6b656e",
    "736563726574",
    "70617373776f7264",
    "617574686f72697a6174696f6e",
]}


def now_iso() -> str:
    """현재 시각을 ISO 문자열로 반환합니다."""
    return datetime.now().isoformat(timespec="seconds")


def create_trace_id(prefix: str = "api") -> str:
    """API 요청 추적용 trace_id를 생성합니다."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    return f"{prefix}_{timestamp}_{suffix}"


def mask_sensitive_data(value: Any) -> Any:
    """dict/list 내부 민감정보를 마스킹합니다."""
    if isinstance(value, dict):
        masked = {}
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                masked[key] = "***MASKED***"
            else:
                masked[key] = mask_sensitive_data(item)
        return masked
    if isinstance(value, list):
        return [mask_sensitive_data(item) for item in value]
    return value


def ensure_parent_dir(path: Path) -> None:
    """로그 파일의 상위 폴더를 생성합니다."""
    path.parent.mkdir(parents=True, exist_ok=True)


def write_jsonl(path: Path, event: dict[str, Any]) -> None:
    """event를 JSONL 파일에 추가합니다."""
    ensure_parent_dir(path)
    safe_event = mask_sensitive_data(event)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(safe_event, ensure_ascii=False) + "\n")


def build_request_log_event(
    trace_id: str,
    path: str,
    method: str,
    status: str,
    latency_ms: int,
    message: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """API 요청 로그 event를 생성합니다."""
    return {
        "timestamp": now_iso(),
        "trace_id": trace_id,
        "path": path,
        "method": method,
        "status": status,
        "latency_ms": latency_ms,
        "message": message,
        "extra": extra or {},
    }


def build_agent_log_event(
    trace_id: str,
    step: str,
    status: str,
    message: str,
    latency_ms: int = 0,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Agent 실행 로그 event를 생성합니다."""
    return {
        "timestamp": now_iso(),
        "trace_id": trace_id,
        "step": step,
        "status": status,
        "latency_ms": latency_ms,
        "message": message,
        "extra": extra or {},
    }
```

---

## 5. app/health_check.py

```python
"""
Chapter 14 Health Check
"""

from __future__ import annotations

from config import settings


def get_health_status() -> dict:
    """서비스 프로세스가 살아 있는지 확인합니다."""
    return {
        "status": "ok",
        "service": settings.service_name,
    }


def get_readiness_status() -> dict:
    """서비스가 요청을 받을 준비가 되었는지 확인합니다."""
    checks = {
        "config_loaded": bool(settings.service_name),
        "log_configured": bool(settings.log_path),
        "agent_log_configured": bool(settings.agent_run_log_path),
    }
    return {
        "ready": all(checks.values()),
        "checks": checks,
    }
```

---

## 6. app/agent_runner.py

```python
"""
Chapter 14 Agent Runner
"""

from __future__ import annotations

import time
from typing import Any

from config import settings
from logging_utils import build_agent_log_event, write_jsonl
from schemas import AgentRunRequest, AgentRunResponse


def run_mock_agent(user_request: str, trace_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """실제 LLM API 없이 동작하는 mock agent입니다."""
    start = time.perf_counter()
    metadata = metadata or {}

    summary = user_request.strip()
    if len(summary) > 120:
        summary = summary[:117] + "..."

    final_answer = (
        "요청을 정상적으로 접수했습니다.\n"
        f"- 요청 요약: {summary}\n"
        "- 처리 방식: Chapter 14 mock agent runner\n"
        "- 확장 방향: Chapter 12의 multi-agent workflow와 연결할 수 있습니다."
    )

    latency_ms = int((time.perf_counter() - start) * 1000)
    return {
        "status": "success",
        "trace_id": trace_id,
        "final_answer": final_answer,
        "latency_ms": latency_ms,
        "warnings": [],
        "metadata": {
            "runner": "mock",
            "source": metadata.get("source", "api"),
        },
    }


def run_agent_service(request: AgentRunRequest, trace_id: str) -> AgentRunResponse:
    """Agent API 요청을 처리하고 응답 schema로 반환합니다."""
    start = time.perf_counter()

    if settings.enable_trace_log:
        write_jsonl(
            settings.agent_run_log_path,
            build_agent_log_event(
                trace_id=trace_id,
                step="agent_start",
                status="success",
                message="agent request received",
                extra={"session_id": request.session_id, "metadata": request.metadata},
            ),
        )

    result = run_mock_agent(
        user_request=request.user_request,
        trace_id=trace_id,
        metadata=request.metadata,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)
    result["latency_ms"] = max(result.get("latency_ms", 0), latency_ms)

    if settings.enable_trace_log:
        write_jsonl(
            settings.agent_run_log_path,
            build_agent_log_event(
                trace_id=trace_id,
                step="agent_complete",
                status="success",
                message="agent request completed",
                latency_ms=result["latency_ms"],
            ),
        )

    return AgentRunResponse(**result)
```

---

## 7. app/trace_middleware.py

```python
"""
Chapter 14 Trace Middleware
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from config import settings
from logging_utils import build_request_log_event, create_trace_id, write_jsonl


async def trace_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """요청 단위 trace_id와 요청 로그를 처리하는 middleware입니다."""
    trace_id = request.headers.get("X-Trace-Id") or create_trace_id()
    request.state.trace_id = trace_id
    start = time.perf_counter()

    try:
        response = await call_next(request)
        latency_ms = int((time.perf_counter() - start) * 1000)
        response.headers["X-Trace-Id"] = trace_id

        if settings.enable_trace_log:
            write_jsonl(
                settings.log_path,
                build_request_log_event(
                    trace_id=trace_id,
                    path=request.url.path,
                    method=request.method,
                    status="success" if response.status_code < 400 else "failed",
                    latency_ms=latency_ms,
                    message="request completed",
                    extra={"status_code": response.status_code},
                ),
            )

        return response

    except Exception as error:
        latency_ms = int((time.perf_counter() - start) * 1000)
        if settings.enable_trace_log:
            write_jsonl(
                settings.log_path,
                build_request_log_event(
                    trace_id=trace_id,
                    path=request.url.path,
                    method=request.method,
                    status="failed",
                    latency_ms=latency_ms,
                    message=str(error),
                    extra={"error_type": type(error).__name__},
                ),
            )
        raise
```

---

## 8. app/app.py

```python
"""
Chapter 14 FastAPI Agent Service
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agent_runner import run_agent_service
from config import settings
from health_check import get_health_status, get_readiness_status
from logging_utils import create_trace_id
from schemas import AgentRunRequest, AgentRunResponse, ErrorResponse, HealthResponse, ReadinessResponse
from trace_middleware import trace_middleware


app = FastAPI(
    title=settings.service_name,
    description="Chapter 14 Agent API Service",
    version="0.1.0",
)

app.middleware("http")(trace_middleware)


@app.get("/health", response_model=HealthResponse)
def health() -> dict:
    """서비스 프로세스가 살아 있는지 확인합니다."""
    return get_health_status()


@app.get("/ready", response_model=ReadinessResponse)
def ready() -> dict:
    """서비스가 실제 요청을 받을 준비가 되었는지 확인합니다."""
    return get_readiness_status()


@app.get("/settings")
def public_settings() -> dict:
    """민감정보를 제외한 현재 설정을 확인합니다."""
    return settings.to_public_dict()


@app.post("/agent/run", response_model=AgentRunResponse, responses={500: {"model": ErrorResponse}})
def run_agent(request: AgentRunRequest, http_request: Request) -> AgentRunResponse:
    """Agent workflow를 실행합니다."""
    trace_id = getattr(http_request.state, "trace_id", None) or create_trace_id()
    return run_agent_service(request, trace_id=trace_id)


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """예상하지 못한 오류를 일정한 JSON 형식으로 반환합니다."""
    trace_id = getattr(request.state, "trace_id", None) or create_trace_id()
    error = ErrorResponse(
        trace_id=trace_id,
        error_type=type(exc).__name__,
        message="Agent service request failed.",
        warnings=["자세한 원인은 서버 로그에서 trace_id로 확인하세요."],
    )
    return JSONResponse(status_code=500, content=error.model_dump())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
```

---

## 9. app/smoke_test.py

```python
"""
Chapter 14 Smoke Test
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_agent_run() -> None:
    response = client.post(
        "/agent/run",
        json={
            "user_request": "수업 공지를 짧게 작성해 주세요.",
            "session_id": "smoke-test",
            "metadata": {"source": "smoke_test"},
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["trace_id"]
    assert body["final_answer"]
    assert "X-Trace-Id" in response.headers


if __name__ == "__main__":
    test_health()
    test_ready()
    test_agent_run()
    print("smoke test passed")
```

---

## 10. app/Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 11. app/compose.yaml

```yaml
services:
  agent-api:
    build: .
    container_name: chapter14-agent-api
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 10s
      timeout: 3s
      retries: 3
```

---

## 실행 방법

### 1. 로컬 실행

```bash
cd app
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app:app --reload
```

Windows PowerShell에서는 다음과 같이 가상환경을 활성화합니다.

```powershell
cd app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app:app --reload
```

### 2. API 확인

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/settings
```

```bash
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"user_request":"수업 공지를 짧게 작성해 주세요.","session_id":"demo","metadata":{"source":"curl"}}'
```

### 3. Smoke test 실행

```bash
cd app
python smoke_test.py
```

### 4. Docker Compose 실행

```bash
cd app
docker compose up --build
```

다른 터미널에서 확인합니다.

```bash
curl http://localhost:8000/health
```

### 5. 로그 확인

```bash
cd app
cat logs/request_logs.jsonl
cat logs/agent_runs.jsonl
```

Windows PowerShell에서는 다음 명령을 사용할 수 있습니다.

```powershell
Get-Content logs/request_logs.jsonl
Get-Content logs/agent_runs.jsonl
```

---

## 통과 기준

```text
- /health가 200 OK를 반환한다.
- /ready가 ready=true를 반환한다.
- /settings가 공개 설정만 반환한다.
- /agent/run이 trace_id와 final_answer를 반환한다.
- 응답 header에 X-Trace-Id가 포함된다.
- logs/request_logs.jsonl 파일이 생성된다.
- logs/agent_runs.jsonl 파일이 생성된다.
- smoke_test.py가 통과한다.
- docker compose up --build로 서비스가 실행된다.
```
