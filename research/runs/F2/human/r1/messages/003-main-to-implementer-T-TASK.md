---
seq: 3
sender: "main"
receiver: "implementer"
type: "T-TASK"
timestamp: "2026-10-29T23:51:47.330Z"
agent: "implementer"
agent_id: "adf655f5c26eda860"
turn: 1
reply_to: null
chars: 1361
tokens_est: 609
wait_s: null
---

F2(클릭 통계와 커스텀 별칭)를 구현해 주세요.

읽을 문서:
- 설계서: docs/features/F2.md
- 구현 계획(사람 승인 완료, 기준 문서): docs/plans/F2-plan.md — 특히 3절 인터페이스와 5절 해석 결정 D-F2-1~9
- 화면 목업(문구·배치·색의 기준): docs/plans/mockups/F2-index.html 과 거기서 링크한 F2-*.html. 404 화면은 F1-not-found.html 그대로.
- F1 계획: docs/plans/F1-plan.md (D-1~D-11 유지)
- CLAUDE.md의 고정 계약

할 일:
- src/shortlink/ 안의 스텁(raise NotImplementedError)을 모두 구현: validation.validate_alias, repository.create(alias=...)·record_click·AliasTakenError, api.get_link_stats와 POST /links의 alias/409 처리, web.format_display_timestamp·stats_page, POST / 폼의 alias 처리(error_field 포함), GET /{code}가 record_click을 쓰도록 변경.
- db.init_schema: 새 컬럼 추가와 F1 DB 마이그레이션(PRAGMA table_info로 없는 컬럼만 ALTER TABLE ADD COLUMN).
- repository.get이 clicks, last_accessed_at까지 채우도록.
- 템플릿: home.html(별칭 칸, form-error, error_field에 따른 aria-invalid), result.html("통계 보기" 링크, 컨텍스트에 code 필요), 새 stats.html. 목업 마크업을 그대로 따릅니다.
- style.css 끝에 목업의 "F2 추가 스타일" 블록을 그대로 덧붙입니다.

주의:
- F1 동작과 기존 F1 테스트(tests/)는 그대로 통과해야 합니다. 홈 폼은 여전히 label for="url", name="url", "줄이기" 버튼, URL 오류 시 value 유지가 있어야 합니다.
- tests/는 test-writer가 동시에 작성 중이니 건드리지 마세요.
- 이 PC에서는 `uv run pytest`가 애플리케이션 제어 정책으로 막힙니다. `uv run python -m pytest`로 실행하세요. 린트: `uv run ruff check src tests`, `uv run ruff format src`.
- git 커밋은 하지 마세요(오케스트레이터가 체크포인트를 만듭니다).

끝나면 바꾼 파일 목록, 계획과 다르게 한 점(있다면 이유), 기존 테스트 실행 결과를 짧게 보고해 주세요.
