---
seq: 3
sender: "main"
receiver: "implementer"
type: "T-TASK"
timestamp: "2026-10-29T05:28:46.547Z"
agent: "implementer"
agent_id: "a76b9356aae1c5ad6"
turn: 1
reply_to: null
chars: 1462
tokens_est: 671
wait_s: null
---

F1(단축 URL 생성과 리다이렉트)을 구현해 줘. 사람이 계획과 목업을 승인했다.

읽을 것:
- 설계서: docs/features/F1.md (수용 기준 AC-1~AC-23)
- 구현 계획: docs/plans/F1-plan.md (특히 3절 인터페이스, 5절 해석 결정 D-1~D-8은 승인된 결정이니 그대로 따른다)
- 화면 목업: docs/plans/mockups/F1-index.html, F1-home.html, F1-result.html, F1-error.html, F1-not-found.html
- 스켈레톤: src/shortlink/{validation,codes,db,repository,dependencies,api,web}.py (스텁의 이름, 시그니처, docstring 규칙 유지). main.py의 create_app 연결은 이미 되어 있다.

할 일:
1. 스텁의 NotImplementedError를 모두 구현한다. api.create_link, web 라우트들의 파라미터는 자유롭게 정하되 동작은 docstring과 계획을 따른다.
   - POST /links: url이 없거나 문자열이 아니면(숫자, null, 배열) 422. 검증 실패는 {"detail": "<validation 문구>"}로 422. pydantic 기본 동작에 기대지 말고 int→str 변환 같은 coercion이 생기지 않게 한다(StrictStr 등).
   - GET /{code}: Starlette RedirectResponse 대신 Response(302, Location=location_header_value(url))를 쓴다. ASCII는 그대로, 비ASCII만 UTF-8 퍼센트 인코딩.
   - sqlite3 연결은 호출마다 열고 반드시 닫는다. 모든 SQL은 파라미터 바인딩.
2. 템플릿 src/shortlink/templates/{base,home,result,not_found}.html: 목업의 마크업 구조, 클래스, 문구, title을 그대로 따른다. 오류 화면은 home.html에 error와 입력값을 넘겨 렌더링(422). 자동 이스케이프 유지, |safe/Markup 금지.
3. src/shortlink/static/style.css: 목업의 "공통 스타일" 블록을 그대로 옮긴다. src/shortlink/static/copy.js: 목업 결과 화면의 인라인 스크립트를 파일로 옮기고 result.html에서 <script src="/static/copy.js" defer>로 불러온다. 템플릿에서 /static 경로는 하드코딩해도 된다.
4. tests/는 건드리지 않는다(test-writer가 동시에 작성 중). 스스로 확인하려면 임시 스크립트나 TestClient를 직접 돌려 보되 저장소에 파일을 남기지 않는다.
5. 끝나기 전에 uv run ruff check src, uv run ruff format src.

보고는 네 정의의 보고 형식으로.
