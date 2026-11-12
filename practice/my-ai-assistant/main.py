"""My AI Assistant — shared lesson foundation. Default mode: free, deterministic mock."""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Reply:
    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_input_tokens: int | None = None
    measurement_mode: str = "mock"
    fallback_reason: str | None = None


class ChatClient(Protocol):
    def ask(self, question: str) -> Reply: ...


class MockClient:
    def ask(self, question: str) -> Reply:
        question = question.strip()
        if not question:
            raise ValueError("질문을 입력해야 합니다.")
        return Reply(
            text=f"[MOCK 예시] 질문을 받았습니다: {question}\n실제 OpenAI API 응답이 아닙니다.",
            model="mock-fixture",
        )


class OpenAIClient:
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("OPENAI_API_KEY를 설정해야 합니다.")
        if not model:
            raise ValueError("OPENAI_MODEL을 설정해야 합니다.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Live 모드에는 pip install -r requirements.txt가 필요합니다.") from exc
        self.client = OpenAI(api_key=api_key, timeout=30.0, max_retries=0)
        self.model = model

    def ask(self, question: str) -> Reply:
        question = question.strip()
        if not question:
            raise ValueError("질문을 입력해야 합니다.")
        response = self.client.responses.create(
            model=self.model,
            input=question,
            max_output_tokens=128,
        )
        usage = getattr(response, "usage", None)
        detail = getattr(usage, "input_tokens_details", None) if usage is not None else None
        return Reply(
            text=response.output_text or "",
            model=getattr(response, "model", self.model),
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            cached_input_tokens=getattr(detail, "cached_tokens", None),
            measurement_mode="live",
        )


class GeminiClient:
    """2순위(폴백) 모델. 1순위 OpenAI 호출이 API 오류로 실패할 때 사용한다."""

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY를 설정해야 합니다.")
        if not model:
            raise ValueError("GEMINI_MODEL_NAME을 설정해야 합니다.")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("Live 모드에는 pip install -r requirements.txt가 필요합니다.") from exc
        self.client = genai.Client(api_key=api_key)
        self.config = types.GenerateContentConfig(max_output_tokens=128)
        self.model = model

    def ask(self, question: str) -> Reply:
        question = question.strip()
        if not question:
            raise ValueError("질문을 입력해야 합니다.")
        response = self.client.models.generate_content(
            model=self.model, contents=question, config=self.config,
        )
        usage = getattr(response, "usage_metadata", None)
        return Reply(
            text=response.text or "",
            model=getattr(response, "model_version", None) or self.model,
            input_tokens=getattr(usage, "prompt_token_count", None),
            output_tokens=getattr(usage, "candidates_token_count", None),
            cached_input_tokens=getattr(usage, "cached_content_token_count", None),
            measurement_mode="live",
        )


class FallbackClient:
    """1순위 호출이 API 오류로 실패하면 2순위 클라이언트로 한 번만 재시도한다.

    설정 오류(ValueError)는 숨기지 않는다. 2순위 클라이언트는 필요할 때만 만든다.
    """

    def __init__(self, primary: ChatClient, make_secondary):
        self.primary = primary
        self.make_secondary = make_secondary

    def ask(self, question: str) -> Reply:
        try:
            return self.primary.ask(question)
        except ValueError:
            raise
        except Exception as exc:
            reason = type(exc).__name__
            try:
                secondary = self.make_secondary()
            except ValueError as config_exc:
                raise ValueError(f"1순위 호출 실패({reason}) 후 2순위 설정 오류: {config_exc}") from exc
            return replace(secondary.ask(question), fallback_reason=reason)


def make_client(mode: str, api_key: str | None = None, model: str | None = None,
                provider: str = "openai") -> ChatClient:
    if mode == "mock":
        return MockClient()
    if mode == "live" and provider == "gemini":
        return GeminiClient(
            api_key if api_key is not None else os.getenv("GEMINI_API_KEY", ""),
            model if model is not None else os.getenv("GEMINI_MODEL_NAME", ""),
        )
    if mode == "live":
        return OpenAIClient(
            api_key if api_key is not None else os.getenv("OPENAI_API_KEY", ""),
            model if model is not None else os.getenv("OPENAI_MODEL", ""),
        )
    raise ValueError("mode는 mock 또는 live여야 합니다.")


def load_local_env() -> None:
    """Read only the explicitly supported keys from an untracked local .env file."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in {"OPENAI_API_KEY", "OPENAI_MODEL", "GEMINI_API_KEY", "GEMINI_MODEL_NAME"}:
            os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def run(question: str, client: ChatClient) -> Reply:
    return client.ask(question)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="My AI Assistant — OpenAI runtime foundation")
    parser.add_argument("question", nargs="?", default="이번 과정에서 무엇을 만들까요?")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock")
    parser.add_argument("--provider", choices=["openai", "gemini"], default="openai")
    parser.add_argument("--fallback", choices=["none", "openai", "gemini"], default="none",
                        help="1순위 호출이 API 오류로 실패하면 사용할 2순위 provider")
    args = parser.parse_args(argv)
    try:
        if args.mode == "live":
            load_local_env()
        client = make_client(args.mode, provider=args.provider)
        if args.mode == "live" and args.fallback != "none":
            client = FallbackClient(client, lambda: make_client("live", provider=args.fallback))
        reply = run(args.question, client)
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        # Do not print request bodies, credentials, or SDK error messages.
        print(f"API_ERROR: {type(exc).__name__} (민감정보 제외)", file=sys.stderr)
        return 3
    print(reply.text)
    print(f"\n[mode={reply.measurement_mode}; model={reply.model}]", file=sys.stderr)
    if reply.fallback_reason:
        print(f"[fallback used: primary failed with {reply.fallback_reason}]", file=sys.stderr)
    if reply.measurement_mode == "live":
        print(
            f"[usage input={reply.input_tokens}, output={reply.output_tokens}, "
            f"cached_input={reply.cached_input_tokens}]",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
