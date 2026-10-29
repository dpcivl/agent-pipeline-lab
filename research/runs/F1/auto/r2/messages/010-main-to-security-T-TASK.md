---
seq: 10
sender: "main"
receiver: "security"
type: "T-TASK"
timestamp: "2026-10-29T05:14:11.262Z"
agent: "security"
agent_id: "a66ac9b4e9288e49c"
turn: 1
reply_to: null
chars: 599
tokens_est: 296
wait_s: null
---

F1 보안 점검 1라운드를 해 줘. 리뷰 체크포인트 커밋은 166f2b6(HEAD)이고, 기준 스냅샷 e8f75ad 이후 변경 전체가 대상이다(`git diff e8f75ad..166f2b6`).

- 설계서: docs/features/F1.md (F1 범위: 생성, 검증, 리다이렉트, 웹 화면. 인증·요청 수 제한은 F3 범위 밖)
- 해석 결정: docs/plans/F1-decisions.md (D-2 공백·제어 문자 거절, D-3 Location 헤더의 비ASCII 퍼센트 인코딩 등)
- 코드: src/shortlink/ (validation.py, storage.py, api.py, web.py, templates/, static/copy.js)

특히 봐 줄 것: 스킴 검증 우회(대소문자, 앞쪽 공백/제어 문자, 유니코드), Location 헤더 주입, SQL 바인딩, 템플릿 XSS(속성값 포함, data-copy, href), 오류 응답의 내부 정보 노출, 짝 없는 서로게이트 문자 같은 입력으로 인한 500, bandit 결과. 범위 밖(F3)인 rate limit은 minor 제안으로만 적어라.

네 정의의 보고 형식(S-번호)으로 보고해 줘.
