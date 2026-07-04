# Chapter 7 청킹 전략별 검색 결과 비교

입력 문서: `data/course_policy_long.txt`
검색 결과 수: top 3

| 질문 | 전략 | top 1 chunk_id | section | distance | top 1 text 요약 |
| --- | --- | --- | --- | --- | --- |
| 과제 제출 기한은 언제인가요? | paragraph | paragraph_course_policy_long_p015_c001 | 5. 과제 제출 정책 | 0.4764 | ## 5. 과제 제출 정책 |
| 과제 제출 기한은 언제인가요? | size300_overlap0 | size300_overlap0_course_policy_long_p015_c001 | 5. 과제 제출 정책 | 0.4677 | ## 5. 과제 제출 정책 |
| 과제 제출 기한은 언제인가요? | size300_overlap50 | size300_overlap50_course_policy_long_p015_c001 | 5. 과제 제출 정책 | 0.4724 | ## 5. 과제 제출 정책 |
| 과제 제출 기한은 언제인가요? | size500_overlap100 | size500_overlap100_course_policy_long_p015_c001 | 5. 과제 제출 정책 | 0.4717 | ## 5. 과제 제출 정책 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | paragraph | paragraph_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.4896 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | size300_overlap0 | size300_overlap0_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.4395 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | size300_overlap50 | size300_overlap50_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.437 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | size500_overlap100 | size500_overlap100_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.4418 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | paragraph | paragraph_course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.3372 | ## 12. 미니 프로젝트 결과물 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | size300_overlap0 | size300_overlap0_course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.3638 | ## 12. 미니 프로젝트 결과물 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | size300_overlap50 | size300_overlap50_course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.3331 | ## 12. 미니 프로젝트 결과물 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | size500_overlap100 | size500_overlap100_course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.3218 | ## 12. 미니 프로젝트 결과물 |