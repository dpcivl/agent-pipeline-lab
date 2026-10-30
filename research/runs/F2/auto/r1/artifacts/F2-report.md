# F2 실행 보고서 — 클릭 통계와 커스텀 별칭

- 설계서: `docs/features/F2.md` (v1)
- 실행 모드: auto
- 브랜치: `run/F2-auto-r1` (기준 커밋 `4cf5823`)
- 종료 상태: **완료**

## 1. 단계별 진행 기록

| 단계 | 내용 | 호출한 에이전트 | 결과 |
|---|---|---|---|
| 0 | 실행 위치 확인 | — | `RUN_WORKTREE` |
| 1 | 계획(`F2-plan.md`), 해석 결정(`F2-decisions.md`), 스켈레톤 스텁, 목업 7개 | 메인 직접 | 스텁 상태에서 F1 테스트 175개 통과. H1(auto)은 스스로 승인 |
| 2 | 구현과 테스트 작성 (병렬) | implementer, test-writer | 구현 완료. 새 테스트 277개 작성(전체 452개) |
| 3 | 테스트 루프 1회차 | tester | PASS (452 통과). 전체 스위트를 3번 반복했고 간헐 실패 없음 |
| 4 | 리뷰 1라운드 (병렬) | reviewer, qa, security | blocker 0, major 0, minor 6. 루프 종료 |
| 5 | 커밋 전 확인 | — | H4(auto)라 바로 진행 |
| 6 | 실행 보고서 | 메인 직접 | 이 문서 |
| 7 | 문서와 기능 커밋 | doc-keeper | `docs/service.md`, `CHANGELOG.md` 갱신, 기능 커밋 |

### 체크포인트 커밋

| 해시 | 메시지 |
|---|---|
| `a4d9c71` | wip(F2): 1 계획, 스켈레톤, 목업 |
| `34689f1` | wip(F2): 2 구현과 테스트 작성 (리뷰 1라운드 체크포인트) |

테스트 루프와 리뷰 라운드에서 수정이 없었으므로 3·4단계 체크포인트 커밋은 없습니다.

## 2. 루프 횟수와 지적 수

- 테스트 루프: 1회 (첫 실행에서 PASS)
- 리뷰 라운드: 1라운드

| 라운드 | blocker | major | minor | 출처 |
|---|---|---|---|---|
| 1 | 0 | 0 | 6 | reviewer 3, qa 1, security 2 |

## 3. 미해결 지적

없음 (blocker·major 0건).

## 4. minor 지적 (고치지 않고 기록만 함)

| id | 내용 | 메모 |
|---|---|---|
| Q-1 | `alias`가 문자열이 아닐 때(`123`, `true`, 배열) 422 본문이 `{"detail": "alias는 문자열이어야 합니다."}`가 아니라 FastAPI 기본 형식이다 | 계획 3.3절에 정한 동작. F1에서 `url`이 문자열이 아닐 때와 같은 방식이다. `MSG_ALIAS_NOT_STRING`은 `validate_alias` 단위 호출에서만 쓴다 |
| R-1 | `migrate_schema`의 열 확인(PRAGMA)과 추가(ALTER)가 한 트랜잭션이 아니다. 여러 프로세스가 F1 DB로 동시에 처음 시작하면 한쪽이 `duplicate column name`으로 시작에 실패할 수 있다 | 다시 시작하면 정상이고 데이터 손상은 없다. `BEGIN IMMEDIATE`로 묶거나 duplicate column 오류를 무시하면 고칠 수 있다 |
| R-2 | `db.init_schema` docstring에 스텁 단계의 작업 지시 문장 "(F2: the CREATE TABLE statement must include the new columns.)"이 남아 있다 | 문서 정리 |
| R-3 | `tests/test_stats_api.py`의 HTTP 동시성 테스트가 스레드 안에서 난 예외를 모으지 않는다. 실패할 때 원인을 진단하기 어렵다 | 결과 판정은 정확하다 |
| S-1 | 예약어가 설계서의 9개뿐이라 F3에서 생길 한 단계 경로(`login`, `health` 등)를 미리 막지 않는다 | F3 설계 때 예약어 확장과 "고정 라우트는 `/{code}`보다 먼저 등록" 테스트를 검토한다 |
| S-2 | F2부터 `GET /{code}`가 DB 쓰기를 한다. 요청 수 제한이 없어 클릭을 부풀릴 수 있고, 대량 요청이 오면 쓰기 잠금 경합이 생길 수 있다 | 요청 수 제한은 F3 범위. WAL 모드, 없는 코드는 UPDATE하지 않기 같은 완화책을 F3 위험 목록에 넣는다. 클릭 수는 중복을 제거하지 않은 값이다 |

