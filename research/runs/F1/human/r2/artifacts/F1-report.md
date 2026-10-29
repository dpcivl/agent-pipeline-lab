# F1 실행 보고서 — 단축 URL 생성과 리다이렉트

- 모드: human
- 브랜치: `run/F1-human-r2` (기준 커밋 `8b7193b`)
- 종료 상태: **완료**

## 1. 단계별 진행 기록

| 단계 | 내용 | 호출한 에이전트 | 결과 |
|---|---|---|---|
| 1 | 계획(`docs/plans/F1-plan.md`), `src/` 스켈레톤 스텁 6개, 화면 목업 4개와 목록(`docs/plans/mockups/F1-index.html`) 작성 | 메인 직접 작성 | H1에서 사람이 수정 없이 승인 |
| 2 | 구현과 테스트 작성 (병렬) | implementer, test-writer | 구현 완료, 테스트 170건 작성 |
| 3 | 테스트 루프 | tester | 1회차 PASS (170/170), ruff 통과 |
| 4 | 리뷰 루프 | reviewer, qa, security (병렬) | 1라운드에서 blocker 0, major 0으로 종료 |
| 5 | 커밋 전 확인 | — | H4에서 사람이 진행 승인 (minor는 기록만) |
| 6 | 실행 보고서 | 메인 직접 작성 | 이 문서 |
| 7 | 문서와 기능 커밋 | doc-keeper | — |

### 체크포인트 커밋

| 해시 | 메시지 |
|---|---|
| `a36cfe2` | wip(F1): 1 계획, 스켈레톤, 목업 |
| `92f903f` | wip(F1): 2 구현과 테스트 작성 (리뷰 1라운드 체크포인트) |

3단계와 4단계에서는 수정이 없어 체크포인트 커밋을 만들지 않았습니다.

## 2. 루프 횟수와 지적 수

- 테스트 루프: 1회 (첫 실행 PASS, 수정 0회)
- 리뷰 라운드: 1라운드

| 라운드 | 담당 | blocker | major | minor |
|---|---|---|---|---|
| 1 | reviewer | 0 | 0 | 4 |
| 1 | qa | 0 | 0 | 2 |
| 1 | security | 0 | 0 | 7 |
| 1 | 합계 (중복 R-3 = S-1 합침) | 0 | 0 | 12 |

참고:
- 이 환경에서는 `uv run pytest`가 실행 정책에 막혀(`pytest.exe`, os error 4551) 모든 에이전트가 `uv run python -m pytest`로 실행했습니다.
- 2단계 중 implementer가 본 테스트 1건 실패(`test_check_order_when_several_rules_fail[long-and-scheme]`, 입력 길이 계산 오류)는 test-writer가 작업을 마치기 전에 스스로 고쳤습니다. 3단계 tester 실행에서는 실패가 없었습니다.

## 3. 미해결 지적

없음 (blocker와 major 0건).

## 4. minor 지적 (기록만, 수정하지 않음)

| id | 내용 | 비고 |
|---|---|---|
| R-3 / S-1 | 깊게 중첩된 JSON 본문(`[` 10만 개)에서 `RecursionError`가 잡히지 않아 422가 아니라 500 | `except (ValueError, RecursionError)`로 해결 가능 |
| R-1 | `urlsplit`의 `ValueError` 분기가 스킴 검사보다 먼저 실행되어 `ftp://[abc`가 `MSG_BAD_SCHEME` 대신 `MSG_NO_HOST`를 받음. lone surrogate가 `MSG_INVALID_CHARS` 문구를 받아 원인과 문구가 맞지 않음. 두 분기가 docstring과 계획에 없음 | 상태 코드는 422로 맞음 |
| R-2 | lone surrogate, `urlsplit` 오류, D-9 코드 충돌 재시도와 10회 소진을 검증하는 테스트 없음 | |
| R-4 | 템플릿 경로가 `main.TEMPLATES_DIR`과 `web.py` 두 곳에 정의되고 `main.TEMPLATES_DIR`은 쓰이지 않음 | |
| S-2 | 폼 `url`에 multipart 파일을 보내면 FastAPI 기본 422 JSON이 내부 객체 정보(SpooledTemporaryFile 속성)를 담아 응답 | HTML 화면 계약에서도 벗어남 |
| S-3 | 양방향 제어 문자(U+202E), 폭 없는 문자(U+200B), C1 제어 문자가 든 URL을 받아들여 결과 화면에서 URL 위장 가능 | `unicodedata.category`로 Cc/Cf/Zl/Zp 거절 제안 |
| S-4 | `https://good.com\@evil.com`을 `urlsplit`과 브라우저가 서로 다른 호스트로 해석 | 지금은 호스트 정책이 없어 악용 불가 |
| S-5 | CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy 응답 헤더 없음 | |
| S-6 | 서비스 자신(base_url)을 가리키는 URL로 리다이렉트 사슬이나 루프 생성 가능 | F3 범위 |
| S-7 | 인증, 요청 수 제한, 본문 크기 상한, CSRF 대책 없음. `/links`가 Content-Type을 확인하지 않음 | F3 범위 |
| Q-1 | 포트 범위를 벗어난 URL(`http://a.com:99999/`)도 생성됨 | 설계서에 규칙 없음 |
| Q-2 | `HEAD /{code}`가 405 | 설계서에 규칙 없음 |

