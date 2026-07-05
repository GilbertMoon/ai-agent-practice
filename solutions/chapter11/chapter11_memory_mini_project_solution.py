"""Chapter 11 미니 프로젝트 정답 예시.

주제: 대화 기록을 기억하는 수업 공지 Q&A 에이전트

실행:
    python solutions/chapter11/chapter11_memory_mini_project_solution.py chat
    python solutions/chapter11/chapter11_memory_mini_project_solution.py evaluate

생성 파일:
    outputs/chapter11_conversation_history.json
    outputs/chapter11_memory_store.json
    outputs/chapter11_memory_workflow.log
    outputs/chapter11_memory_evaluation.csv
    outputs/chapter11_memory_evaluation_report.md
"""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
HISTORY_PATH = OUTPUT_DIR / "chapter11_conversation_history.json"
MEMORY_PATH = OUTPUT_DIR / "chapter11_memory_store.json"
WORKFLOW_LOG_PATH = OUTPUT_DIR / "chapter11_memory_workflow.log"
EVALUATION_CSV_PATH = OUTPUT_DIR / "chapter11_memory_evaluation.csv"
EVALUATION_REPORT_PATH = OUTPUT_DIR / "chapter11_memory_evaluation_report.md"

MAX_RECENT_MESSAGES = 6
DEFAULT_TOP_K = 3

EXIT_COMMANDS = {"/exit", "/quit", "exit", "quit"}

HELP_TEXT = """
사용 가능한 명령:
/history        최근 대화 보기
/memory         저장된 메모리 보기
/clear          대화 기록 초기화
/clear-memory   장기 메모리 초기화
/help           도움말 보기
/exit           종료
""".strip()

SAMPLE_CONVERSATIONS = [
    "미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?",
    "그럼 제출 형식도 알려 주세요.",
    "방금 말한 내용을 표로 정리해 주세요.",
    "api key는 어떻게 관리하나요?",
    "제가 짧은 답변을 선호한다는 점을 기억해 주세요.",
    "앞으로 답변은 간단히 해 주세요.",
    "내 API Key는 abc123이라고 기억해 주세요.",
    "비밀번호는 1234라고 기억해 주세요.",
]

COURSE_FAQ = [
    {
        "keywords": ["미니 프로젝트", "결과물"],
        "answer": (
            "미니 프로젝트 결과물에는 PDF 보고서, 실행 가능한 코드, 그리고 검색 또는 메모리 동작을 확인할 수 있는 출력 로그가 포함되어야 합니다."
        ),
    },
    {
        "keywords": ["제출", "형식"],
        "answer": (
            "제출 형식은 보통 GitHub 저장소 링크와 함께 보고서 파일, 소스 코드 폴더, 실행 결과를 정리한 산출물을 포함하는 형태로 준비하면 됩니다."
        ),
    },
    {
        "keywords": ["표", "정리"],
        "answer": "직전 답변 내용을 표 형태로 정리해 드리겠습니다.",
    },
    {
        "keywords": ["memory", "메모리"],
        "answer": (
            "이 에이전트는 최근 대화 기록과 장기 메모리를 함께 사용합니다. 최근 대화는 현재 흐름을 보완하고, 장기 메모리는 사용자 선호나 작업 상태를 오래 유지하는 데 사용합니다."
        ),
    },
]

MEMORY_SAVE_SIGNALS = [
    "기억해 주세요",
    "기억해줘",
    "기억해",
    "앞으로",
    "선호합니다",
    "선호해요",
    "좋아합니다",
    "싫어합니다",
    "완료했습니다",
    "진행 상태",
    "다음 작업",
]

SECURITY_KEYWORDS = [
    "api key",
    "apikey",
    "token",
    "토큰",
    ".env",
    "환경 변수",
    "비밀번호",
    "password",
]

SECURITY_MANAGEMENT_KEYWORDS = [
    "관리",
    "저장",
    "보호",
    "어디",
    "어떻게",
    "필요",
]

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)api\s*key\s*(?:는|은|:|=)?\s*[A-Za-z0-9_\-]{4,}"),
    re.compile(r"(?i)token\s*(?:은|는|:|=)?\s*[A-Za-z0-9_\-]{4,}"),
    re.compile(r"(?i)password\s*(?:는|is|:|=)?\s*\S+"),
    re.compile(r"비밀번호"),
    re.compile(r"주민등록번호"),
    re.compile(r"\b01[016789]-?\d{3,4}-?\d{4}\b"),
    re.compile(r"(?i)sk-[A-Za-z0-9\-_]{4,}"),
]


