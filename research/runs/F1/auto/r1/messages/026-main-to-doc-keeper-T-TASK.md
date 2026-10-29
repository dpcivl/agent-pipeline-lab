---
seq: 26
sender: "main"
receiver: "doc-keeper"
type: "T-TASK"
timestamp: "2026-10-29T04:55:16.928Z"
agent: "doc-keeper"
agent_id: "ad11b461f0a743be3"
turn: 1
reply_to: null
chars: 994
tokens_est: 456
wait_s: null
---

F1(단축 URL 생성과 리다이렉트) 구현이 끝났다. 서비스 문서와 CHANGELOG를 갱신하고 기능 커밋 하나를 만들어 줘.

기준 자료:
- 설계서: docs/features/F1.md
- 실제 코드: src/shortlink/ (api.py, web.py, validation.py, links.py, db.py, main.py, config.py, templates/, static/)
- 결정 기록: docs/plans/F1-decisions.md. 오류 문구, Location 인코딩, 서로게이트 거절 등이 여기 있다.
- 실행 보고서: docs/plans/F1-report.md. 작성은 끝났고, 커밋에 포함해야 한다.

할 일:
1. docs/service.md를 새로 쓴다. 담을 내용:
   - 화면 4개와 사용 흐름: 홈 /, 결과 POST /, 입력 오류 422, 찾을 수 없음 404
   - API: POST /links 요청·응답 예시와 422 오류 문구 목록, GET /{code}의 302/404
   - 검증 규칙
   - 환경 변수 SHORTLINK_DB_PATH, SHORTLINK_BASE_URL과 기본값
   - 서버 실행 명령
2. CHANGELOG.md를 새로 쓰고 F1 항목을 추가한다.
3. `git add -A --sparse`로 남은 변경을 모두 담는다. 커밋 전에 git status와 `git diff --cached --stat`으로 확인한다.
4. 기능 커밋을 만든다.
   - 첫 줄: `F1: 단축 URL 생성과 리다이렉트 (API와 웹 화면)`
   - 본문: 변경 요점 목록
   - 이 기능의 체크포인트 커밋은 3개다: a01a065, 62a0bf3, 5c61fc4
   - 메시지 끝에 다음 줄을 넣는다:
     Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

git push, 브랜치 변경, 이력 수정은 하지 않는다. 보고는 네 보고 형식으로 해 줘.
