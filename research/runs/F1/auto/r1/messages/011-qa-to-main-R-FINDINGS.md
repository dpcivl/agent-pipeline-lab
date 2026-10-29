---
seq: 11
sender: "qa"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T04:47:26.092Z"
agent: "qa"
agent_id: "a60810b096cc659b6"
turn: 1
reply_to: 9
chars: 3567
tokens_est: 1539
wait_s: null
---

## 결과: 지적 0건 (blocker 0, major 0, minor 0)

서버는 포트 8765와 임시 DB(저장소 밖 mktemp)로 띄워 확인했고, 끝난 뒤 종료했습니다. 포트 8765 LISTEN 0건, `git status` 변경 없음을 확인했습니다.

## 수용 기준 검증
| 수용 기준 | 요청 | 기대 | 실제 | 판정 |
|---|---|---|---|---|
| AC-1 | POST /links `{"url":"https://example.com/path?q=1"}` | 201 + code, short_url, url, created_at | 201, 4개 필드 모두 있음 | 통과 |
| AC-2 | 위 응답의 code와 short_url | 영숫자 7자, short_url이 `<base_url>/<code>`와 같음 | `6D2d4EX`, `http://127.0.0.1:8765/6D2d4EX` | 통과 |
| AC-3 | `HTTPS://Example.com/A`, 한글 경로 URL | url이 요청과 글자 그대로 같음 | 그대로 반환. 한글은 JSON 파일로 보내 확인함 | 통과 |
| AC-4 | `http://example.com` | 201 | 201 | 통과 |
| AC-5 | ftp://, javascript:, data:, mailto: | 422 | 4건 모두 422, detail은 "http:// 또는 https://로 시작하는 URL만 …" | 통과 |
| AC-6 | url 없음, 123, 0, "" | 422 | 모두 422. 문구는 "URL을 입력해 주세요." 또는 "URL은 문자열이어야 합니다." | 통과 |
| AC-7 | `https://` | 422 | 422 "URL에 호스트(도메인)가 없습니다." | 통과 |
| AC-8 | 2,048자, 2,049자 URL | 2,048자는 201, 2,049자는 422 | 201 / 422 "URL은 2,048자 이하여야 합니다." 웹 폼도 같은 결과 | 통과 |
| AC-9 | 거절 요청 뒤 DB 확인 | 저장 없음 | 읽기 전용으로 DB를 열어 보니 `http`로 시작하지 않는 URL, 빈 URL, 공백 포함 URL, 2,048자 초과 URL 모두 0행 | 통과 |
| AC-10 | GET /{code} | 302 + Location | 302, `location: https://example.com/path?q=1` | 통과 |
| AC-11 | GET /nope123, GET /ab | 404 | 둘 다 404, 404 HTML 화면 | 통과 |
| AC-12 | 같은 URL을 2번 생성 | 서로 다른 코드 | 코드가 다름. 폼으로 만든 코드의 리다이렉트도 확인함 | 통과 |
| AC-13 | 같은 URL로 100번 생성 | 코드 100개 모두 고유 | 100개 모두 고유 | 통과 |
| AC-14 | 서버 종료 뒤 같은 DB 경로로 재시작, 이전 코드로 GET | 302 | 302, `location: https://persist.example/x` | 통과 |
| AC-15 | created_at | UTC ISO 8601, 1분 이내 | `2026-10-29T04:45:53Z`. 서버 date 헤더와 일치 | 통과 |
| AC-16 | GET / | 200 text/html, 폼(POST, /), label이 붙은 name="url" 입력칸, "줄이기" 버튼 | 모두 있음. `<h1>`, 설명 문구, `<label for="url">`도 3.6 기준과 일치 | 통과 |
| AC-17 | 폼으로 올바른 URL 제출 | 200, href가 단축 URL인 링크와 원래 URL | 200, `<a id="short-url" href="http://127.0.0.1:8765/CE6YzT2">`, 원래 URL 표시 | 통과 |
| AC-18 | 결과 화면 | "복사" 버튼, "/"로 가는 "다른 URL 줄이기" 링크 | `data-copy` 버튼 "복사"와 `<a href="/">다른 URL 줄이기</a>` 있음. `/static/copy.js`는 200 text/javascript | 통과 |
| AC-19 | 폼으로 `ftp://…`, 빈 값, 필드 없음, 앞쪽 공백 URL 제출 | 422 HTML, 오류 메시지, 입력값 유지, 저장 없음 | 모두 422. `<p class="alert" role="alert" id="url-error">` 표시, `value="…"`와 `aria-invalid="true"` 있음, 저장 없음 | 통과 |
| AC-20 | 오류 화면: `ftp://x"><script>alert(1)</script>`. 결과 화면: `https://a.com/<script>alert(1)</script>`와 `…&c=<x>` | 원문 `<script>` 태그가 HTML에 나오지 않음 | 오류 화면은 `&#34;&gt;&lt;script&gt;`로 이스케이프. 결과 화면은 `<script>alert` 원문 0건, `&amp;`와 `&lt;x&gt;`로 이스케이프 | 통과 |
| AC-21 | 없는 코드로 GET | 404 HTML, 안내 문구, 홈 링크 | 404, `<h1>링크를 찾을 수 없습니다</h1>`, `<a href="/">홈으로 가기</a>` | 통과 |
| AC-22 | 홈, 결과, 오류, 404 화면 | `<html lang="ko">`와 viewport meta | 4개 화면 모두 있음 | 통과 |
| AC-23 | 폼으로 만든 코드로 GET | 302 | 302, `location: https://example.org/form?x=1` | 통과 |

### 추가 확인
- D-1: `HTTPS://Example.com/A`는 201이고 그대로 저장됨.
- D-2: 앞쪽 공백이 든 URL은 422이고 "URL에 공백이나 제어 문자를 넣을 수 없습니다." 문구가 나옴.
- D-3: 한글 경로의 Location은 `https://example.com/%ED%95%9C%EA%B8%80`로 퍼센트 인코딩되어 나오고 500 오류는 없음.
- D-4: API 오류 응답은 `{"detail":"<한국어 문구>"}` 형식이고 문구가 plan 3.2 표와 일치함. JSON이 아니거나 배열인 본문은 422 "요청 본문은 JSON 객체여야 합니다."
- D-5: 7자가 아닌 코드(`/ab`)도 404 HTML 화면으로 응답함.
- D-7: 폼에 url 필드가 없으면 HTML 422 화면 "URL을 입력해 주세요."가 나옴.
- 목업 비교: 홈, 결과, 오류, 404 화면의 문구와 마크업이 목업 및 plan 3.6 고정 요소와 일치함.
- `/static/style.css`는 200 text/css, 없는 정적 파일은 404.
- `POST /abc`는 405, `GET /links`는 404로 응답함. 설계서에 규정이 없는 경계 동작이라 지적하지 않았습니다.
- 375px 폭 가로 스크롤은 브라우저로 렌더링하지 않아 확인하지 못했습니다. 목업과 같은 CSS(`flex-wrap`, `min-width:0`, `overflow-wrap`)가 쓰이는 것만 응답에서 확인했습니다.

## 지적 목록
없음.

## 이전 지적 확인 (2라운드부터)
해당 없음(1라운드).
