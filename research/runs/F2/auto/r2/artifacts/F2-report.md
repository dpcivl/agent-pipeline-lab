# F2 실행 보고서 — 클릭 통계와 커스텀 별칭

- 모드: auto (사람 개입 지점 H1~H4를 메인 세션이 스스로 처리)
- 브랜치: `run/F2-auto-r2`
- 종료 상태: **완료**
- 설계서: `docs/features/F2.md` (v1), 계획: `docs/plans/F2-plan.md`, 결정 기록: `docs/plans/F2-decisions.md`, 목업: `docs/plans/mockups/F2-index.html`

## 1. 단계별 진행 기록

| 단계 | 내용 | 호출한 에이전트 | 결과 |
|---|---|---|---|
| 0 | 실행 위치 확인 | (메인) | `RUN_WORKTREE` |
| 1 | 계획, 스켈레톤(`validation`, `repository`, `api`, `web`, `db` 스텁과 docstring), 목업 6개 + 목록 | (메인) | H1: auto 자체 승인 |
| 2 | 구현과 테스트 작성 (병렬) | implementer, test-writer | 둘 다 완료 |
| 3 | 테스트 루프 | tester | 1회차 PASS (394개, 동시성 테스트 10회 반복 모두 통과) |
| 4-1 | 리뷰 1라운드 | reviewer, qa, security (병렬) | blocker 0, major 0, minor 10 (통합 후) → 루프 종료 |
| 4-1 | H3 | (메인, auto) | 고칠 항목 없음. R-1은 결정 D-12로 기록 |
| 5 | H4 커밋 전 확인 | (메인, auto) | 바로 진행 |
| 6 | 실행 보고서 | (메인) | 이 문서 |
| 7 | 문서와 기능 커밋 | doc-keeper | 기능 커밋 |

### 체크포인트 커밋

| 해시 | 메시지 | 비고 |
|---|---|---|
| `8bad8e8` | wip(F2): 1 계획, 스켈레톤, 목업 | |
| `b42b3bb` | wip(F2): 2 구현과 테스트 작성 | 리뷰 1라운드 체크포인트 |

테스트 루프와 리뷰 루프에서 수정이 없었으므로 `3 …`, `4 …` 체크포인트는 없다.

## 2. 루프 횟수와 지적 수

- 테스트 루프: 1회 (첫 실행 PASS, 394개 = F1 175개 + F2 219개)
- 리뷰 라운드: 1라운드

| 라운드 | 에이전트 | blocker | major | minor |
|---|---|---|---|---|
| 1 | reviewer | 0 | 0 | 4 (R-1~R-4) |
| 1 | qa | 0 | 0 | 0 (AC-1~AC-23, F1 DB 호환성 모두 PASS) |
| 1 | security | 0 | 0 | 7 (S-1~S-7) |
| 1 | **통합** | **0** | **0** | **10** (R-3 = S-4 중복 합침) |

## 3. 미해결 지적과 minor 지적 (모두 기록만, 고치지 않음)

미해결(blocker/major) 지적은 없다.

| id | 내용 | 비고 |
|---|---|---|
| R-1 | 문자열이 아닌 `alias`(숫자 등)의 422 본문이 FastAPI 기본 형식이라 계획 3.3·목업 문구표("alias는 문자열이어야 합니다.")와 어긋남 | 결정 D-12로 현재 동작(F1 `url`과 같은 규칙)을 확정. 목업 목록의 해당 행은 `validate_alias` 단독 호출 기준으로 읽는다 |
| R-2 | 동시 리다이렉트에서 `last_accessed_at`이 최대 1초 이른 값으로 덮어써질 수 있음 (시각을 잠금 밖에서 계산). 클릭 수는 정확함 | `MAX(COALESCE(...), ?)`나 SQL `strftime('now')`로 고칠 수 있음 |
| R-3 / S-4 | `init_schema`의 열 확인과 `ALTER TABLE`이 원자적이지 않아, F1 DB로 여러 워커를 동시에 띄우면 한 워커가 `duplicate column name`으로 시작 실패할 수 있음 | 단일 프로세스 기본 실행에는 영향 없음. 재시작하면 정상. `BEGIN IMMEDIATE`나 중복 열 오류 무시로 해결 가능 |
| R-4 | `web.py`의 `follow_link`와 모듈 docstring이 F2 동작(클릭 집계, F2 목업)을 반영하지 않음 | 문서성 |
| S-1 | 리다이렉트 반복으로 클릭 수 부풀리기, 별칭 대량 선점 가능 | F3 요청 수 제한 범위 |
| S-2 | 통계가 코드만 알면 누구에게나 공개됨. 추측하기 쉬운 별칭은 사용 패턴이 드러남 | F3 인증·소유자 범위 |
| S-3 | 리다이렉트가 DB 쓰기에 묶여 잠금 경합·읽기 전용 DB에서 500 가능 | 쓰기 실패 시 `get()`으로 폴백, WAL·busy_timeout 검토 |
| S-5 | bandit B608 2건 (`f"SELECT {self._COLUMNS} ..."`, 클래스 상수라 오탐) | 고정 리터럴 쿼리로 정리 권장 |
| S-6 | 예약어 목록이 F3에서 생길 한 단계 경로(`login`, `logout`, `health`, `keys` 등)를 미리 막지 않음 | F3 계획에서 예약어 확장과 라우트 등록 순서 규칙을 정해야 함 |
| S-7 | 대소문자만 다르거나 생김새가 비슷한 별칭으로 사칭 가능 | AC-8에 따른 설계상 수용. F3에서 검토 |

