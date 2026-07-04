import json
import re
from typing import Any

from tool_schemas import get_tool_declaration_by_name, get_tool_names


class ArgumentValidationError(ValueError):
    """tool arguments 검증 실패 시 사용하는 예외입니다."""


MAX_TOP_K = 5
MIN_TOP_K = 1
ALLOWED_DETAIL_LEVELS = {"brief", "detailed"}
ALLOWED_SECTIONS = {
    "1. 수업 운영 원칙",
    "2. 과제 제출 정책",
    "3. GitHub 제출 정책",
    "4. API Key 보안 정책",
    "5. 오류 질문 가이드",
    "6. 미니 프로젝트 안내",
}

SENSITIVE_PATTERNS = [
    r"(?i)api[_-]?key",
    r"(?i)secret",
    r"(?i)token",
    r"(?i)password",
    r"(?i)\.env",
    r"(?i)gemini_api_key",
    r"(?i)openai_api_key",
    r"(?i)upstage_api_key",
    r"[A-Za-z]:\\\\[^\s]+",
    r"/home/[^\s]+",
    r"/mnt/data/[^\s]+",
]


def get_parameter_schema(tool_name: str) -> dict[str, Any]:
    """tool 이름에 해당하는 parameters schema를 반환합니다."""
    declaration = get_tool_declaration_by_name(tool_name)
    if declaration is None:
        raise ArgumentValidationError(f"존재하지 않는 tool입니다: {tool_name}")
    return declaration.get("parameters", {})


def get_required_fields(tool_name: str) -> list[str]:
    """Function Declaration에서 required 필드 목록을 가져옵니다."""
    schema = get_parameter_schema(tool_name)
    return schema.get("required", [])


def get_properties(tool_name: str) -> dict[str, Any]:
    """Function Declaration에서 properties 정보를 가져옵니다."""
    schema = get_parameter_schema(tool_name)
    return schema.get("properties", {})


def validate_tool_name(tool_name: str) -> None:
    """
    tool 이름이 Function Declaration에 존재하는지 확인합니다。
    LLM이 요청한 tool 이름을 그대로 실행하면 안 됩니다。
    반드시 사전에 선언된 tool 이름인지 확인해야 합니다。
    """
    if tool_name not in get_tool_names():
        raise ArgumentValidationError(
            f"지원하지 않는 tool입니다: {tool_name}. "
            f"사용 가능한 tool: {get_tool_names()}"
        )


def validate_arguments_is_dict(arguments: Any) -> None:
    """arguments가 dict인지 확인합니다。"""
    if not isinstance(arguments, dict):
        raise ArgumentValidationError(
            f"arguments는 dict여야 합니다. 현재 타입: {type(arguments).__name__}"
        )


def validate_required_arguments(tool_name: str, arguments: dict[str, Any]) -> None:
    """required 필드가 arguments에 모두 포함되어 있는지 확인합니다。"""
    required_fields = get_required_fields(tool_name)
    missing_fields = [
        field
        for field in required_fields
        if field not in arguments or arguments[field] in (None, "")
    ]
    if missing_fields:
        raise ArgumentValidationError(
            f"필수 arguments가 누락되었습니다。 "
            f"tool={tool_name}, missing={missing_fields}"
        )


def validate_unknown_arguments(tool_name: str, arguments: dict[str, Any]) -> None:
    """Function Declaration에 정의되지 않은 argument가 들어왔는지 확인합니다。"""
    properties = get_properties(tool_name)
    allowed_fields = set(properties.keys())
    provided_fields = set(arguments.keys())

    unknown_fields = sorted(provided_fields - allowed_fields)

    if unknown_fields:
        raise ArgumentValidationError(
            f"정의되지 않은 arguments가 포함되어 있습니다。 "
            f"tool={tool_name}, unknown={unknown_fields}, allowed={sorted(allowed_fields)}"
        )


