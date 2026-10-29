---
seq: 14
sender: "main"
receiver: "implementer"
type: "T-FIX"
timestamp: "2026-10-29T05:18:12.898Z"
agent: "implementer"
agent_id: "a46510386cb9984ad"
turn: 2
reply_to: null
chars: 805
tokens_est: 393
wait_s: null
---

리뷰 1라운드 major 1건을 고쳐 줘. reviewer R-1, security S-1, qa Q-1이 같은 문제를 지적했다.

문제: POST /links에 {"url": "https://example.com/\ud800"}처럼 짝 없는 서로게이트가 든 URL을 보내면 validate_url을 통과하고, storage.create의 sqlite3 INSERT에서 UnicodeEncodeError가 나서 500이 된다. 본문에 UTF-8 서로게이트 바이트(\xed\xa0\x80)를 그대로 넣어도 json.loads가 surrogatepass로 디코딩해 같은 결과가 나온다.

결정(docs/plans/F1-decisions.md D-10, 계획서 3장 검사 순서 표 4-1 행): URL에 서로게이트 문자(U+D800~U+DFFF)가 하나라도 있으면 URLValidationError로 거절, 문구는 정확히 `URL에 쓸 수 없는 문자가 있습니다.`. 검사 위치는 D-2 공백·제어 문자 검사 바로 다음, 스킴 검사 전. validate_url 안에 두어 API와 폼이 같은 규칙을 쓰게 한다. 다른 Cc/Cf 문자 거절(S-3)이나 그 밖의 minor 지적은 이번에 반영하지 않는다.

tests/는 test-writer가 동시에 회귀 테스트를 추가하니 건드리지 마라. 끝나면 ruff check/format 하고, 직접 TestClient로 두 경우(JSON 이스케이프, 원시 바이트)가 422인지 확인한 뒤 보고 형식으로 보고해 줘.

Address this before completing your current task.
