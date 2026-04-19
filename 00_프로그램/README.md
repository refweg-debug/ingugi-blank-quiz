# 인구기 워크스페이스

이 폴더는 `인구기` 과목 전용 작업 공간이다. 모든 원본 자료, 정제 텍스트, 메타데이터, 검증 대기 이미지, 프로그램 파일은 `인구기` 폴더 안에만 둔다.

## 폴더 규칙

- `가슴`, `등`, `배`, `골반`, `공통자료`
- 각 부위 폴더 아래:
  - `01_원본자료/강의원본`
  - `01_원본자료/필기본`
  - `01_원본자료/전공서`
  - `02_정제텍스트/강의원본`
  - `02_정제텍스트/필기본`
  - `02_정제텍스트/전공서`
  - `03_메타데이터`
  - `03_메타데이터/페이지매칭`
  - `04_검증대기`
  - `05_명제/강의원본`
  - `05_명제/필기본`
  - `05_명제/통합`
  - `06_검증명제/강의원본`
  - `06_검증명제/필기본`
  - `06_검증명제/통합`
  - `07_페이지판독/강의원본`
  - `07_페이지판독/필기본`
  - `07_페이지판독/전공서`
  - `08_문항/강의원본`
  - `08_문항/필기본`
  - `08_문항/통합`
  - `09_현재통합/current_pages`
  - `09_현재통합/current_propositions`
  - `09_현재통합/current_questions`
  - `09_현재통합/current_verified`
  - `09_현재통합/history`
  - `11_시각시드/강의원본`
  - `11_시각시드/필기본`
  - `12_완전텍스트기록/강의원본`
  - `12_완전텍스트기록/필기본`
  - `13_강의비교기록/강의원본`
  - `13_강의비교기록/필기본`
  - `녹음파일`
- `공통자료` 아래:
  - `00_수집함/기출문제_투입폴더`
  - `01_원본자료/조직학전공서`
  - `01_원본자료/기출문제_형식참고`
  - `02_정제텍스트/조직학전공서`
  - `02_정제텍스트/기출문제_형식참고`
  - `03_메타데이터`
  - `04_검증대기`
- `00_프로그램`
  - `config`: 원본 파일 동기화 설정
  - `src`: 파이프라인 코드
  - `output`: 전체 실행 요약
  - `_scratch`: 임시 이미지/디버그 산출물

## 현재 원칙

- 원본 자료는 복사해서 `01_원본자료`에 둔다. 원본 위치의 파일은 건드리지 않는다.
- 기존 `강의자료` 폴더에 있던 수업 PDF와 그 파생 산출물은 모두 `필기본`으로 이관한다. 교수 원본 PDF는 항상 먼저 `강의원본`에 둔다.
- `pure text`는 `핵심요약`이 아니라 페이지의 모든 구성요소를 빠짐없이 학습하기 위한 전량 추출 초안이어야 한다.
- 텍스트 블록은 필터링하지 않고 전부 저장한다.
- 페이지에 그림, 사진, 도식, 색상 주석, 손필기성 요소가 있으면 그 페이지는 완전성 확보 전까지 `04_검증대기`에 남긴다.
- `기출문제`는 부위별 암기 원본이 아니라 `출제 형식 참고용 공통 자료`로 취급한다. 따라서 과목 레벨의 `공통자료` 폴더에 통합 보관한다.
- 부위별 폴더에는 `기출문제` 디렉터리를 유지하지 않는다. 기출은 항상 `공통자료`에서만 관리한다.
- 조직학 내용은 부위별로 쪼개지지 않으므로 `공통자료/조직학전공서`에 통합 보관하고, 모든 부위의 명제 생성/검증에서 공용 레퍼런스로 참조한다.
- 조직학 전공서가 아직 비어 있어도 파이프라인은 계속 진행한다. 대신 조직학 표지어가 잡힌 페이지는 `...requires_histology_reference` 상태로 남겨 두고, 나중에 공통 조직학 전공서가 들어오면 재검증한다.
- 현재 버전은 `PDF`를 우선 지원한다. `docx`, `hwp`는 추후 변환기를 붙일 수 있게 구조만 열어 둔다.
- 각 부위의 `녹음파일` 폴더에는 수업 녹음파일을 텍스트로 변환한 뒤, 그 전사본에서 뽑은 명제 텍스트 파일을 보관한다.

