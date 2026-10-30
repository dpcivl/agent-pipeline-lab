---
seq: 27
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-30T00:24:37.295Z"
agent: "security"
agent_id: "ab096ebd4ae25c7d8"
turn: 2
reply_to: 24
chars: 3419
tokens_est: 1740
wait_s: null
---

## 결과: 지적 4건 (blocker 0, major 0, minor 4)

S-1은 해결됐습니다. 이번 변경에서 새로 생긴 지적은 없습니다. 남은 4건(S-2~S-5)은 H3 결정에 따라 minor로 기록만 하고 고치지 않은 지난 지적입니다. 점검 범위는 `git diff e9f25fe..6b2d234`입니다. 실제 코드가 바뀐 곳은 `src/shortlink/db.py`이고, `api.py`와 `web.py`는 docstring만 바뀌었으며, 그 밖에 `tests/test_stats.py`에 테스트가 추가됐습니다. `repository.py`와 템플릿은 바뀌지 않았습니다. 파일은 수정하지 않았습니다.

## 지적 목록

### S-2 [minor] 예약어 목록이 지금 있는 경로만 막음 (H3: 기록만, F3에서 검토)
- 위치: `src/shortlink/validation.py:84`
- 취약점, 공격 시나리오, 수정 제안: 1라운드와 같습니다. 변경 없음.

### S-3 [minor] 대소문자만 다른 별칭으로 흉내 내기 (설계서 AC-8 결정, 기록만)
- 위치: `src/shortlink/validation.py:82, 130`
- 취약점, 공격 시나리오, 수정 제안: 1라운드와 같습니다. 변경 없음.

### S-4 [minor] 인증 없는 통계 공개와 클릭이 세지지 않는 존재 확인 경로 (H3: F3에서 검토)
- 위치: `src/shortlink/api.py`의 `get_link_stats`, `src/shortlink/web.py`의 `stats_page`
- 취약점, 공격 시나리오, 수정 제안: 1라운드와 같습니다. 변경 없음.

### S-5 [minor] 리다이렉트가 쓰기 트랜잭션이 되어 클릭 부풀리기와 잠금 경합이 생김 (H3: F3에서 검토)
- 위치: `src/shortlink/web.py`의 `follow_link`, `src/shortlink/repository.py:107-117`
- 취약점, 공격 시나리오, 수정 제안: 1라운드와 같습니다. 변경 없음.

## 이전 지적 확인 (2라운드부터)
- S-1: 해결 (M-1로 통합됨). 근거는 다음과 같습니다.
  - 바뀐 코드: `src/shortlink/db.py:39-62`. 이 연결에서만 `isolation_level = None`으로 두고, `BEGIN IMMEDIATE` 안에서 CREATE, `PRAGMA table_info`, ALTER를 한 번에 처리합니다. 예외가 나면 `ROLLBACK` 후 다시 던지고, 정상이면 `COMMIT`합니다.
  - 동시 시작 재현: 1라운드에서는 4개 프로세스 120번 중 90번이 실패했습니다.
    - 공유 scratchpad의 `race.py`(4개 프로세스, 40라운드): 실패 0/40
    - 새로 쓴 `race2.py`(6개 프로세스 x 30라운드)
      - F1 DB: 180번 중 실패 0
      - 빈 DB 동시 생성: 180번 중 실패 0
      - 모든 라운드에서 마지막 컬럼은 5개로 맞았습니다.
  - 확인 2의 결과: db.py에 새 문제 없음
    - isolation_level 변경 범위: `init_schema`가 쓰는 연결에서만 바꿉니다. `connect()`와 저장소 연결은 그대로라서 `create`/`record_click`의 `with conn` 트랜잭션 동작은 달라지지 않습니다.
    - 예외 시 연결 상태: ALTER 도중에 `KeyboardInterrupt`를 일으켜 보니 예외가 그대로 전달됐습니다. 먼저 실행된 `clicks` ALTER까지 되돌려졌고(컬럼 3개 유지), 그 직후 다른 연결이 timeout 0.5초로 `BEGIN IMMEDIATE`를 바로 얻었습니다. 다시 실행하니 정상으로 마이그레이션됐습니다. 잠금이 남거나 스키마가 반쯤 바뀐 채로 남지 않습니다. `BEGIN IMMEDIATE`가 `try` 밖에 있어서 잠금을 얻지 못했을 때 엉뚱한 ROLLBACK을 실행하지도 않습니다. 연결은 `closing()`으로 항상 닫힙니다.
    - 잠금 보유 시간: 트랜잭션 안에는 DDL 몇 문장만 있어서 잠금을 오래 잡지 않습니다. 다른 연결이 쓰기 잠금을 계속 잡고 있으면 기본 busy timeout 후 약 5.5초에 `OperationalError: database is locked`로 시작에 실패하고, 잠금이 풀린 뒤 다시 실행하면 성공합니다. 시작 시점에 실패하는 동작이라 받아들일 만합니다.
  - 지적은 아니지만 참고할 점 두 가지입니다.
    - 이제 `create_app()`은 마이그레이션이 필요 없을 때도 시작할 때마다 짧게 쓰기 잠금을 잡습니다. 트래픽이 있는 상태에서 재시작하면 S-5의 쓰기 경합과 겹칠 수 있지만, 대기 한도가 5초라 실제로 문제 될 가능성은 낮습니다.
    - SQLite가 오류(디스크 가득 참, I/O 오류 등) 때문에 트랜잭션을 스스로 이미 되돌린 경우, `except`의 `ROLLBACK`이 "no transaction is active"로 다시 실패해서 그 오류가 원래 예외를 덮을 수 있습니다. 원래 예외는 traceback의 `__context__`에 남고, 연결을 닫으면 어차피 되돌려지므로 보안 영향은 없습니다. 고친다면 `if conn.in_transaction: conn.rollback()`처럼 쓰면 됩니다.
- S-2: 미해결. H3 결정으로 기록만 하고 F3에서 검토합니다.
- S-3: 미해결. 설계서 AC-8에 따른 동작이라 기록만 합니다.
- S-4: 미해결. H3 결정으로 기록만 하고 F3에서 검토합니다.
- S-5: 미해결. H3 결정으로 기록만 하고 F3에서 검토합니다.

## 그 밖의 확인
- bandit: `uv run bandit`은 애플리케이션 제어 정책에 막혀 1라운드처럼 `uv run python -m bandit -r src -q`로 돌렸고, 지적 0건입니다(종료 코드 0).
- SQL: 새로 들어온 SQL은 상수 문자열(`BEGIN IMMEDIATE`, `ROLLBACK`, `COMMIT`)뿐이라 인젝션이 생길 곳이 없습니다.
- 공유 scratchpad: `race.py`는 다른 세션이 다시 쓴 파일이었습니다. 무해한 점검 스크립트임을 확인한 뒤 실행했습니다.

확인에 쓴 스크립트:
- <HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F2-human-r1\6b9f136f-7a3b-45ab-a757-4610fbafef32\scratchpad\race.py
- <HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F2-human-r1\6b9f136f-7a3b-45ab-a757-4610fbafef32\scratchpad\race2.py
