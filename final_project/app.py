from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from agent_runner import run_agent
from config import settings
from evaluator import evaluate_response
from report_generator import read_latest_report
from schemas import (
    AgentRequest,
    AgentResponse,
    EvaluationRequest,
    EvaluationResult,
    HealthResponse,
    ReadinessResponse,
)
from trace_logger import create_trace_id


app = FastAPI(
    title=settings.service_name,
    description="Chapter 15 AgentOps Final Project API",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        environment=settings.environment,
    )


@app.get("/ready", response_model=ReadinessResponse)
def ready() -> ReadinessResponse:
    dependencies = {
        "docs_dir": "enabled" if settings.enable_rag else "disabled",
        "memory": "enabled" if settings.enable_memory else "disabled",
        "evaluation": "enabled" if settings.enable_evaluation else "disabled",
        "trace_log": "enabled" if settings.enable_trace_log else "disabled",
    }

    return ReadinessResponse(
        status="ready",
        service=settings.service_name,
        dependencies=dependencies,
    )


@app.get("/settings")
def public_settings() -> dict:
    return settings.to_public_dict()


@app.post("/agent/run", response_model=AgentResponse)
def agent_run(payload: AgentRequest, request: Request) -> AgentResponse:
    trace_id = request.headers.get("X-Trace-Id") or create_trace_id()
    return run_agent(payload, trace_id=trace_id)


@app.post("/agent/evaluate", response_model=EvaluationResult)
def agent_evaluate(payload: EvaluationRequest) -> EvaluationResult:
    return evaluate_response(
        payload.user_request,
        payload.final_answer,
        payload.sources,
    )


@app.get("/reports/latest", response_class=PlainTextResponse)
def latest_report() -> str:
    return read_latest_report()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )