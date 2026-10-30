---
seq: 25
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-30T00:17:32.060Z"
agent: "reviewer"
agent_id: "a4da8d475ce801a88"
turn: 2
reply_to: 22
chars: 2861
tokens_est: 1295
wait_s: null
---

## 결과: 지적 2건 (blocker 0, major 0, minor 2)

M-1(R-3)과 R-1은 둘 다 해결됐습니다. `git diff e9f25fe..6b2d234` 변경분에서 새로 찾은 것은 minor 2건뿐이고 둘 다 엣지 케이스입니다. 이번 라운드에서 돌린 것은 `ruff check`와 `ruff format --check`(둘 다 통과), `tests/test_stats.py`(36개 통과)입니다. 전체 테스트는 다시 돌리지 않았습니다.

## 지적 목록

### R-5 [minor] 예외 처리의 `ROLLBACK`이 원래 예외를 가릴 수 있음
- 위치: `src/shortlink/db.py:59-61` (`except BaseException: conn.execute("ROLLBACK")`)
- 문제: SQLite는 일부 오류(SQLITE_FULL, SQLITE_IOERR, SQLITE_NOMEM 등)가 나면 트랜잭션을 스스로 롤백합니다. 그 뒤에 `ROLLBACK`을 또 실행하면 `OperationalError: cannot rollback - no transaction is active`가 납니다. 이 오류가 실제 원인(예: 디스크 가득 참)을 가려서, 원래 예외는 `__context__`에만 남습니다. 시작 실패를 진단하기가 어려워집니다.
- 근거: try 블록 안의 CREATE/PRAGMA/ALTER가 위 오류로 실패하는 경우입니다. 정상 경로와 동시 시작 경로에는 영향이 없습니다.
- 수정 제안: `if conn.in_transaction: conn.execute("ROLLBACK")`로 감쌉니다. 다른 방법으로, `closing()`이 연결을 닫을 때 미완료 트랜잭션이 자동으로 롤백된다는 점에 기대고 except 블록을 빼도 됩니다.

### R-6 [minor] 동시 마이그레이션 테스트가 끝나지 않은 스레드를 확인하지 않음
- 위치: `tests/test_stats.py` `_init_schema_concurrently()` (`thread.join(timeout=30)` 이후)
- 문제: `join(timeout=30)`이 시간 초과로 끝나도 스레드가 살아 있는지 검사하지 않습니다. 어떤 스레드가 멈춰 있어도 `errors == []`이고, 다른 스레드가 마이그레이션을 끝냈으면 컬럼 검사도 통과합니다. 결국 거짓 통과가 됩니다. 지금은 busy timeout 5초와 barrier timeout 10초가 있어서 실제로 멈출 가능성은 낮습니다.
- 근거: `errors`에는 예외만 모이고, 끝나지 않은 스레드는 기록되지 않습니다.
- 수정 제안: join 뒤에 `assert not any(t.is_alive() for t in threads)`를 넣습니다. 또는 살아 있는 스레드를 `errors`에 기록합니다.

## 이전 지적 확인
- R-3 (= M-1, security S-1과 같은 건, H3에서 major로 올림): **해결**
  - 코드: `src/shortlink/db.py`에서 `isolation_level = None`로 바꾸고, 명시적 `BEGIN IMMEDIATE` 안에서 CREATE, PRAGMA 확인, ALTER를 한 번에 실행한 뒤 COMMIT합니다. sqlite3 모듈의 암묵적 트랜잭션과 섞이지 않습니다. `BEGIN IMMEDIATE`는 busy handler(기본 5초)를 따르므로, 늦게 시작한 프로세스는 기다렸다가 완성된 스키마를 보고 아무것도 추가하지 않습니다.
  - 재현 확인: scratchpad 스크립트(<HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F2-human-r1\6b9f136f-7a3b-45ab-a757-4610fbafef32\scratchpad\race\run_race.py)로 회귀 테스트와 같은 시나리오(F1 DB, 스레드 6개, barrier)를 돌렸습니다.
    - 이전 구현(e9f25fe의 db.py): 3회 실행 모두 10라운드 중 10라운드가 `OperationalError('duplicate column name: clicks')`로 실패했습니다.
    - 새 구현: 50라운드 중 실패 0입니다.
  - 따라서 새 테스트 `test_concurrent_init_schema_on_f1_database_migrates_exactly_once`는 회귀를 실제로 잡아냅니다. 컬럼이 하나씩만 생기는지와 기존 행이 `(0, None)`인지도 확인합니다.
- R-1 (H3에서 major로 올림): **해결**
  - `web.py` 모듈 docstring에 F2 목업이 추가됐습니다.
  - `shorten_form`의 "(to add)"가 지워졌습니다.
  - `create_link` docstring에 `alias`(생략·null이면 무작위, `""`과 규칙 위반·비문자열이면 422)와 409(`MSG_ALIAS_TAKEN`)가 적혔습니다. 실제 동작과 일치합니다.
- R-2, R-4: H3 결정에 따라 minor로 기록만 하는 항목이라 다시 지적하지 않습니다.

관련 파일:
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r1\src\shortlink\db.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r1\src\shortlink\web.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r1\src\shortlink\api.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r1\tests\test_stats.py
