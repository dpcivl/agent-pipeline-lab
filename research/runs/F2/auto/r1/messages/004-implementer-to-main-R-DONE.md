---
seq: 4
sender: "implementer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T07:14:43.237Z"
agent: "implementer"
agent_id: "af5d8999c063e4176"
turn: 1
reply_to: 2
chars: 2859
tokens_est: 1165
wait_s: null
---

## 결과: 완료

## 변경 파일
- src/shortlink/validation.py: `validate_alias()` 구현 (문자열 아님 → 길이 → `re.fullmatch(r"[A-Za-z0-9-]+")` → 하이픈 양끝 → 예약어(소문자 비교) 순서, 입력 그대로 반환). `import re` 추가.
- src/shortlink/db.py: `init_schema`의 CREATE TABLE에 `clicks`, `last_accessed_at` 추가 후 `migrate_schema(conn)` 호출. `migrate_schema`는 `PRAGMA table_info(links)`로 빠진 열만 `ALTER TABLE ... ADD COLUMN`.
- src/shortlink/repository.py: `create(url, alias=...)`는 alias를 코드로 한 번만 INSERT하고 `IntegrityError`면 `AliasConflictError`를 던진다. `get`은 clicks와 last_accessed_at까지 채운다. `record_click`은 UPDATE 한 문장과 rowcount 확인, 이후 SELECT를 한 트랜잭션에서 한다. 행 변환용 `_SELECT_LINK`, `_link_from_row` 헬퍼 추가.
- src/shortlink/api.py: URL 검증 후 alias 검증(`""` 포함 422), 충돌 시 409 `MSG_ALIAS_TAKEN`. `GET /links/{code}/stats`는 `repository.get`을 쓰고 없으면 JSON 404.
- src/shortlink/web.py: 폼 alias 처리(빈 문자열이면 없음, 422, 409). `home`과 오류 응답은 `error_field`, `alias_value` 컨텍스트를 `_home_error` 헬퍼로 넘긴다. 결과 화면에 `code` 전달. `GET /stats/{code}`를 구현했고, `GET /{code}`는 `record_click`을 쓴다.
- src/shortlink/templates/home.html: 별칭 입력칸과 힌트, `field`/`form-actions` 구조, 오류 문단 `id="form-error"`, `error_field`에 따른 `aria-invalid`와 `aria-describedby`.
- src/shortlink/templates/result.html: `link-row` 안에 상대 경로 `/stats/{{ code }}` "통계 보기"와 "다른 URL 줄이기".
- src/shortlink/templates/stats.html: 새 통계 화면. 목업 구조 그대로. 시각은 `<time>`, 마지막 접근이 없으면 `<dd class="muted">아직 없음</dd>`.
- src/shortlink/static/style.css: 목업 공통 블록(F1 블록과 "F2 추가 스타일")과 일치하는 것을 `diff --strip-trailing-cr`로 확인. 작업 트리의 CRLF 혼재를 LF로 정리했다. 인덱스는 원래 LF다.

## 구현한 수용 기준
- AC-1~AC-9 (별칭 API): validation.py `validate_alias`, repository.py `create`, api.py `create_link`
- AC-10, AC-11 (폼 별칭, 422/409, 입력값 유지): web.py `shorten_form`, home.html
- AC-12~AC-16 (통계 API, 클릭 수 증가, 조회와 404는 세지 않음): repository.py `record_click`/`get`, api.py `get_link_stats`, web.py `follow_link`
- AC-17, AC-18, AC-21, AC-22 (통계 화면, 404, 이스케이프, lang/viewport): web.py `stats_page`, stats.html, base.html
- AC-19 ("통계 보기" 링크): result.html
- AC-20와 F1 DB 이전: db.py `init_schema`와 `migrate_schema`
- AC-23 (F1 회귀): 기존 테스트 통과

검증: `uv run ruff format src`와 `uv run ruff check src`는 이상 없음. `uv run python -m pytest -q`는 323개 통과했다. 이 중 기존 F1 테스트가 175개이고, 나머지는 test-writer가 쓴 새 테스트로 보인다. 그 시점 tests/에는 `test_alias_api.py`와 `test_alias_validation.py`만 있었고, 다른 새 테스트 파일은 없었다. 별칭 오류 화면과 통계 화면의 HTML은 임시 스크립트로 직접 확인했다.

## 계획에 없던 판단
- 폼 오류 문단의 id를 F1의 `url-error`에서 `form-error`로 바꿨다. F2 목업이 그렇게 되어 있고, 기존 테스트 어디에서도 `url-error`를 쓰지 않는다.
- URL 오류일 때 `aria-invalid`와 `aria-describedby="form-error"`는 URL 칸에만 붙인다. 별칭 오류일 때는 별칭 칸에 `aria-describedby="form-error alias-hint"`를 붙인다. 오류가 없을 때 별칭 칸은 `aria-describedby="alias-hint"`다. 모두 목업과 같다.
- 별칭 충돌의 `AliasConflictError`는 `create` 안에서 `from None`으로 다시 던진다.

## 남은 문제와 질문
- 없음. tests/는 수정하지 않았다.
- 중간에 한 번 Bash 도구로 파이썬 스크립트를 실행하다 인용 문제로 실패했다. 그때는 아무 파일도 바뀌지 않았고, 이후 Edit 도구로 다시 적용했다.
