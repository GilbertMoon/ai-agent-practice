import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UTF8_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}  # Windows cp949 콘솔에서도 한글 출력 검증
sys.path.insert(0, str(ROOT))
from main import FallbackClient, MockClient, Reply, make_client, run


class FailingClient:
    def __init__(self, exc: Exception):
        self.exc = exc

    def ask(self, question: str) -> Reply:
        raise self.exc


class FoundationTests(unittest.TestCase):
    def test_mock_reply_is_not_real_api(self):
        reply = run("안녕하세요", MockClient())
        self.assertIn("[MOCK 예시]", reply.text)
        self.assertEqual(reply.measurement_mode, "mock")
        self.assertIsNone(reply.input_tokens)

    def test_blank_question_rejected(self):
        with self.assertRaises(ValueError):
            run("  ", MockClient())

    def test_no_api_key_needed_for_mock(self):
        self.assertIsInstance(make_client("mock"), MockClient)

    def test_live_mode_missing_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
            make_client("live", api_key="", model="test-model")

    def test_live_mode_missing_model_rejected(self):
        with self.assertRaisesRegex(ValueError, "OPENAI_MODEL"):
            make_client("live", api_key="fake", model="")

    def test_gemini_missing_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "GEMINI_API_KEY"):
            make_client("live", api_key="", model="test-model", provider="gemini")

    def test_gemini_missing_model_rejected(self):
        with self.assertRaisesRegex(ValueError, "GEMINI_MODEL_NAME"):
            make_client("live", api_key="fake", model="", provider="gemini")

    def test_fallback_used_when_primary_api_fails(self):
        client = FallbackClient(FailingClient(ConnectionError("down")), MockClient)
        reply = run("안녕하세요", client)
        self.assertIn("[MOCK 예시]", reply.text)
        self.assertEqual(reply.fallback_reason, "ConnectionError")

    def test_fallback_not_used_when_primary_succeeds(self):
        def never():
            raise AssertionError("secondary must not be created")
        reply = run("안녕하세요", FallbackClient(MockClient(), never))
        self.assertIsNone(reply.fallback_reason)

    def test_fallback_does_not_hide_config_errors(self):
        client = FallbackClient(FailingClient(ValueError("설정 오류")), MockClient)
        with self.assertRaises(ValueError):
            run("안녕하세요", client)

    def test_fallback_reports_primary_failure_when_secondary_misconfigured(self):
        def missing_key():
            raise ValueError("GEMINI_API_KEY를 설정해야 합니다.")
        client = FallbackClient(FailingClient(ConnectionError("down")), missing_key)
        with self.assertRaisesRegex(ValueError, r"1순위 호출 실패\(ConnectionError\).*GEMINI_API_KEY"):
            run("안녕하세요", client)

    def test_unsupported_mode(self):
        with self.assertRaises(ValueError):
            make_client("unsupported")

    def test_mock_cli(self):
        p = subprocess.run([sys.executable, str(ROOT / "main.py"), "과제 일정"],
                           capture_output=True, text=True, encoding="utf-8", env=UTF8_ENV, check=False)
        self.assertEqual(p.returncode, 0)
        self.assertIn("과제 일정", p.stdout)
        self.assertIn("mode=mock", p.stderr)

    def test_cli_rejects_empty(self):
        p = subprocess.run([sys.executable, str(ROOT / "main.py"), " "],
                           capture_output=True, text=True, encoding="utf-8", env=UTF8_ENV, check=False)
        self.assertEqual(p.returncode, 2)
        self.assertIn("ERROR", p.stderr)


if __name__ == "__main__":
    unittest.main()
