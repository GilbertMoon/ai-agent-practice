# 데이터 수집 가이드 (Data Collection Guide)

> ⚠️ **이 문서를 읽지 않고 크롤러를 돌리지 마십시오.**
> 이용 조건 위반과 과도한 요청은 **감점 사유이며**, IP 차단으로 팀 전체 작업이 중단될 수 있습니다.
> 교수자는 실제로 차단(HTTP 403)을 경험했습니다. §5를 반드시 읽으십시오.

---

## 1. 수집 대상 요약

| 자료 | 개수 | 형식 | 자동 수집 |
|---|---:|---|---|
| 공식 온라인 사용자 설명서 (잉크젯 공통) | 1 | PDF + HTML | ✅ 허용 |
| 공식 온라인 사용자 설명서 (레이저 공통) | 1 | PDF + HTML | ✅ 허용 |
| 공식 FAQ (**선택**, 한국 등록 4개 제품만) | 제품별 93~138건 | HTML (브라우저 열람) | ❌ 자동 수집 불가·금지 (§4) |

**설명서는 2개뿐입니다.** 이유는 ``project_overview.md` §4` 참조.

---

## 2. 공식 설명서 — 확정된 URL

교수자가 **2026-11-18 에 실제 접속하여 확인**한 URL입니다.

### 2.1 잉크젯 공통 설명서 (`MAN-INKJET-CVT830`)

| 항목 | 값 |
|---|---|
| HTML 목차 | `https://support.brother.com/g/s/id/htmldoc/mfc/cv_dcpt830dw/kor/index.html` |
| **PDF (전체 설명서)** | `https://support.brother.com/g/s/id/htmldoc/mfc/cv_dcpt830dw/kor/PDF/PDF.pdf` |
| 언어 | 한국어 (ko-KR) |
| 버전 표기 | `버전 0` / © 2024 Brother Industries, Ltd. |
| 커버 모델 (문서에 명시된 전체) | DCP‑T530DW, DCP‑T535DW, DCP‑T536DW, DCP‑T730DW, DCP‑T735DW, DCP‑T830DW, DCP‑T835DW, MFC‑T930DW, MFC‑T935DW |
| **그중 우리 대상 제품** | DCP-T530DW, DCP-T730DW, DCP-T830DW, DCP-T835DW, MFC-T930DW |

### 2.2 레이저 공통 설명서 (`MAN-LASER-CVL2508`)

| 항목 | 값 |
|---|---|
| HTML 목차 | `https://support.brother.com/g/s/id/htmldoc/mfc/cv_dcpl2508dw/kor/index.html` |
| **PDF (전체 설명서)** | `https://support.brother.com/g/s/id/htmldoc/mfc/cv_dcpl2508dw/kor/PDF/PDF.pdf` |
| 언어 | 한국어 (ko-KR) |
| 버전 표기 | `버전 0` / © 2023 Brother Industries, Ltd. |
| 커버 모델 (문서에 명시된 전체) | HL‑L2464DW, DCP‑L2605DW, DCP‑L2640DW, HL‑L2480DW, DCP‑L2680DW, MFC‑L2800DW, MFC‑L2805DW, MFC‑L2820DW, MFC‑L2885DW, MFC‑L2880DW, MFC‑L2880DWXL, MFC‑L2920DW |
| **그중 우리 대상 제품** | HL-L2464DW, DCP-L2605DW, DCP-L2640DW, MFC-L2805DW, MFC-L2885DW |

> 💡 PDF 경로의 `cv_` 는 "common view"(공통 설명서)를 뜻합니다. `cv_dcpt830dw` 는
> "DCP-T830DW를 대표 모델로 하는 공통 문서"이며 **DCP-T830DW 전용 문서가 아닙니다.**

### 2.3 다운로드와 동일본 확인 (PowerShell)

**공개 데이터셋 버전: `BROTHER10-PUBLIC-v1`** — 아래 2개 PDF가 10개 제품 전부를 커버합니다.
모든 팀은 같은 공식 URL에서 **각자 직접** 내려받고(약관상 교수자가 파일을 배포할 수 없습니다), 아래 SHA-256으로 **동일본인지 확인**합니다.

| 파일 (저장 이름) | 크기 (bytes) | 쪽수 | SHA-256 | 대상 제품 |
|---|---:|---:|---|---|
| `MAN-INKJET-CVT830.pdf` | 8,739,442 | 466 | `8887de50224f50958ce4652873feb1761904176854e3f70517e6710a9d401287` | DCP-T530DW, DCP-T730DW, DCP-T830DW, DCP-T835DW, MFC-T930DW |
| `MAN-LASER-CVL2508.pdf` | 6,680,155 | 633 | `b53fe97856ebb4cf5c7c1a1f0c21893452bd70337363a4e16e4f5b64e0992280` | HL-L2464DW, DCP-L2605DW, DCP-L2640DW, MFC-L2805DW, MFC-L2885DW |

