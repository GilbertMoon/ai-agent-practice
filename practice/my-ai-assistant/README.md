# My AI Assistant — Claude Code 개발 + OpenAI API 실행

**개발 보조 도구는 Claude Code, 학생이 만드는 AI 비서의 실제 모델은 OpenAI API**입니다. 두 서비스의 인증/과금은 별개입니다.

현재 단계는 A3 최소 실행 기반입니다. RAG, Tool, MCP, Memory, AgentOps는 후속 강의에서 누적합니다.

## Mock 실행 — API 키 불필요

Windows PowerShell:

```powershell
Set-Location C:\dev\ai-agent-practice\practice\my-ai-assistant
# 처음 실습할 때만 가상환경 생성 (이미 있다면 생략)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py "이번 주 과제를 정리해 줘"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`[MOCK 예시]`는 실제 모델 답변이 아닙니다. 공통 `requirements.txt`에는 후속 Lesson 06에서 사용할 Chroma가 포함되어 있으므로 Lesson 01에서 설치해 두면 전체 회귀 테스트를 실행할 수 있습니다. Mock 실행 자체는 API Key와 외부 모델 호출이 필요하지 않습니다.

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

## Lesson 02 — 반복 질문용 콘솔 프로그램

```powershell
Set-Location C:\dev\ai-agent-practice\practice\my-ai-assistant
python chat_loop.py --mode mock
python -m unittest discover -s tests -v
```

`chat_loop.py`는 기존 `main.py`의 Mock/OpenAI 클라이언트를 재사용합니다. `exit` 또는 `quit`로 종료합니다. 각 질문은 **독립 요청**으로 처리하며 현재는 과거 질문을 다음 요청에 전달하지 않습니다. API Key 설정이 완료되었다면 `python chat_loop.py --mode live`를 실행할 수 있으나, **입력한 질문마다 API 요금이 발생할 수 있습니다**.

강의안은 별도 비공개 강의 저장소에서 관리하고, 학생에게 공개할 코드·이미지는 이 공개 저장소에 배포합니다.

## Lesson 03 — Prompt & Context 비교

```powershell
python prompt_compare.py "AI Agent와 챗봇의 차이는?"
python prompt_compare.py "과제 제출 시간은?" --context "수업 공지: 과제는 금요일 오후 6시까지 제출합니다."
```

기본값 `preview`는 프롬프트 구성만 표시하고 API를 호출하지 않습니다. `--mode live`는 기본·구조화 프롬프트 **최대 2회**의 OpenAI API 호출을 수행하므로 비용이 발생할 수 있습니다.

## Lesson 04 — 문서 검색과 근거 기반 답변

```powershell
python document_qa.py "과제 제출 기한은 언제인가요?"
python document_qa.py "우주선 연료는 무엇인가요?"
python -m unittest discover -s tests -v
```

`data/lesson04_notice.md`에서 단순 키워드로 관련 문단을 찾습니다. 검색 결과는 **문서 원문이지 AI 생성 답변이 아닙니다**. 기본 `preview`는 API 키 없이 실행됩니다. 근거가 없는 질문은 `--mode live`에서도 **API 호출 0회**로 답변을 보류합니다. 실제 근거 기반 모델 답변은 `python document_qa.py "과제 제출 기한은 언제인가요?" --mode live`로 선택적으로 실행할 수 있으며 API 요금이 발생할 수 있습니다.

## Lesson 05 — 키워드 검색과 벡터 유사도 비교

기본 모드는 **수동으로 정의한 학습용 벡터 Fixture**입니다. 실제 모델 임베딩이나 AI 의미 이해를 증명하지 않습니다.

```powershell
python document_qa.py "마감일"
python embedding_search.py "마감일"
python embedding_search.py "문의 게시판"
python -m unittest discover -s tests -v
```

OpenAI Embeddings API의 실측 결과를 별도로 확인하려면 로컬 `.env`에 `OPENAI_API_KEY`와 사용 가능한 **임베딩 전용** `OPENAI_EMBEDDING_MODEL`을 설정한 뒤 `python embedding_search.py "마감일" --mode live`를 명시적으로 실행합니다. 이때 질문과 문단을 전송하고 API 사용량에 따라 별도 요금이 발생할 수 있습니다. 기본 Fixture는 API 호출이 없습니다.

## Lesson 06 — Chroma 영속 벡터 저장소

Lesson 05의 벡터 검색 결과를 Chroma 컬렉션에 저장하고, **별도의 프로세스에서 다시 열어 검색**합니다.

```powershell
python -m pip install -r requirements-lesson06.txt
python vector_store.py index
python vector_store.py count
python vector_store.py query "마감일"
python -m unittest discover -s tests -v
```

기본 Fixture는 수동 정의한 3차원 학습 벡터를 사용하며 **외부 API 요청을 보내지 않습니다.** Chroma의 자동 임베딩도 비활성화됩니다. 로컬 저장 폴더 `.chroma_lesson06/`는 Git에서 제외됩니다.

선택적 OpenAI Live 모드는 로컬 `.env`의 `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL=text-embedding-3-small` 설정을 사용합니다.

```powershell
python vector_store.py index --mode live
python vector_store.py count --mode live
python vector_store.py query "마감일" --mode live
```

**Live index와 Live query는 각각 임베딩 API 요청이 발생할 수 있습니다.** 모델을 바꿀 경우 기존 Live 컬렉션의 벡터와 혼용하지 마세요. 이번 실습은 조회 결과의 `distance`가 코사인 **유사도**가 아닌 코사인 **거리**라는 점도 확인합니다.
