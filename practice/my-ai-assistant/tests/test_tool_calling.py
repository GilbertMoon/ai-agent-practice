"""Lesson 09 tests; Fixture and mock-only, zero external calls."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

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


if __name__=="__main__":
    unittest.main()