@dataclass
class Message:
    """대화 메시지 스키마."""

    role: str
    content: str
    created_at: str


@dataclass
class MemoryItem:
    """장기 메모리 스키마."""

    id: str
    category: str
    content: str
    source: str
    importance: int
    created_at: str
    updated_at: str


@dataclass
class MemoryCandidate:
    """메모리 저장 후보 스키마."""

    category: str
    content: str
    source: str
    importance: int
    should_save: bool
    blocked_reason: str | None = None


@dataclass
class WorkflowResult:
    """한 턴의 workflow 실행 결과."""

    question: str
    recent_context: str
    retrieved_memories: list[MemoryItem]
    memory_candidates: list[MemoryCandidate]
    saved_memories: list[MemoryItem]
    answer: str


@dataclass
class EvaluationRow:
    """평가 결과 행 스키마."""

    turn_number: int
    question: str
    recent_context_created: bool
    retrieved_memory_count: int
    memory_candidate_count: int
    saved_memory_count: int
    answer_preview: str


def now_iso() -> str:
    """현재 시각을 ISO 문자열로 반환합니다."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_output_dir() -> None:
    """출력 디렉터리를 생성합니다."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: object) -> None:
    """JSON 파일을 저장합니다."""
    ensure_output_dir()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path, default: object) -> object:
    """JSON 파일을 읽고 실패하면 기본값을 반환합니다."""
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def message_from_dict(data: dict[str, object]) -> Message:
    """dict를 Message로 변환합니다."""
    return Message(
        role=str(data.get("role", "unknown")),
        content=str(data.get("content", "")),
        created_at=str(data.get("created_at", now_iso())),
    )


def memory_from_dict(data: dict[str, object]) -> MemoryItem:
    """dict를 MemoryItem으로 변환합니다."""
    return MemoryItem(
        id=str(data.get("id", "memory_unknown")),
        category=str(data.get("category", "project_state")),
        content=str(data.get("content", "")),
        source=str(data.get("source", "conversation")),
        importance=int(data.get("importance", 3)),
        created_at=str(data.get("created_at", now_iso())),
        updated_at=str(data.get("updated_at", now_iso())),
    )


def load_history() -> list[Message]:
    """대화 기록을 불러옵니다."""
    raw = read_json(HISTORY_PATH, [])

    if not isinstance(raw, list):
        return []

    history: list[Message] = []

    for item in raw:
        if isinstance(item, dict):
            history.append(message_from_dict(item))

    return history


def save_history(history: list[Message]) -> None:
    """대화 기록을 저장합니다."""
    write_json(HISTORY_PATH, [asdict(message) for message in history])


def append_message(role: str, content: str) -> Message:
    """대화 기록에 새 메시지를 추가합니다."""
    history = load_history()
    message = Message(role=role, content=content.strip(), created_at=now_iso())
    history.append(message)
    save_history(history)
    return message


def clear_history() -> None:
    """대화 기록을 초기화합니다."""
    save_history([])


def load_memories() -> list[MemoryItem]:
    """저장된 장기 메모리를 불러옵니다."""
    raw = read_json(MEMORY_PATH, [])

    if not isinstance(raw, list):
        return []

    memories: list[MemoryItem] = []

    for item in raw:
        if isinstance(item, dict):
            memories.append(memory_from_dict(item))

    return memories


def save_memories(memories: list[MemoryItem]) -> None:
    """장기 메모리를 저장합니다."""
    write_json(MEMORY_PATH, [asdict(memory) for memory in memories])


def clear_memories() -> None:
    """장기 메모리를 초기화합니다."""
    save_memories([])


def next_memory_id(memories: list[MemoryItem]) -> str:
    """다음 메모리 ID를 계산합니다."""
    return f"memory_{len(memories) + 1:03d}"