## 실행

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\ingugi_pipeline.py sync
python .\src\ingugi_pipeline.py ingest-common-exams
python .\src\ingugi_pipeline.py build
```

## 기존 8765 review_app 정적 배포

- Active completion scope: `배` and `골반` only.
- Frozen units: do not update `가슴` or `등`; those exams are already completed.
- Question prompt quality rule: every fill-blank prompt must be self-contained. Do not use context-dependent references such as `이 두`, `이들`, `그 구멍`, `방금`, `여기서`, `해당 구조`, or `해당 부분` unless the antecedent is explicitly named inside the same prompt.
- Encoding guard: before running inline Python or regex scans from PowerShell, run `Set-ExecutionPolicy -Scope Process Bypass; . .\tools\Set-Utf8Session.ps1` inside `00_프로그램`. Without this, `$OutputEncoding` may be `us-ascii` and Korean literals can arrive in Python as `?`, breaking regex and path/prompt checks.

- 원본 로컬 검토 앱은 `review_app`이며, LAN 서버 주소는 `http://192.168.1.3:8765/` 형태다.
- Git에는 원본 PDF, 전공서, 녹음파일, 파이프라인 중간 산출물 전체를 올리지 않고, 정적 웹앱에 필요한 `review_app` 파일과 export된 `review_app/data`만 올린다.
- 정적 데이터는 기존 8765 서버의 `/api/library`, `/api/page`, `/api/review-image` 응답 형태를 파일로 바꾼 것이다.

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\export_review_app_static_bundle.py
python -m http.server 8770 --directory .\review_app
```

- 로컬 확인 주소는 `http://127.0.0.1:8770/` 이다.
- GitHub Pages 같은 정적 호스팅에서는 `00_프로그램/review_app` 폴더를 배포 대상으로 잡으면 된다.
- 새 문항 JSON이 생기면 exporter를 다시 실행한 뒤 `review_app/data` 변경분을 Git에 커밋한다.

## 범용 코어 연결

- 범용 코어는 `C:\Users\a\Desktop\거실\코덱스\범용프로그램`에 둔다.
- 범용 프롬프트는 `C:\Users\a\Desktop\거실\코덱스\범용프롬프트`에 둔다.
- 인구기 전용 하드코딩은 이 폴더 안의 `config/domain_pack`와 기존 설정 파일에 둔다.
- 인구기 명제 생성 정책은 `config/domain_pack/ingugi_proposition_policy.json`에 둔다.
- 원칙:
  - 수업자료를 1차 소스로 사용하되, 현재 적재본은 `필기본`으로 본다
  - 명확한 필기만 제한 반영
  - 전공서의 명확한 문장으로 canonical proposition 확장
  - 페이지 단어 조합형 명제는 근거 템플릿이 있을 때만 생성
- 브리지 실행:

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\ingugi_universal_bridge.py
```

- 이 명령은 인구기 도메인 팩을 범용 코어에 연결한 런타임 번들을 `output/universal_runtime_ingugi.json`으로 생성한다.

## 공통 기출 투입

- 기출문제는 `C:\Users\a\Desktop\거실\코덱스\인구기\공통자료\00_수집함\기출문제_투입폴더`에 넣는다.
- 이때 사용자는 `폴더 구조 통째로` 넣어도 된다.
- `ingest-common-exams` 명령은 다음을 수행한다.
  - 수집함 아래를 재귀 스캔
  - 중첩 폴더를 무시하고 파일만 평탄화
  - 동일한 파일명이 여러 개면 `수정 시간이 가장 최신인 파일`만 남김
  - 나머지 중복본은 제거
  - 빈 폴더를 정리
  - 결과 파일은 `공통자료/01_원본자료/기출문제_형식참고`에만 남김

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\ingugi_pipeline.py ingest-common-exams --build-after
```

