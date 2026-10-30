---
seq: 2
sender: "main"
receiver: "implementer"
type: "T-TASK"
timestamp: "2026-10-29T07:12:04.889Z"
agent: "implementer"
agent_id: "af5d8999c063e4176"
turn: 1
reply_to: null
chars: 1343
tokens_est: 600
wait_s: null
---

F2(클릭 통계와 커스텀 별칭)를 구현해 줘.

읽을 문서:
- 설계서: docs/features/F2.md
- 구현 계획: docs/plans/F2-plan.md (인터페이스, 문구, 라우트, 템플릿 컨텍스트가 모두 여기 있음)
- 해석 결정: docs/plans/F2-decisions.md (E-1~E-14)
- 화면 목업: docs/plans/mockups/F2-index.html 과 거기서 링크된 F2-*.html. 문구, 배치, 클래스, CSS는 목업을 그대로 따른다.

할 일:
1. 스켈레톤의 `raise NotImplementedError` 스텁을 모두 구현한다: validation.validate_alias, db.migrate_schema(+ init_schema의 CREATE TABLE에 새 열 추가 후 migrate_schema 호출), repository(Link 확장 필드 채우기, create(alias=...), get이 clicks/last_accessed_at 반환, record_click), api(alias 처리·409, GET /links/{code}/stats), web(폼 alias 처리 422/409, GET /{code}에서 record_click, GET /stats/{code}).
2. 템플릿: home.html(별칭 입력칸, form-error/aria 처리, error_field), result.html("통계 보기" 상대 링크 + link-row, 컨텍스트에 code), 새 stats.html. not_found.html은 그대로.
3. style.css: 목업 <style>의 공통 블록 전체(F1 블록 + "F2 추가 스타일")와 같게 만든다.

주의:
- F1 기존 테스트(tests/test_*.py, 175개)는 수정 없이 계속 통과해야 한다. 특히 결과 화면에서 href가 `<base_url>/`로 시작하는 링크는 단축 URL 하나뿐이어야 하므로 "통계 보기"는 반드시 상대 경로 `/stats/{code}`.
- 별칭 문자 검사는 ASCII만(`re.fullmatch(r"[A-Za-z0-9-]+", ...)`), 예약어 비교는 대소문자 무시.
- 클릭 증가는 UPDATE 한 문장으로 원자적으로.
- 이스케이프 유지(|safe, Markup 금지). SQL은 파라미터 바인딩.
- 이 환경에서 `uv run pytest`가 애플리케이션 제어 정책으로 막힐 수 있다. 그러면 `uv run python -m pytest -q`를 쓴다.
- 새 테스트는 test-writer가 동시에 tests/에 쓰고 있다. tests/는 수정하지 않는다. 끝내기 전에 ruff check/format(src)과 기존 테스트 실행.
