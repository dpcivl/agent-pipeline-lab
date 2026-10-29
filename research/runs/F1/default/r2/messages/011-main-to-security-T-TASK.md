---
seq: 11
sender: "main"
receiver: "security"
type: "T-TASK"
timestamp: "2026-10-29T02:21:21.709Z"
agent: "security"
agent_id: "a0411bab91b1e0f90"
turn: 1
reply_to: null
chars: 693
tokens_est: 363
wait_s: null
---

F1(단축 URL 생성과 리다이렉트) 보안 점검 1라운드입니다. 리뷰 체크포인트는 `62afa74`입니다.

- 범위: `src/shortlink/**`(템플릿, static/copy.js 포함). 이번 기능 전체 변경은 `git diff 7c88212..62afa74 -- src`로 볼 수 있습니다.
- 기준: 설계서 `docs/features/F1.md`, 계획 `docs/plans/F1-plan.md`(특히 3절 검증 규칙, 7절 해석 결정 D-3 공백·제어 문자 거절, D-7 비ASCII URL의 Location 퍼센트 인코딩)
- 에이전트 정의의 점검 항목을 따르되, F1 범위에 없는 것(인증, 별칭, rate limit — F3 범위)은 "범위 밖" 참고로만 적고 심각도를 매기지 말아 주세요. 단, 설계서 범위 안에서 실제 악용 가능한 문제는 빠짐없이 보고합니다.
- 특히 볼 것: `javascript:`/`data:` 등 위험 스킴이 결과 화면의 `href`나 `Location`으로 나갈 경로, 템플릿 이스케이프(속성 값 안의 `value`, `data-copy`, `href`), `Location` 헤더 주입(CRLF), SQL 파라미터 바인딩, 422/500 응답에 내부 정보 노출, `uv run bandit -r src -q` 결과.
- 파일은 수정하지 않습니다. 보고는 에이전트 정의의 형식을 따릅니다.
