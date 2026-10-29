---
seq: 19
sender: "implementer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T06:11:59.479Z"
agent: "implementer"
agent_id: "a76b9356aae1c5ad6"
turn: 2
reply_to: 17
chars: 2143
tokens_est: 962
wait_s: null
---

## 결과: 완료
M-1, R-2, S-3 세 건을 모두 고쳤다. `uv run ruff check src`는 통과했고 `uv run ruff format src`는 변경 없음이다. `uv run python -m pytest -q`는 92개 통과, 실패 0이다. 이번 수정 전에 이미 있던 테스트가 깨지지 않았다. 계획서(3.1 표, D-9~D-11)는 읽고 따랐고 수정하지 않았다. `tests/`는 건드리지 않았다.

## 변경 파일
- `src/shortlink/validation.py`: `MSG_INVALID_ENCODING = "URL에 올바르지 않은 문자가 있습니다."`를 추가했다. 규칙 5로 `url.encode("utf-8")`가 `UnicodeEncodeError`를 내면 이 문구로 거절한다. 스킴은 6, 호스트는 7로 밀렸고 docstring도 갱신했다.
- `src/shortlink/static/copy.js`: 클릭 핸들러에서 `navigator.clipboard`나 `writeText`가 없으면 `#copy-status`에 "복사하지 못했습니다. 링크를 직접 선택해 복사해 주세요."를 표시하고 return한다.
- `src/shortlink/security.py` (신규): `add_security_headers(app)`가 `@app.middleware("http")`로 헤더를 붙인다.
  - 모든 응답에 `X-Content-Type-Options: nosniff`를 붙인다.
  - `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`는 `content-type`이 `text/html`이고 경로가 `app.docs_url`, `app.redoc_url`, `app.swagger_ui_oauth2_redirect_url`가 아닐 때만 붙인다.
- `src/shortlink/main.py`: `app.state.settings` 설정 직후에 `add_security_headers(app)` 호출과 import를 추가했다. `create_app(settings=None)` 시그니처는 그대로다.

## 구현한 수용 기준
- M-1 / D-9: JSON `{"url": "https://e.com/\ud800"}`이 이제 `POST /links`에서 422 `{"detail": "URL에 올바르지 않은 문자가 있습니다."}`로 거절된다. 이전에는 500이었다. `ftp://\ud800`은 규칙 5가 스킴 검사보다 앞서므로 같은 인코딩 문구가 나온다.
- R-2 / D-11: `copy.js`에 `navigator.clipboard`가 없을 때 실패 문구를 바로 표시하는 분기를 넣었다. 브라우저 동작은 직접 확인하지 못했다.
- S-3 / D-10: TestClient로 확인했다.
  - `/`, 404 화면(`/nope123`), 입력 오류 422 화면, 결과 화면: nosniff와 CSP가 모두 붙는다.
  - `/docs`, `/redoc`, `/docs/oauth2-redirect`: nosniff만 붙고 CSP는 없으며 200으로 계속 동작한다.
  - `/openapi.json`, `/static/style.css`, 302 리다이렉트, `POST /links` 201: nosniff만 붙는다.
  - 템플릿에는 인라인 `<style>`, `style=`, 인라인 `<script>`, 이벤트 핸들러 속성이 없다. `<script src="/static/copy.js" defer>` 하나뿐이라 `default-src 'self'`로 동작한다.

## 계획에 없던 판단
- 헤더 로직을 `main.py`에 직접 쓰지 않고 새 모듈 `security.py`로 분리했다. `main.py`는 고정 계약 파일이라 변경을 호출 한 줄로 줄이려는 것이다.
- 경로 제외 목록은 `/docs` 같은 값을 하드코딩하지 않고 FastAPI 앱의 `docs_url` 등에서 읽는다. 경로 설정을 바꿔도 CSP 제외가 어긋나지 않는다.
- CSP는 "HTML 응답에 한정하고 docs 경로만 제외"하는 방식으로 했다. 경로 화이트리스트 방식보다, 이후 기능에서 HTML 화면이 늘어도 자동으로 보호된다.

## 남은 문제와 질문
- 없음.