## 4. 설계서 해석 결정

계획 5절 (D-1~D-11)과 결정 기록 (D-12~D-13) 요약:

| # | 결정 |
|---|---|
| D-1 | API: `alias` 없음·`null` = 별칭 없음, `""`는 422. 폼: 빈 입력칸 = 별칭 없음 |
| D-2 | 검사 순서: URL → 별칭(길이 → 문자 → 하이픈 → 예약어). 오류 문구는 하나만 |
| D-3 | 별칭 공백은 제거하지 않고 422 (정규화 없음) |
| D-4 | 예약어는 대소문자 무시 (`Admin`, `LINKS`도 422) |
| D-5 | `openapi.json`은 목록에 두지만 문자 규칙에서 먼저 걸림 |
| D-6 | 별칭이 기존 무작위 코드와 같아도 409 |
| D-7 | 통계 API 404 본문은 JSON `{"detail": "링크를 찾을 수 없습니다."}` |
| D-8 | 통계 화면 시각은 `YYYY-MM-DD HH:MM:SS UTC`, `<time datetime>`에 ISO 원문 |
| D-9 | 302 응답마다 클릭 1. 봇·중복 방문 구분 없음 |
| D-10 | `last_accessed_at`은 `created_at`과 같은 형식 |
| D-11 | 앱 시작 시 `ALTER TABLE ADD COLUMN`으로 F1 DB 자동 이전, 기존 링크 클릭 0부터 |
| D-12 | 문자열이 아닌 `alias`는 F1 `url`과 같이 FastAPI 기본 422 본문 |
| D-13 | 리뷰 1라운드 blocker·major 0 → 루프 종료, minor는 기록만 |

## 5. 종료 상태

**완료.** 테스트 394개 통과, ruff check·format 통과, QA가 실제 서버로 AC-1~AC-23과 F1 DB 호환성을 모두 PASS로 확인. blocker와 major 지적 없음.

## 6. 결과 확인 방법

1. 서버 실행 (저장소 루트에서):

   ```bash
   uv run uvicorn shortlink.main:create_app --factory
   ```

   기본 DB는 `shortlink.db`, 기본 주소는 `http://localhost:8000`이다. 다른 DB를 쓰려면 `SHORTLINK_DB_PATH`를 지정한다.

2. 브라우저로 확인할 순서:
   1. `http://localhost:8000/` — 홈 화면에 "줄일 URL"과 "별칭 (선택)" 입력칸이 있는지 본다.
   2. URL `https://example.com`, 별칭 `my-link`로 "줄이기" → 결과 화면의 단축 URL이 `http://localhost:8000/my-link`이고 "통계 보기" 링크가 있는지 본다.
   3. "통계 보기" (`http://localhost:8000/stats/my-link`) → 클릭 수 0, 마지막 접근 시각 "아직 없음".
   4. 새 탭에서 `http://localhost:8000/my-link`를 2~3번 연다 (example.com으로 이동) → 통계 화면을 새로 고치면 클릭 수가 늘고 마지막 접근 시각이 채워진다.
   5. 홈에서 같은 별칭 `my-link`로 다시 제출 → 409 화면에 "이미 쓰이는 별칭입니다. 다른 별칭을 입력해 주세요."와 입력값이 남아 있다.
   6. 별칭 `my link`(공백) 또는 `ab` 제출 → 422 화면과 규칙 오류 문구.
   7. `http://localhost:8000/stats/nothing-here` → 404 "링크를 찾을 수 없습니다" 화면.

3. API 확인:

   ```bash
   curl -s -X POST http://localhost:8000/links -H "Content-Type: application/json" -d "{\"url\": \"https://example.com\", \"alias\": \"api-link\"}"
   ```

   ```bash
   curl -s http://localhost:8000/links/api-link/stats
   ```

4. 화면 기준 목업: `docs/plans/mockups/F2-index.html`을 브라우저로 열어 실제 화면과 비교한다.
5. 테스트: `uv run pytest` (394개).
