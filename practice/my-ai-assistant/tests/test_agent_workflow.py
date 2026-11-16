"""Lesson 11 fully offline deterministic plan & execute tests."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_workflow import MAX_STEPS, Step, Plan, make_plan, verify, execute_plan, main


class AgentWorkflowTests(unittest.TestCase):
    def test_combined_has_two_steps(self):
        plan = make_plan("combined")
        self.assertEqual([s.name for s in plan.steps], ["find_notice", "add_numbers"])

    def test_plan_only_does_not_run_tool(self):
        with patch("agent_workflow.dispatch", side_effect=AssertionError("DO_NOT_EXECUTE")):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["plan"]), 0)
            self.assertIn("[PLAN_ONLY]", output.getvalue())

    def test_combined_finishes_with_verified_results(self):
        report = execute_plan(make_plan("combined"))
        self.assertEqual(report["status"], "COMPLETED")
        self.assertEqual([x["status"] for x in report["trace"]], ["PASS", "PASS"])

    def test_missing_evidence_holds(self):
        plan = make_plan("missing")
        self.assertEqual([step.name for step in plan.steps], ["find_notice", "add_numbers"])
        report = execute_plan(plan)
        self.assertEqual(report["status"], "HOLD")
        self.assertIn("근거", report["trace"][0]["reason"])
        self.assertEqual(report["completed"], 1)
        self.assertEqual(report["total"], 2)
        self.assertEqual(report["not_run"], [{"index": 2, "tool": "add_numbers"}])

    def test_deadline_needs_actual_time_phrase_not_just_a_search_hit(self):
        step = make_plan("combined").steps[0]
        fake_hit = {"found": True, "source": "lesson04_notice.md",
                    "text": "과제 제출 방법은 LMS에 안내합니다."}
        passed, reason = verify(step, fake_hit)
        self.assertFalse(passed)
        self.assertIn("기한", reason)

    def test_deadline_accepts_real_fixture_sentence(self):
        step = make_plan("combined").steps[0]
        correct = {"found": True, "source": "lesson04_notice.md",
                   "text": "이번 주 과제 제출 기한은 금요일 오후 6시입니다."}
        self.assertTrue(verify(step, correct)[0])

    def test_failed_search_has_not_run_trace_output(self):
        from agent_workflow import print_execution
        with contextlib.redirect_stdout(io.StringIO()) as output:
            print_execution(execute_plan(make_plan("missing")))
        self.assertIn("[NOT_RUN] step=2; tool=add_numbers", output.getvalue())
        self.assertIn("status=HOLD; completed=1/2", output.getvalue())

    def test_math_finishes(self):
        report = execute_plan(make_plan("math", -5, 7))
        self.assertEqual(report["trace"][0]["result"]["sum"], 2)

    def test_mismatch_holds(self):
        report = execute_plan(make_plan("math", 2, 3), runner=lambda req: {"sum": 999})
        self.assertEqual(report["status"], "HOLD")

    def test_no_execution_after_failure(self):
        seen = []
        def runner(req):
            seen.append(req.name)
            return {"found": False}
        report = execute_plan(make_plan("combined"), runner=runner)
        self.assertEqual(report["status"], "HOLD")
        self.assertEqual(seen, ["find_notice"])
        self.assertEqual(report["completed"], 1)

    def test_unregistered_tool_rejected(self):
        plan = Plan("unsafe", (Step("delete_file", {}, "found"),))
        report = execute_plan(plan)
        self.assertEqual(report["status"], "HOLD")

    def test_too_many_steps_rejected(self):
        plan = Plan("long", tuple(Step("add_numbers", {"a": 1, "b": 2}, "sum") for _ in range(MAX_STEPS + 1)))
        with self.assertRaises(ValueError):
            execute_plan(plan)

    def test_empty_plan_rejected(self):
        with self.assertRaises(ValueError):
            execute_plan(Plan("empty", ()))

    def test_wrong_sum_type_rejected(self):
        self.assertFalse(verify(Step("add_numbers", {"a": 1, "b": 2}, "sum"), {"sum": True})[0])

    def test_fixture_does_not_call_model(self):
        with patch("agent_workflow.make_client", side_effect=AssertionError("MODEL_FORBIDDEN")):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["run"]), 0)

    def test_live_run_is_blocked_without_api(self):
        with patch("agent_workflow.make_client", side_effect=AssertionError("MODEL_FORBIDDEN")):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["run", "--mode", "live"]), 2)
            self.assertIn("계획 제안만", output.getvalue())

    def test_missing_cli_exit_nonzero(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["run", "--scenario", "missing"]), 2)

    def test_unsupported_scenario_rejected(self):
        with self.assertRaises(ValueError):
            make_plan("unsafe")


if __name__ == "__main__":
    unittest.main()
