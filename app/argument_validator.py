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
