---
seq: 28
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T06:14:54.543Z"
agent: "security"
agent_id: "accb681291420c0b3"
turn: 2
reply_to: 25
chars: 3044
tokens_est: 1440
wait_s: null
---

## 결과: 지적 1건 (blocker 0, major 0, minor 1)

S-1과 S-3은 해결됐다. 남은 1건은 F3에서 다루기로 한 S-2다. 변경분(`git diff 9f6fab9..f1200fd`)에서 새로 생긴 보안 문제는 없고, bandit을 다시 돌린 결과도 0건이다(`uv run bandit -r src -q`, exit 0). 확인은 저장소 밖 임시 DB와 TestClient 점검 스크립트로 했다(아래 경로).

## 지적 목록

### S-2 [minor] 요청 수 제한과 요청 본문 크기 제한 없음 (F3 범위, 기록만)
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\api.py:31`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\web.py:50`
- 취약점: 인증 없이 링크를 무제한으로 만들 수 있고, 요청 본문 전체 크기에 앱 수준 상한이 없다.
- 공격 시나리오: 링크를 대량으로 만들어 SQLite 파일을 키우거나 스팸 URL을 단축한다. 매우 큰 본문을 보내 메모리를 소모시킨다.
- 수정 제안: F3에서 rate limit을 넣고, 리버스 프록시나 미들웨어로 본문 크기를 제한한다. H3 결정대로 F1에서는 기록만 한다.

## 이전 지적 확인
- S-1: 해결
  - `validation.py:56-59`에 `url.encode("utf-8")` 검사(규칙 5, `MSG_INVALID_ENCODING`)가 추가됐다. 순서는 제어 문자 검사 다음, urlsplit 앞이다.
  - JSON `"https://a.test/\ud800"`은 이제 422 `{"detail": "URL에 올바르지 않은 문자가 있습니다."}`를 받고 저장되는 행이 없다.
  - 짝이 맞는 서로게이트 이스케이프(`\ud83d\ude00`, 이모지)는 정상 문자로 디코딩되어 201로 저장된다. 정상 입력이 잘못 막히지 않는다.
  - 서로게이트 값이 저장되지 않으므로 Location 헤더나 템플릿까지 갈 경로도 없다.
- S-2: 미해결 — H3 결정대로 F3 범위라 기록만 유지한다.
- S-3: 해결 (`<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\security.py`, `main.py:35`)
  - **CSP 값**: `default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`. 이 정책에서 막히는 템플릿 요소가 없다. 템플릿에는 인라인 `<script>`와 `style=`이 없고, `copy.js`와 `style.css`는 같은 출처에서 오며, 폼은 `/`로 제출한다. `unsafe-inline`과 `unsafe-eval`이 없고, `object-src`는 `default-src 'self'`로 대체된다.
  - **적용 범위**: 모든 HTML 화면에 CSP와 `nosniff`가 함께 붙는 것을 확인했다.
    - `GET /` 200
    - `POST /` 200과 422
    - 없는 코드의 404, `GET /links` 404
    - `/DOCS` 404
  - 302 리다이렉트, JSON 201/422/405, static css/js와 static 404에는 `nosniff`만 붙는다. HTML이 아니므로 CSP는 붙지 않는다(D-10과 일치).
  - **/docs 예외가 우회 경로가 되지 않는 이유**:
    - 예외는 `app.docs_url`, `app.redoc_url`, `swagger_ui_oauth2_redirect_url`과 경로가 정확히 같을 때만 적용된다. 예외 판단과 라우팅 모두 퍼센트 디코딩이 끝난 경로를 쓰므로 두 판단이 어긋나지 않는다. 예를 들어 `/%64ocs`는 docs 페이지로 라우팅되면서 CSP도 빠진다. 같은 docs 페이지일 뿐이라 우회가 아니다.
    - `/docs/`는 307로 `/docs`에 보내지고, `/DOCS`는 우리 404 화면이라 CSP가 붙는다.
    - docs 라우트가 `/{code}`보다 먼저 등록되므로 우리 템플릿이 예외 경로로 나갈 수 없다.
    - docs와 redoc, oauth2-redirect HTML은 FastAPI가 만드는 고정 내용이다. 사용자 입력이나 쿼리를 반영하지 않고, Swagger `queryConfigEnabled`도 설정되어 있지 않다.
    - 따라서 예외 경로에서 사용자 입력을 주입할 방법이 없다.
  - **예외 응답**:
    - HTTPException, 검증 422, 404, 405처럼 ExceptionMiddleware 안에서 만들어지는 응답에는 헤더가 붙는다.
    - 처리되지 않은 예외로 나는 500(`text/plain`, `Internal Server Error`)에는 `nosniff`가 붙지 않는다. Starlette의 ServerErrorMiddleware가 사용자 미들웨어 바깥에 있기 때문이다.
    - 이 500의 본문은 사용자 입력이 섞이지 않은 고정 문자열이라 MIME 스니핑으로 악용할 여지가 없다. 그래서 지적으로 올리지 않았다. 굳이 막으려면 `app.add_exception_handler(Exception, ...)`로 500 응답을 직접 만들거나 순수 ASGI 미들웨어로 바꾸면 된다.

참고 (지적 아님): F2에서 커스텀 별칭을 넣을 때 `docs`, `redoc`, `openapi.json`, `static`, `links` 같은 예약어는 별칭으로 쓰지 못하게 해야 한다. 등록 순서 때문에 이런 별칭은 리다이렉트되지 않고 가려진다.

점검 스크립트: `<HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F1-human-r1\56be2f53-1a32-42ee-8657-b069f6e12cce\scratchpad\probe2.py`
