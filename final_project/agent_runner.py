"""
Chapter 15 Agent Runner

RAG, Tool, Memory, Evaluation, Trace, Backlog, Report를 하나의 실행 흐름으로 연결합니다.
"""

from __future__ import annotations

from config import settings
from evaluator import append_evaluation_csv, evaluate_response
from improvement_backlog import create_backlog_items, save_backlog
from memory_store import memory_store
from rag_pipeline import build_context, search_documents
from report_generator import save_latest_report
from schemas import AgentRequest, AgentResponse
from tool_registry import run_if_needed
from trace_logger import log_step


def generate_answer(user_request: str, context: str, tool_result: dict | None) -> str:
    lines = [
        "요청을 분석한 결과는 다음과 같습니다.",
        "",
        f"요청: {user_request}",
        "",
        "## 참고 근거",
        context,
    ]
    if tool_result:
        lines.extend(["", "## 도구 실행 결과", str(tool_result.get("result", ""))])
    else:
        lines.extend(["", "## 답변 초안", "관련 문서를 바탕으로 요청 내용을 처리했습니다."])
    return "\n".join(lines)


def run_agent(request: AgentRequest, trace_id: str) -> AgentResponse:
    log_step(trace_id, "agent_start", "success", "agent request received", {"session_id": request.session_id})

    memory = memory_store.load(request.session_id) if settings.enable_memory else []
    log_step(trace_id, "memory_load", "success", "memory loaded", {"memory_count": len(memory)})

    sources = search_documents(request.user_request) if settings.enable_rag else []
    context = build_context(sources)
    log_step(trace_id, "rag_search", "success", "document search completed", {"source_count": len(sources)})

    tool_result = run_if_needed(request.user_request, context)
    if tool_result:
        log_step(trace_id, "tool_call", tool_result.get("status", "success"), "tool executed", tool_result)

    final_answer = generate_answer(request.user_request, context, tool_result)
    evaluation = evaluate_response(request.user_request, final_answer, sources) if settings.enable_evaluation else None

    backlog_items = create_backlog_items(evaluation) if evaluation else []

    response = AgentResponse(
        status="success",
        trace_id=trace_id,
        final_answer=final_answer,
        sources=sources,
        evaluation=evaluation,
        backlog_items=backlog_items,
        warnings=[] if sources else ["검색된 근거 문서가 없습니다."],
        metadata={
            "runner": "agentops_final_project",
            "memory_count": len(memory),
            "tool_used": tool_result.get("tool") if tool_result else None,
        },
    )

    if request.session_id and settings.enable_memory:
        memory_store.append(request.session_id, {"user_request": request.user_request, "trace_id": trace_id})

    if evaluation:
        append_evaluation_csv(trace_id, evaluation)
    save_backlog(backlog_items)
    save_latest_report(response)
    log_step(trace_id, "agent_complete", "success", "agent request completed", {"score": evaluation.total_score if evaluation else None})
    return response