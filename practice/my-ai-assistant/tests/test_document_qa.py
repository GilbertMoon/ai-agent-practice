import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from document_qa import DEFAULT_DOC, NO_EVIDENCE, build_grounded_prompt, read_document, retrieve, split_sections, tokenize


class DocumentQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read_document(DEFAULT_DOC)

    def test_document_exists(self):
        self.assertIn("과제 제출 기한", self.document)

    def test_sections(self):
        sections = split_sections(self.document)
        self.assertTrue(any(name == "과제 제출" for name, _ in sections))

    def test_question_retrieves_deadline(self):
        evidence = retrieve(self.document, "과제 제출 기한은 언제인가요?", DEFAULT_DOC.name)
        self.assertTrue(evidence)
        self.assertIn("금요일 오후 6시", evidence[0].text)
        self.assertEqual(evidence[0].source, DEFAULT_DOC.name)

    def test_unknown_query_returns_no_evidence(self):
        self.assertEqual(retrieve(self.document, "우주선 연료는 무엇인가요?", DEFAULT_DOC.name), [])

    def test_blank_query_no_evidence(self):
        self.assertEqual(retrieve(self.document, "  ", DEFAULT_DOC.name), [])

    def test_top_k_limits(self):
        self.assertLessEqual(len(retrieve(self.document, "과제", DEFAULT_DOC.name, 1)), 1)

    def test_prompt_contains_source_and_question(self):
        evidence = retrieve(self.document, "과제 제출 기한은 언제인가요?", DEFAULT_DOC.name)
        prompt = build_grounded_prompt("과제 제출 기한은 언제인가요?", evidence)
        self.assertIn("lesson04_notice.md", prompt)
        self.assertIn("출처=", prompt)
        self.assertIn("금요일 오후 6시", prompt)

    def test_prompt_rejects_no_evidence(self):
        with self.assertRaises(ValueError):
            build_grounded_prompt("질문", [])

    def test_cli_preview_no_api_key(self):
        env = {k: v for k, v in os.environ.items()
               if k not in {"OPENAI_API_KEY", "OPENAI_MODEL", "GEMINI_API_KEY", "GEMINI_MODEL_NAME"}}
        env["PYTHONIOENCODING"] = "utf-8"
        run = subprocess.run(
            [sys.executable, str(ROOT / "document_qa.py"), "과제 제출 기한은 언제인가요?"],
            text=True, capture_output=True, encoding="utf-8", env=env, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("금요일 오후 6시", run.stdout)
        self.assertIn("[PREVIEW]", run.stdout)

    def test_cli_unknown_no_api_calls(self):
        run = subprocess.run(
            [sys.executable, str(ROOT / "document_qa.py"), "우주선 연료는 무엇인가요?", "--mode", "live"],
            text=True, capture_output=True, encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn(NO_EVIDENCE, run.stdout)
        self.assertIn("api_calls=0", run.stdout)

    def test_missing_document_error(self):
        with self.assertRaises(FileNotFoundError):
            read_document(ROOT / "missing_doc_test.md")

    def test_literal_tokenizer(self):
        self.assertIn("제출", tokenize("과제 제출 기한은?"))


if __name__ == "__main__":
    unittest.main()
