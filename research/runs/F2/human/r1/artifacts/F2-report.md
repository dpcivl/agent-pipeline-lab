# F2 실행 보고서 — 클릭 통계와 커스텀 별칭

- 모드: human
- 브랜치: `run/F2-human-r1`
- 종료 상태: **완료**
- 설계서: `docs/features/F2.md` (v1), 계획: `docs/plans/F2-plan.md`, 목업: `docs/plans/mockups/F2-index.html`

## 1. 단계별 진행 기록

| 단계 | 내용 | 호출한 에이전트 | 결과 |
|---|---|---|---|
| 0 | 실행 위치 확인 | (메인) | `RUN_WORKTREE` |
| 1 | 계획, 스켈레톤(validation·repository·api·web 스텁, db 문서화), 목업 6개 + 목록 | (메인) | H1: 사람 승인, 수정 요청 없음 |
| 2 | 구현과 테스트 작성 (병렬) | implementer, test-writer | 둘 다 완료 |
| 3 | 테스트 루프 | tester | 1회차 PASS (405개) |
| 4-1 | 리뷰 1라운드 | reviewer, qa, security (병렬) | blocker 0, major 0, minor 8 (통합 후) |
| 4-1 | H3 | (사람) | M-1(R-3/S-1)과 R-1을 major로 올려 수정, 나머지 기록만 |
| 4-1 | 1라운드 수정 | implementer, test-writer (병렬), tester (이어서 호출) | PASS (406개) |
| 4-2 | 리뷰 2라운드 | reviewer, qa, security (이어서 호출) | blocker 0, major 0 → 루프 종료 |
| 5 | H4 커밋 전 확인 | (사람) | 진행 승인 |
| 6 | 실행 보고서 | (메인) | 이 문서 |
| 7 | 문서와 기능 커밋 | doc-keeper | 기능 커밋 `F2: ...` |

참고: 1라운드 수정 때 implementer와 test-writer는 2단계 에이전트를 이어서 호출하지 않고 새로 띄웠다(절차 규칙 위반, 결과에는 영향 없음).

### 체크포인트 커밋

| 해시 | 메시지 | 비고 |
|---|---|---|
| `216517a` | wip(F2): 1 계획, 스켈레톤, 목업 | |
| `e9f25fe` | wip(F2): 2 구현과 테스트 작성 | 리뷰 1라운드 체크포인트 |
| `6b2d234` | wip(F2): 4 리뷰 1라운드 수정 | 리뷰 2라운드 체크포인트 |

테스트 루프에서 수정이 없었으므로 `3 테스트 루프 <n>회차 수정` 체크포인트는 없다. 기능 커밋은 doc-keeper가 이 보고서를 포함해 만든다.

## 2. 루프 횟수와 지적 수

- 테스트 루프: 1회 (첫 실행 PASS, 405개). 리뷰 1라운드 수정 후 재실행 1회 PASS (406개).
- 리뷰 라운드: 2라운드

| 라운드 | 에이전트 | blocker | major | minor |
|---|---|---|---|---|
| 1 | reviewer | 0 | 0 | 4 (R-1, R-2, R-3, R-4) |
| 1 | qa | 0 | 0 | 0 |
| 1 | security | 0 | 0 | 5 (S-1~S-5) |
| 1 | **통합** | **0** | **0** | **8** (M-1 = R-3/S-1, R-1, R-2, R-4, S-2~S-5) |
| 2 | reviewer | 0 | 0 | 2 (R-5, R-6) |
| 2 | qa | 0 | 0 | 0 |
| 2 | security | 0 | 0 | 4 (S-2~S-5 유지) |
| 2 | **통합** | **0** | **0** | **8** (R-2, R-4, R-5, R-6, S-2~S-5) |

### 1라운드 처리 (H3 사람 결정)

| id | 원래 심각도 | 내용 | 처리 |
|---|---|---|---|
| M-1 (R-3/S-1) | minor → **major** | F1 DB 마이그레이션의 컬럼 확인과 `ALTER`가 원자적이지 않아, 여러 워커가 동시에 시작하면 `duplicate column name`으로 시작 실패 (security 재현 90/120) | 수정: `init_schema`를 `BEGIN IMMEDIATE` 트랜잭션 하나로 묶음. 회귀 테스트 `test_concurrent_init_schema_on_f1_database_migrates_exactly_once` 추가(수정 전 코드에서 5/5 실패 확인). 2라운드에서 reviewer·qa·security 모두 해결 확인 |
| R-1 | minor → **major** | 스텁 시절 docstring("F2 (to add)")이 남고 `create_link`에 alias·409 설명 없음 | 수정. 2라운드에서 해결 확인 |
| R-2, R-4, S-2~S-5 | minor | 아래 3절 | 기록만 |

