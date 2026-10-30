---
seq: 18
sender: "test-writer#2"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-30T00:07:21.198Z"
agent: "test-writer#2"
agent_id: "a542d32d511d17b4b"
turn: 1
reply_to: 17
chars: 2063
tokens_est: 964
wait_s: null
---

## 결과: 완료
## 변경 파일
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r1\tests\test_stats.py: F1 스키마 DB 동시 마이그레이션 회귀 테스트 1개와 헬퍼 2개를 추가했습니다. `import threading`도 추가했습니다. `src/`는 건드리지 않았고 커밋도 하지 않았습니다.

## 추가한 테스트
- `test_concurrent_init_schema_on_f1_database_migrates_exactly_once`
  - 반복마다 새 F1 DB 파일(3컬럼, 행 3개)을 만듭니다.
  - 스레드 6개가 `threading.Barrier`로 동시에 출발해 `init_schema(db_path)`를 호출합니다.
  - 이 과정을 10회 반복합니다(`RACE_ROUNDS=10`, `RACE_WORKERS=6`).
  - 모든 스레드가 예외 없이 끝나는지 확인합니다.
  - `PRAGMA table_info` 컬럼이 정확히 `code, url, created_at, clicks, last_accessed_at` 하나씩인지 확인합니다.
  - 기존 3행이 `clicks=0, last_accessed_at=NULL`로 남는지 확인합니다.
  - 모든 SQLite 연결은 `closing`으로 닫습니다.
- 헬퍼는 `_create_f1_database`, `_init_schema_concurrently`입니다.
- spawn 프로세스 대신 스레드를 택했습니다. Windows에서 spawn 자식이 테스트 모듈을 import하느라 느리고, 스레드로도 경쟁이 충분히 재현되기 때문입니다.

## 수용 기준과 테스트 대응
- M-1(동시 시작 시 마이그레이션 원자성): `test_concurrent_init_schema_on_f1_database_migrates_exactly_once`
  - M-1은 기능 설계서의 수용 기준이 아니라 리뷰 결함입니다. F2 호환성 요구(F1 DB로 시작해도 동작)의 동시 시작 경로를 덮습니다.

## 버그를 잡는다는 근거
- 수정 전 코드(`git show e9f25fe:src/shortlink/db.py`)를 저장소 밖 스크래치 경로(`<HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F2-human-r1\6b9f136f-7a3b-45ab-a757-4610fbafef32\scratchpad\old\old_db.py`)에 꺼냈습니다.
- 같은 테스트 함수의 `init_schema`만 그 파일 것으로 바꿔 5회 실행했습니다. 5/5회 모두 round 0에서 실패했고, 오류는 `OperationalError('duplicate column name: clicks')`였습니다. 실행 시간은 0.3초입니다.
- 저장소의 현재 `src/shortlink/db.py`는 아직 수정 전 상태입니다(`git diff -- src`가 비어 있음). 그래서 저장소 안에서 이 테스트는 현재 실패하고, 이 실패는 의도한 것입니다.
  - 확인한 명령: `uv run python -m pytest tests/test_stats.py -k concurrent`를 3번 실행해 모두 실패했습니다.
  - 전체 실행(`uv run python -m pytest -q`)은 `1 failed, 405 passed`였습니다. 실패한 1개가 이 테스트입니다.
- 참고용으로 `BEGIN IMMEDIATE`로 묶은 임시 구현을 스크래치 경로(`...\scratchpad\fixed\old_db.py`)에 만들어 같은 시나리오를 돌렸습니다. 10회 모두 통과했고 약 1초 걸렸습니다. 같은 구현에서 테스트 전체 소요는 몇 초 이내일 것으로 봅니다.
- implementer의 수정이 반영되면 이 테스트가 통과해야 합니다.

## 설계서 해석이 필요했던 부분
- 없음

## 남은 문제와 질문
- 없음
- `uv run ruff check src tests`는 통과했고, `uv run ruff format tests`는 "9 files left unchanged"였습니다.
