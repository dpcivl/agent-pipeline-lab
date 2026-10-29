---
seq: 13
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T04:48:16.385Z"
agent: "reviewer"
agent_id: "a449550ba56e63033"
turn: 1
reply_to: 8
chars: 4842
tokens_est: 2317
wait_s: null
---

## 결과: 지적 5건 (blocker 0, major 1, minor 4)

전체적으로 설계서, 계획, D-1~D-7과 잘 맞습니다. 확인한 내용은 이렇습니다.
- 고정 계약은 지켜졌습니다. `create_app(settings=None)`의 시그니처가 그대로이고, 라우터 등록과 `init_db`도 앱 생성 안에서 끝납니다. `Settings`는 바뀌지 않았고, `settings`/`app`/`client` 픽스처는 의미가 그대로이며 `link_count` 픽스처만 추가됐습니다. templates와 static 위치도 맞습니다.
- 라우트 순서는 /static, /links, /, /{code} 순입니다.
- 쿼리는 모두 파라미터 바인딩을 씁니다.
- Jinja 자동 이스케이프가 켜져 있습니다(`select_autoescape()`). `|safe`는 쓰지 않았습니다.
- 템플릿 4개는 목업의 구조, 문구, class, aria 속성과 같습니다. style.css와 copy.js도 목업의 `<style>`, `<script>`와 글자 단위로 같습니다.

## 지적 목록

### R-1 [major] 리다이렉트 Location에서 일부 ASCII 문자가 퍼센트 인코딩되어 D-3·AC-10과 어긋남
- 위치: `src/shortlink/web.py:56`, 테스트 주석 `tests/test_web.py:273-274`
- 문제: Starlette `RedirectResponse`는 `quote(url, safe=":/%#?=@[]!$&'()*+,;")`를 씁니다(`.venv/Lib/site-packages/starlette/responses.py:218`). 그래서 비ASCII 문자뿐 아니라 safe 목록에 없는 ASCII 문자 `" < > \ ^ \` { | }`도 인코딩됩니다. 예를 들어 `https://example.com/?a=1|2`를 저장하면 Location은 `https://example.com/?a=1%7C2`가 됩니다. 이런 문자는 헤더에 그대로 넣어도 문제가 없습니다.
- 근거: D-3은 "ASCII URL은 글자 그대로 나가고, 한글처럼 헤더에 그대로 넣을 수 없는 문자는 퍼센트 인코딩된다"고 정했고, AC-10은 "Location 헤더에 원래 URL"을 요구합니다. 구현은 두 문장 모두와 다르게 동작합니다. `test_ac20_script_url_is_stored_verbatim_and_redirects`의 주석("characters that cannot go into a header verbatim are percent-encoded")도 사실과 다릅니다. `<`, `>`는 헤더에 넣을 수 있는 문자입니다. 이 동작을 직접 확인하는 테스트도 없습니다.
- 수정 제안: 둘 중 하나를 고르면 됩니다.
  - (a) 구현을 D-3에 맞춥니다. 비ASCII 문자만 인코딩합니다. 예: `quote(url, safe=<출력 가능한 ASCII 0x21-0x7E 전체>)`를 쓰거나, 비ASCII 문자만 골라 `quote`하고 `Response(status_code=302, headers={"location": ...})`로 직접 응답합니다. 공백과 제어 문자는 D-2에서 이미 막혀 있으므로 안전합니다.
  - (b) 현재 동작을 유지하고 D-3 문구를 "비ASCII와 URI에 쓸 수 없는 일부 ASCII 문자(`"<>\^\`{|}`)는 퍼센트 인코딩된다"로 고칩니다.
  
  어느 쪽이든 `|`나 `{}`가 든 URL로 Location 값을 고정하는 테스트를 추가하고, test_web.py:273의 주석을 실제 동작에 맞게 고칩니다.

