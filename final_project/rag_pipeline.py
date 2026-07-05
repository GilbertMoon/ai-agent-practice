from __future__ import annotations

import re
from pathlib import Path

from config import settings
from schemas import SourceDocument


def tokenize(text: str) -> list[str]:
    """문장을 검색 가능한 단어 목록으로 변환합니다."""
    return [token for token in re.split(r"\W+", text.lower()) if len(token) >= 2]


def read_markdown_files(docs_dir: str | None = None) -> list[tuple[Path, str]]:
    """지정된 폴더에서 Markdown 파일을 읽습니다."""
    base_dir = Path(docs_dir or settings.docs_dir)

    if not base_dir.exists():
        return []

    markdown_files = sorted(base_dir.glob("*.md"))
    return [(path, path.read_text(encoding="utf-8")) for path in markdown_files]


def search_documents(query: str, docs_dir: str | None = None, top_k: int = 3) -> list[SourceDocument]:
    """사용자 질문과 관련 있는 Markdown 문서를 검색합니다."""
    query_terms = set(tokenize(query))

    if not query_terms:
        return []

    results: list[SourceDocument] = []

    for path, text in read_markdown_files(docs_dir):
        text_terms = set(tokenize(text))
        score = len(query_terms & text_terms)

        if score <= 0:
            continue

        preview = text.strip().replace("\n", " ")[:300]
        results.append(
            SourceDocument(
                path=str(path),
                score=score,
                preview=preview,
            )
        )

    return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]


def build_context(sources: list[SourceDocument]) -> str:
    """검색 결과를 Agent가 사용할 context 문자열로 변환합니다."""
    if not sources:
        return "검색된 문서 근거가 없습니다."

    chunks: list[str] = []

    for idx, source in enumerate(sources, start=1):
        chunks.append(
            f"[{idx}] {source.path} (score={source.score})\n{source.preview}"
        )

    return "\n\n".join(chunks)


if __name__ == "__main__":
    sample_query = "재택근무와 문서 보안 정책을 알려줘"
    found_sources = search_documents(sample_query)
    print(build_context(found_sources))