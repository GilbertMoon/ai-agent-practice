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
    """파일명을 chunk ID에 사용하기 좋은 형태로 바꿉니다."""
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
    """chunk와 함께 저장할 metadata(출처, section, 문단 번호 등)를 생성합니다."""
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


def split_sections_to_chunks(
    paragraphs: list[str],
    source: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[dict]:
    """같은 section 제목 아래의 문단을 하나로 이어 붙인 뒤 chunk_size 기준으로 나눕니다.

    문단이 짧은 문서에서는 문단마다 따로 자르면 chunk_size가 효과를 내지 못합니다.
    그래서 '## 제목' 문단을 기준으로 section을 만들고, section 본문 전체를 나눕니다.
    paragraph_id에는 section이 시작되는 문단 번호를 저장합니다.
    """
    sections = []
    current = None

    for paragraph_id, paragraph in enumerate(paragraphs, start=1):
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        lines = paragraph.splitlines()

        if lines[0].strip().startswith("#"):
            current = {
                "title": detect_section_title(paragraph),
                "paragraph_id": paragraph_id,
                "texts": [],
            }
            sections.append(current)
            body = "\n".join(lines[1:]).strip()
            if body:
                current["texts"].append(body)
            continue

        if current is None:
            current = {"title": "문서 전체", "paragraph_id": paragraph_id, "texts": []}
            sections.append(current)

        current["texts"].append(paragraph)

    chunk_items = []
    source_id = normalize_source_id(source)

    for section_no, section in enumerate(sections, start=1):
        section_text = "\n".join(section["texts"])

        if not section_text:
            continue

        chunks = split_text_by_size(section_text, chunk_size, chunk_overlap)

        for chunk_index, chunk_text in enumerate(chunks, start=1):
            chunk_items.append(
                {
                    "id": f"{source_id}_s{section_no:03d}_c{chunk_index:03d}",
                    "text": chunk_text,
                    "metadata": build_chunk_metadata(
                        source=source,
                        section=section["title"],
                        paragraph_id=section["paragraph_id"],
                        chunk_index=chunk_index,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                    ),
                }
            )

    return chunk_items