def add_memory(candidate: MemoryCandidate) -> MemoryItem:
    """메모리 후보를 실제 장기 메모리로 저장합니다."""
    memories = load_memories()
    timestamp = now_iso()
    memory = MemoryItem(
        id=next_memory_id(memories),
        category=candidate.category,
        content=candidate.content,
        source=candidate.source,
        importance=candidate.importance,
        created_at=timestamp,
        updated_at=timestamp,
    )
    memories.append(memory)
    save_memories(memories)
    return memory


def build_recent_context(history: list[Message], limit: int = MAX_RECENT_MESSAGES) -> str:
    """최근 대화 context 문자열을 생성합니다."""
    if not history:
        return ""

    lines = []

    for message in history[-limit:]:
        lines.append(f"{message.role}: {message.content}")

    return "\n".join(lines)


def tokenize(text: str) -> set[str]:
    """간단한 keyword 검색용 토큰 집합을 생성합니다."""
    tokens = re.findall(r"[A-Za-z0-9가-힣]+", text.lower())
    stopwords = {
        "은",
        "는",
        "이",
        "가",
        "을",
        "를",
        "에",
        "의",
        "로",
        "과",
        "와",
        "좀",
        "더",
        "그럼",
        "방금",
    }
    return {token for token in tokens if len(token) >= 2 and token not in stopwords}


def score_memory(question: str, memory: MemoryItem) -> int:
    """질문과 메모리의 관련도를 계산합니다."""
    question_tokens = tokenize(question)
    memory_tokens = tokenize(memory.content)

    score = len(question_tokens & memory_tokens) * 2
    score += memory.importance

    if memory.category == "user_preference":
        score += 1

    return score


def retrieve_related_memories(question: str, memories: list[MemoryItem], top_k: int = DEFAULT_TOP_K) -> list[MemoryItem]:
    """질문과 관련된 메모리를 검색합니다."""
    scored_rows: list[tuple[int, MemoryItem]] = []

    for memory in memories:
        score = score_memory(question, memory)

        if score > 0:
            scored_rows.append((score, memory))

    scored_rows.sort(key=lambda row: row[0], reverse=True)
    return [memory for _, memory in scored_rows[:top_k]]


def build_memory_context(memories: list[MemoryItem]) -> str:
    """검색된 메모리 목록을 context 문자열로 변환합니다."""
    if not memories:
        return ""

    return "\n".join(f"- [{memory.category}] {memory.content}" for memory in memories)


def contains_sensitive_info(text: str) -> bool:
    """민감정보가 포함되었는지 확인합니다."""
    normalized = text.strip()

    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(normalized):
            return True

    return False


def has_memory_save_intent(user_message: str) -> bool:
    """사용자가 메모리 저장을 명시적으로 요청했는지 판단합니다."""
    return any(signal in user_message for signal in MEMORY_SAVE_SIGNALS)


def is_security_management_question(question: str) -> bool:
    """보안 관리 방법을 묻는 일반 질문인지 판단합니다."""
    lowered = question.lower()
    has_security_keyword = any(keyword in lowered for keyword in SECURITY_KEYWORDS)
    has_management_keyword = any(keyword in question for keyword in SECURITY_MANAGEMENT_KEYWORDS)

    if not has_security_keyword:
        return False

    if has_memory_save_intent(question):
        return False

    return has_management_keyword or "api key" in lowered or "apikey" in lowered or "token" in lowered


def build_security_management_answer() -> str:
    """민감정보 관리 방법에 대한 규칙 기반 답변을 반환합니다."""
    return (
        "API Key나 토큰, 비밀번호 같은 민감정보는 코드에 직접 작성하지 말고 .env 파일 또는 환경 변수로 관리하세요. "
        ".env는 반드시 .gitignore에 추가하고 GitHub에 업로드하지 않는 것이 좋습니다."
    )


def infer_memory_category(user_message: str) -> str:
    """메모리 category를 추정합니다."""
    normalized = user_message.lower()

    if "선호" in user_message or "짧" in user_message or "간단" in user_message:
        return "user_preference"

    if "완료" in user_message or "진행" in user_message or "작성" in user_message:
        return "project_state"

    if "수업" in user_message or "강의" in user_message or "과제" in user_message:
        return "course_context"

    if "기억" in user_message or "다음" in user_message or "결정" in user_message:
        return "task_decision"

    return "project_state"


