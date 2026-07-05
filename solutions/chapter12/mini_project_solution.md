# Chapter 12 미니 프로젝트 솔루션

## 목표

역할 분담형 수업 공지 분석·안내문 작성 에이전트를 구현합니다.

사용자 요청을 입력하면 여러 agent가 하나의 shared state를 기준으로 협업합니다.

```text
Planner
→ Researcher
→ Writer
→ Reviewer
→ Writer revision
→ Final Answer
```

---

## 권장 파일 구조

```text
ai-agent-practice/
├── app/
│   ├── agent_schema.py
│   ├── shared_state.py
│   ├── planner_agent.py
│   ├── researcher_agent.py
│   ├── writer_agent.py
│   ├── reviewer_agent.py
│   ├── coordinator.py
│   ├── collaboration_logger.py
│   ├── multi_agent_workflow.py
│   └── evaluate_multi_agent.py
├── data/
│   └── sample_tasks.json
├── outputs/
│   └── multi_agent_evaluation.csv
├── collaboration.log
└── solutions/
    └── chapter12/
        └── mini_project_solution.md
```

---

## 구현 기준

### 1. AgentSpec schema

`app/agent_schema.py`에서 agent의 이름, 역할, 목표, 입력, 출력, 도구 사용 여부를 정의합니다.

필수 agent는 다음과 같습니다.

```text
- Planner Agent
- Researcher Agent
- Writer Agent
- Reviewer Agent
```

---

### 2. Shared State

`app/shared_state.py`에서 여러 agent가 함께 사용하는 state를 정의합니다.

핵심 state key는 다음과 같습니다.

```text
user_request
memory_context
plan
research_notes
draft_answer
review_feedback
final_answer
revision_count
logs
error
```

---

### 3. Planner Agent

`app/planner_agent.py`는 사용자 요청을 실행 가능한 작업 단계로 나눕니다.

예상 출력은 다음과 같습니다.

```text
- 사용자 요청 의도 파악
- 필요한 조건 확인
- 공지/과제/마감일/제출 형식 분리
- 학생 안내문 작성 단계 정의
```

---

### 4. Researcher Agent

`app/researcher_agent.py`는 사용자 요청과 plan을 기준으로 필요한 확인 사항을 정리합니다.

예상 출력은 `research_notes`에 저장됩니다.

```text
- 요청 요약
- 과제 조건 확인 필요
- 제출 방식 확인 필요
- 마감일 확인 필요
- 평가 기준 확인 필요
```

---

### 5. Writer Agent

`app/writer_agent.py`는 plan과 research_notes를 바탕으로 초안과 최종 답변을 작성합니다.

핵심 함수는 다음과 같습니다.

```text
writer_agent
revise_answer
finalize_answer
```

---

### 6. Reviewer Agent

`app/reviewer_agent.py`는 초안에서 누락된 항목이나 확인이 필요한 항목을 찾습니다.

예상 feedback 예시는 다음과 같습니다.

```text
- 제출 항목 확인 필요
- 마감일 확인 필요
- 평가 기준 확인 필요
```

---

### 7. Coordinator

`app/coordinator.py`는 agent 실행 순서를 제어합니다.

로깅 파일이 아직 없는 단계에서도 실행되도록 다음과 같이 선택적 import를 적용합니다.

```python
try:
    from collaboration_logger import log_agent_step
except ModuleNotFoundError:
    def log_agent_step(state, agent_name, status="success", message="", **kwargs):
        return state
```

이후 `app/collaboration_logger.py`를 추가하면 자동으로 collaboration log가 기록됩니다.

---

### 8. Collaboration Logger

`app/collaboration_logger.py`는 agent 실행 로그를 state와 파일에 함께 기록합니다.

생성되는 로그 파일은 다음과 같습니다.

```text
collaboration.log
```

로그 항목은 다음과 같습니다.

```text
timestamp
agent_name
input_keys
output_keys
status
message
```

---

### 9. Multi-Agent Workflow

`app/multi_agent_workflow.py`는 전체 workflow 실행 진입점입니다.

실행 명령은 다음과 같습니다.

```bash
python app/multi_agent_workflow.py
```

예상 출력은 다음과 같습니다.

```text
Chapter 12 Multi-Agent Workflow
======================================================================
[상태 요약]
{
  "plan_count": 6,
  "research_note_count": 5,
  "has_draft_answer": true,
  "review_feedback_count": 1,
  "has_final_answer": true,
  "log_count": 5,
  "error": null
}

[최종 답변]
안녕하세요. 아래와 같이 안내드립니다.
...
```

---

### 10. Evaluation

