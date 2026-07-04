from prompt_template import build_prompt


OUTPUT_FORMATS = {
    "markdown": (
        "다음 Markdown 형식으로 작성하세요.\n\n"
        "## 핵심 요약\n"
        "## 상세 설명\n"
        "## 실무 예시"
    ),
    "table": (
        "다음 Markdown 표 형식으로 작성하세요.\n\n"
        "| 항목 | 설명 |\n"
        "| --- | --- |\n"
        "| 개념 | ... |\n"
        "| 장점 | ... |\n"
        "| 주의점 | ... |"
    ),
    "json": (
        "다음 JSON 형식으로만 작성하세요.\n\n"
        "{\n"
        "  \"summary\": \"핵심 요약\",\n"
        "  \"example\": \"실무 예시\",\n"
        "  \"caution\": \"주의점\"\n"
        "}"
    ),
}


def main() -> None:
    topic = input("설명할 주제를 입력하세요: ").strip()
    output_type = input("출력 형식(markdown/table/json)을 입력하세요: ").strip().lower()

    if not topic:
        print("주제를 입력해 주세요.")
        return

    if output_type not in OUTPUT_FORMATS:
        print("지원하지 않는 출력 형식입니다. markdown, table, json 중 하나를 입력하세요.")
        return

    prompt = build_prompt(
        role="당신은 AI Agent Engineering 교재를 작성하는 AI 튜터입니다.",
        context="학습자가 LLM 서비스 개발을 처음 배우고 있습니다.",
        task=f"{topic}의 개념을 설명하세요.",
        constraints="초보자도 이해할 수 있게 작성하고, 너무 긴 설명은 피하세요.",
        output_format=OUTPUT_FORMATS[output_type],
    )

    print("\n[생성된 프롬프트]")
    print(prompt)


if __name__ == "__main__":
    main()