## 산출물

- `02_정제텍스트/.../*.txt`: 페이지별 전체 텍스트 블록 인벤토리와 pure text 초안
- `03_메타데이터/*.json`: 페이지별 구성요소 수집 결과, 블록 목록, 검토 신호
- `03_메타데이터/페이지매칭/*.json`: `필기본`과 `강의원본` 사이의 페이지 대응 manifest
- `04_검증대기/*.md`: 완전성 미달 페이지 목록
- `04_검증대기/<문서명>/pXXX.png`: 이미지 위주 페이지 렌더링
- `00_프로그램/output/build_summary.json`: 전체 실행 요약

## 명제 초안 생성

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\generate_ingugi_propositions.py --unit 가슴 --category 필기본 --source-stem merged_20260404_010004 --page 2
```

- 이 명령은 필기본 텍스트, 명확한 페이지 용어, 부위 전공서 문장, 공통 조직학 전공서 문장을 조합해 1차 명제를 생성한다.
- 산출물은 `각 부위\05_명제\<카테고리>` 아래의 JSON과 Markdown으로 저장된다.
- 단, PDF는 `페이지 전체를 AI가 먼저 읽는 방식`이 강제된다. `05_명제` 산출물은 `07_페이지판독` manifest가 `ai_page_read_complete`가 되기 전까지 임시 상태다.
- 페이지에 조직학 표지어가 있지만 `공통자료/조직학전공서`가 비어 있으면 명제/검증 산출물은 `...requires_histology_reference` 상태로 유지된다.
- 용어 정규화용 시드 사전은 `config/domain_pack/ingugi_glossary_seed.json`에 둔다.

## AI 페이지 우선 판독

- PDF의 텍스트 레이어와 OCR 결과는 보조 증거일 뿐이며, 의미 추출의 시작점이 될 수 없다.
- 항상 `렌더링된 페이지 전체 -> 시각요소 인벤토리 -> 작은 글자 확대 판독 -> OCR 교차검증 -> 명제화` 순서를 따른다.
- `07_페이지판독\<카테고리>\<source>__pXXX_ai_page_read.json`이 없으면 해당 페이지는 `provisional_requires_ai_page_read`로 남는다.
- `init_ai_page_read_manifest.py`는 고해상도 페이지 PNG, 겹치는 타일 이미지, AI 요청 패키지를 함께 만든다.

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\init_ai_page_read_manifest.py --unit 가슴 --category 필기본 --source-stem merged_20260404_010004 --page 2
```

- 이 명령은 AI page-first 판독 결과를 채워 넣을 manifest 틀을 만든다.
- 동시에 `07_페이지판독\<카테고리>\_assets` 아래에 고해상도 페이지 이미지와 tile 이미지를 만들고, `..._ai_page_read_request.json`에 AI 입력 패키지를 저장한다.
- 최종 명제화와 문항화는 manifest의 `semantic_read_status`가 `ai_page_read_complete`일 때만 완료 상태로 본다.

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\apply_ai_page_read_result.py --unit 가슴 --category 필기본 --source-stem merged_20260404_010004 --page 2 --input-json C:\temp\page2_read_result.json --rerun
```

- 이 명령은 AI가 채운 판독 결과 JSON을 manifest에 반영하고, 필요하면 명제 생성과 검증을 다시 실행한다.
- 반영 시에는 품질 게이트가 함께 실행된다. `ai_page_read_complete`가 들어와도 저신뢰 요소, 누락된 시각 관계, 필수 inventory 누락이 있으면 `ai_page_read_needs_review`로 강등된다.
- 실제 provider 호출은 `run_ai_page_read.py`로 실행한다. `scaffold`는 스키마 검증용 초안을 만들고, `openai`는 `OPENAI_API_KEY`가 있을 때 실제 비전 호출을 수행한다.

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\run_ai_page_read.py --unit 가슴 --category 필기본 --source-stem merged_20260404_010004 --page 2 --provider scaffold
```

