---
seq: 14
sender: "qa"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T05:36:06.453Z"
agent: "qa"
agent_id: "aa7468d7770b0ba5c"
turn: 1
reply_to: 10
chars: 4229
tokens_est: 1882
wait_s: null
---

## 결과: 지적 2건 (blocker 0, major 1, minor 1)

서버는 임시 DB, 포트 8765로 띄웠다. 검증이 끝난 뒤 종료했고 포트가 비어 있는 것을 확인했다. 저장소 파일은 수정하지 않았고 `git status`도 깨끗하다.

## 수용 기준 검증
| 수용 기준 | 요청 | 기대 | 실제 | 판정 |
|---|---|---|---|---|
| AC-1 | POST /links `{"url":"https://example.com/path?q=1"}` | 201, 필드 4개 | 201, code/short_url/url/created_at | 통과 |
| AC-2 | 위와 동일 | 7자 영숫자, `short_url`은 base_url/code | `XS0JpCu`, `http://127.0.0.1:8765/XS0JpCu` | 통과 |
| AC-3 | `HTTPS://Example.com/A%20b?x=<y>` | url 글자 그대로 | 그대로 반환, DB에도 원문 그대로 | 통과 |
| AC-4 | `http://example.com` | 201 | 201 | 통과 |
| AC-5 | ftp, javascript:, data:, mailto: | 422 | 4개 모두 422 | 통과 |
| AC-6 | `{}`, `{"url":123}`, `{"url":""}`, `{"url":null}`, 깨진 JSON, `[1]` | 422 | 모두 422. `{}`와 123은 FastAPI 기본 본문, 빈 문자열은 `{"detail":"URL을 입력해 주세요."}` | 통과 |
| AC-7 | `https://`, `https://:80` | 422 | 둘 다 422. `https://`는 "URL에 호스트(도메인)가 없습니다…" | 통과 |
| AC-8 | 2048자 / 2049자 | 201 / 422 | 201 / 422 | 통과 |
| AC-9 | 거절 요청(API ftp, 폼 ftp 등) 전후로 DB 행 수 비교 | 변화 없음 | 106 → 106. 서로게이트 500 요청 후에도 행이 늘지 않음 | 통과 |
| AC-10 | `GET /XS0JpCu` | 302, Location | 302, `location: https://example.com/path?q=1`. 대문자 스킴과 `<`는 그대로(D-4) | 통과 |
| AC-11 | `GET /nonexist` | 404 | 404, text/html (D-6) | 통과 |
| AC-12 | 같은 URL을 두 번 생성 | 코드가 다르고 둘 다 리다이렉트 | 100회 생성 중 같은 URL이 서로 다른 코드를 받음. 개별 리다이렉트도 302 | 통과 |
| AC-13 | 100회 연속 생성 | 코드 100개가 모두 다름 | 고유 코드 100개 | 통과 |
| AC-14 | 같은 DB 경로로 서버를 재시작 | 이전 코드가 리다이렉트됨 | 재시작 후 `XS0JpCu`와 폼으로 만든 `jzwg4Qb` 모두 302 | 통과 |
| AC-15 | created_at 확인 | UTC ISO 8601, 1분 이내 | `2026-10-29T05:33:04Z` 형식. 서버 Date 헤더와 일치 | 통과 |
| AC-16 | `GET /` | 200, text/html, 폼, label, name=url, "줄이기" | 모두 충족. `<form method="post" action="/">`, `<label for="url">`, 목업과 문구·구조가 같음 | 통과 |
| AC-17 | 폼으로 올바른 URL 제출 | 200, 단축 URL 링크와 원래 URL 표시 | `<a class="short-url" href="http://127.0.0.1:8765/jzwg4Qb">`와 원래 URL(`&amp;`로 이스케이프) 표시. 목업과 동일 | 통과 |
| AC-18 | 결과 화면 | "복사" 버튼, `href="/"`인 "다른 URL 줄이기" | `copy-button` 복사 버튼, `back-link` 다른 URL 줄이기, `#copy-status`, `copy.js` defer 모두 있음 | 통과 |
| AC-19 | 폼으로 `ftp://example.com/files/report.pdf` 제출, 빈 값, 필드 없음 | 422 HTML, 오류 메시지, 입력값 유지, 저장 없음 | 422. 오류 문구와 `value=` 유지, `aria-invalid`, `role="alert"`까지 목업과 일치. 행 수 변화 없음 | 통과 |
| AC-20 | `<script>` 포함 URL을 결과 화면과 오류 화면에 제출 | 이스케이프됨 | 결과 화면은 `&lt;script&gt;`로 표시. 오류 화면 `value`도 이스케이프됨. `"><b>x`는 `&#34;&gt;&lt;b&gt;x` | 통과 |
| AC-21 | `GET /zzz` | 404 HTML, 안내 문구, 홈 링크 | "링크를 찾을 수 없습니다", "홈으로 가기" `href="/"`. 목업과 일치 | 통과 |
| AC-22 | 네 화면 | lang="ko", viewport | 모두 있음 | 통과 |
| AC-23 | 폼으로 만든 코드에 `GET` | 302 | 302, `location: https://example.com/a?b=1&c=2` | 통과 |
| 정적 파일 | `/static/style.css`, `/static/copy.js` | 200 | 200. text/css, text/javascript. copy.js 내용은 목업 스크립트와 같음 | 통과 |

