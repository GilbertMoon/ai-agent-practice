"""Lesson 07 — educational chunking comparison and Chroma persistence.

Fixture vectors are manually programmed, NOT semantic model embeddings.
All generated data go to .chroma_lesson07, never the Lesson 06 store.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

from document_qa import read_document
from embedding_search import fixture_vector, live_vectors
from main import load_local_env
from vector_store import create_client

ROOT = Path(__file__).resolve().parent
DEFAULT_DOC = ROOT / "data" / "lesson07_long_notice.md"
DEFAULT_STORE = ROOT / ".chroma_lesson07"
STRATEGIES = ("fixed", "paragraph", "overlap")
MODES = ("fixture", "live")


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    strategy: str
    ordinal: int
    start: int
    end: int
    text: str


def split_chunks(text: str, source: str, strategy: str, size: int = 160, overlap: int = 30) -> list[Chunk]:
    if strategy not in STRATEGIES:
        raise ValueError("strategy는 fixed, paragraph, overlap 중 하나여야 합니다.")
    if not 40 <= size <= 2000:
        raise ValueError("size는 40~2000이어야 합니다.")
    if not 0 <= overlap < size:
        raise ValueError("overlap은 0 이상이고 size보다 작아야 합니다.")
    if not text.strip():
        raise ValueError("문서가 비어 있습니다.")

    ranges: list[tuple[int, int]] = []
    if strategy == "paragraph":
        # Preserve original offsets so a selected result can be traced to its source.
        for match in re.finditer(r"[^\r\n]+(?:\r?\n(?!\r?\n)[^\r\n]+)*", text):
            if match.group().strip():
                ranges.append((match.start(), match.end()))
    else:
        step = size if strategy == "fixed" else size - overlap
        for start in range(0, len(text), step):
            end = min(start + size, len(text))
            ranges.append((start, end))
            if end == len(text):
                break

    chunks = []
    for n, (start, end) in enumerate(ranges, start=1):
        part = text[start:end]
        if not part.strip():
            continue
        digest = hashlib.sha256(f"{source}|{strategy}|{n}|{start}|{end}".encode()).hexdigest()[:12]
        chunks.append(Chunk(f"l07-{digest}", source, strategy, n, start, end, part))
    return chunks


def collection_name(mode: str, strategy: str, size: int, overlap: int) -> str:
    # Distinct collections prevent mixing chunk configurations or embedding spaces.
    token = f"lesson07_{mode}_{strategy}_s{size}"
    return token + (f"_o{overlap}" if strategy == "overlap" else "")


def get_collection(client, mode: str, strategy: str, size: int, overlap: int, model: str = ""):
    if mode not in MODES:
        raise ValueError("mode는 fixture 또는 live입니다.")
    name = collection_name(mode, strategy, size, overlap)
    expected_model = "handcrafted-3d-v1" if mode == "fixture" else model
    if not expected_model:
        raise ValueError("OPENAI_EMBEDDING_MODEL이 필요합니다.")
    metadata = {"lesson": "07", "mode": mode, "model": expected_model, "strategy": strategy}
    try:
        col = client.get_collection(name=name, embedding_function=None)
    except Exception as original:
        try:
            names = {c.name for c in client.list_collections()}
        except Exception:
            raise original
        if name in names:
            raise
        return client.create_collection(
            name=name, embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
            metadata=metadata,
        )
    meta = col.metadata or {}
    if any(meta.get(k) != v for k, v in metadata.items()):
        raise ValueError("기존 컬렉션의 임베딩 모델 또는 설정이 다릅니다.")
    return col


def index_chunks(col, chunks: list[Chunk], mode: str, model: str = "") -> int:
    if not chunks:
        raise ValueError("저장할 청크가 없습니다.")
    vectors = (
        [fixture_vector(c.text) for c in chunks]
        if mode == "fixture" else live_vectors([c.text for c in chunks], model)
    )
    if len(vectors) != len(chunks):
        raise ValueError("벡터 개수가 청크와 다릅니다.")
    if mode == "fixture":
        # The hand-written theme dictionary misses some text spans. A tiny
        # fallback allows demonstration of storage, NOT quality evaluation.
        vectors = [v if any(v) else [0.001, 0.001, 0.001] for v in vectors]
    col.upsert(
        ids=[c.id for c in chunks],
        embeddings=vectors,
        documents=[c.text for c in chunks],
        metadatas=[
            {"source": c.source, "strategy": c.strategy, "start": c.start, "end": c.end, "ordinal": c.ordinal}
            for c in chunks
        ],
    )
    return col.count()


def query_chunks(col, question: str, mode: str, top_k: int, model: str = "") -> list[dict]:
    if not question.strip():
        raise ValueError("질문을 입력하세요.")
    if not 1 <= top_k <= 10:
        raise ValueError("top-k는 1~10이어야 합니다.")
    if col.count() == 0:
        raise ValueError("저장된 청크가 없습니다. 먼저 index를 실행하세요.")
    vector = fixture_vector(question) if mode == "fixture" else live_vectors([question], model)[0]
    if not any(vector):
        return []
    data = col.query(
        query_embeddings=[vector], n_results=min(top_k, col.count()),
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"id": id_, "text": body, "source": meta["source"],
         "start": meta["start"], "end": meta["end"], "ordinal": meta["ordinal"],
         "distance": float(dist)}
        for id_, body, meta, dist in zip(
            data["ids"][0], data["documents"][0], data["metadatas"][0], data["distances"][0]
        )
    ]


def hit_at_k(results: list[dict], reference_phrase: str) -> int:
    """Teaching metric: exact gold phrase in top-k returned chunk, not semantic correctness."""
    return int(any(reference_phrase in row["text"] for row in results))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lesson 07 chunking and retrieval")
    parser.add_argument("action", choices=("preview", "index", "count", "query", "evaluate"))
    parser.add_argument("question", nargs="?")
    parser.add_argument("--strategy", choices=STRATEGIES, default="paragraph")
    parser.add_argument("--size", type=int, default=160)
    parser.add_argument("--overlap", type=int, default=30)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--mode", choices=MODES, default="fixture")
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    parser.add_argument("--document", type=Path, default=DEFAULT_DOC)
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.top_k <= 10:
            raise ValueError("top-k는 1~10이어야 합니다.")
        if args.strategy != "overlap" and args.overlap != 30:
            raise ValueError("overlap 옵션은 overlap 전략에서만 변경하세요.")
        if args.action == "query" and not (args.question or "").strip():
            raise ValueError("query에 질문을 입력하세요.")
        model = ""
        if args.mode == "live" and args.action in ("index", "query"):
            load_local_env()
            model = os.getenv("OPENAI_EMBEDDING_MODEL", "").strip()
            if not model or not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY와 OPENAI_EMBEDDING_MODEL이 필요합니다.")
        elif args.mode == "live":
            load_local_env()
            model = os.getenv("OPENAI_EMBEDDING_MODEL", "").strip()
            if not model:
                raise ValueError("Live 모드의 모델을 설정하세요.")

        text = read_document(args.document)
        chunks = split_chunks(text, args.document.name, args.strategy, args.size, args.overlap)
        if args.action == "preview":
            print(f"[PREVIEW] strategy={args.strategy}; chunks={len(chunks)}; api_calls=0")
            for c in chunks:
                print(f"[{c.ordinal}] id={c.id}; range={c.start}:{c.end}; chars={len(c.text)}")
                print(c.text.replace("\n", " ")[:110])
            return 0
        client = create_client(args.store)
        col = get_collection(client, args.mode, args.strategy, args.size, args.overlap, model)
        if args.action == "index":
            count = index_chunks(col, chunks, args.mode, model)
            print(f"[INDEX] mode={args.mode}; strategy={args.strategy}; count={count}; store={args.store.name}")
        elif args.action == "count":
            print(f"[COUNT] mode={args.mode}; strategy={args.strategy}; count={col.count()}")
        else:
            questions = [args.question] if args.action == "query" else [
                "과제 마감일", "API Key 보안", "질문 게시판"
            ]
            gold = ["금요일 오후 6시", "로컬 .env", "질문 게시판"]
            for i, question in enumerate(questions):
                rows = query_chunks(col, question, args.mode, args.top_k, model)
                print(f"[QUERY] question={question}; strategy={args.strategy}; results={len(rows)}")
                for rank, row in enumerate(rows, 1):
                    print(f"[{rank}] distance={row['distance']:.3f}; id={row['id']}; source={row['source']}; range={row['start']}:{row['end']}")
                    print(row["text"].replace("\n", " ")[:160])
                if args.action == "evaluate":
                    print(f"[EVAL] gold={gold[i]}; hit@{args.top_k}={hit_at_k(rows, gold[i])}")
        if args.mode == "fixture":
            print("[FIXTURE] 수동 3차원 벡터, 실제 AI 임베딩 아님; api_calls=0")
        else:
            print(f"[LIVE] model={model}; count는 API 호출 없음; index/query는 호출 가능")
        return 0
    except (ValueError, FileNotFoundError) as exc:
        print(f"설정 오류: {exc}")
        return 2
    except ImportError:
        print("설정 오류: 필요한 라이브러리가 설치되지 않았습니다.")
        return 2
    except Exception as exc:
        print(f"실행 오류: {type(exc).__name__} (비밀정보 비표시)")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