`app/evaluate_multi_agent.py`는 `data/sample_tasks.json`을 기준으로 여러 task를 실행하고 결과를 CSV로 저장합니다.

실행 명령은 다음과 같습니다.

```bash
python app/evaluate_multi_agent.py
```

생성 파일은 다음과 같습니다.

```text
multi_agent_evaluation.csv
```

---

## data/sample_tasks.json 예시

```json
[
  {
    "id": "task_001",
    "title": "학생 안내문 작성",
    "user_request": "이번 주 수업 공지와 과제 조건을 종합해서 학생들에게 보낼 안내문을 작성해 주세요.",
    "expected_agents": ["Planner Agent", "Researcher Agent", "Writer Agent", "Reviewer Agent"],
    "expected_outputs": ["plan", "research_notes", "draft_answer", "review_feedback", "final_answer"]
  },
  {
    "id": "task_002",
    "title": "기말 프로젝트 제출 조건 정리",
    "user_request": "기말 프로젝트 제출 조건을 정리하고, 누락된 내용이 있으면 확인 필요라고 표시해 주세요.",
    "expected_agents": ["Planner Agent", "Researcher Agent", "Writer Agent", "Reviewer Agent"],
    "expected_outputs": ["plan", "research_notes", "draft_answer", "review_feedback", "final_answer"]
  },
  {
    "id": "task_003",
    "title": "평가 기준 포함 안내",
    "user_request": "학생들이 혼동하지 않도록 제출물, 제출 형식, 마감일, 평가 기준을 나누어 안내해 주세요.",
    "expected_agents": ["Planner Agent", "Researcher Agent", "Writer Agent", "Reviewer Agent"],
    "expected_outputs": ["plan", "research_notes", "draft_answer", "review_feedback", "final_answer"]
  },
  {
    "id": "task_004",
    "title": "간단 개념 설명",
    "user_request": "멀티 에이전트가 무엇인지 짧게 설명해 주세요.",
    "expected_agents": ["Planner Agent", "Researcher Agent", "Writer Agent", "Reviewer Agent"],
    "expected_outputs": ["plan", "research_notes", "draft_answer", "review_feedback", "final_answer"]
  }
]
```

---

## 실행 방법

### 1. 가상환경 활성화

Windows PowerShell 기준입니다.

```powershell
cd D:\DEV\ai-agent-practice
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install python-dotenv
```

이미 가상환경이 있다면 활성화만 합니다.

```powershell
cd D:\DEV\ai-agent-practice
.\.venv\Scripts\Activate.ps1
```

---

### 2. Workflow 실행

```powershell
python app/multi_agent_workflow.py
```

확인할 항목은 다음과 같습니다.

```text
- plan_count가 1 이상인지
- research_note_count가 1 이상인지
- has_draft_answer가 true인지
- has_final_answer가 true인지
- error가 null인지
```

---

### 3. 로그 확인

```powershell
Get-Content collaboration.log
```

정상적으로 실행되면 다음 agent 로그가 기록됩니다.

```text
Planner Agent
Researcher Agent
Writer Agent
Reviewer Agent
Coordinator
```

---

### 4. 평가 실행

```powershell
python app/evaluate_multi_agent.py
```

정상 실행 예시는 다음과 같습니다.

```text
Chapter 12 Multi-Agent Evaluation
total: 4
saved: multi_agent_evaluation.csv
----------------------------------------------------------------------
task_id: task_001
title: 학생 안내문 작성
plan_count: 6
research_notes_count: 5
review_feedback_count: 1
final_answer_exists: 1
expected_agent_coverage: 1
```

---

### 5. 평가 CSV 확인

```powershell
Get-Content multi_agent_evaluation.csv
```

평가 CSV에는 다음 항목이 포함됩니다.

```text
task_id
title
plan_exists
plan_count
research_notes_count
draft_exists
review_feedback_count
final_answer_exists
revision_applied
log_count
expected_agent_coverage
error
```

---

## 통과 기준

```text
- python app/multi_agent_workflow.py 실행 시 최종 답변이 출력된다.
- collaboration.log 파일이 생성된다.
- collaboration.log에 Planner, Researcher, Writer, Reviewer, Coordinator 로그가 남는다.
- python app/evaluate_multi_agent.py 실행 시 total: 4가 출력된다.
- multi_agent_evaluation.csv 파일이 생성된다.
- 각 task의 final_answer_exists 값이 1이다.
- 각 task의 expected_agent_coverage 값이 1이다.
```

---

## 확장 과제

```text
- memory_context를 researcher/writer에 연결
- reviewer를 fact reviewer와 style reviewer로 분리
- 실패한 agent만 재실행
- token/cost/latency 추정 로그 추가
- Chapter 13 evaluation pipeline과 연결
```
