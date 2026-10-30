---
seq: 17
sender: "main"
receiver: "test-writer#2"
type: "T-TASK"
timestamp: "2026-10-30T00:04:18.846Z"
agent: "test-writer#2"
agent_id: "a542d32d511d17b4b"
turn: 1
reply_to: null
chars: 1177
tokens_est: 614
wait_s: null
---

F2 리뷰 1라운드에서 사람이 고치기로 한 M-1의 회귀 테스트를 추가해 주세요.

M-1: `src/shortlink/db.py`의 `init_schema()`가 F1 스키마 DB(links: code TEXT PRIMARY KEY, url TEXT NOT NULL, created_at TEXT NOT NULL)를 마이그레이션할 때, 컬럼 확인(PRAGMA table_info)과 ALTER TABLE ADD COLUMN이 원자적이지 않아, 여러 프로세스가 동시에 시작하면 늦은 쪽이 `sqlite3.OperationalError: duplicate column name`으로 실패합니다. implementer가 지금 동시에 BEGIN IMMEDIATE 트랜잭션으로 묶는 수정을 하고 있습니다(src/는 건드리지 마세요).

할 일: `tests/test_stats.py`의 마이그레이션 테스트 근처에, 같은 F1 DB 파일에 대해 `init_schema(db_path)`를 여러 실행 단위에서 동시에 호출해도 모두 예외 없이 끝나고, 결과 테이블에 clicks·last_accessed_at 컬럼이 하나씩만 있고 기존 행이 clicks=0으로 남는지 확인하는 테스트를 추가해 주세요.
- 진짜 경쟁을 만들려면 프로세스(multiprocessing, spawn)나 스레드 + threading.Barrier를 쓰세요. 여러 번(예: 10~20회 반복) 시도해 수정 전 코드에서는 높은 확률로 실패하도록 해 주세요. 너무 느리지 않게(몇 초 이내).
- Windows에서 돌아가야 합니다(spawn 방식이면 대상 함수는 모듈 최상위 함수). SQLite 연결은 항상 닫아 주세요.
- 이 PC에서는 `uv run python -m pytest`로 실행합니다(`uv run pytest`는 정책상 막힘). `uv run ruff check src tests`, `uv run ruff format tests`도 확인.
- git 커밋은 하지 마세요.

가능하면 `git stash` 대신, 수정 전 코드(`git show e9f25fe:src/shortlink/db.py`)를 저장소 밖 임시 경로에 꺼내 같은 경쟁 시나리오로 실패하는지 확인해 테스트가 버그를 잡는다는 근거를 보고해 주세요(저장소 안 파일을 수정 전으로 되돌리지 마세요). 끝나면 추가한 테스트 이름과 실행 결과를 짧게 보고해 주세요.
