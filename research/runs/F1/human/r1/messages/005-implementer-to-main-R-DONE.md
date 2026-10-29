---
seq: 5
sender: "implementer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T05:31:15.169Z"
agent: "implementer"
agent_id: "a76b9356aae1c5ad6"
turn: 1
reply_to: 3
chars: 3450
tokens_est: 1488
wait_s: null
---

## 결과: 완료
스텁의 NotImplementedError를 모두 구현했고, 템플릿 4개와 `style.css`, `copy.js`를 작성했다. `uv run ruff check src`는 통과했고 `uv run ruff format src`는 변경 없음이다. `uv run pytest`는 돌리지 않았다. 대신 TestClient 임시 스크립트로 AC-1~AC-23 동작을 확인했다. 스크립트는 scratchpad에만 두고 저장소에는 남기지 않았다.

## 변경 파일
- `src/shortlink/validation.py`: `validate_url` 구현. 문구 순서는 3.1절 표를 따른다.
- `src/shortlink/codes.py`: `generate_code`(`secrets.choice`), `build_short_url`.
- `src/shortlink/db.py`: `connect`, `init_schema`(`closing`과 `with conn`으로 커밋 후 닫음).
- `src/shortlink/repository.py`: `format_timestamp`, `LinkRepository.create/get`. 호출마다 연결을 열고 닫으며, 충돌 시 최대 10회 재시도한 뒤 `RuntimeError`를 던진다. SQL은 모두 `?` 바인딩이다.
- `src/shortlink/dependencies.py`: `app.state`에서 settings와 repository를 꺼낸다.
- `src/shortlink/api.py`: `POST /links`. 요청 모델 `LinkIn(url: StrictStr)`을 추가했다.
- `src/shortlink/web.py`: `location_header_value`, `GET /`, `POST /`, `GET /{code}`.
- `src/shortlink/templates/base.html`, `home.html`, `result.html`, `not_found.html`: 목업의 구조, 클래스, 문구, title을 따랐다. `|safe`와 `Markup`은 쓰지 않았다.
- `src/shortlink/static/style.css`: 목업 공통 스타일 블록을 그대로 옮겼다. 구분 주석 두 줄만 뺐다.
- `src/shortlink/static/copy.js`: 목업의 인라인 스크립트를 그대로 옮겼다. `result.html`이 `<script src="/static/copy.js" defer>`로 불러온다.

## 구현한 수용 기준
- AC-1~AC-4, AC-15: `api.create_link`와 `repository.create`. `created_at`은 초 단위 `Z` 형식(D-8)이고, `url`은 원문 그대로이며, `http://`도 통과한다.
- AC-5~AC-8: `validation.validate_url`. 스킴 4종, 필드 없음, 숫자, 빈 문자열, `https://`는 422이고, 2,048자는 201, 2,049자는 422다.
  - 필드 없음, 숫자, null, 배열, 객체 아님, JSON 오류는 FastAPI 기본 422 본문이다.
  - 검증 실패는 `{"detail": "<문구>"}`로 `HTTPException(422)`를 통해 낸다.
- AC-9: 검증이 저장보다 먼저라서 거절 시 INSERT가 없다. 확인했다(API 거절 요청 뒤 `links` 행 수가 변하지 않음. 화면 입력 오류도 마찬가지).
- AC-10~AC-12: `web.follow_link`는 `Response(302, Location=location_header_value(url))`를 쓴다. 없는 코드는 `not_found.html`로 404다.
  - `<`, `>`, `"`가 든 ASCII URL은 그대로 나가고, 한글은 UTF-8 퍼센트 인코딩된다.
  - `%ED%95%9C`처럼 이미 인코딩된 부분은 건드리지 않는다.
- AC-13: `secrets.choice`로 만든 코드 100개가 모두 달랐다.
- AC-14: `create_app`을 두 번 만들어도 같은 `db_path`의 코드가 302로 이어졌다.
- AC-16~AC-18: `web.home`, `web.shorten_form`과 `home.html`, `result.html`. 폼, label, "줄이기" 버튼, `a.short-url`의 href, 원래 URL, "복사" 버튼, "다른 URL 줄이기"(`href="/"`)가 나온다.
- AC-19, AC-20: `web.shorten_form`이 `home.html`을 422로 렌더링한다. 입력값은 `value="..."`에 남고 오류 문구가 보인다. 자동 이스케이프가 동작해서 `&lt;script&gt;`로 나오고 `<script>alert` 원문은 없다. 결과 화면의 원래 URL도 같다.
- AC-21: `web.follow_link`와 `not_found.html`.
- AC-22: `base.html`에 `lang="ko"`와 viewport meta가 있다.
- AC-23: 폼으로 만든 코드도 `GET /{code}`가 302로 응답한다.

## 계획에 없던 판단
- `urlsplit`이 `ValueError`를 던지는 URL(예: `https://[`)은 스킴을 먼저 보고, 스킴이 http/https면 `MSG_NO_HOST`로 처리했다. 규칙 순서(스킴 → 호스트)를 유지하면서 500을 막으려는 것이다.
- API의 검증 실패는 `JSONResponse`를 직접 반환하지 않고 `HTTPException(422, detail=<문구>)`를 쓴다. `response_model`과 반환 타입을 스텁(`-> LinkOut`)대로 유지하기 위해서다. 응답 본문은 `{"detail": "<문구>"}`로 같다.
- `home.html`의 템플릿 변수는 `error`와 `url_value`로 정했다. 오류가 있을 때만 `aria-invalid`와 `aria-describedby`가 붙고, title도 오류일 때만 "입력 오류 — ShortLink"다. 목업의 홈/오류 두 화면을 한 템플릿으로 합친 결과다.
- 복사 스크립트는 `base.html`의 `{% block scripts %}`에 두었다. 목업 위치(`</main>` 뒤)와 같다.

## 남은 문제와 질문
- 이 JSON은 아직 처리하지 못해 500이 난다. `{"url": "https://e.com/\ud800"}`처럼 짝 없는 서로게이트가 든 `url`은 sqlite3 바인딩 단계에서 `UnicodeEncodeError`가 난다. 승인된 검증 규칙(D-1~D-8)에 없어서 임의로 규칙을 추가하지 않았다. 422로 거절하려면 계획에 규칙을 넣어야 한다.
- 이 작업 트리에는 test-writer가 만든 `tests/conftest.py`, `tests/test_api_links.py`, `tests/test_redirect.py` 변경이 보인다. 내가 건드린 파일이 아니다.
- 테스트가 틀렸다고 판단한 부분은 없다.
