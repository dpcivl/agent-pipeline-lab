---
seq: 26
sender: "qa"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T06:14:05.431Z"
agent: "qa"
agent_id: "aa7468d7770b0ba5c"
turn: 2
reply_to: 24
chars: 1775
tokens_est: 828
wait_s: null
---

## 결과: 지적 0건 (blocker 0, major 0, minor 0)

서버는 임시 DB, 포트 8765로 띄웠다. 검증 후 종료했고 포트가 비어 있는 것을 확인했다. 저장소 파일은 수정하지 않았다.

## 수용 기준 검증 (2라운드: 변경분 관련 + 회귀)
| 수용 기준 | 요청 | 기대 | 실제 | 판정 |
|---|---|---|---|---|
| Q-1 | POST /links `{"url":"https://e.com/\ud800"}` | 422, `{"detail":"URL에 올바르지 않은 문자가 있습니다."}`, 저장 없음 | 422이고 본문이 기대와 같다. 500 없음 | 통과 |
| Q-1 (짝이 맞는 서로게이트) | `{"url":"https://e.com/😀"}` | 201 | 201 | 통과 |
| D-10 CSP | 홈 200, 입력 오류 422, 결과 200(폼 제출), 404 HTML | `default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'` | 네 화면 모두 이 헤더가 정확히 있다 | 통과 |
| D-10 nosniff | API 201, API 422, 302, /static/*, /openapi.json, /docs, /redoc, HTML 4종 | 모든 응답에 `x-content-type-options: nosniff` | 모두 있다 | 통과 |
| D-10 문서 화면 | /docs, /redoc | 200, CSP 없음 | 200이고 CSP 헤더가 없다 | 통과 |
| CSP 아래 화면 동작 | 홈과 결과 화면 HTML 확인 | 인라인 `<script>`, `<style>`, `style=`, `on*=` 핸들러가 없고 외부 리소스는 'self'뿐 | 인라인 요소는 0건이다. `<link href="/static/style.css">`와 `<script src="/static/copy.js" defer>`만 쓰고 둘 다 같은 출처이며 200으로 제공된다. 폼 action은 `/`이다. 한계: 실제 브라우저로 CSP 위반이 없는지는 확인하지 못했다. HTML과 헤더로만 판단했다 | 통과 |
| AC-1 회귀 | POST /links 정상 URL | 201, 네 필드 | 201, 네 필드 | 통과 |
| AC-10 회귀 | GET /{code} | 302 + Location | 302, `location: https://example.com/path?q=1` | 통과 |
| AC-17 회귀 | 폼 제출 성공 | 200, `class="short-url"` 링크와 원래 URL | 정상 | 통과 |
| AC-19 회귀 | 폼으로 `ftp://x` 제출 | 422, 오류 문구, 입력값 유지 | 422, 오류 문구와 `value="ftp://x"` 유지 | 통과 |
| AC-21 회귀 | GET /zzz | 404 HTML | 404 HTML이다. CSP도 있다 | 통과 |

## 지적 목록
없음. 참고: 짝이 맞는 😀 응답의 `url`이 내 터미널에서는 `??`로 보였다. 이전 라운드의 한글 URL은 같은 터미널에서 정상으로 보였다. 터미널이 이모지를 표시하지 못하는 것일 수 있으나, 서버가 이 값을 훼손하는지는 이번에 확인하지 못했다. 필요하면 UTF-8로 파일에 저장해 바이트를 비교해 볼 만하다.

## 이전 지적 확인
- Q-1: 해결. 서로게이트가 422 한국어 문구로 거절되고 500이 없다. 짝이 맞는 서로게이트는 201이다.
- Q-2: 사람이 기록만 하기로 결정했으므로 확인하지 않았다.
