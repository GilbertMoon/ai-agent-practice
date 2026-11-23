# RAG League — 학생용 공개 자료 안내

> AX 2기 Brother RAG Knowledge Agent 프로젝트 | 학생 전체 공용 공개 자료

이 디렉터리는 학생들이 **GitHub 로그인 권한 없이** 열람할 수 있도록 공개한 프로젝트 시작 자료입니다.
교수자 전용 `rag-basic` Private 저장소에 접근할 필요가 없습니다.

## 공식 학생용 가이드

1. [데이터 수집 가이드](data_collection_guide.md) — Brother 공식 한국어 PDF 2종의 다운로드 위치, 원본 검증, FAQ 이용 조건
2. [공개 DEV 평가 질문 10개](evaluation_practice.md) — 답변 가능 8개와 정보 부족으로 답변을 보류해야 하는 질문 2개

## 프로젝트 개요

- 대상: Brother 프린터·복합기 10개 제품
- 기본 자료: **공식 한국어 사용자 설명서 2개** (제품별 10개 PDF가 아닙니다)
- 개발 과제: 제품별 정확한 답변과 검증 가능한 근거를 제시하는 RAG Agent
- 실습 환경: Python 3.12, VS Code 등 팀별 개발 환경
- 진행 기간: 2026-11-19 ~ 11-30 (일정과 공식 제출 규칙은 RAG League Portal 최신 공지를 우선 확인)

## 바로 시작하는 순서

1. [데이터 수집 가이드](data_collection_guide.md)에서 공식 PDF 링크 2개를 확인합니다.
2. Brother 공식 사이트에서 설명서 2개를 직접 다운로드합니다.
3. 가이드에 명시된 SHA-256 값과 내려받은 파일의 해시를 비교합니다.
4. 다운로드한 문서를 텍스트 추출 → 청킹 → 임베딩 → 검색 가능한 형태로 준비합니다.
5. [공개 DEV 질문 10개](evaluation_practice.md)로 검색 결과의 출처·답변·답변 보류를 테스트합니다.
6. 공식 제출, 계정, Preflight, 평가 시간, 점수와 모델 정책은 **Portal 공지사항**을 확인합니다.

## 원본 PDF (제조사 공식 링크)

- **잉크젯 공통 설명서:** https://support.brother.com/g/s/id/htmldoc/mfc/cv_dcpt830dw/kor/PDF/PDF.pdf
- **레이저 공통 설명서:** https://support.brother.com/g/s/id/htmldoc/mfc/cv_dcpl2508dw/kor/PDF/PDF.pdf

PDF 원본은 이 저장소에 올리지 않습니다. 공식 다운로드 URL에서 직접 받으세요. FAQ는 기본 개발에 필수가 아니며, 사이트 이용조건을 따라 선택적으로 브라우저에서 열람할 수 있습니다.

## 공개 DEV 질문과 Hidden 평가의 차이

- 공개 DEV **10문항**: 개발·튜닝용 (답변 가능 8, 답변 보류 2)
- 공식 Hidden 평가: 별도 비공개 문항·정답으로 채점, 학생에게 배포하지 않음
- 10문항 결과에만 과적합하거나 정답을 하드코딩하지 마세요.

## 안전 및 문의

- API Key, 비밀번호, 토큰, 학생 개인 정보는 GitHub나 Q&A 글에 작성하지 마세요.
- 타사 설명서 PDF·FAQ 본문, 파생된 전체 텍스트를 Public 저장소에 커밋하지 마세요.
- 자료·정책 관련 문의는 공식 **RAG League Portal Q&A**를 이용하세요.

> 이 공개 폴더에는 학생 대상 문서만 제공합니다. Hidden 질문, Answer Key, 교수자 전용 파일은 포함하지 않습니다.
