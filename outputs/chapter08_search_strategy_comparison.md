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
| 민감 정보는 어디에 저장해야 하나요? | 4. API Key 보안 정책 | 0 | 0 | 0 | 2 | paragraph_course_policy_long_p032_c001 | 10. metadata 설계 기준 | 1.0323 | top 3 안에 충분한 정답 근거가 부족함 |
| GitHub 제출 기준은 무엇인가요? | 6. GitHub 제출 기준 | 2 | 1 | 2 | 2 | paragraph_course_policy_long_p019_c001 | 6. GitHub 제출 기준 | 0.8907 | top 1 결과가 질문에 직접 답할 가능성이 높음 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | 7. 오류 질문 방법 | 1 | 0 | 1 | 2 | paragraph_course_policy_long_p034_c001 | 11. 검색 결과 비교 기준 | 0.9006 | top 3 안에 충분한 정답 근거가 부족함 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | 12. 미니 프로젝트 결과물 | 2 | 1 | 2 | 2 | paragraph_course_policy_long_p038_c001 | 12. 미니 프로젝트 결과물 | 0.6528 | top 1 결과가 질문에 직접 답할 가능성이 높음 |

## 상세 검색 결과

### 질문: 민감 정보는 어디에 저장해야 하나요?

- 기대 section: `4. API Key 보안 정책`
- 코멘트: top 3 안에 충분한 정답 근거가 부족함

| rank | chunk_id | section | distance | 관련성 | 충분성 | 근거성 | text 요약 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | paragraph_course_policy_long_p032_c001 | 10. metadata 설계 기준 | 1.0323 | 0 | 0 | 2 | metadata는 검색 결과를 해석할 때 중요합니다. 검색된 chunk가 어느 문서에서 왔는지, 어느 섹션에 있는지, 원래 문단의 어느 위치에서 만들어졌는지 알 수 있어야 합니다. RAG에서는 답변뿐 아니라 근거 제 |
| 2 | size500_overlap100_course_policy_long_p032_c001 | 10. metadata 설계 기준 | 1.1452 | 0 | 0 | 2 | metadata는 검색 결과를 해석할 때 중요합니다. 검색된 chunk가 어느 문서에서 왔는지, 어느 섹션에 있는지, 원래 문단의 어느 위치에서 만들어졌는지 알 수 있어야 합니다. RAG에서는 답변뿐 아니라 근거 제 |
| 3 | size300_overlap50_course_policy_long_p032_c001 | 10. metadata 설계 기준 | 1.1558 | 0 | 0 | 2 | metadata는 검색 결과를 해석할 때 중요합니다. 검색된 chunk가 어느 문서에서 왔는지, 어느 섹션에 있는지, 원래 문단의 어느 위치에서 만들어졌는지 알 수 있어야 합니다. RAG에서는 답변뿐 아니라 근거 제 |

### 질문: GitHub 제출 기준은 무엇인가요?

- 기대 section: `6. GitHub 제출 기준`
- 코멘트: top 1 결과가 질문에 직접 답할 가능성이 높음

| rank | chunk_id | section | distance | 관련성 | 충분성 | 근거성 | text 요약 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | paragraph_course_policy_long_p019_c001 | 6. GitHub 제출 기준 | 0.8907 | 2 | 2 | 2 | 실습 코드는 GitHub에 커밋하고 푸시합니다. 커밋 메시지는 작업 내용을 알 수 있도록 작성합니다. 예를 들어 Add chapter07 chunking practice structure, Implement chun |
| 2 | paragraph_course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.9436 | 2 | 1 | 2 | ## 6. GitHub 제출 기준 |
| 3 | size300_overlap50_course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.9467 | 2 | 1 | 2 | ## 6. GitHub 제출 기준 |

### 질문: 오류 질문을 할 때 무엇을 함께 공유해야 하나요?

- 기대 section: `7. 오류 질문 방법`
- 코멘트: top 3 안에 충분한 정답 근거가 부족함

| rank | chunk_id | section | distance | 관련성 | 충분성 | 근거성 | text 요약 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | paragraph_course_policy_long_p034_c001 | 11. 검색 결과 비교 기준 | 0.9006 | 1 | 1 | 2 | 청킹 전략을 비교할 때는 동일한 질문 세트를 사용해야 합니다. 예를 들어 API Key는 어디에 저장해야 하나요, 과제 제출 기한은 언제인가요, 오류 질문을 할 때 무엇을 함께 공유해야 하나요, 미니 프로젝트 결과물 |
| 2 | size300_overlap0_course_policy_long_p034_c001 | 11. 검색 결과 비교 기준 | 0.9159 | 1 | 1 | 2 | 청킹 전략을 비교할 때는 동일한 질문 세트를 사용해야 합니다. 예를 들어 API Key는 어디에 저장해야 하나요, 과제 제출 기한은 언제인가요, 오류 질문을 할 때 무엇을 함께 공유해야 하나요, 미니 프로젝트 결과물 |
| 3 | size300_overlap50_course_policy_long_p034_c001 | 11. 검색 결과 비교 기준 | 0.9182 | 1 | 1 | 2 | 청킹 전략을 비교할 때는 동일한 질문 세트를 사용해야 합니다. 예를 들어 API Key는 어디에 저장해야 하나요, 과제 제출 기한은 언제인가요, 오류 질문을 할 때 무엇을 함께 공유해야 하나요, 미니 프로젝트 결과물 |

### 질문: 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?

- 기대 section: `12. 미니 프로젝트 결과물`
- 코멘트: top 1 결과가 질문에 직접 답할 가능성이 높음

| rank | chunk_id | section | distance | 관련성 | 충분성 | 근거성 | text 요약 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | paragraph_course_policy_long_p038_c001 | 12. 미니 프로젝트 결과물 | 0.6528 | 2 | 2 | 2 | 미니 프로젝트를 제출할 때는 어떤 chunk_size와 chunk_overlap을 사용했는지 명시해야 합니다. 또한 가장 좋은 결과를 보인 설정이 무엇인지 짧게 설명해야 합니다. 정답은 하나로 고정되어 있지 않습니다 |
| 2 | size500_overlap100_course_policy_long_p038_c001 | 12. 미니 프로젝트 결과물 | 0.6805 | 2 | 2 | 2 | 미니 프로젝트를 제출할 때는 어떤 chunk_size와 chunk_overlap을 사용했는지 명시해야 합니다. 또한 가장 좋은 결과를 보인 설정이 무엇인지 짧게 설명해야 합니다. 정답은 하나로 고정되어 있지 않습니다 |
| 3 | size300_overlap50_course_policy_long_p038_c001 | 12. 미니 프로젝트 결과물 | 0.6862 | 2 | 2 | 2 | 미니 프로젝트를 제출할 때는 어떤 chunk_size와 chunk_overlap을 사용했는지 명시해야 합니다. 또한 가장 좋은 결과를 보인 설정이 무엇인지 짧게 설명해야 합니다. 정답은 하나로 고정되어 있지 않습니다 |
