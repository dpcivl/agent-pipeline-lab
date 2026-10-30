---
seq: 14
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-30T00:03:29.669Z"
agent: "security"
agent_id: "ab096ebd4ae25c7d8"
turn: 1
reply_to: 11
chars: 5125
tokens_est: 2714
wait_s: null
---

## 결과: 지적 5건 (blocker 0, major 0, minor 5)

F2 변경분(`git diff 79faa29..e9f25fe`)을 점검했습니다. 원격에서 악용할 수 있는 취약점은 찾지 못했습니다. 지적 5건은 모두 방어를 강화하는 제안입니다. 저장소 파일은 하나도 수정하지 않았고, 동작 확인은 scratchpad의 임시 DB로만 했습니다.

## 지적 목록

### S-1 [minor] F1 DB 마이그레이션이 여러 프로세스가 동시에 시작하면 실패함
- 위치: `src/shortlink/db.py:44-48`
- 취약점: `PRAGMA table_info`로 컬럼을 확인한 뒤 `ALTER TABLE`을 하는 사이에 다른 프로세스가 끼어들 수 있습니다(TOCTOU). Python 3.12 sqlite3의 기본 모드는 DDL 앞에서 트랜잭션을 자동으로 열지 않아서, 확인과 추가가 원자적으로 묶이지 않습니다.
- 공격 시나리오: 외부 공격은 아니고 가용성 문제입니다. F1 DB를 쓰던 서버를 F2로 올리면서 `uvicorn --workers N`으로 띄우면, 처음 한 워커를 뺀 나머지가 `OperationalError: duplicate column name: clicks`로 시작에 실패합니다. 재현해 보니 4개 프로세스로 30번 시도한 120번 중 90번이 실패했습니다(시도마다 1개만 성공). 다시 시작하면 정상으로 돌아옵니다.
- 수정 제안: 확인과 추가를 `BEGIN IMMEDIATE` 트랜잭션 하나로 묶거나, `duplicate column name` 오류를 잡은 뒤 컬럼을 다시 확인하고 넘어가게 합니다.

### S-2 [minor] 예약어 목록이 지금 있는 경로만 막음
- 위치: `src/shortlink/validation.py:84` (`RESERVED_ALIASES`)
- 취약점: 예약어는 설계서의 9개뿐입니다. `login`, `logout`, `signin`, `account`, `settings`, `auth`, `health`, `robots`, `favicon`, `help`, `support`, `security` 같은 이름은 별칭으로 만들 수 있습니다(`login`, `health`, `favicon`, `robots`가 201로 생성되는 것을 확인함). 예약어 검사는 생성할 때만 하므로, 나중에 예약어를 늘려도 이미 저장된 별칭은 남습니다.
- 공격 시나리오: (1) 공격자가 `https://<서비스>/login`이나 `/account-security` 같은 별칭을 피싱 페이지로 연결하면, 서비스 도메인의 공식 경로처럼 보여 신뢰도가 올라갑니다. (2) F3에서 `/login` 같은 한 단계 경로를 추가하면, 이미 있는 같은 이름의 별칭과 경로가 서로 가립니다.
- 수정 제안: F3에서 생길 경로와 흔한 운영·인증 경로를 지금 예약어에 넣습니다. F3에서 경로를 추가할 때는 그 이름의 기존 별칭이 DB에 있는지 확인하는 절차를 둡니다. 설계서 예약어 9개 밖으로 늘리는 일이라 사람 결정이 필요합니다.

### S-3 [minor] 대소문자만 다른 별칭으로 흉내 내기
- 위치: `src/shortlink/validation.py:82, 130`, `src/shortlink/repository.py`의 별칭 INSERT
- 취약점: 별칭이 대소문자를 구분해서(AC-8, D-F2-3), `Team-Docs`가 있어도 `team-docs`나 `TEAM-DOCS`를 다른 사람이 만들 수 있습니다. `l`/`I`/`1`, `O`/`0`처럼 헷갈리는 문자도 막지 않습니다.
- 공격 시나리오: 공개된 별칭 `/Team-Docs`를 보고 공격자가 `/team-docs`를 피싱 URL로 만들어 둡니다. 링크를 손으로 치거나 소문자로 옮겨 적는 사용자는 공격자의 링크로 이동합니다.
- 수정 제안: 설계서가 정한 동작이라 지금은 위험을 받아들인 것으로 기록만 해 두면 됩니다. 나중에 바꾼다면 소문자로 정규화한 키에 UNIQUE를 걸어 대소문자 변형 생성을 막는 방법이 있습니다(AC-8 변경이 필요함).

### S-4 [minor] 인증 없는 통계 공개와 클릭이 세지지 않는 존재 확인 경로
- 위치: `src/shortlink/api.py:83-93`, `src/shortlink/web.py:138-147`
- 취약점: 코드만 알면 누구나 원래 URL, 클릭 수, 마지막 접근 시각을 볼 수 있습니다. 통계 조회는 클릭을 세지 않으므로, 링크를 만든 사람 모르게 존재 여부와 행선지를 확인할 수 있습니다. 무작위 코드(62^7)는 추측하기 어렵지만, 별칭은 사전 단어라 쉽게 추측됩니다.
- 공격 시나리오: 공격자가 흔한 단어 별칭을 통계 API로 훑어서 다른 사람의 링크와 행선지(쿼리 문자열에 들어 있는 토큰 포함)를 모읍니다. 한 사람에게만 보낸 링크라면 `last_accessed_at`을 보고 받는 사람이 언제 열었는지 알 수 있습니다.
- 수정 제안: F3 인증 범위입니다. F3에서 통계 조회를 링크 소유자로 제한하는 것을 권합니다. 그 전까지는 문서에 "통계는 공개됨"이라고 적어 둡니다.

