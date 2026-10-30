---
seq: 13
sender: "qa"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-30T00:02:36.342Z"
agent: "qa"
agent_id: "a72746a8b0cb3d19c"
turn: 1
reply_to: 10
chars: 3583
tokens_est: 1530
wait_s: null
---

## 결과: 지적 0건 (blocker 0, major 0, minor 0)

서버를 임시 DB로 띄워 HTTP로 확인한 결과, F2 AC-1~AC-22는 모두 PASS입니다. F1 DB 호환도 PASS입니다. AC-23은 F1 주요 흐름을 다시 확인했고 `uv run pytest`도 405개 모두 통과했습니다.

환경은 다음과 같습니다.
- 포트 8765와 8766을 사용했습니다.
- DB는 임시 경로 `/tmp/qa1` 아래에 만들었습니다.
- 저장소의 shortlink.db는 건드리지 않았습니다.
- 검증이 끝난 뒤 서버를 모두 종료했고, 두 포트에 LISTEN 상태가 없는 것을 확인했습니다.
- `git status`는 깨끗합니다.

## 수용 기준 검증
| 수용 기준 | 요청 | 기대 | 실제 | 판정 |
|---|---|---|---|---|
| AC-1 | POST /links {url, alias:"my-link"} | 201, code=my-link, short_url=<base>/my-link | 201, code "my-link", short_url "http://127.0.0.1:8765/my-link" | PASS |
| AC-2 | GET /my-link | 302, Location이 원래 URL | 302, location: https://example.com | PASS |
| AC-3 | alias 생략, alias:null | 7자 영숫자 | "o2h8byi", "NbAAvdw" | PASS |
| AC-4 | 3자, 4자, 30자, 31자 | 422, 201, 201, 422 | 422, 201, 201, 422 | PASS |
| AC-5 | `ab_cd`, `ab.cd`, `ab/cd`, `ab cd`, 한글 4자, 전각 숫자, `-abcd`, `abcd-`, `abcd\n` | 모두 422 | 모두 422 (한글과 전각은 UTF-8 파일 본문으로 보냄) | PASS |
| AC-6 | links, static, stats, docs, redoc, openapi.json, api, admin, manage, Admin | 422 | 모두 422 | PASS |
| AC-7 | my-link 재생성 | 409이고 기존 링크 유지. 무작위 코드와 같은 별칭도 409 | 409, 기존 링크는 https://example.com으로 302. 무작위 코드 R09b3Bi로 시도해도 409 | PASS |
| AC-8 | My-Link와 my-link | 둘 다 생성, 각자 URL로 302 | My-Link는 https://other.com, my-link는 https://example.com | PASS |
| AC-9 | 422·409 거절 뒤 DB 행 수 | 거절된 값이 저장되지 않음 | 15행이 모두 성공한 요청과 일치. 거절된 값(abc, links, Admin, 빈 문자열 등)은 DB에 없음 | PASS |
| AC-10 | 홈 폼, 폼으로 별칭 제출 | label for="alias", input name="alias", 결과의 단축 URL에 별칭 | label "별칭 (선택)", input name="alias" 있음. 결과 화면 단축 URL이 /form-ali | PASS |
| AC-11 | 폼에 `my_link` 제출, 중복 별칭 제출 | 422·409 HTML, 오류 문구, url과 alias 값 유지 | 422와 409 모두 오류 문구가 나오고 입력값이 유지됨. 오류가 난 칸에만 aria-invalid가 붙음. URL의 `<x>"`는 이스케이프됨. 목업 F2-alias-error와 같은 구조 | PASS |
| AC-12 | 새 링크의 통계 API | 200, clicks 0, last_accessed_at null | 200, `"clicks":0`, `null` | PASS |
| AC-13 | GET /{code} 3번 | clicks 3, last_accessed_at 채워짐 | 이전 접근 2회에 3회를 더해 5. last_accessed_at이 `2026-10-29T23:58:10Z` 형식으로 채워짐 | PASS |
| AC-14 | 통계 API와 화면을 여러 번 조회 | clicks가 늘지 않음 | 통계 API를 반복 조회해도 5로 유지. 통계 화면도 0으로 유지 | PASS |
| AC-15 | 없는 코드로 GET | 404이고 클릭 수 변화 없음 | 404. 다른 링크의 clicks는 그대로 | PASS |
| AC-16 | 없는 코드의 통계 API | 404 | 404, `{"detail":"링크를 찾을 수 없습니다."}` | PASS |
| AC-17 | GET /stats/{code} | 200 HTML, 클릭 수, 원래 URL, 접근 전에는 "아직 없음" | 목업 F2-stats와 일치. 접근 전에는 "아직 없음", 접근 후에는 `<time>`으로 표시. 1,234번 접근 뒤 "1,234회"로 표시 | PASS |
| AC-18 | 없는 코드의 통계 화면 | 404 HTML | 404, "링크를 찾을 수 없습니다" 화면 (F1과 같음) | PASS |
| AC-19 | 결과 화면의 링크 | href="/stats/{code}", 글자 "통계 보기" | `<a class="stats-link" href="/stats/form-ali">통계 보기</a>` | PASS |
| AC-20 | 같은 DB로 서버 재시작 | 클릭 수 유지 | 재시작 뒤 clicks 1234 유지 | PASS |
| AC-21 | URL에 `<script>alert(1)</script>`가 든 링크의 통계 화면 | 원문 없음, `&lt;script&gt;` 있음 | `https://example.com/&lt;script&gt;alert(1)&lt;/script&gt;` | PASS |
| AC-22 | 통계 화면 | `<html lang="ko">`, viewport meta | 둘 다 있음 | PASS |
| AC-23 | F1 주요 흐름과 `uv run pytest` | F1 AC 유지 | 생성 201, 302 리다이렉트, 없는 코드 404, URL 검증 422, 결과 화면과 오류 화면 모두 정상. pytest 405 passed | PASS |
| F1 DB 호환 | F1 스키마(3컬럼)로 만든 DB에 abc1234 행을 넣고 서버를 띄움 | 기존 링크가 리다이렉트되고 clicks가 0부터 셈 | 통계 clicks 0, last_accessed_at null. GET /abc1234는 302로 https://old.example.com/x. 이후 clicks 1. 통계 화면 200. 새 별칭 생성 201. abc1234를 별칭으로 쓰면 409. 서버를 다시 띄워도(마이그레이션 두 번째 실행) 오류 없이 clicks 1 유지 | PASS |

## 지적 목록
없음.

참고로 다음 두 가지는 앱 문제가 아니라 내 검증 환경의 문제였습니다.
- Windows 셸에서 한글이나 `\u` 이스케이프를 명령줄 인자로 보냈을 때 400 "error parsing the body"가 났습니다. UTF-8 파일 본문으로 보내면 정상적으로 422가 됩니다.
- 처음에는 클릭 증가가 느린 curl 반복문으로 확인했습니다.

## 이전 지적 확인
1라운드라 해당 없음.
