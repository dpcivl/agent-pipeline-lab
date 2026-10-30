---
seq: 13
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-30T00:48:58.713Z"
agent: "reviewer"
agent_id: "ae10abacb60ba5f81"
turn: 1
reply_to: 9
chars: 5239
tokens_est: 2455
wait_s: null
---

## 결과: 지적 6건 (blocker 0, major 0, minor 6)

검토 범위는 `git diff 0b748cc 16fdb28` 전체입니다. src, templates, CSS, tests, docs/plans, mockups를 봤습니다. 파일은 수정하지 않았고, Bash는 git과 grep, awk 같은 읽기 명령에만 썼습니다.

총평: 계획 3절의 인터페이스와 D2-1~D2-9가 그대로 구현돼 있습니다. 템플릿 4개는 목업 F2-home, F2-error-alias, F2-error-duplicate, F2-result, F2-stats, F2-stats-empty와 마크업 구조, 클래스, 문구, aria 속성까지 맞습니다. style.css의 F2 블록은 목업 블록과 글자까지 같고, F1 공통 스타일은 바뀌지 않았습니다. F1 테스트 파일은 test_repository.py에 추가만 있고 기존 테스트는 고치지 않았습니다. 고정 계약(`create_app`, `Settings`, conftest 픽스처)도 그대로입니다.

정확성에서 확인한 것:
- 별칭 INSERT의 IntegrityError는 `with conn` 안에서 롤백된 뒤 409로 바뀝니다.
- `record_click`은 SQL 안에서 증가시키고, UPDATE와 SELECT가 한 트랜잭션에서 돕니다.
- F1 DB 마이그레이션은 열마다 따로 검사합니다. `NOT NULL DEFAULT 0` ADD COLUMN은 SQLite에서 허용됩니다.
- 404 경로에서는 clicks가 바뀌지 않습니다.

blocker와 major는 찾지 못했습니다.

## 지적 목록

### R-1 [minor] 리다이렉트가 매번(404 포함) 쓰기 트랜잭션이 되어 잠금 경합으로 500이 날 수 있음
- 위치: src/shortlink/web.py:173, src/shortlink/repository.py:114-131, src/shortlink/db.py:22-24
- 문제: F1에서 `GET /{code}`는 읽기만 했습니다. 이제 모든 요청이 `UPDATE`를 실행합니다. 없는 코드라 갱신되는 행이 0개여도 UPDATE 문은 RESERVED 잠금을 잡습니다. 그래서 봇이 404 경로를 훑는 요청도 쓰기 잠금을 다툽니다. `connect()`는 기본 rollback journal 모드에 기본 busy timeout 5초인 `sqlite3.connect`만 부릅니다. 동시 요청이 많으면 `sqlite3.OperationalError: database is locked`가 핵심 경로인 리다이렉트를 500으로 만들 수 있고, 이건 F1에 없던 실패 방식입니다.
- 근거: 계획 3.3 "`GET /{code}`는 `repository.record_click(code)`로 바꾼다"는 따랐습니다. 다만 계획이 동시성에서 요구한 것은 "수가 빠지지 않게"뿐이고, 잠금 실패는 다루지 않았습니다.
- 수정 제안: 다음 중 하나를 고르면 됩니다. 결정은 계획에 기록해 주세요.
  - `init_schema()`에서 `PRAGMA journal_mode=WAL`을 켜고, `connect()`에 `timeout`을 명시합니다. WAL로 바꾸면 F1 DB 파일 옆에 -wal과 -shm 파일이 생기니 문서에 적어야 합니다.
  - 지금 방식을 받아들이고, 계획 5절에 "부하 시 잠금 대기 가능"을 결정으로 남깁니다.

### R-2 [minor] F1 DB 마이그레이션이 여러 프로세스가 동시에 시작할 때 실패할 수 있음
- 위치: src/shortlink/db.py:45-55
- 문제: `PRAGMA table_info` 확인과 `ALTER TABLE` 사이에 잠금이 없습니다. 파이썬 sqlite3는 DDL 앞에 암묵적 BEGIN을 걸지 않아서 문장마다 자동 커밋됩니다. `uvicorn --workers N`처럼 여러 프로세스가 동시에 F1 DB로 `create_app`을 부르면 두 프로세스가 모두 "열 없음"을 보고 ALTER를 실행합니다. 늦은 쪽은 `duplicate column name: clicks`로 시작에 실패합니다. 새 DB의 `CREATE TABLE IF NOT EXISTS`는 이 문제가 없고, 처음 마이그레이션할 때 한 번만 생기는 경합입니다.
- 근거: 계획 3.2는 "여러 번 불러도 안전해야 한다"라고 합니다. 순차 호출은 테스트로 확인돼 있지만 동시 호출은 아닙니다.
- 수정 제안: `ensure_click_columns` 앞뒤를 `BEGIN IMMEDIATE ... COMMIT`으로 감싸 확인과 변경을 한 쓰기 트랜잭션에 넣습니다. 또는 `OperationalError`가 "duplicate column name"이면 무시합니다.

