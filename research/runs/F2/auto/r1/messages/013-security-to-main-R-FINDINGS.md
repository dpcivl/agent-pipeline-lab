---
seq: 13
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T07:21:34.617Z"
agent: "security"
agent_id: "a07e766323a926f72"
turn: 1
reply_to: 10
chars: 3877
tokens_est: 2060
wait_s: null
---

## 결과: 지적 2건 (blocker 0, major 0, minor 2)

F2 보안 점검 1라운드 결과, blocker와 major는 없습니다. 방어 강화 제안 2건만 냈습니다. 대상은 `git diff 4cf5823..34689f1`의 src 변경 전체입니다. 파일은 하나도 고치지 않았습니다. 동적 점검은 scratchpad의 임시 DB를 TestClient에 연결해서만 했습니다. 실행한 스크립트는 <HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F2-auto-r1\72a36773-a2c4-4e3a-8b68-3622c6f595d2\scratchpad\probe2.py 입니다.

### 문제없음으로 확인한 항목

- **bandit:** `uv run bandit -r src -q`에서 발견된 문제가 0건입니다(exit 0).
- **별칭 문자 규칙:** 모두 422로 거절됩니다.
  - 확인한 입력: `"abcd\n"`, `"abcd "`, `"abéd"`, 전각 `"ａbcd"`, `"abcı"`, `"abc/d"`, `"..ab"`, `"abcd%0a"`, 짝 없는 서로게이트 `"\ud800abc"`(raw JSON)
  - `re.fullmatch(r"[A-Za-z0-9-]+")`를 써서 `$` 뒤 줄바꿈 우회가 통하지 않습니다. 정규화를 하지 않아 공백이나 줄바꿈이 코드에 섞일 수 없습니다.
  - 서로게이트도 문자 규칙에서 막히므로, F1의 M-1과 같은 500이 별칭 쪽에서는 재발하지 않습니다.
- **예약어:** 대소문자를 무시하고 비교합니다(`ADMIN`, `Stats`, `docs`는 422).
  - `/stats/{code}`는 경로 구간이 2개라 `/{code}`와 겹치지 않습니다. API 라우터가 먼저 등록되고 `/{code}`는 맨 마지막입니다.
  - 따라서 지금 있는 라우트를 별칭이 가리는 경우는 없습니다.
- **별칭이 경로·헤더·HTML에 들어가는 경우:** 별칭이 ASCII `[A-Za-z0-9-]`만 허용해 헤더나 경로 주입 여지가 없습니다.
  - `short_url`은 운영자 설정 `base_url`에 DB의 코드를 붙여 만듭니다.
  - 결과 화면의 `href="/stats/{{ code }}"`도 검증된 코드라 안전합니다.
- **XSS:** 자동 이스케이프가 동작하고 `|safe`나 `Markup`은 쓰지 않습니다.
  - 통계 화면 원래 URL `https://e.com/<script>"'`는 `&lt;script&gt;&#34;&#39;`로 출력됩니다.
  - 오류 화면에서 다시 채워 주는 별칭 `"><img src=x>`는 `value="&#34;&gt;&lt;img src=x&gt;"`로 출력됩니다.
  - 통계 화면은 원래 URL을 링크(`href`)가 아니라 텍스트로만 보여 주므로 위험한 스킴이 들어갈 자리가 없습니다.
- **SQL:** INSERT(alias), SELECT, UPDATE 모두 `?` 바인딩입니다. 마이그레이션의 `PRAGMA table_info(links)`와 `ALTER TABLE ... ADD COLUMN` 2개는 상수 문자열이고 외부 값을 끼워 넣지 않습니다.
- **409/404 응답:** 고정 문구만 담고 내부 정보는 없습니다.
  - 409는 별칭이 이미 있다는 사실을 알려 주지만, `GET /{alias}`로도 같은 것을 알 수 있어 새로 노출되는 정보가 아닙니다.
  - 5000자 코드로 통계 API를 불러도 404 JSON으로 정상 처리됩니다.
- **클릭 집계:**
  - 통계 API·화면 조회와 404는 클릭을 세지 않습니다.
  - `HEAD /{code}`, `OPTIONS /{code}`는 405라 클릭이 늘지 않습니다(조회 결과 clicks=0 유지).
  - 증가는 UPDATE 한 문장으로 원자적이고, 다시 읽기도 같은 트랜잭션 안에서 합니다.