- `--apply --rerun`을 함께 주면 provider 결과를 manifest에 반영한 뒤 명제 생성과 검증까지 다시 실행한다.
- 문서 전체를 순차 처리할 때는 아래 래퍼를 사용한다.

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\run_ai_page_read_for_source.py --unit 가슴 --category 필기본 --source-stem merged_20260404_010004 --provider scaffold --max-pages 3
```

- `--skip-complete`를 주면 이미 완료된 페이지는 건너뛴다.

## 전공서 그림 참조 인덱스

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\build_textbook_figure_reference_index.py --unit 가슴
```

- 이 명령은 부위 전공서와 `공통자료/조직학전공서`를 함께 읽어, 그림이 있는 페이지마다 `같은 페이지 문맥 + 앞뒤 페이지 문맥 + 키워드`를 묶은 로컬 참조 인덱스를 생성한다.
- 출력은 `output/<unit>_textbook_figure_reference_index.json|md`에 저장된다.
- 이후 이미지 판독은 일반 인터넷 검색보다 이 인덱스를 우선 사용해 그림 후보와 주변 문장을 좁힌 뒤 명제를 만든다.

## 전공서 figure atlas

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\build_textbook_figure_atlas.py --unit 가슴
```

- 이 명령은 그림 참조 인덱스를 기반으로 전공서의 figure page를 atlas 형태로 미리 뽑아 둔다.
- PDF 안의 image block이 잡히면 crop으로 저장하고, 그렇지 않으면 review page 전체 이미지를 fallback으로 저장한다.
- 이후 AI page read 요청은 이 atlas와 참조 인덱스의 후보 페이지를 먼저 참고해 속도와 정확도를 같이 올린다.

## 전체 전공서 시각 캐시 선제 구축

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\prepare_textbook_visual_cache.py
```

- 이 명령은 각 부위의 전공서에 대해 `그림 참조 인덱스 -> figure atlas`를 전부 미리 생성한다.
- 기준은 조직학 여부가 아니라 `전공서 파일에 있는 모든 사진/그림 페이지`다.
- 이후 개별 page read는 매번 전공서 PDF 전체를 다시 훑지 않고, 먼저 이 캐시를 참조한다.

