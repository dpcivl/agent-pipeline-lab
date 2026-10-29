# F1 실행 보고서 — 단축 URL 생성과 리다이렉트

- 모드: human
- 브랜치: `run/F1-human-r1`
- 종료 상태: **완료**
- 설계서: `docs/features/F1.md` (v2), 계획: `docs/plans/F1-plan.md`, 목업: `docs/plans/mockups/F1-index.html`

## 1. 단계별 진행 기록

| 단계 | 내용 | 호출한 에이전트 | 결과 |
|---|---|---|---|
| 0 | 실행 위치 확인 | (메인) | `RUN_WORKTREE` |
| 1 | 계획, 스켈레톤(src 스텁 7개 + `create_app` 연결), 목업 4개 + 목록 | (메인) | H1: 사람 승인, 수정 요청 없음 |
| 2 | 구현과 테스트 작성 (병렬) | implementer, test-writer | 둘 다 완료 |
| 3 | 테스트 루프 | tester | 1회차 PASS (152개) |
| 4-1 | 리뷰 1라운드 | reviewer, qa, security (병렬) | major 1, minor 5 (통합 후) |
| 4-1 | H3 | (사람) | M-1 새 문구로 422, R-2·R-3·S-3 수정, Q-2·S-2 기록만 |
| 4-1 | 1라운드 수정 | implementer, test-writer (병렬), tester | PASS (175개) |
| 4-2 | 리뷰 2라운드 | reviewer, qa, security (이어서 호출) | blocker 0, major 0, minor 2 → 루프 종료 |
| 5 | H4 커밋 전 확인 | (사람) | 진행 승인 |
| 6 | 실행 보고서 | (메인) | 이 문서 |
| 7 | 문서와 기능 커밋 | doc-keeper | 기능 커밋 |

### 체크포인트 커밋

| 해시 | 메시지 | 비고 |
|---|---|---|
| `214eec8` | wip(F1): 1 계획, 스켈레톤, 목업 | |
| `9f6fab9` | wip(F1): 2 구현과 테스트 작성 | 리뷰 1라운드 체크포인트 |
| `f1200fd` | wip(F1): 4 리뷰 1라운드 수정 | 리뷰 2라운드 체크포인트 |

테스트 루프에서 수정이 없었으므로 `3 테스트 루프 <n>회차 수정` 체크포인트는 없다.

## 2. 루프 횟수와 지적 수

- 테스트 루프: 1회 (첫 실행 PASS). 리뷰 1라운드 수정 후 재실행 1회 PASS.
- 리뷰 라운드: 2라운드

| 라운드 | 에이전트 | blocker | major | minor |
|---|---|---|---|---|
| 1 | reviewer | 0 | 1 (R-1) | 2 (R-2, R-3) |
| 1 | qa | 0 | 1 (Q-1) | 1 (Q-2) |
| 1 | security | 0 | 0 | 3 (S-1, S-2, S-3) |
| 1 | **통합** | **0** | **1** (M-1 = R-1/Q-1/S-1) | **5** (R-2, R-3, Q-2, S-2, S-3) |
| 2 | reviewer | 0 | 0 | 1 (R-4) |
| 2 | qa | 0 | 0 | 0 |
| 2 | security | 0 | 0 | 1 (S-2 유지) |
| 2 | **통합** | **0** | **0** | **2** (R-4, S-2) |

### 1라운드 처리 (H3 사람 결정)

| id | 심각도 | 내용 | 처리 |
|---|---|---|---|
| M-1 (R-1/Q-1/S-1) | major | JSON의 짝 없는 서로게이트(`\ud800`) URL이 검증을 통과해 SQLite 바인딩에서 500 | 수정: 검증 규칙 5 추가, `MSG_INVALID_ENCODING`으로 422 (D-9). 2라운드에서 해결 확인 |
| R-2 | minor | `navigator.clipboard`가 없으면 복사 실패 안내가 안 나옴 | 사람 결정으로 수정 (D-11). 해결 확인 |
| R-3 | minor | 충돌 재시도 테스트 단언이 느슨함 | 사람 결정으로 수정. 해결 확인 |
| S-3 | minor | 보안 응답 헤더 없음 | 사람 결정으로 수정 (D-10, `security.py`). 해결 확인 |
| Q-2 | minor | `https://[` 같은 깨진 호스트에도 "호스트가 없습니다" 문구 | 기록만 |
| S-2 | minor | 요청 수 제한, 본문 크기 제한 없음 | 기록만 (F3 범위) |

## 3. 미해결 지적과 minor 지적

미해결(blocker/major): 없음.

남은 minor:

