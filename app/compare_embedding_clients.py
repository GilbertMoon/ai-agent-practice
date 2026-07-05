from gemini_embedding_client import embed_text as embed_text_with_gemini
from embedding_client import embed_text as embed_text_with_local

TEST_TEXT = "API Key는 .env 파일에 저장하고 GitHub에 올리지 않습니다."


def print_embedding_summary(name: str, embedding: list[float]) -> None:
    print("=" * 70)
    print(name)
    print("=" * 70)
    print(f"벡터 길이: {len(embedding)}")
    print("앞 10개 값:")
    print([round(value, 6) for value in embedding[:10]])
    print()


def main() -> None:
    print("비교 문장:")
    print(TEST_TEXT)
    print()

    try:
        gemini_embedding = embed_text_with_gemini(TEST_TEXT)
        print_embedding_summary("Gemini 임베딩", gemini_embedding)
    except Exception as error:
        print("Gemini 임베딩 실행 실패")
        print(error)
        print()

    local_embedding = embed_text_with_local(TEST_TEXT)
    print_embedding_summary("로컬 임베딩", local_embedding)

    print("주의:")
    print("서로 다른 임베딩 모델이 만든 벡터는 차원 수와 벡터 공간이 다를 수 있습니다.")
    print("따라서 Gemini 벡터와 로컬 벡터를 직접 코사인 유사도로 비교하지 않습니다.")
    print("검색 실습에서는 질문과 문서를 반드시 같은 임베딩 모델로 변환해야 합니다.")


if __name__ == "__main__":
    main()