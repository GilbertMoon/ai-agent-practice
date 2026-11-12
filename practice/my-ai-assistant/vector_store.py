"""Lesson 06: persisted Chroma vector search with explicit embeddings.

Default fixture uses hand-written educational vectors (NOT model embeddings).
Live requires explicit selection and calls OpenAI only when index is created
or for a query. Chroma's automatic embedding function is always disabled.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from document_qa import DEFAULT_DOC, read_document, split_sections
from embedding_search import fixture_vector, live_vectors
from main import load_local_env

ROOT = Path(__file__).resolve().parent
DEFAULT_STORE = ROOT / ".chroma_lesson06"
NAMES = {"fixture": "lesson06_fixture", "live": "lesson06_openai"}


def create_client(store: Path):
    import chromadb
    return chromadb.PersistentClient(path=str(store))


def get_collection(client, mode: str, model: str = ""):
    name = NAMES[mode]
    expected_model = model if mode == "live" else "handcrafted-3d-v1"
    # Explicitly disable Chroma's automatic embedding model/download.
    try:
        collection = client.get_collection(name=name, embedding_function=None)
    except Exception as exc:
        # Only create on a verified absence; do not hide invalid DB errors.
        try:
            existing = {item.name for item in client.list_collections()}
        except Exception:
            raise exc
        if name in existing:
            raise
        return client.create_collection(
            name=name,
            embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
            metadata={"lesson_mode": mode, "embedding_model": expected_model},
        )

    metadata = collection.metadata or {}
    if metadata.get("lesson_mode") != mode or metadata.get("embedding_model") != expected_model:
        raise ValueError("기존 컬렉션의 모델/모드가 다릅니다. 저장 경로 또는 모델을 확인하세요.")
    return collection


def index_document(collection, mode: str, model: str) -> int:
    document = read_document(DEFAULT_DOC)
    sections = split_sections(document)
    ids = [f"notice-{i:02}" for i in range(1, len(sections) + 1)]
    texts = [name + "\n" + body for name, body in sections]
    vectors = (
        [fixture_vector(text) for text in texts]
        if mode == "fixture"
        else live_vectors(texts, model)
    )
    if not vectors or any(len(vector) != len(vectors[0]) for vector in vectors):
        raise ValueError("벡터 길이가 일정하지 않습니다.")
    collection.upsert(
        ids=ids,
        embeddings=vectors,
        documents=[body for _, body in sections],
        metadatas=[{"source": DEFAULT_DOC.name, "section": name} for name, _ in sections],
    )
    return collection.count()


def query_document(collection, question: str, mode: str, model: str, top_k: int):
    if collection.count() == 0:
        raise ValueError("저장된 문단이 없습니다. 먼저 index를 실행하세요.")
    vector = fixture_vector(question) if mode == "fixture" else live_vectors([question], model)[0]
    if not any(vector):
        return []
    result = collection.query(
        query_embeddings=[vector],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    rows = []
    for doc_id, body, meta, distance in zip(
        result["ids"][0], result["documents"][0],
        result["metadatas"][0], result["distances"][0]
    ):
        rows.append({
            "id": doc_id, "section": meta["section"], "source": meta["source"],
            "text": body, "distance": float(distance),
        })
    # Do not invent a universal similarity threshold; inspect returned content.
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lesson 06 persistent vector DB")
    parser.add_argument("action", choices=("index", "query", "count"))
    parser.add_argument("question", nargs="?")
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    parser.add_argument("--top-k", type=int, default=2)
    args = parser.parse_args(argv)

    if not 1 <= args.top_k <= 3 or (args.action == "query" and not (args.question or "").strip()):
        print("설정 오류: query에는 질문이 필요하며 top-k는 1~3입니다.")
        return 2

    model = ""
    if args.mode == "live":
        load_local_env()
        model = os.getenv("OPENAI_EMBEDDING_MODEL", "").strip()
        if not model:
            print("설정 오류: OPENAI_EMBEDDING_MODEL이 필요합니다.")
            return 2
        if not os.getenv("OPENAI_API_KEY"):
            print("설정 오류: OPENAI_API_KEY가 필요합니다.")
            return 2

    try:
        collection = get_collection(create_client(args.store), args.mode, model)
        if args.action == "index":
            count = index_document(collection, args.mode, model)
            print(f"[INDEX] mode={args.mode}; count={count}; store={args.store.name}")
        elif args.action == "count":
            print(f"[COUNT] mode={args.mode}; count={collection.count()}; store={args.store.name}")
        else:
            rows = query_document(collection, args.question, args.mode, model, args.top_k)
            print(f"[QUERY] mode={args.mode}; count={len(rows)}; source={DEFAULT_DOC.name}")
            for row in rows:
                print(f"[{row['section']}] distance={row['distance']:.3f}; id={row['id']}")
                print(row["text"])
            if not rows:
                print("검색 결과 없음")
        if args.mode == "fixture":
            print("[FIXTURE] 수동 3차원 벡터 — 실제 의미 임베딩 아님, API 호출 0회")
        else:
            print(f"[LIVE] model={model} (index와 query는 각각 Embeddings API 호출 가능)")
        return 0
    except (ValueError, FileNotFoundError, ImportError) as exc:
        if isinstance(exc, ValueError):
            # ValueErrors above contain only application-authored messages.
            print(f"설정 오류: {exc}")
        else:
            print(f"설정 오류: {type(exc).__name__}")
        return 2
    except Exception as exc:
        print(f"실행 오류: {type(exc).__name__} (키 및 상세 내용은 출력하지 않음)")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