### R-3 [minor] 목업 색인의 "문자열이 아님" 행이 실제 API 동작과 다름
- 위치: docs/plans/mockups/F2-index.html:47, src/shortlink/api.py:30, src/shortlink/validation.py:89,123
- 문제: 목업 색인에는 "문자열이 아님 (API에서만 발생) 422 — alias는 문자열이어야 합니다."라고 적혀 있습니다. 하지만 `LinkIn.alias: StrictStr | None` 때문에 숫자 같은 비문자열 alias는 FastAPI 기본 422 본문(`detail`이 목록)을 받습니다. 그래서 `MSG_ALIAS_NOT_STRING`은 API에서도 화면에서도 실제로 나오지 않습니다. 화면 폼 값은 항상 문자열입니다.
- 근거: 계획 3.3에 "숫자 같은 비문자열 `alias`는 FastAPI 기본 422"라고 적혀 있고, 구현은 계획을 따랐습니다. F1의 `url`과도 같은 방식입니다. 문서 두 곳이 서로 어긋난 상태입니다.
- 수정 제안: 목업 색인의 해당 행을 "API에서 FastAPI 기본 422(본문 형식 다름)"로 고칩니다. 또는 그 행을 빼고 상수는 단위 검증용이라고 주석을 답니다. 코드 변경은 필요 없습니다.

### R-4 [minor] 같은 문구와 같은 변환이 여러 곳에 흩어져 있음
- 위치: src/shortlink/api.py:95,101, src/shortlink/api.py:108-110, src/shortlink/web.py:156-157
- 문제:
  - 통계 API 404 문구 `"링크를 찾을 수 없습니다."`가 리터럴로 들어가 있습니다. not_found.html 제목과 같은 뜻인데 상수가 아닙니다.
  - "None이면 None, 아니면 format_timestamp" 변환을 api.py와 web.py가 각자 씁니다. 그런데 조건식이 api.py는 `is not None`, web.py는 truthiness로 서로 다릅니다.
- 근거: 다른 문구(`MSG_ALIAS_TAKEN` 등)는 validation.py에 상수로 모으는 것이 계획 3.1의 방식입니다.
- 수정 제안: `MSG_LINK_NOT_FOUND` 상수를 만들고, repository.py에 `format_optional_timestamp(value: datetime | None) -> str | None` 같은 도우미를 하나 두어 두 곳이 같이 쓰게 합니다.

### R-5 [minor] 테스트 빈틈
- 위치: tests/test_migration.py 전체, tests/test_aliases.py:226-229
- 문제:
  1. 열이 일부만 있는 DB(`clicks`만 있고 `last_accessed_at`은 없음)는 테스트하지 않습니다. `ensure_click_columns`가 열마다 따로 검사하는 분기 중 하나만 지나갑니다. 중간에 실패했다가 다시 시작하는 경우가 바로 이 상태입니다.
  2. `test_reserved_alias_still_serves_the_real_route`의 docstring은 "/docs, /links 경로가 그대로 동작"이라고 하지만, 실제로는 `/docs`와 `/openapi.json`만 확인합니다.
- 근거: 계획 4절 보조 테스트 "`init_schema` 두 번 호출 안전"과 D2-9 "없는 열만 ADD COLUMN"입니다.
- 수정 제안:
  1. F1 스키마에 `clicks` 열만 미리 추가하고 값을 넣은 DB를 만듭니다. `create_app` 뒤 그 값이 유지되고 `last_accessed_at`이 NULL인지 확인하는 테스트를 추가합니다.
  2. docstring을 실제 확인 내용에 맞추거나, `POST /links`가 계속 201인지 확인하는 단언을 넣습니다.

### R-6 [minor] OpenAPI 문서에 409와 404 응답이 선언되지 않음
- 위치: src/shortlink/api.py:49, src/shortlink/api.py:89
- 문제: `POST /links`의 409와 `GET /links/{code}/stats`의 404가 `responses=`에 없습니다. 그래서 /docs 화면에는 201(또는 200)과 422만 보입니다. 동작은 맞습니다.
- 근거: 설계서와 계획이 409와 404를 API 계약으로 정했습니다. 같은 서비스가 `/docs`를 공개합니다.
- 수정 제안: `responses={409: {"description": ..., "content": ...}}`와 404 선언을 추가합니다. 필요하면 `{"detail": str}` 모델도 만듭니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)

참고 파일:
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\src\shortlink\db.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\src\shortlink\repository.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\src\shortlink\api.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\src\shortlink\web.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\docs\plans\mockups\F2-index.html
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\tests\test_migration.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\tests\test_aliases.py
