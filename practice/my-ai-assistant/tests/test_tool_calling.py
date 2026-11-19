"""Lesson 09 tests; Fixture and mock-only, zero external calls."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tool_calling import ToolRequest, validate_arguments, dispatch, fixture_request, run_fixture, main


class ToolCallingTests(unittest.TestCase):
    def test_allowlist(self):
        with self.assertRaisesRegex(ValueError,"허용되지"):
            dispatch(ToolRequest("delete_file","{}"))

    def test_add(self):
        self.assertEqual(dispatch(ToolRequest("add_numbers",'{"a":12,"b":30}'))["sum"],42)

    def test_negative_add(self):
        self.assertEqual(dispatch(ToolRequest("add_numbers",'{"a":-2,"b":4}'))["sum"],2)

    def test_reject_extra_keys(self):
        with self.assertRaises(ValueError):
            validate_arguments("add_numbers",'{"a":1,"b":2,"cmd":"rm"}')

    def test_reject_bool_and_float(self):
        for raw in ('{"a":true,"b":1}','{"a":1.5,"b":2}'):
            with self.assertRaises(ValueError):
                validate_arguments("add_numbers",raw)

    def test_reject_large_integer(self):
        with self.assertRaises(ValueError):
            validate_arguments("add_numbers",'{"a":100001,"b":0}')

    def test_reject_bad_json(self):
        with self.assertRaises(ValueError):
            validate_arguments("find_notice",'{oops}')

    def test_reject_empty_query(self):
        with self.assertRaises(ValueError):
            validate_arguments("find_notice",'{"query":"  "}')

    def test_notice_found_with_source(self):
        result=dispatch(ToolRequest("find_notice",'{"query":"과제 제출"}'))
        self.assertTrue(result["found"])
        self.assertEqual(result["source"],"lesson04_notice.md")

    def test_notice_no_match(self):
        result=dispatch(ToolRequest("find_notice",'{"query":"우주선 연료"}'))
        self.assertFalse(result["found"])

    def test_fixture_rule_is_explicit(self):
        self.assertEqual(fixture_request("12 + 30").name,"add_numbers")
        self.assertEqual(fixture_request("공지 검색: 과제 제출").name,"find_notice")
        self.assertIsNone(fixture_request("자유로운 질문"))

    def test_fixture_no_network(self):
        with patch("tool_calling.run_live",side_effect=AssertionError("NETWORK_FORBIDDEN")):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(["12 + 30"]),0)
            self.assertIn('"sum": 42',out.getvalue())
            self.assertIn("api_calls=0",out.getvalue())

    def test_no_tool_does_not_invent_result(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["날씨 알려줘"]),0)
        self.assertIn("[NO_TOOL]",out.getvalue())

    def test_empty_cli_is_error(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([]),2)

    def test_tool_listing(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["--list-tools"]),0)
        self.assertIn("add_numbers",out.getvalue())
        self.assertIn("find_notice",out.getvalue())


    def _mock_live(self, replies):
        """Mock the SDK so these tests never use real API credentials or network."""
        from tool_calling import run_live
        client = MagicMock()
        client.responses.create.side_effect = replies
        with patch.dict(sys.modules, {"openai": SimpleNamespace(OpenAI=lambda **kw: client)}):
            with patch("tool_calling.load_local_env"):
                with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "test-model"}):
                    with contextlib.redirect_stdout(io.StringIO()) as output:
                        code = run_live("12와 30을 더해 주세요")
        return code, output.getvalue(), client

    def test_live_success_has_execution_evidence(self):
        call = SimpleNamespace(type="function_call", name="add_numbers", arguments='{"a":12,"b":30}', call_id="a1")
        code, output, client = self._mock_live([
            SimpleNamespace(output=[call], output_text="", status="completed", incomplete_details=None, model="test"),
            SimpleNamespace(output=[], output_text="42입니다.", status="completed", incomplete_details=None, model="test"),
        ])
        self.assertEqual(code, 0)
        self.assertIn("[TOOL_EXECUTED] name=add_numbers", output)
        self.assertNotIn("[TOOL_REJECTED]", output)
        self.assertIn('"sum": 42', output)
        self.assertEqual(client.responses.create.call_count, 2)

    def test_live_rejected_name_has_no_execution_evidence(self):
        call = SimpleNamespace(type="function_call", name="delete_file", arguments="{}", call_id="a2")
        code, output, client = self._mock_live([
            SimpleNamespace(output=[call], output_text="", status="completed", incomplete_details=None, model="test"),
            SimpleNamespace(output=[], output_text="도구 거부", status="completed", incomplete_details=None, model="test"),
        ])
        self.assertEqual(code, 0)
        self.assertIn("[TOOL_REJECTED] name=delete_file", output)
        self.assertNotIn("[TOOL_EXECUTED]", output)

    def test_live_invalid_json_arguments_rejected(self):
        call = SimpleNamespace(type="function_call", name="add_numbers", arguments='{"a":true,"b":30}', call_id="a3")
        code, output, _ = self._mock_live([
            SimpleNamespace(output=[call], output_text="", status="completed", incomplete_details=None, model="test"),
            SimpleNamespace(output=[], output_text="입력 오류", status="completed", incomplete_details=None, model="test"),
        ])
        self.assertEqual(code, 0)
        self.assertIn("[TOOL_REJECTED]", output)
        self.assertNotIn("[TOOL_EXECUTED]", output)

    def test_live_incomplete_or_blank_response_holds(self):
        examples = [("completed", "", None), ("incomplete", "미완성", {"reason": "max_output_tokens"})]
        for status, answer, details in examples:
            with self.subTest(status=status, answer=answer):
                code, output, _ = self._mock_live([
                    SimpleNamespace(output=[], output_text=answer, status=status, incomplete_details=details, model="test"),
                ])
                self.assertEqual(code, 4)
                self.assertIn("[LIVE_INCOMPLETE]", output)
                self.assertIn("[HOLD]", output)

    def test_live_step_limit_holds_with_exit_4(self):
        first = SimpleNamespace(type="function_call", name="add_numbers", arguments='{"a":12,"b":30}', call_id="s1")
        again = SimpleNamespace(type="function_call", name="add_numbers", arguments='{"a":1,"b":2}', call_id="s2")
        code, output, client = self._mock_live([
            SimpleNamespace(output=[first], output_text="", status="completed", incomplete_details=None, model="test"),
            SimpleNamespace(output=[again], output_text="", status="completed", incomplete_details=None, model="test"),
        ])
        self.assertEqual(code, 4)  # HOLD must not exit 0 (success)
        self.assertIn("[HOLD]", output)
        self.assertEqual(output.count("[TOOL_EXECUTED]"), 1)  # the request at the step limit is not executed
        self.assertNotIn("call_id=s2", output)
        self.assertEqual(client.responses.create.call_count, 2)

    def test_live_too_many_tool_calls_holds_with_exit_4(self):
        calls = [SimpleNamespace(type="function_call", name="add_numbers", arguments='{"a":1,"b":2}', call_id=f"m{i}")
                 for i in range(4)]
        code, output, client = self._mock_live([
            SimpleNamespace(output=calls, output_text="", status="completed", incomplete_details=None, model="test"),
        ])
        self.assertEqual(code, 4)
        self.assertIn("[HOLD]", output)
        self.assertNotIn("[TOOL_EXECUTED]", output)
        self.assertEqual(client.responses.create.call_count, 1)


if __name__=="__main__":
    unittest.main()
