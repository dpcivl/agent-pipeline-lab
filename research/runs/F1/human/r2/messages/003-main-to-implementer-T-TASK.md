---
seq: 3
sender: "main"
receiver: "implementer"
type: "T-TASK"
timestamp: "2026-10-29T06:33:33.425Z"
agent: "implementer"
agent_id: "a7209a70a1d337cf1"
turn: 1
reply_to: null
chars: 1751
tokens_est: 800
wait_s: null
---

F1(단축 URL 생성과 리다이렉트)을 구현해 주세요.

읽을 문서:
- 기능 설계서: docs/features/F1.md (수용 기준 AC-1~AC-23)
- 구현 계획(사람 승인 완료): docs/plans/F1-plan.md — 모듈 구조, 인터페이스, 검증 순서와 문구, 화면별 고정 문구, 설계서 해석 결정 D-1~D-9를 그대로 따르세요.
- 화면 목업: docs/plans/mockups/F1-home.html, F1-result.html, F1-input-error.html, F1-not-found.html (목록: F1-index.html). 문구, 마크업 구조(class, id, aria 속성), 색을 목업과 맞추세요.
- 고정 계약: CLAUDE.md

할 일:
1. 스텁(src/shortlink/validation.py, codes.py, db.py, links.py, api.py, web.py)의 NotImplementedError를 실제 구현으로 바꾸세요. 스텁에 있는 이름, 상수, 문구 상수는 유지합니다(테스트 작성자가 같은 인터페이스를 기준으로 동시에 테스트를 쓰고 있습니다). 특히 DB 테이블 이름은 `links`(테스트가 직접 행 수를 셉니다).
2. src/shortlink/main.py의 create_app()을 확장: init_schema(settings.db_path), app.state.store = LinkStore(settings.db_path), api.router 먼저, web.router 나중에 등록. 기존 이름·시그니처·/static 마운트는 유지.
3. 템플릿 src/shortlink/templates/(base.html, home.html, result.html, not_found.html)와 정적 파일 src/shortlink/static/style.css(목업의 <style> 내용), copy.js(목업 결과 화면의 스크립트)를 만드세요. Jinja2 자동 이스케이프를 쓰고 사용자 입력에 |safe/Markup을 쓰지 마세요. 모든 페이지에 <html lang="ko">와 viewport meta.
4. 주의점:
   - POST /links는 본문을 직접 JSON으로 읽고(Pydantic 자동 형 변환 회피), JSON 객체가 아니면 422 {"detail": ...}.
   - GET /{code}의 리다이렉트는 RedirectResponse 대신 Response(status_code=302, headers={"Location": ...})로, ASCII는 그대로 두고 비ASCII 문자만 UTF-8 퍼센트 인코딩(D-6).
   - created_at 형식 'YYYY-MM-DDTHH:MM:SSZ'(UTC, 초 단위).
   - 코드 생성은 secrets 사용, 충돌(IntegrityError) 시 최대 10번 재시도.
   - SQLite 연결은 작업마다 열고 닫기, 모든 쿼리 파라미터 바인딩.
   - POST / 폼에서 url 필드가 없어도 422 오류 화면(MSG_REQUIRED)이 나와야 합니다(FastAPI 기본 검증 오류 JSON이 나오지 않게).
   - 오류 화면은 상태 422, 입력칸에 제출한 값 유지(이스케이프), aria-invalid="true".
5. tests/는 수정하지 마세요. 끝내기 전에 uv run ruff check src, uv run ruff format src를 실행하고, 서버나 TestClient로 간단히 동작을 확인해도 좋습니다.

보고는 에이전트 정의의 보고 형식을 따르세요.
