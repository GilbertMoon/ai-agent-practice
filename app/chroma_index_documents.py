from document_prompt import read_text_file, split_paragraphs
from embedding_client import embed_text
from chroma_client import get_chroma_collection

DATA_FILE = "data/course_notice.txt"


def prepare_document(content: str, title: str = "course_notice.txt") -> str:
    return f"title: {title} | text: {content}"


def main() -> None:
    collection = get_chroma_collection()
    document = read_text_file(DATA_FILE)
    paragraphs = split_paragraphs(document)

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for index, paragraph in enumerate(paragraphs, start=1):
        doc_id = f"course_notice_{index}"
        embedding_input = prepare_document(paragraph)
        embedding = embed_text(embedding_input)

        ids.append(doc_id)
        documents.append(paragraph)
        embeddings.append(embedding)
        metadatas.append(
            {
                "source": "course_notice.txt",
                "paragraph_id": index,
            }
        )

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"Chroma 인덱싱 완료: {len(ids)}개 문단")


if __name__ == "__main__":
    main()
