---
seq: 13
sender: "qa"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T05:17:43.279Z"
agent: "qa"
agent_id: "a11b9ec634215fd51"
turn: 1
reply_to: 9
chars: 5104
tokens_est: 2073
wait_s: null
---

## 결과: 지적 3건 (blocker 0, major 1, minor 2)

서버는 정상 기동했고(임시 DB, 포트 8765), AC-1~AC-23이 모두 통과했습니다. 종료 확인: 8765 포트에 LISTEN 소켓이 없고 TIME_WAIT 항목만 남았습니다. 저장소 파일은 수정하지 않았습니다.

## 수용 기준 검증
| 수용 기준 | 요청 | 기대 | 실제 | 판정 |
|---|---|---|---|---|
| AC-1 | POST /links {"url":"https://example.com/path?q=1"} | 201, code/short_url/url/created_at | 201, 4개 필드 모두 있음 | 통과 |
| AC-2 | 위 응답과 추가 응답 확인 | 7자 영숫자, short_url=base_url/code | `DQqlMrx`, `http://127.0.0.1:8765/DQqlMrx` | 통과 |
| AC-3 | 위 응답의 url | 요청 URL과 동일 | 동일. `HTTPS://Example.com/A`, `a%20b#frag`, 비ASCII, `<>"` 모두 글자 그대로 | 통과 |
| AC-4 | http://example.com | 201 | 201 | 통과 |
| AC-5 | ftp:, javascript:, data:, mailto: | 422 | 모두 422 ("http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다.") | 통과 |
| AC-6 | {}, {"url":123}, {"url":""}, null | 422 | 422 (문구 "URL을 입력해 주세요." / "URL은 문자열이어야 합니다.") | 통과 |
| AC-7 | https:// | 422 | 422 ("URL에 호스트(도메인)가 없습니다.") | 통과 |
| AC-8 | 2048자 / 2049자 | 201 / 422 | 201 / 422 ("URL은 2,048자를 넘을 수 없습니다.") | 통과 |
| AC-9 | 거절 요청 후 DB 확인 (API ftp, API 숫자, 폼 javascript:) | 행 수 불변 | links 행 수 117 -> 117 | 통과 |
| AC-10 | GET /{code} | 302, Location=원래 URL | 302, `location: https://dup.example/` | 통과 |
| AC-11 | GET /nope123 | 404 | 404 | 통과 |
| AC-12 | 같은 URL 2회 | 다른 코드, 둘 다 리다이렉트 | `mavwieF`, `zevSTtq`, 둘 다 302 -> https://dup.example/ | 통과 |
| AC-13 | 100회 연속 생성 | 모두 다른 코드 | 고유 코드 100개 | 통과 |
| AC-14 | 같은 DB로 서버 재시작 후 이전 코드 GET | 302 | 재시작 후 3개 코드(`mavwieF`, `bpZGxnB`, `0GHZTPZ`) 모두 302와 올바른 Location | 통과 |
| AC-15 | created_at | UTC ISO 8601, 1분 이내 | `2026-10-29T05:14:34Z` (서버 date 헤더와 동일) | 통과 |
| AC-16 | GET / | 200 text/html, form post "/", label+name=url, "줄이기" | 모두 충족 | 통과 |
| AC-17 | 폼 POST https://example.com/a?x=1&y=2 | 200, href=단축 URL, 원래 URL 표시 | 200, `<a class="short-url" href="http://127.0.0.1:8765/0GHZTPZ">`, 원래 URL 표시 (`&amp;`로 이스케이프) | 통과 |
| AC-18 | 결과 화면 | "복사" 버튼, `/`로 가는 "다른 URL 줄이기" | `button.copy-button data-copy=...` "복사", `<a href="/">다른 URL 줄이기</a>`, `/static/copy.js` 로드 | 통과 |
| AC-19 | 폼 POST ftp://..., 빈 값, https://, 앞 공백 URL | 422 HTML, 오류 문구, 값 유지, 미저장 | 422, `<p class="error" role="alert">`, `value="ftp://files.example.com/report.pdf"` 유지, 행 수 불변 | 통과 |
| AC-20 | `<script>alert(1)</script>` 등 | 이스케이프 | 오류 화면 `value="&lt;script&gt;..."`, 결과 화면 `&lt;script&gt;`. 서버가 넣은 `<script src="/static/copy.js">` 외에 원문 태그 없음 | 통과 |
| AC-21 | GET /nope123 | 404 HTML, 안내 문구, 홈 링크 | 404 text/html, "링크를 찾을 수 없습니다", `<a href="/">홈으로 가기</a>` | 통과 |
| AC-22 | 4개 화면 | html lang="ko", viewport | 4개 화면 모두 있음 | 통과 |
| AC-23 | 폼으로 만든 코드 `0GHZTPZ` | 302 | 302 -> https://example.com/a?x=1&y=2 (재시작 후에도 동일) | 통과 |
| D-1 | HTTPS://Example.com/A | 허용, 그대로 저장 | 201, Location도 동일 | 통과 |
| D-2 | 공백, 탭 계열, \r\n, NUL, DEL, U+00A0, U+0085, U+2028, 앞 공백 | 422 | 모두 422 ("URL에 공백이나 제어 문자를 넣을 수 없습니다.") | 통과 |
| D-3 | `https://예시.com/경로?q=한글`, `https://a.com/😀<>"` | 응답은 원문, Location은 비ASCII만 인코딩 | 응답 원문 그대로. Location `https://%EC%98%88%EC%8B%9C.com/%EA%B2%BD%EB%A1%9C?q=%ED%95%9C%EA%B8%80`, `https://a.com/%F0%9F%98%80<>"` 이고 ASCII 문자는 그대로 | 통과 |
| D-4/D-9 | 깨진 JSON, 배열 본문, form-urlencoded로 /links | 422 + detail | 422 + 한국어 detail | 통과 |
| D-5 | /nope123, /abcdefg, /favicon.ico, Accept: application/json | 항상 404 HTML | 404 text/html | 통과 (아래 Q-2 예외 있음) |
| D-8 | http://[abc | 422 호스트 문구 | 422 "URL에 호스트(도메인)가 없습니다." | 통과 |
| 정적 파일 | /static/style.css, /static/copy.js | 200 | 200, text/css / text/javascript | 통과 |
| 목업 비교 | 홈, 결과, 오류, 404 | 문구, 구조, 링크 일치 | 제목, 설명, 라벨, 플레이스홀더, 오류 `p.error#url-error role=alert`, `aria-invalid`, `aria-describedby`, 404 문구까지 일치. 목업 전용 note는 제외되어 있고 style은 `/static/style.css`로 분리됨 | 통과 |

