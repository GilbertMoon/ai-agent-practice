"""Lesson 10 offline unit tests; real stdio sessions tested separately."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mcp_lesson10_logic import add_numbers, find_notice, public_notice, lesson_prompt
from mcp_lesson10_fixture import main as fixture_main
from mcp_lesson10_client import main as client_main, SERVER, ToolResultError


class MCPBasicsTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add_numbers(12, 30), {"sum": 42})

    def test_add_negative(self):
        self.assertEqual(add_numbers(-5, 7)["sum"], 2)

    def test_reject_bool_as_int(self):
        with self.assertRaises(ValueError):
            add_numbers(True, 2)

    def test_reject_out_of_range(self):
        with self.assertRaises(ValueError):
            add_numbers(100001, 1)

    def test_notice_found(self):
        self.assertTrue(find_notice("과제 제출")["found"])

    def test_notice_unknown(self):
        self.assertFalse(find_notice("우주선 연료")["found"])

    def test_notice_reject_blank(self):
        with self.assertRaises(ValueError):
            find_notice("   ")

    def test_resource_is_fixed_public_file(self):
        self.assertIn("과제 제출", public_notice())

    def test_prompt_is_template_not_model(self):
        self.assertIn("MCP", lesson_prompt("MCP"))

    def test_prompt_reject_blank(self):
        with self.assertRaises(ValueError):
            lesson_prompt(" ")

    def test_fixture_never_uses_mcp(self):
        with patch("mcp_lesson10_client.run", side_effect=AssertionError("MCP_FORBIDDEN")):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(fixture_main(["add"]), 0)
            self.assertIn("MCP 프로토콜 통신 아님", output.getvalue())

    def test_server_file_exists(self):
        self.assertTrue(SERVER.is_file())

    def test_client_rejects_invalid_before_mcp(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(client_main(["add", "--a", "100001"]), 2)

    def test_client_tool_result_error_is_failure_not_success(self):
        with patch("mcp_lesson10_client.run", side_effect=ToolResultError("tool rejected")):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(client_main(["add"]), 4)
        self.assertIn("Tool 실행 실패", output.getvalue())
        self.assertNotIn("통신 완료", output.getvalue())

    def test_fixture_lists_three_primitives(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(fixture_main(["list"]), 0)
        self.assertIn("[RESOURCES]", output.getvalue())
        self.assertIn("[PROMPTS]", output.getvalue())


if __name__ == "__main__":
    unittest.main()
