---
seq: 2
sender: "main"
receiver: "implementer"
type: "T-TASK"
timestamp: "2026-10-29T04:40:41.714Z"
agent: "implementer"
agent_id: "abf585d38424abbbe"
turn: 1
reply_to: null
chars: 1804
tokens_est: 766
wait_s: null
---

F1(단축 URL 생성과 리다이렉트)을 구현해 줘. test-writer가 동시에 tests/를 작성하고 있다.

읽을 것:
- 설계서: docs/features/F1.md (AC-1~AC-23)
- 구현 계획: docs/plans/F1-plan.md — 모듈 구조, 인터페이스, 검증 순서와 오류 문구(3.2 표), 화면 고정 요소(3.6)가 모두 여기 있다. 그대로 따른다.
- 해석 결정: docs/plans/F1-decisions.md (D-1~D-7: 스킴 대소문자 무시, 공백/제어 문자 거절, RedirectResponse 사용, 오류 형식 {"detail": ...}, 없는 코드는 항상 404 HTML, 입력칸 type="text" inputmode="url", 폼 url 누락 시 422 HTML)
- 화면 목업: docs/plans/mockups/F1-home.html, F1-result.html, F1-error.html, F1-not-found.html (인덱스 F1-index.html). 문구, 마크업 구조, 클래스, 색을 그대로 따른다.

스켈레톤(이미 있음, 시그니처 유지하고 본문 구현):
- src/shortlink/db.py, validation.py, links.py, api.py, web.py
- src/shortlink/main.py의 create_app()은 이미 db.init_db 호출과 라우터 등록(api 다음 web)을 하도록 연결해 두었다. 고정 계약이니 확장만.

만들 것:
- 템플릿: src/shortlink/templates/base.html(공통 head: <html lang="ko">, charset, viewport meta `<meta name="viewport" content="width=device-width, initial-scale=1">`, /static/style.css 링크), home.html(오류/제출값 선택적 표시), result.html, not_found.html
- 정적 파일: src/shortlink/static/style.css(목업의 <style> 내용을 그대로), src/shortlink/static/copy.js(결과 목업의 스크립트), result.html에서 <script src="/static/copy.js" defer></script>
- Jinja2 자동 이스케이프를 끄지 말고 |safe나 Markup을 쓰지 않는다.

주의:
- POST /links는 await request.json()으로 직접 읽어 Pydantic 형 변환을 피한다(숫자 url은 422여야 함). JSON 파싱 실패나 객체가 아닌 본문도 422 {"detail": ...}.
- 오류 문구는 계획 3.2 표의 문자열을 글자 그대로 쓴다. API detail과 화면 오류 메시지가 같다.
- GET /{code}는 web 라우터 맨 마지막. 302는 RedirectResponse(url, status_code=302).
- created_at은 'YYYY-MM-DDTHH:MM:SSZ' UTC.
- 끝나면 `uv run ruff check src`, `uv run ruff format src` 실행, 그리고 서버가 import되는지 간단히 확인(`uv run python -c "from shortlink.main import create_app; create_app()"`는 cwd에 shortlink.db를 만들 수 있으니 임시 경로 Settings로 확인하고 만들어진 파일은 지운다).
- tests/는 건드리지 않는다. 저장소 밖 경로는 쓰지 않는다. git 커밋은 하지 않는다.

보고는 네 정의의 보고 형식으로.
