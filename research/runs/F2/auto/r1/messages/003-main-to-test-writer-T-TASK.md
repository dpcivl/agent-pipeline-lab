---
seq: 3
sender: "main"
receiver: "test-writer"
type: "T-TASK"
timestamp: "2026-10-29T07:12:04.899Z"
agent: "test-writer"
agent_id: "ad449d73f4906be98"
turn: 1
reply_to: null
chars: 1230
tokens_est: 562
wait_s: null
---

F2(클릭 통계와 커스텀 별칭)의 수용 기준 테스트를 써 줘.

읽을 문서:
- 설계서: docs/features/F2.md (AC-1~AC-23)
- 구현 계획: docs/plans/F2-plan.md — 4절에 수용 기준별 테스트 파일과 확인할 것, 3절에 인터페이스(validate_alias, InvalidAliasError, MSG_ALIAS_* 상수, LinkRepository.create(url, alias=None), record_click, AliasConflictError, db.migrate_schema)가 있다.
- 해석 결정: docs/plans/F2-decisions.md (E-1~E-14)
- 화면 목업: docs/plans/mockups/F2-index.html 과 F2-*.html (문구 기준)
- 스켈레톤: src/shortlink/ (구현은 implementer가 동시에 진행 중이라 지금은 NotImplementedError가 난다. 인터페이스만 보고 쓴다)

할 일:
- 계획 4절의 새 파일: tests/test_alias_api.py, tests/test_alias_web.py, tests/test_stats_api.py, tests/test_stats_web.py, tests/test_alias_validation.py, tests/test_migration.py, 그리고 tests/test_repository.py에 F2 테스트 추가(기존 테스트는 그대로).
- 기존 F1 테스트는 수정하지 않는다. conftest.py는 확장만(필요하면 F1 스키마 DB를 만드는 헬퍼, 클릭 수를 직접 읽는 헬퍼 등).
- 화면 테스트는 tests/test_web.py의 HTMLParser 방식을 참고하되, 공용 헬퍼가 필요하면 새 모듈로 빼지 말고 각 파일에 두거나 conftest 픽스처로 둔다(기존 test_web.py는 건드리지 않는다).
- 경계값과 실패 경로 포함. 422/409 뒤 행 수 불변, 통계 화면 조회도 clicks를 늘리지 않음, 없는 코드 접근이 다른 링크 clicks를 바꾸지 않음, 앱 재생성 후 clicks 유지, F1 스키마 DB 이전.
- 이 환경에서 `uv run pytest`가 막히면 `uv run python -m pytest -q`를 쓴다. 지금은 구현 전이라 새 테스트가 실패하는 것이 정상이다. 수집 오류(import 에러 등)만 없게 확인하고, ruff check/format(tests)을 실행한다.
