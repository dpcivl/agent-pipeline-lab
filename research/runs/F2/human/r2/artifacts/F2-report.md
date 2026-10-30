# F2 실행 보고서 — 클릭 통계와 커스텀 별칭

- 설계서: `docs/features/F2.md` (v1)
- 계획: `docs/plans/F2-plan.md`, 목업: `docs/plans/mockups/F2-index.html`
- 실행 모드: human
- 브랜치: `run/F2-human-r2` (베이스 `0b748cc`)

## 1. 종료 상태

**완료.** 수용 기준 AC-1~AC-23을 모두 만족합니다(테스트 393개 통과, QA 블랙박스 검증 전부 PASS). blocker·major 지적 0건, minor 7건은 사람 결정(H3)에 따라 기록만 했습니다.

## 2. 단계별 진행 기록

| 단계 | 내용 | 호출한 에이전트 | 결과 |
|---|---|---|---|
| 0 | 실행 위치 확인 | (메인) | `RUN_WORKTREE` |
| 1 | 계획, 스켈레톤(스텁), 목업 7개 작성 | (메인) | H1: 사람이 수정 없이 승인 |
| 2 | 구현과 테스트 작성(병렬) | implementer, test-writer | 구현 완료, 새 테스트 파일 4개와 기존 파일 2개에 테스트 추가 |
| 3 | 테스트 루프 | tester | 1회차 PASS (393 passed, flaky 없음, ruff 통과) |
| 4 | 리뷰 루프 | reviewer, qa, security | 1라운드: blocker 0, major 0, minor 7 → H3: 사람이 "기록만" 결정, 루프 종료 |
| 5 | 커밋 전 확인 | (메인) | H4: 사람이 진행 승인 |
| 6 | 실행 보고서 | (메인) | 이 문서 |
| 7 | 문서와 기능 커밋 | doc-keeper | 서비스 문서, CHANGELOG, 기능 커밋 |

### 체크포인트 커밋

| 해시 | 메시지 |
|---|---|
| `2989fea` | wip(F2): 1 계획, 스켈레톤, 목업 |
| `16fdb28` | wip(F2): 2 구현과 테스트 작성 (리뷰 1라운드 체크포인트) |

3단계와 4단계에서는 수정이 없어 체크포인트 커밋을 따로 만들지 않았습니다. 기능 커밋은 doc-keeper가 만듭니다(`F2: ...`).

## 3. 루프 통계

- 테스트 루프: 1회 (1회차 PASS, 실패 0)
- 리뷰 라운드: 1라운드

| 라운드 | blocker | major | minor | 출처별 |
|---|---|---|---|---|
| 1 | 0 | 0 | 7 (중복 통합 후) | reviewer 6, security 3, qa 0 (R-1=S-1, R-2=S-2 통합) |

## 4. 미해결 지적과 minor 지적

미해결(2라운드 연속 미해결) 지적: 없음.

minor 지적 (사람 결정 H3: 고치지 않고 기록만):

| ID | 출처 | 내용 | 제안된 방향 |
|---|---|---|---|
| M-1 | R-1, S-1 | `GET /{code}`가 매번 쓰기 트랜잭션(UPDATE)이 되어, DB 쓰기 잠금이 5초 넘게 잡혀 있으면 리다이렉트 자체가 500이 됨(security 실측). F1에 없던 실패 방식 | 클릭 기록 실패 시 `get()`으로 대신 조회해 302 유지(fail-open), 또는 WAL + busy_timeout |
| M-2 | R-2, S-2 | `ensure_click_columns`의 확인과 `ALTER TABLE`이 원자적이지 않아, 여러 워커가 F1 DB로 동시에 시작하면 늦은 쪽이 `duplicate column name`으로 시작 실패(재시작하면 정상) | `BEGIN IMMEDIATE`로 묶기, 또는 duplicate column 오류만 무시 |
| M-3 | R-3 | 목업 색인 `F2-index.html`의 "문자열이 아님 → alias는 문자열이어야 합니다." 행이 실제와 다름(실제는 FastAPI 기본 422, F1 `url`과 같은 방식) | 문서 수정 |
| M-4 | R-4 | 통계 API 404 문구가 리터럴, `None`/`format_timestamp` 변환이 api.py와 web.py에 중복(조건식도 서로 다름) | `MSG_LINK_NOT_FOUND` 상수, `format_optional_timestamp()` 도우미 |
| M-5 | R-5 | 열이 일부만 있는 DB 마이그레이션 테스트 없음, `test_reserved_alias_still_serves_the_real_route` docstring이 확인 내용과 다름 | 테스트 보강 |
| M-6 | R-6 | OpenAPI 문서에 `POST /links` 409, `GET /links/{code}/stats` 404 미선언 | `responses=` 추가 |
| M-7 | S-3 | 코드를 아는 누구나 통계(클릭 수, 마지막 접근 시각)를 볼 수 있음. 추측하기 쉬운 별칭이면 상대가 링크를 열었는지 알 수 있음 | 설계상 허용(인증은 범위 밖). F3에서 소유자만 보게 할지 검토 |

