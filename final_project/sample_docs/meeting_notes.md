# 회의록 샘플

## 2026년 7월 AgentOps 프로젝트 회의

참석자: 기획자, 개발자, 운영 담당자

### 논의 내용

- 최종 프로젝트는 업무 문서 기반 AI Agent Assistant로 진행합니다.
- 기본 검색은 Markdown 문서 keyword search로 시작합니다.
- 실제 LLM API 연결은 확장 과제로 둡니다.
- 모든 요청에는 trace_id를 부여합니다.
- 평가 결과는 CSV로 저장합니다.
- 실패 유형은 retrieval_error, writing_error, safety_error, quality_regression으로 우선 분류합니다.

### 액션 아이템

- 샘플 문서 3개 작성
- smoke test 작성
- latest_report.md 생성 구조 확인
- improvement_backlog.md 생성 구조 확인