def validate_argument_type(
    field_name: str,
    value: Any,
    expected_type: str,
) -> None:
    """단일 argument 값의 타입을 검증합니다。"""
    if expected_type == "string":
        if not isinstance(value, str):
            raise ArgumentValidationError(
                f"argument 타입 오류: {field_name}은 string이어야 합니다。"
            )

    elif expected_type == "integer":
        if not isinstance(value, int):
            raise ArgumentValidationError(
                f"argument 타입 오류: {field_name}은 integer여야 합니다。"
            )

    elif expected_type == "number":
        if not isinstance(value, (int, float)):
            raise ArgumentValidationError(
                f"argument 타입 오류: {field_name}은 number여야 합니다。"
            )

    elif expected_type == "boolean":
        if not isinstance(value, bool):
            raise ArgumentValidationError(
                f"argument 타입 오류: {field_name}은 boolean이어야 합니다。"
            )

    elif expected_type == "object":
        if not isinstance(value, dict):
            raise ArgumentValidationError(
                f"argument 타입 오류: {field_name}은 object여야 합니다。"
            )

    elif expected_type == "array":
        if not isinstance(value, list):
            raise ArgumentValidationError(
                f"argument 타입 오류: {field_name}은 array여야 합니다。"
            )


def validate_argument_types(tool_name: str, arguments: dict[str, Any]) -> None:
    """Function Declaration의 type 정보를 기준으로 argument 타입을 검증합니다。"""
    properties = get_properties(tool_name)

    for field_name, value in arguments.items():
        field_schema = properties.get(field_name, {})
        expected_type = field_schema.get("type")

        if expected_type is None:
            continue

        validate_argument_type(
            field_name=field_name,
            value=value,
            expected_type=expected_type,
        )


def validate_enum_values(tool_name: str, arguments: dict[str, Any]) -> None:
    """enum이 정의된 argument의 값이 허용 범위 안에 있는지 검증합니다。"""
    properties = get_properties(tool_name)

    for field_name, value in arguments.items():
        field_schema = properties.get(field_name, {})
        allowed_values = field_schema.get("enum")

        if not allowed_values:
            continue

        if value not in allowed_values:
            raise ArgumentValidationError(
                f"허용되지 않은 enum 값입니다。 "
                f"field={field_name}, value={value!r}, allowed={allowed_values}"
            )


def validate_top_k_range(arguments: dict[str, Any]) -> None:
    """
    top_k 범위를 제한합니다。
    LLM이 top_k=1000처럼 큰 값을 만들더라도 그대로 실행하면 안 됩니다。
    검색 비용과 응답 크기를 통제하기 위해 최대값을 제한합니다。
    """
    if "top_k" not in arguments:
        return

    top_k = arguments["top_k"]

    if not isinstance(top_k, int):
        raise ArgumentValidationError("top_k는 integer여야 합니다。")

    if top_k < MIN_TOP_K:
        raise ArgumentValidationError(f"top_k는 {MIN_TOP_K} 이상이어야 합니다。")

    if top_k > MAX_TOP_K:
        raise ArgumentValidationError(f"top_k는 최대 {MAX_TOP_K}까지만 허용됩니다。")


def validate_section_value(arguments: dict[str, Any]) -> None:
    """
    section 값이 허용된 목록에 있는지 확인합니다。
    LLM이 임의의 section이나 내부 경로를 section 값으로 넣는 것을 방지합니다。
    """
    if "section" not in arguments:
        return

    section = arguments["section"]

    if section not in ALLOWED_SECTIONS:
        raise ArgumentValidationError(
            f"허용되지 않은 section입니다: {section}. "
            f"허용 section: {sorted(ALLOWED_SECTIONS)}"
        )


def validate_detail_level_value(arguments: dict[str, Any]) -> None:
    """detail_level 값이 허용된 범위인지 확인합니다。"""
    if "detail_level" not in arguments:
        return

    detail_level = arguments["detail_level"]

    if detail_level not in ALLOWED_DETAIL_LEVELS:
        raise ArgumentValidationError(
            f"허용되지 않은 detail_level입니다: {detail_level}. "
            f"허용 값: {sorted(ALLOWED_DETAIL_LEVELS)}"
        )


def contains_sensitive_text(value: Any) -> bool:
    """값 안에 민감정보 패턴이 포함되어 있는지 확인합니다。"""
    if not isinstance(value, str):
        return False

    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, value):
            return True

    return False


