"""Chapter 06 미니 프로젝트 정답 예시

Chroma 기반 수업 공지 RAG 챗봇입니다.
프로젝트 루트에서 다음 명령으로 실행할 수 있습니다.

    python solutions/chapter06/chapter06_chroma_rag_solution.py

사전 준비:
    pip install -r requirements.txt

주의:
- .env 파일에 GEMINI_API_KEY가 설정되어 있어야 합니다.
- .env 파일과 chroma_db/ 폴더는 GitHub에 올리지 않습니다.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
DATA_FILE = PROJECT_ROOT / "data" / "course_notice.txt"
CHROMA_DB_PATH = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "course_notice"
EMBEDDING_MODEL = "gemini-embedding-2"
ANSWER_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-3.5-flash")

# solutions/chapter06 폴더에서 실행해도 app 폴더의 공통 함수를 불러올 수 있도록 설정합니다.
sys.path.append(str(APP_DIR))
os.chdir(PROJECT_ROOT)

from document_prompt import build_document_prompt, read_text_file, split_paragraphs  # noqa: E402


def get_api_key() -> str:
    """.env 파일에서 Gemini API Key를 읽습니다."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY를 .env 파일에서 확인하세요.")

    return api_key


def get_genai_client() -> genai.Client:
    """Gemini API 클라이언트를 생성합니다."""
    return genai.Client(api_key=get_api_key())


def embed_text(text: str) -> list[float]:
    """텍스트를 Gemini 임베딩 벡터로 변환합니다."""
    client = get_genai_client()
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    return result.embeddings[0].values


def ask_gemini(prompt: str) -> str:
    """검색된 문단을 근거로 Gemini 답변을 생성합니다."""
    client = get_genai_client()
    interaction = client.interactions.create(
        model=ANSWER_MODEL,
        input=prompt,
    )
    return interaction.output_text


def prepare_query(question: str) -> str:
    """질문을 검색용 임베딩 입력 형식으로 변환합니다."""
    return f"task: search result | query: {question}"


def prepare_document(content: str, title: str = "course_notice.txt") -> str:
    """문단을 검색 대상 문서 임베딩 입력 형식으로 변환합니다."""
    return f"title: {title} | text: {content}"


def get_chroma_collection():
    """Chroma Persistent Client와 collection을 준비합니다."""
    client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    return client.get_or_create_collection(name=COLLECTION_NAME)


def index_course_notice() -> None:
    """course_notice.txt 문단을 Chroma collection에 저장합니다."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"문서 파일을 찾을 수 없습니다: {DATA_FILE}\n"
            "data/course_notice.txt 파일을 먼저 준비하세요."
        )

    collection = get_chroma_collection()
    document = read_text_file(str(DATA_FILE))
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
                "source": DATA_FILE.name,
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


def search_documents(question: str, top_k: int = 3) -> list[dict]:
    """질문과 관련 있는 문단을 Chroma에서 검색합니다."""
    collection = get_chroma_collection()
    query_embedding = embed_text(prepare_query(question))

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    items = []
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        items.append(
            {
                "id": doc_id,
                "document": document,
                "metadata": metadata,
                "distance": distance,
            }
        )

    return items


def build_context(search_results: list[dict]) -> str:
    """검색 결과를 RAG 프롬프트 context로 변환합니다."""
    context_parts = []

    for item in search_results:
        metadata = item["metadata"] or {}
        source = metadata.get("source", "unknown")
        paragraph_id = metadata.get("paragraph_id", "unknown")
        distance = item["distance"]
        document = item["document"]

        context_parts.append(
            f"[문단 {paragraph_id}, source={source}, distance={distance:.4f}]\n{document}"
        )

    return "\n\n".join(context_parts)


def answer_question(question: str) -> tuple[list[dict], str]:
    """Chroma 검색 결과를 근거로 질문에 답변합니다."""
    search_results = search_documents(question, top_k=3)
    context = build_context(search_results)
    prompt = build_document_prompt(context, question)
    answer = ask_gemini(prompt)
    return search_results, answer


def print_search_results(search_results: list[dict]) -> None:
    """검색 결과를 보기 좋게 출력합니다."""
    print("\n[검색된 관련 문단]")

    for item in search_results:
        metadata = item["metadata"] or {}
        print(f"문단 ID: {item['id']}")
        print(f"출처: {metadata.get('source', 'unknown')}")
        print(f"문단 번호: {metadata.get('paragraph_id', 'unknown')}")
        print(f"distance: {item['distance']:.4f}")
        print(item["document"])
        print()


def main() -> None:
    print("Chroma 기반 문서 Q&A 프로그램")
    print(f"사용 문서: {DATA_FILE.relative_to(PROJECT_ROOT)}")
    print(f"Chroma DB 경로: {CHROMA_DB_PATH.relative_to(PROJECT_ROOT)}")
    print()

    index_course_notice()
    print("종료하려면 exit를 입력하세요.")
    print()

    while True:
        question = input("질문: ").strip()

        if question.lower() in {"exit", "quit", "q"}:
            print("프로그램을 종료합니다.")
            break

        if not question:
            print("질문을 입력하세요.")
            continue

        search_results, answer = answer_question(question)
        print_search_results(search_results)

        print("[답변]")
        print(answer)
        print("-" * 60)


if __name__ == "__main__":
    main()
