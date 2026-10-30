---
seq: 11
sender: "qa"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T08:21:42.874Z"
agent: "qa"
agent_id: "a6233e35397c5401e"
turn: 1
reply_to: 9
chars: 3479
tokens_est: 1452
wait_s: null
---

## 결과: 지적 0건 (blocker 0, major 0, minor 0)

검증 대상은 커밋 b42b3bb다. 서버를 실제로 띄워 curl로 확인했다. 서버는 모두 종료했고, 포트 8765와 8766이 비었음을 확인했다. 임시 파일도 지웠고 `git status`는 깨끗하다. 저장소 파일은 수정하지 않았다. `uv run pytest`는 돌리지 않았다(AC-23은 HTTP로만 확인).

## 수용 기준 검증
| AC | 요청 | 기대 | 실제 | 판정 |
|---|---|---|---|---|
| AC-1 | POST /links {url, alias:"my-link"} | 201, code=별칭, short_url=base/별칭 | 201, code="my-link", short_url="http://127.0.0.1:8765/my-link" | PASS |
| AC-2 | GET /my-link | 302 + 원래 URL | 302, location: https://example.com | PASS |
| AC-3 | alias 생략, alias:null | 7자 영숫자 | 3dBsASb, 2BqdKeG (각 7자, 201) | PASS |
| AC-4 | 3, 4, 30, 31자 | 422, 201, 201, 422 | 그대로 | PASS |
| AC-5 | 공백, _, /, ., 한글, -abcd, abcd-, my-link | 앞의 7개는 422, my-link는 생성 | 7개 모두 422. 한글은 raw UTF-8과 `\u` 이스케이프 모두 422 (사유는 아래 비고). my-link는 이미 만든 뒤라 409로 확인 | PASS |
| AC-6 | links, static, stats, docs, redoc, openapi.json, api, admin, manage, Admin | 전부 422 | 전부 422. openapi.json은 문자 규칙, api는 길이 규칙에 먼저 걸림(계획서 D-2, D-5와 일치) | PASS |
| AC-7 | my-link를 다른 URL로 재생성 | 409, 기존 링크 유지 | 409 "이미 쓰이는 별칭입니다...", GET은 기존 URL 그대로 302 | PASS |
| AC-8 | My-Link와 my-link | 둘 다 생성, 각자 URL로 302 | 201, My-Link는 https://upper.com, my-link는 https://example.com | PASS |
| AC-9 | 422와 409 뒤 상태 | 저장 없음 | 409로 거절된 요청이 원본 URL을 바꾸지 않았다. 422로 거절된 별칭 코드는 stats가 404. 저장 개수는 직접 세지 않았다 | PASS |
| AC-10 | GET /, 폼 alias 제출 | label "별칭 (선택)", name="alias", 결과의 단축 URL에 별칭 | 목업과 구조와 문구가 일치. 결과 href는 http://127.0.0.1:8765/web-alias | PASS |
| AC-11 | 폼 422(alias=a_b), 409(중복), URL 오류 | 해당 상태의 HTML, 오류 문구, 입력값 유지 | 422, 409, 422 모두 `p.error#form-error`가 있다. url과 alias 값이 유지되고 따옴표는 `&#34;`로 이스케이프된다. aria-invalid는 오류 대상 필드에만 붙는다. 목업 F2-error-conflict와 동일 | PASS |
| AC-12 | 새 링크 통계 | 200, clicks 0, last_accessed_at null | 그대로 (필드 6개) | PASS |
| AC-13 | GET 3회 후 통계 | clicks 3, 시각 채워짐 | clicks 3, last_accessed_at "2026-10-29T08:20:39Z" | PASS |
| AC-14 | 통계 API 반복 조회 | clicks 불변 | 6에서 6 그대로 | PASS |
| AC-15 | 없는 코드 GET | 404, 클릭 불변 | 404, 기존 링크 clicks 그대로 | PASS |
| AC-16 | GET /links/nonexist/stats | 404 | 404 {"detail":"링크를 찾을 수 없습니다."} | PASS |
| AC-17 | GET /stats/web-alias (접근 전, 접근 후) | 200 HTML, 클릭 수, 원래 URL, "아직 없음" | 접근 전 clicks 0과 "아직 없음". 접근 후 clicks 1, "아직 없음"이 사라지고 `<time>`이 표시됨. 목업 F2-stats-empty, F2-stats와 구조가 일치 | PASS |
| AC-18 | GET /stats/nonexist | 404 HTML | 404, text/html, "링크를 찾을 수 없습니다" | PASS |
| AC-19 | 결과 화면 | /stats/{code} 링크 "통계 보기" | `<a class="back-link" href="/stats/web-alias">통계 보기</a>` | PASS |
| AC-20 | 서버 재시작(같은 DB) | clicks 유지 | clicks 6, last_accessed_at 그대로 | PASS |
| AC-21 | URL `https://example.com/a?x=1&y=<b>` | 이스케이프 | `&amp;y=&lt;b&gt;`. 결과 화면과 통계 화면 모두 해당 | PASS |
| AC-22 | 통계 화면 | lang="ko", viewport | 둘 다 있음 | PASS |
| AC-23 | F1 핵심 흐름 | 201, 302, 404, 홈, 결과, 오류 화면 | 생성 201, 302, 없는 코드 404(HTML), 홈 200, 결과 200, URL 오류 422 화면, /static/style.css 200, /docs 200, /links와 /stats(한 단계 경로) 404 | PASS |
| 호환성 | 3열 스키마 F1 DB에 행 2개를 넣고 그 파일로 서버 시작 | 기존 링크 302, clicks 0부터 | GET /abc1234는 302(https://old.example.com/x). 접근 전 stats는 clicks 0, last_accessed_at null. 2회 더 접근하면 clicks 3(총 3회 접근)으로 정상. 이전된 DB에서도 별칭 생성은 201 | PASS |

## 지적 목록
없음.

비고(결함 아님)
- 검증 중 400 "error parsing the body"가 두 번 나왔다. 둘 다 Windows 셸이나 curl이 한글과 `\u` 문자를 인자로 넘기며 본문을 깨뜨린 탓이다. 파이썬 urllib이나 `--data-binary @파일`로 다시 보내면 422로 정상 처리된다.
- 호환성 테스트 중 처음 한 번은 내 셋업 실수(포트 충돌, 빈 DB)로 500이 났다. 포트를 비우고 F1 DB를 새로 만들어 다시 확인한 결과는 정상이다. 앱의 결함이 아니다.
- 3자 별칭 `a_b`는 순서상 길이 규칙 문구가 먼저 나온다(계획서 D-2와 일치).

## 이전 지적 확인
1라운드라 해당 없음.
