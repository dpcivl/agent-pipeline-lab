---
seq: 3
sender: "main"
receiver: "implementer"
type: "T-TASK"
timestamp: "2026-10-29T02:16:16.030Z"
agent: "implementer"
agent_id: "a728f26e96b119b15"
turn: 1
reply_to: null
chars: 1354
tokens_est: 621
wait_s: null
---

F1(단축 URL 생성과 리다이렉트)을 구현해 주세요.

## 기준 문서
- 설계서: `docs/features/F1.md` (v2, AC-1~AC-23)
- 구현 계획: `docs/plans/F1-plan.md` — 모듈 구조, 인터페이스, 검증 규칙 순서와 문구, 화면 규칙, 해석 결정 D-1~D-9를 모두 따르세요.
- 화면 목업: `docs/plans/mockups/F1-home.html`, `F1-result.html`, `F1-input-error.html`, `F1-not-found.html` (문구·마크업 구조·클래스명·색을 그대로 따름)

## 할 일
1. 스켈레톤 스텁(`codes.py`, `validation.py`, `db.py`, `repository.py`, `schemas.py`, `deps.py`, `api.py`, `web.py`)의 `NotImplementedError`를 모두 구현합니다. 공개 이름과 시그니처는 테스트 작성자가 그대로 쓰고 있으니 바꾸지 마세요(추가는 가능). `main.py`의 `create_app` 연결은 이미 되어 있습니다.
2. 템플릿 `src/shortlink/templates/`에 `base.html`, `home.html`(입력 오류도 이 템플릿으로, `error`·`url` 변수), `result.html`, `not_found.html`을 만듭니다. 자동 이스케이프를 유지하고 `|safe`/`Markup`을 사용자 입력에 쓰지 마세요.
3. 정적 파일: 목업의 `<style>` 내용을 `src/shortlink/static/style.css`로, 결과 목업의 스크립트를 `src/shortlink/static/copy.js`로 옮기고 템플릿에서 `/static/style.css`, `/static/copy.js`로 참조합니다. 템플릿에 인라인 스크립트는 두지 마세요.
4. 상태 코드: 홈 200, 결과 200, 입력 오류 422, 찾을 수 없음 404, 리다이렉트 302(`RedirectResponse(url, status_code=302)`), API 생성 201.
5. 기존 `src/shortlink/static/.gitkeep`, `templates/.gitkeep`은 지워도 됩니다.

## 주의
- `tests/`는 test-writer가 동시에 작성 중입니다. 건드리지 마세요. 스스로 동작을 확인하려면 임시 스크립트나 `TestClient`를 저장소 밖 임시 위치가 아니라 커맨드라인(`uv run python -c ...`)으로 돌려 보세요.
- 끝내기 전에 `uv run ruff check src`, `uv run ruff format src`를 실행하세요.
- 보고는 에이전트 정의의 보고 형식을 따릅니다.
