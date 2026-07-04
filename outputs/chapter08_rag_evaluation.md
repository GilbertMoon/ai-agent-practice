# Chapter 8 RAG 답변 품질 평가

이 파일은 `app/evaluate_rag_answer.py` 실행 결과입니다.

검색 결과 수: top 3

## 평가 기준

| 항목 | 의미 | 점수 |
| --- | --- | --- |
| 답변 관련성 | 질문에 맞게 답했는가? | 0~2 |
| 충실성 | 검색된 context에 근거해 답했는가? | 0~2 |
| 근거성 | 답변에 source, section, chunk_id가 포함되는가? | 0~2 |
| 간결성 | 불필요하게 길지 않은가? | 0~2 |

## 질문별 답변 품질 요약

| 질문 | 답변 관련성 | 충실성 | 근거성 | 간결성 | 총점 | top context | 코멘트 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 민감 정보는 어디에 저장해야 하나요? | 2 | 2 | 2 | 2 | 8 | size500_overlap100_course_policy_long_p013_c001 | 질문에 적절하고 context에 근거한 답변으로 보임 |
| GitHub 제출 기준은 무엇인가요? | 1 | 2 | 2 | 2 | 7 | course_policy_long_p018_c001 | 일부 관련성은 있으나 근거성 또는 충실성 확인 필요 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | 2 | 2 | 2 | 2 | 8 | size300_overlap50_course_policy_long_p022_c001 | 질문에 적절하고 context에 근거한 답변으로 보임 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | 1 | 2 | 2 | 2 | 7 | course_policy_long_p036_c001 | 일부 관련성은 있으나 근거성 또는 충실성 확인 필요 |

## 상세 답변

### 질문: 민감 정보는 어디에 저장해야 하나요?

#### 생성 답변

답변: Gemini API Key와 같은 민감 정보는 반드시 .env 파일에 저장해야 합니다. 코드에 직접 작성해서는 안 되며, .env 파일은 .gitignore에 포함하여 GitHub에 커밋되지 않도록 관리해야 합니다.

근거: size500_overlap100_course_policy_long_p013_c001 (4. API Key 보안 정책)

#### 검색 context

| rank | chunk_id | section | distance | text 요약 |
| --- | --- | --- | --- | --- |
| 1 | size500_overlap100_course_policy_long_p013_c001 | 4. API Key 보안 정책 | 0.7217 | Gemini API Key는 반드시 .env 파일에 저장합니다. API Key를 Python 코드에 직접 작성하지 않습니다. .env 파일은 .gitignore에 포함되어 있어야 하며 GitHub에 커밋하지 않습니다 |
| 2 | size300_overlap0_course_policy_long_p013_c001 | 4. API Key 보안 정책 | 0.7227 | Gemini API Key는 반드시 .env 파일에 저장합니다. API Key를 Python 코드에 직접 작성하지 않습니다. .env 파일은 .gitignore에 포함되어 있어야 하며 GitHub에 커밋하지 않습니다 |
| 3 | size300_overlap50_course_policy_long_p013_c001 | 4. API Key 보안 정책 | 0.7245 | Gemini API Key는 반드시 .env 파일에 저장합니다. API Key를 Python 코드에 직접 작성하지 않습니다. .env 파일은 .gitignore에 포함되어 있어야 하며 GitHub에 커밋하지 않습니다 |

### 질문: GitHub 제출 기준은 무엇인가요?

#### 생성 답변

답변: 제공된 문서에는 GitHub 제출 기준의 항목명만 명시되어 있을 뿐, 구체적인 세부 내용은 포함되어 있지 않습니다.

근거: course_policy_long_p018_c001, 6. GitHub 제출 기준

#### 검색 context

| rank | chunk_id | section | distance | text 요약 |
| --- | --- | --- | --- | --- |
| 1 | course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.2348 | ## 6. GitHub 제출 기준 |
| 2 | size500_overlap100_course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.2452 | ## 6. GitHub 제출 기준 |
| 3 | size300_overlap50_course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.2606 | ## 6. GitHub 제출 기준 |

### 질문: 오류 질문을 할 때 무엇을 함께 공유해야 하나요?

#### 생성 답변

답변: 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 공유해야 합니다. 가능하면 터미널 화면 캡처나 로그 파일을 함께 첨부하십시오.

근거: size300_overlap50_course_policy_long_p022_c001 (7. 오류 질문 방법)

#### 검색 context

| rank | chunk_id | section | distance | text 요약 |
| --- | --- | --- | --- | --- |
| 1 | size300_overlap50_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.437 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 |
| 2 | size300_overlap0_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.4395 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 |
| 3 | size500_overlap100_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.4418 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 |

### 질문: 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?

#### 생성 답변

답변: 제공된 문서에는 '12. 미니 프로젝트 결과물'이라는 제목만 있을 뿐, 구체적으로 포함되어야 할 내용은 기재되어 있지 않습니다.

근거: course_policy_long_p036_c001 (12. 미니 프로젝트 결과물)

#### 검색 context

| rank | chunk_id | section | distance | text 요약 |
| --- | --- | --- | --- | --- |
| 1 | course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.2763 | ## 12. 미니 프로젝트 결과물 |
| 2 | size500_overlap100_course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.3218 | ## 12. 미니 프로젝트 결과물 |
| 3 | size300_overlap50_course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.3331 | ## 12. 미니 프로젝트 결과물 |
