import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prompt_compare import build_prompt_pair, compare_live, validate_format
from main import Reply


class SpyClient:
    def __init__(self):
        self.asked = []

    def ask(self, question):
        self.asked.append(question)
        return Reply(text="## 핵심 설명\nA\n## 쉬운 예시\nB\n## 확인할 점\nC",
                     model="fake", input_tokens=1, output_tokens=2,
                     measurement_mode="live")


class CompareTests(unittest.TestCase):
    def test_basic_prompt_preserved(self):
        pair = build_prompt_pair("  AI Agent가 뭐예요?  ")
        self.assertEqual(pair.basic, "AI Agent가 뭐예요?")

    def test_structured_sections_and_question(self):
        p = build_prompt_pair("학습 계획", "내 수업은 월요일")
        self.assertIn("내 수업은 월요일", p.structured)
        self.assertIn("사용자 질문: 학습 계획", p.structured)
        self.assertIn("## 핵심 설명", p.structured)

    def test_empty_question_fails(self):
        with self.assertRaises(ValueError):
            build_prompt_pair(" ")

    def test_length_limit(self):
        with self.assertRaises(ValueError):
            build_prompt_pair("x" * 1001)
        with self.assertRaises(ValueError):
            build_prompt_pair("ok", "x" * 1501)

    def test_format_validation(self):
        got = validate_format("## 핵심 설명\n내용\n## 쉬운 예시\n예시")
        self.assertTrue(got["핵심 설명"])
        self.assertFalse(got["확인할 점"])

    def test_two_live_calls_in_fake_client(self):
        client = SpyClient()
        pair = build_prompt_pair("질문")
        results = compare_live(pair, client)
        self.assertEqual(len(client.asked), 2)
        self.assertEqual(client.asked[0], "질문")
        self.assertEqual(client.asked[1], pair.structured)
        self.assertEqual(len(results), 2)

    def test_preview_cli_needs_no_key(self):
        run = subprocess.run(
            [sys.executable, str(ROOT / "prompt_compare.py"), "질문", "--mode", "preview"],
            text=True, capture_output=True, encoding="utf-8",
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
            check=False,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("[PREVIEW]", run.stdout)
        self.assertIn("## 쉬운 예시", run.stdout)


if __name__ == "__main__":
    unittest.main()
