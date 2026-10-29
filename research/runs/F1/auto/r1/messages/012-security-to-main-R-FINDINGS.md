---
seq: 12
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T04:47:39.165Z"
agent: "security"
agent_id: "a184f4afb29f737c5"
turn: 1
reply_to: 10
chars: 5914
tokens_est: 2773
wait_s: null
---

## 결과: 지적 6건 (blocker 0, major 0, minor 6)

F1(체크포인트 62a0bf3)에서 blocker나 major는 나오지 않았습니다. 6건 모두 minor입니다. 그중 S-1은 실제로 재현했습니다. JSON 본문에 lone surrogate(`\ud800`)가 든 URL을 보내면 500 오류가 납니다.

점검 방법:
- `uv run bandit -r src -q`를 실행했고 지적은 0건입니다(종료 코드 0).
- 의존성 파일 `pyproject.toml`과 `uv.lock`은 이번 변경분(0e781ba..62a0bf3)에서 바뀌지 않았습니다.
- TestClient로 동작을 확인했습니다. 프로브 스크립트는 `<HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F1-auto-r1\596f5b0b-4686-4b10-a66a-5c1df0187553\scratchpad\probe.py`에 두었습니다. DB도 이 폴더에 만들었고 확인 뒤 지웠습니다. 저장소 파일은 수정하지 않았습니다.

문제가 없는 항목:
- SQL 인젝션: `links.py`의 INSERT와 SELECT, `db.py`의 스키마 생성 모두 `?` 바인딩을 씁니다. 코드 자리에 `' OR 1=1--`를 넣어도 404만 돌아옵니다.
- XSS:
  - `Jinja2Templates`의 autoescape가 켜져 있습니다. Starlette 기본값인 `select_autoescape`가 `.html`에 적용됩니다.
  - `|safe`와 `Markup`을 쓰는 곳은 없습니다.
  - `href`에는 `short_url`(base_url과 서버가 만든 코드)만 들어가고, 원래 URL은 텍스트로만 표시됩니다.
  - `value="{{ value }}"` 속성에서도 따옴표가 이스케이프됩니다. `"><script>`를 넣어 봤지만 결과 화면과 오류 화면 모두 원문 태그가 나오지 않았습니다.
  - `copy.js`는 `dataset.copy`를 클립보드에 쓰기만 하고 DOM에 넣지 않습니다.
- 스킴 검증: `urlsplit` 결과의 스킴을 http/https 허용 목록으로 확인합니다. 제어 문자와 공백을 먼저 거절하므로, 앞쪽 공백을 이용한 우회(`" javascript:"`)도 막힙니다.
- 헤더 주입: CR/LF와 제어 문자는 `validation.py:36`에서 거절됩니다. `RedirectResponse`는 비ASCII를 퍼센트 인코딩합니다(D-3). 이미 `%0d%0a`로 인코딩된 값은 그대로 나가지만 헤더를 끊지는 않습니다.
- 코드 예측성: `secrets.choice`로 62^7(약 3.5조) 공간에서 고릅니다.
- 정보 노출: 처리되지 않은 예외는 FastAPI 기본값대로 본문 `Internal Server Error`만 돌아오고 스택은 노출되지 않습니다(debug 꺼짐).
- 정적 파일: `StaticFiles`가 경로 탈출을 막습니다.

## 지적 목록

### S-1 [minor] 유니코드 surrogate가 든 URL을 보내면 500 오류
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\validation.py:36`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\links.py:53-56`
- 취약점: JSON 문자열의 `\ud800` 같은 짝 없는 surrogate는 Python str로 그대로 들어옵니다. `validate_url`은 이것을 통과시키고, sqlite3에 바인딩할 때 `UnicodeEncodeError: surrogates not allowed`가 납니다. 처리되지 않으므로 500이 됩니다. 재현: `{"url":"https://a.com/\ud800"}`를 보내면 500 Internal Server Error가 돌아옵니다. 저장은 되지 않고 내부 정보도 노출되지 않습니다.
- 공격 시나리오: 인증 없이 누구나 500을 계속 일으킬 수 있습니다. 그러면 오류 로그가 넘치고 모니터링 경보가 오작동합니다. 설계서는 이런 입력을 422로 거절하라고 하는데 그렇게 되지 않습니다.
- 수정 제안: `validate_url`에 `value.encode("utf-8")` 시도를 넣고, `UnicodeEncodeError`가 나면 422 `InvalidURLError`로 바꿉니다. 또는 U+D800–U+DFFF가 든 값을 거절합니다. 회귀 테스트도 하나 추가합니다.

### S-2 [minor] 표시를 속이는 유니코드 문자 허용(bidi 제어, C1 제어, 줄 구분자)
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\validation.py:36`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\templates\result.html:14`
- 취약점: D-2는 C0 제어 문자와 U+007F만 막습니다. 다음 문자들은 저장되고 결과 화면에 표시됩니다.
  - U+202E(RLO) 같은 bidi 제어 문자
  - U+0080–U+009F(C1 제어, 예: U+0085 NEL)
  - U+2028/U+2029
  - 그 밖의 유니코드 공백(U+00A0, U+3000 등)

  `Location`에서는 퍼센트 인코딩되므로 헤더 주입은 없습니다(확인: `%E2%80%AE`, `%C2%85`).
