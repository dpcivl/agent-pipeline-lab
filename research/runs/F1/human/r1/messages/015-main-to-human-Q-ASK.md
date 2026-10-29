---
seq: 15
sender: "main"
receiver: "human"
type: "Q-ASK"
timestamp: "2026-10-29T05:36:53.052Z"
agent: ""
agent_id: ""
turn: 0
reply_to: null
chars: 1238
tokens_est: 627
wait_s: null
---

{"questions": [{"question": "[H3] 리뷰 1라운드의 major 지적은 1건입니다(M-1). POST /links에 짝 없는 서로게이트 문자(예: \"https://e.com/\\ud800\")가 든 URL을 보내면 422가 아니라 500이 납니다. 저장은 되지 않고 웹 폼에서는 생기지 않습니다. 이 건은 어떻게 처리할까요?", "header": "M-1 처리", "multiSelect": false, "options": [{"label": "새 문구로 422 (추천)", "description": "검증 규칙 4 다음에 UTF-8 인코딩 검사를 넣고 새 문구 \"URL에 올바르지 않은 문자가 있습니다.\"로 거절합니다. 계획서 3.1 표와 목업 문구 표에 D-9로 추가합니다."}, {"label": "기존 문구로 422", "description": "같은 검사를 넣되, 기존 문구 \"URL에 공백이나 제어 문자를 넣을 수 없습니다.\"를 재사용합니다. 문구 표는 바뀝니다 않지만 원인과 문구가 조금 어긋납니다."}, {"label": "고치지 않음", "description": "제외하고 미해결로 기록만 합니다."}]}, {"question": "minor 지적은 규칙상 고치지 않고 기록만 합니다. 이번 라운드에서 같이 고칠 항목이 있으면 골라 주세요. 고르지 않으면 전부 기록만 합니다.", "header": "minor", "multiSelect": true, "options": [{"label": "R-2 복사 실패 안내", "description": "비보안 HTTP처럼 navigator.clipboard가 없는 환경에서 \"복사하지 못했습니다…\" 문구가 나오지 않습니다. copy.js에 가드 한 줄을 추가합니다."}, {"label": "R-3 재시도 테스트 강화", "description": "충돌 재시도 테스트의 단언이 느슨합니다. 시도 횟수 == MAX_ATTEMPTS(10)로 고정합니다."}, {"label": "S-3 보안 응답 헤더", "description": "CSP, X-Content-Type-Options: nosniff, frame-ancestors 'none'을 미들웨어로 붙입니다. 방어를 한 격 더 두는 조치입니다."}, {"label": "Q-2 깨진 호스트 문구", "description": "https://[ 같은 입력에도 \"호스트가 없습니다\" 문구가 나옵니다. 현재도 422이고 동작 문제는 없습니다."}]}]}
