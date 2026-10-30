---
seq: 11
sender: "main"
receiver: "security"
type: "T-TASK"
timestamp: "2026-10-29T23:57:40.145Z"
agent: "security"
agent_id: "ab096ebd4ae25c7d8"
turn: 1
reply_to: null
chars: 518
tokens_est: 283
wait_s: null
---

F2(클릭 통계와 커스텀 별칭) 보안 점검 1라운드입니다. 리뷰 체크포인트는 커밋 e9f25fe이고, F2 변경 전체는 `git diff 79faa29..e9f25fe`입니다(79faa29 = F1 완료 스냅샷, F1 보안 결정은 docs/plans/F1-plan.md D-9, D-10).

- 설계서: docs/features/F2.md, 계획: docs/plans/F2-plan.md (해석 결정 D-F2-1~9는 사람 승인 완료)
- 새 공격면: 사용자가 정하는 별칭(경로 충돌, 예약어 우회, 유니코드), 통계 API/화면(이스케이프, 정보 노출), 클릭 카운트(SQL, 원자성), F1 DB 마이그레이션, 템플릿의 새 출력 지점.
- 범위 밖(설계서): 인증, 요청 수 제한 — 이것 자체는 F3 범위이니 지적하더라도 minor로만.

지적마다 blocker / major / minor 심각도, 위치(파일:줄), 공격 시나리오, 고칠 방향을 S-1, S-2처럼 번호를 붙여 보고해 주세요. 파일은 수정하지 마세요.
