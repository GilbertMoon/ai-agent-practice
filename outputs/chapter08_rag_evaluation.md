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
| 민감 정보는 어디에 저장해야 하나요? | 0 | 2 | 1 | 2 | 5 | paragraph_course_policy_long_p032_c001 | 질문과 답변의 관련성이 낮아 보임 |
| GitHub 제출 기준은 무엇인가요? | 2 | 2 | 2 | 2 | 8 | paragraph_course_policy_long_p019_c001 | 질문에 적절하고 context에 근거한 답변으로 보임 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | 1 | 2 | 2 | 2 | 7 | paragraph_course_policy_long_p034_c001 | 일부 관련성은 있으나 근거성 또는 충실성 확인 필요 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | 2 | 2 | 2 | 2 | 8 | paragraph_course_policy_long_p038_c001 | 질문에 적절하고 context에 근거한 답변으로 보임 |

## 상세 답변

### 질문: 민감 정보는 어디에 저장해야 하나요?

#### 생성 답변

답변: 제공된 수업 안내 문서에는 민감 정보 저장 위치에 대한 내용이 포함되어 있지 않습니다.

근거: 해당 내용 없음 (context 1, 2, 3 / section: 10. metadata 설계 기준)

#### 검색 context

| rank | chunk_id | section | distance | text 요약 |
| --- | --- | --- | --- | --- |
| 1 | paragraph_course_policy_long_p032_c001 | 10. metadata 설계 기준 | 1.0323 | metadata는 검색 결과를 해석할 때 중요합니다. 검색된 chunk가 어느 문서에서 왔는지, 어느 섹션에 있는지, 원래 문단의 어느 위치에서 만들어졌는지 알 수 있어야 합니다. RAG에서는 답변뿐 아니라 근거 제 |
| 2 | size500_overlap100_course_policy_long_p032_c001 | 10. metadata 설계 기준 | 1.1452 | metadata는 검색 결과를 해석할 때 중요합니다. 검색된 chunk가 어느 문서에서 왔는지, 어느 섹션에 있는지, 원래 문단의 어느 위치에서 만들어졌는지 알 수 있어야 합니다. RAG에서는 답변뿐 아니라 근거 제 |
| 3 | size300_overlap50_course_policy_long_p032_c001 | 10. metadata 설계 기준 | 1.1558 | metadata는 검색 결과를 해석할 때 중요합니다. 검색된 chunk가 어느 문서에서 왔는지, 어느 섹션에 있는지, 원래 문단의 어느 위치에서 만들어졌는지 알 수 있어야 합니다. RAG에서는 답변뿐 아니라 근거 제 |

### 질문: GitHub 제출 기준은 무엇인가요?

#### 생성 답변

답변: 실습 코드를 GitHub에 커밋하고 푸시해야 하며, 커밋 메시지는 작업 내용을 알 수 있도록 구체적으로 작성해야 합니다. 의미 없는 메시지나 너무 큰 단위의 커밋은 지양해야 합니다.

근거: paragraph_course_policy_long_p019_c001, 6. GitHub 제출 기준

#### 검색 context

| rank | chunk_id | section | distance | text 요약 |
| --- | --- | --- | --- | --- |
| 1 | paragraph_course_policy_long_p019_c001 | 6. GitHub 제출 기준 | 0.8907 | 실습 코드는 GitHub에 커밋하고 푸시합니다. 커밋 메시지는 작업 내용을 알 수 있도록 작성합니다. 예를 들어 Add chapter07 chunking practice structure, Implement chun |
| 2 | paragraph_course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.9436 | ## 6. GitHub 제출 기준 |
| 3 | size300_overlap50_course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.9467 | ## 6. GitHub 제출 기준 |

### 질문: 오류 질문을 할 때 무엇을 함께 공유해야 하나요?

#### 생성 답변

답변: 제공된 문서에는 오류 질문 시 무엇을 함께 공유해야 하는지에 대한 구체적인 답변 내용이 포함되어 있지 않습니다.

근거: paragraph_course_policy_long_p034_c001 (11. 검색 결과 비교 기준)

#### 검색 context

| rank | chunk_id | section | distance | text 요약 |
| --- | --- | --- | --- | --- |
| 1 | paragraph_course_policy_long_p034_c001 | 11. 검색 결과 비교 기준 | 0.9006 | 청킹 전략을 비교할 때는 동일한 질문 세트를 사용해야 합니다. 예를 들어 API Key는 어디에 저장해야 하나요, 과제 제출 기한은 언제인가요, 오류 질문을 할 때 무엇을 함께 공유해야 하나요, 미니 프로젝트 결과물 |
| 2 | size300_overlap0_course_policy_long_p034_c001 | 11. 검색 결과 비교 기준 | 0.9159 | 청킹 전략을 비교할 때는 동일한 질문 세트를 사용해야 합니다. 예를 들어 API Key는 어디에 저장해야 하나요, 과제 제출 기한은 언제인가요, 오류 질문을 할 때 무엇을 함께 공유해야 하나요, 미니 프로젝트 결과물 |
| 3 | size300_overlap50_course_policy_long_p034_c001 | 11. 검색 결과 비교 기준 | 0.9182 | 청킹 전략을 비교할 때는 동일한 질문 세트를 사용해야 합니다. 예를 들어 API Key는 어디에 저장해야 하나요, 과제 제출 기한은 언제인가요, 오류 질문을 할 때 무엇을 함께 공유해야 하나요, 미니 프로젝트 결과물 |

### 질문: 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요?

#### 생성 답변

답변: 미니 프로젝트 제출 시 사용한 chunk_size와 chunk_overlap 값을 명시해야 하며, 가장 좋은 결과를 보인 설정에 대한 짧은 설명을 포함해야 합니다.

근거: chunk_id: paragraph_course_policy_long_p038_c001, section: 12. 미니 프로젝트 결과물

#### 검색 context

| rank | chunk_id | section | distance | text 요약 |
| --- | --- | --- | --- | --- |
| 1 | paragraph_course_policy_long_p038_c001 | 12. 미니 프로젝트 결과물 | 0.6528 | 미니 프로젝트를 제출할 때는 어떤 chunk_size와 chunk_overlap을 사용했는지 명시해야 합니다. 또한 가장 좋은 결과를 보인 설정이 무엇인지 짧게 설명해야 합니다. 정답은 하나로 고정되어 있지 않습니다 |
| 2 | size500_overlap100_course_policy_long_p038_c001 | 12. 미니 프로젝트 결과물 | 0.6805 | 미니 프로젝트를 제출할 때는 어떤 chunk_size와 chunk_overlap을 사용했는지 명시해야 합니다. 또한 가장 좋은 결과를 보인 설정이 무엇인지 짧게 설명해야 합니다. 정답은 하나로 고정되어 있지 않습니다 |
| 3 | size300_overlap50_course_policy_long_p038_c001 | 12. 미니 프로젝트 결과물 | 0.6862 | 미니 프로젝트를 제출할 때는 어떤 chunk_size와 chunk_overlap을 사용했는지 명시해야 합니다. 또한 가장 좋은 결과를 보인 설정이 무엇인지 짧게 설명해야 합니다. 정답은 하나로 고정되어 있지 않습니다 |
