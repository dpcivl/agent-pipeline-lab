---
seq: 13
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T02:24:18.628Z"
agent: "security"
agent_id: "a0411bab91b1e0f90"
turn: 1
reply_to: 11
chars: 5862
tokens_est: 2870
wait_s: null
---

## 결과: 지적 5건 (blocker 0, major 0, minor 5)

F1 범위 안에서 원격으로 악용할 수 있는 취약점(blocker, major)은 찾지 못했습니다. 5건은 모두 방어를 강화하자는 minor 제안입니다. `uv run bandit -r src -q` 결과는 0건(exit 0)이고, 대상은 `git diff 7c88212..62afa74 -- src` 전체입니다. 위험 입력은 TestClient로 실제 요청을 보내 확인했고, 확인용 스크립트는 scratchpad에만 두었습니다. 저장소 파일은 하나도 수정하지 않았습니다.

### 확인한 결과 문제없는 항목
- **위험 스킴**: `javascript:`, `JaVaScRiPt://`, `data:`, `https:\\evil.com`, `https:/evil.com`, `https:evil.com`, `http://[::1`, `https://@/`, `https://:80`, 앞쪽 공백이 붙은 URL은 모두 422로 거절됩니다. 같은 이름의 폼 필드를 두 번 보내도(`url=https://a.com&url=javascript:…`) 마지막 값이 검증되어 422가 납니다. Starlette `RedirectResponse`는 `quote(url, safe=":/%#?=@[]!$&'()*+,;")`만 적용하고 스킴은 바꾸지 않으므로 `Location`으로 나가는 값은 항상 http/https입니다.
- **결과 화면 링크**: `href`와 `data-copy`에는 사용자 URL이 들어가지 않습니다. `base_url`(설정값)과 코드(영숫자 7자)로 만든 단축 URL만 들어가고, 원래 URL은 텍스트로만 표시됩니다.
- **CRLF 주입(D-3, D-7)**: `\r\n`, `\x00`, U+2028은 `_is_blocked_char`에서 422로 거절됩니다. 이미 인코딩된 `%0d%0a`는 문자열 그대로 나가서 헤더가 갈라지지 않습니다. 비ASCII 문자는 `Location`에서 퍼센트 인코딩됩니다(`é` → `%C3%A9`, `한글` → `%ED%95%9C…`).
- **템플릿 이스케이프**: `web.templates.env.autoescape`는 `select_autoescape()`라서 `.html` 템플릿에 켜져 있습니다. `"`, `'`, `<`가 `value`, 본문, `href`, `data-copy`에서 모두 `&#34;`, `&#39;`, `&lt;`로 바뀌는 것을 결과 화면과 오류 화면에서 확인했습니다. `|safe`와 `Markup`은 어디에도 없습니다. `copy.js`는 `getAttribute`와 `textarea.value`만 쓰고 `innerHTML`은 쓰지 않습니다.
- **SQL**: `repository.py:66`, `:78`, `:87`은 모두 `?` 파라미터 바인딩이거나 고정 쿼리입니다.
- **500 응답**: 코드 생성 재시도 실패를 일부러 일으켜 보니 `Internal Server Error`(text/plain, 21바이트)만 나가고 스택 트레이스는 담기지 않았습니다(debug 꺼짐).
- **기타**: `/static/../main.py`와 `/static/%2e%2e/main.py`는 404입니다. 404 화면에 요청 코드가 다시 출력되지 않습니다. 코드는 `secrets`로 생성됩니다. 단축 URL은 Host 헤더가 아니라 `Settings.base_url`로 만듭니다.
- **의존성(uv.lock)**: fastapi 0.162.0, starlette 1.10.0, jinja2 3.1.6, python-multipart 0.0.32, pydantic 2.14.1, uvicorn 0.54.0, h11 0.16.0. 제가 아는 알려진 취약 버전 범위에는 해당하지 않습니다.

## 지적 목록

### S-1 [minor] 요청 본문 크기 제한이 없고, 422 응답이 입력 전체를 다시 돌려줌
- 위치: `src/shortlink/main.py:32`(본문 크기 제한 없음), `src/shortlink/schemas.py:10-21`(FastAPI 기본 422 응답의 `input` 필드), `src/shortlink/templates/home.html:15`와 `src/shortlink/web.py:49-51`(너무 긴 입력도 `value`에 그대로 넣음)
- 취약점: 2,048자 검사는 본문을 메모리에 모두 읽은 뒤에야 실행됩니다. 422 응답에는 받은 값이 통째로 다시 담깁니다. 30MB JSON을 보내면 30,000,143바이트짜리 422 응답이 돌아오고, 900KB 폼을 보내면 901,102바이트짜리 HTML이 돌아오는 것을 확인했습니다. 폼 필드는 1MB를 넘으면 400으로 끊기지만 JSON에는 이런 상한이 없습니다.
- 공격 시나리오: 인증 없는 공격자가 수백 MB짜리 JSON을 `POST /links`로 반복해서 보냅니다. 서버는 본문, 파싱 결과, 응답 사본을 모두 메모리에 올려야 하므로 메모리와 대역폭이 고갈됩니다. 요청 수 제한은 F3 범위지만, 요청 한 건의 크기 상한은 이와 별개 문제입니다.
- 수정 제안: 미들웨어나 리버스 프록시에서 본문 크기에 상한을 둡니다(예: 16KB 초과면 413). 이와 함께 422 응답에서 `input`을 빼거나 잘라서 보내고, 2,048자 초과로 거절된 경우에는 화면의 `value`를 비우거나 앞부분만 남깁니다.

