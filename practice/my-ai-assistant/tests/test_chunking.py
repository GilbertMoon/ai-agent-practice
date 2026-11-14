"""Lesson 07 offline chunking tests. Do not invoke provider API."""
import unittest
from unittest.mock import patch
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from chunking import split_chunks, hit_at_k, collection_name, main, DEFAULT_DOC


class ChunkingTests(unittest.TestCase):
    def setUp(self):
        self.text = DEFAULT_DOC.read_text(encoding="utf-8")

    def test_fixed_preserves_all_characters(self):
        chunks = split_chunks(self.text, "sample.md", "fixed", 100)
        self.assertEqual("".join(c.text for c in chunks), self.text)

    def test_overlap_adjacent_range(self):
        chunks = split_chunks(self.text, "sample.md", "overlap", 100, 20)
        self.assertTrue(len(chunks) > 1)
        self.assertEqual(chunks[0].text[-20:], chunks[1].text[:20])

    def test_paragraphs_preserve_source_offsets(self):
        chunks = split_chunks(self.text, "sample.md", "paragraph")
        self.assertTrue(len(chunks) >= 4)
        for chunk in chunks:
            self.assertEqual(chunk.text, self.text[chunk.start:chunk.end])

    def test_stable_ids(self):
        a = split_chunks(self.text, "sample.md", "fixed", 160)
        b = split_chunks(self.text, "sample.md", "fixed", 160)
        self.assertEqual([x.id for x in a], [x.id for x in b])

    def test_rejects_invalid_size_and_overlap(self):
        with self.assertRaises(ValueError):
            split_chunks(self.text, "sample.md", "overlap", 50, 50)
        with self.assertRaises(ValueError):
            split_chunks(self.text, "sample.md", "fixed", 10)

    def test_collections_are_isolated(self):
        self.assertNotEqual(collection_name("fixture", "fixed", 160, 30), collection_name("fixture", "paragraph", 160, 30))
        self.assertNotEqual(collection_name("fixture", "paragraph", 160, 30), collection_name("live", "paragraph", 160, 30))

    def test_hit_at_k_is_exact_phrase_only(self):
        self.assertEqual(hit_at_k([{"text": "금요일 오후 6시"}], "금요일 오후 6시"), 1)
        self.assertEqual(hit_at_k([{"text": "금요일 오후 6시"}], "월요일"), 0)

    def test_preview_no_client_no_network(self):
        with patch("chunking.create_client", side_effect=AssertionError("NETWORK_FORBIDDEN")), patch("chunking.live_vectors", side_effect=AssertionError("NETWORK_FORBIDDEN")):
            self.assertEqual(main(["preview", "--strategy", "fixed", "--size", "100"]), 0)

    def test_rejects_bad_cli(self):
        self.assertEqual(main(["query", "--strategy", "paragraph"]), 2)
        self.assertEqual(main(["preview", "--strategy", "overlap", "--size", "40", "--overlap", "40"]), 2)


if __name__ == "__main__":
    unittest.main()
