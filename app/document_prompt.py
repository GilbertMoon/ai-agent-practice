def read_text_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()
    
def build_document_prompt(document: str, question: str) -> str:
    return f"""
역할:
당신은 문서를 근거로 답변하는 AI 튜터입니다.

맥락:
다음 문서를 참고하세요.

{document}

작업:
사용자 질문에 답변하세요.

사용자 질문:
{question}

제약조건:
- 문서에 있는 내용만 근거로 답변하세요.
- 문서에 답이 없으면 '문서에서 확인할 수 없습니다'라고 답하세요.
- 답변은 한국어로 작성하세요.
- 가능하면 근거 문장을 함께 제시하세요.
""".strip()


def split_paragraphs(document: str) -> list[str]:
    return [
        paragraph.strip()
        for paragraph in document.split("\n\n")
        if paragraph.strip()
    ]


def find_relevant_paragraphs(document: str, question: str, top_k: int = 3) -> list[str]:
    paragraphs = split_paragraphs(document)
    question_words = set(question.lower().split())

    scored = []
    for paragraph in paragraphs:
        paragraph_words = set(paragraph.lower().split())
        score = len(question_words & paragraph_words)
        if score > 0:
            scored.append((score, paragraph))

    scored.sort(reverse=True, key=lambda item: item[0])
    return [paragraph for score, paragraph in scored[:top_k]]