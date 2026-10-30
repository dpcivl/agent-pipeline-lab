---
seq: 12
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T08:22:44.481Z"
agent: "security"
agent_id: "a3119cc4291fd310b"
turn: 1
reply_to: 10
chars: 6232
tokens_est: 3114
wait_s: null
---

## 결과: 지적 7건 (blocker 0, major 0, minor 7)

F2 변경분(`git diff 663d5ad b42b3bb`)의 보안 점검 1라운드입니다. blocker와 major는 없습니다. 중점 항목은 모두 통과했고, 지적 7건은 모두 방어를 강화하는 minor입니다. 파일은 하나도 수정하지 않았습니다.

### 중점 항목 점검 결과
- **별칭 검증:** `_ALIAS_PATTERN.fullmatch`가 ASCII 범위 `[A-Za-z0-9-]`만 받고 IGNORECASE 플래그도 없습니다. 임시 DB로 직접 요청을 보내 확인했고, 아래 입력은 모두 422로 거절됐습니다(500 없음). `abcd\n`, 전각 `ａｂｃｄ`, `ab\x00cd`, Kelvin 기호 `\u212aabc`, 점 없는 i `abc\u0131`, JSON `\ud800abc`(서로게이트).
- **예약어:** 소문자로 바꿔 비교하므로 `ADMIN`, `Stats`도 422입니다. 무작위 코드는 7자라서 예약어(6자 이하, `openapi.json` 제외)와 겹칠 수 없습니다. FastAPI의 `/docs` 계열은 앱 생성 시 먼저 등록되고, `web.router`는 맨 마지막에 등록되어 우선순위도 안전합니다.
- **SQL:** 새로 추가된 INSERT, UPDATE, SELECT가 모두 `?` 바인딩을 씁니다. f-string에 들어가는 값은 클래스 상수 `_COLUMNS`뿐입니다.
- **스키마 이전:** `init_schema`의 `PRAGMA table_info(links)`와 두 `ALTER TABLE` 문은 모두 고정 문자열이고 외부 입력이 섞이지 않습니다.
- **클릭 증가의 원자성:** `record_click`이 `clicks = clicks + 1`로 SQL 안에서 늘리고, 다시 읽기까지 한 트랜잭션입니다. 쓰기 잠금을 잡은 상태라 그 사이에 다른 쓰기가 끼어들 수 없습니다.
- **XSS:**
  - Starlette 1.10의 `Jinja2Templates`가 `select_autoescape()`를 쓰므로 `.html` 템플릿은 자동 이스케이프됩니다. `|safe`나 `Markup`은 없습니다.
  - 홈 폼에 `"><script>`를 별칭으로 넣으면 `value="&#34;&gt;&lt;script&gt;..."`로 이스케이프됩니다.
  - 통계 화면의 원래 URL은 `href`가 아니라 텍스트로만 나오고 `&lt;x&gt;&#34;`로 이스케이프됩니다. `href="{{ short_url }}"`과 `href="/stats/{{ code }}"`에는 설정값 base_url과 검증된 코드만 들어갑니다.
  - 통계 화면과 오류 화면 모두 CSP 헤더가 붙습니다(직접 확인).
- **오류 응답:** 사용자 지정 예외 처리기가 없고 debug도 꺼져 있습니다. 404, 409, 422 본문은 고정된 한국어 문구뿐입니다. 서로게이트가 든 경로(`/stats/%ED%A0%80`, `/%ED%A0%80`)는 500이 아니라 404입니다.
- **bandit:** B608 Medium 2건이 나왔고 오탐입니다(S-5).

## 지적 목록

### S-1 [minor] 클릭 수 부풀리기와 별칭 대량 선점 (F3 요청 수 제한 범위)
- 위치: src/shortlink/web.py:135, src/shortlink/api.py:50, src/shortlink/web.py:89
- 취약점: `GET /{code}`를 누구나 무제한으로 호출해 클릭 수를 늘릴 수 있습니다. 별칭 생성에도 제한이 없습니다.
- 공격 시나리오:
  - 스크립트로 특정 링크에 수만 번 요청을 보내 통계를 조작합니다.
  - 기억하기 쉬운 별칭(브랜드명, 흔한 단어)을 대량으로 미리 등록해 선점합니다.
  - 409 응답으로 어떤 별칭이 이미 있는지 알아낼 수 있습니다. 다만 리다이렉트 자체로도 알 수 있는 정보입니다.