## 5. 설계서 해석 결정

`docs/plans/F2-decisions.md`의 E-1~E-14를 1단계에서 정했습니다. 테스트 루프에서 spec_ambiguous는 없었으므로 이후 추가된 결정은 없습니다.

- E-1 별칭 검사 순서(문자열 → 길이 → 문자 → 하이픈 양끝 → 예약어), 처음 걸린 문구 하나만 표시
- E-2 예약어는 대소문자를 무시하고 비교 (`Admin`도 422)
- E-3 API: `alias`가 없거나 `null`이면 무작위 코드, `""`이면 422
- E-4 폼: 빈 별칭은 "주지 않음"
- E-5 별칭 앞뒤 공백을 잘라 내지 않고 422
- E-6 URL과 별칭이 둘 다 틀리면 URL 오류만 표시하고 입력값은 둘 다 유지
- E-7 무작위로 만든 기존 코드와 같은 별칭도 409, 대소문자 구분
- E-8 409 본문 `{"detail": "이미 쓰이는 별칭입니다. 다른 별칭을 입력해 주세요."}`
- E-9 통계 API의 404는 JSON `{"detail": "링크를 찾을 수 없습니다."}`
- E-10 클릭 증가는 UPDATE 한 문장으로 원자적으로 처리
- E-11 F1 DB는 시작할 때 `ALTER TABLE ADD COLUMN`으로 자동 이전 (기존 링크 clicks 0)
- E-12 통계 화면의 시각은 API와 같은 문자열을 `<time>`에 표시
- E-13 통계는 코드를 아는 사람 누구나 볼 수 있음 (인증은 F3)
- E-14 "통계 보기"는 상대 경로 `/stats/{code}`

## 6. 종료 상태

**완료.** F2 수용 기준 AC-1~AC-22는 테스트와 QA 블랙박스 검증을 모두 통과했습니다. AC-23(F1 회귀)은 기존 F1 테스트 175개를 수정 없이 통과했고, QA도 회귀를 확인했습니다. F1 DB 호환성(F1 스키마 파일로 시작, 기존 링크 리다이렉트, 클릭 수 0부터)은 QA와 `tests/test_migration.py`로 확인했습니다.

## 7. 결과 확인 방법

1. 테스트 실행 (452개 통과가 기대값):
   ```bash
   uv run pytest
   ```
   애플리케이션 제어 정책 때문에 `pytest` 실행이 막히면 `uv run python -m pytest`를 씁니다.
2. 서버 실행 (저장소 루트):
   ```bash
   uv run uvicorn shortlink.main:create_app --factory
   ```
3. 브라우저로 다음 순서대로 확인합니다.
   1. `http://localhost:8000/`: 홈 화면에 "줄일 URL"과 "별칭 (선택)" 입력칸이 있습니다.
   2. URL `https://example.com`, 별칭 `my-link`로 "줄이기"를 누릅니다. 결과 화면에 `http://localhost:8000/my-link`와 "통계 보기" 링크가 나옵니다.
   3. 같은 별칭으로 한 번 더 제출하면 409 화면에 "이미 쓰이는 별칭입니다. 다른 별칭을 입력해 주세요."가 나오고, 입력값이 남아 있습니다.
   4. 별칭 `my_link`를 제출하면 422 화면에 "별칭에는 영문, 숫자, 하이픈(-)만 쓸 수 있습니다."가 나옵니다.
   5. "통계 보기"(`http://localhost:8000/stats/my-link`)를 엽니다. 클릭 수는 0이고, 마지막 접근 시각은 "아직 없음"입니다.
   6. `http://localhost:8000/my-link`를 2~3번 연 뒤 통계 화면을 새로 고칩니다. 클릭 수와 마지막 접근 시각이 갱신됩니다.
   7. `http://localhost:8000/stats/nope1234`를 열면 404 "링크를 찾을 수 없습니다" 화면이 나옵니다.
4. API 확인:
   ```bash
   curl -s -i -X POST -H "Content-Type: application/json" -d '{"url": "https://example.com", "alias": "api-demo"}' http://localhost:8000/links
   ```
   ```bash
   curl -s http://localhost:8000/links/api-demo/stats
   ```
5. 목업과 비교: `docs/plans/mockups/F2-index.html`을 브라우저로 엽니다.
