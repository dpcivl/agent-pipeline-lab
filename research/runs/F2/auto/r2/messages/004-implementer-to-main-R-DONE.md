---
seq: 4
sender: "implementer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T08:15:35.413Z"
agent: "implementer"
agent_id: "a7e1816d2a97d608a"
turn: 1
reply_to: 2
chars: 2867
tokens_est: 1266
wait_s: null
---

## 결과: 완료
기존 테스트 175개는 모두 통과했고 `ruff check src`와 `ruff format src`도 깨끗하다. F2 새 테스트는 test-writer가 작성 중이라 돌리지 않았다. 대신 스크래치 스크립트로 F1 형식(3열) DB 이전, 별칭 생성, 409/422, 클릭 증가, 통계 화면 404를 확인했다.

## 변경 파일
- `src/shortlink/validation.py`: `validate_alias`를 3.1 순서와 문구대로 구현했다. 문자 검사는 `re.fullmatch(r"[A-Za-z0-9-]+")`이고 예약어는 `lower()`로 비교한다.
- `src/shortlink/db.py`: 새 DB는 5열 스키마로 만든다. 기존 DB는 `PRAGMA table_info(links)`로 확인해 없는 열만 `ALTER TABLE ADD COLUMN`한다. 여러 번 불러도 안전하다.
- `src/shortlink/repository.py`: `create(url, alias)`는 INSERT 한 번을 하고, `IntegrityError`가 나면 `AliasTakenError`를 던진다. `get`과 `record_click`은 새 열을 `Link`에 채운다. `record_click`은 `UPDATE ... clicks = clicks + 1` 후 `rowcount == 0`이면 `None`, 아니면 같은 트랜잭션에서 행을 다시 읽어 돌려준다.
- `src/shortlink/api.py`: `POST /links`는 URL 검증 → 별칭 검증 → 저장 순서이고, 422와 409 본문은 `{"detail": 문구}`다. `GET /links/{code}/stats`도 구현했고, 없는 코드는 404 `{"detail": MSG_LINK_NOT_FOUND}`다.
- `src/shortlink/web.py`:
  - 폼 `alias`를 처리한다. 빈 값은 별칭 없음으로 본다.
  - 오류 시 422/409로 `error_field`, `url_value`, `alias_value`를 넘긴다.
  - `GET /{code}`는 `record_click`을 쓴다.
  - `GET /stats/{code}`, `_stats_context`, `display_timestamp`를 구현했다.
  - 결과 화면 컨텍스트에 `code`를 추가했다.
- `src/shortlink/templates/home.html`: 목업대로 `div.field` 구조, 별칭 입력칸과 안내 문구, `id="form-error"`로 바꿨다. `aria-invalid`는 `error_field`와 같은 칸에만 붙는다.
- `src/shortlink/templates/result.html`: `div.link-row`에 "통계 보기"(`/stats/{{ code }}`)와 "다른 URL 줄이기"를 나란히 뒀다.
- `src/shortlink/templates/stats.html`: 새 통계 화면이다. 목업 마크업과 같다.
- `src/shortlink/static/style.css`: 목업의 "F2 추가 스타일" 블록을 `F2-home.html`에서 그대로 복사해 끝에 붙였다.

## 구현한 수용 기준
- AC-1~AC-9 (별칭 생성, 리다이렉트, 길이·문자·예약어, 409, 대소문자, 저장 없음): `validation.validate_alias`, `repository.create`, `api.create_link`.
- AC-10, AC-11 (폼 별칭 입력칸, 422/409 오류 화면, 입력값 유지): `templates/home.html`, `web.shorten_form`.
- AC-12~AC-16 (통계 API, 클릭 증가, 조회와 404는 세지 않음): `repository.record_click`, `web.follow_link`, `api.link_stats`.
- AC-17~AC-19, AC-21, AC-22 (통계 화면, 404, "통계 보기" 링크, 이스케이프, lang/viewport): `web.stats_page`, `templates/stats.html`, `templates/result.html`. 이스케이프는 Jinja 자동 이스케이프에 맡겼다.
- AC-20, D-11 (재생성 후 유지, F1 DB 이전): `db.init_schema`.
- AC-23: 기존 175개 테스트 통과.

## 계획에 없던 판단
- 비문자열 `alias`(숫자, 배열 등)의 422 본문은 FastAPI/pydantic 기본 형식(detail이 리스트)이다. 스켈레톤의 `LinkIn.alias: StrictStr | None`을 그대로 뒀고, F1에서 `url`이 비문자열일 때와 같은 규칙이다. 계획 3.3은 이 경우도 `{"detail": "<문구>"}`로 읽힐 수 있다. test-writer가 비문자열 `alias`의 detail 본문(`MSG_ALIAS_NOT_STRING`)까지 검사하면 이 부분이 실패한다. 그렇게 하려면 `LinkIn.alias`를 `object | None`으로 바꾸는 방법이 있는데, 스텁 시그니처를 건드리는 일이라 하지 않았다.
- `home.html`의 별칭 칸은 오류가 없을 때와 `error_field`가 `url`일 때 `aria-describedby="alias-hint"`를 갖는다. 목업이 기본 상태에서 그렇게 돼 있어서 따랐다.
- 이전 코드가 동시 시작에서 열 추가가 겹치는 경우(duplicate column)는 따로 처리하지 않았다. 한 프로세스가 `create_app`을 부르는 흐름이라 계획 범위로 봤다.

## 남은 문제와 질문
- 없음. 새 `.html`과 `.css` 파일은 LF로 썼는데, 기존 템플릿 일부는 CRLF라 줄바꿈이 섞여 있다. git이 알아서 맞추는 수준이다(경고만 뜸).
