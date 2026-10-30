---
seq: 4
sender: "main"
receiver: "test-writer"
type: "T-TASK"
timestamp: "2026-10-29T23:51:47.344Z"
agent: "test-writer"
agent_id: "af331b1f347ae9d90"
turn: 1
reply_to: null
chars: 1246
tokens_est: 582
wait_s: null
---

F2(클릭 통계와 커스텀 별칭)의 수용 기준 테스트를 작성해 주세요.

읽을 문서:
- 설계서: docs/features/F2.md (AC-1~AC-23)
- 구현 계획(사람 승인 완료, 기준 문서): docs/plans/F2-plan.md — 3절 인터페이스(문구 상수, 상태 코드, 응답 필드), 4절 AC와 테스트 대응표, 5절 해석 결정 D-F2-1~9
- 화면 목업: docs/plans/mockups/F2-index.html 과 F2-*.html (마크업: id="alias", name="alias", label for="alias", id="form-error", "통계 보기" 링크 href="/stats/<code>", 통계 화면 "아직 없음", 클릭 수는 천 단위 쉼표)
- 기존 테스트 스타일: tests/conftest.py(고정 픽스처 settings/app/client, count_links), tests/test_web.py(HTML 파싱 방식)

할 일:
- 계획 4절의 새 파일 tests/test_aliases.py, tests/test_stats.py, tests/test_web_f2.py 작성. 보조 테스트(validate_alias 단위 테스트, F1 스키마 DB 마이그레이션 테스트, repository AliasTakenError/record_click)도 포함.
- 메시지 문구는 src/shortlink/validation.py의 MSG_ALIAS_* 상수를 import해서 비교해도 됩니다(상수는 이미 정의됨).
- conftest.py는 확장만 허용(예: 링크의 clicks를 DB에서 직접 읽는 헬퍼 픽스처). 기존 F1 테스트 파일은 고치지 마세요.

주의:
- src/는 implementer가 동시에 구현 중입니다. 지금은 스텁(NotImplementedError)이라 새 테스트가 실패하는 게 정상입니다. src/는 건드리지 마세요.
- 이 PC에서는 `uv run pytest`가 애플리케이션 제어 정책으로 막힙니다. `uv run python -m pytest`로 실행하세요. 린트: `uv run ruff check src tests`, `uv run ruff format tests`.
- Windows: SQLite 연결은 항상 닫아야 tmp 정리가 됩니다(contextlib.closing).
- git 커밋은 하지 마세요.

끝나면 파일별 테스트 개수, AC별 대응 테스트 이름, 수집(collect) 오류가 없는지 확인한 결과를 짧게 보고해 주세요.
