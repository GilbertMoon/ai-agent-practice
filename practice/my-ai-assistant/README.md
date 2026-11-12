# My AI Assistant — Claude Code 개발 + OpenAI API 실행

**개발 보조 도구는 Claude Code, 학생이 만드는 AI 비서의 실제 모델은 OpenAI API**입니다. 두 서비스의 인증/과금은 별개입니다.

현재 단계는 A3 최소 실행 기반입니다. RAG, Tool, MCP, Memory, AgentOps는 후속 강의에서 누적합니다.

## Mock 실행 — API 키 불필요

Windows PowerShell:

```powershell
Set-Location C:\dev\ai-agent-engineering-book\practice\my-ai-assistant
python main.py "이번 주 과제를 정리해 줘"
python -m unittest discover -s tests -v
```

`[MOCK 예시]`는 실제 모델 답변이 아닙니다.

## 실제 OpenAI API 호출 — 유료일 수 있음

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

`.env`에 실제 `OPENAI_API_KEY`와 **해당 계정에서 사용 가능한** `OPENAI_MODEL`을 입력합니다. 키는 코드/채팅/스크린샷/커밋에 넣지 않습니다. `.env`는 Git 제외 대상입니다.

```powershell
python main.py --mode live "안녕하세요. 한 문장으로 자기소개해 주세요."
```

- 한 번 실행하면 최대 **한 번의 Responses API 요청**을 시도합니다(SDK retry 0, 출력 최대 128 토큰, Timeout 30초).
- 출력에는 사용 모델·입력/출력 토큰·cached input tokens(있을 때만)을 기록합니다. 미제공은 `None`으로 남깁니다.
- 요청에 따라 API 요금이 발생하며 **ChatGPT 구독이나 Claude Code 구독과 별도 과금**될 수 있습니다.
- 모델/요금/지원 기능은 [OpenAI 개발자 문서](https://platform.openai.com/docs) 및 [API 요금표](https://platform.openai.com/pricing)에서 확인합니다. 모델 ID/요금을 임의로 고정하지 않습니다.
- 초기 A3의 비용은 계산하지 않습니다. A3-05에서 모델별 단가와 실제 Usage로 계산하도록 확장합니다.

## 2순위 모델(Gemini)로 폴백 — 선택

1순위 OpenAI 호출이 **API 오류**(잘못된 모델 ID, 인증 실패, 네트워크 오류 등)로 실패하면 Gemini를 한 번 더 호출하도록 지정할 수 있습니다.

```powershell
python main.py --mode live --fallback gemini "안녕하세요. 한 문장으로 자기소개해 주세요."
```

- `.env`에 `GEMINI_API_KEY`와 `GEMINI_MODEL_NAME`(예: `gemini-flash-lite-latest`)을 추가로 입력합니다. 변수 이름은 2장 강의안과 같습니다.
- 1순위가 성공하면 Gemini는 호출하지 않습니다. 2순위가 사용되면 `[fallback used: primary failed with <오류 유형>]`이 표시됩니다.
- 키·모델 누락 같은 **설정 오류는 폴백하지 않고** 바로 알려 줍니다.
- Gemini만 단독으로 호출하려면 `--provider gemini`를 사용합니다.

**검증 기준:** Mock 테스트, API Key/Model 누락 테스트, 폴백 동작 테스트(가짜 클라이언트 사용, API 키 불필요), 실제 Live 응답과 Usage를 구분합니다. Live 검증 결과는 `docs/improvement/A3_FOUNDATION_IMPLEMENTATION_REPORT.md`에 기록합니다.