## 3. 미해결 지적과 minor 지적

미해결(blocker/major): 없음.

남은 minor:

- **R-2** 통계 API 404 문구 `"링크를 찾을 수 없습니다."`가 `api.py`에 리터럴로 있다. 다른 문구처럼 `MSG_*` 상수로 옮기면 좋다.
- **R-4** `record_click`의 `UPDATE ... RETURNING`은 SQLite 3.35 이상이 필요하다. 이 환경은 3.49 이상이라 문제없지만 요구 사항이 문서화되어 있지 않다.
- **R-5** `init_schema`의 예외 처리 `ROLLBACK`이, SQLite가 이미 트랜잭션을 되돌린 경우(디스크 가득 참 등) "no transaction is active"로 실패해 원래 예외를 가릴 수 있다. `if conn.in_transaction:`으로 감싸면 된다.
- **R-6** 동시 마이그레이션 테스트가 `join(timeout=30)` 뒤 살아 있는 스레드를 확인하지 않아, 멈춘 스레드가 있어도 통과할 수 있다.
- **S-2** 예약어가 설계서의 9개뿐이라 `login`, `health`, `favicon` 같은 별칭을 만들 수 있다(피싱처럼 보이는 경로, F3 경로와의 충돌). F3에서 예약어 확장과 기존 별칭 확인 절차 검토.
- **S-3** 대소문자만 다른 별칭(`Team-Docs` / `team-docs`)으로 흉내 낼 수 있다. 설계서 AC-8이 정한 동작이라 위험 수용으로 기록.
- **S-4** 코드만 알면 누구나 통계(원래 URL, 클릭 수, 마지막 접근 시각)를 볼 수 있다. F3 인증 범위.
- **S-5** 리다이렉트마다 쓰기 트랜잭션이 생겨, 요청이 몰리면 `database is locked` 500과 클릭 부풀리기가 가능하다. F3 요청 수 제한 범위. 당장은 `record_click` 실패 시 리다이렉트를 계속하는 방어, WAL 모드를 검토할 수 있다.

참고 (지적 아님):

- 이제 `create_app()`은 마이그레이션이 필요 없을 때도 시작할 때 짧게 쓰기 잠금을 잡는다(security 2라운드 참고 사항).
- 이 환경에서는 응용 프로그램 제어 정책(os error 4551)이 `pytest.exe`, `bandit.exe`를 막아 `uv run python -m pytest`, `uv run python -m bandit`으로 실행했다.

## 4. 설계서 해석 결정

계획서 5절에 기록. D-F2-1~D-F2-9는 H1에서 사람이 승인했다. 테스트 루프에서 spec_ambiguous(H2)는 없었다. F1 결정 D-1~D-11은 그대로 유지.

| # | 결정 |
|---|---|
| D-F2-1 | 폼에서 별칭 칸이 비어 있으면 별칭 없음 → 7자 무작위 코드 |
| D-F2-2 | API에서 `alias` 생략·`null`은 별칭 없음, `""`은 길이 규칙 위반 422 |
| D-F2-3 | 별칭은 입력 그대로 검사 (앞뒤 공백 제거·소문자 변환 없음) |
| D-F2-4 | 예약어는 대소문자 무시로 비교 (`Admin`, `STATS`도 422) |
| D-F2-5 | 검사 순서: URL 검증 → 별칭 검증 → 중복(409). 둘 다 틀리면 URL 문구 하나만 |
| D-F2-6 | 통계 API 404 본문은 `{"detail": "링크를 찾을 수 없습니다."}` JSON |
| D-F2-7 | `last_accessed_at`은 `created_at`과 같은 형식, 화면에는 `2026-10-29 01:23:45 UTC`로 표시하고 `<time datetime>`으로 감쌈 |
| D-F2-8 | 클릭 수는 SQL `clicks = clicks + 1` 한 문장으로 원자적 증가, HEAD는 따로 처리하지 않음 |
| D-F2-9 | 통계 화면의 단축 URL을 눌러 이동하면 그 클릭도 센다 |

