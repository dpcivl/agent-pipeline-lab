---
seq: 2
sender: "main"
receiver: "implementer"
type: "T-TASK"
timestamp: "2026-10-29T08:13:30.285Z"
agent: "implementer"
agent_id: "a7e1816d2a97d608a"
turn: 1
reply_to: null
chars: 1728
tokens_est: 706
wait_s: null
---

F2(클릭 통계와 커스텀 별칭)를 구현해 줘.

읽을 것:
- 설계서: `docs/features/F2.md`
- 구현 계획: `docs/plans/F2-plan.md` (인터페이스, 문구, 검사 순서, 해석 결정 D-1~D-11이 모두 여기 있다. 계획을 그대로 따른다.)
- 화면 목업: `docs/plans/mockups/F2-index.html`과 거기서 링크된 F2-*.html. 템플릿 마크업(클래스, id, aria 속성, 문구)은 목업과 같게 하고, 목업의 "F2 추가 스타일" 블록을 `src/shortlink/static/style.css` 끝에 그대로 붙인다.
- 기존 F1 코드와 결정: `docs/plans/F1-plan.md`

스켈레톤: `src/shortlink/validation.py`(`validate_alias`, 문구 상수), `repository.py`(`Link` 필드, `AliasTakenError`, `create(url, alias=None)`, `record_click`), `api.py`(`LinkIn.alias`, `LinkStatsOut`, `link_stats`), `web.py`(`display_timestamp`, `stats_page`, `_stats_context`), `db.py`(docstring의 TODO) 에 스텁이 있다. `NotImplementedError`를 모두 구현으로 바꾼다.

해야 할 일 요약:
1. `validate_alias` (계획 3.1 순서와 문구).
2. `db.init_schema`: 새 DB는 5열 스키마, F1 DB(3열)는 `PRAGMA table_info`로 확인해 없는 열만 `ALTER TABLE ADD COLUMN`. 여러 번 호출해도 안전.
3. 저장소: 별칭 INSERT 한 번, PK 충돌 시 `AliasTakenError`. `record_click`은 SQL 안에서 `clicks = clicks + 1`로 원자적 증가 후 행을 다시 읽어 반환, 없으면 None. `get`/`record_click` 모두 새 열을 `Link`에 채운다.
4. API: `POST /links` alias 처리(URL 먼저 검증 → 별칭 검증 → 저장, 422 `{"detail": 문구}`, 409 `{"detail": MSG_ALIAS_TAKEN}`), `GET /links/{code}/stats` (404 JSON `{"detail": MSG_LINK_NOT_FOUND}`).
5. 웹: 폼 `alias`(빈 값 = 없음), 오류 시 422/409와 `url_value`, `alias_value` 유지, `error_field`로 원인 칸에만 aria-invalid. `GET /{code}`는 `record_click` 사용. `GET /stats/{code}` 통계 화면, 없으면 F1 `not_found.html` 404. 결과 화면에 "통계 보기" 링크(`/stats/{code}`).
6. F1 동작(기존 `tests/`의 175개 테스트)은 모두 그대로 통과해야 한다. 홈 화면 오류 문구의 id가 `url-error`에서 `form-error`로 바뀌는 것은 목업대로 한다.

`tests/`는 test-writer가 동시에 작성 중이니 건드리지 마. 끝내기 전에 `uv run pytest`(기존 테스트), `uv run ruff check src`, `uv run ruff format src`를 실행하고, 계획에 없는 판단을 했다면 보고에 적어 줘.
