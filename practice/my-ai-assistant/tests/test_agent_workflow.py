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
        report = execute_plan(make_plan("missing"))
        self.assertEqual(report["status"], "HOLD")
        self.assertIn("근거", report["trace"][0]["reason"])

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
