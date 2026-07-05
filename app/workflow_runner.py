"""
Chapter 10 Basic Workflow Runner

모든 step을 순서대로 실행하는 기본 workflow runner입니다.
"""

import importlib
import json
import sys
import types
from pathlib import Path
from typing import Any, Callable


WorkflowStep = Callable[[dict[str, Any]], dict[str, Any]]


def ensure_app_package() -> None:
    """
    python app/workflow_runner.py 방식으로 실행해도
    app.* import와 app 폴더 안의 일반 import가 모두 동작하도록 실행 환경을 보정합니다.
    """
    app_dir = Path(__file__).resolve().parent
    project_root = app_dir.parent

    for path in (project_root, app_dir):
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)

    app_package = sys.modules.get("app")

    if app_package is None or not hasattr(app_package, "__path__"):
        package = types.ModuleType("app")
        package.__path__ = [str(app_dir)]
        sys.modules["app"] = package


def load_app_function(module_name: str, function_name: str):
    """app 폴더 안의 모듈에서 특정 함수를 불러옵니다."""
    module = importlib.import_module(f"app.{module_name}")
    return getattr(module, function_name)


ensure_app_package()

answer_step = load_app_function("answer_generator", "answer_step")
fallback_step = load_app_function("fallback_handler", "fallback_step")
create_initial_state = load_app_function("state_schema", "create_initial_state")
summarize_state = load_app_function("state_schema", "summarize_state")
log_step = load_app_function("workflow_logger", "log_step")

analyze_question_step = load_app_function("workflow_steps", "analyze_question_step")
route_question_step = load_app_function("workflow_steps", "route_question_step")
search_step = load_app_function("workflow_steps", "search_step")
evaluate_retrieval_step = load_app_function("workflow_steps", "evaluate_retrieval_step")


WORKFLOW_STEPS: list[WorkflowStep] = [
    analyze_question_step,
    route_question_step,
    search_step,
    evaluate_retrieval_step,
    fallback_step,
    answer_step,
]


def run_workflow(user_question: str, write_log: bool = True) -> dict[str, Any]:
    """모든 step을 순서대로 실행하고 step별 로그를 남깁니다."""
    state = create_initial_state(user_question)

    for step in WORKFLOW_STEPS:
        state = step(state)
        log_step(state, step.__name__, write_file=write_log)

    return state


def print_state_summary(state: dict[str, Any]) -> None:
    """최종 state 요약을 보기 좋게 출력합니다."""
    print("\n[최종 state 요약]")
    print(json.dumps(summarize_state(state), ensure_ascii=False, indent=2))


def main() -> None:
    """대화형으로 기본 workflow를 실행합니다."""
    print("Chapter 10 Basic Workflow Runner")
    print("종료하려면 exit 또는 quit를 입력하세요.")

    while True:
        question = input("\n질문을 입력하세요: ").strip()

        if question.lower() in {"exit", "quit"}:
            print("프로그램을 종료합니다.")
            break

        if not question:
            print("질문이 비어 있습니다. 다시 입력해 주세요.")
            continue

        state = run_workflow(question, write_log=True)
        print_state_summary(state)


if __name__ == "__main__":
    main()