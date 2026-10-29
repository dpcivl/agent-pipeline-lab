---
seq: 11
sender: "main"
receiver: "security"
type: "T-TASK"
timestamp: "2026-10-29T05:32:37.369Z"
agent: "security"
agent_id: "accb681291420c0b3"
turn: 1
reply_to: null
chars: 475
tokens_est: 253
wait_s: null
---

F1 보안 점검 1라운드다. 리뷰 체크포인트 커밋은 9f6fab9 (d1ad59f가 기능 이전 상태).

- 설계서: docs/features/F1.md (인증·요청 수 제한은 F3 범위라 F1에서는 범위 밖. 이 항목은 minor 이하로 기록만)
- 승인된 계획과 해석: docs/plans/F1-plan.md 5절 D-1~D-8
- 검토 대상: src/shortlink/** (템플릿, static/copy.js 포함)
- 특히: XSS(자동 이스케이프, href에 들어가는 short_url, data-copy 속성), Location 헤더 인젝션, 오픈 리다이렉트(URL 단축기 특성상 설계된 동작임을 감안), SQL 바인딩, 에러 응답 정보 노출, bandit 결과.
- implementer가 짝 없는 서로게이트 문자가 든 url이 500을 낸다고 보고했다. 이것의 보안 영향도 판단해 줘.

보고는 네 정의의 보고 형식으로 (S-번호).
