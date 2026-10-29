# F1 실행 보고서 — 단축 URL 생성과 리다이렉트

- 모드: auto
- 브랜치: `run/F1-auto-r2` (기준 스냅샷 `e8f75ad`)
- 설계서: `docs/features/F1.md` v2
- 종료 상태: **완료**. AC-1~AC-23 모두 만족, 테스트 96개 통과, 리뷰 2라운드에서 blocker·major 0건

## 1. 단계별 진행 기록

| 단계 | 내용 | 호출한 에이전트 | 결과 |
|---|---|---|---|
| 0 | 실행 위치 확인 | (메인) | `RUN_WORKTREE` |
| 1 | 계획서, 해석 결정(D-1~D-7), 스텁 5개(`codes`, `validation`, `storage`, `api`, `web`)와 `main.py` 연결, 목업 4개와 목록 | (메인) | H1 auto 자체 승인 |
| 2 | 구현과 테스트 작성 (병렬) | implementer, test-writer | 구현 완료, 테스트 89개 작성. implementer 판단 2건을 D-8, D-9로 기록 |
| 3 | 테스트 루프 1회차 | tester | PASS (89/89), ruff 통과 |
| 4-1 | 리뷰 1라운드 (병렬) | reviewer, qa, security | blocker 0, major 1(중복 합침), minor 9 |
| 4-1 수정 | major 수정과 회귀 테스트 (병렬) → 재실행 | implementer, test-writer → tester | 결정 D-10 추가, PASS (96/96) |
| 4-2 | 리뷰 2라운드 (병렬, 변경분만) | reviewer, qa, security | blocker 0, major 0, minor 1 → 루프 종료 |
| 5 | 커밋 전 확인 | (메인) | H4 auto, 바로 진행 |
| 6 | 실행 보고서 | (메인) | 이 문서 |
| 7 | 서비스 문서와 기능 커밋 | doc-keeper | — |

### 체크포인트 커밋

| 해시 | 메시지 | 비고 |
|---|---|---|
| `d829929` | wip(F1): 1 계획, 스켈레톤, 목업 | |
| `166f2b6` | wip(F1): 2 구현과 테스트 작성 | 리뷰 1라운드 체크포인트 (3단계는 수정 없이 PASS여서 별도 커밋 없음) |
| `36183ce` | wip(F1): 4 리뷰 1라운드 수정 | 리뷰 2라운드 체크포인트 |

## 2. 루프 횟수와 지적 수

- 테스트 루프: 1회 (첫 실행 PASS). 리뷰 수정 후 재실행 1회 포함 tester 호출은 총 2번
- 리뷰 라운드: 2라운드

| 라운드 | blocker | major | minor | 비고 |
|---|---|---|---|---|
| 1 | 0 | 1 (R-1 = S-1 = Q-1 합침, 원 보고 3건) | 9 (R-2, R-3, R-4, S-2, S-3, S-4, S-5, Q-2, Q-3) | reviewer 4건, security 5건, qa 3건 |
| 2 | 0 | 0 | 1 (R-5) | R-1, S-1, Q-1 해결 확인 |

해결한 지적:

- **R-1/S-1/Q-1 [major]** 짝 없는 서로게이트 문자(`"\ud800"`)가 든 URL이 검증을 통과해 SQLite 저장 단계에서 500. → `validate_url`에서 U+D800~U+DFFF를 422로 거절(D-10). 회귀 테스트 3개(케이스 7개) 추가.

## 3. 미해결 지적과 minor 지적

미해결(blocker·major): 없음.

minor (기록만, 고치지 않음):

| id | 내용 | 제안 |
|---|---|---|
| R-2 | async 핸들러 안에서 동기 sqlite3 I/O를 호출해 이벤트 루프를 막음 | `run_in_threadpool`로 감싸거나 `def` 핸들러로 |
| R-3 | 클립보드 API가 없거나(비보안 컨텍스트 http 배포) 복사가 실패하면 반응이 없음 | 실패 시 텍스트 선택이나 안내 문구 |
| R-4 | 템플릿 경로 상수가 `main.py`(미사용)와 `web.py` 두 곳에 있음 | 공용 모듈로 옮기기 |
| R-5 | 원시 서로게이트 바이트 테스트가 오류 문구까지는 확인하지 않음 | `== {"detail": MSG_SURROGATE}`로 강화 |
| S-2 | 깊게 중첩된 JSON 본문이 `RecursionError`로 500 | `except (ValueError, RecursionError)` |
| S-3 | C1 제어 문자, 양방향 제어 문자(Cc/Cf)를 허용해 결과 화면 표시를 꾸밀 수 있음 | `unicodedata.category`로 Cc/Cf 거절 |
| S-4 | 요청 수 제한과 본문 크기 제한 없음 (F3 범위) | F3에서 rate limit, 프록시에서 본문 상한 |
| S-5 | CSP, nosniff, frame-ancestors 같은 보안 응답 헤더 없음 | 헤더 미들웨어 |
| Q-2 | `/a/b`처럼 슬래시가 든 경로의 404가 JSON(FastAPI 기본) | 전역 404 핸들러로 HTML |
| Q-3 | 끝 슬래시 경로(`/nope/`)가 307로 리다이렉트된 뒤 404 | `redirect_slashes=False` |