- 수정 제안: F3에서 IP나 API 키 단위로 생성과 리다이렉트에 요청 수 제한을 둡니다. 별칭 생성은 인증 사용자로 한정하는 것을 검토합니다.

### S-2 [minor] 통계가 코드만 알면 누구에게나 공개됨 (F3 인증·소유자 범위)
- 위치: src/shortlink/api.py:86-104, src/shortlink/web.py:143-158
- 취약점: `/links/{code}/stats`와 `/stats/{code}`에 소유자 확인이 없습니다. 무작위 코드(62^7)는 추측하기 어렵지만 별칭은 추측하기 쉽습니다.
- 공격 시나리오: 제3자가 `/stats/team-offsite` 같은 추측 가능한 별칭의 클릭 수와 `last_accessed_at`을 조회해 사용 시점과 규모를 알아냅니다. 원래 URL은 리다이렉트로도 드러나므로 새로 노출되는 것은 사용 패턴입니다.
- 수정 제안: F3에서 링크에 소유자를 두고, 통계는 소유자 API 키로만 조회하게 합니다.

### S-3 [minor] 리다이렉트가 DB 쓰기 성공에 묶여 잠금 경합이나 읽기 전용 DB에서 500이 남
- 위치: src/shortlink/repository.py:107-125, src/shortlink/web.py:135
- 취약점: F1에서는 리다이렉트가 읽기만 했습니다. 이제는 매 요청마다 쓰기 트랜잭션이 필요합니다. `connect()`는 sqlite3 기본값(busy timeout 5초, rollback journal)을 씁니다. 잠금을 못 얻거나 DB 파일이 읽기 전용이거나 디스크가 꽉 차면 `sqlite3.OperationalError`가 나고, 그 링크는 500이 됩니다.
- 공격 시나리오: 공격자가 아무 코드로나 리다이렉트를 대량으로 보내 쓰기를 직렬화시킵니다. 그러면 정상 사용자의 리다이렉트와 링크 생성까지 지연되거나 500을 받습니다. 집계 기능 하나가 핵심 기능인 리다이렉트의 가용성을 떨어뜨리는 셈입니다.
- 수정 제안:
  - `follow_link`에서 `sqlite3.OperationalError`를 잡아 로그만 남기고 `repository.get(code)`로 리다이렉트를 계속합니다.
  - `PRAGMA journal_mode=WAL`과 `busy_timeout`을 명시하는 것도 검토합니다.
  - 근본 대책은 F3의 요청 수 제한입니다.

### S-4 [minor] 스키마 이전의 확인과 실행 사이 경쟁 (여러 워커가 동시에 시작할 때)
- 위치: src/shortlink/db.py:132-145
- 취약점: Python sqlite3(3.12, 기본 isolation_level)는 DDL과 PRAGMA 앞에서 트랜잭션을 자동으로 열지 않습니다. 그래서 `PRAGMA table_info` 확인과 `ALTER TABLE` 실행이 원자적이지 않습니다. 외부 입력이 섞이는 문제는 없습니다.
- 공격 시나리오: 직접적인 공격 경로는 없습니다. F1 DB로 `uvicorn --workers N`을 띄우면 두 워커가 모두 "열 없음"으로 보고 `ALTER`를 실행합니다. 뒤에 실행한 쪽이 `duplicate column name` OperationalError로 시작에 실패할 수 있습니다(가용성 문제).
- 수정 제안: `conn.execute("BEGIN IMMEDIATE")`로 확인과 ALTER를 한 쓰기 트랜잭션에 묶습니다. 또는 `duplicate column name` 오류를 잡아 무시합니다.