def estimate_importance(user_message: str) -> int:
    """메모리 중요도를 추정합니다."""
    if "반드시" in user_message or "꼭" in user_message or "기억" in user_message:
        return 5

    if "선호" in user_message or "짧" in user_message or "간단" in user_message:
        return 4

    return 3


def build_memory_candidates(user_message: str, assistant_message: str) -> list[MemoryCandidate]:
    """대화에서 메모리 저장 후보를 생성합니다."""
    candidates: list[MemoryCandidate] = []

    if not has_memory_save_intent(user_message):
        return candidates

    if contains_sensitive_info(user_message):
        candidates.append(
            MemoryCandidate(
                category="task_decision",
                content=user_message.strip(),
                source="conversation",
                importance=5,
                should_save=False,
                blocked_reason="민감정보가 포함되어 저장하지 않습니다.",
            )
        )
        return candidates

    should_remember = any(
        phrase in user_message
        for phrase in ["기억해", "기억해 주세요", "선호", "앞으로", "짧", "간단"]
    )

    if should_remember:
        candidates.append(
            MemoryCandidate(
                category=infer_memory_category(user_message),
                content=user_message.strip(),
                source="conversation",
                importance=estimate_importance(user_message),
                should_save=True,
            )
        )

    return candidates


def save_memory_candidates(candidates: list[MemoryCandidate]) -> list[MemoryItem]:
    """메모리 후보를 저장하고 저장된 메모리를 반환합니다."""
    if not candidates:
        return []

    existing_contents = {memory.content for memory in load_memories()}
    saved_memories: list[MemoryItem] = []

    for candidate in candidates:
        if not candidate.should_save:
            continue

        if candidate.content in existing_contents:
            continue

        saved_memory = add_memory(candidate)
        saved_memories.append(saved_memory)
        existing_contents.add(candidate.content)

    return saved_memories


def prefers_brief_answer(memories: list[MemoryItem]) -> bool:
    """저장된 메모리 중 짧은 답변 선호가 있는지 확인합니다."""
    for memory in memories:
        content = memory.content.lower()
        if "짧" in content or "간단" in content:
            return True

    return False


def build_table_answer_from_recent_context(recent_context: str) -> str:
    """최근 대화를 표로 정리한 답변을 생성합니다."""
    rows = []

    for line in recent_context.splitlines()[-4:]:
        if ": " not in line:
            continue
        role, content = line.split(": ", 1)
        rows.append(f"| {role} | {content} |")

    if not rows:
        return "정리할 최근 대화가 없어 표를 만들지 못했습니다."

    return "\n".join([
        "방금 대화를 표로 정리했습니다.",
        "",
        "| 역할 | 내용 |",
        "| --- | --- |",
        *rows,
    ])

def lookup_course_answer(question: str) -> str | None:
    """질문 keyword에 맞는 규칙 기반 답변을 반환합니다."""
    lowered = question.lower()

    for row in COURSE_FAQ:
        if all(keyword.lower() in lowered for keyword in row["keywords"]):
            return str(row["answer"])

    for row in COURSE_FAQ:
        if any(keyword.lower() in lowered for keyword in row["keywords"]):
            return str(row["answer"])

    return None


def generate_rule_based_answer(question: str, recent_context: str, retrieved_memories: list[MemoryItem]) -> str:
    """외부 LLM 없이 규칙 기반 답변을 생성합니다."""
    brief_mode = prefers_brief_answer(load_memories())

    if is_security_management_question(question):
        return build_security_management_answer()

    if "표" in question and "정리" in question:
        return build_table_answer_from_recent_context(recent_context)

    course_answer = lookup_course_answer(question)

    if course_answer:
        if brief_mode:
            return course_answer

        details = []

        if retrieved_memories:
            details.append("관련 메모리를 참고했습니다.")

        if recent_context:
            details.append("최근 대화 흐름도 반영했습니다.")

        if details:
            return f"{course_answer}\n\n" + " ".join(details)

        return course_answer

    if "기억" in question and retrieved_memories:
        first_memory = retrieved_memories[0]
        return f"현재 기억하고 있는 관련 메모리는 다음과 같습니다: {first_memory.content}"

    if brief_mode:
        return "질문을 확인했습니다. 현재 저장된 메모리와 최근 대화를 바탕으로 추가 설명이 필요하면 더 구체적으로 물어봐 주세요."

    return (
        "질문을 확인했습니다. 현재 저장된 메모리와 최근 대화 흐름을 살펴봤지만, "
        "정확히 대응하는 규칙 답변은 없었습니다. 제출 형식, 결과물, 메모리 동작처럼 더 구체적인 키워드로 질문해 주세요."
    )