def validate_no_sensitive_arguments(arguments: dict[str, Any]) -> None:
    """
    arguments 안에 API Key, .env, 내부 경로 같은 민감정보가 포함되는지 확인합니다。
    """
    for field_name, value in arguments.items():
        if contains_sensitive_text(value):
            raise ArgumentValidationError(
                f"민감정보로 보이는 값이 argument에 포함되어 있습니다: {field_name}"
            )


def sanitize_text(text: str) -> str:
    """민감정보로 보이는 텍스트를 마스킹합니다。"""
    sanitized = text

    for pattern in SENSITIVE_PATTERNS:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized)

    return sanitized


def sanitize_tool_output(value: Any) -> Any:
    """
    tool 실행 결과에서 민감정보를 제거합니다。
    tool 결과를 모델이나 사용자에게 다시 전달하기 전에 사용할 수 있습니다。
    """
    if isinstance(value, str):
        return sanitize_text(value)

    if isinstance(value, list):
        return [sanitize_tool_output(item) for item in value]

    if isinstance(value, dict):
        sanitized_dict = {}

        for key, item in value.items():
            if contains_sensitive_text(str(key)):
                sanitized_dict[key] = "[REDACTED]"
            else:
                sanitized_dict[key] = sanitize_tool_output(item)

        return sanitized_dict

    return value


def make_safe_error_message(error: Exception) -> str:
    """
    내부 오류 메시지를 사용자에게 그대로 노출하지 않기 위한 안전한 메시지를 만듭니다。
    """
    raw_message = str(error)
    sanitized_message = sanitize_text(raw_message)

    if len(sanitized_message) > 300:
        sanitized_message = sanitized_message[:300] + "..."

    return sanitized_message


