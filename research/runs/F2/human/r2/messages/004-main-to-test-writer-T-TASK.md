---
seq: 4
sender: "main"
receiver: "test-writer"
type: "T-TASK"
timestamp: "2026-10-30T00:38:39.151Z"
agent: "test-writer"
agent_id: "a8b445add493b81db"
turn: 1
reply_to: null
chars: 1244
tokens_est: 610
wait_s: null
---

F2(클릭 통계와 커스텀 별칭)의 테스트를 작성해 줘. 사람이 계획과 목업을 승인했다.

읽을 문서:
- 설계서: docs/features/F2.md (수용 기준 AC-1~AC-23)
- 구현 계획: docs/plans/F2-plan.md — 3절 인터페이스와 문구, 4절 "수용 기준과 테스트 대응"(파일 배치와 확인할 것), 5절 해석 결정 D2-1~D2-9
- 화면 목업: docs/plans/mockups/F2-*.html (문구, 요소, 속성 기준)
- 기존 테스트 스타일과 픽스처: tests/conftest.py(고정 계약: settings, app, client 픽스처. count_links 있음), tests/test_web.py(HTML 파싱 헬퍼 방식), tests/test_api_links.py 등

할 일 (쓰기 영역: tests/** 만):
- 새 파일: tests/test_aliases.py, tests/test_stats.py, tests/test_web_f2.py, tests/test_migration.py
- 기존 파일에 추가: tests/test_validation.py(validate_alias), tests/test_repository.py(create alias, AliasTakenError, record_click)
- conftest.py는 확장만 한다(새 픽스처 추가 가능, 기존 픽스처 의미 변경 금지).
- 기존 F1 테스트는 고치지 않는다(AC-23 회귀 확인용).

주의:
- 구현은 implementer가 동시에 작성 중이다. 지금 src/에는 스텁(NotImplementedError)이 있으므로 테스트가 실패하는 것은 정상이다. 계획서의 인터페이스(함수 이름, 시그니처, 문구 상수, 템플릿 클래스/id)를 기준으로 쓴다.
- 문구는 validation 모듈 상수를 import해서 비교하는 방식을 우선한다(화면 테스트는 HTML에 그 문구가 보이는지).
- 시각 관련 테스트는 시계에 너무 민감하지 않게(요청 전후 범위 비교).
- Windows에서 tmp 정리가 막히지 않게 sqlite 연결은 항상 닫는다.
- 마이그레이션 테스트는 F1 스키마(code, url, created_at 3열)로 DB 파일을 직접 만든 뒤 create_app.

끝나면 `uv run ruff check tests`, `uv run ruff format tests`를 돌리고, 만든 테스트 목록(파일별 테스트 이름과 대응 AC)을 짧게 보고해 줘. 커밋은 하지 않는다.