교수자 확인: 2026-11-18 최초 측정, 2026-11-20 공식 URL에서 다시 내려받아 **같은 값** 확인. 기계 판독용 원본: `docs/research/source_manifest.csv`.

```powershell
# 프로젝트 루트에서 실행
New-Item -ItemType Directory -Force data\source\manuals | Out-Null

Invoke-WebRequest -UseBasicParsing `
  -Uri "https://support.brother.com/g/s/id/htmldoc/mfc/cv_dcpt830dw/kor/PDF/PDF.pdf" `
  -OutFile "data\source\manuals\MAN-INKJET-CVT830.pdf"

Invoke-WebRequest -UseBasicParsing `
  -Uri "https://support.brother.com/g/s/id/htmldoc/mfc/cv_dcpl2508dw/kor/PDF/PDF.pdf" `
  -OutFile "data\source\manuals\MAN-LASER-CVL2508.pdf"

# 동일본 확인 — 두 줄 모두 OK 가 나와야 합니다
$expected = @{
  'MAN-INKJET-CVT830.pdf' = '8887de50224f50958ce4652873feb1761904176854e3f70517e6710a9d401287'
  'MAN-LASER-CVL2508.pdf' = 'b53fe97856ebb4cf5c7c1a1f0c21893452bd70337363a4e16e4f5b64e0992280'
}
foreach ($f in $expected.Keys) {
  $h = (Get-FileHash "data\source\manuals\$f" -Algorithm SHA256).Hash.ToLower()
  if ($h -eq $expected[$f]) { "$f OK" } else { "$f 다름 - 교수자에게 알리십시오" }
}
```

**`다름`이 나오면** 문서가 갱신되었거나 다운로드가 깨진 것입니다. 한 번 더 내려받아 보고, 그래도 다르면 Q&A로 알리십시오
(평가 기준 문서 버전과 어긋날 수 있습니다). 파일을 임의로 고치거나 다른 출처의 PDF로 바꾸지 마십시오.

> PDF 원본(`data/source/`)은 **Git에 커밋하지 않습니다** (§5.4). 팀원도 각자 위 명령으로 내려받으면 같은 파일이 됩니다.
> 공개 데이터는 이 2개 PDF(+ 선택 FAQ 열람)뿐입니다. **비공개 평가 질문·정답은 배포되지 않습니다.**
---

## 3. HTML 설명서 (선택)

PDF 외에 HTML 버전도 있습니다. HTML은 **절(section) 단위 URL**을 가지므로
출처 링크가 정확해지는 장점이 있습니다.

- 절 URL 형식: `.../kor/html/GUID-<UUID>_1.html`
- 예: `https://support.brother.com/g/s/id/htmldoc/mfc/cv_dcpl2508dw/kor/html/GUID-7A38839F-5CD3-4CAD-A170-5EA17E89A64E_1.html`

> PDF만 쓸지, HTML도 쓸지, 둘을 합칠지는 **팀의 설계 결정**입니다.
> 둘을 합치면 **동일 내용 중복**이 생기므로 중복 제거 전략이 필요합니다(데이터 품질 평가 항목).

---

## 4. FAQ — ⚠️ 선택(OPTIONAL) 자료입니다

> 🔴 **2026-11-18 방침 변경:** FAQ는 **필수 과제에서 제외**되었습니다.
> 이유는 두 가지이며, 둘 다 교수자가 실측으로 확인했습니다.
>
> 1. **기술적 차단** — FAQ 엔드포인트가 스크립트 접근에 `HTTP 403` 을 반환합니다
>    (브라우저는 정상). 자동 수집이 불가능합니다.
> 2. **이용약관 제약** — Brother 약관은 개인적 사용 범위를 넘는
>    **복제·배포·2차적 저작물 작성을 금지**합니다. 교수자가 FAQ 본문을 수집해
>    배포할 수 없고, 공개 저장소에 올릴 수도 없습니다.
>
> 상세: ``../docs/research/faq_access_resolution.md``

### 4.1 따라서 이렇게 하십시오

| 해도 되는 것 ✅ | 하지 말 것 ❌ |
|---|---|
| 브라우저로 FAQ를 **열람**하며 문제 이해에 참고 | FAQ 자동 수집 스크립트 작성 |
| 개인 학습 범위에서 내용을 메모·정리 | 403 우회 시도 |
| FAQ **ID·카테고리·관련 모델** 같은 서지정보 기록 | FAQ 본문을 저장소에 커밋 |
| FAQ를 활용했다면 보고서에 기록 (가점) | FAQ 본문을 외부에 배포 |
| **FAQ 없이 설명서만으로 과제 수행** (기본 경로) | 없는 FAQ를 **창작** |