def append_workflow_log(entry: dict[str, object]) -> None:
    """워크플로우 실행 로그를 JSON Lines 형식으로 추가합니다."""
    ensure_output_dir()
    with WORKFLOW_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_memory_workflow(question: str) -> WorkflowResult:
    """메모리 기반 workflow를 실행합니다."""
    history = load_history()
    memories = load_memories()

    recent_context = build_recent_context(history, limit=MAX_RECENT_MESSAGES)
    retrieved_memories = retrieve_related_memories(question, memories, top_k=DEFAULT_TOP_K)
    answer = generate_rule_based_answer(question, recent_context, retrieved_memories)

    append_message("user", question)
    append_message("assistant", answer)

    memory_candidates = build_memory_candidates(question, answer)
    saved_memories = save_memory_candidates(memory_candidates)

    append_workflow_log(
        {
            "timestamp": now_iso(),
            "question": question,
            "recent_context_created": bool(recent_context),
            "retrieved_memory_count": len(retrieved_memories),
            "memory_candidate_count": len(memory_candidates),
            "saved_memory_count": len(saved_memories),
            "answer_preview": answer[:120],
        }
    )

    return WorkflowResult(
        question=question,
        recent_context=recent_context,
        retrieved_memories=retrieved_memories,
        memory_candidates=memory_candidates,
        saved_memories=saved_memories,
        answer=answer,
    )


def format_memory(memory: MemoryItem) -> str:
    """메모리 항목을 출력용 문자열로 변환합니다."""
    return (
        f"[{memory.category}] {memory.content} "
        f"(importance={memory.importance}, source={memory.source})"
    )


def print_history(limit: int = 10) -> None:
    """최근 대화 기록을 출력합니다."""
    history = load_history()

    if not history:
        print("저장된 대화 기록이 없습니다.")
        return

    print("\n[최근 대화 기록]")
    for message in history[-limit:]:
        print(f"{message.role}: {message.content}")


def print_memories() -> None:
    """저장된 메모리를 출력합니다."""
    memories = load_memories()

    if not memories:
        print("저장된 메모리가 없습니다.")
        return

    print("\n[저장된 메모리]")
    for memory in memories:
        print(format_memory(memory))


def handle_command(command: str) -> bool:
    """CLI 명령을 처리합니다."""
    normalized = command.strip().lower()

    if normalized in EXIT_COMMANDS:
        print("대화를 종료합니다.")
        return False

    if normalized == "/history":
        print_history()
        return True

    if normalized == "/memory":
        print_memories()
        return True

    if normalized == "/clear":
        clear_history()
        print("대화 기록을 초기화했습니다.")
        return True

    if normalized == "/clear-memory":
        clear_memories()
        print("장기 메모리를 초기화했습니다.")
        return True

    if normalized == "/help":
        print(HELP_TEXT)
        return True

    print("알 수 없는 명령입니다. /help를 입력해 사용 가능한 명령을 확인하세요.")
    return True


def run_chat_cli() -> None:
    """대화형 CLI를 실행합니다."""
    ensure_output_dir()

    print("Chapter 11 Memory Mini Project CLI")
    print("명령어 목록을 보려면 /help를 입력하세요.")
    print("종료하려면 /exit를 입력하세요.\n")

    while True:
        user_input = input("사용자> ").strip()

        if not user_input:
            continue

        if user_input.startswith("/") or user_input.lower() in EXIT_COMMANDS:
            should_continue = handle_command(user_input)

            if not should_continue:
                break

            print()
            continue

        result = run_memory_workflow(user_input)
        print(f"에이전트> {result.answer}\n")

        if result.saved_memories:
            print("[새로 저장된 메모리]")
            for memory in result.saved_memories:
                print(format_memory(memory))
            print()

        blocked_candidates = [candidate for candidate in result.memory_candidates if not candidate.should_save]
        if blocked_candidates:
            print("[저장 차단된 메모리 후보]")
            for candidate in blocked_candidates:
                print(f"- {candidate.content} ({candidate.blocked_reason})")
            print()


