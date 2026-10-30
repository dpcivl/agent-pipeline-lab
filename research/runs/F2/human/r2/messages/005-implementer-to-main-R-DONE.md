---
seq: 5
sender: "implementer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-30T00:40:22.840Z"
agent: "implementer"
agent_id: "a6f57ffdc2a6f9660"
turn: 1
reply_to: 3
chars: 2569
tokens_est: 1065
wait_s: null
---

## 결과: 완료
## 변경 파일
- src/shortlink/validation.py: validate_alias 구현. 순서는 비문자열, 길이, 문자 규칙(`re.fullmatch`), 예약어(소문자 비교).
- src/shortlink/db.py: init_schema의 CREATE TABLE에 새 열 2개 추가. ensure_click_columns는 PRAGMA table_info로 확인해 없는 열만 ALTER TABLE.
- src/shortlink/repository.py: `create(url, alias)`는 alias가 있으면 INSERT 1회, PRIMARY KEY 충돌이면 AliasTakenError. `get`은 새 열까지 읽는다. `record_click`은 SQL `clicks = clicks + 1`로 증가시키고 한 트랜잭션에서 갱신된 Link를 돌려주며, 없는 코드면 None. `_row_to_link` 헬퍼를 추가했다.
- src/shortlink/api.py: URL 검사 후 alias 검사(422), AliasTakenError는 409(MSG_ALIAS_TAKEN). `GET /links/{code}/stats`는 `get()`만 쓰고 없는 코드는 JSON 404.
- src/shortlink/web.py:
  - 폼 `alias` 처리(빈 문자열이면 별칭 없음). 오류 화면 컨텍스트는 error/error_field/url_value/alias_value.
  - result.html에 `code` 전달, `GET /stats/{code}`, `display_timestamp`.
  - `follow_link`는 `record_click`을 쓴다.
- src/shortlink/templates/home.html: 목업대로 `.field` 구조, 별칭 칸, `alias-hint`, `.form-actions`.
- src/shortlink/templates/result.html: `.result-actions` 행에 "통계 보기"(`/stats/{{ code }}`)와 "다른 URL 줄이기".
- src/shortlink/templates/stats.html: 새 파일. base.html을 상속하고 접근 기록이 없으면 `<dd class="muted">아직 없음</dd>`를 보여 준다.
- src/shortlink/static/style.css: 목업의 "F2 추가 스타일" 블록을 그대로 끝에 덧붙였다. F1 공통 스타일은 그대로다.

## 구현한 수용 기준
- AC-1~AC-9: validation.py(`validate_alias`), repository.py(`create`, `AliasTakenError`), api.py(`create_link`). 대소문자 구분은 BINARY 비교 그대로이고, 거절 시에는 저장하지 않는다.
- AC-10, AC-11: web.py(`shorten_form`)와 home.html. 422/409 오류 화면에서 URL과 별칭 값이 남고 자동 이스케이프된다.
- AC-12~AC-16, AC-20: api.py(`get_link_stats`), repository.py(`record_click`, `get`), web.py(`follow_link`). 없는 코드는 `record_click`이 None이라 아무것도 바뀌지 않는다.
- AC-17, AC-18, AC-21, AC-22: web.py(`link_stats_page`)와 stats.html. 원래 URL은 이스케이프되고 `|safe`는 쓰지 않았으며 `lang`과 viewport는 base.html이 제공한다.
- AC-19: result.html.
- AC-23: 기존 tests 175개가 모두 통과한다.
- F1 DB 호환(D2-9): 열 3개짜리 F1 스키마 DB로 임시 스모크를 돌렸다. 기존 링크가 302로 동작했고 통계는 clicks 0에서 접근 뒤 1이 되었다.

## 계획에 없던 판단
- 오류 문구의 id를 F1의 `url-error`에서 계획서 3.4절의 `form-error`로 바꿨다. 목업과 계획서 기준이다. 기존 tests에는 `url-error` 참조가 없다. URL 오류 화면은 F1과 문구와 위치가 같고 id와 `aria-describedby`만 달라졌다.
- URL 오류일 때도 오류 문구를 폼 맨 위에 두고 `aria-invalid`는 URL 칸에만 붙인다. 계획서의 error_field 규칙대로다.
- `GET /stats/{code}` 컨텍스트의 `created_at`, `last_accessed_at`에는 `format_timestamp()` 문자열(`<time datetime>`용)을 넣었다. 보이는 글자는 `*_display`에 `display_timestamp()` 결과를 넣었다. 스텁 docstring의 "datetime attr"을 이렇게 해석했다.

## 남은 문제와 질문
- 없음.
- ruff check src tests는 통과했고 ruff format src도 실행했다. pytest는 175개가 통과했다. 커밋은 하지 않았다.
- 새 F2 테스트는 아직 보지 못했다(test-writer가 작성 중이라 tests/에는 F1 테스트만 있다).
