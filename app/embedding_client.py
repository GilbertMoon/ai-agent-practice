from functools import lru_cache

from sentence_transformers import SentenceTransformer

LOCAL_EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """로컬 임베딩 모델을 한 번만 로드해서 재사용합니다."""
    return SentenceTransformer(LOCAL_EMBEDDING_MODEL_NAME)


def embed_text(text: str) -> list[float]:
    """입력 텍스트를 로컬 임베딩 벡터로 변환합니다."""
    model = get_embedding_model()
    embedding = model.encode(
        text,
        normalize_embeddings=True,
    )
    return embedding.tolist()


def main() -> None:
    text = "AI Agent Engineering"
    embedding = embed_text(text)

    print("입력 문장:")
    print(text)
    print()

    print("로컬 임베딩 모델:")
    print(LOCAL_EMBEDDING_MODEL_NAME)
    print()

    print("임베딩 벡터 길이:")
    print(len(embedding))
    print()

    print("임베딩 벡터 앞 10개 값:")
    print(embedding[:10])


if __name__ == "__main__":
    main()