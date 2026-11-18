"""Lesson 07 tests for lesson07_pgvector.py (PostgreSQL + pgvector chunking).

Offline tests need no database and never call the OpenAI API.

Database tests run only when the DB_* settings (.env or environment) reach a PostgreSQL
server with pgvector. They work inside a temporary schema ``lesson07_test_<random>`` that
is selected with PGOPTIONS search_path and dropped at the end, so the existing
``lesson06_*`` and ``lesson07_*`` tables are never written. Existing lesson06_* tables are
only counted before and after to prove they were not changed. Set LESSON07_SKIP_DB=1 to
skip the database tests; when the database is unreachable they are reported as skipped.
"""
import contextlib
import io
import os
import re
import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import lesson07_pgvector as l7  # noqa: E402

TEXT = l7.SOURCE.read_text(encoding="utf-8")
GOLD = "금요일 오후 6시"


def make_args(**kw):
    base = dict(command="preview", question=None, strategy="fixed", size=160, overlap=0,
                top_k=3, mode="fixture")
    base.update(kw)
    return SimpleNamespace(**base)


def run_cli(*argv, extra_env=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.update(extra_env or {})
    return subprocess.run([sys.executable, str(ROOT / "lesson07_pgvector.py"), *argv], cwd=ROOT, env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=120)


class ChunkingOfflineTests(unittest.TestCase):
    def test_fixed_chunks_cover_source_in_order(self):
        chunks = l7.split_chunks(TEXT, "fixed", 160, 0)
        self.assertEqual("".join(c for _, _, c in chunks), TEXT)
        for i, (start, end, content) in enumerate(chunks):
            self.assertEqual(start, i * 160)
            self.assertEqual(TEXT[start:end], content)
            self.assertLessEqual(len(content), 160)

    def test_paragraph_chunks_are_blank_line_blocks_with_offsets(self):
        chunks = l7.split_chunks(TEXT, "paragraph", 160, 0)
        expected = [p for p in TEXT.split("\n\n") if p.strip()]
        self.assertEqual([c for _, _, c in chunks], expected)
        for start, end, content in chunks:
            self.assertEqual(TEXT[start:end], content)

    def test_overlap_chunks_share_exact_overlap(self):
        chunks = l7.split_chunks(TEXT, "overlap", 160, 30)
        self.assertGreater(len(chunks), 1)
        for i, (start, end, content) in enumerate(chunks):
            self.assertEqual(start, i * 130)
            self.assertEqual(TEXT[start:end], content)
        for (s1, e1, c1), (s2, _, c2) in zip(chunks, chunks[1:]):
            if e1 - s1 == 160:
                self.assertEqual(c1[-30:], c2[:30])

    def test_invalid_size_or_overlap_rejected(self):
        for size, overlap in ((0, 0), (40, 40), (160, 200), (160, -1)):
            with self.assertRaises(ValueError):
                l7.split_chunks(TEXT, "overlap", size, overlap)

    def test_settings_key_and_chunk_id_are_stable_and_distinct(self):
        key = l7.settings_key(make_args(strategy="fixed", size=160, overlap=0))
        self.assertEqual(key, "fixed:size=160:overlap=0")
        cid = l7.make_id(key, 0, 160)
        self.assertRegex(cid, r"^[0-9a-f]{20}$")
        self.assertEqual(cid, l7.make_id(key, 0, 160))
        self.assertNotEqual(cid, l7.make_id(key, 160, 320))
        self.assertNotEqual(cid, l7.make_id("overlap:size=160:overlap=30", 0, 160))
        for strategy, overlap in (("fixed", 0), ("paragraph", 0), ("overlap", 30)):
            k = l7.settings_key(make_args(strategy=strategy, overlap=overlap))
            ids = [l7.make_id(k, s, e) for s, e, _ in l7.split_chunks(TEXT, strategy, 160, overlap)]
            self.assertEqual(len(ids), len(set(ids)))

    def test_fixture_vector_counts_keywords_and_zero_vector(self):
        self.assertEqual(l7.fixture_vector("과제 마감일"), [1.0, 1.0, 0.0])
        self.assertEqual(l7.fixture_vector("과제 제출 과제"), [2.0, 0.0, 1.0])
        self.assertEqual(l7.fixture_vector("질문 게시판"), [0.0, 0.0, 0.0])
        self.assertEqual(l7.vector_literal([1, 0.5, 0]), "[1.0,0.5,0.0]")

    def test_zero_question_vector_never_queries_database(self):
        with patch.object(l7, "connect", side_effect=AssertionError("DB must not be used")):
            self.assertIsNone(l7.search(make_args(question="API Key 보안")))

    def test_preview_uses_no_database_or_network(self):
        out = io.StringIO()
        with patch.object(l7, "connect", side_effect=AssertionError("NO_DB")), \
                patch.object(l7, "live_vectors", side_effect=AssertionError("NO_NETWORK")), \
                patch.object(sys, "argv", ["lesson07_pgvector.py", "preview", "--strategy", "overlap",
                                           "--size", "160", "--overlap", "30"]), \
                contextlib.redirect_stdout(out):
            l7.main()
        lines = [x for x in out.getvalue().splitlines() if x.startswith("chunk=")]
        self.assertEqual(len(lines), len(l7.split_chunks(TEXT, "overlap", 160, 30)))

    def test_cli_input_errors(self):
        r = run_cli("query", "--strategy", "paragraph")
        self.assertEqual(r.returncode, 2)
        self.assertIn("query 뒤에 질문을 입력하세요", r.stderr)
        r = run_cli("evaluate", "--top-k", "0")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--top-k는 1 이상이어야 합니다", r.stderr)
        r = run_cli("preview", "--strategy", "semantic")
        self.assertEqual(r.returncode, 2)
        r = run_cli("preview", "--strategy", "overlap", "--size", "40", "--overlap", "40")
        self.assertEqual(r.returncode, 1)
        self.assertIn("ValueError", r.stderr)


def _db_reason():
    if os.getenv("LESSON07_SKIP_DB") == "1":
        return "LESSON07_SKIP_DB=1"
    try:
        with l7.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_available_extensions WHERE name='vector'")
            if not cur.fetchone():
                return "pgvector extension is not available"
    except Exception as exc:  # noqa: BLE001 - any connection problem means "not available"
        return f"PostgreSQL not reachable ({type(exc).__name__})"
    return ""


class PgvectorDatabaseTests(unittest.TestCase):
    """Runs in a temporary schema; never writes lesson06_* / lesson07_* tables."""

    @classmethod
    def setUpClass(cls):
        reason = _db_reason()
        if reason:
            raise unittest.SkipTest(reason)
        cls.schema = "lesson07_test_" + uuid.uuid4().hex[:10]
        cls.old_pgoptions = os.environ.get("PGOPTIONS")
        with l7.connect() as conn, conn.cursor() as cur:
            cls.lesson06_before = cls._lesson06_counts(cur)
            cur.execute(f"CREATE SCHEMA {cls.schema}")
        os.environ["PGOPTIONS"] = f"-c search_path={cls.schema},public"

    @classmethod
    def tearDownClass(cls):
        if cls.old_pgoptions is None:
            os.environ.pop("PGOPTIONS", None)
        else:
            os.environ["PGOPTIONS"] = cls.old_pgoptions
        with l7.connect() as conn, conn.cursor() as cur:
            cur.execute(f"DROP SCHEMA IF EXISTS {cls.schema} CASCADE")

    @staticmethod
    def _lesson06_counts(cur):
        cur.execute("""SELECT table_schema, table_name FROM information_schema.tables
                       WHERE table_name LIKE 'lesson06%' AND table_schema NOT LIKE 'lesson07_test_%'
                       ORDER BY 1, 2""")
        counts = {}
        for schema, table in cur.fetchall():
            cur.execute(f'SELECT count(*) FROM "{schema}"."{table}"')
            counts[f"{schema}.{table}"] = cur.fetchone()[0]
        return counts

    def sql(self, query, params=()):
        with l7.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT current_schema()")
            self.assertEqual(cur.fetchone()[0], self.schema)  # never the real lesson tables
            cur.execute(query, params)
            return cur.fetchall()

    def index(self, *setting):
        r = run_cli("index", *setting)
        self.assertEqual(r.returncode, 0, r.stderr)
        return int(re.search(r"count=(\d+)", r.stdout).group(1))

    def test_index_count_and_reindex_without_duplicates(self):
        for strategy, size, overlap in (("fixed", 160, 0), ("paragraph", 160, 0), ("overlap", 160, 30)):
            setting = ("--strategy", strategy, "--size", str(size), "--overlap", str(overlap))
            expected = len(l7.split_chunks(TEXT, strategy, size, overlap))
            self.assertEqual(self.index(*setting), expected)
            self.assertEqual(self.index(*setting), expected)  # second run replaces, not appends
            key = f"{strategy}:size={size}:overlap={overlap}"
            rows = self.sql("SELECT count(*), count(DISTINCT id), min(ordinal), max(ordinal) "
                            "FROM lesson07_fixture_chunks WHERE strategy=%s", (key,))
            self.assertEqual(rows[0], (expected, expected, 0, expected - 1))
            r = run_cli("count", *setting)
            self.assertIn(f"COUNT {expected}", r.stdout)

    def test_reindex_keeps_other_settings(self):
        n_par = self.index("--strategy", "paragraph")
        self.index("--strategy", "fixed", "--size", "160")
        self.index("--strategy", "fixed", "--size", "160")
        rows = self.sql("SELECT count(*) FROM lesson07_fixture_chunks WHERE strategy='paragraph:size=160:overlap=0'")
        self.assertEqual(rows[0][0], n_par)

    def test_metadata_matches_source_ranges(self):
        self.index("--strategy", "overlap", "--size", "160", "--overlap", "30")
        rows = self.sql("SELECT id, strategy, source, start_pos, end_pos, ordinal, content FROM lesson07_fixture_chunks "
                        "WHERE strategy='overlap:size=160:overlap=30' ORDER BY ordinal")
        for cid, key, source, start, end, ordinal, content in rows:
            self.assertEqual(source, "lesson07_long_notice.md")
            self.assertEqual(TEXT[start:end], content)
            self.assertEqual(cid, l7.make_id(key, start, end))

    def test_query_in_new_process_after_index(self):
        self.index("--strategy", "fixed", "--size", "160")  # process 1 ends here
        r = run_cli("query", "과제 마감일", "--strategy", "fixed", "--size", "160", "--top-k", "3")  # process 2
        self.assertEqual(r.returncode, 0, r.stderr)
        distances = [float(x) for x in re.findall(r"distance=([0-9.]+)", r.stdout)]
        self.assertTrue(1 <= len(distances) <= 3)
        self.assertEqual(distances, sorted(distances))
        self.assertIn("lesson07_long_notice.md[", r.stdout)

    def test_zero_vector_chunks_are_stored_but_not_returned(self):
        self.index("--strategy", "fixed", "--size", "160")
        key = "fixed:size=160:overlap=0"
        zero = self.sql("SELECT count(*) FROM lesson07_fixture_chunks WHERE strategy=%s AND vector_norm(embedding)=0", (key,))
        nonzero = self.sql("SELECT count(*) FROM lesson07_fixture_chunks WHERE strategy=%s AND vector_norm(embedding)>0", (key,))
        self.assertGreater(zero[0][0], 0)
        rows = l7.search(make_args(question="과제 마감일", strategy="fixed", size=160, overlap=0, top_k=10))
        self.assertEqual(len(rows), nonzero[0][0])
        self.assertTrue(all(any(w in row[4] for w in l7.KEYWORDS) for row in rows))
        r = run_cli("query", "질문 게시판", "--strategy", "fixed", "--size", "160")
        self.assertIn("검색 불가", r.stdout)

    def test_hit_at_1_and_hit_at_3_fixture_baseline(self):
        # Regression baseline: measured Fixture output of the unchanged Lesson 07 code.
        cases = [(("--strategy", "fixed", "--size", "160"), 2),
                 (("--strategy", "paragraph"), 2),
                 (("--strategy", "overlap", "--size", "160", "--overlap", "30"), 2),
                 (("--strategy", "overlap", "--size", "160", "--overlap", "60"), 3)]
        for setting, first_rank in cases:
            self.index(*setting)
            r3 = run_cli("evaluate", *setting, "--top-k", "3")
            r1 = run_cli("evaluate", *setting, "--top-k", "1")
            self.assertIn("Hit@3=1", r3.stdout, setting)
            self.assertIn(f"정답 문구 첫 등장 순위: {first_rank}", r3.stdout, setting)
            self.assertIn("Hit@1=0", r1.stdout, setting)
            rows = l7.search(make_args(question="과제 마감일", strategy=setting[1],
                                       size=int(setting[3]) if len(setting) > 2 else 160,
                                       overlap=int(setting[5]) if len(setting) > 4 else 0, top_k=3))
            ranks = [i for i, row in enumerate(rows, start=1) if GOLD in row[4]]
            self.assertEqual(ranks[0], first_rank)

    def test_lesson06_tables_unchanged(self):
        self.index("--strategy", "fixed", "--size", "160")
        with l7.connect() as conn, conn.cursor() as cur:
            self.assertEqual(self._lesson06_counts(cur), self.lesson06_before)


if __name__ == "__main__":
    unittest.main()
