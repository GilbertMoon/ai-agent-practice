"""Lesson 08 evaluation tests: no network, no provider API."""
import io
import contextlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from chunking import split_chunks
from rag_quality import rank_chunks, gold_rank, extract_evidence, evaluate_cases, load_cases, main, DEFAULT_DOC, DEFAULT_CASES


class RagQualityTests(unittest.TestCase):
    def setUp(self):
        source = DEFAULT_DOC.read_text(encoding="utf-8")
        self.chunks = split_chunks(source, DEFAULT_DOC.name, "paragraph")

    def test_gold_rank_and_reciprocal(self):
        rows = rank_chunks("과제 마감일", self.chunks)
        rank = gold_rank(rows, "금요일 오후 6시")
        self.assertIsNotNone(rank)
        self.assertGreaterEqual(rank, 1)
        self.assertLessEqual(rank, 3)

    def test_no_gold_match_is_not_answer(self):
        rows = rank_chunks("과제 마감일", self.chunks)
        self.assertIsNone(extract_evidence(rows, "이 문구는 없습니다"))

    def test_out_of_domain_fixture_returns_no_results(self):
        self.assertEqual(rank_chunks("우주선 연료", self.chunks), [])

    def test_evaluation_labels_answerability(self):
        data = load_cases(DEFAULT_CASES)
        metrics = evaluate_cases(data, self.chunks)
        self.assertEqual(len(metrics), 4)
        self.assertIsNone(metrics[-1]["hit"])
        self.assertFalse(metrics[-1]["expected_answerable"])

    def test_empty_query_rejected(self):
        with self.assertRaises(ValueError):
            rank_chunks(" ", self.chunks)

    def test_bad_top_k_rejected(self):
        with self.assertRaises(ValueError):
            rank_chunks("과제", self.chunks, top_k=0)

    def test_offline_evaluation_never_calls_api(self):
        with patch("rag_quality.live_vectors", side_effect=AssertionError("NO_NETWORK")), patch("rag_quality.make_client", side_effect=AssertionError("NO_NETWORK")):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                result = main(["evaluate"])
            self.assertEqual(result, 0)
            self.assertIn("[SUMMARY]", out.getvalue())

    def test_preview_requires_exact_evidence(self):
        with patch("rag_quality.make_client", side_effect=AssertionError("NO_NETWORK")):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                result = main(["preview", "과제 마감일", "--gold", "이 문구는 없습니다"])
            self.assertEqual(result, 0)
            self.assertIn("[NO_EVIDENCE]", out.getvalue())

    def test_hit_rr_and_mrr_follow_gold_rank(self):
        cases = load_cases(DEFAULT_CASES)
        at3 = evaluate_cases(cases, self.chunks, top_k=3)
        at1 = evaluate_cases(cases, self.chunks, top_k=1)
        answerable = [x for x in at3 if x["expected_answerable"]]
        self.assertEqual(len(answerable), 3)
        for wide, narrow in zip(at3, at1):
            if not wide["expected_answerable"]:
                continue
            rank = wide["gold_rank"]
            self.assertEqual(wide["hit"], int(rank is not None))
            self.assertAlmostEqual(wide["reciprocal_rank"], 1.0 / rank if rank else 0.0)
            self.assertEqual(narrow["hit"], int(rank == 1))
        expected_mrr = sum(x["reciprocal_rank"] for x in answerable) / len(answerable)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["evaluate"]), 0)
        self.assertIn(f"mrr={expected_mrr:.3f}", out.getvalue())

    def test_extract_evidence_is_exact_source_span(self):
        source = DEFAULT_DOC.read_text(encoding="utf-8")
        rows = rank_chunks("과제 마감일", self.chunks)
        self.assertTrue(rows)
        phrase, row = extract_evidence(rows, "금요일 오후 6시")
        self.assertEqual(phrase, "금요일 오후 6시")
        self.assertEqual(source[row.start:row.end], row.text)
        self.assertIn(phrase, row.text)

    def test_lesson07_chunking_is_reused_unchanged(self):
        import chunking
        import rag_quality
        self.assertIs(rag_quality.split_chunks, chunking.split_chunks)
        self.assertEqual(rag_quality.DEFAULT_DOC, chunking.DEFAULT_DOC)
        source = DEFAULT_DOC.read_text(encoding="utf-8")
        for strategy in ("fixed", "paragraph", "overlap"):
            chunks = split_chunks(source, DEFAULT_DOC.name, strategy, 160, 30)
            self.assertTrue(chunks)
            for chunk in chunks:
                self.assertEqual(source[chunk.start:chunk.end], chunk.text)

    def test_generate_requires_explicit_live(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            result = main(["generate", "과제 마감일", "--gold", "금요일 오후 6시"])
        self.assertEqual(result, 2)
        self.assertIn("mode live", out.getvalue())


if __name__ == "__main__":
    unittest.main()