## 지적 목록
### Q-1 [major] 짝 없는 서로게이트 문자가 든 URL에서 500
- 재현: `POST /links`, 본문 `{"url":"https://a.com/\ud800"}` (유효한 JSON 이스케이프)
- 기대: 422 거절 (D-4, 설계서 검증 규칙). 서버 오류가 나면 안 됩니다.
- 실제: `500 Internal Server Error` (본문 "Internal Server Error"). 서버 로그에 `storage.py create`에서 `UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800'`가 남았습니다. 행은 저장되지 않았습니다(행 수 117 유지). 같은 문자를 폼으로 보내는 경우는 확인하지 못했습니다(폼 입력은 UTF-8로 디코딩되어 서로게이트가 들어오기 어려움).
- 수정 제안: 검증 단계에서 `url.encode("utf-8")` 실패(UnicodeEncodeError)나 서로게이트 범위(U+D800~U+DFFF) 문자를 거절합니다. 문구는 D-2의 "공백이나 제어 문자" 또는 새 문구를 쓰면 되고, 결정 기록에 추가하길 권합니다.

### Q-2 [minor] 슬래시가 든 경로의 404가 JSON으로 나옴
- 재현: `curl -i http://127.0.0.1:8765/a/b`
- 기대: D-5 "코드 형식이 아닌 경로도 같은 404 화면" (404 HTML)
- 실제: `404 Not Found`, `content-type: application/json` (FastAPI 기본 `{"detail":"Not Found"}`). `/nope123`, `/favicon.ico`는 HTML 404입니다.
- 수정 제안: 전역 404 예외 핸들러로 모든 미일치 경로에 HTML 404를 돌려줍니다.

### Q-3 [minor] 끝에 슬래시가 붙은 경로가 307로 리다이렉트됨
- 재현: `curl -i http://127.0.0.1:8765/nope/`, `curl -i http://127.0.0.1:8765/bpZGxnB/`
- 기대: 없는 코드는 404 HTML (D-5). 존재하는 코드의 `/code/`는 설계서에 규정이 없습니다.
- 실제: `307 Temporary Redirect`, `location: http://127.0.0.1:8765/nope`. 없는 코드를 먼저 307로 보낸 뒤 404를 돌려줍니다. 참고로 `HEAD /{code}`는 405입니다. 설계서 범위 밖이라 지적하지 않고 기록만 합니다.
- 수정 제안: `redirect_slashes=False`로 바꿔 `/nope/`가 바로 404 HTML이 되게 합니다. 의도한 동작이면 결정 기록에 남겨 주세요.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)

참고: 서버 로그의 traceback은 Q-1 재현 한 건뿐입니다. 사용한 임시 DB는 `/tmp/tmp.6uqi5Upe1M/qa.db`(Git Bash 경로)입니다.
