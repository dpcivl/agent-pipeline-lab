---
seq: 9
sender: "main"
receiver: "reviewer"
type: "T-TASK"
timestamp: "2026-10-29T02:21:21.685Z"
agent: "reviewer"
agent_id: "a00ed3da5d1f40b84"
turn: 1
reply_to: null
chars: 783
tokens_est: 395
wait_s: null
---

F1(단축 URL 생성과 리다이렉트) 리뷰 1라운드입니다. 리뷰 체크포인트는 `62afa74`이고, 테스트 224개가 모두 통과한 상태입니다.

- 기준: 설계서 `docs/features/F1.md`(AC-1~AC-23), 구현 계획 `docs/plans/F1-plan.md`(인터페이스, 화면 규칙, 해석 결정 D-1~D-9), 목업 `docs/plans/mockups/F1-*.html`
- 범위: `src/shortlink/**`(템플릿, static 포함)와 `tests/**`. 이번 기능 전체 변경은 `git diff 7c88212..62afa74 -- src tests`로 볼 수 있습니다(`7c88212`는 기능 시작 전 커밋).
- 볼 것: 정확성, 설계서와 계획 충실도, 고정 계약(`create_app`, `Settings`, conftest 픽스처) 준수, 템플릿이 목업의 구조·문구를 따르는지, 테스트가 수용 기준을 실제로 검증하는지(빠지거나 약한 단언), 유지보수성.
- 참고로 implementer가 계획에 없이 정한 판단: 입력 오류 시 `aria-describedby="url-error url-hint"`(목업 기준), `web.py`에 `TEMPLATES_DIR` 별도 정의(순환 import 회피), D-3의 공백·제어 문자를 `str.isspace()`와 C0/C1 제어 문자로 넓게 해석, `urlsplit`의 `ValueError`를 422로 처리. 이 판단들이 적절한지도 봐 주세요.
- 파일은 수정하지 않습니다. 보고는 에이전트 정의의 형식을 따릅니다.
