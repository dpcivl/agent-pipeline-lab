---
seq: 12
sender: "qa"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-30T00:48:10.831Z"
agent: "qa"
agent_id: "a9261a1aaf1377a99"
turn: 1
reply_to: 10
chars: 4032
tokens_est: 1668
wait_s: null
---

## 결과: 지적 0건 (blocker 0, major 0, minor 0)

F2 QA 1라운드(체크포인트 16fdb28) 결과입니다. AC-1~AC-23, 호환성, 재시작 유지, 목업 대조 모두 PASS이고 문제는 발견하지 못했습니다.

방법: 포트 8765에 서버를 띄워 curl과 python urllib로 블랙박스 검증했습니다. DB는 저장소 안 `qa_tmp/*.db`에 두었다가 끝나고 지웠습니다. 서버는 종료했고 8765 포트는 LISTENING이 없고 TIME_WAIT만 남아 있습니다. `git status`는 clean입니다. 저장소 파일은 수정하지 않았습니다.

## 수용 기준 검증
| 수용 기준 | 요청 | 기대 | 실제 | 판정 |
|---|---|---|---|---|
| AC-1 | POST /links {url, alias:"my-link"} | 201, code=별칭, short_url=base/별칭 | 201, code "my-link", short_url "http://127.0.0.1:8765/my-link" | PASS |
| AC-2 | GET /my-link | 302 원래 URL | 302, location https://example.com/a | PASS |
| AC-3 | alias 필드 없음 / null | 7자 영숫자 코드 | 둘 다 201, 7자 코드(88lj3Sk, e7G6Ri1) | PASS |
| AC-4 | 3자, 31자, 4자, 30자 | 422, 422, 201, 201 | 422, 422, 201, 201 | PASS |
| AC-5 | 공백, `_`, `/`, `.`, 한글, `-abcd`, `abcd-`, `a-b-c-d` | 앞의 7개는 422, `a-b-c-d`는 201 | 그대로. 한글, `éabcd`, 전각 `ａｂｃｄ`, 개행·앞뒤 공백, 아랍 숫자도 422 | PASS |
| AC-6 | 예약어 9개와 `Admin`, `Links`, `STATS`, `ReDoc` | 422 | 전부 422. `api`는 3자라 길이 문구, `openapi.json`은 문자 규칙 문구로 거절(계획 3.1의 검사 순서와 일치) | PASS |
| AC-7 | 같은 별칭으로 재생성, 기존 무작위 코드(88lj3Sk)를 별칭으로 | 409, 기존 링크 유지 | 409 "이미 쓰이는 별칭입니다…", 기존 링크 302 유지, 무작위 코드 충돌도 409 | PASS |
| AC-8 | My-Link와 my-link | 둘 다 생성, 각자 URL로 302 | 201, 각자 https://upper.com / https://example.com/a로 302 | PASS |
| AC-9 | API 422·409 4건 전후 DB 행 수. 폼 422·409 전후 행 수 | 변화 없음 | 12행 → 12행. 폼 거절 뒤에도 행 수 그대로 | PASS |
| AC-10 | GET /, 폼으로 alias 제출 | label for="alias" "별칭 (선택)", 결과 단축 URL이 별칭 | label과 name="alias" 입력칸 있음. 결과 HTML의 short-url과 data-copy가 `/form-alias` | PASS |
| AC-11 | 폼 422(`fall_sale"x`), 409(중복), 예약어, 빈 별칭 | 422/409 HTML, 오류 문구, URL·별칭 값 유지 | 422/409 상태와 문구가 목업과 같고 `value`가 이스케이프되어 유지됨. 별칭 칸에만 aria-invalid. URL 오류면 URL 칸에만 aria-invalid. 빈 별칭은 무작위 7자 코드(D2-1) | PASS |
| AC-12 | 새 링크 GET /links/abcd/stats | 200, clicks 0, last_accessed_at null | 200, `"clicks":0,"last_accessed_at":null`, 필드 6개 | PASS |
| AC-13 | GET /my-link 3회 | clicks 3, last_accessed_at 채움 | 3번 만에 3이 되고 `last_accessed_at` 채워짐, 형식 `…Z` | PASS |
| AC-14 | 통계 API 3회 조회와 통계 화면 조회 | clicks 불변 | 6 → 6 | PASS |
| AC-15 | GET /nonexist1 | 404, 다른 링크 클릭 수 불변 | 404, 다른 링크 clicks 불변 | PASS |
| AC-16 | GET /links/nope/stats | 404 | 404 JSON `{"detail":"링크를 찾을 수 없습니다."}` | PASS |
| AC-17 | GET /stats/my-link, /stats/abcd | 200 HTML, 클릭 수, 원래 URL, 접근 전 "아직 없음" | 200 text/html, 클릭 수와 원래 URL 표시. 접근 전 `<dd class="muted">아직 없음</dd>`, 접근 후에는 `<time>` 표시 | PASS |
| AC-18 | GET /stats/nope | 404 HTML | 404 text/html, "링크를 찾을 수 없습니다", F1 404와 본문 동일 | PASS |
| AC-19 | 결과 화면 | /stats/{code} "통계 보기" 링크 | 무작위 코드와 별칭 둘 다 `<a class="stats-link" href="/stats/…">통계 보기</a>`, `.result-actions` 안에 있음 | PASS |
| AC-20 | 서버 재시작 전후 | 클릭 수 유지 | my-link 6 → 재시작 후 6, abcd 30 → 30, 이후 접근 시 7 | PASS |
| AC-21 | url=`https://example.com/<script>alert(1)</script>`, alias xss-test | 이스케이프 | 통계 화면에 `&lt;script&gt;`, 원문 `<script>` 없음 | PASS |
| AC-22 | GET /stats/{code} | lang=ko, viewport, CSP | `<html lang="ko">`, viewport meta 있음, CSP·nosniff 헤더 있음 | PASS |
| AC-23 | F1 흐름 표본과 `uv run pytest` | F1 유지 | 홈 200, URL 규칙 위반·빈 URL·`{}`·잘못된 JSON 모두 422, F1 404 화면 동일, /docs·/openapi.json·/static 200. pytest 393 passed | PASS |
| 호환성(F1 DB) | 열 3개(code, url, created_at)로 만든 DB에 행 2개 삽입 후 서버 기동 | 기동 성공, 기존 링크 302, clicks 0부터 | 정상 기동(PRAGMA로 열 추가됨). stats clicks 0, last_accessed_at null. GET으로 302 후 clicks 1, 다른 행은 0. 이후 별칭 생성 201. 재시작 시 마이그레이션 재실행도 무해하고 clicks 1 유지 | PASS |
| 동시성 보조 확인 | GET /abcd 30개 동시 요청 | 클릭 30 | clicks 30으로 누락 없음 | PASS |
| 목업 대조 | F2-home, error-alias, error-duplicate, result, stats, stats-empty | 문구·구조 일치 | 라벨, 안내 문구, 오류 위치(폼 맨 위 `p.error#form-error`), aria 속성, 통계 구조(click-count, stats-list, time datetime)가 목업과 같음. style.css에 F2 추가 스타일 블록 있음. 목업의 샘플 값(예: fall-sale-2026)만 실제 값으로 바뀜 | PASS |

## 지적 목록
없음.

참고(지적 아님):
- 셸에서 curl로 한글을 보냈을 때 400이 나온 것은 Git Bash의 인코딩 문제입니다. python으로 UTF-8 JSON을 보내면 한글 alias가 설계대로 422로 거절됩니다.
- `HEAD /{code}`는 405이고 `/stats/`처럼 끝에 슬래시가 붙으면 307입니다. 둘 다 F1 동작과 같고 F2 요구사항 밖입니다.

## 이전 지적 확인
1라운드라 해당 없음.
