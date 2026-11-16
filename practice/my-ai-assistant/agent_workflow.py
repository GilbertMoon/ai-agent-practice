"""Lesson 11: bounded, evidence-first agent execution workflow.

Fixture plan is deterministic, NOT an LLM-generated plan. Read-only
Lesson 09 dispatcher performs all actions, with explicit verification.
Live mode requests a plan suggestion only; it never executes the suggestion.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from typing import Callable

from main import load_local_env, make_client
from tool_calling import ToolRequest, dispatch

MAX_STEPS = 3


@dataclass(frozen=True)
class Step:
    name: str
    arguments: dict
    expected: str


@dataclass(frozen=True)
class Plan:
    scenario: str
    steps: tuple[Step, ...]


def make_plan(scenario: str, a: int = 12, b: int = 30) -> Plan:
    if scenario not in ("combined", "math", "missing"):
        raise ValueError("지원하는 시나리오는 combined, math, missing입니다.")
    steps = []
    if scenario in ("combined", "missing"):
        query = "과제 제출" if scenario == "combined" else "우주선 연료"
        steps.append(Step("find_notice", {"query": query}, "deadline" if scenario == "combined" else "found"))
    if scenario in ("combined", "missing", "math"):
        steps.append(Step("add_numbers", {"a": a, "b": b}, "sum"))
    if len(steps) > MAX_STEPS:
        raise ValueError("단계 상한 초과")
    return Plan(scenario, tuple(steps))


def verify(step: Step, result: dict) -> tuple[bool, str]:
    if not isinstance(result, dict) or "error" in result:
        return False, "도구 결과 형식 또는 오류"
    if step.expected in ("found", "deadline"):
        if result.get("found") is not True or not result.get("source") or not result.get("text"):
            return False, "검색 근거 없음"
        if step.expected == "deadline":
            # This classroom fixture checks that the cited passage actually
            # contains a submission deadline, not merely any search hit.
            text = result["text"]
            pattern = r"과제\s*제출\s*기한[^\n]{0,80}?(?:월|화|수|목|금|토|일)요일\s*(?:오전|오후)\s*\d{1,2}시"
            if not isinstance(text, str) or not re.search(pattern, text):
                return False, "과제 제출 기한 문구 미확인"
            return True, "과제 제출 기한과 출처 확인(교육용 패턴 검증)"
        return True, "검색 근거와 출처 확인"
    if step.expected == "sum":
        expected = step.arguments["a"] + step.arguments["b"]
        if type(result.get("sum")) is not int or result["sum"] != expected:
            return False, "계산 결과 불일치"
        return True, "계산 결과 검증"
    return False, "알 수 없는 검증 규칙"


def execute_plan(plan: Plan, runner: Callable[[ToolRequest], dict] = dispatch) -> dict:
    if not plan.steps or len(plan.steps) > MAX_STEPS:
        raise ValueError("실행 단계 수가 허용 범위를 벗어났습니다.")
    trace = []
    for index, step in enumerate(plan.steps, start=1):
        # Always pass through the Lesson 09 allowlist and JSON argument validation.
        request = ToolRequest(step.name, json.dumps(step.arguments, ensure_ascii=False))
        try:
            result = runner(request)
            ok, reason = verify(step, result)
        except (ValueError, TypeError, KeyError) as exc:
            ok, reason, result = False, type(exc).__name__, {}
        status = "PASS" if ok else "FAIL"
        trace.append({"index": index, "tool": step.name, "status": status, "reason": reason, "result": result})
        if not ok:
            return {"status": "HOLD", "completed": len(trace), "total": len(plan.steps),
                    "trace": trace, "not_run": [
                        {"index": i, "tool": pending.name}
                        for i, pending in enumerate(plan.steps[len(trace):], start=len(trace) + 1)
                    ]}
    return {"status": "COMPLETED", "completed": len(trace), "total": len(plan.steps), "trace": trace, "not_run": []}


def print_plan(plan: Plan) -> None:
    print(f"[PLAN] scenario={plan.scenario}; steps={len(plan.steps)}; mode=fixture")
    for i, step in enumerate(plan.steps, 1):
        print(f"[PLAN_STEP {i}] tool={step.name}; arguments={json.dumps(step.arguments, ensure_ascii=False)}; check={step.expected}")


def print_execution(report: dict) -> None:
    for row in report["trace"]:
        print(f"[STEP {row['index']}] {row['tool']} status={row['status']}; check={row['reason']}")
        result = row["result"]
        if row["tool"] == "find_notice":
            print(f"[EVIDENCE] found={result.get('found', False)}; source={result.get('source', '(none)')}")
        elif row["tool"] == "add_numbers":
            print(f"[RESULT] sum={result.get('sum', '(none)')}")
    for pending in report.get("not_run", []):
        print(f"[NOT_RUN] step={pending['index']}; tool={pending['tool']}; reason=선행 검증 실패")
    print(f"[FINAL] status={report['status']}; completed={report['completed']}/{report['total']}")
    print("[FIXTURE] 규칙 기반 계획·검증. 실제 모델 계획 아님; model_api_calls=0")


def live_plan_suggestion(scenario: str) -> None:
    # A model may suggest a plan but never gets authority to execute it.
    load_local_env()
    client = make_client("live")
    prompt = (
        "읽기 전용 AI 비서의 계획 초안만 작성하세요. 도구 실행 금지. "
        "허용 함수는 find_notice(query: string), add_numbers(a: int,b: int)뿐입니다. "
        "각 단계의 검증 기준, 근거 없을 때 HOLD할 조건을 한국어로 간단히 제안하세요. "
        f"시나리오: {scenario}. 실제 실행한 것처럼 표현하지 마세요."
    )
    reply = client.ask(prompt)
    print("[LIVE_PLAN_ONLY] 아래는 모델이 제안한 텍스트입니다. 실행되지 않았습니다.")
    print(reply.text)
    print(f"[LIVE] model={reply.model}; input={reply.input_tokens}; output={reply.output_tokens}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lesson 11 bounded read-only agent")
    parser.add_argument("action", choices=("plan", "run"))
    parser.add_argument("--scenario", choices=("combined", "math", "missing"), default="combined")
    parser.add_argument("--a", type=int, default=12)
    parser.add_argument("--b", type=int, default=30)
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    args = parser.parse_args(argv)
    try:
        plan = make_plan(args.scenario, args.a, args.b)
        if args.mode == "live":
            if args.action != "plan":
                raise ValueError("Live 모드는 계획 제안만 허용하며 실행하지 않습니다.")
            live_plan_suggestion(args.scenario)
            return 0
        print_plan(plan)
        if args.action == "plan":
            print("[PLAN_ONLY] 실제 도구 실행 없음; model_api_calls=0")
            return 0
        report = execute_plan(plan)
        print_execution(report)
        return 0 if report["status"] == "COMPLETED" else 2
    except ValueError as exc:
        print(f"설정 오류: {exc}")
        return 2
    except Exception as exc:
        print(f"실행 오류: {type(exc).__name__} (민감정보 비표시)")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