def save_evaluation_csv(rows: list[EvaluationRow]) -> None:
    """평가 결과 CSV를 저장합니다."""
    ensure_output_dir()

    with EVALUATION_CSV_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "turn_number",
                "question",
                "recent_context_created",
                "retrieved_memory_count",
                "memory_candidate_count",
                "saved_memory_count",
                "answer_preview",
            ],
        )
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def save_evaluation_report(rows: list[EvaluationRow], final_memories: list[MemoryItem]) -> None:
    """평가 결과 Markdown 리포트를 저장합니다."""
    ensure_output_dir()

    lines = [
        "# Chapter 11 Memory Mini Project Evaluation",
        "",
        "이 파일은 `evaluate` 모드 실행 결과입니다.",
        "",
        "## Turn Summary",
        "",
        "| turn | question | recent context | retrieved memories | memory candidates | saved memories | answer preview |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in rows:
        lines.append(
            "| {turn_number} | {question} | {recent_context_created} | {retrieved_memory_count} | {memory_candidate_count} | {saved_memory_count} | {answer_preview} |".format(
                turn_number=row.turn_number,
                question=row.question.replace("|", "/"),
                recent_context_created="yes" if row.recent_context_created else "no",
                retrieved_memory_count=row.retrieved_memory_count,
                memory_candidate_count=row.memory_candidate_count,
                saved_memory_count=row.saved_memory_count,
                answer_preview=row.answer_preview.replace("|", "/"),
            )
        )

    lines.extend(
        [
            "",
            "## Final Memory Store",
            "",
        ]
    )

    if final_memories:
        for memory in final_memories:
            lines.append(f"- {format_memory(memory)}")
    else:
        lines.append("- 저장된 메모리가 없습니다.")

    preference_saved = any("짧" in memory.content or "간단" in memory.content for memory in final_memories)
    sensitive_saved = any(contains_sensitive_info(memory.content) for memory in final_memories)

    lines.extend(
        [
            "",
            "## Checks",
            "",
            f"- 사용자 선호 메모리 저장 여부: {'yes' if preference_saved else 'no'}",
            f"- 민감정보 메모리 저장 차단 여부: {'yes' if not sensitive_saved else 'no'}",
        ]
    )

    EVALUATION_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_evaluation() -> None:
    """샘플 대화를 기반으로 평가를 실행합니다."""
    ensure_output_dir()
    clear_history()
    clear_memories()
    WORKFLOW_LOG_PATH.write_text("", encoding="utf-8")

    rows: list[EvaluationRow] = []

    for turn_number, question in enumerate(SAMPLE_CONVERSATIONS, start=1):
        result = run_memory_workflow(question)
        rows.append(
            EvaluationRow(
                turn_number=turn_number,
                question=question,
                recent_context_created=bool(result.recent_context),
                retrieved_memory_count=len(result.retrieved_memories),
                memory_candidate_count=len(result.memory_candidates),
                saved_memory_count=len(result.saved_memories),
                answer_preview=result.answer.replace("\n", " ")[:120],
            )
        )

    final_memories = load_memories()
    save_evaluation_csv(rows)
    save_evaluation_report(rows, final_memories)

    print("[evaluation summary]")
    for row in rows:
        print(
            f"turn={row.turn_number}, recent_context={row.recent_context_created}, "
            f"retrieved={row.retrieved_memory_count}, candidates={row.memory_candidate_count}, "
            f"saved={row.saved_memory_count}"
        )

    print(f"\nCSV saved to: {EVALUATION_CSV_PATH}")
    print(f"Report saved to: {EVALUATION_REPORT_PATH}")


def print_usage() -> None:
    """CLI 사용법을 출력합니다."""
    print("사용법:")
    print("  python solutions/chapter11/chapter11_memory_mini_project_solution.py chat")
    print("  python solutions/chapter11/chapter11_memory_mini_project_solution.py evaluate")


def main() -> None:
    """프로그램 진입점입니다."""
    if len(sys.argv) < 2:
        print_usage()
        raise SystemExit(1)

    mode = sys.argv[1].strip().lower()

    if mode == "chat":
        run_chat_cli()
        return

    if mode == "evaluate":
        run_evaluation()
        return

    print_usage()
    raise SystemExit(1)


if __name__ == "__main__":
    main()