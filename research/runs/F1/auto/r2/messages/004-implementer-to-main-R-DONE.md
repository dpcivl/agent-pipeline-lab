---
seq: 4
sender: "implementer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T05:12:19.417Z"
agent: "implementer"
agent_id: "a46510386cb9984ad"
turn: 1
reply_to: 2
chars: 2759
tokens_est: 1204
wait_s: null
---

## 결과: 완료
## 변경 파일
- /C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/codes.py: `generate_code`를 `secrets.choice`로 구현
- .../src/shortlink/validation.py: `validate_url`을 계획의 검사 순서와 문구대로 구현(값은 바꾸지 않음). 호스트 없음 문구는 상수 `NO_HOST_MESSAGE`로 뺌
- .../src/shortlink/storage.py: `init_schema`, `create`(코드 충돌 시 재시도, 10회 실패하면 RuntimeError), `get`, `count`. 호출마다 연결을 열고 닫으며 `?` 바인딩을 씀. `created_at`은 `YYYY-MM-DDTHH:MM:SSZ`
- .../src/shortlink/api.py: `POST /links` 구현. 201과 네 필드, 실패하면 422 `{"detail": ...}`
- .../src/shortlink/web.py: `GET /`, `POST /`, `GET /{code}` 구현. 비ASCII 문자만 UTF-8 퍼센트 인코딩하는 `_encode_location` 추가
- .../src/shortlink/templates/base.html, home.html, result.html, not_found.html: 목업의 마크업, 클래스, 문구를 따름. `.mockup-note`와 인라인 `<script>`는 넣지 않고 `result.html`에 `<script src="/static/copy.js" defer>`만 둠
- .../src/shortlink/static/style.css: 목업 `<style>` 블록을 들여쓰기만 바꿔 옮김. `.mockup-note` 규칙과 안내 주석은 뺌
- .../src/shortlink/static/copy.js: 목업 스크립트 동작을 옮김. `navigator.clipboard`가 없거나 복사가 실패해도 오류 없이 넘어감
- `main.py`, `config.py`, `pyproject.toml`은 바꾸지 않았다. 의존성도 추가하지 않았다.

## 구현한 수용 기준
- AC-1~AC-4: `api.py`의 `create_link`와 `storage.py`의 `create`. `short_url`은 `settings.base_url`로 만들고 `url`은 받은 그대로 돌려줌
- AC-5~AC-8: `validation.py`. 스킴은 대소문자를 구분하지 않고(D-1), 길이는 2,048자까지 허용
- AC-9, AC-19: 검증을 통과한 뒤에만 `create`를 호출하므로 거절된 요청은 저장하지 않음
- AC-10, AC-11, AC-21, AC-23: `web.py`의 `follow`. 있으면 302와 `Location`, 없으면 `not_found.html` 404
- AC-12, AC-13: 요청마다 새 코드를 만들고 PRIMARY KEY 충돌 시 다시 만듦
- AC-14: SQLite 파일에 저장하고 `create_app`이 `init_schema`를 부름(기존 `main.py`)
- AC-15: `storage.py`의 UTC `created_at`
- AC-16~AC-18, AC-20, AC-22: `home.html`, `result.html`, `base.html`. `|safe`와 `Markup`은 쓰지 않았고 `<script>` 입력이 `&lt;script&gt;`로 나옴을 직접 확인함
- AC-19: `POST /` 실패 시 `home.html`을 422로 렌더링하고 `error`와 `url_value`를 넘김. 입력칸에 `aria-invalid`와 `aria-describedby`를 붙임

TestClient로 직접 확인한 것: 생성, 302 `Location`, 422 각 경우, 폼 결과·오류 화면, 404 화면, 비ASCII URL의 `Location`(`https://%EC%98%88%EC%8B%9C.com/...?a=<>`), `/static/style.css`와 `/static/copy.js` 200. `uv run ruff check src`는 통과했고 `uv run ruff format src`도 실행함. pytest는 돌리지 않았다(테스트 파일이 아직 없음).

## 계획에 없던 판단
- `urlsplit`이 ValueError를 내는 URL(예: `http://[abc`)은 "호스트 없음" 문구로 422 처리: 검증 중 예외가 나면 500이 되므로. 이 경우 스킴 검사가 호스트 검사보다 먼저 일어나지 않는다. 예를 들어 `ftp://[abc`는 스킴 문구가 아니라 호스트 문구가 나온다.
- API 본문이 JSON이 아니거나 객체가 아닐 때의 `detail`: 계획에 문구가 없어서 `요청 본문은 {"url": ...} 형태의 JSON 객체여야 합니다.`로 정함(D-4는 422만 정함).
- 폼의 `url` 값이 파일 업로드 등 문자열이 아니면 `None`으로 보고 "URL을 입력해 주세요."로 처리.

## 남은 문제와 질문
- 짝 없는 서로게이트 문자(JSON `"\ud800"` 같은 값)가 든 URL은 현재 검증을 통과한다. 그런데 SQLite에 저장할 때 UnicodeEncodeError가 나서 API가 500을 돌려줄 것으로 보인다(이 경우는 직접 실행해 보지 않음). 설계서와 D-2에 없는 규칙이라 추가하지 않았다. 필요하면 검증 규칙에 넣는 결정이 필요하다.
- tests/는 건드리지 않았고, 틀렸다고 판단한 테스트는 없다.
