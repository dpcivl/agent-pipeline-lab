---
seq: 14
sender: "main"
receiver: "implementer"
type: "T-FIX"
timestamp: "2026-10-29T04:49:12.276Z"
agent: "implementer"
agent_id: "abf585d38424abbbe"
turn: 2
reply_to: null
chars: 1480
tokens_est: 660
wait_s: null
---

리뷰 1라운드에서 고칠 major 2건이다. 고칠 범위는 src/ 안이다(tests/는 test-writer가 따로 맡는다). 리뷰 체크포인트는 62a0bf3이고, 갱신된 결정은 docs/plans/F1-decisions.md의 D-3(개정)과 D-8, 계획은 docs/plans/F1-plan.md의 3.2 표(4a/4b)와 3.5에 있다.

1) R-1 [major] 리다이렉트 Location이 일부 ASCII 문자를 퍼센트 인코딩함 (src/shortlink/web.py follow)
- 원인: Starlette RedirectResponse는 quote(url, safe=":/%#?=@[]!$&'()*+,;")를 쓴다. 그래서 `" < > \ ^ \` { | }` 같은 ASCII 문자까지 인코딩한다. 예를 들어 `https://example.com/?a=1|2`는 Location이 `...a=1%7C2`로 나간다. 이는 AC-10("Location 헤더에 원래 URL")과 개정된 D-3에 어긋난다.
- 고칠 방향(D-3 개정): 출력 가능한 ASCII(0x21–0x7E)는 모두 글자 그대로 둔다. 비ASCII 문자만 UTF-8 퍼센트 인코딩하고, 이미 있는 %xx는 건드리지 않는다.
  - 예: `quote(url, safe="".join(chr(c) for c in range(0x21, 0x7F)))`로 만든 값을 `Response(status_code=302, headers={"location": ...})`로 돌려준다. RedirectResponse 서브클래스를 써도 된다.
  - 공백과 제어 문자는 검증에서 이미 막힌다.
  - 이 함수는 작은 헬퍼(예: links.py나 web.py의 `location_header(url) -> str`)로 분리하면 좋다.

2) S-1 [major로 올림] 짝 없는 서로게이트가 든 URL이 500 오류를 냄 (src/shortlink/validation.py)
- 재현: POST /links에 `{"url":"https://a.com/\ud800"}`을 보내면 검증을 통과한 뒤 sqlite3 바인딩에서 UnicodeEncodeError가 나고 500이 된다.
- 고칠 방향(D-8): 4a 단계를 길이 검사 다음, 공백·제어 문자 검사(4b) 전에 넣는다. U+D800–U+DFFF 문자가 하나라도 있으면 InvalidURLError("URL에 쓸 수 없는 문자가 들어 있습니다.")를 던진다.

minor(R-2~R-5, S-2~S-6)는 이번에 고치지 않는다. 끝나면 `uv run ruff check src`, `uv run ruff format src`를 실행한다. 직접 스모크 확인도 한다: `|{}<>\^` 문자가 든 URL과 한글 URL의 Location, 그리고 \ud800 입력이 422가 되는지. git 커밋은 하지 않는다. 보고는 네 보고 형식으로 써라.

Address this before completing your current task.
