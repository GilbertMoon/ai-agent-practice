from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    user_request: str = Field(..., min_length=1, max_length=3000, description="사용자 요청")
    session_id: str | None = Field(default=None, max_length=100, description="대화 세션 ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="요청 출처와 부가 정보")


class SourceDocument(BaseModel):
    path: str
    score: int
    preview: str


class EvaluationResult(BaseModel):
    request_fulfillment: int
    groundedness: int
    completeness: int
    clarity: int
    safety: int
    total_score: int
    failure_type: str
    comment: str


class BacklogItem(BaseModel):
    issue_id: str
    failure_type: str
    problem: str
    improvement: str
    priority: Literal["high", "medium", "low"]


class AgentResponse(BaseModel):
    status: Literal["success", "failed"]
    trace_id: str
    final_answer: str
    sources: list[SourceDocument] = Field(default_factory=list)
    evaluation: EvaluationResult | None = None
    backlog_items: list[BacklogItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationRequest(BaseModel):
    user_request: str
    final_answer: str
    sources: list[SourceDocument] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    service: str
    dependencies: dict[str, str]


class ErrorResponse(BaseModel):
    status: Literal["failed"] = "failed"
    trace_id: str
    error_type: str
    message: str
    warnings: list[str] = Field(default_factory=list)