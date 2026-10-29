---
seq: 13
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T05:34:47.510Z"
agent: "security"
agent_id: "accb681291420c0b3"
turn: 1
reply_to: 11
chars: 4757
tokens_est: 2345
wait_s: null
---

## 결과: 지적 3건 (blocker 0, major 0, minor 3)

blocker나 major는 없다. XSS, Location 헤더 인젝션, SQL 인젝션, 에러 응답의 정보 노출은 모두 막혀 있다. bandit도 지적 0건이다(`uv run bandit -r src -q`, exit 0).

## 지적 목록

### S-1 [minor] 짝 없는 서로게이트가 든 url이 검증을 통과해 500 응답
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\validation.py:51-52` (검사 누락), 예외가 나는 곳은 `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\repository.py:56-59`
- 취약점: JSON 문자열 `"https://a.test/\ud800"`은 파이썬 str 안에 짝 없는 서로게이트로 들어온다. `validate_url`은 이 값을 막지 않는다(직접 확인: 원문 그대로 반환). 그다음 sqlite3가 값을 바인딩하면서 UTF-8로 인코딩할 때 `UnicodeEncodeError: surrogates not allowed`가 나고, 처리되지 않은 예외라서 500이 된다.
- 보안 영향 (재현해서 확인):
  - 응답 본문은 `text/plain`의 `Internal Server Error` 한 줄뿐이다. 트레이스백, 경로, SQL은 노출되지 않는다(debug 꺼짐).
  - INSERT 바인딩 단계에서 실패하므로 행이 저장되지 않는다(행 수 0). 그래서 이 값이 나중에 `location_header_value()`나 템플릿에 들어갈 경로가 없다. 헤더 인젝션이나 XSS로 이어지지 않는다.
  - 폼 경로(`POST /`)에서는 잘못된 UTF-8(`%ED%A0%80`, `%FF`)이 디코딩 단계에서 U+FFFD로 바뀌므로 이 문제가 생기지 않는다. 200으로 저장된다.
  - 남는 영향은 두 가지뿐이다. 하나는 422로 거절해야 할 입력에 5xx를 준다는 계약 위반이다. 다른 하나는 반복 요청으로 서버 로그에 트레이스백이 쌓이고 5xx 경보가 울릴 수 있다는 점이다. 원격에서 악용할 수 있는 취약점은 아니다.
- 공격 시나리오: 공격자가 `\ud800` 이스케이프를 넣은 JSON을 대량으로 보낸다. 그러면 에러 로그와 5xx 지표가 오염되어 모니터링 노이즈가 생기고, 실제 장애를 알아보기 어려워진다. 데이터 오염이나 정보 유출은 없다.
- 수정 제안: `validate_url`의 4번 규칙(문자 검사)에서 서로게이트(U+D800-U+DFFF)도 거절한다. 문구는 `MSG_INVALID_CHAR`를 쓰거나 별도 문구를 둔다. 예를 들어 `0xD800 <= ord(char) <= 0xDFFF` 조건을 추가하거나, `url.encode("utf-8")`의 `UnicodeEncodeError`를 잡아 `InvalidURLError`를 던진다. `tests/test_validation.py`와 `tests/test_api_links.py`에 422가 나고 저장되지 않는지 확인하는 테스트를 추가한다. 규칙을 추가하는 것이므로 계획 D-2에 함께 기록할 것을 권한다.

### S-2 [minor] 요청 수 제한과 요청 본문 크기 제한 없음 (F3 범위, 기록만)
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\api.py:31`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\web.py:50`
- 취약점: 인증 없이 링크를 무제한으로 만들 수 있다. url 길이는 2,048자로 제한되지만, JSON과 폼 본문은 검증 전에 통째로 파싱되므로 본문 전체 크기에는 앱 수준 상한이 없다.
- 공격 시나리오: 스크립트로 링크를 대량 생성해 SQLite 파일을 키우거나(디스크 고갈), 피싱이나 스팸 URL을 대량으로 단축한다. 수백 MB짜리 본문을 보내 메모리를 소모시킨다.
- 수정 제안: F3에서 IP나 API 키 단위의 rate limit을 넣는다. 본문 크기 상한은 리버스 프록시(예: `client_max_body_size`)나 미들웨어에서 몇 KB로 제한한다. F1에서는 조치하지 않아도 된다.

### S-3 [minor] 보안 응답 헤더 없음 (방어 심화)
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\main.py:30-41` (`GET /` 응답 헤더는 `content-type`과 `content-length`뿐)
- 취약점: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, 프레이밍 제한(`frame-ancestors`/`X-Frame-Options`)이 없다. 지금은 XSS가 없지만, 나중에 템플릿 이스케이프가 하나라도 빠지면 이를 막아 줄 2차 방어선이 없다.
- 공격 시나리오: F2/F3에서 별칭이나 통계 화면을 추가할 때 이스케이프가 누락되면 스크립트가 바로 실행된다. 화면을 iframe에 넣는 클릭재킹도 가능하다(현재는 인증이 없어 피해가 작다).
- 수정 제안: 템플릿에 인라인 스크립트와 인라인 스타일이 없으므로(`copy.js`, `style.css`는 외부 파일), 미들웨어로 `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`와 `X-Content-Type-Options: nosniff`를 붙여도 동작이 깨지지 않는다.

