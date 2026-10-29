---
seq: 11
sender: "main"
receiver: "security"
type: "T-TASK"
timestamp: "2026-10-29T06:38:02.725Z"
agent: "security"
agent_id: "aab67cfb2c1bcd0a3"
turn: 1
reply_to: null
chars: 590
tokens_est: 310
wait_s: null
---

F1(단축 URL 생성과 리다이렉트) 보안 점검 1라운드입니다. 리뷰 체크포인트: 92f903f (현재 HEAD). 기능 전체 변경은 `git diff 8b7193b..92f903f`.

- 설계서: docs/features/F1.md, 구현 계획(사람 승인 완료, 해석 결정 D-1~D-9): docs/plans/F1-plan.md
- 대상: src/shortlink/** (템플릿, static 포함)
- 이 기능 범위: 인증·요청 수 제한·만료는 F3 범위(설계서 "범위 밖")이므로, 그 부재 자체는 이번 기능의 blocker/major로 보지 말고 필요하면 minor로 기록만 해 주세요.
- 특히 볼 것: URL 검증 우회(스킴 대소문자, 공백·제어 문자, 유니코드, urlsplit 파싱 차이), Location 헤더 주입, XSS(결과 화면 href/텍스트, 오류 화면 input value, data-copy 속성), SQL 바인딩, 에러 응답 정보 노출, 코드 생성의 예측 불가능성, bandit(`uv run bandit -r src -q`).

파일은 수정하지 말고, 에이전트 정의의 보고 형식(S-번호, 심각도)으로 보고해 주세요.
