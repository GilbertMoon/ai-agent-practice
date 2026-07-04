# Chapter 8 검색 품질 평가표

이 파일은 `app/evaluate_retrieval.py` 실행 결과입니다.

검색 결과 수: top 3

## 평가 기준

| 항목 | 의미 | 점수 |
| --- | --- | --- |
| top 1 관련성 | 첫 번째 검색 결과가 질문에 직접 답하는가? | 0~2 |
| top 3 포함 여부 | 정답 근거가 top 3 안에 들어오는가? | 0 또는 1 |
| 근거 충분성 | top 1 chunk만으로 답변 근거가 충분한가? | 0~2 |
| 근거 표시 가능성 | source, section, chunk_id를 제시할 수 있는가? | 0~2 |

## 질문별 평가 요약

| 질문 | 기대 section | top1 관련성 | top3 포함 | 근거 충분성 | 근거 표시 | top1 chunk_id | top1 section | distance | 코멘트 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 민감 정보는 어디에 저장해야 하나요? | 4. API Key 보안 정책 | 2 | 1 | 2 | 2 | size500_overlap100_course_policy_long_p013_c001 | 4. API Key 보안 정책 | 0.7217 | top 1 결과가 질문에 직접 답할 가능성이 높음 |
| GitHub 제출 기준은 무엇인가요? | 6. GitHub 제출 기준 | 2 | 1 | 1 | 2 | course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.2348 | top 1 결과가 질문에 직접 답할 가능성이 높음 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | 7. 오류 질문 방법 | 2 | 1 | 2 | 2 | size300_overlap50_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.437 | top 1 결과가 질문에 직접 답할 가능성이 높음 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | 12. 미니 프로젝트 결과물 | 2 | 1 | 1 | 2 | course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.2763 | top 1 결과가 질문에 직접 답할 가능성이 높음 |

## 상세 검색 결과

### 질문: 민감 정보는 어디에 저장해야 하나요?

- 기대 section: `4. API Key 보안 정책`
- 코멘트: top 1 결과가 질문에 직접 답할 가능성이 높음

| rank | chunk_id | section | distance | 관련성 | 충분성 | 근거성 | text 요약 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | size500_overlap100_course_policy_long_p013_c001 | 4. API Key 보안 정책 | 0.7217 | 2 | 2 | 2 | Gemini API Key는 반드시 .env 파일에 저장합니다. API Key를 Python 코드에 직접 작성하지 않습니다. .env 파일은 .gitignore에 포함되어 있어야 하며 GitHub에 커밋하지 않습니다 |
| 2 | size300_overlap0_course_policy_long_p013_c001 | 4. API Key 보안 정책 | 0.7227 | 2 | 2 | 2 | Gemini API Key는 반드시 .env 파일에 저장합니다. API Key를 Python 코드에 직접 작성하지 않습니다. .env 파일은 .gitignore에 포함되어 있어야 하며 GitHub에 커밋하지 않습니다 |
| 3 | size300_overlap50_course_policy_long_p013_c001 | 4. API Key 보안 정책 | 0.7245 | 2 | 2 | 2 | Gemini API Key는 반드시 .env 파일에 저장합니다. API Key를 Python 코드에 직접 작성하지 않습니다. .env 파일은 .gitignore에 포함되어 있어야 하며 GitHub에 커밋하지 않습니다 |

### 질문: GitHub 제출 기준은 무엇인가요?

- 기대 section: `6. GitHub 제출 기준`
- 코멘트: top 1 결과가 질문에 직접 답할 가능성이 높음

| rank | chunk_id | section | distance | 관련성 | 충분성 | 근거성 | text 요약 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.2348 | 2 | 1 | 2 | ## 6. GitHub 제출 기준 |
| 2 | size500_overlap100_course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.2452 | 2 | 1 | 2 | ## 6. GitHub 제출 기준 |
| 3 | size300_overlap50_course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.2606 | 2 | 1 | 2 | ## 6. GitHub 제출 기준 |

### 질문: 오류 질문을 할 때 무엇을 함께 공유해야 하나요?

- 기대 section: `7. 오류 질문 방법`
- 코멘트: top 1 결과가 질문에 직접 답할 가능성이 높음

| rank | chunk_id | section | distance | 관련성 | 충분성 | 근거성 | text 요약 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | size300_overlap50_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.437 | 2 | 2 | 2 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 |
| 2 | size300_overlap0_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.4395 | 2 | 2 | 2 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 |
| 3 | size500_overlap100_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.4418 | 2 | 2 | 2 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 |

### 질문: 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?

- 기대 section: `12. 미니 프로젝트 결과물`
- 코멘트: top 1 결과가 질문에 직접 답할 가능성이 높음

| rank | chunk_id | section | distance | 관련성 | 충분성 | 근거성 | text 요약 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.2763 | 2 | 1 | 2 | ## 12. 미니 프로젝트 결과물 |
| 2 | size500_overlap100_course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.3218 | 2 | 1 | 2 | ## 12. 미니 프로젝트 결과물 |
| 3 | size300_overlap50_course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.3331 | 2 | 1 | 2 | ## 12. 미니 프로젝트 결과물 |