그 밖의 구현 결정: 클릭 수는 천 단위 쉼표로 표시(`1,284회`), 홈 폼 오류 문구 id를 `url-error`에서 `form-error`로 바꾸고 문제가 된 칸에만 `aria-invalid`, F1 DB는 `PRAGMA table_info`로 없는 컬럼만 `ALTER TABLE ADD COLUMN`(M-1 수정 후 `BEGIN IMMEDIATE` 트랜잭션 안에서).

## 5. 종료 상태

**완료.** AC-1~AC-23 모두 테스트(406개 통과, F1 테스트 포함)와 qa 블랙박스 검증으로 확인했다. 리뷰·QA 확인 항목인 F1 DB 호환(기존 링크 리다이렉트, 클릭 수 0부터)도 qa가 서버를 띄워 확인했고, 여러 워커·서버 동시 시작도 정상이다. blocker/major 미해결 없음.

## 6. 결과 확인 방법

1. 테스트 실행

   ```bash
   uv run python -m pytest -q
   ```

   (`uv run pytest`가 실행 정책으로 막히지 않는 환경이면 그것을 써도 된다.) 406개가 통과해야 한다.

2. 서버 실행 (저장소 루트에서)

   ```bash
   uv run uvicorn shortlink.main:create_app --factory
   ```

   기본 DB는 `shortlink.db`, 기본 주소는 `http://localhost:8000`. F1 때 쓰던 `shortlink.db`가 있으면 그대로 써도 된다(시작할 때 새 컬럼이 추가되고 기존 링크는 클릭 수 0부터 센다).

3. 브라우저로 확인할 순서 (목업 `docs/plans/mockups/F2-index.html`과 비교)
   1. `http://localhost:8000/` — 홈 화면에 "줄일 URL"과 "별칭 (선택)" 칸, 안내 문구, "줄이기" 버튼이 세로로 있다.
   2. URL `https://example.com/spring`, 별칭 `spring-sale`로 "줄이기" — 결과 화면의 단축 URL이 `http://localhost:8000/spring-sale`이고, "통계 보기"와 "다른 URL 줄이기" 링크가 있다.
   3. "통계 보기" 클릭 — `/stats/spring-sale` 통계 화면: 클릭 수 `0회`, 마지막 접근 "아직 없음".
   4. 새 탭에서 `http://localhost:8000/spring-sale`을 세 번 열어 `https://example.com/spring`으로 이동하는지 확인한 뒤, 통계 화면을 새로고침 — `3회`, 마지막 접근 시각이 `YYYY-MM-DD HH:MM:SS UTC`로 보인다. 새로고침을 여러 번 해도 클릭 수는 그대로다.
   5. 홈에서 같은 별칭 `spring-sale`로 다시 제출 — 409 화면에 "이미 사용 중인 별칭입니다. 다른 별칭을 입력해 주세요."가 보이고 URL과 별칭이 입력칸에 남는다.
   6. 별칭 `my_link`로 제출 — "별칭에는 영문, 숫자, 하이픈(-)만 쓸 수 있습니다." (422). `abc`는 길이 문구, `admin`은 예약어 문구.
   7. 별칭 칸을 비우고 제출 — 7자 무작위 코드가 만들어진다(F1과 같음).
   8. `http://localhost:8000/stats/zzzzzzz` — "링크를 찾을 수 없습니다" 404 화면.
   9. 개발자 도구에서 폭 375px로 바꿔 홈·통계 화면에 가로 스크롤이 없는지 확인.

4. API 확인 (`http://localhost:8000/docs`에서도 가능)

   ```bash
   curl -s -i -X POST -H "Content-Type: application/json" -d "{\"url\": \"https://example.com\", \"alias\": \"my-link\"}" http://localhost:8000/links
   ```

   201과 `"code": "my-link"`, `"short_url": "http://localhost:8000/my-link"`. 같은 요청을 다시 보내면 409.

   ```bash
   curl -s http://localhost:8000/links/my-link/stats
   ```

   `clicks`, `created_at`, `last_accessed_at`(접근 전 `null`)이 온다. `curl -s -o /dev/null http://localhost:8000/my-link` 뒤 다시 조회하면 `clicks`가 1 늘어 있다.
