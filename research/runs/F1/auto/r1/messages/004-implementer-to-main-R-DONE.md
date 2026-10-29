---
seq: 4
sender: "implementer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T04:41:56.948Z"
agent: "implementer"
agent_id: "abf585d38424abbbe"
turn: 1
reply_to: 2
chars: 3289
tokens_est: 1418
wait_s: null
---

## 결과: 완료

## 변경 파일
- src/shortlink/db.py: `connect`는 요청마다 새 sqlite3 연결을 열고, `init_db`는 `links` 스키마를 만든다.
- src/shortlink/validation.py: `validate_url`을 계획 3.2 표의 검사 순서와 문구 그대로 구현했다. 입력값은 정규화하지 않고 그대로 돌려준다.
- src/shortlink/links.py: `generate_code`(`secrets.choice` 7자), `utc_now_iso`, `short_url`, `create_link`, `get_link`를 구현했다. `create_link`는 코드가 겹치면(`IntegrityError`) 최대 10번 다시 시도하고, 계속 실패하면 `RuntimeError`를 낸다. 모든 쿼리는 `?` 바인딩을 쓴다.
- src/shortlink/api.py: `POST /links`는 `await request.json()`으로 본문을 직접 읽는다. JSON 파싱 실패나 객체가 아닌 본문은 422 `{"detail": "요청 본문은 JSON 객체여야 합니다."}`, 검증 실패는 422 `{"detail": <문구>}`, 성공은 201이다.
- src/shortlink/web.py: `GET /`, `POST /`, `GET /{code}`를 구현했다. 폼은 `url`이 없으면 `""`로 받는다. 302는 `RedirectResponse(url, status_code=302)`이고, 없는 코드는 404 HTML 화면이다.
- src/shortlink/templates/base.html: 공통 head(`<html lang="ko">`, charset, viewport, `/static/style.css`)와 `title`, `content`, `scripts` 블록.
- src/shortlink/templates/home.html: 홈 화면과 입력 오류 화면을 겸한다. `error`가 있을 때만 `<p class="alert" role="alert" id="url-error">`, `aria-invalid="true"`, `aria-describedby="url-error url-hint"`를 출력한다.
- src/shortlink/templates/result.html: 결과 화면. `<script src="/static/copy.js" defer></script>`를 포함한다.
- src/shortlink/templates/not_found.html: 찾을 수 없음 화면.
- src/shortlink/static/style.css: 목업 `<style>` 내용을 그대로 옮겼다.
- src/shortlink/static/copy.js: 결과 목업의 스크립트를 그대로 옮겼다.
- src/shortlink/static/.gitkeep, src/shortlink/templates/.gitkeep: 디렉터리에 실제 파일이 생겨 삭제했다.
- main.py와 config.py는 수정하지 않았다. pyproject.toml과 uv.lock도 그대로다.

## 구현한 수용 기준
- AC-1~AC-4: `api.py`의 `create_link_api`, `links.py`의 `create_link`, `generate_code`, `short_url`. `url`은 저장하고 응답할 때 그대로 쓰고, `http://`도 통과한다.
- AC-5~AC-8: `validation.py`의 `validate_url`. 2,048자는 통과하고 2,049자는 거절한다. `url`이 숫자이거나 없거나 빈 문자열이면 거절한다.
- AC-9, AC-19: 검증을 통과한 뒤에만 `create_link`를 호출하므로 거절된 요청은 저장하지 않는다.
- AC-10, AC-11: `web.py`의 `follow`.
- AC-12, AC-13: 요청마다 새 코드를 만들고, 겹치면 다시 시도한다.
- AC-14: `init_db`는 `CREATE TABLE IF NOT EXISTS`라서 같은 `db_path`로 앱을 다시 만들어도 이전 코드가 남는다.
- AC-15: `utc_now_iso`.
- AC-16, AC-18: `home.html`, `result.html`.
- AC-17, AC-23: `web.py`의 `shorten_form`.
- AC-19, AC-20: `home.html`이 제출값을 이스케이프해서 오류 화면에 표시한다. `result.html`도 같다. 자동 이스케이프는 켜 둔 채로 `|safe`나 `Markup`은 쓰지 않았다.
- AC-21: `not_found.html`.
- AC-22: `base.html`.

## 계획에 없던 판단
- `validate_url`에서 `urlsplit`이 `ValueError`를 내는 경우(예: `http://[`)를 따로 처리했다. 스킴이 http/https가 아니면 5번 문구, 맞으면 6번 문구(호스트 없음)로 422를 돌려준다. 500 오류를 막으려고 한 것이다.
- `base.html`에 `title`, `content`, `scripts` 블록을 뒀다. 목업마다 `<title>`이 달라서 `title` 블록으로 맞췄다. 홈과 오류 화면은 "ShortLink — URL 단축", 결과는 "단축 URL을 만들었습니다 — ShortLink", 404는 "링크를 찾을 수 없습니다 — ShortLink"다.
- `create_link`는 시도마다 같은 연결을 쓰고 `created_at`은 한 번만 계산한다.

## 확인한 것
- `uv run ruff check src`는 통과했고 `uv run ruff format src`는 실행했다.
- 임시 DB 경로로 TestClient 스모크 테스트를 돌렸고, 끝난 뒤 DB 파일은 지웠다. cwd에는 `shortlink.db`가 생기지 않았다.
- 확인한 항목은 다음과 같다.
  - API 생성은 201이고, 숫자·빈 문자열·누락·ftp·호스트 없음·2,049자·JSON이 아닌 본문·배열 본문은 422에 계획의 문구가 나온다.
  - `HTTPS://Example.com`은 201이다.
  - 리다이렉트는 302이고, 없는 코드는 404 HTML이다.
  - 폼의 `<script>` 입력은 422이고 이스케이프되어 표시된다. 폼에 `url`이 없으면 422 HTML이다.
  - 성공한 폼 결과의 `&`, `<`, `>`는 이스케이프된다.
  - `/static/style.css`와 `/static/copy.js`는 200이다.
- pytest는 실행하지 않았다. tests/는 test-writer가 작성 중이라 건드리지 않았다.

## 남은 문제와 질문
- 없음