### 4.2 FAQ를 전혀 쓰지 않아도 됩니다

**설명서 2개가 10개 제품을 모두 커버합니다.** FAQ 없이 설명서만으로 과제를 수행할 수 있습니다.

데이터 품질 배점에서도 **FAQ 미확보를 정직하게 기록하면 감점하지 않습니다.**
없는 FAQ를 만들어내는 것이 감점 사유입니다.

### 4.3 제품별 FAQ 가용성 (참고)

| 제품 | 한국 FAQ | 건수 |
|---|:--:|---:|
| DCP-T730DW / DCP-T830DW / MFC-T930DW / MFC-L2805DW | ✅ | 109 / 112 / 138 / 93 |
| 나머지 6개 제품 | ❌ | 0 |

⚠️ 6개 제품은 한국 미시판이며, **다른 제품의 공통 FAQ 적용 모델 목록에도 등장하지 않습니다**
(교수자가 FAQ 20건을 전수 확인). 즉 한국 FAQ로 이 6개 제품을 커버할 방법은 없습니다.

### 4.4 설명서의 문제 해결 절을 쓰십시오 (권장 경로)

FAQ 대신 설명서의 문제 해결·유지보수 절을 활용하십시오. 충분히 풍부합니다.

| 영역 | 위치 (PDF 페이지) |
|---|---|
| 오류 및 유지보수 메시지 | 잉크젯 p.297~ / 레이저 해당 절 |
| 프린터 용지 걸림 | 잉크젯 p.317~325 |
| 네트워크·Wi-Fi·WPS | 잉크젯 p.238~257 / 레이저 p.281~ |
| 제품 청소 (증상→원인→조치) | 잉크젯 p.376~381 / 레이저 p.521 |
| 비품 교체·드럼 카운터 | 레이저 p.510~515 |
| 남은 부품 수명 확인 | 레이저 p.528 |

> 이 영역은 실제 사용자 질문이 많은 영역입니다. 반드시 색인하십시오.

### 4.5 FAQ 본문 구조 (수동 참고 시)

브라우저로 FAQ를 열면 아래 필드가 보입니다.

| 필드 | 예 |
|---|---|
| FAQ ID | `faq00002496_008` |
| 날짜 | `11/09/2026` |
| 카테고리 | `제품 설치 > 기기 설치 / 설정` |
| **관련 모델** | 적용 모델 목록 (최대 55개까지 확인됨) |

⚠️ **하나의 FAQ가 스캐너·잉크젯·레이저를 동시에 커버**합니다.
제품별로 따로 저장하면 중복이 폭증합니다 — `faq_id` 기준 1건만 보관하십시오.

## 5. 🚨 이용 조건 및 수집 규칙 (위반 시 감점)

### 5.1 robots.txt — 반드시 지켜야 하는 경계

`https://support.brother.com/robots.txt` 를 교수자가 2026-11-18 확인한 결과입니다.

| 경로 | 자동 수집 | 비고 |
|---|:--:|---|
| `/g/s/id/htmldoc/**` (설명서 HTML·PDF) | ✅ 허용 | 설명서 수집 경로 |
| `/g/b/producttop.aspx` | ✅ 허용 | |
| `/g/b/faqtop.aspx` | ✅ 허용 | FAQ 목록 |
| `/g/b/faqend.aspx` | ✅ 허용 | FAQ 본문 |
| `/g/b/manualtop.aspx` | ✅ 허용 | |
| **`/*/manuallist.aspx`** | ❌ **금지** | `Disallow` 명시 |
| **`/*/downloadend.aspx`** | ❌ **금지** | `Disallow` 명시 |
| **`/*/downloadhowto.aspx`** | ❌ **금지** | |
| **`/*/agreement.aspx`** | ❌ **금지** | |
| **`/*/faqendbranchprintable.aspx`** | ❌ **금지** | 인쇄용 FAQ 페이지 |
| **`/g/s/wbm/**`** | ❌ **금지** | |
| **`/*?c=jp`, `/*&c=jp`** | ❌ **금지** | 일본 사이트 파라미터 |

> ⚠️ **Python 표준 라이브러리 `urllib.robotparser` 는 이 robots.txt를 올바르게 해석하지 못합니다.**
> `Disallow: /*/manuallist.aspx` 처럼 **경로 중간에 `*` 가 있는 패턴을 지원하지 않아**
> 금지 경로를 "허용"으로 잘못 보고합니다. 교수자가 실제로 확인한 버그입니다.
> robots 준수가 필요하면 와일드카드를 직접 처리하십시오.
> 참고 구현: `tools/polite_fetch.py` (교수자 제공, 그대로 써도 됩니다).

금지 경로의 자료가 필요하면 **자동 수집하지 말고 브라우저에서 수동으로** 열람하십시오.
우리 프로젝트에 필요한 자료는 **모두 허용 경로로 접근 가능**합니다.

