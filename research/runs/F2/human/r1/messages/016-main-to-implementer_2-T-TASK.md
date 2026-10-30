---
seq: 16
sender: "main"
receiver: "implementer#2"
type: "T-TASK"
timestamp: "2026-10-30T00:04:18.836Z"
agent: "implementer#2"
agent_id: "a6c00ee82887d825d"
turn: 1
reply_to: null
chars: 1234
tokens_est: 603
wait_s: null
---

F2 리뷰 1라운드 지적 중 사람이 major로 올려 수정하기로 한 2건을 고쳐 주세요. 나머지 minor는 고치지 않습니다.

M-1 (reviewer R-3, security S-1): `src/shortlink/db.py`의 init_schema F1 DB 마이그레이션이 원자적이지 않습니다. `PRAGMA table_info` 확인과 `ALTER TABLE ... ADD COLUMN`이 각각 자동 커밋으로 실행되어, F1 DB로 여러 프로세스(`uvicorn --workers N`)가 동시에 시작하면 늦은 쪽이 `OperationalError: duplicate column name`으로 시작에 실패합니다(security가 4개 프로세스로 120번 중 90번 재현). 고칠 방향: 테이블 생성·컬럼 확인·ALTER를 `BEGIN IMMEDIATE ... COMMIT` 트랜잭션 하나로 묶는 방법을 우선 권합니다(Python 3.12 sqlite3 레거시 트랜잭션 모드에서는 isolation_level 동작에 주의해서 명시적으로 BEGIN IMMEDIATE를 실행). 필요하면 busy timeout 안에서 기다리게 해 주세요. 여러 번 불러도 안전해야 하는 성질은 유지합니다.

R-1: 스텁 시절 docstring이 남아 실제 동작과 다릅니다.
- `src/shortlink/web.py` shorten_form docstring의 "F2 (to add): ..."를 현재형으로.
- `src/shortlink/web.py` 모듈 docstring에 F2 목업(docs/plans/mockups/F2-*.html)도 기준으로 적기.
- `src/shortlink/api.py` create_link docstring에 alias 처리(생략·null이면 무작위, ""이면 422, 규칙 위반 422)와 409(MSG_ALIAS_TAKEN)를 추가.

M-1의 동시 시작을 확인하는 회귀 테스트는 test-writer가 따로 쓸 예정이니 tests/는 건드리지 마세요. 대신 scratchpad 등 저장소 밖 임시 경로에서 여러 프로세스 동시 시작 재현 스크립트로 수정 전/후를 확인해 주세요(저장소 안에 파일을 남기지 마세요).
`uv run python -m pytest`로 전체 테스트, `uv run ruff check src tests`, `uv run ruff format src`도 확인하고, git 커밋은 하지 마세요.
끝나면 바꾼 내용과 재현 확인 결과를 짧게 보고해 주세요.