375px 가로 스크롤은 블랙박스로 렌더링 확인을 하지 못했다. `style.css`에 목업의 `@media (max-width:480px)` 규칙은 들어 있다.

## 지적 목록
### Q-1 [major] 짝 없는 서로게이트 URL에서 `POST /links`가 500을 반환
- 재현: `curl -s -i -X POST -H 'Content-Type: application/json' --data-binary '{"url":"https://e.com/\ud800"}' http://127.0.0.1:8765/links`
- 기대: 정상이면 201, 거절이면 422. 어떤 경우든 500이면 안 된다. D-5에 따른 `{"detail": "<한국어 문구>"}` 본문이 와야 한다.
- 실제: `500 Internal Server Error`, 본문은 `text/plain` "Internal Server Error". DB에는 저장되지 않아 AC-9는 유지된다. 서버 로그에 예외가 남는다.
- 수정 제안: `validate_url`에서 UTF-8로 인코딩되지 않는 문자열(`url.encode("utf-8")` 실패)을 새 문구로 422 거절하고 문구 상수를 추가한다. 또는 저장과 `Location` 변환 경로에서 이 예외를 처리한다. 폼 경로는 `%ED%A0%80`을 보냈을 때 파서가 대체 문자로 바꿔서 200이 되었다. 즉 JSON 경로에서만 재현된다.

### Q-2 [minor] `https://[` 같은 깨진 호스트에 "호스트가 없습니다" 문구가 나옴
- 재현: `{"url":"https://["}` 또는 폼에 `https://[` 제출
- 기대: 500은 아니고 422여야 한다. 문구는 원인에 맞으면 더 좋다.
- 실제: 422이고 문구는 "URL에 호스트(도메인)가 없습니다. 예: https://example.com"이다. 호스트가 아예 없는 것이 아니라 형식이 잘못된 경우인데 같은 문구가 나온다. 동작상 문제는 없다.
- 수정 제안: 필수 아님. 파싱 `ValueError`용 문구를 별도로 두거나 현재 문구를 유지하고 D 결정에 기록한다.

## 참고 (지적 아님)
- 한글 URL `https://예.com/경로?q=한`은 201로 생성된다. 리다이렉트는 `location: https://%EC%98%88.com/%EA%B2%BD%EB%A1%9C?q=%ED%95%9C`로 퍼센트 인코딩되어 D-4와 일치하고 500이 없다.
- 앞 공백 URL은 `{"detail":"URL에 공백이나 제어 문자를 넣을 수 없습니다."}`로 422이고, 줄바꿈이 든 URL도 422이다(D-2).
- `GET /{code}/`(끝에 슬래시)는 307 후 404가 된다. 설계서 범위 밖이다.
- `HEAD /{code}`는 405이다. 설계서 범위 밖이다.
- 첫 재시작 시도에서 `uv run`이 `uvicorn`을 못 찾는 오류가 한 번 났다. 작업 디렉터리를 `/tmp`에서 실행했기 때문으로 보인다. 저장소 디렉터리에서는 정상이었다.

## 이전 지적 확인
1라운드이므로 해당 없음.