참고 기록(지적 아님): 폼으로 잘못된 UTF-8 바이트를 보내면 Starlette가 U+FFFD로 바꿔 디코딩해 그대로 저장된다(qa 2라운드). `http://evil.com\@good.com`은 파이썬과 브라우저의 호스트 해석이 다르다. 지금은 호스트 허용 목록이 없어 영향이 없지만 도메인 차단 기능을 넣을 때 고려해야 한다(security 1라운드).

## 4. 설계서 해석 결정

상세 내용은 `docs/plans/F1-decisions.md`에 있다.

| id | 결정 |
|---|---|
| D-1 | 스킴은 대소문자를 구분하지 않고 비교하며, 값은 받은 그대로 저장 |
| D-2 | 공백 문자나 제어 문자(U+0000~U+001F, U+007F)가 든 URL은 422 (앞뒤 공백 포함, 지우지 않음) |
| D-3 | `Location` 헤더에서만 비ASCII를 UTF-8 퍼센트 인코딩하고 ASCII는 그대로 둠 |
| D-4 | 422 본문은 API `{"detail": "<한국어 문구>"}`, 폼은 오류 HTML |
| D-5 | 없는 코드는 항상 404 HTML 화면 |
| D-6 | `created_at`은 초 단위, `Z` 접미사 |
| D-7 | 폼 입력칸은 `type="text"`이고 `required`가 없음. 서버 422 화면이 보이게 하기 위함 |
| D-8 | `urlsplit`이 파싱하지 못하는 URL은 "호스트 없음" 문구로 422 (implementer 판단) |
| D-9 | JSON이 아니거나 객체가 아닌 본문은 422와 전용 문구 (implementer 판단) |
| D-10 | 서로게이트 문자(U+D800~U+DFFF)는 422 `URL에 쓸 수 없는 문자가 있습니다.` (리뷰 1라운드 반영) |

## 5. 종료 상태

**완료.** 테스트 96개 통과, `ruff check`와 `ruff format --check` 통과, bandit 지적 없음. qa가 실제 서버로 AC-1~AC-23을 모두 확인했고, 같은 DB로 재시작한 뒤의 리다이렉트(AC-14)도 확인했다. 리뷰 2라운드에서 blocker·major 0건이며, minor 10건은 기록만 했다.

## 6. 결과 확인 방법

1. 테스트 실행

   ```bash
   uv run pytest
   ```

   96개 통과가 나와야 한다.

2. 서버 실행 (저장소 루트에서)

   ```bash
   uv run uvicorn shortlink.main:create_app --factory
   ```

   기본 DB는 현재 폴더의 `shortlink.db`, 기본 주소는 `http://localhost:8000`이다. 바꾸려면 `SHORTLINK_DB_PATH`와 `SHORTLINK_BASE_URL`을 쓴다.

3. 브라우저에서 확인할 순서
   1. `http://localhost:8000/` 홈 화면을 연다. 서비스 이름 "ShortLink", 한 줄 설명, "줄일 URL" 입력칸, "줄이기" 버튼이 보여야 한다.
   2. `https://example.com/path?q=1`을 입력하고 "줄이기"를 누른다. 결과 화면에 단축 URL 링크, 원래 URL, "복사" 버튼, "다른 URL 줄이기" 링크가 보여야 한다.
   3. "복사"를 누르면 버튼이 2초 동안 "복사됨"으로 바뀌고 클립보드에 단축 URL이 들어간다.
   4. 단축 URL 링크를 누르면 `https://example.com/path?q=1`로 이동해야 한다.
   5. 홈에서 `ftp://example.com`을 제출한다. 오류 문구 "http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다."가 나오고, 입력칸에 값이 남아 있어야 한다.
   6. `http://localhost:8000/nope123`을 연다. "링크를 찾을 수 없습니다" 안내와 "홈으로 가기" 링크가 보여야 한다.
   7. 개발자 도구에서 폭을 375px로 줄여도 가로 스크롤이 생기지 않아야 한다.
   8. 화면을 목업과 비교한다. 목업 목록은 `docs/plans/mockups/F1-index.html`을 브라우저로 열면 된다.

4. API 확인

   ```bash
   curl -i -X POST http://localhost:8000/links -H "Content-Type: application/json" -d '{"url": "https://example.com/path?q=1"}'
   ```

   201과 `code`, `short_url`, `url`, `created_at`이 와야 한다. 받은 `short_url`로 `curl -i <short_url>`을 보내면 `302`와 `Location: https://example.com/path?q=1`이 와야 한다.
