---
seq: 5
sender: "implementer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T02:19:59.117Z"
agent: "implementer"
agent_id: "a728f26e96b119b15"
turn: 1
reply_to: 3
chars: 2876
tokens_est: 1198
wait_s: null
---

## 결과: 완료
## 변경 파일
- `src/shortlink/codes.py`: `generate_code`(secrets 7자), `is_valid_code`, `build_short_url` 구현
- `src/shortlink/validation.py`: `validate_url` 구현. 계획의 순서와 문구를 따랐고, 받은 값을 그대로 반환
- `src/shortlink/db.py`: `connect`, `init_db` 구현
- `src/shortlink/repository.py`: `format_timestamp`, `LinkRepository`(create/get/count, PK 충돌 재시도, `CodeGenerationError`) 구현
- `src/shortlink/schemas.py`: `LinkCreate.check_url`이 `validate_url`을 호출하고 실패 시 `ValueError(message)`를 던짐
- `src/shortlink/deps.py`: `get_settings`, `get_repository` 구현
- `src/shortlink/api.py`: `POST /links` 구현(201)
- `src/shortlink/web.py`: `GET /`, `POST /`, `GET /{code}`, `get_templates` 구현. 모듈 수준 `templates`와 `TEMPLATES_DIR`를 추가
- `src/shortlink/templates/base.html`, `home.html`, `result.html`, `not_found.html`: 목업의 문구, 마크업, 클래스명대로 작성. 자동 이스케이프를 유지했고 `|safe`는 쓰지 않았으며 인라인 스크립트도 없음
- `src/shortlink/static/style.css`: 목업 `<style>` 내용을 그대로 옮김
- `src/shortlink/static/copy.js`: 결과 목업의 스크립트를 옮김. `result.html`에서만 `/static/copy.js`로 불러옴
- `src/shortlink/static/.gitkeep`, `src/shortlink/templates/.gitkeep`: 삭제

## 구현한 수용 기준
- AC-1~AC-4, AC-15: `api.py`의 `create_link`, `repository.py`의 `create`와 `format_timestamp`, `codes.py`
- AC-5~AC-8: `validation.py`의 `validate_url`과 `schemas.py`의 `LinkCreate`(스킴, 호스트, 길이, 타입, 빈 값). 필드 누락과 타입 오류는 Pydantic의 `StrictStr`이 처리
- AC-9: 검증은 저장 전에 끝나서 거절된 요청은 `repository.create`에 닿지 않음
- AC-10~AC-12, AC-14: `web.py`의 `follow`(302 `RedirectResponse`, 없는 코드 404). 요청마다 새 코드를 만들고 SQLite 파일에 저장
- AC-13: `codes.generate_code`와 `LinkRepository.create`의 충돌 재시도
- AC-16~AC-19, AC-22, AC-23: `web.py`의 `home`/`submit`과 `home.html`, `result.html`, `base.html`. 입력 오류는 422이고 제출 값이 `value`에 남음
- AC-20: Jinja2 자동 이스케이프. `<script>` 입력이 `&lt;script&gt;`로 나오는 것을 결과 화면과 오류 화면 모두에서 확인
- AC-21: `web.py`의 `follow`와 `not_found.html`

검증 결과는 다음과 같습니다.
- `TestClient`로 직접 확인했고, 위 동작이 모두 기대대로 나왔습니다.
- 저장소에 이미 있는 `tests/`도 실행했습니다. `uv run pytest`가 129개 통과했습니다.
- `uv run ruff check src`와 `uv run ruff format src`는 문제 없이 끝났습니다.

## 계획에 없던 판단
- 입력 오류 시 `aria-describedby`를 `"url-error url-hint"`로 했습니다. 목업 `F1-input-error.html`이 그렇게 되어 있습니다. 계획 4절에는 `"url-error"`만 적혀 있어 두 문서가 다릅니다. 오류가 없는 홈 화면에는 `aria-describedby="url-hint"`를 넣었습니다.
- `web.py`에 `TEMPLATES_DIR`를 자체 정의했습니다. `main.py`에서 가져오면 순환 import가 생기기 때문입니다.
- 4단계 공백과 제어 문자 검사에는 `str.isspace()`(유니코드 공백 포함)와 ASCII 제어 문자, 0x7F~0x9F(C1 제어 문자)를 포함했습니다. D-3의 "공백·제어 문자"를 넓게 해석한 것입니다.
- `urlsplit`이 `ValueError`를 던지는 경우(예: `http://[`)는 스킴이 http/https면 `MSG_NO_HOST`로, 아니면 `MSG_SCHEME`으로 422 처리했습니다. 500이 나지 않게 하려는 것입니다.
- `base.html`에 `title`, `content`, `scripts` 블록을 두었고, 결과 화면에만 `copy.js`를 불러옵니다.
- 계획 문서 헤더는 목업을 `F1-index.html`로 적고 있습니다. 실제 화면 목업은 `F1-home.html`, `F1-result.html`, `F1-input-error.html`, `F1-not-found.html`이며 이 네 개를 기준으로 구현했습니다. `F1-index.html`은 목업 목차 페이지로 보여 따르지 않았습니다.

## 남은 문제와 질문
- 없음. 테스트가 틀렸다고 판단되는 부분도 없습니다.
