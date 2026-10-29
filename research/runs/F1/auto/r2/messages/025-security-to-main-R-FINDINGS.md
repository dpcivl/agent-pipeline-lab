---
seq: 25
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T05:20:02.979Z"
agent: "security"
agent_id: "a66ac9b4e9288e49c"
turn: 2
reply_to: 22
chars: 1626
tokens_est: 822
wait_s: null
---

## 결과: 지적 0건 (blocker 0, major 0, minor 0)

S-1은 해결됐습니다. 이번 변경분(`git diff 166f2b6..36183ce`)에서 새 취약점이나 우회는 찾지 못했습니다. 이 라운드는 S-1 확인과 이번 diff만 봤습니다. S-2~S-5는 지시대로 아래에 "미반영(minor)"로만 적었습니다. 따로 실행한 결과로는 `uv run python -m bandit -r src -q`가 출력 없이 exit 0이었고, `uv run pytest`는 96개가 모두 통과했습니다. bandit을 python 모듈로 실행한 이유는 1라운드와 같습니다. bandit 실행 파일을 애플리케이션 제어 정책이 차단합니다. 저장소 파일은 수정하지 않았습니다.

## 지적 목록
- 없음

## 이전 지적 확인
- S-1: 해결
  - 수정 위치: C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/validation.py:40-42. D-2 공백·제어 문자 검사 다음, `urlsplit`과 스킴 검사 전에 서로게이트(U+D800~U+DFFF) 검사가 들어갔습니다.
  - 확인한 입력: HEAD 36183ce에서 API로 보냈습니다.
    - 경로의 짝 없는 high(`\ud800`), 경로의 짝 없는 low(`\udfff`), 순서가 뒤집힌 쌍(`\ude00\ud83d`), 끝에 붙은 high(`\udbff`), 호스트 안의 서로게이트, 스킴 앞의 서로게이트: 모두 422 "URL에 쓸 수 없는 문자가 있습니다."
    - 서로게이트와 `\u0000`을 함께 넣은 경우: 앞선 D-2 검사에서 422
  - 저장된 행: 거절된 요청은 하나도 저장되지 않았습니다(count는 정상 요청 1건뿐).
  - 회귀 없음: 정상적인 서로게이트 쌍 `\ud83d\ude00`은 `json.loads`가 U+1F600 한 글자로 합치므로 201이 나고, 리다이렉트도 `Location: http://a.com/%F0%9F%98%80`으로 정상입니다.
  - 웹 폼: `%ED%A0%80`은 Starlette가 U+FFFD로 바꿔 디코딩하므로 처음부터 서로게이트가 들어오지 않습니다(200). 500은 없습니다.
  - 우회 가능성: 파이썬 `str`가 UTF-8로 인코딩하지 못하는 경우는 서로게이트 코드 포인트뿐이므로, 이 검사로 S-1 경로는 모두 막힙니다. `web.py`의 `quote()`와 JSONResponse 인코딩도 같은 원인이라 함께 막혔습니다.
- S-2: 미반영(minor). 깊게 중첩된 JSON이 RecursionError로 500을 내는 문제로, C:<HOME>/Documents/dev/agent-pipeline-lab-runs/F1-auto-r2/src/shortlink/api.py:23-26은 바뀌지 않았습니다.
- S-3: 미반영(minor). D-10의 "범위"에 기록만 됐습니다. C1 제어 문자와 양방향 제어 같은 Cc/Cf 범주는 여전히 허용됩니다.
- S-4: 미반영(minor). rate limit과 본문 크기 제한은 F3 범위입니다.
- S-5: 미반영(minor). 보안 응답 헤더(CSP, nosniff, frame-ancestors)가 아직 없습니다.