- **보안 헤더(F1 D-10):** 새 응답에도 붙습니다.
  - `/stats/{code}`(200과 404), 폼의 409·422 HTML 화면에는 CSP와 nosniff가 모두 붙습니다.
  - `/links/{code}/stats` JSON(200과 404)과 409 JSON에는 nosniff가 붙습니다.

## 지적 목록

### S-1 [minor] 예약어 목록이 앞으로 생길 한 단계 경로를 미리 막지 않음
- 위치: `src/shortlink/validation.py:83`
- 취약점: 예약어가 설계서의 9개뿐입니다. F3에서 인증·관리 경로(`login`, `logout`, `signup`, `keys`, `health` 같은 이름)가 생기면 그전에 같은 이름으로 만든 별칭과 충돌합니다.
- 공격 시나리오:
  - 지금 순서(`web.router` 맨 마지막)를 지키면, 새 고정 라우트가 이기고 그 별칭 링크는 영영 열리지 않습니다(기존 사용자 링크가 깨짐).
  - 등록 순서를 실수로 바꾸면 반대로 공격자가 미리 선점한 별칭(`/login` 등)이 서비스 경로를 가로채 피싱 페이지로 보낼 수 있습니다.
  - 지금 당장 악용할 수는 없습니다.
- 수정 제안:
  - F3 설계 때 쓸 경로 이름을 정해 예약어에 미리 넣습니다. 설계서가 목록을 고정하고 있으므로 결정 기록(E-2 보완)으로 남기는 것이 좋습니다.
  - "고정 라우트는 `/{code}`보다 먼저 등록한다"는 순서를 테스트로 고정할 것도 권합니다. 지금은 `main.py:41`의 주석뿐입니다.

### S-2 [minor] 리다이렉트(GET)가 이제 DB 쓰기를 하는데 요청 수 제한이 없어 클릭 부풀리기와 쓰기 경합이 가능함
- 위치: `src/shortlink/web.py:160`, `src/shortlink/repository.py:111-127`, `src/shortlink/db.py:21`
- 취약점: F2부터 모든 `GET /{code}`가 `record_click()` 안에서 UPDATE 트랜잭션을 엽니다.
  - 없는 코드도 UPDATE를 실행하므로 쓰기 잠금을 잡습니다.
  - 인증 없는 GET이 그대로 SQLite 쓰기가 되며, 요청 수 제한·중복 제거·busy timeout 조정·WAL 설정이 없습니다(기본 `sqlite3.connect`, timeout 5초).
- 공격 시나리오:
  - (a) 누구나 같은 코드를 반복 요청해 clicks를 마음대로 부풀릴 수 있습니다. 링크 미리보기 봇의 요청도 클릭으로 셉니다.
  - (b) 임의 경로로 GET을 대량으로 보내면 쓰기 잠금 경합이 생기고, 심하면 `database is locked`로 500이 나서 링크 생성과 리다이렉트가 함께 막힐 수 있습니다.
- 수정 제안:
  - 근본 대책인 요청 수 제한은 F3 범위입니다(F1 S-2를 F3로 넘긴 기록이 있음). 다만 F2에서 GET이 쓰기가 된 점을 F3 위험 목록에 덧붙여 기록합니다.
  - 당장 할 수 있는 완화책은 두 가지입니다.
    - `connect()`에서 `PRAGMA journal_mode=WAL`을 켜고 timeout을 명시합니다.
    - `record_click`을 SELECT로 존재를 확인한 뒤 있을 때만 UPDATE하게 바꿔, 없는 코드는 쓰기 잠금을 잡지 않게 합니다. 이때도 증가는 지금처럼 한 문장 UPDATE로 원자성을 유지해야 합니다.
  - 클릭 수는 신뢰할 수 있는 지표가 아니라는 점(중복 제거 없음)을 문서에 적어 두는 것도 권합니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)

참고로 별칭이 대소문자를 구분해서 `MyBrand`와 `mybrand`처럼 비슷한 별칭을 만들 수 있지만, 설계서 AC-8이 정한 동작이라 지적하지 않았습니다. 통계 공개 범위도 E-13에 따라 지적하지 않았습니다.