## 확인한 항목 (문제 없음)

- **XSS**
  - 자동 이스케이프가 켜져 있다. Starlette 1.10.0의 `Jinja2Templates(directory=...)`는 `autoescape=select_autoescape()`를 쓰고, 템플릿이 모두 `.html`이라 자동 이스케이프가 적용된다.
  - `|safe`와 `Markup`은 어디에도 쓰이지 않는다.
  - 재현 결과: `"><script>alert(1)</script>`와 `'onmouseover='alert(1)`을 넣어도 결과 화면과 오류 화면에 원문이 나오지 않는다. 사용자 값이 들어가는 `value="{{ url_value }}"`는 큰따옴표로 감싼 속성이고 `"`와 `'`가 이스케이프된다.
- **href, data-copy**: `short_url`은 운영자 설정 `base_url`과 서버가 만든 `[A-Za-z0-9]{7}` 코드로만 조합되고, 사용자 입력이 들어가지 않는다. 사용자 URL은 `<p>` 텍스트로만 출력되고 `href`에는 들어가지 않는다. `copy.js`는 `dataset.copy`를 `clipboard.writeText`로, 상태 문구는 `textContent`로 다루며 `innerHTML`을 쓰지 않는다.
- **스킴 우회**: `JaVaScRiPt:alert(1)`, `javascript:alert(1)//https://a.test`, `https:\\evil.test`는 모두 422로 거절된다. 공백과 C0 제어 문자를 먼저 거절하므로, 브라우저와 urlsplit이 앞쪽 공백이나 탭·줄바꿈을 서로 다르게 처리하는 점을 이용한 우회도 막힌다.
- **Location 헤더 인젝션**: CR/LF를 포함한 0x20 이하 문자와 0x7F는 검증 단계에서 거절된다. 비ASCII 문자(U+2028, U+0085 같은 C1 문자, NBSP 포함)는 `location_header_value()`가 퍼센트 인코딩한다. 재현 결과 `https://a.test/%E2%80%A8x%C2%85y%C2%A0z`로 나간다. `<`, `>`, `"`, `'`가 Location에 그대로 들어가지만 헤더 문맥에서는 무해하다(D-4).
- **오픈 리다이렉트**: URL 단축기로서 설계된 동작이다. 서버는 대상 URL에 직접 요청하지 않으므로 SSRF는 없다. 내부 주소(localhost, 사설 IP)로 보내는 리다이렉트나 `https://bank.example@evil.test` 같은 사용자정보 위장은 피싱 악용 소지로만 남는다. 정책을 정할 문제이고 F1 조치 대상은 아니다.
- **SQL**: `repository.py:57`과 `repository.py:69` 모두 `?` 바인딩을 쓴다. `db.py`의 DDL은 상수 문자열이다. `GET /{code}`의 code는 길이 제한이 없지만 바인딩되므로 안전하다.
- **코드 예측**: `secrets.choice`로 62^7(약 3.5×10^12)가지 중 하나를 뽑으므로 열거가 사실상 불가능하다.
- **에러 응답 정보 노출**: 500 응답은 일반 문구뿐이다. FastAPI 기본 422 응답에 `input` 필드로 요청값이 되돌아오지만 요청자 자신의 입력이므로 문제없다. `/docs`와 `/openapi.json`이 공개되어 있으나 공개 API라 민감 정보는 없다(운영에서 끄는 것은 선택 사항).

점검용 스크립트(저장소 밖, 임시 DB 사용): `<HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F1-human-r1\56be2f53-1a32-42ee-8657-b069f6e12cce\scratchpad\probe.py`
