from embedding_client import embed_text
from vector_math import cosine_similarity

def prepare_query(question: str) -> str:
    return f"task: search result | query: {question}"


def prepare_document(content: str, title: str = "course_notice.txt") -> str:
    return f"title: {title} | text: {content}"

from embedding_client import embed_text


def build_embedded_paragraphs(paragraphs: list[str]) -> list[dict]:
    embedded_paragraphs = []

    for index, paragraph in enumerate(paragraphs, start=1):
        embedding_input = prepare_document(paragraph)
        embedding = embed_text(embedding_input)
        embedded_paragraphs.append(
            {
                "id": index,
                "text": paragraph,
                "embedding": embedding,
            }
        )

    return embedded_paragraphs




def search_similar_paragraphs(
    question: str,
    embedded_paragraphs: list[dict],
    top_k: int = 3,
) -> list[dict]:
    query_embedding = embed_text(prepare_query(question))
    scored = []

    for item in embedded_paragraphs:
        score = cosine_similarity(query_embedding, item["embedding"])
        scored.append({**item, "score": score})

    scored.sort(reverse=True, key=lambda item: item["score"])
    return scored[:top_k]