- **Q-2** 형식이 깨진 호스트(`https://[`)에 "URL에 호스트(도메인)가 없습니다." 문구가 나온다. 422로 거절되므로 동작 문제는 없다.
- **S-2** 요청 수 제한과 요청 본문 크기 제한이 없다. F3(요청 수 제한)에서 다룬다.
- **R-4** `test_copy_script_guards_missing_clipboard_api`가 `"navigator.clipboard"` 문자열만 확인해서 가드를 지워도 통과한다. `"!navigator.clipboard"` 확인으로 강화 가능.

참고 (지적 아님):

- 처리되지 않은 예외로 나는 500 응답에는 `nosniff`가 붙지 않는다(Starlette ServerErrorMiddleware가 사용자 미들웨어 바깥). 본문은 고정 문구라 위험 없음.
- F2 커스텀 별칭에서는 `docs`, `redoc`, `openapi.json`, `static`, `links` 같은 예약어를 막아야 한다. 라우트 순서상 그런 별칭은 리다이렉트되지 않는다.
- 이 환경에서는 응용 프로그램 제어 정책(os error 4551)이 `pytest.exe`를 막아 `uv run pytest` 대신 `uv run python -m pytest`로 실행했다.

## 4. 설계서 해석 결정

계획서 5절에 기록. D-1~D-8은 H1에서 사람이 승인, D-9~D-11은 H3에서 사람이 결정했다. 테스트 루프에서 spec_ambiguous(H2)는 없었다.

| # | 결정 |
|---|---|
| D-1 | 스킴은 대소문자 무시(`HTTPS://` 허용), 저장은 원문 그대로 |
| D-2 | 공백, ASCII 제어 문자가 든 URL은 422 |
| D-3 | 2,048자는 문자(code point) 수 기준 |
| D-4 | `Location`은 ASCII 그대로, 비ASCII만 UTF-8 퍼센트 인코딩 (`RedirectResponse` 대신 `Response`) |
| D-5 | 검증 실패 422 본문은 `{"detail": "<한국어 문구>"}`, 형식 오류는 FastAPI 기본 422 |
| D-6 | 없는 코드는 API/화면 구분 없이 HTML 404 |
| D-7 | 폼 입력칸은 `type="text"` + `inputmode="url"`, `required` 없음 (검증은 서버 한 곳) |
| D-8 | `created_at`은 초 단위, `Z` 접미사 |
| D-9 | UTF-8로 인코딩할 수 없는 문자(짝 없는 서로게이트)가 든 URL은 `MSG_INVALID_ENCODING`으로 422 |
| D-10 | 우리 HTML 화면에 CSP, 모든 응답에 `X-Content-Type-Options: nosniff`, `/docs`·`/redoc`은 CSP 제외 |
| D-11 | `navigator.clipboard`가 없으면 즉시 복사 실패 문구 표시 |

## 5. 종료 상태

**완료.** AC-1~AC-23 모두 테스트(175개 통과)와 qa 블랙박스 검증으로 확인했다. blocker/major 미해결 없음.

## 6. 결과 확인 방법

1. 테스트 실행

   ```bash
   uv run python -m pytest -q
   ```

   (`uv run pytest`가 실행 정책으로 막히지 않는 환경이면 그것을 써도 된다.)

2. 서버 실행 (저장소 루트에서)

   ```bash
   uv run uvicorn shortlink.main:create_app --factory
   ```

   기본 DB는 `shortlink.db`, 기본 주소는 `http://localhost:8000`. 바꾸려면 `SHORTLINK_DB_PATH`, `SHORTLINK_BASE_URL` 환경 변수를 쓴다.

3. 브라우저로 확인할 순서
   1. `http://localhost:8000/` — 홈 화면. 목업 `docs/plans/mockups/F1-home.html`과 비교.
   2. 입력칸에 `https://example.com/path?q=1`을 넣고 "줄이기" — 결과 화면에 단축 URL 링크, 원래 URL, "복사" 버튼, "다른 URL 줄이기" 링크가 보인다. "복사"를 누르면 "복사했습니다."가 나온다.
   3. 단축 URL 링크를 클릭 — `https://example.com/path?q=1`로 이동한다.
   4. 홈에서 `ftp://example.com/files/report.pdf`를 제출 — 오류 문구 "http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다."가 보이고 입력값이 남는다.
   5. 홈에서 빈 값으로 제출 — "URL을 입력해 주세요."
   6. `http://localhost:8000/zzzzzzz` — "링크를 찾을 수 없습니다" 화면과 "홈으로 가기" 링크.
   7. 브라우저 개발자 도구에서 폭 375px로 바꿔 가로 스크롤이 없는지 확인.

4. API 확인 (`http://localhost:8000/docs`에서도 가능)

   ```bash
   curl -s -i -X POST -H "Content-Type: application/json" -d "{\"url\": \"https://example.com/path?q=1\"}" http://localhost:8000/links
   ```

   201과 `code`, `short_url`, `url`, `created_at`이 오고, `curl -s -i http://localhost:8000/<code>`는 302와 `Location`을 돌려준다.
