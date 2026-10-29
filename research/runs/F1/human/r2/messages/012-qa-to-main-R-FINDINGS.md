---
seq: 12
sender: "qa"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T06:39:39.119Z"
agent: "qa"
agent_id: "aa0e6b6432eadb203"
turn: 1
reply_to: 10
chars: 3464
tokens_est: 1514
wait_s: null
---

## 결과: 지적 2건 (blocker 0, major 0, minor 2)

서버는 임시 DB와 8765 포트로 띄워 확인했습니다. 종료 후 8765 포트에 LISTEN 소켓은 없고(TIME_WAIT만 남음), `git status`도 깨끗합니다. 저장소 파일은 수정하지 않았습니다.

## 수용 기준 검증
| 수용 기준 | 요청 | 기대 | 실제 | 판정 |
|---|---|---|---|---|
| AC-1 | POST /links `{"url":"https://example.com/path?q=1"}` | 201과 네 필드 | 201, code, short_url, url, created_at 모두 있음 | 통과 |
| AC-2 | 같은 요청 | 7자 영숫자 code, short_url은 base_url/code | `7IrUU69`, `http://127.0.0.1:8765/7IrUU69` | 통과 |
| AC-3 | `http://Example.com/A#Frag`, `HTTPS://EXAMPLE.com`, `<x>"y` 포함 URL | url이 글자 그대로 | 모두 그대로 돌려줌 | 통과 |
| AC-4 | `http://` URL | 201 | 201 | 통과 |
| AC-5 | ftp, javascript, data, mailto | 422 | 4건 모두 422 | 통과 |
| AC-6 | 필드 없음, 숫자, 불리언, 빈 문자열, null, JSON 아닌 본문, JSON 배열 | 422 | 모두 422. 본문은 `{"detail":"<한국어>"}` | 통과 |
| AC-7 | `https://`, `http://`, `https:///path` | 422 | 422 (MSG_NO_HOST) | 통과 |
| AC-8 | 2048자 / 2049자 | 201 / 422 | 201 / 422 (API와 폼 모두) | 통과 |
| AC-9 | 거절 요청(API 422, 폼 422, 필드 없는 폼) 전후 DB 행 수 | 변화 없음 | 113 → 113 | 통과 |
| AC-10 | GET /{code} | 302와 Location | 302, `location: https://example.com/path?q=1` | 통과 |
| AC-11 | GET /zzzzzzz | 404 | 404 HTML | 통과 |
| AC-12 | 같은 URL 2회 생성 | 코드가 다르고 둘 다 리다이렉트 | 코드가 다르고 둘 다 302 | 통과 |
| AC-13 | 100회 연속 생성 | 100개 모두 고유 | 고유 코드 100개 | 통과 |
| AC-14 | 같은 DB 경로로 서버를 껐다 다시 띄운 뒤 GET | 302 | 302, Location 동일 | 통과 |
| AC-15 | created_at | `YYYY-MM-DDTHH:MM:SSZ`, 요청 시각과 1분 이내 | `2026-10-29T06:38:24Z`, 서버 date 헤더 06:38:23 | 통과 |
| AC-16 | GET / | 200, text/html, 폼, label, name="url", "줄이기" | 모두 있음. 목업과 문구가 일치 | 통과 |
| AC-17 | POST / 올바른 URL | 200, 단축 URL href, 원래 URL | `<a class="short-url" href=...>`와 `.original-url` 있음 | 통과 |
| AC-18 | 결과 화면 | "복사" 버튼, href="/" 링크 | `data-copy` 버튼과 "다른 URL 줄이기" 링크 있음 | 통과 |
| AC-19 | POST / ftp URL, 빈 값, 필드 없음 | 422, 오류 문구, 입력값 유지, 저장 없음 | 422, `<p class="error" id="url-error" role="alert">`, value와 aria-invalid 있음, 저장 없음 | 통과 |
| AC-20 | `...<script>`, `ftp://x"><script>...` | 이스케이프 | `&lt;script&gt;`, value 속성은 `&#34;&gt;&lt;`로 이스케이프. 원문 태그 없음 | 통과 |
| AC-21 | GET /zzzzzzz | 404 HTML, 안내 문구, 홈 링크 | "링크를 찾을 수 없습니다", "주소가 정확한지 확인해 주세요.", `href="/"` 있음. 목업과 일치 | 통과 |
| AC-22 | 홈, 결과, 오류, 404 화면 | `lang="ko"`, viewport meta | 모두 있음 | 통과 |
| AC-23 | 폼으로 만든 코드 GET | 302 | 폼으로 만든 링크 `qiyxU4E`로 요청해 확인. Location은 위와 동일하게 동작 | 통과 |

경계 상황 결과는 다음과 같습니다.
- `" https://a.com"`, `https://a.com/a b`, NUL 문자, U+00A0 포함 URL은 모두 422입니다(D-1).
- 비ASCII URL `https://a.com/한글?q=é`는 201로 원문을 그대로 돌려줍니다. Location은 `https://a.com/%ED%95%9C%EA%B8%80?q=%C3%A9`입니다(D-6).
- GET /links는 404 HTML이고(계획서와 동일), `/static/style.css`와 `/static/copy.js`는 200입니다.
- 잘못된 UTF-8 바이트 본문은 422입니다.
- `Content-Type: text/plain`인 JSON 본문은 201로 처리됩니다. 계획서에서 본문을 직접 읽는다고 했으므로 의도된 동작으로 봅니다.
- 템플릿 문구와 구조는 목업(home, result, input-error, not-found)과 일치합니다. 홈 화면에 헤더가 없는 것도 목업과 같습니다.

## 지적 목록
### Q-1 [minor] 범위를 벗어난 포트 번호를 가진 URL이 생성됨
- 재현: `POST /links` 본문 `{"url":"http://a.com:99999/"}`
- 기대: 설계서와 계획서에 포트 검증 규칙은 없습니다. 그래도 접속할 수 없는 URL이므로 거절하는 편이 자연스럽습니다. 리다이렉트 자체는 문제가 없습니다.
- 실제: 201로 생성됩니다. `https://[::1`처럼 형식이 깨진 호스트는 422(MSG_NO_HOST)로 거절됩니다.
- 수정 제안: 설계서 범위 밖이므로 현행 유지해도 됩니다. 거절하려면 `urlsplit(...).port` 접근에서 발생하는 ValueError를 검증에 추가하고, 문구는 계획서 3절에 정해야 합니다.

### Q-2 [minor] `HEAD /{code}`가 405를 반환함
- 재현: `curl -I http://127.0.0.1:8765/7IrUU69`
- 기대: 설계서에 규정은 없습니다. GET 리다이렉트와 같은 302를 기대할 수 있습니다.
- 실제: 405 Method Not Allowed
- 수정 제안: 설계서에 없으므로 무시해도 됩니다. 링크 미리보기나 링크 검사 도구를 고려한다면 HEAD도 허용합니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)