### S-5 [minor] bandit B608 2건 (오탐이지만 패턴 정리 권장)
- 위치: src/shortlink/repository.py:101, src/shortlink/repository.py:123
- 취약점: `f"SELECT {self._COLUMNS} FROM links WHERE code = ?"`에 들어가는 값은 클래스 상수(84행)라서 현재 악용할 수 없습니다. 다만 bandit 결과가 계속 Medium 2건으로 남고, 문자열을 조립하는 SQL 패턴이 코드에 남습니다.
- 공격 시나리오: 지금 당장은 없습니다. 나중에 누군가 이 패턴을 본떠 정렬 열이나 필드 이름 같은 외부 입력을 f-string에 넣으면 SQL 인젝션이 됩니다. bandit 경고에 익숙해지면 진짜 경고를 놓칠 위험도 있습니다.
- 수정 제안: 열 목록을 고정 리터럴 쿼리 상수로 만들어 씁니다(예: `_SELECT_BY_CODE = "SELECT code, url, created_at, clicks, last_accessed_at FROM links WHERE code = ?"`). 또는 근거 주석과 함께 `# nosec B608`을 붙입니다.

### S-6 [minor] 예약어 목록이 F3에서 생길 한 단계 경로를 미리 막지 않음
- 위치: src/shortlink/validation.py:25-27
- 취약점: 지금 목록은 현재 경로만 다룹니다. F3(인증, 관리 화면)에서 `/login`, `/logout`, `/keys`, `/health`, `/me`, `/account`, `/signup` 같은 경로가 생기기 전에 누구나 그 이름으로 별칭을 등록할 수 있습니다.
- 공격 시나리오:
  - 공격자가 지금 `login` 별칭을 피싱 URL로 등록해 둡니다.
  - F3 라우트를 `web.router`보다 뒤에 등록하거나 마운트로 추가하면, `https://<서비스>/login`이 공격자 페이지로 리다이렉트됩니다.
  - 앞에 등록하면 이런 하이재킹은 없지만, 기존 별칭 링크가 소리 없이 깨집니다.
- 수정 제안:
  - 예상되는 경로 이름(login, logout, signup, auth, keys, api-keys, me, account, users, health, admin 계열)을 지금 예약어에 넣습니다.
  - 한 단계 경로를 새로 만들 때는 RESERVED_ALIASES에 추가하고 `web.router`보다 먼저 등록하는 규칙을 계획 문서에 남깁니다.
  - F3 이전 단계에서 기존 코드와 겹치는지 검사합니다.

### S-7 [minor] 대소문자 구분과 혼동 문자로 다른 사람의 별칭을 사칭할 수 있음 (설계상 수용, AC-8)
- 위치: src/shortlink/validation.py:9, src/shortlink/validation.py:124
- 취약점: 설계서(AC-8)대로 `My-Bank`와 `my-bank`는 다른 별칭입니다. `l`, `I`, `1`이나 `O`, `0`처럼 생김새가 비슷한 문자로 만든 별칭도 각각 따로 등록됩니다.
- 공격 시나리오: 널리 쓰이는 별칭 `my-bank`와 대소문자만 다르거나(`My-Bank`) 생김새가 비슷한(`my-bank1`, `rny-bank`) 별칭을 피싱 URL로 등록해, 사용자가 진짜 링크로 착각하게 합니다.
- 수정 제안: 설계 범위 안에서는 기록만 해 둡니다. F3에서 검토할 것은 다음과 같습니다.
  - 대소문자를 무시한 중복 검사(`COLLATE NOCASE` 고유 인덱스) 여부를 사람이 결정합니다.
  - 리다이렉트 전에 목적지를 미리 보여 주는 화면을 둡니다.
  - 악용 신고와 삭제 기능을 둡니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)

관련 파일:
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\validation.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\repository.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\db.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\web.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\api.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\templates\stats.html
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\templates\home.html
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\templates\result.html

직접 확인할 때 쓴 임시 DB는 scratchpad에 만들었다가 바로 지웠습니다.
