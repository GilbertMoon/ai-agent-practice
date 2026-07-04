from pathlib import Path

from chroma_client import get_chroma_collection
from chunk_utils import split_paragraphs_to_chunks
from document_prompt import read_text_file, split_paragraphs
from embedding_client import embed_text

DATA_FILE = "data/course_policy_long.txt"
SOURCE_NAME = Path(DATA_FILE).name
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


def prepare_document_for_embedding(chunk_text: str, metadata: dict) -> str:
    """임베딩 입력에 본문과 기본 metadata를 함께 넣습니다."""
    return (
        f"source: {metadata['source']} | "
        f"section: {metadata['section']} | "
        f"paragraph_id: {metadata['paragraph_id']} | "
        f"chunk_index: {metadata['chunk_index']} | "
        f"text: {chunk_text}"
    )


def main() -> None:
    collection = get_chroma_collection()
    document = read_text_file(DATA_FILE)
    paragraphs = split_paragraphs(document)

    chunk_items = split_paragraphs_to_chunks(
        paragraphs=paragraphs,
        source=SOURCE_NAME,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    if not chunk_items:
        print("인덱싱할 chunk가 없습니다.")
        return

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for item in chunk_items:
        chunk_text = item["text"]
        metadata = item["metadata"]
        embedding_input = prepare_document_for_embedding(chunk_text, metadata)
        embedding = embed_text(embedding_input)

        ids.append(item["id"])
        documents.append(chunk_text)
        embeddings.append(embedding)
        metadatas.append(metadata)

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print("Chapter 7 chunk 인덱싱 완료")
    print(f"문서: {DATA_FILE}")
    print(f"chunk_size: {CHUNK_SIZE}")
    print(f"chunk_overlap: {CHUNK_OVERLAP}")
    print(f"저장된 chunk 수: {len(ids)}")


if __name__ == "__main__":
    main()
