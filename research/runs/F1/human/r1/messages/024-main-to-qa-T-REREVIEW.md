---
seq: 24
sender: "main"
receiver: "qa"
type: "T-REREVIEW"
timestamp: "2026-10-29T06:13:37.978Z"
agent: "qa"
agent_id: "aa7468d7770b0ba5c"
turn: 2
reply_to: null
chars: 652
tokens_est: 312
wait_s: null
---

QA 2라운드다. 직전 리뷰 체크포인트는 9f6fab9, 현재 f1200fd(HEAD). `git diff 9f6fab9..HEAD --stat`의 변경과 관련된 동작만 다시 확인해 줘.

- Q-1(서로게이트 500): 이제 422 `{"detail": "URL에 올바르지 않은 문자가 있습니다."}`이고 저장되지 않아야 함. 짝이 맞는 `😀`은 201.
- Q-2: 사람이 기록만 하기로 결정(수정 안 함). 확인 불필요.
- 새로 추가된 보안 헤더(D-10): 홈/결과/입력오류/404 HTML에 CSP `default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`, 모든 응답에 `X-Content-Type-Options: nosniff`, /docs와 /redoc은 CSP 없이 200. CSP 아래에서도 화면이 깨지지 않는지(스타일시트와 copy.js가 'self'에서 로드되는지, 인라인 스크립트/스타일 없음) 확인.
- 기존 AC가 회귀하지 않았는지 간단히(AC-1, 10, 17, 19, 21 정도).
서버는 반드시 종료하고 포트 확인. 같은 보고 형식, 같은 id 체계로.

Address this before completing your current task.
