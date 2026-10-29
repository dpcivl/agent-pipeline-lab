---
seq: 12
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T05:34:44.660Z"
agent: "reviewer"
agent_id: "a99e7ca7e2a22575b"
turn: 1
reply_to: 9
chars: 3810
tokens_est: 1858
wait_s: null
---

## 결과: 지적 3건 (blocker 0, major 1, minor 2)

전반 평가: 구현이 계획 3절과 D-1~D-8을 충실히 따릅니다. 확인한 내용은 다음과 같습니다.
- 검증 규칙의 순서와 문구가 계획대로입니다. `urlsplit`의 ValueError도 처리합니다.
- 재시도 루프에서 `with conn` 롤백과 `closing`이 올바르게 동작하고, SQL은 모두 파라미터 바인딩입니다.
- Location은 `Response`로 직접 만들고, 라우터 등록 순서와 `create_app` 고정 계약을 지킵니다.
- Jinja2 자동 이스케이프를 유지하고 `|safe`를 쓰지 않습니다.
- 템플릿 4개는 목업(F1-home/result/error/not-found.html)과 구조, 클래스, 문구, title이 같습니다. `style.css`는 목업 공통 스타일 블록과 같고, `copy.js`는 목업의 인라인 스크립트를 그대로 옮겼습니다.
- `conftest.py`는 `count_links`를 추가했을 뿐 기존 픽스처는 그대로입니다.
- AC-1~AC-23이 빠짐없이 테스트와 연결됩니다.

## 지적 목록

### R-1 [major] 짝 없는 서로게이트가 든 url이 검증을 통과해 500이 남 (implementer 자진 보고 건)
- 위치: `src/shortlink/validation.py:45-67` (검증 누락). 실제로 터지는 곳은 `src/shortlink/repository.py:56-59`(INSERT 바인딩)입니다. `src/shortlink/web.py:41`의 `quote(char, safe="")`도 같은 입력에서 UnicodeEncodeError를 냅니다.
- 문제: `POST /links`에 `{"url": "https://e.com/\ud800"}`를 보내면 FastAPI가 본문을 `request.json()`(json.loads)으로 읽습니다(`.venv/.../fastapi/routing.py:464`). 이때 짝 없는 서로게이트가 그대로 str에 남습니다. `StrictStr`와 `validate_url`(제어 문자 검사는 0x20 이하와 0x7F만 봄)을 모두 통과한 뒤, sqlite3가 바인딩하면서 UTF-8로 인코딩하다 UnicodeEncodeError가 납니다. 클라이언트 입력 때문에 처리되지 않은 500이 나는 것입니다. 저장은 되지 않습니다. 예외가 `with conn` 안에서 나서 롤백되므로 AC-9 위반이나 데이터 손상은 아닙니다. 웹 폼에서는 재현되지 않습니다. 브라우저 폼은 퍼센트 인코딩해서 보내고, Starlette가 `unquote_plus`(errors=replace)로 U+FFFD로 바꾸기 때문입니다. 따라서 API 경로만 문제입니다.
- 근거: 설계서와 계획 3.3은 실패를 모두 422로 정의합니다("어떤 경우든 저장하지 않는다"). 이 값은 UTF-8 텍스트로 저장할 수 없는 비정상 문자열인데도 서버 오류로 끝납니다. 이 입력을 막는 테스트도 없습니다.
- 수정 제안: `validate_url`의 규칙 4 바로 뒤(스킴 검사 전)에 `try: url.encode("utf-8") except UnicodeEncodeError: raise InvalidURLError(...)`를 넣어 422로 거절합니다. 문구는 둘 중 하나입니다.
  - `MSG_INVALID_CHAR`를 재사용합니다. 목업 오류 표와 계획 3.1 표를 바꾸지 않아도 됩니다.
  - 새 상수(예: "URL에 올바르지 않은 문자가 있습니다.")를 둡니다. 이 경우 계획 3.1 표에 규칙을 추가해야 하므로 메인이 결정을 기록해야 합니다.

  테스트도 추가합니다. `test_validation.py`에는 `"https://e.com/\ud800"`, `"\udc80"` 입력이 422 문구로 거절되는지 넣습니다. `test_api_links.py`에는 `content='{"url": "https://e.com/\\ud800"}'`와 `Content-Type: application/json`을 직접 보내서 422와 `count_links() == 0`을 확인하는 케이스를 넣습니다. httpx의 `json=`은 이 값을 인코딩하지 못하므로 원문 content로 보내야 합니다.

### R-2 [minor] `navigator.clipboard`가 없는 환경에서 복사 실패 문구가 나오지 않음
- 위치: `src/shortlink/static/copy.js:4`
- 문제: localhost가 아닌 HTTP 같은 비보안 컨텍스트에서는 `navigator.clipboard`가 `undefined`입니다. 그러면 `.writeText` 호출에서 TypeError가 동기로 던져집니다. `.then`의 실패 콜백까지 가지 못하므로 `#copy-status`에 아무것도 표시되지 않습니다. `SHORTLINK_BASE_URL`을 http 사내 도메인으로 배포하면 그대로 이 상황이 됩니다.
- 근거: 계획 3.4는 복사 결과를 "복사했습니다." 또는 "복사하지 못했습니다. 링크를 직접 선택해 복사해 주세요."로 알리라고 합니다. 목업의 인라인 스크립트도 같은 코드라서 목업 위반은 아닙니다. 다만 계획이 의도한 실패 안내가 빠지는 경우입니다.
- 수정 제안: 클릭 핸들러 첫 줄에 `if (!navigator.clipboard) { status.textContent = "복사하지 못했습니다. 링크를 직접 선택해 복사해 주세요."; return; }` 가드를 넣습니다. 목업과 문구, 구조는 그대로 유지됩니다.

### R-3 [minor] 재시도 상한 테스트의 단언이 느슨함
- 위치: `tests/test_repository.py:97` (`assert 1 < len(calls) <= LinkRepository.MAX_ATTEMPTS + 1`)
- 문제: 재시도를 2번만 하고 포기하는 구현도 통과합니다. 그래서 "최대 10회 후 RuntimeError"(계획 3.2)를 실제로 검증하지 못합니다. 현재 구현은 정확히 `MAX_ATTEMPTS`번 시도합니다.
- 근거: 계획 3.2 "PRIMARY KEY 충돌이면 새 코드로 재시도, 최대 10회 후 `RuntimeError`"
- 수정 제안: `assert len(calls) == LinkRepository.MAX_ATTEMPTS`로 고정합니다. 같은 파일의 `test_collision_resolved_on_the_last_attempt_still_succeeds`와 짝을 이뤄 경계를 양쪽에서 확인할 수 있습니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)

참고한 파일:
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\validation.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\repository.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\web.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\static\copy.js
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_repository.py

이번 리뷰는 정적 검토만 했습니다. 서로게이트 입력의 500은 코드 경로를 추적한 결과와 implementer의 보고를 근거로 판단했고, 직접 실행해 재현하지는 않았습니다. 확인은 qa에 맡깁니다.
