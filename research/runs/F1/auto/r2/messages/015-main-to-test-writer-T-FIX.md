---
seq: 15
sender: "main"
receiver: "test-writer"
type: "T-FIX"
timestamp: "2026-10-29T05:18:15.617Z"
agent: "test-writer"
agent_id: "ac6963e1736f78e26"
turn: 2
reply_to: null
chars: 674
tokens_est: 306
wait_s: null
---

리뷰 1라운드 결과로 새 결정 D-10이 생겼다. 회귀 테스트를 tests/test_api.py에 추가해 줘(implementer가 동시에 src를 고치는 중이다).

D-10(docs/plans/F1-decisions.md, 계획서 3장 표 4-1 행): URL에 서로게이트 문자(U+D800~U+DFFF)가 있으면 422, 본문 {"detail": "URL에 쓸 수 없는 문자가 있습니다."}, 저장 행 수 0.

추가할 테스트:
1. JSON 이스케이프: content=b'{"url": "https://example.com/\\ud800"}' (headers content-type application/json) → 422, detail 문구, count_links()==0
2. 원시 바이트: 본문에 UTF-8 인코딩된 서로게이트 바이트 b'\xed\xa0\x80'을 그대로 넣은 경우 → 422, 행 수 0
3. 호스트 부분의 서로게이트(예: "http://\ud800.com/")도 422
(가능하면 parametrize로 묶어도 된다.) 폼 경로는 서로게이트가 U+FFFD로 바뀌어 재현되지 않으니 테스트하지 않아도 된다.

ruff check/format tests 후 보고 형식으로 보고해 줘.

Address this before completing your current task.