### S-5 [minor] 리다이렉트가 쓰기 트랜잭션이 되어 클릭 부풀리기와 잠금 경합이 생김
- 위치: `src/shortlink/web.py:130`, `src/shortlink/repository.py:107-117`
- 취약점: 이제 `GET /{code}`는 없는 코드라도 매번 `UPDATE`(쓰기 잠금)를 실행합니다. 기본 rollback journal 모드와 5초 busy timeout에서 쓰기가 몰리면 `database is locked`로 500이 나고, 그 클릭은 기록되지 않습니다. 클릭 수는 누구나 GET을 반복해 부풀릴 수 있습니다. 원자성은 지켜집니다. 8개 프로세스로 3,200번 동시에 호출한 4번 중 3번은 1,600 클릭이 정확히 맞았고, 1번은 오류 2건(1건은 클릭 손실)이 났습니다.
- 공격 시나리오: 없는 코드로 GET을 많이 보내면 쓰기 잠금 경합이 생겨 정상 리다이렉트와 링크 생성이 느려지거나 500이 납니다. 경쟁 링크의 클릭 수를 조작할 수도 있습니다.
- 수정 제안: 요청 수 제한은 F3 범위입니다. 지금 할 수 있는 방어는 세 가지입니다. (1) `record_click` 실패(`OperationalError`)를 잡고 `get()`으로 되돌아가 리다이렉트는 계속합니다(클릭 집계는 최선 노력으로 둠). (2) WAL 모드와 `busy_timeout`을 설정합니다. (3) 필요하면 쓰기 전에 코드가 있는지 읽기로 먼저 확인해서, 없는 코드는 쓰기 잠금을 잡지 않게 합니다.

## 문제없음으로 확인한 항목
- SQL 인젝션: 새 쿼리(별칭 INSERT, `UPDATE ... RETURNING`, 통계 SELECT)는 모두 파라미터 바인딩을 씁니다. `ALTER`와 `PRAGMA`는 상수 문자열입니다.
- 원자적 증가: `clicks = clicks + 1` 한 문장이라 읽고-더하고-쓰기가 없습니다. 동시 실행에서도 업데이트가 사라지지 않았습니다. 404는 클릭을 세지 않습니다.
- 별칭 검증: `isascii()`와 `fullmatch`로 검사합니다. `"abcd\n"`, 키릴 문자 `с`, NUL은 422입니다. `Links`, `LINKS`는 예약어로 422입니다. `openapi.json`은 문자 규칙에서 막힙니다. 검증이 저장보다 먼저 일어나고, 중복은 SELECT 없이 INSERT 결과로 409를 판단해서 경쟁 상태가 없습니다.
- 경로 충돌: `/links`, `/static`은 404입니다. `/docs`, `/redoc`, 두 단계 경로인 `/stats/{code}`와 `/links/{code}/stats`는 별칭과 겹치지 않습니다.
- XSS: Jinja2 자동 이스케이프가 켜져 있고 `|safe`와 `Markup`은 쓰지 않습니다. 폼 오류 화면에 되돌려 보여 주는 별칭 `"><script>`는 `&#34;&gt;&lt;script&gt;`로 이스케이프됩니다. 통계 화면은 원래 URL을 텍스트로만 출력하고, `href`에는 `base_url`과 검증된 코드만 들어갑니다. 결과 화면의 `/stats/{{ code | urlencode }}`도 안전합니다. CSP 미들웨어는 새 화면에도 적용됩니다.
- 정보 노출: 통계 API 404 본문은 고정 문구입니다. 500은 FastAPI 기본 응답이라 내부 정보가 나가지 않습니다.
- 마이그레이션 데이터: F1 행은 `clicks=0`, `last_accessed_at=NULL`이 되고, `init_schema`를 여러 번 불러도 안전합니다(단일 프로세스 기준. 동시 실행은 S-1).
- bandit: `uv run bandit`은 애플리케이션 제어 정책에 막혀 실행되지 않았습니다. 대신 `uv run python -m bandit -r src -q`로 돌렸고 지적 0건입니다(종료 코드 0).
- 의존성: fastapi 0.162.0, starlette 1.10.0, jinja2 3.1.6, markupsafe 3.0.4, python-multipart 0.0.32, pydantic 2.14.1, uvicorn 0.54.0. F2에서 새로 추가된 의존성은 없습니다. 취약점 DB로 대조하지는 않았습니다(pip-audit 없음).

## 이전 지적 확인 (2라운드부터)
- 해당 없음(1라운드)

참고: 확인에 쓴 스크립트는 아래 경로에 있으며 저장소 밖입니다.
- <HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F2-human-r1\6b9f136f-7a3b-45ab-a757-4610fbafef32\scratchpad\probe.py
- <HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F2-human-r1\6b9f136f-7a3b-45ab-a757-4610fbafef32\scratchpad\race.py
- <HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F2-human-r1\6b9f136f-7a3b-45ab-a757-4610fbafef32\scratchpad\clicks.py
