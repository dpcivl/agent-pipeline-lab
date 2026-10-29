---
seq: 12
sender: "qa"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T02:23:53.403Z"
agent: "qa"
agent_id: "aed70ddfd3bef930d"
turn: 1
reply_to: 10
chars: 3534
tokens_est: 1470
wait_s: null
---

## 결과: 지적 0건 (blocker 0, major 0, minor 0)

임시 DB(`/tmp/tmp.pVATjvcjFI/qa.db`)와 포트 8765로 서버를 띄워 블랙박스로 확인했습니다. 서버는 종료했고 포트 8765가 비었습니다. `git status`도 깨끗합니다.

## 수용 기준 검증
| 수용 기준 | 요청 | 기대 | 실제 | 판정 |
|---|---|---|---|---|
| AC-1 | POST /links `{"url":"https://example.com/path?q=1"}` | 201, 네 필드 | 201, `code`, `short_url`, `url`, `created_at` 모두 있음 | 통과 |
| AC-2 | 같은 요청 | 7자 영숫자, `short_url`=`base/code` | `pF3xFfT`, `http://127.0.0.1:8765/pF3xFfT` | 통과 |
| AC-3 | 쿼리, `HTTPS://Example.com/Path` | 글자 그대로 | 그대로 반환 (대문자 유지) | 통과 |
| AC-4 | `http://example.com` | 201 | 201 | 통과 |
| AC-5 | ftp, javascript, data, mailto | 422 | 전부 422 (스킴 문구) | 통과 |
| AC-6 | `{}`, `5`, `""`, `null` | 422 | 전부 422 | 통과 |
| AC-7 | `https://` | 422 | 422, "URL에 호스트(도메인)가 없습니다." | 통과 |
| AC-8 | 2,048자와 2,049자 (API와 폼) | 201 / 422 | API와 폼 모두 2,048자는 성공, 2,049자는 422 | 통과 |
| AC-9 | 거절 요청(API 스킴 오류, 폼 ftp, API `{}`) 전후로 DB 행 수 비교 | 변화 없음 | sqlite 직접 조회에서 111 → 111 | 통과 |
| AC-10 | `GET /{code}` | 302와 `Location` | 302, `location: https://example.com/path?q=1&A=B` | 통과 |
| AC-11 | 없는 7자 코드 `AAAAAAA` | 404 | 404 HTML | 통과 |
| AC-12 | 같은 URL 2회 | 코드가 다르고 둘 다 302 | `ylvd4mh`, `6tUTVud` (리다이렉트는 `Location` 일치로 확인한 항목 외에는 개별 GET 생략) | 통과 |
| AC-13 | 100회 연속 생성 | 모두 다름 | 100개 모두 고유 | 통과 |
| AC-14 | 같은 DB 경로로 서버 재시작 후 이전 코드 GET | 302 | 재시작 후 `q9XltM5` → 302 `https://persist.example.com/x` | 통과 |
| AC-15 | `created_at` | UTC ISO 8601, 1분 이내 | `2026-10-29T02:21:41Z` 형식, 서버 시각(`date -u`)과 일치 | 통과 |
| AC-16 | `GET /` | 200, text/html, 폼, label, 버튼 | 200, `text/html; charset=utf-8`, `form method=post action=/`, `label for=url`, `name="url"`, "줄이기" 버튼 | 통과 |
| AC-17 | 폼 제출 `https://example.com/a?x=1&y=2` | 200, 단축 URL 링크와 원래 URL | 200, `<a id="short-url" href="http://127.0.0.1:8765/OD8Dox3">`, 원래 URL 표시 (`&amp;`로 이스케이프) | 통과 |
| AC-18 | 결과 화면 | "복사" 버튼, "다른 URL 줄이기" 링크 | `button.copy-button data-copy` "복사", `<a href="/">다른 URL 줄이기</a>` | 통과 |
| AC-19 | 폼에 `ftp://files.example.com/report.pdf` | 422, 오류 문구, 입력값 유지, 저장 없음 | 422, `p.error#url-error role=alert`, `value=` 유지, `aria-invalid` 및 `aria-describedby`, 저장 수 변화 없음 | 통과 |
| AC-20 | `<script>`가 든 URL (결과 화면과 오류 화면) | 이스케이프 | 결과 화면 `&lt;script&gt;alert(1)&lt;/script&gt;`, 오류 화면 `value="&lt;script&gt;..."`, 속성 따옴표 `&#34;` 처리 (원문 태그 없음) | 통과 |
| AC-21 | 없는 코드 GET | 404 HTML, 안내 문구, 홈 링크 | 404, "링크를 찾을 수 없습니다", `<a href="/">홈으로 가기</a>` | 통과 |
| AC-22 | 홈, 결과, 입력 오류, 404 | `lang="ko"`, viewport | 4개 화면 모두 있음 | 통과 |
| AC-23 | 폼으로 만든 코드 GET | 302 | `q9XltM5` → 302 | 통과 |

## 추가 경계 확인 (모두 계획서 4절과 7절 결정에 부합)
- 홈, 결과, 입력 오류, 404 화면의 문구, 구조, `<title>`이 목업과 일치합니다. 오류 화면에는 `aria-describedby="url-error url-hint"`가 있습니다. 결과 화면에는 `/static/copy.js` 스크립트 태그가 있습니다.
- `/static/style.css`는 200 `text/css`, `/static/copy.js`는 200 `text/javascript`로 제공됩니다.
- 스킴 대문자 `HTTPS://Example.com/Path`는 201이고 저장은 입력 그대로입니다 (D-4).
- 앞뒤 공백, 중간 공백, 개행이 든 URL은 422 "공백이나 제어 문자" 문구입니다 (D-3). 폼에서도 같은 문구가 나오고 입력값이 남습니다.
- 비ASCII URL `https://예시.com/경로?q=한글`은 UTF-8 바이트로 보내면 201입니다. 리다이렉트는 302이고 `location`이 퍼센트 인코딩됩니다 (D-7). Git Bash에서 비ASCII를 `-d`로 직접 보낸 첫 시도가 "error parsing the body"로 실패했는데, 셸 인코딩 문제이고 서버 문제가 아닙니다. UTF-8 파일로 보내면 정상입니다.
- 잘못된 JSON 본문(`{bad`), 빈 본문, `[]`, `"x"`, Content-Type 없는 본문은 모두 422 `{"detail":[...]}`입니다 (D-1).
- 폼에서 `url` 필드가 없는 경우(빈 POST, `foo=bar`)는 422 "URL을 입력해 주세요." 화면입니다 (D-8).
- `/favicon.ico`, `/robots.txt`, `/short`, `/abcdefgh`는 모두 404 HTML 화면입니다 (D-9).
- `PUT /`는 405입니다. `GET /links`는 404이며, 7자 영숫자가 아니라서 코드 아님으로 처리된 것으로 보입니다.

## 지적 목록
없음.

## 이전 지적 확인 (2라운드부터)
해당 없음 (1라운드).