- 공격 시나리오: `https://a.com/\u202egpj.exe`처럼 만들면 결과 화면의 "원래 URL"이 `exe.jpg`처럼 뒤집혀 보입니다. 사용자가 링크 목적지를 잘못 믿게 됩니다. 영향은 표시를 속이는 데 그칩니다.
- 수정 제안: D-2의 거절 범위를 넓힙니다. 대상은 C1(0x80–0x9F), `unicodedata.category`가 `Cf`/`Zl`/`Zp`/`Zs`인 문자, 또는 최소한 bidi 제어 문자(U+200E/F, U+202A–U+202E, U+2066–U+2069)입니다. 넓힐 경우 결정 기록 D-2도 함께 갱신합니다.

### S-3 [minor] 오픈 리다이렉트 악용 방지 장치 없음(자기 참조 루프, userinfo 위장)
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\web.py:54`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\validation.py:50-54`
- 취약점: 단축 서비스는 원래 리다이렉트가 기능입니다. 하지만 다음을 막는 장치가 없습니다.
  - 목적지가 서비스 자신(`Settings.base_url` 호스트)인 링크
  - userinfo가 든 URL(`https://user:<EMAIL>/`)
  - 백슬래시가 든 URL. `https://good.com\@evil.com/`은 `https://<EMAIL>/`으로 나가고 브라우저는 호스트를 `evil.com`으로 해석합니다.
- 공격 시나리오:
  - 단축 URL끼리 서로 가리키게 만들어 리다이렉트 루프를 만들 수 있습니다. 서비스 도메인의 신뢰를 이용해 단축을 여러 겹 감싸 목적지를 숨길 수도 있습니다.
  - `https://<EMAIL>/` 형태로 피싱 목적지를 신뢰할 만한 도메인처럼 보이게 할 수 있습니다.
- 수정 제안(F1 범위 밖 정책 사항이라 기록만 함):
  - `hostname`이 base_url 호스트와 같으면 거절합니다.
  - `parts.username`/`parts.password`가 있거나 `\`가 든 URL은 거절합니다.
  - 이후 도메인 차단 목록을 도입하는 것을 검토합니다.

### S-4 [minor] 인증, 요청 수 제한, 요청 본문 크기 제한 없음(F3 범위)
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\api.py:23`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\web.py:31`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\web.py:48-51`
- 취약점:
  - `POST /links`와 `POST /`는 인증과 요청 수 제한이 없습니다.
  - `request.json()`과 폼 파싱은 본문 전체를 메모리에 읽은 뒤에야 2,048자 검사를 합니다.
  - `GET /{code}` 조회에도 요청 수 제한이 없습니다.
- 공격 시나리오:
  - 자동화로 링크를 대량 생성해 SQLite 파일을 계속 키울 수 있습니다.
  - 수 MB에서 수백 MB짜리 JSON 본문으로 메모리와 CPU를 소모시킬 수 있습니다.
  - 코드 공간을 무작위로 대입할 수 있습니다. 공간이 커서 실효성은 낮습니다.
- 수정 제안: F3에서 다음을 다룹니다.
  - API 키 인증. 비교는 `secrets.compare_digest`로 합니다.
  - IP나 키 단위 요청 수 제한
  - 리버스 프록시나 미들웨어로 본문 크기 상한(예: 16KB)

### S-5 [minor] 보안 응답 헤더 없음
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\main.py:28-37`
- 취약점: `GET /` 응답 헤더는 `content-type`과 `content-length`뿐입니다. 다음 헤더가 없습니다.
  - CSP
  - `X-Frame-Options` 또는 `frame-ancestors`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy`
- 공격 시나리오:
  - 다른 사이트가 폼 화면을 iframe으로 감싸 클릭재킹할 수 있습니다. 영향은 링크 생성 유도 정도로 낮습니다.
  - 앞으로 이스케이프 실수가 생겼을 때 막아 줄 2차 방어선이 없습니다.
- 수정 제안: 응답 헤더를 넣는 미들웨어를 추가합니다.
  - 스크립트가 외부 파일 `copy.js` 하나뿐이고 인라인 스크립트가 없으므로 `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`를 그대로 적용할 수 있습니다.
  - 여기에 `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`(또는 `strict-origin`)를 더합니다.

### S-6 [minor] API 문서 엔드포인트가 공개됨
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\main.py:30`
- 취약점: `FastAPI(title="ShortLink")`의 기본 설정 때문에 `/docs`, `/redoc`, `/openapi.json`이 200으로 열려 있습니다. `/docs`는 외부 CDN 스크립트를 불러옵니다. 코드는 7자라서 `GET /{code}`와 경로가 겹치지는 않습니다.
- 공격 시나리오: 공격자가 API 구조를 쉽게 파악합니다. 외부 CDN에 의존하므로 S-5의 CSP 적용과도 충돌합니다.
- 수정 제안: 운영 환경에서는 `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)`로 끄거나 설정값으로 제어합니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음(1라운드)
