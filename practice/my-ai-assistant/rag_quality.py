"""Lesson 08: inspect retrieval quality and evidence-based answers.

Default fixture uses human-defined vectors from Lesson 05: NOT semantic AI.
All default paths are read-only. Only --mode live makes provider requests.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from chunking import DEFAULT_DOC, split_chunks
from document_qa import read_document, build_grounded_prompt, Evidence
from embedding_search import cosine_similarity, fixture_vector, live_vectors
from main import load_local_env, make_client

ROOT = Path(__file__).resolve().parent
DEFAULT_CASES = ROOT / "data" / "lesson08_eval_cases.json"
STRATEGIES = ("fixed", "paragraph", "overlap")


@dataclass(frozen=True)
class Result:
    rank: int
    chunk_id: str
    text: str
    start: int
    end: int
    similarity: float
    source: str


def rank_chunks(question: str, chunks, mode: str = "fixture", model: str = "", top_k: int = 3) -> list[Result]:
    if not question.strip():
        raise ValueError("질문을 입력하세요.")
    if not 1 <= top_k <= 10:
        raise ValueError("top-k는 1~10이어야 합니다.")
    if not chunks:
        return []
    texts = [c.text for c in chunks]
    if mode == "fixture":
        query_vec = fixture_vector(question)
        document_vecs = [fixture_vector(text) for text in texts]
    elif mode == "live":
        vectors = live_vectors([question] + texts, model)
        query_vec, document_vecs = vectors[0], vectors[1:]
    else:
        raise ValueError("지원하지 않는 모드입니다.")
    if not any(query_vec):
        return []
    scored = []
    for c, v in zip(chunks, document_vecs):
        if not any(v):
            continue
        score = cosine_similarity(query_vec, v)
        if score > 0:
            scored.append((c, score))
    scored.sort(key=lambda x: (-x[1], x[0].ordinal))
    return [
        Result(i, c.id, c.text, c.start, c.end, score, c.source)
        for i, (c, score) in enumerate(scored[:top_k], start=1)
    ]


def gold_rank(rows: list[Result], gold: str) -> int | None:
    """Exact reference phrase match, not a judgment of semantic relevance."""
    for row in rows:
        if gold and gold in row.text:
            return row.rank
    return None


def evaluate_cases(cases: list[dict], chunks, mode="fixture", model="", top_k=3) -> list[dict]:
    output = []
    for case in cases:
        question = case["question"]
        gold = case.get("gold", "")
        rows = rank_chunks(question, chunks, mode=mode, model=model, top_k=top_k)
        rank = gold_rank(rows, gold) if gold else None
        output.append({
            "question": question, "gold": gold,
            "expected_answerable": bool(gold),
            "retrieved": len(rows),
            "gold_rank": rank,
            "hit": int(rank is not None) if gold else None,
            "reciprocal_rank": (1.0 / rank) if rank else (0.0 if gold else None),
        })
    return output


def extract_evidence(rows: list[Result], gold: str) -> tuple[str, Result] | None:
    """Only return an exact substring from a retrieved chunk; never fabricate."""
    if not gold:
        return None
    for row in rows:
        if gold in row.text:
            return gold, row
    return None


def load_cases(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("평가 데이터는 비어 있지 않은 배열이어야 합니다.")
    for case in data:
        if not isinstance(case, dict) or not isinstance(case.get("question"), str) or not isinstance(case.get("gold"), str):
            raise ValueError("평가 항목에는 문자열 question과 gold가 필요합니다.")
    return data


def display_rows(rows: list[Result]):
    if not rows:
        print("검색 결과 없음")
    for row in rows:
        print(f"[{row.rank}] sim={row.similarity:.3f}; id={row.chunk_id}; source={row.source}; range={row.start}:{row.end}")
        print(row.text.replace("\n", " ")[:200])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lesson 08 retrieval evidence quality")
    parser.add_argument("action", choices=("search", "evaluate", "preview", "generate"))
    parser.add_argument("question", nargs="?")
    parser.add_argument("--strategy", choices=STRATEGIES, default="paragraph")
    parser.add_argument("--size", type=int, default=160)
    parser.add_argument("--overlap", type=int, default=30)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    parser.add_argument("--gold", default="")
    parser.add_argument("--document", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.top_k <= 10:
            raise ValueError("top-k는 1~10이어야 합니다.")
        if args.action in ("search", "preview", "generate") and not (args.question or "").strip():
            raise ValueError("질문을 입력하세요.")
        if args.action == "generate" and args.mode != "live":
            raise ValueError("generate는 --mode live를 명시해야 합니다.")
        if args.mode == "live":
            load_local_env()
            model = os.getenv("OPENAI_EMBEDDING_MODEL", "").strip()
            if not model or not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY와 OPENAI_EMBEDDING_MODEL이 필요합니다.")
        else:
            model = ""
        text = read_document(args.document)
        chunks = split_chunks(text, args.document.name, args.strategy, args.size, args.overlap)
        if args.action == "evaluate":
            cases = load_cases(args.cases)
            observations = evaluate_cases(cases, chunks, args.mode, model, args.top_k)
            for item in observations:
                print(f"[EVAL] question={item['question']}; gold={item['gold'] or '(none)'}; hit={item['hit']}; rank={item['gold_rank']}; rr={item['reciprocal_rank']}")
            eligible = [x for x in observations if x["expected_answerable"]]
            hits = sum(x["hit"] for x in eligible)
            mrr = sum(x["reciprocal_rank"] for x in eligible) / len(eligible) if eligible else 0
            print(f"[SUMMARY] gold_questions={len(eligible)}; hit@{args.top_k}={hits}/{len(eligible)}; mrr={mrr:.3f}")
            print("[NOTE] Exact-string metric only; unanswered questions are not part of hit@k or MRR.")
            if args.mode == "fixture":
                print("[FIXTURE] 수동 벡터; api_calls=0; 의미 검색 성능 아님")
            return 0

        rows = rank_chunks(args.question, chunks, args.mode, model, args.top_k)
        print(f"[SEARCH] mode={args.mode}; strategy={args.strategy}; chunks={len(chunks)}; retrieved={len(rows)}")
        display_rows(rows)
        if args.action == "search":
            if args.mode == "fixture":
                print("[FIXTURE] 수동 벡터; api_calls=0")
            return 0

        chosen = extract_evidence(rows, args.gold)
        if not chosen:
            print("[NO_EVIDENCE] 검증된 정답 문구를 검색 결과에서 찾지 못했습니다.")
            print("[HOLD] 근거가 없어 답변을 생성하지 않습니다.")
            return 0
        phrase, row = chosen
        print(f"[EVIDENCE] {phrase}")
        print(f"[CITATION] {row.source} range={row.start}:{row.end}; id={row.chunk_id}")
        if args.action == "preview":
            print("[PREVIEW] 원문에서 발췌한 문구이며 모델 생성 답변이 아닙니다. api_calls=0 (fixture인 경우)")
            return 0

        # Explicit optional generation, only after exact evidence verified.
        evidence = [Evidence(row.source, f"range={row.start}:{row.end}", row.text, 1)]
        prompt = build_grounded_prompt(args.question, evidence)
        reply = make_client("live").ask(prompt)
        print("=== 실제 모델 답변 (근거와 대조 필요) ===")
        print(reply.text)
        print(f"[model={reply.model}; input={reply.input_tokens}; output={reply.output_tokens}; cached_input={reply.cached_input_tokens}]")
        return 0
    except (ValueError, FileNotFoundError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"설정 오류: {type(exc).__name__}: {exc}")
        return 2
    except Exception as exc:
        print(f"실행 오류: {type(exc).__name__} (민감정보 비표시)")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