### S-2 [minor] `POST /`에 multipart 파일을 보내면 422 JSON에 내부 객체 구조가 드러남
- 위치: `src/shortlink/web.py:43`(`url: Annotated[str, Form()]`)
- 취약점: `url` 필드를 파일로 보내면 FastAPI 기본 422 JSON 응답이 나갑니다. HTML 화면이 아닙니다. 이 응답의 `input`에 UploadFile 내부 상태(`_max_size`, `_rolled`, `_TemporaryFileArgs`, `_max_mem_size`, 파트 헤더)가 그대로 직렬화됩니다. API 쪽 422에도 의미 없는 `"ctx":{"error":{}}`가 붙습니다.
- 공격 시나리오: 경로나 비밀값이 새지는 않습니다. 다만 프레임워크 종류와 내부 설정(스풀 임계값 1MB)을 알아내는 데 쓰일 수 있습니다. 또 웹 경로에서 HTML이 아닌 응답이 나가므로 422 화면 응답 형식도 일관되지 않습니다.
- 수정 제안: `RequestValidationError` 처리기를 등록해 `input`과 `ctx`를 빼고 `loc`, `msg`, `type`만 남깁니다. 웹 경로는 form을 직접 읽어 `str`이 아닌 값을 `MSG_NOT_STRING`이 담긴 422 HTML로 돌려줍니다.

### S-3 [minor] `/docs`, `/redoc`, `/openapi.json`이 누구에게나 공개됨
- 위치: `src/shortlink/main.py:32`(`FastAPI(title="ShortLink")`)
- 취약점: 세 경로 모두 200을 돌려줘 API 구조 전체가 노출됩니다. Swagger UI는 외부 CDN에서 스크립트를 불러옵니다.
- 공격 시나리오: 지금 F1에서는 영향이 작습니다. 하지만 F3에서 인증·삭제 API가 추가되면 공격자가 노릴 엔드포인트를 쉽게 찾을 수 있습니다.
- 수정 제안: 설정값에 따라 `docs_url=None, redoc_url=None, openapi_url=None`으로 끄는 방안을 검토합니다. 공개를 유지한다면 그 결정을 `docs/plans`에 기록합니다.

### S-4 [minor] 보안 응답 헤더가 없음
- 위치: `src/shortlink/main.py:30-40`(미들웨어 없음). `GET /` 응답 헤더는 `content-length`와 `content-type`뿐입니다.
- 취약점: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `frame-ancestors`(또는 `X-Frame-Options`), `Referrer-Policy`가 없습니다. 템플릿 자동 이스케이프가 유일한 XSS 방어선입니다. 참고로 `select_autoescape()`는 확장자 기준이라 `.html`이 아닌 템플릿을 추가하면 자동 이스케이프가 꺼집니다.
- 공격 시나리오: 나중에 이스케이프가 빠지는 회귀가 생기면 그대로 XSS로 이어집니다. 다른 사이트가 폼 화면을 iframe에 넣는 클릭재킹도 가능합니다.
- 수정 제안: 인라인 스크립트가 없으므로 `default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'` 같은 엄격한 CSP를 바로 적용할 수 있습니다. 여기에 `nosniff`, `Referrer-Policy: no-referrer`(또는 `strict-origin`)를 미들웨어로 붙입니다.

### S-5 [minor] 보이지 않는 문자와 형식 문자(Cf), 전각 호스트, 잘못된 포트가 검증을 통과함
- 위치: `src/shortlink/validation.py:26-29`, `:62-66`
- 취약점: U+200B(폭 없는 공백), U+202E(RLO, 오른쪽에서 왼쪽 표시 강제), U+FEFF는 `isspace()`가 거짓이라 201로 저장됩니다. `https://ｅｖｉｌ.com`(전각 문자)도 저장되는데, 브라우저는 이 호스트를 `evil.com`으로 바꿔 해석합니다. `http://a.com:99999999/`도 저장되는데, 이때 `urlsplit(...).port`를 읽으면 ValueError가 납니다.
- 공격 시나리오: 결과 화면과 JSON의 `url`은 생성한 본인에게만 보이므로 지금은 영향이 작습니다. 하지만 이후 기능에서 원래 URL을 다른 사람에게 보여 주게 되면, RLO나 전각 문자로 실제 목적지를 다르게 보이게 하는 표시 위장에 쓰일 수 있습니다.
- 수정 제안: `unicodedata.category(ch) == "Cf"`인 문자를 D-3 거절 대상에 추가하는 방안을 검토합니다. 호스트는 `parts.port` 접근까지 try 안에 넣어 잘못된 포트를 422로 거절합니다. 전각과 IDN 호스트를 어떻게 다룰지는 결정 기록에 남깁니다.

### 범위 밖 참고 (심각도 없음)
- **오픈 리다이렉트**: 임의의 http(s) 호스트로 302를 보내는 것은 단축 서비스의 본래 기능이라 결함으로 보지 않았습니다. 피싱 도메인 차단, 경고 중간 페이지, 다른 단축 링크를 가리키는 링크(리다이렉트 체인) 제한은 이후 정책 과제입니다.
- **CSRF**: `POST /`에 CSRF 토큰이 없습니다. 지금은 인증이 없어 피해가 없지만, F3에서 인증과 세션이 들어오면 토큰이나 SameSite 쿠키가 필요합니다.
- **대량 생성과 요청 수 제한, 인증과 소유권, 별칭 규칙**: F2·F3 범위입니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)

관련 경로: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-default-r2\src\shortlink\validation.py`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-default-r2\src\shortlink\web.py`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-default-r2\src\shortlink\main.py`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-default-r2\src\shortlink\schemas.py`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-default-r2\src\shortlink\templates\home.html`
