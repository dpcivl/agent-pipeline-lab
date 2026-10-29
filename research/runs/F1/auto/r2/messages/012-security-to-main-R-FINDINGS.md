---
seq: 12
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T05:17:12.436Z"
agent: "security"
agent_id: "a66ac9b4e9288e49c"
turn: 1
reply_to: 10
chars: 5509
tokens_est: 2703
wait_s: null
---

## 결과: 지적 5건 (blocker 0, major 1, minor 4)

대상은 `git diff e8f75ad..166f2b6`입니다(src/shortlink/ 전체와 템플릿, static/copy.js). 원격에서 악용할 수 있는 취약점(blocker)은 찾지 못했습니다. bandit은 `uv run bandit -r src -q`로 실행하면 Windows 애플리케이션 제어 정책(os error 4551)이 실행 파일을 차단합니다. 그래서 `uv run python -m bandit -r src -q`로 돌렸고, 출력 없이 exit 0으로 지적이 없었습니다. 직접 확인할 때는 scratchpad의 스크립트에서 TestClient를 썼고, 저장소 파일은 하나도 수정하지 않았습니다.

## 지적 목록

### S-1 [major] 짝 없는 서로게이트 문자가 검증을 통과해 500 발생
- 위치: C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/validation.py:37 (검증 누락), C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/storage.py:53 (예외 발생 지점), C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/api.py:30-33
- 취약점: JSON 이스케이프 `\ud800`은 `json.loads`를 거치면 짝 없는 서로게이트가 됩니다. `validate_url`은 이 문자를 거르지 않습니다. 그 뒤 sqlite3가 INSERT하면서 UTF-8로 인코딩하다가 `UnicodeEncodeError: surrogates not allowed`를 냅니다. 이 예외는 처리되지 않습니다. 확인 결과 `{"url": "http://a.com/\ud800"}`와 `{"url": "http://\ud800.com/"}` 모두 500이었습니다. 저장된 행은 0건이고, 응답 본문은 일반적인 "Internal Server Error"뿐이라 내부 정보는 나가지 않습니다. 같은 값이 다른 경로로 저장되더라도 `web.py:22`의 `quote(char)`와 JSONResponse 인코딩에서 다시 500이 납니다. 웹 폼에서는 재현되지 않았습니다. urlencoded 값은 대체 문자(U+FFFD)로, multipart 값은 latin-1로 대체 디코딩되기 때문입니다.
- 공격 시나리오: 인증 없이 누구나 이 요청 하나로 500을 반복해서 일으킬 수 있습니다. 오류 로그와 모니터링을 오염시킬 수 있고, D-8이 막으려던 "검증 중 예외로 500"과 같은 종류의 구멍입니다. 데이터가 오염되거나 정보가 새지는 않습니다.
- 수정 제안: `validate_url`에서 `value.encode("utf-8")`을 시도하고, `UnicodeEncodeError`가 나면 422로 거절합니다(예: "URL에 쓸 수 없는 문자가 있습니다."). 또는 문자 검사 루프에 `0xD800 <= ord(char) <= 0xDFFF` 조건을 더합니다. API와 웹 양쪽의 회귀 테스트도 추가합니다.

### S-2 [minor] 깊게 중첩된 JSON 본문이 RecursionError로 500
- 위치: C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/api.py:23-26
- 취약점: `request.json()`이 `[`를 20만 개 이어 붙인 본문이나 `{"a":`를 반복한 본문을 받으면 `RecursionError`를 냅니다. `RecursionError`는 `ValueError`의 하위 클래스가 아니어서 `except ValueError`에 잡히지 않고 500이 됩니다. 응답은 일반 500이라 정보 노출은 없습니다.
- 공격 시나리오: 인증 없이 작은 본문으로 500을 반복해서 일으킬 수 있습니다. 서버가 죽지는 않습니다.
- 수정 제안: `except (ValueError, RecursionError)`로 바꿔 D-9 문구와 함께 422로 돌려줍니다. 장기적으로는 본문 크기 상한(S-4)과 함께 다룹니다.

### S-3 [minor] C1 제어 문자와 유니코드 서식 문자(양방향 제어 등)를 허용
- 위치: C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/validation.py:37
- 취약점: D-2는 U+0000~U+001F, U+007F, `isspace()`만 막습니다. 그래서 U+0080~U+009F(U+0085는 isspace라 거절됨), U+202E(RLO), U+200B(경로 안), U+00AD(소프트 하이픈) 같은 Cc/Cf 문자가 통과합니다. `Location` 헤더에서는 퍼센트 인코딩되므로(예: `%C2%9B`) 헤더 주입은 생기지 않습니다. 문제는 결과 화면(`result.html:15`)과 API 응답의 `url`에 이 문자들이 그대로 표시된다는 점입니다.
- 공격 시나리오: 공격자가 RLO 같은 양방향 제어 문자로 "원래 URL" 표시를 뒤집어 다른 목적지처럼 보이게 하고, 그 단축 URL을 공유해 피싱에 씁니다. 공격자가 자기 입력만 꾸밀 수 있어서 영향은 작습니다.
- 수정 제안: `unicodedata.category(char)`가 `Cc`, `Cf`, `Cs`이면 거절합니다. 이 규칙으로 S-1도 함께 막을 수 있습니다. 결정 기록(D-2)에 범위를 더해 둡니다.