### R-2 [minor] 코드 충돌 시 재시도와 10회 실패 시 RuntimeError 경로에 테스트가 없음
- 위치: `src/shortlink/links.py:49-62`
- 문제: 설계서의 "이미 있는 코드와 겹치면 다시 만듭니다"와 계획 3.3의 "10번 실패하면 RuntimeError"를 확인하는 테스트가 없습니다. tests/ 아래에서 `generate_code`, `monkeypatch`, `IntegrityError`, `RuntimeError`를 검색해도 결과가 없습니다. 무작위로 만드는 7자 코드는 실제로 충돌할 일이 거의 없어서, AC-13의 100개 생성 테스트로는 이 분기가 실행되지 않습니다.
- 근거: 코드를 읽어 보면 동작은 맞습니다. `with conn:` 블록에서 IntegrityError가 나면 롤백한 뒤 continue합니다. 하지만 이 분기가 회귀해도 잡아낼 장치가 없습니다.
- 수정 제안: `monkeypatch`로 `links.generate_code`가 이미 있는 코드를 먼저 돌려준 다음 새 코드를 돌려주게 해서, 결과가 새 코드이고 행 수가 1만 늘었는지 확인합니다. 항상 같은 코드를 돌려주게 해서 RuntimeError가 나는지도 확인합니다.

### R-3 [minor] 잘못된 IPv6 authority를 처리하는 `except ValueError` 분기에 테스트가 없고, 스킴 판정 로직이 중복됨
- 위치: `src/shortlink/validation.py:41-49`
- 문제: `https://[::1`처럼 `urlsplit`이 ValueError를 던지는 입력을 처리하는 분기를 실행하는 테스트가 없습니다. 테스트에 있는 IPv6 입력은 올바른 `https://[::1]/a`뿐입니다. 이 분기는 `value.find(":")`로 스킴을 따로 잘라 내서, 아래쪽 `parts.scheme` 검사와 같은 판정을 다른 방식으로 한 번 더 구현합니다.
- 근거: 이 분기가 빠지거나 바뀌면 API와 폼 모두 500 오류가 날 수 있는데, 테스트로는 드러나지 않습니다.
- 수정 제안: `test_validation.py`에 `"https://[::1"`→MSG_NO_HOST, `"ftp://[::1"`→MSG_SCHEME 같은 경우를 추가합니다. 가능하면 스킴 검사를 `urlsplit` 앞으로 옮겨 정규식이나 `partition(":")` 같은 한 가지 방식으로만 판정합니다. 계획서 3.2의 검사 순서(스킴 → 호스트)는 그대로 지킬 수 있습니다.

### R-4 [minor] async 핸들러 안에서 동기 sqlite3 I/O를 실행함
- 위치: `src/shortlink/api.py:36`, `src/shortlink/web.py:40`, `src/shortlink/web.py:53`
- 문제: `async def` 핸들러가 `links.create_link`와 `links.get_link`(동기 sqlite3 호출)를 그대로 실행해서, 그동안 이벤트 루프가 멈춥니다. 쓰기 잠금 경합이 생기면 sqlite3 기본 timeout(5초) 동안 서버 전체가 응답하지 못할 수 있습니다.
- 근거: FastAPI는 `def` 핸들러만 스레드풀에서 실행합니다.
- 수정 제안: `web.home`, `web.follow`, `web.shorten_form`은 `def`로 바꾸면 됩니다(Form 파라미터는 `def`에서도 받을 수 있습니다). `api.create_link_api`는 `await request.json()`을 써야 하므로 `await run_in_threadpool(links.create_link, ...)`로 감쌉니다. 지금 규모에서는 개선 제안 수준입니다.

### R-5 [minor] 템플릿 디렉터리 경로가 두 곳에 정의되어 있음
- 위치: `src/shortlink/web.py:18`, `src/shortlink/main.py:24`
- 문제: `TEMPLATES_DIR`가 main.py와 web.py에 각각 계산되어 있습니다. main.py의 값은 이제 어디서도 쓰이지 않습니다. 주석에 순환 import 때문이라고 적혀 있지만, 한쪽 경로만 바뀌면 두 값이 어긋날 수 있습니다.
- 수정 제안: 경로 상수를 순환이 생기지 않는 작은 모듈(예: `shortlink/paths.py`)로 옮겨 main과 web이 함께 쓰게 합니다. main.py의 상수는 고정 계약 항목이 아니므로 그 모듈을 다시 export하는 형태로 남겨도 됩니다. 아니면 지금 구조를 유지하고 main.py 쪽에 "web.py와 같은 값"이라는 주석을 답니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)

참고: R-1의 `\` 인코딩은 보안 측면도 있습니다. urlsplit은 `https://example.com\@evil.com`의 호스트를 evil.com으로 해석하는데, 브라우저는 `\`를 `/`로 취급해 호스트를 다르게 봅니다. 이 부분은 security 검토 범위라 이 리뷰의 심각도에는 반영하지 않았습니다.

관련 파일:
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\web.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\validation.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\links.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\api.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\main.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_web.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\docs\plans\F1-decisions.md
