# Chapter 7 청킹 전략별 검색 결과 비교

입력 문서: `data\course_policy_long.txt`
검색 결과 수: top 3

## 비교 기준

- 관련성 2점: 질문에 직접 답할 수 있는 chunk
- 관련성 1점: 일부 관련은 있지만 근거가 부족한 chunk
- 관련성 0점: 질문과 관련이 낮은 chunk

## 전략별 검색 결과 요약

| 질문 | 전략 | rank | chunk_id | section | distance | 관련성 | text 요약 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| API Key는 어디에 저장해야 하나요? | paragraph | 1 | paragraph_course_policy_long_p012_c001 | 4. API Key 보안 정책 | 0.5204 | 1 | ## 4. API Key 보안 정책 |
| API Key는 어디에 저장해야 하나요? | paragraph | 2 | paragraph_course_policy_long_p013_c001 | 4. API Key 보안 정책 | 0.5413 | 2 | Gemini API Key는 반드시 .env 파일에 저장합니다. API Key를 Python 코드에 직접 작성하지 않습니다. .env 파일은 .gitignore에 포함되어 있어야 하며 GitHub에 커밋하지 않습니다. 공개 저장소에 실제 API Key가 올라가면 다른 사람이 해당 키를  |
| API Key는 어디에 저장해야 하나요? | paragraph | 3 | paragraph_course_policy_long_p014_c001 | 4. API Key 보안 정책 | 0.6113 | 2 | .env.example 파일에는 실제 키가 아니라 예시 값만 작성합니다. 예를 들어 GEMINI_API_KEY=your_api_key_here와 같이 더미 값을 넣습니다. 수강생은 로컬 환경에서 .env.example을 참고하여 .env 파일을 직접 만들고, 본인의 실제 API Key를 |
| API Key는 어디에 저장해야 하나요? | size300_overlap0 | 1 | size300_overlap0_course_policy_long_p012_c001 | 4. API Key 보안 정책 | 0.4918 | 1 | ## 4. API Key 보안 정책 |
| API Key는 어디에 저장해야 하나요? | size300_overlap0 | 2 | size300_overlap0_course_policy_long_p013_c001 | 4. API Key 보안 정책 | 0.5045 | 2 | Gemini API Key는 반드시 .env 파일에 저장합니다. API Key를 Python 코드에 직접 작성하지 않습니다. .env 파일은 .gitignore에 포함되어 있어야 하며 GitHub에 커밋하지 않습니다. 공개 저장소에 실제 API Key가 올라가면 다른 사람이 해당 키를  |
| API Key는 어디에 저장해야 하나요? | size300_overlap0 | 3 | size300_overlap0_course_policy_long_p014_c001 | 4. API Key 보안 정책 | 0.5545 | 2 | .env.example 파일에는 실제 키가 아니라 예시 값만 작성합니다. 예를 들어 GEMINI_API_KEY=your_api_key_here와 같이 더미 값을 넣습니다. 수강생은 로컬 환경에서 .env.example을 참고하여 .env 파일을 직접 만들고, 본인의 실제 API Key를 |
| API Key는 어디에 저장해야 하나요? | size300_overlap50 | 1 | size300_overlap50_course_policy_long_p012_c001 | 4. API Key 보안 정책 | 0.4943 | 1 | ## 4. API Key 보안 정책 |
| API Key는 어디에 저장해야 하나요? | size300_overlap50 | 2 | size300_overlap50_course_policy_long_p013_c001 | 4. API Key 보안 정책 | 0.5024 | 2 | Gemini API Key는 반드시 .env 파일에 저장합니다. API Key를 Python 코드에 직접 작성하지 않습니다. .env 파일은 .gitignore에 포함되어 있어야 하며 GitHub에 커밋하지 않습니다. 공개 저장소에 실제 API Key가 올라가면 다른 사람이 해당 키를  |
| API Key는 어디에 저장해야 하나요? | size300_overlap50 | 3 | size300_overlap50_course_policy_long_p014_c001 | 4. API Key 보안 정책 | 0.5669 | 2 | .env.example 파일에는 실제 키가 아니라 예시 값만 작성합니다. 예를 들어 GEMINI_API_KEY=your_api_key_here와 같이 더미 값을 넣습니다. 수강생은 로컬 환경에서 .env.example을 참고하여 .env 파일을 직접 만들고, 본인의 실제 API Key를 |
| API Key는 어디에 저장해야 하나요? | size500_overlap100 | 1 | size500_overlap100_course_policy_long_p013_c001 | 4. API Key 보안 정책 | 0.4991 | 2 | Gemini API Key는 반드시 .env 파일에 저장합니다. API Key를 Python 코드에 직접 작성하지 않습니다. .env 파일은 .gitignore에 포함되어 있어야 하며 GitHub에 커밋하지 않습니다. 공개 저장소에 실제 API Key가 올라가면 다른 사람이 해당 키를  |
| API Key는 어디에 저장해야 하나요? | size500_overlap100 | 2 | size500_overlap100_course_policy_long_p012_c001 | 4. API Key 보안 정책 | 0.5102 | 1 | ## 4. API Key 보안 정책 |
| API Key는 어디에 저장해야 하나요? | size500_overlap100 | 3 | size500_overlap100_course_policy_long_p014_c001 | 4. API Key 보안 정책 | 0.5654 | 2 | .env.example 파일에는 실제 키가 아니라 예시 값만 작성합니다. 예를 들어 GEMINI_API_KEY=your_api_key_here와 같이 더미 값을 넣습니다. 수강생은 로컬 환경에서 .env.example을 참고하여 .env 파일을 직접 만들고, 본인의 실제 API Key를 |
| 과제 제출 기한은 언제인가요? | paragraph | 1 | paragraph_course_policy_long_p015_c001 | 5. 과제 제출 정책 | 0.4764 | 2 | ## 5. 과제 제출 정책 |
| 과제 제출 기한은 언제인가요? | paragraph | 2 | paragraph_course_policy_long_p016_c001 | 5. 과제 제출 정책 | 0.5369 | 2 | 과제 제출 기한은 매주 금요일 23:59입니다. 특별한 공지가 없는 한 지각 제출은 감점될 수 있습니다. 제출 파일에는 실행 코드, 간단한 실행 방법, 결과 요약이 포함되어야 합니다. 코드만 제출하고 실행 방법이나 결과 설명이 없으면 채점자가 의도를 파악하기 어려우므로 감점될 수 있습니 |
| 과제 제출 기한은 언제인가요? | paragraph | 3 | paragraph_course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.694 | 1 | ## 6. GitHub 제출 기준 |
| 과제 제출 기한은 언제인가요? | size300_overlap0 | 1 | size300_overlap0_course_policy_long_p015_c001 | 5. 과제 제출 정책 | 0.4677 | 2 | ## 5. 과제 제출 정책 |
| 과제 제출 기한은 언제인가요? | size300_overlap0 | 2 | size300_overlap0_course_policy_long_p016_c001 | 5. 과제 제출 정책 | 0.5061 | 2 | 과제 제출 기한은 매주 금요일 23:59입니다. 특별한 공지가 없는 한 지각 제출은 감점될 수 있습니다. 제출 파일에는 실행 코드, 간단한 실행 방법, 결과 요약이 포함되어야 합니다. 코드만 제출하고 실행 방법이나 결과 설명이 없으면 채점자가 의도를 파악하기 어려우므로 감점될 수 있습니 |
| 과제 제출 기한은 언제인가요? | size300_overlap0 | 3 | size300_overlap0_course_policy_long_p017_c001 | 5. 과제 제출 정책 | 0.7109 | 2 | 과제 파일명은 장 번호와 이름을 알 수 있도록 작성합니다. 예를 들어 chapter07_chunking_result.md 또는 chapter07_chunking_solution.py와 같이 작성할 수 있습니다. 노트북 파일을 제출하는 경우에는 실행 결과가 남아 있는 상태로 제출합니다.  |
| 과제 제출 기한은 언제인가요? | size300_overlap50 | 1 | size300_overlap50_course_policy_long_p015_c001 | 5. 과제 제출 정책 | 0.4724 | 2 | ## 5. 과제 제출 정책 |
| 과제 제출 기한은 언제인가요? | size300_overlap50 | 2 | size300_overlap50_course_policy_long_p016_c001 | 5. 과제 제출 정책 | 0.5105 | 2 | 과제 제출 기한은 매주 금요일 23:59입니다. 특별한 공지가 없는 한 지각 제출은 감점될 수 있습니다. 제출 파일에는 실행 코드, 간단한 실행 방법, 결과 요약이 포함되어야 합니다. 코드만 제출하고 실행 방법이나 결과 설명이 없으면 채점자가 의도를 파악하기 어려우므로 감점될 수 있습니 |
| 과제 제출 기한은 언제인가요? | size300_overlap50 | 3 | size300_overlap50_course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.6853 | 1 | ## 6. GitHub 제출 기준 |
| 과제 제출 기한은 언제인가요? | size500_overlap100 | 1 | size500_overlap100_course_policy_long_p015_c001 | 5. 과제 제출 정책 | 0.4717 | 2 | ## 5. 과제 제출 정책 |
| 과제 제출 기한은 언제인가요? | size500_overlap100 | 2 | size500_overlap100_course_policy_long_p016_c001 | 5. 과제 제출 정책 | 0.4802 | 2 | 과제 제출 기한은 매주 금요일 23:59입니다. 특별한 공지가 없는 한 지각 제출은 감점될 수 있습니다. 제출 파일에는 실행 코드, 간단한 실행 방법, 결과 요약이 포함되어야 합니다. 코드만 제출하고 실행 방법이나 결과 설명이 없으면 채점자가 의도를 파악하기 어려우므로 감점될 수 있습니 |
| 과제 제출 기한은 언제인가요? | size500_overlap100 | 3 | size500_overlap100_course_policy_long_p018_c001 | 6. GitHub 제출 기준 | 0.6818 | 1 | ## 6. GitHub 제출 기준 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | paragraph | 1 | paragraph_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.4896 | 2 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 터미널 화면 캡처나 로그 파일도 함께 첨부합니다. 이렇게 해야 조교나  |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | paragraph | 2 | paragraph_course_policy_long_p021_c001 | 7. 오류 질문 방법 | 0.5643 | 1 | ## 7. 오류 질문 방법 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | paragraph | 3 | paragraph_course_policy_long_p023_c001 | 7. 오류 질문 방법 | 0.5682 | 1 | 좋은 오류 질문 예시는 다음과 같습니다. python app/chunk_index_documents.py를 실행했는데 GEMINI_API_KEY가 설정되어 있지 않다는 오류가 발생했습니다. .env 파일은 프로젝트 루트에 만들었고, 파일 내용은 GEMINI_API_KEY=... 형식입니 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | size300_overlap0 | 1 | size300_overlap0_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.4395 | 2 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 터미널 화면 캡처나 로그 파일도 함께 첨부합니다. 이렇게 해야 조교나  |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | size300_overlap0 | 2 | size300_overlap0_course_policy_long_p023_c001 | 7. 오류 질문 방법 | 0.5392 | 1 | 좋은 오류 질문 예시는 다음과 같습니다. python app/chunk_index_documents.py를 실행했는데 GEMINI_API_KEY가 설정되어 있지 않다는 오류가 발생했습니다. .env 파일은 프로젝트 루트에 만들었고, 파일 내용은 GEMINI_API_KEY=... 형식입니 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | size300_overlap0 | 3 | size300_overlap0_course_policy_long_p021_c001 | 7. 오류 질문 방법 | 0.5401 | 1 | ## 7. 오류 질문 방법 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | size300_overlap50 | 1 | size300_overlap50_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.437 | 2 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 터미널 화면 캡처나 로그 파일도 함께 첨부합니다. 이렇게 해야 조교나  |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | size300_overlap50 | 2 | size300_overlap50_course_policy_long_p023_c001 | 7. 오류 질문 방법 | 0.5244 | 1 | 좋은 오류 질문 예시는 다음과 같습니다. python app/chunk_index_documents.py를 실행했는데 GEMINI_API_KEY가 설정되어 있지 않다는 오류가 발생했습니다. .env 파일은 프로젝트 루트에 만들었고, 파일 내용은 GEMINI_API_KEY=... 형식입니 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | size300_overlap50 | 3 | size300_overlap50_course_policy_long_p021_c001 | 7. 오류 질문 방법 | 0.5448 | 1 | ## 7. 오류 질문 방법 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | size500_overlap100 | 1 | size500_overlap100_course_policy_long_p022_c001 | 7. 오류 질문 방법 | 0.4418 | 2 | 오류가 발생했을 때는 단순히 안 됩니다라고 질문하지 않습니다. 질문할 때는 실행한 명령어, 전체 에러 메시지, 현재 작업 폴더, Python 버전, 설치한 패키지 목록, 시도한 해결 방법을 함께 공유합니다. 가능하면 터미널 화면 캡처나 로그 파일도 함께 첨부합니다. 이렇게 해야 조교나  |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | size500_overlap100 | 2 | size500_overlap100_course_policy_long_p023_c001 | 7. 오류 질문 방법 | 0.5241 | 1 | 좋은 오류 질문 예시는 다음과 같습니다. python app/chunk_index_documents.py를 실행했는데 GEMINI_API_KEY가 설정되어 있지 않다는 오류가 발생했습니다. .env 파일은 프로젝트 루트에 만들었고, 파일 내용은 GEMINI_API_KEY=... 형식입니 |
| 오류 질문을 할 때 무엇을 함께 공유해야 하나요? | size500_overlap100 | 3 | size500_overlap100_course_policy_long_p021_c001 | 7. 오류 질문 방법 | 0.5412 | 1 | ## 7. 오류 질문 방법 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | paragraph | 1 | paragraph_course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.3372 | 2 | ## 12. 미니 프로젝트 결과물 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | paragraph | 2 | paragraph_course_policy_long_p038_c001 | 12. 미니 프로젝트 결과물 | 0.5143 | 1 | 미니 프로젝트를 제출할 때는 어떤 chunk_size와 chunk_overlap을 사용했는지 명시해야 합니다. 또한 가장 좋은 결과를 보인 설정이 무엇인지 짧게 설명해야 합니다. 정답은 하나로 고정되어 있지 않습니다. 문서 유형과 질문 유형에 따라 적절한 chunking 전략이 달라질  |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | paragraph | 3 | paragraph_course_policy_long_p037_c001 | 12. 미니 프로젝트 결과물 | 0.528 | 2 | Chapter 7 미니 프로젝트 결과물에는 chunk 인덱싱 코드, chunk 검색 코드, 청킹 전략 비교 코드, 긴 샘플 문서, 검색 결과 비교 로그가 포함됩니다. 검색 결과 비교 로그는 outputs/chapter07_chunking_comparison.md에 정리합니다. 비교 로그 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | size300_overlap0 | 1 | size300_overlap0_course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.3638 | 2 | ## 12. 미니 프로젝트 결과물 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | size300_overlap0 | 2 | size300_overlap0_course_policy_long_p037_c001 | 12. 미니 프로젝트 결과물 | 0.4753 | 2 | Chapter 7 미니 프로젝트 결과물에는 chunk 인덱싱 코드, chunk 검색 코드, 청킹 전략 비교 코드, 긴 샘플 문서, 검색 결과 비교 로그가 포함됩니다. 검색 결과 비교 로그는 outputs/chapter07_chunking_comparison.md에 정리합니다. 비교 로그 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | size300_overlap0 | 3 | size300_overlap0_course_policy_long_p038_c001 | 12. 미니 프로젝트 결과물 | 0.4759 | 1 | 미니 프로젝트를 제출할 때는 어떤 chunk_size와 chunk_overlap을 사용했는지 명시해야 합니다. 또한 가장 좋은 결과를 보인 설정이 무엇인지 짧게 설명해야 합니다. 정답은 하나로 고정되어 있지 않습니다. 문서 유형과 질문 유형에 따라 적절한 chunking 전략이 달라질  |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | size300_overlap50 | 1 | size300_overlap50_course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.3331 | 2 | ## 12. 미니 프로젝트 결과물 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | size300_overlap50 | 2 | size300_overlap50_course_policy_long_p038_c001 | 12. 미니 프로젝트 결과물 | 0.4812 | 1 | 미니 프로젝트를 제출할 때는 어떤 chunk_size와 chunk_overlap을 사용했는지 명시해야 합니다. 또한 가장 좋은 결과를 보인 설정이 무엇인지 짧게 설명해야 합니다. 정답은 하나로 고정되어 있지 않습니다. 문서 유형과 질문 유형에 따라 적절한 chunking 전략이 달라질  |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | size300_overlap50 | 3 | size300_overlap50_course_policy_long_p037_c001 | 12. 미니 프로젝트 결과물 | 0.4886 | 2 | Chapter 7 미니 프로젝트 결과물에는 chunk 인덱싱 코드, chunk 검색 코드, 청킹 전략 비교 코드, 긴 샘플 문서, 검색 결과 비교 로그가 포함됩니다. 검색 결과 비교 로그는 outputs/chapter07_chunking_comparison.md에 정리합니다. 비교 로그 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | size500_overlap100 | 1 | size500_overlap100_course_policy_long_p036_c001 | 12. 미니 프로젝트 결과물 | 0.3218 | 2 | ## 12. 미니 프로젝트 결과물 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | size500_overlap100 | 2 | size500_overlap100_course_policy_long_p037_c001 | 12. 미니 프로젝트 결과물 | 0.4867 | 2 | Chapter 7 미니 프로젝트 결과물에는 chunk 인덱싱 코드, chunk 검색 코드, 청킹 전략 비교 코드, 긴 샘플 문서, 검색 결과 비교 로그가 포함됩니다. 검색 결과 비교 로그는 outputs/chapter07_chunking_comparison.md에 정리합니다. 비교 로그 |
| 미니 프로젝트 결과물에는 무엇이 포함되어야 하나요? | size500_overlap100 | 3 | size500_overlap100_course_policy_long_p038_c001 | 12. 미니 프로젝트 결과물 | 0.4956 | 1 | 미니 프로젝트를 제출할 때는 어떤 chunk_size와 chunk_overlap을 사용했는지 명시해야 합니다. 또한 가장 좋은 결과를 보인 설정이 무엇인지 짧게 설명해야 합니다. 정답은 하나로 고정되어 있지 않습니다. 문서 유형과 질문 유형에 따라 적절한 chunking 전략이 달라질  |

## 해석 가이드

- distance 값은 낮을수록 질문과 가까운 벡터로 볼 수 있습니다.
- 하지만 distance만으로 검색 품질을 판단하지 않습니다.
- 검색된 chunk가 실제로 질문에 답할 수 있는지 사람이 함께 확인해야 합니다.
- chunk_size가 너무 크면 여러 주제가 섞일 수 있습니다.
- chunk_size가 너무 작으면 답변에 필요한 맥락이 부족할 수 있습니다.
- overlap은 chunk 경계에서 문장이 잘리는 문제를 줄이는 데 도움이 됩니다.