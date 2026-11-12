"""Lesson 06 offline integration tests: real persistent Chroma, no provider API."""
import contextlib
import gc
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vector_store import create_client, get_collection, index_document, query_document, main as store_main


class VectorStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Chroma 1.x keeps SQLite/HNSW file handles in a shared client cache.
        # unittest runs cleanups LIFO: release handles before removing temp dir.
        self.addCleanup(self._release_chroma)
        self.folder = Path(self.temp.name)

    @staticmethod
    def _release_chroma():
        from chromadb.api.client import SharedSystemClient
        SharedSystemClient.clear_system_cache()
        gc.collect()

    def test_fixture_index_stores_three_sections(self):
        collection = get_collection(create_client(self.folder), "fixture")
        self.assertEqual(index_document(collection, "fixture", ""), 3)
        self.assertEqual(collection.count(), 3)
        records = collection.get(include=["documents", "metadatas"])
        self.assertEqual(set(records["ids"]), {"notice-01", "notice-02", "notice-03"})
        self.assertEqual({m["source"] for m in records["metadatas"]}, {"lesson04_notice.md"})

    def test_reopen_preserves_rows_without_reembedding(self):
        initial = get_collection(create_client(self.folder), "fixture")
        index_document(initial, "fixture", "")
        reopened = get_collection(create_client(self.folder), "fixture")
        self.assertEqual(reopened.count(), 3)
        matches = query_document(reopened, "마감일", "fixture", "", 2)
        self.assertTrue(matches)
        self.assertEqual(matches[0]["section"], "과제 제출")

    def test_second_index_is_idempotent(self):
        collection = get_collection(create_client(self.folder), "fixture")
        self.assertEqual(index_document(collection, "fixture", ""), 3)
        self.assertEqual(index_document(collection, "fixture", ""), 3)

    def test_metadata_and_distance_are_returned(self):
        collection = get_collection(create_client(self.folder), "fixture")
        index_document(collection, "fixture", "")
        results = query_document(collection, "문의 게시판", "fixture", "", 2)
        self.assertTrue(results)
        self.assertEqual(results[0]["section"], "질문 응대")
        self.assertEqual(results[0]["source"], "lesson04_notice.md")
        self.assertIsInstance(results[0]["distance"], float)

    def test_unknown_fixture_query_does_not_call_api(self):
        collection = get_collection(create_client(self.folder), "fixture")
        index_document(collection, "fixture", "")
        with patch("vector_store.live_vectors", side_effect=AssertionError("NETWORK_FORBIDDEN")) as call:
            self.assertEqual(query_document(collection, "우주선 연료", "fixture", "", 2), [])
            call.assert_not_called()

    def test_requires_index_first(self):
        collection = get_collection(create_client(self.folder), "fixture")
        with self.assertRaisesRegex(ValueError, "index"):
            query_document(collection, "마감일", "fixture", "", 2)

    def test_live_model_mismatch_before_api(self):
        live = get_collection(create_client(self.folder), "live", "first-model")
        self.assertEqual(live.count(), 0)
        with patch("vector_store.live_vectors", side_effect=AssertionError("NETWORK_FORBIDDEN")) as call:
            with self.assertRaisesRegex(ValueError, "모델/모드"):
                get_collection(create_client(self.folder), "live", "another-model")
            call.assert_not_called()

    def test_cli_fixture_index_and_query_without_api(self):
        with patch("vector_store.live_vectors", side_effect=AssertionError("NETWORK_FORBIDDEN")) as call:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(store_main(["index", "--store", str(self.folder)]), 0)
                self.assertEqual(store_main(["count", "--store", str(self.folder)]), 0)
                self.assertEqual(store_main(["query", "마감일", "--store", str(self.folder)]), 0)
            self.assertIn("[INDEX]", output.getvalue())
            self.assertIn("[COUNT]", output.getvalue())
            self.assertIn("[QUERY]", output.getvalue())
            call.assert_not_called()

    def test_invalid_cli_rejected(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(store_main(["query", "--store", str(self.folder)]), 2)
            self.assertEqual(store_main(["index", "--top-k", "0", "--store", str(self.folder)]), 2)

    def test_live_requires_config_without_api(self):
        with patch("vector_store.load_local_env"), patch.dict(os.environ, {}, clear=True), patch(
            "vector_store.live_vectors", side_effect=AssertionError("NETWORK_FORBIDDEN")
        ) as call:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                result = store_main(["index", "--mode", "live", "--store", str(self.folder)])
            self.assertEqual(result, 2)
            self.assertIn("OPENAI_EMBEDDING_MODEL", output.getvalue())
            call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
