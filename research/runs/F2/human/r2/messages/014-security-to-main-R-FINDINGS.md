---
seq: 14
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-30T00:49:31.637Z"
agent: "security"
agent_id: "a6b1de572f634da49"
turn: 1
reply_to: 11
chars: 4492
tokens_est: 2450
wait_s: null
---

## 결과: 지적 3건 (blocker 0, major 0, minor 3)

F2 변경분(`git diff 0b748cc 16fdb28 -- src`)에서 원격으로 악용할 수 있는 취약점이나 검증 누락은 찾지 못했습니다. 세 건 모두 방어를 강화하자는 minor 제안입니다. 각 항목은 코드 읽기에 더해 TestClient로 실제 동작을 확인했습니다. 임시 DB는 scratchpad에만 만들었고 저장소 파일은 수정하지 않았습니다.

## 지적 목록

### S-1 [minor] 리다이렉트가 클릭 기록(쓰기 잠금)에 묶여 있어, 쓰기 경합이 생기면 리다이렉트 자체가 500으로 실패함
- 위치: `src/shortlink/web.py:173`, `src/shortlink/repository.py:114-131`
- 취약점: F1의 `GET /{code}`는 읽기만 했습니다. F2부터는 요청마다 `UPDATE`와 커밋을 하므로 DB 쓰기 잠금이 필요합니다. 다른 연결이 쓰기 잠금을 잡고 있으면 sqlite3 기본 대기 시간(5초)을 넘긴 뒤 `OperationalError: database is locked`가 나고, 핵심 기능인 리다이렉트가 500이 됩니다. 실측: 다른 연결에서 `BEGIN IMMEDIATE`로 잠금을 잡자 `GET /abcd`는 5.5초 뒤 500이 났고, 같은 조건에서 읽기만 하는 `GET /links/abcd/stats`는 200이었습니다. 응답 본문은 일반 "Internal Server Error"라서 내부 정보는 노출되지 않습니다.
- 공격 시나리오: 인증 없이 누구나 `GET /{code}`와 `POST /links`를 대량으로 보내 쓰기를 한 줄로 세우면, 정상 사용자의 리다이렉트까지 지연되거나 500이 납니다. 부가 기능인 통계 쓰기가 실패해도 본 기능이 같이 죽는 구조입니다. 요청 수 제한은 범위 밖이지만, 쓰기 실패가 리다이렉트를 끌고 내려가는 점은 F2가 새로 만든 회귀입니다.
- 수정 제안: `follow_link`에서 `record_click`이 `sqlite3.OperationalError`를 내면 `repository.get(code)`로 대신 조회해 302는 그대로 보내고 클릭 1건만 놓치게 합니다(fail-open). 필요하면 `connect()`에 `PRAGMA journal_mode=WAL`과 적절한 `busy_timeout`을 함께 둡니다.

### S-2 [minor] 마이그레이션이 원자적이지 않아, 여러 워커가 동시에 시작하면 F1 DB에서 시작이 실패함
- 위치: `src/shortlink/db.py:51-55` (`ensure_click_columns`)
- 취약점: `PRAGMA table_info`로 열을 확인하는 단계와 `ALTER TABLE ... ADD COLUMN` 단계가 한 쓰기 트랜잭션으로 묶여 있지 않습니다. 파이썬 sqlite3 기본 모드에서는 DDL이 즉시 커밋되므로 `with conn`도 이 둘을 묶지 못합니다. 두 프로세스가 동시에 "열 없음"을 보고 둘 다 ALTER를 실행하면, 늦은 쪽이 `OperationalError: duplicate column name: clicks`로 `create_app()`에서 죽습니다. 연결 두 개를 번갈아 실행해 재현했습니다. 다시 시작하면 정상으로 돌아오고(멱등), 외부로 정보가 노출되지도 않습니다.
- 공격 시나리오: 외부 공격 경로는 없습니다. 배포 중 `uvicorn --workers N`으로 F1 DB를 처음 올릴 때 일부 워커가 시작에 실패할 수 있어 가용성이 떨어집니다.
- 수정 제안: 확인과 ALTER를 `BEGIN IMMEDIATE ... COMMIT` 안에서 실행해 직렬화합니다. 또는 ALTER에서 "duplicate column name" `OperationalError`만 잡아 무시하고, 다른 오류는 그대로 올려 시작을 멈추게 합니다.

