---
seq: 4
sender: "main"
receiver: "test-writer"
type: "T-TASK"
timestamp: "2026-10-29T02:16:16.042Z"
agent: "test-writer"
agent_id: "af5f645dbd4eb649c"
turn: 1
reply_to: null
chars: 1449
tokens_est: 685
wait_s: null
---

F1(단축 URL 생성과 리다이렉트)의 테스트를 작성해 주세요.

## 기준 문서
- 설계서: `docs/features/F1.md` (v2, AC-1~AC-23) — 테스트의 최종 기준
- 구현 계획: `docs/plans/F1-plan.md` — 특히 3절 인터페이스(공개 이름, 검증 문구 상수 `MSG_*`), 4절 화면 규칙, 5절 수용 기준-테스트 대응표, 7절 해석 결정 D-1~D-9
- 화면 목업: `docs/plans/mockups/F1-home.html`, `F1-result.html`, `F1-input-error.html`, `F1-not-found.html` (문구 기준)
- 스켈레톤: `src/shortlink/` (지금은 스텁이라 테스트가 실패하는 것이 정상입니다. implementer가 동시에 구현 중입니다)

## 할 일
- 계획 5절 대응표대로 `tests/test_api_links.py`, `tests/test_redirect.py`, `tests/test_web.py`, `tests/test_validation.py`, `tests/test_repository.py`를 만듭니다. 모든 AC에 최소 하나의 테스트가 대응되게 하고, 경계값(2,048/2,049자)과 실패 경로를 포함합니다.
- HTTP는 `client` 픽스처로 검증합니다. 리다이렉트는 `follow_redirects=False`로 받습니다. 폼 제출은 `client.post("/", data={"url": ...})`.
- AC-9/AC-19의 "아무것도 저장되지 않음"은 `app.state.repository.count()`나 `settings.db_path`의 `links` 테이블을 sqlite3로 직접 세서 확인합니다.
- AC-14는 같은 `settings`로 `create_app`을 다시 만들어 새 `TestClient`로 확인합니다.
- 충돌 재시도는 `LinkRepository(db_path, code_generator=<고정 값을 내는 함수>, max_attempts=...)`로 검증합니다(먼저 `init_db`로 스키마 준비).
- 화면 HTML 검사는 지나치게 공백·속성 순서에 민감하지 않게 써 주세요(예: 정규식이나 핵심 부분 문자열). 단, 목업에서 정한 문구("줄이기", "복사", "다른 URL 줄이기", "링크를 찾을 수 없습니다", 오류 문구)와 `href`, `lang="ko"`, viewport meta는 확인합니다.
- 필요하면 `tests/conftest.py`에 픽스처를 추가할 수 있지만 기존 픽스처는 바꾸지 마세요.
- `src/`는 수정하지 마세요. 끝내기 전에 `uv run ruff check tests`, `uv run ruff format tests`를 실행하고, `uv run pytest --collect-only -q`로 수집 오류가 없는지 확인하세요.
- 보고는 에이전트 정의의 보고 형식을 따릅니다.