### 5.2 요청 속도 — 차단 방지

교수자는 **빠른 연속 요청으로 HTTP 403(WAF 차단)을 실제로 유발**했습니다.
한 번 차단되면 수 분간 모든 요청이 실패합니다.

**준수 규칙:**

| 규칙 | 값 |
|---|---|
| 동일 호스트 요청 간 최소 간격 | **6초 이상** (권장 8~10초) |
| 동시 요청 | **1개** (병렬 수집 금지) |
| 재시도 | 최대 2회, 403/429/503 시 **지수적 백오프** |
| 403 연속 발생 시 | **즉시 중단**하고 수 분 대기. 우회 시도 금지 |
| User-Agent | 일반 브라우저 UA 사용. 위장·회전 금지 |

> 100건 FAQ × 8초 = **약 14분**입니다. 충분히 감당 가능합니다. 서두르지 마십시오.
> ⏱️ **DAY 1 에 수집을 시작하십시오.** DAY 4에 차단당하면 복구할 시간이 없습니다.

### 5.3 금지 사항 (절대)

- ❌ CAPTCHA 또는 접근 제한 **우회**
- ❌ robots.txt 금지 경로 자동 수집
- ❌ 병렬·고속 크롤링
- ❌ 로그인 필요 영역 접근
- ❌ 수집 자료의 **외부 공개 재배포** (GitHub 공개 저장소 업로드 포함)

### 5.4 저작권·재배포 — 리포지토리 정책

Brother 설명서와 FAQ는 **Brother Industries, Ltd. 의 저작물**입니다.
(설명서 하단: `© 2023/2024 Brother Industries, Ltd. All rights reserved.`)

**공식 이용약관 원문** (2026-11-18 확인,
`https://support.brother.com/g/s/common/as/kr/ko/legal.html`):

> "Except to enable your **personal use** of the Information available on these
> Web sites, you are **prohibited from reproducing, distributing, modifying,
> displaying, showing, publicly transmitting or otherwise creating secondary
> products** of any of the information, in whole or in part, regardless of form
> or medium, **without prior permission** from the intellectual property right
> owner(s)."

→ **개인 학습용 다운로드·분석은 허용 범위**로 보되,
  **재배포·공개 전송·2차적 저작물의 외부 공개는 금지**입니다.
→ 그래서 교수자가 원본을 배포하지 않고 **공식 URL 안내**로 대체합니다.
→ 상세 판단: ``../reports/licensing_decision.md``

| 행위 | 가능 여부 |
|---|---|
| 교육 과정 내 열람·분석·색인 | ✅ 수업 범위 내 사용 |
| 로컬에 원본 보관 | ✅ |
| 파생물(청크, 임베딩)을 **로컬**에 보관 | ✅ |
| **공개 저장소에 원본 PDF/FAQ 본문 커밋** | ❌ **금지** |
| 외부 공개 배포·재판매 | ❌ 금지 |

**권장 구성:**

```gitignore
# 원본 자료는 커밋하지 않고, 획득 스크립트와 manifest만 커밋한다
data/source/manuals/*.pdf
data/source/faq/**/*.html
data/processed/**        # 필요 시
```

대신 **재현 가능한 수집 스크립트 + `source_manifest.csv`(URL, SHA-256, 크기)** 를 커밋하십시오.
이것이 재현성 점수를 받는 올바른 방법이며, 저작권 문제도 피합니다.

---

## 6. 수집 산출물 권장 구조 (형식은 자유)

```
data/
├── source/                 # 원본. 절대 수정하지 않음
│   ├── manuals/
│   │   ├── MAN-INKJET-CVT830.pdf
│   │   └── MAN-LASER-CVL2508.pdf
│   └── faq/
│       └── <faq_id>.html
├── manifest/
│   └── source_manifest.csv # url, path, sha256, bytes, collected_at, applicable_models
└── processed/              # 정제·청킹 결과 (팀 자유 형식)
```

---

## 7. 수집 완료 판정 체크리스트

- [ ] 설명서 PDF 2개 다운로드 완료, SHA-256 기록
- [ ] 두 PDF 모두 열리고 **텍스트 추출 가능** 확인 (이미지 PDF 아님)
- [ ] 각 PDF의 커버 모델 목록을 **문서에서 직접 읽어** 기록
- [ ] FAQ 수집 건수 기록 (**중복 제거 후** 기준)
- [ ] FAQ `applicable_models` 매핑 완료
- [ ] 제품 10개 중 FAQ 미확보 제품을 **명시적으로 기록**
- [ ] `source_manifest.csv` 작성
- [ ] 원본이 `.gitignore` 되어 있는지 확인
- [ ] 403 차단 없이 수집 완료 (차단 발생 시 원인·대응 기록)

다음: ``data_processing_guide.md``