### S-4 [minor] 생성 요청 수 제한과 본문 크기 제한이 없음 (F3 범위, 제안만)
- 위치: C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/api.py:24, C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/web.py:38, C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/storage.py:42
- 취약점: `POST /links`와 `POST /`는 인증도 요청 수 제한도 없습니다. `request.json()`은 길이와 상관없이 본문 전체를 메모리에 읽습니다. URL 2,048자 제한도 글자 수 기준이라, 비ASCII 문자는 `Location`에서 최대 약 24KB까지 늘어날 수 있습니다(4바이트 문자 하나가 12자가 됨). 이러면 일부 프록시의 헤더 한도를 넘을 수 있습니다.
- 공격 시나리오: 대량 생성으로 SQLite 파일이 무한정 커지거나, 거대한 본문으로 메모리를 소비하게 할 수 있습니다. 피싱 목적지를 대량으로 단축하는 데 쓰일 수도 있습니다(오픈 리다이렉트는 단축 서비스의 본래 기능이라 결함으로 보지 않습니다).
- 수정 제안: F3에서 IP나 키별 rate limit을 둡니다. 그 전이라도 리버스 프록시나 미들웨어로 요청 본문 크기 상한(예: 16KB)을 거는 것을 검토합니다.

### S-5 [minor] 보안 응답 헤더 없음
- 위치: C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/main.py:29-40, C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/templates/base.html
- 취약점: HTML 응답에 `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `frame-ancestors`(또는 `X-Frame-Options`)가 없습니다. 지금은 XSS 경로가 없으므로 방어를 겹겹이 두자는 제안입니다.
- 공격 시나리오: 나중에 템플릿 실수로 XSS가 생겼을 때 막아 줄 장치가 없습니다. 폼 화면을 iframe에 넣는 클릭재킹도 가능합니다(영향은 작음).
- 수정 제안: 인라인 스크립트가 없고 copy.js가 외부 파일이므로 `default-src 'self'; frame-ancestors 'none'` 수준의 CSP를 쉽게 적용할 수 있습니다. 응답 헤더를 붙이는 미들웨어를 하나 추가하면 됩니다.

## 문제 없음으로 확인한 항목
- 스킴 우회: `JaVaScRiPt:`, 앞쪽 `\x00`·공백·탭, `\ufeff`·`\u200b` 접두, `https\u200b://`, 전각 `ｈｔｔｐｓ`, `java\tscript:`는 모두 422였습니다. 브라우저가 상대 경로나 스킴 상대 경로로 해석할 수 있는 `http:\\evil.com`, `http:/\evil.com`, `https:evil.com`, `http://@`, `http://:80`, `http://[abc`도 모두 422였습니다. 참고로 `http://evil.com\@good.com`은 통과합니다. 파이썬은 호스트를 good.com으로, 브라우저는 evil.com으로 해석합니다. 지금은 호스트 허용 목록이 없어 영향이 없지만, 나중에 도메인 차단 목록을 도입한다면 이 파서 차이를 반드시 고려해야 합니다.
- Location 헤더 주입: CR, LF, 제어 문자는 검증 단계에서 거절됩니다. `%0d%0a` 같은 퍼센트 인코딩된 형태는 ASCII 그대로 나가므로 주입이 되지 않습니다. 비ASCII는 D-3대로 인코딩됩니다(`/한글` → `/%ED%95%9C%EA%B8%80`).
- SQL: storage.py의 모든 쿼리가 `?` 바인딩을 씁니다. `/' OR '1'='1`, `/a%00b`, `/%FF`, `/%ED%A0%80`은 모두 404였습니다.
- XSS: Starlette `Jinja2Templates`가 `select_autoescape()`를 써서 .html 템플릿은 자동 이스케이프가 켜져 있습니다. `|safe`나 `Markup`은 쓰지 않습니다. 오류 화면의 `value="..."`와 결과 화면의 원래 URL에서 `"`, `'`, `<`가 이스케이프되는 것을 확인했습니다. `href`와 `data-copy`에는 운영자 설정에서 온 `short_url`만 들어가고, 사용자 URL은 텍스트로만 표시됩니다. copy.js는 `textContent`만 쓰고 `innerHTML`은 쓰지 않습니다.
- 정보 노출: 코드 충돌 한도 초과(RuntimeError)를 포함한 500 응답은 본문이 `text/plain` "Internal Server Error"뿐이라 traceback이 나가지 않습니다. `/static/../main.py`는 404였습니다. FastAPI 기본 `/docs`와 `/openapi.json`이 열려 있지만 노출되는 스키마가 최소 수준이라 따로 지적하지 않았습니다.
- 코드 생성: `secrets.choice`로 62^7 공간에서 만들어 예측하기 어렵습니다.
- 인증과 다른 사용자 링크 조작: F1 범위 밖(F3)이라 점검하지 않았습니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)
