"""Lesson 07: 로컬 PostgreSQL + pgvector 청킹 실습 (Python 3.12)."""
import argparse
import hashlib
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "data" / "lesson07_long_notice.md"
TABLES = {"fixture": "lesson07_fixture_chunks", "live": "lesson07_live_chunks"}
KEYWORDS = ("과제", "마감", "제출")


def connect():
    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError("누락된 .env 항목: " + ", ".join(missing))
    return psycopg.connect(
        host=os.environ["DB_HOST"], port=int(os.environ["DB_PORT"]),
        dbname=os.environ["DB_NAME"], user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"], connect_timeout=5
    )


def split_chunks(text, strategy, size, overlap):
    if size < 1 or overlap < 0 or overlap >= size:
        raise ValueError("size는 양수이고 overlap은 0 이상 size 미만이어야 합니다.")
    if strategy == "paragraph":
        result, pos = [], 0
        for part in text.split("\n\n"):
            start = text.find(part, pos)
            if start >= 0 and part.strip():
                result.append((start, start + len(part), part))
                pos = start + len(part)
        return result
    stride = size - overlap if strategy == "overlap" else size
    return [(i, min(i + size, len(text)), text[i:i + size])
            for i in range(0, len(text), stride)]


def fixture_vector(text):
    # 교육용 수동 특징 벡터: 실제 의미 임베딩이 아님
    # 세 키워드가 하나도 없으면 [0, 0, 0]입니다. 0벡터는 방향이 없어
    # 코사인 거리를 계산할 수 없으므로 search()에서 검색 대상에서 제외합니다.
    return [float(text.count(word)) for word in KEYWORDS]


def live_vectors(texts):
    from openai import OpenAI
    response = OpenAI().embeddings.create(
        model="text-embedding-3-small", input=texts
    )
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


def vector_literal(numbers):
    return "[" + ",".join(str(float(x)) for x in numbers) + "]"


def ensure_table(cur, mode):
    # 이번 강의 테이블만 생성; 6강 테이블은 수정하지 않음
    table = TABLES[mode]
    dim = 3 if mode == "fixture" else 1536
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute(f"""CREATE TABLE IF NOT EXISTS {table} (
        id TEXT PRIMARY KEY,
        strategy TEXT NOT NULL,
        source TEXT NOT NULL,
        start_pos INTEGER NOT NULL,
        end_pos INTEGER NOT NULL,
        ordinal INTEGER NOT NULL,
        content TEXT NOT NULL,
        embedding VECTOR({dim}) NOT NULL
    )""")


def settings_key(args):
    return f"{args.strategy}:size={args.size}:overlap={args.overlap}"


def make_id(setting, start, end):
    return hashlib.sha256(f"{setting}:{start}:{end}".encode()).hexdigest()[:20]


def build_chunks(args):
    if not SOURCE.is_file():
        raise FileNotFoundError(f"실습 문서가 없습니다: {SOURCE}")
    return split_chunks(SOURCE.read_text(encoding="utf-8"),
                        args.strategy, args.size, args.overlap)


def index(args):
    chunks = build_chunks(args)
    texts = [text for _, _, text in chunks]
    vectors = ([fixture_vector(text) for text in texts] if args.mode == "fixture"
               else live_vectors(texts))
    table, key = TABLES[args.mode], settings_key(args)
    with connect() as conn:
        with conn.cursor() as cur:
            ensure_table(cur, args.mode)
            cur.execute(f"DELETE FROM {table} WHERE strategy = %s", (key,))
            for idx, ((start, end, content), vector) in enumerate(zip(chunks, vectors)):
                cur.execute(
                    f"""INSERT INTO {table}
                    (id,strategy,source,start_pos,end_pos,ordinal,content,embedding)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::vector)
                    ON CONFLICT(id) DO UPDATE SET
                    strategy=EXCLUDED.strategy, source=EXCLUDED.source,
                    start_pos=EXCLUDED.start_pos, end_pos=EXCLUDED.end_pos,
                    ordinal=EXCLUDED.ordinal, content=EXCLUDED.content,
                    embedding=EXCLUDED.embedding""",
                    (make_id(key,start,end),key,SOURCE.name,start,end,idx,
                     content,vector_literal(vector))
                )
    print(f"INDEX mode={args.mode} strategy={key} count={len(chunks)}")


def count(args):
    with connect() as conn:
        with conn.cursor() as cur:
            ensure_table(cur, args.mode)
            cur.execute(f"SELECT count(*) FROM {TABLES[args.mode]} WHERE strategy=%s",
                        (settings_key(args),))
            print("COUNT", cur.fetchone()[0])


def search(args):
    query_vector = (fixture_vector(args.question) if args.mode == "fixture"
                    else live_vectors([args.question])[0])
    if not any(query_vector):
        return None  # 질문이 0벡터이면 코사인 거리를 계산할 수 없음
    table = TABLES[args.mode]
    with connect() as conn:
        with conn.cursor() as cur:
            ensure_table(cur, args.mode)
            cur.execute(
                f"""SELECT ordinal,source,start_pos,end_pos,content,
                           embedding <=> %s::vector AS distance
                    FROM {table}
                    WHERE strategy=%s AND vector_norm(embedding) > 0
                    ORDER BY distance ASC
                    LIMIT %s""",
                (vector_literal(query_vector), settings_key(args), args.top_k)
            )
            return cur.fetchall()


def query(args):
    rows = search(args)
    if rows is None:
        print("검색 불가: 질문에 Fixture 키워드(과제·마감·제출)가 없어 0벡터가 됩니다.")
        return
    if not rows:
        print("검색 결과 0건: 같은 설정으로 index를 먼저 실행하세요.")
    for ordinal,source,start,end,content,distance in rows:
        print(f"rank chunk={ordinal} {source}[{start}:{end}] distance={distance:.4f}")
        print(content[:220].replace("\n", " "))


def evaluate(args):
    args.question = "과제 마감일"
    rows = search(args) or []
    gold = "금요일 오후 6시"
    ranks = [rank for rank, row in enumerate(rows, start=1) if gold in row[4]]
    print(f"Hit@{args.top_k}={int(bool(ranks))} (교육용 정답 문자열 포함 여부)")
    print(f"정답 문구 첫 등장 순위: {ranks[0] if ranks else '-'} (검색 결과 {len(rows)}건)")
    print("주의: 검색 품질 지표가 실제 답변의 정확도를 보장하지 않습니다.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["preview","index","count","query","evaluate"])
    parser.add_argument("question", nargs="?")
    parser.add_argument("--strategy", choices=["fixed","paragraph","overlap"], default="fixed")
    parser.add_argument("--size", type=int, default=160)
    parser.add_argument("--overlap", type=int, default=0)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--mode", choices=["fixture","live"], default="fixture")
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k는 1 이상이어야 합니다.")
    if args.command == "query" and not args.question:
        parser.error("query 뒤에 질문을 입력하세요.")
    if args.command == "preview":
        for idx,(start,end,content) in enumerate(build_chunks(args)):
            print(f"chunk={idx} [{start}:{end}] len={len(content)} {content[:80]!r}")
    elif args.command == "index": index(args)
    elif args.command == "count": count(args)
    elif args.command == "query": query(args)
    else: evaluate(args)


if __name__ == "__main__":
    main()
