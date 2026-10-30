---
seq: 3
sender: "main"
receiver: "test-writer"
type: "T-TASK"
timestamp: "2026-10-29T08:13:30.300Z"
agent: "test-writer"
agent_id: "addded36c42b16b35"
turn: 1
reply_to: null
chars: 1545
tokens_est: 712
wait_s: null
---

F2(클릭 통계와 커스텀 별칭)의 테스트를 작성해 줘.

읽을 것:
- 설계서: `docs/features/F2.md` (수용 기준 AC-1~AC-23이 기준)
- 구현 계획: `docs/plans/F2-plan.md` — 특히 3절 인터페이스(문구 상수, 검사 순서, API 응답 모양), 4절 "수용 기준과 테스트 대응" 표, 5절 해석 결정 D-1~D-11
- 화면 목업: `docs/plans/mockups/F2-index.html`과 F2-*.html (문구 기준)
- 스켈레톤: `src/shortlink/validation.py`, `repository.py`, `api.py`, `web.py`의 새 시그니처와 docstring. 구현은 implementer가 동시에 만들고 있으므로 지금은 스텁(`NotImplementedError`)이다. 현재 구현 동작이 아니라 설계서와 계획을 기준으로 쓴다.

만들 것 (계획 4절):
- 새 파일: `tests/test_aliases.py`(AC-1~9), `tests/test_stats.py`(AC-12~16, 20), `tests/test_web_f2.py`(AC-10, 11, 17, 18, 19, 21, 22), `tests/test_migration.py`(F1 3열 스키마 DB를 sqlite3로 직접 만들어 행을 넣은 뒤 `create_app` → 기존 링크 302, clicks 0에서 시작, 리다이렉트 뒤 1; `init_schema` 반복 호출 안전).
- 기존 `tests/test_validation.py`에 `validate_alias` 규칙 순서와 문구 테스트, `tests/test_repository.py`에 `create(alias=...)` 충돌 시 `AliasTakenError`와 저장 없음, `record_click` 증가와 없는 코드 None 테스트를 추가.
- 기존 F1 테스트는 고치지 않는다(AC-23은 기존 테스트 전체가 계속 통과하는 것으로 확인). `conftest.py`는 확장만(예: 특정 코드의 clicks를 DB에서 직접 읽는 헬퍼 픽스처).

주의:
- 경계값과 실패 경로를 포함한다(3자/31자, 4자/30자, 공백·`_`·`/`·`.`·한글, 앞뒤 하이픈, 예약어 9개 + 대문자 예약어, 무작위 코드와 같은 별칭 409, `alias: null`, `alias: ""`, `alias: 123`).
- 422/409 뒤에는 `count_links()`로 저장이 없음을 확인한다.
- HTML은 상태 코드, `text/html`, 문구, `value="..."`, 링크 `href`, 이스케이프(`&lt;script&gt;`)를 확인한다. 마크업 세부(공백, 속성 순서)에 지나치게 묶이지 않게 쓴다.
- 시각 형식은 `^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$`.

`src/`는 수정하지 마. 끝내기 전에 `uv run ruff check tests`와 `uv run ruff format tests`를 실행해 줘. 스텁 때문에 새 테스트가 실패하는 건 정상이다. 다만 수집(collection) 오류는 없어야 한다.
