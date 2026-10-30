---
seq: 11
sender: "main"
receiver: "security"
type: "T-TASK"
timestamp: "2026-10-30T00:45:29.992Z"
agent: "security"
agent_id: "a6b1de572f634da49"
turn: 1
reply_to: null
chars: 585
tokens_est: 310
wait_s: null
---

F2(클릭 통계와 커스텀 별칭) 보안 점검 1라운드다. 리뷰 체크포인트: 16fdb28. F1 완료 상태는 0b748cc이고, 변경분은 `git diff 0b748cc 16fdb28 -- src`다(필요하면 src 전체도 봐).

참고: docs/features/F2.md, docs/plans/F2-plan.md(D2-1~D2-9), F1 보안 결정은 docs/plans/F1-plan.md 5절(D-2, D-4, D-9, D-10: CSP, nosniff 등). 범위 밖: 인증, 요청 수 제한, 관리 화면(F3).

중점: 별칭을 통한 경로/라우트 충돌·우회(예약어, 대소문자, 유니코드), SQL 인젝션과 파라미터 바인딩, XSS(통계 화면, 오류 화면의 별칭 값, 결과 화면 href의 code), 오픈 리다이렉트 관련 F1 동작 유지, 클릭 수 갱신의 경쟁 조건, 마이그레이션 중 오류 처리, 정보 노출(오류 본문, 통계 API로 남의 링크 조회 — 설계상 허용인지 판단).
지적마다 심각도(blocker/major/minor), 파일:줄, 공격 시나리오, 고칠 방향, ID(S-1, S-2...)를 적어 줘. 파일은 수정하지 않는다.