## 5. 설계서 해석 결정

H1에서 사람이 승인한 결정 (`docs/plans/F1-plan.md` 6절):

| # | 결정 |
|---|---|
| D-1 | 공백이나 제어 문자(U+0000–U+001F, U+007F, `str.isspace`)가 든 URL은 422 |
| D-2 | 스킴은 대소문자를 무시하고 비교, 저장은 원문 그대로 |
| D-3 | 길이 2,048자는 Python `len()` 기준 |
| D-4 | JSON `null`, JSON 객체가 아닌 본문도 422. 오류 본문은 `{"detail": "<한국어 문구>"}` |
| D-5 | `created_at`은 초 단위에 `Z` 접미사 (`2026-10-29T01:23:45Z`) |
| D-6 | `Location`은 ASCII는 글자 그대로, 비ASCII 문자만 UTF-8 퍼센트 인코딩 |
| D-7 | 입력칸은 `type="text" inputmode="url"`, `required` 없음 (검증은 서버) |
| D-8 | 없는 코드는 API와 화면 모두 404 HTML 화면 |
| D-9 | 코드 충돌 시 최대 10번 재생성, 모두 실패하면 500 |

구현 중 implementer가 추가로 내린 판단 (reviewer가 타당하다고 확인):

| # | 판단 | 이유 |
|---|---|---|
| D-10 | UTF-8로 인코딩할 수 없는 문자열(lone surrogate)은 `MSG_INVALID_CHARS`로 422 | 거르지 않으면 SQLite 저장에서 500 |
| D-11 | `urlsplit`이 `ValueError`를 내는 URL(예: `http://[abc`)은 `MSG_NO_HOST`로 422 | 500 방지 (검사 순서 문제는 R-1) |
| D-12 | API 전용 문구 `MSG_NOT_OBJECT = "요청 본문은 JSON 객체여야 합니다."`를 `api.py`에 추가 | 계획에 본문이 객체가 아닐 때의 문구가 없었음 |
| D-13 | `Jinja2Templates`를 `web.py`에서 직접 생성 | `main` → `web` 순환 import 회피 (경로 중복은 R-4) |

## 6. 종료 상태

**완료.** AC-1~AC-23을 모두 충족합니다. 테스트 170건이 통과하고, qa가 실제 서버로 23개 수용 기준을 모두 확인했습니다. blocker와 major 지적은 없고, minor 12건은 위 4절에 기록했습니다.

## 7. 결과 확인 방법

1. 테스트 실행 (이 환경에서 `uv run pytest`가 막히면 두 번째 명령을 씁니다)

   ```bash
   uv run pytest
   ```

   ```bash
   uv run python -m pytest
   ```

2. 서버 실행 (저장소 루트에서, DB는 기본값 `shortlink.db`)

   ```bash
   uv run uvicorn shortlink.main:create_app --factory
   ```

3. 브라우저로 다음 순서대로 확인합니다.
   1. `http://localhost:8000/` — 홈 화면. "ShortLink", 설명 문구, "줄일 URL" 입력칸, "줄이기" 버튼이 보이는지
   2. 입력칸에 `https://example.com/path?q=1`을 넣고 "줄이기" — 결과 화면에 단축 URL 링크, 원래 URL, "복사" 버튼, "다른 URL 줄이기" 링크가 보이는지
   3. "복사"를 누르고 버튼이 2초 동안 "복사됨"으로 바뀌는지, 클립보드에 단축 URL이 들어갔는지
   4. 단축 URL 링크를 눌러 `https://example.com/path?q=1`로 이동하는지
   5. 홈에서 `javascript:alert(1)`을 넣고 "줄이기" — 빨간 오류 문구 "http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다."와 입력값이 남아 있는지
   6. `http://localhost:8000/zzzzzzz` — "링크를 찾을 수 없습니다" 화면과 "홈으로 가기" 링크
   7. 브라우저 개발자 도구에서 폭을 375px로 줄여 가로 스크롤이 생기지 않는지
   8. 서버를 껐다 다시 켠 뒤 2에서 만든 단축 URL이 여전히 이동하는지

4. API 확인

   ```bash
   curl -s -i -X POST http://localhost:8000/links -H "Content-Type: application/json" -d "{\"url\": \"https://example.com/path?q=1\"}"
   ```

   201과 `code`, `short_url`, `url`, `created_at`이 오면 정상입니다. 받은 `short_url`로 `curl -s -i <short_url>`을 보내면 302와 `Location` 헤더가 옵니다.

5. 화면 목업과 비교: `docs/plans/mockups/F1-index.html`을 브라우저로 엽니다.
