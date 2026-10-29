---
seq: 13
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T06:40:09.640Z"
agent: "security"
agent_id: "aab67cfb2c1bcd0a3"
turn: 1
reply_to: 11
chars: 6546
tokens_est: 3245
wait_s: null
---

## 결과: 지적 7건 (blocker 0, major 0, minor 7)

점검 범위는 `git diff 8b7193b..92f903f`의 src/shortlink/** 전체(템플릿, static 포함)입니다. 파일은 하나도 수정하지 않았습니다. 동작 확인은 scratchpad의 임시 DB와 TestClient로만 했습니다. 확인에 쓴 스크립트는 <HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F1-human-r2\10841074-89d3-4f0b-8f60-ecaae70bc1e7\scratchpad\probe.py 입니다.

blocker나 major로 볼 문제는 없었습니다. 직접 확인한 결과는 다음과 같습니다.

**URL 검증 우회 시도**
- 모두 422로 막혔습니다: `jAvAsCrIpT:alert(1)`, `javascript://a.com/%0aalert(1)`, `http:javascript:...`, `http:\\evil.com`, 전각 `ｈttp://`, U+3000·U+0085가 든 URL, 앞에 공백이 붙은 URL.
- urlsplit이 앞쪽 C0 제어 문자를 지우고 탭·CR·LF를 빼는 동작은 문제가 되지 않습니다. 그보다 먼저 4번 검사(공백·제어 문자)가 거절하기 때문입니다.
- 스킴은 ASCII scheme_chars로만 인식되므로 유니코드로 우회할 수 없습니다.
- 짝 없는 서로게이트도 거절됩니다.

**Location 헤더 주입**
- 공백·제어 문자를 검증에서 거절하고 비ASCII 문자는 퍼센트 인코딩합니다. 그래서 헤더 값에는 출력 가능한 ASCII만 들어갑니다.
- 예: `http://a.com/é?x=<y>"'`를 넣으면 302와 `http://a.com/%C3%A9?x=<y>"'`가 나옵니다. CRLF는 들어갈 수 없습니다.

**XSS**
- 자동 이스케이프가 켜져 있습니다. Starlette Jinja2Templates가 `select_autoescape`를 써서 .html 템플릿을 이스케이프합니다.
- `|safe`와 `Markup`은 어디에도 쓰지 않습니다.
- 입력칸 value를 깨려는 `x" autofocus onfocus=alert(1)`은 `&#34;`로 이스케이프되어 속성 밖으로 나가지 못합니다.
- 원래 URL 텍스트도 이스케이프됩니다.
- 결과 화면의 `href`와 `data-copy`에는 설정값 base_url과 서버가 만든 코드만 들어갑니다. 사용자 URL은 href에 넣지 않습니다.
- copy.js는 `dataset`과 `textContent`만 써서 안전합니다.

**SQL**
- links.py:42-45의 INSERT, links.py:54-55의 SELECT 모두 `?` 바인딩을 씁니다. db.py는 고정된 DDL만 실행합니다.

**코드 생성**
- `secrets.choice`로 62자 중 7자를 뽑습니다(경우의 수 약 3.5e12, 약 41.7비트). 예측하기 어렵습니다.

**에러 응답**
- 코드 충돌이 10번 이어질 때 나는 RuntimeError, DB 오류 같은 처리되지 않은 예외는 Starlette 기본 응답인 "Internal Server Error"만 돌려줍니다. 디버그 정보는 나가지 않습니다.

**bandit**
- `uv run bandit -r src -q`는 탐지 결과 없이 exit 0으로 끝났습니다.

## 지적 목록

### S-1 [minor] 깊게 중첩된 JSON 본문을 보내면 처리되지 않은 500이 납니다
- 위치: <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\src\shortlink\api.py:28-31
- 취약점: `await request.json()`은 `ValueError`만 잡습니다. 아주 깊게 중첩된 배열(`[` 10만 개)을 보내면 json 파서가 `RecursionError`를 내고, 이는 ValueError가 아니라서 그대로 500이 됩니다. 실제로 500이 나는 것을 확인했습니다. 설계서는 본문이 JSON 객체가 아니면 422라고 정했으므로 계약과도 어긋납니다.
- 공격 시나리오: 정보는 새지 않습니다(기본 500 문구만 나감). 다만 아무나 서버 오류를 일으킬 수 있어 오류 로그가 쌓이고, 요청마다 재귀 파싱에 CPU를 씁니다.
- 수정 제안: `except (ValueError, RecursionError)`로 잡아 `MSG_NOT_OBJECT`와 422를 돌려줍니다. 본문 크기 상한(S-7)을 같이 두면 더 좋습니다.

### S-2 [minor] 웹 폼에 multipart 파일을 보내면 FastAPI 기본 422 JSON이 내부 객체 정보를 그대로 돌려줍니다
- 위치: <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\src\shortlink\web.py:39
- 취약점: `url: Annotated[str | None, Form()]`에 multipart로 파일(`files={"url": ...}`)을 보내면 핸들러에 오기 전에 FastAPI의 RequestValidationError가 납니다. 이때 `{"detail":[{"type":"string_type",...,"input":{"filename":...,"file":{"_file":{},"_max_size":1048576,"_rolled":false,"_TemporaryFileArgs":{...}}}}]}` 같은 JSON 응답이 나갑니다. 같은 키를 여러 값으로 보낸 경우도 422 JSON입니다. 결과적으로 HTML 화면 계약을 벗어나고, 서버 내부 객체의 속성(SpooledTemporaryFile 설정 등)이 응답에 담깁니다.
- 공격 시나리오: 직접 피해는 작습니다. 공격자는 이 응답으로 프레임워크와 라이브러리의 내부 구조를 알아내 핑거프린팅에 쓸 수 있습니다.
- 수정 제안: 다음 둘 중 하나를 권합니다.
  - 핸들러가 `request.form()`을 직접 읽고, 값이 `str`가 아니면 `MSG_NOT_STRING`과 함께 home.html 422를 돌려줍니다.
  - 앱 전역에 RequestValidationError 핸들러를 두어 `input` 필드를 빼고 응답합니다.

### S-3 [minor] 양방향 텍스트 제어 문자, 보이지 않는 문자, C1 제어 문자가 든 URL을 받아들여 결과 화면에서 원래 URL을 위장할 수 있습니다
- 위치: <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\src\shortlink\validation.py:47
- 취약점: 제어 문자 검사가 `isspace()`, U+0000-001F, U+007F만 봅니다. 그래서 다음 문자가 통과하는 것을 확인했습니다.
  - U+202E(RLO) 같은 양방향 텍스트 제어 문자
  - U+200B 같은 폭 없는 문자
  - U+0080-U+009F 범위의 C1 제어 문자(U+0085 제외)
  
  Location 헤더에서는 퍼센트 인코딩되므로 헤더 주입은 생기지 않습니다. 하지만 result.html:12의 원래 URL 텍스트는 화면에 그대로 렌더링됩니다.
- 공격 시나리오: `http://evil.example/\u202egnp.exe` 같은 URL을 만들면 결과 화면이나 그 화면 캡처에 다른 주소처럼 보입니다. 공격자는 이를 피싱 링크의 신뢰도를 높이는 데 쓸 수 있습니다.
- 수정 제안: 다음 문자도 MSG_INVALID_CHARS로 거절합니다.
  - `unicodedata.category(ch)`가 `Cc`, `Cf`, `Zl`, `Zp`인 문자
  - 최소한 U+0080-U+009F, U+200B-U+200F, U+202A-U+202E, U+2066-U+2069, U+FEFF
  
  정규화를 하지 않는 원칙(D-1)과도 충돌하지 않습니다. 고치는 것이 아니라 거절하는 것이기 때문입니다.

### S-4 [minor] 검증에 쓰는 urlsplit과 브라우저의 URL 해석이 백슬래시를 다르게 처리해 호스트가 어긋납니다
- 위치: <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\src\shortlink\validation.py:52-62
- 취약점: `https://good.com\@evil.com`을 넣으면 urlsplit은 hostname을 `evil.com`으로 봅니다. 브라우저(WHATWG URL)는 http(s)에서 `\`를 `/`로 처리하므로 실제 이동하는 곳은 `good.com`입니다. `http://\evil.com`도 통과합니다(urlsplit의 hostname은 `\evil.com`). 지금은 호스트 허용·차단 정책이 없어서 바로 악용할 수는 없습니다.
- 공격 시나리오: 앞으로 F3 등에서 도메인 차단 목록이나 자기 도메인 루프 차단을 urlsplit의 hostname으로 구현하면 이 차이로 우회할 수 있습니다.
- 수정 제안: 다음 중 하나를 권합니다.
  - 지금 단계에서 authority 부분(`//` 뒤 첫 `/?#` 전)에 `\`가 있으면 거절합니다.
  - 호스트 기반 정책을 넣을 때 WHATWG 방식의 파서를 씁니다.
  
  어느 쪽이든 회귀 테스트에 이 두 사례를 넣어 두기를 권합니다.

### S-5 [minor] 보안 응답 헤더가 없습니다
- 위치: <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\src\shortlink\main.py:30-40 (미들웨어 없음), web.py의 각 HTMLResponse
- 취약점: HTML 응답에 `Content-Security-Policy`, `X-Frame-Options`(또는 CSP `frame-ancestors`), `X-Content-Type-Options: nosniff`, `Referrer-Policy`가 없습니다. 지금은 이스케이프가 올바르게 되어 있어서 XSS 경로는 찾지 못했습니다.
- 공격 시나리오: 공격자가 홈 화면을 iframe에 넣어 클릭재킹을 할 수 있습니다. 나중에 템플릿에서 이스케이프가 하나라도 빠지면 그것을 막아 줄 2차 방어선이 없습니다.
- 수정 제안: 간단한 미들웨어로 다음 헤더를 붙입니다. `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`(또는 `strict-origin`). 지금 인라인 스크립트가 없어서 `script-src 'self'`로 충분합니다.

### S-6 [minor, 기록용·F3 범위] 서비스 자신을 가리키는 URL과 오픈 리다이렉트 악용
- 위치: <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\src\shortlink\web.py:65-73, validation.py:59-62
- 취약점: http(s) URL이면 대상을 가리지 않습니다. 이는 URL 단축 서비스의 본래 기능입니다. 다만 `SHORTLINK_BASE_URL` 자체를 가리키는 URL도 받아들여서 단축 링크끼리 서로 가리키는 리다이렉트 루프나 사슬을 만들 수 있습니다.
- 공격 시나리오: 공격자는 단축 링크를 여러 겹 감싸 최종 피싱 주소를 숨길 수 있고, 링크 A와 B를 서로 가리키게 해 무한 리다이렉트를 만들 수 있습니다.
- 수정 제안: 이번 기능 범위 밖이므로 기록만 합니다. 이후에 base_url 호스트를 대상으로 하는 URL을 거절하는 방안을 검토하기를 권합니다. 이때 S-4의 파싱 차이를 같이 고려해야 합니다. 필요하면 도메인 차단 목록도 함께 검토합니다.

### S-7 [minor, 기록용·F3 범위] 인증, 요청 수 제한, 본문 크기 제한, CSRF 대책이 없습니다
- 위치: <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\src\shortlink\api.py:19-38, web.py:35-54
- 취약점: 다음이 모두 없습니다.
  - `POST /links`와 `POST /`의 인증과 요청 수 제한
  - 요청 본문 크기 상한. 길이 검사(2,048자)는 본문을 다 파싱한 뒤에 합니다.
  - 폼의 CSRF 토큰
  
  또한 `/links`는 Content-Type을 확인하지 않아서 다른 사이트의 `text/plain` 폼 제출로도 링크가 만들어집니다.
- 공격 시나리오: 공격자가 대량 생성으로 DB를 키우거나, 아주 큰 본문으로 메모리와 CPU를 쓰게 할 수 있습니다. 지금은 인증이 없어서 CSRF로 생기는 실질 피해는 없습니다.
- 수정 제안: 설계서상 F3 범위이므로 기록만 합니다. F3에서 다음을 넣기를 권합니다.
  - 요청 수 제한
  - 본문 크기 상한(예: 8KB, 서버 설정이나 미들웨어)
  - `/links`가 `application/json`만 받도록 확인
  - 인증을 넣을 때 폼에 CSRF 토큰이나 SameSite 쿠키 적용
