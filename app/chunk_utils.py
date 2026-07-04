from pathlib import Path


def split_text_by_size(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """문자 수 기준으로 text를 chunk 단위로 나눕니다."""
    if chunk_size <= 0:
        raise ValueError("chunk_size는 0보다 커야 합니다.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap은 0 이상이어야 합니다.")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap은 chunk_size보다 작아야 합니다.")

    chunks = []
    start = 0
    text = text.strip()

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - chunk_overlap

    return chunks


def normalize_source_id(source: str) -> str:
    """파일명을 Chroma chunk ID에 사용하기 좋은 형태로 바꿉니다."""
    return Path(source).stem.replace(" ", "_")


def detect_section_title(paragraph: str, current_section: str = "문서 전체") -> str:
    """문단의 첫 줄을 기준으로 현재 section 이름을 추정합니다."""
    first_line = paragraph.strip().splitlines()[0].strip()

    if first_line.startswith("#"):
        return first_line.lstrip("#").strip()

    if first_line.startswith("[") and first_line.endswith("]"):
        return first_line.strip("[] ")

    return current_section


def build_chunk_metadata(
    source: str,
    section: str,
    paragraph_id: int,
    chunk_index: int,
    chunk_size: int,
    chunk_overlap: int,
) -> dict:
    """Chroma에 함께 저장할 chunk metadata를 생성합니다."""
    return {
        "source": source,
        "section": section,
        "paragraph_id": paragraph_id,
        "chunk_index": chunk_index,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }


def split_paragraphs_to_chunks(
    paragraphs: list[str],
    source: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[dict]:
    """문단 목록을 chunk 목록으로 변환합니다."""
    chunk_items = []
    current_section = "문서 전체"
    source_id = normalize_source_id(source)

    for paragraph_id, paragraph in enumerate(paragraphs, start=1):
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        current_section = detect_section_title(paragraph, current_section)
        chunks = split_text_by_size(paragraph, chunk_size, chunk_overlap)

        for chunk_index, chunk_text in enumerate(chunks, start=1):
            chunk_id = f"{source_id}_p{paragraph_id:03d}_c{chunk_index:03d}"
            metadata = build_chunk_metadata(
                source=source,
                section=current_section,
                paragraph_id=paragraph_id,
                chunk_index=chunk_index,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            chunk_items.append(
                {
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": metadata,
                }
            )

    return chunk_items
