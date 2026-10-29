---
seq: 17
sender: "main"
receiver: "implementer"
type: "T-FIX"
timestamp: "2026-10-29T06:11:09.863Z"
agent: "implementer"
agent_id: "a76b9356aae1c5ad6"
turn: 2
reply_to: null
chars: 1232
tokens_est: 550
wait_s: null
---

리뷰 1라운드 결과다. 사람이 우선순위를 정했고 아래 3건을 고쳐 달라. docs/plans/F1-plan.md 3.1 표와 5절 D-9~D-11을 갱신해 두었으니 먼저 읽어라. test-writer가 tests/를 동시에 고치고 있으니 tests/는 건드리지 마라.

1. M-1 [major] (R-1/S-1/Q-1) 짝 없는 서로게이트가 든 url이 POST /links에서 500
   - validation.py에 `MSG_INVALID_ENCODING = "URL에 올바르지 않은 문자가 있습니다."` 추가.
   - validate_url 규칙 순서: 1 문자열 아님, 2 빈 값, 3 길이, 4 공백/제어문자, **5 UTF-8로 인코딩 불가(url.encode("utf-8")가 UnicodeEncodeError) → MSG_INVALID_ENCODING**, 6 스킴, 7 호스트. docstring도 갱신.
2. R-2 [minor, 사람이 수정 결정] static/copy.js: 클릭 핸들러에서 `navigator.clipboard`(또는 writeText)가 없으면 바로 "복사하지 못했습니다. 링크를 직접 선택해 복사해 주세요."를 #copy-status에 표시하고 return.
3. S-3 [minor, 사람이 수정 결정] 보안 응답 헤더 (D-10)
   - 모든 응답에 `X-Content-Type-Options: nosniff`.
   - 우리 HTML 화면(홈, 결과, 입력 오류, 404)에 `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`.
   - FastAPI의 /docs, /redoc(및 /docs/oauth2-redirect)은 CDN 스크립트와 인라인 스크립트를 쓰므로 CSP를 붙이지 않아 계속 동작해야 한다.
   - 구현 방식은 자유(미들웨어 등). 고정 계약 create_app(settings=None)의 시그니처는 유지, 확장만. 템플릿에 인라인 script/style이 없는지 다시 확인.

끝나면 ruff check/format src, 그리고 `uv run python -m pytest -q`로 기존 테스트가 깨지지 않았는지 확인(pytest.exe는 정책으로 막힐 수 있음). 같은 보고 형식으로.

Address this before completing your current task.
