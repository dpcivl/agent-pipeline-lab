---
seq: 18
sender: "main"
receiver: "test-writer"
type: "T-FIX"
timestamp: "2026-10-29T06:11:12.508Z"
agent: "test-writer"
agent_id: "ad099a69ee132ab3c"
turn: 2
reply_to: null
chars: 1350
tokens_est: 544
wait_s: null
---

리뷰 1라운드 결과다. 사람이 우선순위를 정했고 테스트 쪽은 아래 3건이다. docs/plans/F1-plan.md 3.1 표(규칙 7개로 변경)와 5절 D-9~D-11을 갱신해 두었으니 먼저 읽어라. implementer가 src/를 동시에 고치고 있으니 src/는 건드리지 마라(지금 실행하면 새 테스트가 실패할 수 있는데 정상).

1. M-1 / D-9: 짝 없는 서로게이트 URL 거절
   - 새 상수 `shortlink.validation.MSG_INVALID_ENCODING = "URL에 올바르지 않은 문자가 있습니다."`, 규칙 순서는 4 공백/제어문자 → 5 UTF-8 인코딩 불가 → 6 스킴 → 7 호스트.
   - test_validation.py: "https://e.com/\ud800", "https://e.com/\udc80" 등이 MSG_INVALID_ENCODING. 순서 확인(예: 공백과 서로게이트가 같이 있으면 MSG_INVALID_CHAR, "ftp://e.com/\ud800"은 MSG_INVALID_ENCODING).
   - test_api_links.py: `content='{"url": "https://e.com/\\ud800"}'`, `headers={"Content-Type": "application/json"}`로 원문 JSON을 보내 422, 본문 {"detail": MSG_INVALID_ENCODING}, count_links()==0.
2. R-3: tests/test_repository.py:97의 `1 < len(calls) <= MAX_ATTEMPTS + 1`을 `len(calls) == LinkRepository.MAX_ATTEMPTS`로 고정.
3. S-3 / D-10: 보안 헤더
   - 홈, 결과, 입력 오류(422), 404 HTML 응답에 `Content-Security-Policy` 헤더가 있고 `default-src 'self'`와 `frame-ancestors 'none'`을 포함.
   - `X-Content-Type-Options: nosniff`가 HTML 화면, POST /links JSON 응답, 302 리다이렉트에 있음.
   - GET /docs는 200이고 CSP 헤더가 없음(Swagger UI가 CDN을 쓰므로).
   (R-2 copy.js는 JS라 pytest 대상이 아님. 원하면 /static/copy.js 응답 본문에 "navigator.clipboard" 가드 문자열이 있는지 정도만 확인해도 되지만 필수는 아니다.)

끝나면 ruff check/format tests. 같은 보고 형식으로.

Address this before completing your current task.
