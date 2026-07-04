DEFAULT_ROLE = "당신은 초보자를 위한 친절한 AI 튜터입니다."
DEFAULT_CONTEXT = "이 설명은 AI Agent Engineering 교재의 학습 보조 자료로 사용됩니다."


def build_prompt(
    role: str,
    context: str,
    task: str,
    constraints: str,
    output_format: str,
) -> str:
    return f"""
역할:
{role}

맥락:
{context}

작업:
{task}

제약조건:
{constraints}

출력 형식:
{output_format}
""".strip()


def make_tutor_prompt(topic: str) -> str:
    return build_prompt(
        role=DEFAULT_ROLE,
        context=DEFAULT_CONTEXT,
        task=f"{topic}의 개념을 설명하세요.",
        constraints=(
            "- 5문장 이내로 작성하세요.\n"
            "- 어려운 용어는 쉽게 풀어서 설명하세요.\n"
            "- 마지막에 실무 예시 1개를 추가하세요."
        ),
        output_format=(
            "다음 Markdown 형식으로 작성하세요.\n\n"
            "## 핵심 설명\n"
            "## 쉬운 비유\n"
            "## 실무 예시"
        ),
    )


if __name__ == "__main__":
    sample_prompt = make_tutor_prompt("AI Agent")
    print(sample_prompt)