### S-3 [minor] 통계 API와 화면이 코드만 알면 누구에게나 클릭 수와 마지막 접근 시각을 공개함 (설계상 허용, 결정 기록 권고)
- 위치: `src/shortlink/api.py` `get_link_stats`(`GET /links/{code}/stats`), `src/shortlink/web.py` `link_stats_page`(`GET /stats/{code}`)
- 취약점: 링크에 소유자 개념이 없어서 남의 링크 통계도 볼 수 있습니다. 판단: 설계서 F2.md에 소유자나 인증이 없고 인증은 범위 밖입니다. 원래 URL은 코드만 알면 리다이렉트로 이미 알 수 있으므로 통계가 URL을 추가로 노출하지는 않습니다. 따라서 F2에서는 허용 범위로 봅니다. 다만 새로 드러나는 정보가 둘 있습니다. (1) `clicks`와 `last_accessed_at`은 받는 사람의 행동 정보입니다(언제 열었는지). (2) 별칭은 추측하기 쉬운 이름이라(`/links/resume/stats` 같은 식) 무작위 7자 코드보다 조회 대상이 되기 쉽습니다.
- 공격 시나리오: 특정 사람에게 보낸 별칭 링크의 통계를 계속 조회해, 상대가 링크를 열었는지와 그 시각을 알아냅니다. 같은 맥락에서 `<img src="/{code}">`를 다른 사이트에 심거나 미리보기 봇을 이용해 클릭 수를 부풀릴 수 있지만, 이는 D2-8과 요청 수 제한(범위 밖)에서 이미 받아들인 한계입니다.
- 수정 제안: F2 코드는 고칠 필요가 없습니다. `docs/plans/F2-plan.md` 5절에 "통계는 코드를 아는 누구나 조회 가능(설계상 허용)"을 결정으로 남기고, F3(인증과 관리 화면)에서 소유자만 통계를 보게 할지 검토합니다.

## 문제 없음으로 확인한 항목 (중점 요청 대응)
- 별칭 검증(`src/shortlink/validation.py`): 길이 검사를 정규식보다 먼저 하고(최대 30자라 ReDoS 여지 없음), `fullmatch`에 ASCII 범위만 씁니다. 전각 문자, 아랍 숫자, `İ`, `ſ`, 폭 없는 공백, 끝 줄바꿈, 짝 없는 서로게이트(JSON `\ud800`)를 모두 422로 거절하는 것을 확인했습니다. 예약어는 ASCII를 통과한 뒤 `.lower()`로 비교하므로 유니코드 대소문자 변환을 이용한 우회가 없습니다(`LINKS`, `Stats`, `ADMIN` 거절).
- 라우트 충돌: 한 단계 경로는 `/docs`, `/redoc`, `/openapi.json`, `/links`(POST 전용이라 GET은 `/{code}`로 감), `/static`(마운트는 `/static/` 아래만 받음)이고 모두 예약어에 들어 있습니다. 무작위 코드는 7자라 예약어(최대 6자, `openapi.json`은 `.` 포함)와 겹칠 수 없습니다. 라우트는 대소문자를 구분하므로 `/ABCD`는 404입니다. `%2F`는 경로 분리로 처리되어 404입니다.
- SQL: 새로 추가된 INSERT, UPDATE, SELECT가 모두 `?` 바인딩을 씁니다. PRAGMA와 ALTER는 고정 문자열입니다. bandit 지적 0건입니다.
- 별칭 중복: PRIMARY KEY 충돌에 맡기는 INSERT 한 번이라 확인 후 사용 사이의 경쟁(TOCTOU)이 없습니다. 409 뒤에도 기존 링크는 원래 URL로 리다이렉트됩니다. 409 본문에 기존 URL이 담기지 않습니다.
- 클릭 수 경쟁: `clicks = clicks + 1`을 SQL 안에서 하고, UPDATE와 SELECT가 같은 트랜잭션입니다. 16스레드로 200회 동시 요청을 보내 정확히 200이 늘었습니다. HEAD와 OPTIONS는 405라서 세지 않습니다. 통계 조회는 `get()`만 씁니다.
- XSS: Starlette `Jinja2Templates`의 자동 이스케이프가 켜져 있고, `|safe`와 `Markup`은 0건입니다. 오류 화면의 `value="{{ alias_value }}"`에 `"><script>`를 넣으면 `&#34;&gt;&lt;script&gt;`로 이스케이프됩니다. `result.html`의 `href="/stats/{{ code }}"`는 코드가 무작위 영숫자이거나 검증된 별칭(`[A-Za-z0-9-]`)이라 위험한 스킴이 들어갈 수 없습니다. `stats.html`은 원래 URL을 텍스트로만 보여 주고 href에 쓰지 않으며, CSP 헤더가 붙는 것을 확인했습니다.
- 오픈 리다이렉트: `follow_link`의 Location은 F1과 같은 `location_header_value()`를 쓰고 `validate_url`도 바뀌지 않아 F1 동작이 유지됩니다.
- 정보 노출: 404는 고정 문구, 500은 일반 문구입니다. 마이그레이션 오류는 시작 시점에 프로세스를 멈출 뿐 HTTP로 노출되지 않습니다. 비문자열 `alias`에 대한 FastAPI 기본 422 본문은 입력값을 되돌려 주지만 JSON에 nosniff가 붙어 있고, F1부터 있던 동작입니다.
- 의존성: `pyproject.toml`과 `uv.lock`은 F2에서 바뀌지 않았습니다. dev 의존성 `httpx2`는 Starlette 1.10 테스트 클라이언트가 요구하는 패키지입니다.
