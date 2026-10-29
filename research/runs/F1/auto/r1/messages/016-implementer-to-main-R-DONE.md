---
seq: 16
sender: "implementer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T04:49:38.225Z"
agent: "implementer"
agent_id: "abf585d38424abbbe"
turn: 2
reply_to: 14
chars: 1423
tokens_est: 612
wait_s: null
---

## 결과: 완료
## 변경 파일
- <HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r1/src/shortlink/web.py: R-1 수정. 작은 헬퍼 `location_header(url)`를 추가했다. 출력 가능한 ASCII(0x21–0x7E)는 그대로 두고 비ASCII만 UTF-8 퍼센트 인코딩한다. 이미 있는 %xx는 건드리지 않는다. `follow`는 `RedirectResponse` 대신 `Response(status_code=302, headers={"location": location_header(link.url)})`를 돌려준다. 안 쓰게 된 `RedirectResponse` import는 제거했다.
- <HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r1/src/shortlink/validation.py: S-1 수정(D-8). 길이 검사 다음, 공백·제어 문자 검사 앞에 4a 단계를 넣었다. U+D800–U+DFFF 문자가 하나라도 있으면 `InvalidURLError("URL에 쓸 수 없는 문자가 들어 있습니다.")`를 던진다. docstring의 검사 순서 설명도 고쳤다.
## 구현한 수용 기준
- AC-10(Location에 원래 URL): web.py의 `location_header`와 `follow`
- AC-5~AC-9 경계 입력(서로게이트는 500이 아니라 422, 저장 없음): validation.py 4a 단계
## 계획에 없던 판단
- 없음. D-3 개정, D-8, 계획 3.2 표(4a/4b), 3.5를 그대로 따랐다.
## 확인한 것
- `uv run ruff format src`와 `uv run ruff check src`를 실행했고 오류는 없었다.
- 임시 DB로 스모크를 돌렸고 끝난 뒤 지웠다. 결과는 아래와 같다.
  - `https://example.com/?a=1|2{x}<y>\^`"`의 Location은 입력과 글자 그대로 같았다. `|`, `{`, `}`, `<`, `>`, `\`, `^`, `` ` ``, `"`가 모두 인코딩되지 않았다.
  - `https://예제.com/경로?q=한글%20x`는 `https://%EC%98%88%EC%A0%9C.com/%EA%B2%BD%EB%A1%9C?q=%ED%95%9C%EA%B8%80%20x`가 됐다. 한글만 인코딩됐고 `%20`은 그대로다.
  - `https://e.com/%7C`는 `%7C` 그대로 나갔다.
  - JSON `\ud800`이 든 URL은 422 `{"detail": "URL에 쓸 수 없는 문자가 들어 있습니다."}`였다.
- cwd에 `shortlink.db`는 생기지 않았다. tests/는 건드리지 않았고 pytest는 실행하지 않았다. 커밋도 하지 않았다.
## 남은 문제와 질문
- 없음