## 조직학 공통 전공서 갭 리포트

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\report_histology_reference_gaps.py --unit 가슴 --category 필기본 --source-stem merged_20260404_010004
```

- 이 명령은 현재 자료에서 조직학 표지어가 잡히는 페이지를 모아 `output/*_histology_reference_gap.json|md`로 저장한다.
- 조직학 책이 아직 없을 때도 어떤 페이지가 나중에 공통 조직학 전공서 재검증 대상인지 먼저 분리할 수 있다.

## 페이지 매칭과 통합본

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\match_course_material_pages.py --unit 가슴 --note-source-stem merged_20260404_010004
python .\src\adapter_bridge\process_integrated_source.py --unit 가슴 --note-source-stem merged_20260404_010004
```

- 첫 번째 명령은 `필기본`과 `강의원본`의 페이지 대응 manifest를 `03_메타데이터/페이지매칭`에 만든다.
- `강의원본` 메타데이터가 없으면 즉시 오류로 멈춘다. `강의원본` 누락은 예외 흐름이 아니라 입력 실수로 취급한다.
- 두 번째 명령은 `05_명제/통합`과 `06_검증명제/통합` 아래에 합쳐진 결과를 쓴다.

## 입력 검증

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\validate_ingugi_inputs.py
```

- 이 명령은 `필기본`이 있는 단원마다 `강의원본` 메타데이터가 존재하는지 먼저 검사한다.
- 누락이 있으면 `output/ingugi_input_validation.json`에 기록하고 즉시 오류로 종료한다.
- `process_all_ingugi_sources.py`는 시작할 때 이 검사를 자동으로 먼저 실행한다.

## 문서 전체 일괄 처리

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\process_ingugi_source.py --unit 가슴 --category 필기본 --source-stem merged_20260404_010004 --verify
```

- 이 명령은 문서의 모든 페이지에 대해 `05_명제` 생성과 `06_검증명제` 생성을 순차 실행한다.
- 전체 진행 요약은 `output/<unit>_<category>_<source>_pagewise_summary.json`에 저장된다.
- `process_all_ingugi_sources.py`는 위 처리 뒤에 자동으로 페이지 매칭과 통합본 생성까지 수행한다.

## 빈칸문항 생성

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\generate_ingugi_questions.py --unit 가슴 --category 필기본 --source-stem merged_20260404_010004 --page 2
```

- 문항은 전부 `빈칸채우기`로만 생성한다.
- 한 명제에서 용어, 수치, 서술어를 각각 비운 단일 빈칸 문제를 여러 개 만든다.
- 한 명제에 학습 요소가 여러 개 있으면 다중 빈칸 문제도 함께 만든다.
- `AI page read`가 완료된 페이지에서는 같은 명제를 `image_grounded_fill_blank`로도 생성한다.
- 출력 경로는 `08_문항/<카테고리>/<source>__pXXX_questions.json|md` 이다.
## Figure Concept Cache

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\build_textbook_figure_concept_cache.py --unit 가슴
```

- `figure atlas`의 각 그림 crop마다 별도 JSON 캐시를 만든다.
- 각 그림 캐시에는 `image_path`, `anchor_keywords`, `same_page_context`, `neighbor_context`, `figure_identity_contract`, `visual_concept_contract`, `visual_propositions` 저장 슬롯이 들어간다.
- 목적은 `그림 파일 자체`와 `그 그림의 연관 개념/명제 파일`을 미리 묶어 두는 것이다.
- 전체 시각 캐시 선제 구축 명령은 이제 `그림 참조 인덱스 -> figure atlas -> figure concept cache`까지 한 번에 만든다.
## 필기본 완전 텍스트 기록

```powershell
cd C:\Users\a\Desktop\거실\코덱스\인구기\00_프로그램
python .\src\adapter_bridge\build_note_exhaustive_text_records.py --unit 배 --category 필기본 --source-stem 20260402_필기본_인체의구조와기능1(신화경교수님)_배(소화비뇨계통)1_강권호
```

- `12_완전텍스트기록/<category>/<source>__pXXX.json|md`는 필기본 페이지를 `text layer + OCR`로 함께 기록한 페이지 단위 텍스트 감사 산출물이다.
- 각 페이지마다 아래를 저장한다.
  - `pdf_char_inventory`: PDF text layer에서 읽은 글자 단위 기록
  - `pdf_span_inventory`, `pdf_lines`, `pdf_words`: text layer 전수 기록
  - `ocr_fragments`, `ocr_lines`: 렌더링된 페이지 이미지를 다시 읽은 OCR 기록
  - `merged_lines`: PDF와 OCR을 줄 단위로 대조한 병합 결과
  - `corrected_blocks`: 명제 생성이 우선 사용하는 교정 텍스트 블록
  - `supplemental_ocr_blocks`: 누락 방지용 OCR 보조 블록
- `process_ingugi_source.py`는 `필기본` 문서를 처리할 때 이 기록을 먼저 만들고, 이후 명제 생성은 기존 `03_메타데이터`의 `text_blocks`보다 `12_완전텍스트기록`의 `corrected_blocks`를 우선 사용한다.
