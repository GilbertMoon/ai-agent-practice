"""Lesson 05: keyword vs vector search.

Fixture mode uses deliberately HAND-ASSIGNED educational vectors, NOT model
embeddings. Live mode uses OpenAI's separate Embeddings API, with explicit opt-in.
"""
from __future__ import annotations

import argparse
import math
import os
from dataclasses import dataclass
from pathlib import Path

from document_qa import DEFAULT_DOC, read_document, retrieve, split_sections
from main import load_local_env

# Three hand-picked dimensions: deadlines, security, questions.
# This is a transparent classroom fixture, not learned semantic understanding.
THEMES = {
    "deadline": ("마감", "마감일", "기한", "언제", "제출", "due", "deadline"),
    "security": ("비밀", "보안", "키", "key", "환경", "인증", "비밀번호"),
    "help": ("문의", "질문", "상담", "게시판", "연락"),
}


@dataclass(frozen=True)
class Ranked:
    section: str
    text: str
    similarity: float


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("벡터의 차원은 같고 0보다 커야 합니다.")
    norm_left = math.sqrt(sum(x*x for x in left))
    norm_right = math.sqrt(sum(x*x for x in right))
    if norm_left == 0 or norm_right == 0:
        return 0.0
    return sum(x*y for x,y in zip(left,right)) / (norm_left*norm_right)


def fixture_vector(text: str) -> list[float]:
    normalized = text.lower()
    return [float(sum(word in normalized for word in words)) for words in THEMES.values()]


def rank_sections(
    sections: list[tuple[str, str]], question_vector: list[float],
    section_vectors: list[list[float]], top_k: int = 2
) -> list[Ranked]:
    if len(sections) != len(section_vectors):
        raise ValueError("문서와 벡터 수가 다릅니다.")
    scored = [
        Ranked(section, paragraph, cosine_similarity(question_vector, vector))
        for (section, paragraph), vector in zip(sections, section_vectors)
    ]
    scored.sort(key=lambda result: -result.similarity)
    return [result for result in scored if result.similarity > 0][:top_k]


def live_vectors(texts: list[str], model: str) -> list[list[float]]:
    if not model:
        raise ValueError("OPENAI_EMBEDDING_MODEL이 필요합니다.")
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY가 필요합니다.")
    from openai import OpenAI
    client = OpenAI(api_key=key, timeout=30.0, max_retries=0)
    response = client.embeddings.create(model=model, input=texts)
    ordered = sorted(response.data, key=lambda item: item.index)
    if len(ordered) != len(texts):
        raise RuntimeError("임베딩 응답 개수가 요청과 일치하지 않습니다.")
    return [item.embedding for item in ordered]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lesson 05 embedding search")
    parser.add_argument("question", nargs="?", default="마감일이 언제인가요?")
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    parser.add_argument("--top-k", type=int, default=2)
    args = parser.parse_args(argv)
    if not 1 <= args.top_k <= 3 or not args.question.strip():
        print("설정 오류: 질문과 top-k(1~3)를 확인하세요.")
        return 2

    document = read_document(DEFAULT_DOC)
    sections = split_sections(document)
    baseline = retrieve(document, args.question, DEFAULT_DOC.name, top_k=args.top_k)
    print("=== 키워드 검색 ===")
    if not baseline:
        print("일치 단어 없음")
    for item in baseline:
        print(f"[{item.section}] score={item.score}: {item.text}")

    if args.mode == "fixture":
        query_vector = fixture_vector(args.question)
        paragraph_vectors = [fixture_vector(name+" "+body) for name,body in sections]
        print("\n[FIXTURE] 학습용 수동 벡터. 실제 모델 임베딩이나 품질 측정이 아닙니다.")
    else:
        try:
            load_local_env()
            model = os.getenv("OPENAI_EMBEDDING_MODEL", "").strip()
            vectors = live_vectors([args.question]+[name+" "+body for name,body in sections], model)
            query_vector, paragraph_vectors = vectors[0], vectors[1:]
            print("\n[LIVE] OpenAI Embeddings API 결과, 사용 모델: "+model)
        except ValueError as exc:
            # ValueError messages are authored in this module and contain
            # only setting names, never key values.
            print(f"설정 오류: {exc}")
            return 2
        except ImportError as exc:
            print(f"설정 오류: {type(exc).__name__}")
            return 2
        except Exception as exc:
            print(f"API_ERROR: {type(exc).__name__} (비밀정보 제외)")
            return 3

    results = rank_sections(sections, query_vector, paragraph_vectors, args.top_k)
    print("=== 벡터 유사도 검색 ===")
    if not results:
        print("유사도 0 초과 문단 없음")
    for item in results:
        print(f"[{item.section}] cosine={item.similarity:.3f}: {item.text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
