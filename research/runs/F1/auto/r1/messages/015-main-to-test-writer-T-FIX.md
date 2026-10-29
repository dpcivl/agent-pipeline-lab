---
seq: 15
sender: "main"
receiver: "test-writer"
type: "T-FIX"
timestamp: "2026-10-29T04:49:14.867Z"
agent: "test-writer"
agent_id: "a3c9dd2bf4b0cc4ad"
turn: 2
reply_to: null
chars: 1437
tokens_est: 650
wait_s: null
---

리뷰 1라운드에서 결정이 바뀐 부분에 맞춰 tests/를 보강해 줘. implementer가 지금 동시에 src/를 고치고 있다. 갱신된 결정은 docs/plans/F1-decisions.md의 D-3(개정)과 D-8에 있고, 계획은 docs/plans/F1-plan.md 3.2 표(4a/4b)와 3.5에 있다.

1) R-1 / D-3 개정: 리다이렉트 Location 규칙
- 출력 가능한 ASCII(0x21–0x7E)는 모두 글자 그대로 나가야 한다. `|`, `{`, `}`, `<`, `>`, `\`, `^`, `` ` ``, `"`가 포함된다.
- 비ASCII 문자만 UTF-8 퍼센트 인코딩된다. 이미 있는 %xx는 그대로 둔다.
- 테스트를 추가해 줘:
  - `https://example.com/?a=1|2&b={x}` 같은 URL은 Location이 요청값과 글자 그대로 같다.
  - `https://example.com/<script>alert(1)</script>`도 Location이 글자 그대로다.
  - 한글 경로는 `%ED%95%9C...`로 인코딩된다.
  - `https://example.com/a%20b`처럼 이미 인코딩된 값은 그대로 나간다.
- 기존 테스트가 Location을 퍼센트 인코딩을 풀어서 비교하던 부분(test_ac20_script_url_is_stored_verbatim_and_redirects 등)은 위 규칙에 맞게 정확한 값 비교로 고친다. 사실과 다른 주석(test_web.py 273-274 근처, "characters that cannot go into a header verbatim are percent-encoded")도 고친다.

2) S-1 / D-8: 짝 없는 서로게이트
- 서로게이트(U+D800–U+DFFF)가 든 URL은 422 `{"detail": "URL에 쓸 수 없는 문자가 들어 있습니다."}`이고 아무것도 저장하지 않는다.
- API 테스트는 JSON 원문을 직접 보낸다. 예: `client.post("/links", content='{"url": "https://a.com/\\ud800"}', headers={"content-type": "application/json"})`. 파이썬 문자열의 이스케이프가 JSON 본문의 `\ud800`으로 들어가는지 확인한다.
- validate_url 단위 테스트에 `"https://a.com/\ud800"`를 넣고, 검사 순서도 확인한다. 순서는 길이 > 서로게이트 > 공백·제어 문자다.
- support.py에 문구 상수를 추가한다.

끝나면 `uv run ruff check tests`, `uv run ruff format tests`를 실행한다. src/는 건드리지 않고 커밋도 하지 않는다. 보고는 네 보고 형식으로 써라.

Address this before completing your current task.
