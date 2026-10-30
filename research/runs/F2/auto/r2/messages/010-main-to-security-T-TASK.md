---
seq: 10
sender: "main"
receiver: "security"
type: "T-TASK"
timestamp: "2026-10-29T08:19:41.720Z"
agent: "security"
agent_id: "a3119cc4291fd310b"
turn: 1
reply_to: null
chars: 552
tokens_est: 291
wait_s: null
---

F2(클릭 통계와 커스텀 별칭) 보안 점검 1라운드다. 점검 체크포인트는 커밋 `b42b3bb`, F2 이전 기준은 `663d5ad`(`git diff 663d5ad b42b3bb`가 F2 변경 전체).

참고: 설계서 `docs/features/F2.md`, 계획 `docs/plans/F2-plan.md`, F1 보안 결정(CSP, nosniff 등)은 `docs/plans/F1-plan.md` 5절 D-9~D-11.

중점: 별칭 입력 검증 우회(유니코드, 개행, 예약어/경로 충돌, 대소문자), SQL 바인딩, 스키마 이전(`db.init_schema`의 ALTER TABLE에 외부 입력이 섞이지 않는지), 클릭 증가의 원자성, 통계 화면과 오류 화면의 XSS(별칭과 URL 이스케이프, 속성 컨텍스트), 통계 API/화면을 통한 정보 노출, 오류 응답에 내부 정보 노출. 범위 밖(인증, 요청 수 제한 등 F3)은 minor로만 기록.

각 지적에 blocker / major / minor 심각도, 파일:줄, 공격 시나리오, 고칠 방향을 붙여 줘. 파일은 수정하지 않는다.
