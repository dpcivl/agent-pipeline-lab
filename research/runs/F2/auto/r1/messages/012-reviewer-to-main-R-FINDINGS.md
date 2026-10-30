---
seq: 12
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T07:21:33.688Z"
agent: "reviewer"
agent_id: "a4b43659dbe0207c9"
turn: 1
reply_to: 8
chars: 3755
tokens_est: 1770
wait_s: null
---

## 결과: 지적 3건 (blocker 0, major 0, minor 3)

검토 범위는 `git diff 4cf5823..34689f1` 전체입니다. 소스 6개, 템플릿 3개, style.css, conftest와 테스트 7개를 봤습니다. 읽기 전용 명령인 `ruff check --no-cache`와 `ruff format --check --no-cache`도 돌렸고 둘 다 통과했습니다. 작업 트리는 바꾸지 않았습니다.

요청하신 중점 항목은 모두 문제가 없습니다.
- **migrate_schema 정확성**: `PRAGMA table_info`로 빠진 열만 `ALTER TABLE ADD COLUMN`합니다. 기존 행은 `clicks`가 0, `last_accessed_at`이 NULL이 되고, 여러 번 불러도 안전합니다(E-11). test_migration.py가 F1 파일로 앱 시작, 302, clicks 0부터 세기, 재시작 후 값 유지, 한 열만 빠진 경우까지 확인합니다.
- **record_click**: `UPDATE ... SET clicks = clicks + 1` 한 문장으로 늘리고, 같은 연결과 같은 트랜잭션 안에서 SELECT로 다시 읽습니다. `rowcount == 0`이면 None을 돌려주고 아무것도 늘리지 않습니다(E-10). 첫 문장이 쓰기라서 SQLite busy handler가 동작하므로 deferred 트랜잭션에서도 교착이 생기지 않습니다.
- **별칭 검증**: 순서가 E-1과 같습니다. `re.fullmatch(r"[A-Za-z0-9-]+")`로 ASCII만 허용하므로 `"abcd\n"`, 전각 문자, 한글은 거절됩니다. 예약어는 `alias.lower()`로 비교해 대소문자를 무시하고(E-2), 공백을 잘라 내지 않습니다(E-5).
- **409 시 저장 없음**: 별칭은 재시도 없이 한 번만 INSERT하고, `IntegrityError`가 나면 `AliasConflictError`로 바꿉니다. 트랜잭션은 롤백됩니다. API와 화면 모두 URL을 먼저 검사하고(E-6), 빈 문자열과 null 처리도 E-3, E-4와 맞습니다.
- **고정 계약**: main.py와 config.py는 바뀌지 않았습니다. conftest.py는 `read_clicks`, `total_clicks`, `create_f1_database`를 끝에 추가만 했습니다. 기존 F1 테스트는 test_repository.py에 import 한 줄을 고치고 테스트를 덧붙인 것 말고는 바뀌지 않았습니다.
- **목업 일치**: home, error-alias, error-conflict, result, stats, stats-new 화면의 구조, 문구, 클래스, id, aria 속성이 목업과 같습니다. style.css는 목업의 공통 스타일 블록에서 주석 두 줄만 뺀 것과 같습니다.
- **수용 기준 대응**: AC-1~AC-22에 모두 대응하는 테스트가 있고 경계값 테스트도 충분합니다.

## 지적 목록

### R-1 [minor] migrate_schema의 "열 확인 후 추가"가 한 트랜잭션이 아님
- 위치: `src/shortlink/db.py:32-56` (`init_schema`, `migrate_schema`)
- 문제: Python sqlite3의 기본 설정(legacy isolation_level `""`)은 INSERT, UPDATE, DELETE, REPLACE 앞에서만 BEGIN을 자동으로 겁니다. 그래서 `with conn:` 안에 있어도 CREATE, PRAGMA, ALTER는 각각 따로 커밋되고, PRAGMA로 확인하는 것과 ALTER로 추가하는 것이 원자적이지 않습니다. 여러 프로세스가 같은 F1 DB 파일로 동시에 시작하면(예: `uvicorn --workers N`) 둘 다 열이 없다고 보고 ALTER를 실행합니다. 이때 뒤에 실행된 쪽은 `sqlite3.OperationalError: duplicate column name: clicks`로 시작에 실패합니다. 다시 시작하면 정상이 되므로 데이터가 손상되지는 않습니다.
- 근거: docstring의 "The caller owns the connection and the transaction"과 `init_schema`의 주석 "`with conn` commits the transaction"이 실제 동작과 다릅니다.
- 수정 제안: 둘 중 하나로 고칩니다.
  1. `migrate_schema` 시작에서 `conn.execute("BEGIN IMMEDIATE")`를 실행해 PRAGMA와 ALTER를 한 쓰기 트랜잭션으로 묶습니다.
  2. ALTER에서 난 `OperationalError`의 메시지가 "duplicate column name"이면 무시합니다.

  어느 쪽이든 docstring도 실제 동작에 맞게 고칩니다.

### R-2 [minor] init_schema docstring에 스텁 단계의 작업 지시 문장이 남아 있음
- 위치: `src/shortlink/db.py:29`
- 문제: 구현이 끝났는데 "(F2: the CREATE TABLE statement must include the new columns.)"라는 구현 지시 문장이 그대로 남아 있습니다.
- 근거: 계획 2절의 "`init_schema`는 구현 단계에서 수정" 메모를 지우지 않은 것입니다.
- 수정 제안: 해당 문장을 지우거나, 새 DB는 F2 스키마로 바로 만든다는 설명으로 바꿉니다.

### R-3 [minor] HTTP 동시성 테스트가 스레드 안에서 난 예외를 모으지 않음
- 위치: `tests/test_stats_api.py:350-372` (`test_concurrent_redirects_do_not_lose_clicks`)
- 문제: TestClient는 서버 쪽 예외(예: `sqlite3.OperationalError: database is locked`)를 호출한 쪽에서 다시 던집니다. worker가 `failures`에 넣는 것은 302가 아닌 상태 코드뿐이라서, 예외가 나면 그 스레드는 조용히 끝납니다. 그러면 pytest에는 경고(`PytestUnhandledThreadExceptionWarning`)만 남고, 테스트는 마지막 개수 비교에서 원인을 알 수 없는 메시지로 실패합니다. 개수 비교 덕분에 틀린 결과를 통과시키지는 않지만 실패 원인을 진단하기 어렵습니다. 그 밖의 안정성은 괜찮습니다. 스레드마다 별도 TestClient를 쓰고, 앱에 lifespan이 없고, 쓰기는 총 80건이라 기본 busy timeout 5초 안에서 충분합니다.
- 근거: 같은 목적의 `tests/test_repository.py:321-343`은 `errors` 리스트에 예외를 모아 `assert errors == []`로 확인합니다.
- 수정 제안: worker 본문을 `try/except Exception`으로 감싸고, 잡은 예외를 `failures`(또는 별도 `errors` 리스트)에 넣어 확인합니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)

관련 파일:
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r1\src\shortlink\db.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r1\tests\test_stats_api.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r1\tests\test_repository.py