## 5. 설계서 해석 결정

H1에서 사람이 승인한 결정입니다(`docs/plans/F2-plan.md` 5절). 실행 중 H2(설계서 모호함)는 발생하지 않았습니다.

| # | 결정 |
|---|---|
| D2-1 | 폼의 빈 별칭은 "별칭 없음"(무작위 코드). API는 필드 없음·`null`이 별칭 없음, `""`는 422 |
| D2-2 | 오류 우선순위: URL 검사 → 별칭 규칙 → 중복, 처음 걸린 하나만 표시 |
| D2-3 | 예약어는 대소문자 무시(`Admin`, `API`도 거절). 별칭 자체는 대소문자 구분 |
| D2-4 | 기존 무작위 코드와 같은 별칭도 409 |
| D2-5 | 409·422 본문은 `{"detail": "<한국어 문구>"}` |
| D2-6 | 마지막 접근 시각은 302를 보낸 시각(UTC, 초 단위, `Z`). 통계 화면은 `2026-10-29 01:23:45 UTC`로 표시하고 `<time datetime>`에 원래 형식 |
| D2-7 | 통계 API 404는 JSON `{"detail": "링크를 찾을 수 없습니다."}`, 통계 화면 404는 HTML |
| D2-8 | 클릭은 `GET /{code}`가 302를 보낸 경우만 셈. 봇·중복 구분 없음 |
| D2-9 | F1 DB는 앱 시작 시 없는 열만 `ALTER TABLE ADD COLUMN` |

구현 중 계획에 없던 판단(implementer 보고): 오류 문구 요소의 id를 F1의 `url-error`에서 계획·목업대로 `form-error`로 바꿈(URL 오류 화면의 문구와 위치는 F1과 같음).

## 6. 결과 확인 방법

1. 테스트 실행

   ```bash
   uv run pytest
   ```

   393개가 모두 통과해야 합니다.

2. 서버 실행 (저장소 루트에서)

   ```bash
   uv run uvicorn shortlink.main:create_app --factory
   ```

   기본 주소는 `http://localhost:8000`, DB 파일은 `shortlink.db`입니다. F1 시절의 `shortlink.db`가 있으면 그대로 써도 됩니다(기존 링크는 클릭 수 0부터 셉니다).

3. 브라우저로 확인할 순서
   1. `http://localhost:8000/` — 홈 화면에 "줄일 URL"과 "별칭 (선택)" 입력칸이 있는지 봅니다.
   2. URL `https://example.com`, 별칭 `my-link`를 넣고 "줄이기" → 결과 화면의 단축 URL이 `http://localhost:8000/my-link`이고 "통계 보기" 링크가 있는지 봅니다.
   3. "통계 보기"(`http://localhost:8000/stats/my-link`) → 클릭 수 0, 마지막 접근 "아직 없음".
   4. `http://localhost:8000/my-link`를 몇 번 열어 example.com으로 이동하는지 확인한 뒤, 통계 화면을 새로고침해 클릭 수와 마지막 접근 시각이 바뀌는지 봅니다.
   5. 홈에서 같은 별칭 `my-link`로 다시 제출 → 409 오류 화면("이미 쓰이는 별칭입니다…")에 입력값이 남아 있는지 봅니다.
   6. 별칭 `my_link`(밑줄) 또는 `abc`(3자) → 422 오류 화면.
   7. `http://localhost:8000/stats/nope` → "링크를 찾을 수 없습니다" 404 화면.
   8. 폭을 375px로 줄여 화면이 깨지지 않는지 봅니다.

4. API 확인 (다른 터미널에서)

   ```bash
   curl -i -X POST http://localhost:8000/links -H "Content-Type: application/json" -d "{\"url\": \"https://example.com\", \"alias\": \"api-link\"}"
   ```

   ```bash
   curl -i http://localhost:8000/links/api-link/stats
   ```

   첫 요청은 `201`과 `"code":"api-link"`, 두 번째는 `200`과 `"clicks":0`, `"last_accessed_at":null`이어야 합니다. API 문서는 `http://localhost:8000/docs`에서 볼 수 있습니다.
