---
seq: 5
sender: "implementer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T23:54:26.494Z"
agent: "implementer"
agent_id: "adf655f5c26eda860"
turn: 1
reply_to: 3
chars: 2801
tokens_est: 1255
wait_s: null
---

## 결과: 완료

## 변경 파일
- /src/shortlink/validation.py: `validate_alias` 구현. 계획 3.1의 순서와 문구를 따르고 입력은 그대로 돌려줌. 정규식은 `re.fullmatch`와 `isascii()`를 같이 씀.
- /src/shortlink/db.py: `init_schema`가 새 컬럼 `clicks`, `last_accessed_at`을 만들고, F1 DB에는 `PRAGMA table_info`로 확인해 없는 컬럼만 `ALTER TABLE ADD COLUMN`.
- /src/shortlink/repository.py: `create(alias=...)`는 INSERT 한 번으로 처리하고 충돌이면 `AliasTakenError`. `record_click`은 `UPDATE ... RETURNING` 한 문장. `get`이 `clicks`와 `last_accessed_at`까지 채움. 행→`Link` 변환 헬퍼 `_row_to_link` 추가.
- /src/shortlink/api.py: `POST /links`의 별칭 검증(422)과 중복(409) 처리, `GET /links/{code}/stats`.
- /src/shortlink/web.py: `format_display_timestamp`, `stats_page`, `POST /` 폼의 alias 처리와 `error_field`, `GET /{code}`가 `record_click` 사용, 홈 컨텍스트에 `alias_value`와 `error_field` 추가, 결과 컨텍스트에 `code` 추가.
- /src/shortlink/templates/home.html: 별칭 칸과 안내 문구, `form-error`, `error_field`에 따른 `aria-invalid`. 목업의 `.field`와 `.form-actions` 마크업을 따름.
- /src/shortlink/templates/result.html: "통계 보기" 링크를 `link-row`로 감쌈.
- /src/shortlink/templates/stats.html: 새 통계 화면. 목업의 `stats`와 `stats-empty` 마크업을 따름.
- /src/shortlink/static/style.css: 목업의 "F2 추가 스타일" 블록을 끝에 그대로 덧붙임. 기존 파일이 CRLF라서 줄바꿈을 CRLF로 맞춤.

## 구현한 수용 기준
- AC-1~9: validation.py, repository.py, api.py의 `create_link`
- AC-10, 11: web.py `shorten_form`, home.html
- AC-12~16: repository.py `record_click`과 `get`, api.py `get_link_stats`, web.py `follow_link`
- AC-17, 18, 21, 22: web.py `stats_page`, stats.html (Jinja2 자동 이스케이프, base.html의 lang과 viewport)
- AC-19: result.html
- AC-20: SQLite 파일에 저장
- AC-23: 기존 테스트 통과
- F1 DB 마이그레이션: db.py. 확인 방법은 아래 "검증"에 적음.

## 계획에 없던 판단
- 홈 폼의 오류 문구 id를 F1의 `url-error`에서 `form-error`로 바꿈. 계획 3.4와 목업(F2-alias-error, F2-alias-conflict)을 따른 것이고, 기존 F1 테스트는 이 id에 의존하지 않아 통과함.
- 홈 폼 레이아웃을 목업대로 URL 칸, 별칭 칸, 버튼의 세로 배치로 바꿈. F1의 `field-row`(입력칸과 버튼을 가로로 배치) 마크업은 홈 화면에서 쓰지 않지만, CSS는 남겼고 `.short-url-row`가 계속 씀.
- 별칭 칸이 오류 상태가 아닐 때도 `aria-describedby="alias-hint"`를 붙임. 목업 F2-home과 같음.
- `record_click`은 `UPDATE ... RETURNING` 결과를 `fetchone` 대신 `fetchall`로 끝까지 읽은 뒤 커밋함. 미완료 문장 상태에서 커밋하지 않으려는 안전장치임.
- 결과 화면의 "통계 보기" 링크는 `{{ code | urlencode }}`를 씀. 코드는 영숫자와 하이픈뿐이라 값은 달라지지 않음.
- 통계 화면의 클릭 수는 `{:,}`로 포맷한 문자열을 템플릿에 넘김.
- 소스 파일은 CRLF였는데, 홈 화면과 통계 화면 템플릿은 Write로 새로 써서 LF가 됨. 나머지 py 파일은 Edit이라 줄바꿈이 유지됨. 줄바꿈이 CRLF와 LF로 섞여도 동작에는 영향이 없음.

## 검증
- `uv run ruff check src tests`는 통과했고, `uv run ruff format src`는 파일 1개를 재포맷함.
- `uv run python -m pytest -q`는 175개가 모두 통과함. 그 시점에 tests/ 안에 test-writer가 쓰던 test_aliases.py와 conftest.py의 변경이 있었고, 그것까지 포함한 결과임. 클릭 수, 통계, 화면 테스트 파일은 아직 없었음.
- 스크래치패드에서 수동 스모크 스크립트로 F1 스키마(3컬럼) DB를 만들어 확인함. 앱을 두 번 시작해도 오류가 없었고, 통계 `clicks`가 0에서 시작해 리다이렉트 302 뒤 1로 올랐음. 별칭 오류(422)와 중복(409) 화면에서는 입력값 유지와 `aria-invalid`가 목업대로였음. 통계 화면 이스케이프, "아직 없음", 없는 코드 404도 확인함.

## 남은 문제와 질문
- 없음. 테스트가 틀렸다고 판단한 곳도 없음.
