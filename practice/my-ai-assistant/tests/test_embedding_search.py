import contextlib
import io
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from embedding_search import (
    cosine_similarity, fixture_vector, rank_sections, live_vectors,
    main as embedding_main,
)
from document_qa import DEFAULT_DOC, read_document, retrieve, split_sections


class EmbeddingSearchTests(unittest.TestCase):
    def test_cosine_identical(self):
        self.assertAlmostEqual(cosine_similarity([1,2], [1,2]), 1)

    def test_cosine_orthogonal(self):
        self.assertEqual(cosine_similarity([1,0], [0,1]), 0)

    def test_zero_vector(self):
        self.assertEqual(cosine_similarity([0,0], [3,4]), 0)

    def test_invalid_vector_dimensions(self):
        with self.assertRaises(ValueError):
            cosine_similarity([1], [1,2])

    def test_fixture_synonym_mapping(self):
        self.assertGreater(fixture_vector("마감일")[0], 0)
        self.assertGreater(fixture_vector("제출 기한")[0], 0)

    def test_keyword_misses_but_fixture_finds(self):
        doc = read_document(DEFAULT_DOC)
        query = "마감일"
        self.assertEqual(retrieve(doc, query, DEFAULT_DOC.name), [])
        sections = split_sections(doc)
        matches = rank_sections(
            sections, fixture_vector(query),
            [fixture_vector(name+" "+body) for name,body in sections])
        self.assertTrue(matches)
        self.assertEqual(matches[0].section, "과제 제출")

    def test_no_similarity_for_unrelated_query(self):
        doc = read_document(DEFAULT_DOC)
        sections = split_sections(doc)
        matches = rank_sections(
            sections, fixture_vector("우주선 연료"),
            [fixture_vector(name+" "+body) for name,body in sections])
        self.assertEqual(matches, [])

    def test_section_vector_mismatch(self):
        with self.assertRaises(ValueError):
            rank_sections([("one","doc")], [1.0], [])

    def test_fixture_cli_has_no_network(self):
        output = io.StringIO()
        with patch("embedding_search.live_vectors", side_effect=AssertionError("NO_API")) as api, \
             contextlib.redirect_stdout(output):
            exit_code = embedding_main(["마감일", "--mode", "fixture"])
        self.assertEqual(exit_code, 0)
        self.assertIn("학습용 수동 벡터", output.getvalue())
        api.assert_not_called()

    def test_live_missing_model_has_no_api_call(self):
        with patch("embedding_search.load_local_env"), \
             patch("embedding_search.live_vectors", side_effect=ValueError("no model")):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(embedding_main(["마감일", "--mode", "live"]), 2)

    def test_top_k_error(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(embedding_main(["마감일", "--top-k", "0"]), 2)


if __name__ == "__main__":
    unittest.main()