def normalize_arguments(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    tool별 기본값을 보완합니다。
    Function Declaration에는 기본값이 직접 들어 있지 않을 수 있으므로,
    실행 함수에서 자주 사용하는 기본값을 여기서 보완합니다。
    """
    normalized = dict(arguments)

    if tool_name in {
        "search_course_policy",
        "filter_course_policy_by_section",
        "search_course_policy_by_keyword",
    }:
        normalized.setdefault("top_k", 3)

    if tool_name == "search_course_policy_by_keyword":
        normalized.setdefault("question", "")

    if tool_name == "get_chapter_summary":
        normalized.setdefault("detail_level", "brief")

    return normalized


def validate_arguments(
    tool_name: str,
    arguments: dict[str, Any],
    allow_unknown: bool = False,
) -> dict[str, Any]:
    """
    tool_name과 arguments를 검증하고 정규화된 arguments를 반환합니다。

    검증 순서：
    1. tool 이름 확인
    2. arguments가 dict인지 확인
    3. required 필드 확인
    4. 정의되지 않은 argument 확인
    5. 타입 확인
    6. enum 값 확인
    7. top_k 범위 확인
    8. section 허용값 확인
    9. detail_level 허용값 확인
    10. 민감정보 포함 여부 확인
    11. 기본값 보완
    12. 기본값 보완 후 다시 범위 검증
    """
    validate_tool_name(tool_name)
    validate_arguments_is_dict(arguments)
    validate_required_arguments(tool_name, arguments)

    if not allow_unknown:
        validate_unknown_arguments(tool_name, arguments)

    validate_argument_types(tool_name, arguments)
    validate_enum_values(tool_name, arguments)

    validate_top_k_range(arguments)
    validate_section_value(arguments)
    validate_detail_level_value(arguments)
    validate_no_sensitive_arguments(arguments)

    normalized = normalize_arguments(tool_name, arguments)

    validate_top_k_range(normalized)
    validate_section_value(normalized)
    validate_detail_level_value(normalized)
    validate_no_sensitive_arguments(normalized)

    return normalized


def validate_function_call(function_call: dict[str, Any]) -> dict[str, Any]:
    """
    function_call dict 전체를 검증합니다。

    예상 입력 형식：
    {
        "name": "search_course_policy",
        "args": {
            "question": "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
            "top_k": 3
        }
    }
    """
    if not isinstance(function_call, dict):
        raise ArgumentValidationError("function_call은 dict여야 합니다。")

    tool_name = function_call.get("name")
    arguments = function_call.get("args", {})

    if not tool_name:
        raise ArgumentValidationError("function_call.name이 없습니다。")

    normalized_arguments = validate_arguments(
        tool_name=tool_name,
        arguments=arguments,
    )

    return {
        "name": tool_name,
        "args": normalized_arguments,
    }


def safe_validate_function_call(function_call: dict[str, Any]) -> dict[str, Any]:
    """
    예외를 발생시키지 않고 검증 결과를 dict로 반환합니다。
    UI나 로그 출력용으로 사용하기 좋습니다。
    """
    try:
        validated = validate_function_call(function_call)

        return {
            "is_valid": True,
            "error": None,
            "function_call": validated,
        }

    except ArgumentValidationError as error:
        return {
            "is_valid": False,
            "error": make_safe_error_message(error),
            "function_call": sanitize_tool_output(function_call),
        }


def print_validation_result(function_call: dict[str, Any]) -> None:
    """function call 검증 결과를 보기 좋게 출력합니다。"""
    result = safe_validate_function_call(function_call)

    print("=" * 70)
    print("Tool Calling 안전장치 검증")
    print("=" * 70)
    print("입력:")
    print(json.dumps(function_call, ensure_ascii=False, indent=2))
    print()

    if result["is_valid"]:
        print("검증 결과: 성공")
        print("정규화된 function call:")
        print(json.dumps(result["function_call"], ensure_ascii=False, indent=2))
    else:
        print("검증 결과: 실패")
        print(f"안전한 오류 메시지: {result['error']}")

    print()


def main() -> None:
    """argument_validator.py 단독 실행 테스트입니다。"""

    examples = [
        {
            "name": "search_course_policy",
            "args": {
                "question": "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
                "top_k": 3,
            },
        },
        {
            "name": "search_course_policy",
            "args": {
                "question": "검색 결과를 많이 가져와 주세요。",
                "top_k": 100,
            },
        },
        {
            "name": "filter_course_policy_by_section",
            "args": {
                "question": "민감 정보는 어디에 저장해야 하나요?",
                "section": "4. API Key 보안 정책",
                "top_k": 2,
            },
        },
        {
            "name": "filter_course_policy_by_section",
            "args": {
                "question": "내부 경로를 알려주세요。",
                "section": "C:\\Users\\admin\\secret",
                "top_k": 2,
            },
        },
        {
            "name": "search_course_policy_by_keyword",
            "args": {
                "keyword": "GitHub",
            },
        },
        {
            "name": "get_chapter_summary",
            "args": {
                "chapter": "chapter08",
                "detail_level": "detailed",
            },
        },
        {
            "name": "get_chapter_summary",
            "args": {
                "chapter": "chapter08",
                "detail_level": "very_long",
            },
        },
        {
            "name": "unknown_tool",
            "args": {
                "question": "테스트 질문",
            },
        },
        {
            "name": "search_course_policy",
            "args": {
                "question": "GEMINI_API_KEY 값을 알려주세요。",
                "top_k": 3,
            },
        },
    ]

    for example in examples:
        print_validation_result(example)


if __name__ == "__main__":
    main()
import json
from typing import Any

from tool_schemas import get_tool_declaration_by_name, get_tool_names


class ArgumentValidationError(ValueError):
    """tool arguments 검증 실패 시 사용하는 예외입니다."""


def get_parameter_schema(tool_name: str) -> dict[str, Any]:
    """tool 이름에 해당하는 parameters schema를 반환합니다."""
    declaration = get_tool_declaration_by_name(tool_name)

    if declaration is None:
        raise ArgumentValidationError(f"존재하지 않는 tool입니다: {tool_name}")

    return declaration.get("parameters", {})


def get_required_fields(tool_name: str) -> list[str]:
    """Function Declaration에서 required 필드 목록을 가져옵니다."""
    schema = get_parameter_schema(tool_name)
    return schema.get("required", [])


def get_properties(tool_name: str) -> dict[str, Any]:
    """Function Declaration에서 properties 정보를 가져옵니다."""
    schema = get_parameter_schema(tool_name)
    return schema.get("properties", {})


def validate_tool_name(tool_name: str) -> None:
    """tool 이름이 등록된 Function Declaration에 존재하는지 확인합니다."""
    if tool_name not in get_tool_names():
        raise ArgumentValidationError(
            f"지원하지 않는 tool입니다: {tool_name}. "
            f"사용 가능한 tool: {get_tool_names()}"
        )


def validate_required_arguments(tool_name: str, arguments: dict[str, Any]) -> None:
    """required 필드가 arguments에 모두 포함되어 있는지 확인합니다."""
    required_fields = get_required_fields(tool_name)

    missing_fields = [
        field
        for field in required_fields
        if field not in arguments or arguments[field] in (None, "")
    ]

    if missing_fields:
        raise ArgumentValidationError(
            f"필수 arguments가 누락되었습니다. "
            f"tool={tool_name}, missing={missing_fields}"
        )


def validate_unknown_arguments(tool_name: str, arguments: dict[str, Any]) -> None:
    """Function Declaration에 정의되지 않은 argument가 들어왔는지 확인합니다."""
    properties = get_properties(tool_name)
    allowed_fields = set(properties.keys())
    provided_fields = set(arguments.keys())

    unknown_fields = sorted(provided_fields - allowed_fields)

    if unknown_fields:
        raise ArgumentValidationError(
            f"정의되지 않은 arguments가 포함되어 있습니다. "
            f"tool={tool_name}, unknown={unknown_fields}, allowed={sorted(allowed_fields)}"
        )


def validate_argument_type(
    field_name: str,
    value: Any,
    expected_type: str,
) -> None:
    """단일 argument 값의 타입을 검증합니다."""
    if expected_type == "string":
        if not isinstance(value, str):
            raise ArgumentValidationError(
                f"argument 타입 오류: {field_name}은 string이어야 합니다. "
                f"현재 값: {value!r}"
            )

    elif expected_type == "integer":
        if not isinstance(value, int):
            raise ArgumentValidationError(
                f"argument 타입 오류: {field_name}은 integer여야 합니다. "
                f"현재 값: {value!r}"
            )

    elif expected_type == "number":
        if not isinstance(value, (int, float)):
            raise ArgumentValidationError(
                f"argument 타입 오류: {field_name}은 number여야 합니다. "
                f"현재 값: {value!r}"
            )

    elif expected_type == "boolean":
        if not isinstance(value, bool):
            raise ArgumentValidationError(
                f"argument 타입 오류: {field_name}은 boolean이어야 합니다. "
                f"현재 값: {value!r}"
            )

    elif expected_type == "object":
        if not isinstance(value, dict):
            raise ArgumentValidationError(
                f"argument 타입 오류: {field_name}은 object여야 합니다. "
                f"현재 값: {value!r}"
            )

    elif expected_type == "array":
        if not isinstance(value, list):
            raise ArgumentValidationError(
                f"argument 타입 오류: {field_name}은 array여야 합니다. "
                f"현재 값: {value!r}"
            )


def validate_argument_types(tool_name: str, arguments: dict[str, Any]) -> None:
    """Function Declaration의 type 정보를 기준으로 argument 타입을 검증합니다."""
    properties = get_properties(tool_name)

    for field_name, value in arguments.items():
        field_schema = properties.get(field_name, {})
        expected_type = field_schema.get("type")

        if expected_type is None:
            continue

        validate_argument_type(
            field_name=field_name,
            value=value,
            expected_type=expected_type,
        )


def validate_enum_values(tool_name: str, arguments: dict[str, Any]) -> None:
    """enum이 정의된 argument의 값이 허용 범위 안에 있는지 검증합니다."""
    properties = get_properties(tool_name)

    for field_name, value in arguments.items():
        field_schema = properties.get(field_name, {})
        allowed_values = field_schema.get("enum")

        if not allowed_values:
            continue

        if value not in allowed_values:
            raise ArgumentValidationError(
                f"허용되지 않은 enum 값입니다. "
                f"field={field_name}, value={value!r}, allowed={allowed_values}"
            )


def normalize_arguments(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    tool별 기본값을 보완합니다.

    Function Declaration에는 기본값이 직접 들어 있지 않을 수 있으므로,
    실행 함수에서 자주 사용하는 기본값을 여기서 보완합니다.
    """
    normalized = dict(arguments)

    if tool_name in {
        "search_course_policy",
        "filter_course_policy_by_section",
        "search_course_policy_by_keyword",
    }:
        normalized.setdefault("top_k", 3)

    if tool_name == "search_course_policy_by_keyword":
        normalized.setdefault("question", "")

    if tool_name == "get_chapter_summary":
        normalized.setdefault("detail_level", "brief")

    return normalized


def validate_arguments(
    tool_name: str,
    arguments: dict[str, Any],
    allow_unknown: bool = False,
) -> dict[str, Any]:
    """
    tool_name과 arguments를 검증하고 정규화된 arguments를 반환합니다.

    검증 순서:
    1. tool 이름 확인
    2. arguments가 dict인지 확인
    3. required 필드 확인
    4. 정의되지 않은 argument 확인
    5. 타입 확인
    6. enum 값 확인
    7. 기본값 보완
    """
    validate_tool_name(tool_name)

    if not isinstance(arguments, dict):
        raise ArgumentValidationError(
            f"arguments는 dict여야 합니다. 현재 타입: {type(arguments).__name__}"
        )

    validate_required_arguments(tool_name, arguments)

    if not allow_unknown:
        validate_unknown_arguments(tool_name, arguments)

    validate_argument_types(tool_name, arguments)
    validate_enum_values(tool_name, arguments)

    return normalize_arguments(tool_name, arguments)


def validate_function_call(function_call: dict[str, Any]) -> dict[str, Any]:
    """
    function_call dict 전체를 검증합니다.

    예상 입력 형식:
    {
        "name": "search_course_policy",
        "args": {
            "question": "오류 질문을 할 때 무엇을 공유해야 하나요?",
            "top_k": 3
        }
    }
    """
    if not isinstance(function_call, dict):
        raise ArgumentValidationError("function_call은 dict여야 합니다.")

    tool_name = function_call.get("name")
    arguments = function_call.get("args", {})

    if not tool_name:
        raise ArgumentValidationError("function_call.name이 없습니다.")

    normalized_arguments = validate_arguments(
        tool_name=tool_name,
        arguments=arguments,
    )

    return {
        "name": tool_name,
        "args": normalized_arguments,
    }


def safe_validate_function_call(function_call: dict[str, Any]) -> dict[str, Any]:
    """
    예외를 발생시키지 않고 검증 결과를 dict로 반환합니다.
    UI나 로그 출력용으로 사용하기 좋습니다.
    """
    try:
        validated = validate_function_call(function_call)

        return {
            "is_valid": True,
            "error": None,
            "function_call": validated,
        }

    except ArgumentValidationError as error:
        return {
            "is_valid": False,
            "error": str(error),
            "function_call": function_call,
        }


def print_validation_result(function_call: dict[str, Any]) -> None:
    """function call 검증 결과를 보기 좋게 출력합니다."""
    result = safe_validate_function_call(function_call)

    print("=" * 70)
    print("Function Call Arguments 검증")
    print("=" * 70)
    print("입력:")
    print(json.dumps(function_call, ensure_ascii=False, indent=2))
    print()

    if result["is_valid"]:
        print("검증 결과: 성공")
        print("정규화된 function call:")
        print(json.dumps(result["function_call"], ensure_ascii=False, indent=2))
    else:
        print("검증 결과: 실패")
        print(f"오류: {result['error']}")

    print()


def main() -> None:
    """argument_validator.py 단독 실행 테스트입니다."""
    examples = [
        {
            "name": "search_course_policy",
            "args": {
                "question": "오류 질문을 할 때 무엇을 함께 공유해야 하나요?",
                "top_k": 3,
            },
        },
        {
            "name": "filter_course_policy_by_section",
            "args": {
                "question": "민감 정보는 어디에 저장해야 하나요?",
                "section": "4. API Key 보안 정책",
            },
        },
        {
            "name": "search_course_policy_by_keyword",
            "args": {
                "keyword": "GitHub",
            },
        },
        {
            "name": "get_chapter_summary",
            "args": {
                "chapter": "chapter08",
                "detail_level": "detailed",
            },
        },
        {
            "name": "get_chapter_summary",
            "args": {
                "chapter": "chapter08",
                "detail_level": "very_long",
            },
        },
        {
            "name": "search_course_policy",
            "args": {
                "top_k": 3,
            },
        },
        {
            "name": "unknown_tool",
            "args": {
                "question": "테스트 질문",
            },
        },
    ]

    for example in examples:
        print_validation_result(example)


if __name__ == "__main__":
    main()
