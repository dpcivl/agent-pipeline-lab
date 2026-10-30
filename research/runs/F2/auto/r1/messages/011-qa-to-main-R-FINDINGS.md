---
seq: 11
sender: "qa"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T07:20:23.897Z"
agent: "qa"
agent_id: "a3459ae8c94d484cc"
turn: 1
reply_to: 9
chars: 3229
tokens_est: 1422
wait_s: null
---

## 결과: 지적 1건 (blocker 0, major 0, minor 1)

서버는 임시 DB와 포트 8765로 띄웠고, 검증이 끝난 뒤 종료했습니다. 포트 8765는 비어 있는 것을 확인했습니다. 저장소 파일은 수정하지 않았습니다.

## 수용 기준 검증
| 수용 기준 | 요청 | 기대 | 실제 | 판정 |
|---|---|---|---|---|
| AC-1 | POST /links alias=my-link | 201, code와 short_url이 별칭 | 201, code=my-link, short_url=`http://127.0.0.1:8765/my-link` | 통과 |
| AC-2 | GET /my-link | 302 | 302, location은 원래 URL | 통과 |
| AC-3 | alias 생략 또는 null | 7자 코드 | 둘 다 201, 7자 코드 | 통과 |
| AC-4 | 3자, 4자, 30자, 31자 | 422, 201, 201, 422 | 그대로 | 통과 |
| AC-5 | `a_bcd`, `a.bcd`, `ab cd`, `-abcd`, `abcd-`, 한글 | 422 | 모두 422. 한글은 UTF-8 파일로 보내 확인했고 "영문, 숫자, 하이픈만" 문구 | 통과 |
| AC-6 | links, static, stats, docs, redoc, admin, manage, Admin | 422 | 422. `openapi.json`은 문자 규칙으로, `api`는 길이 규칙으로 먼저 걸려 422 (E-1 검사 순서대로) | 통과 |
| AC-7 | 같은 별칭 재생성 | 409, 기존 링크 유지 | 409 `{"detail":"이미 쓰이는 별칭입니다. 다른 별칭을 입력해 주세요."}`. 무작위로 만든 기존 코드와 같은 별칭도 409. 기존 링크는 원래 URL로 302 | 통과 |
| AC-8 | My-Link와 my-link | 둘 다 생성, 각자 URL로 302 | 201, 각자의 URL로 302 | 통과 |
| AC-9 | 거절된 별칭 | 저장 안 됨 | `/abc`, `/my_link`, `/links/Admin/stats` 모두 404 | 통과 |
| AC-10 | GET /, 폼 제출 | label이 붙은 alias 입력칸, 결과에 별칭 | `<label for="alias">별칭 (선택)</label>`과 `name="alias"`가 있고, 결과의 단축 URL이 `/form-alias` | 통과 |
| AC-11 | 폼에 잘못된 별칭, 중복 별칭 | 422, 409 HTML에 오류 문구, 입력값 유지 | 422, 409. `id="form-error" role="alert"` 문구가 목업과 같고, 문제가 된 입력칸에 `aria-invalid="true"`, URL과 별칭 값이 남음. URL과 별칭이 모두 틀리면 URL 오류만 표시 | 통과 |
| AC-12 | 새 링크 통계 | clicks 0, last_accessed_at null | 그대로 | 통과 |
| AC-13 | GET 3회 | clicks 3, 시각 채워짐 | clicks 3, 시각 채워짐 | 통과 |
| AC-14 | 통계 API 반복 조회 | clicks 불변 | 3 그대로 | 통과 |
| AC-15 | 없는 코드 GET | 다른 링크 clicks 불변 | 7자 코드와 긴 별칭형 코드 모두 404, 기존 링크 clicks 불변 | 통과 |
| AC-16 | 없는 코드의 통계 API | 404 | 404 JSON `{"detail":"링크를 찾을 수 없습니다."}` | 통과 |
| AC-17 | GET /stats/{code} | 200, 클릭 수, 원래 URL, "아직 없음" | 목업과 같은 구조. 접근이 없으면 `<dd class="muted">아직 없음</dd>` | 통과 |
| AC-18 | 없는 코드의 통계 화면 | 404 HTML | F1과 같은 "링크를 찾을 수 없습니다" 화면 | 통과 |
| AC-19 | 결과 화면 링크 | `/stats/{code}` "통계 보기" | `<a class="back-link" href="/stats/form-alias">통계 보기</a>` | 통과 |
| AC-20 | 서버 재시작 후 같은 DB | clicks 유지 | clicks 3과 last_accessed_at 유지 | 통과 |
| AC-21 | 통계 화면 이스케이프 | 이스케이프 | `&#34;&gt;&lt;script&gt;`로 이스케이프되고 script 태그는 없음 | 통과 |
| AC-22 | 통계 화면 head | lang="ko", viewport | 둘 다 있음. `/static/style.css`도 200 | 통과 |
| F1 회귀 | POST /links, GET /{code}, 없는 코드, 폼 422 | F1 동작 유지 | 201, 302, 404 HTML, URL 검증 422(API는 JSON, 폼은 HTML)가 모두 정상. 홈 화면도 정상 | 통과 |
| 호환성 | F1 스키마와 행 하나(`Old1234`)로 만든 DB로 시작 | 리다이렉트 동작, clicks 0부터 | 시작 성공. 통계는 clicks 0, last_accessed_at null. GET 후 clicks 1, 통계 화면 200. 같은 DB에 새 별칭 생성도 정상 | 통과 |

## 지적 목록
### Q-1 [minor] alias가 문자열이 아닐 때 422 본문이 설계된 문구가 아니라 FastAPI 기본 형식
- 재현: `POST /links` 본문 `{"url":"https://example.com","alias":123}`. `["abcd"]`와 `true`도 같음.
- 기대: F2-index 목업에는 "alias는 문자열이어야 합니다."가 있습니다. F1 D-5와 E-8 형식은 `{"detail": "<문구>"}`입니다.
- 실제: 422이지만 본문이 `{"detail":[{"type":"string_type","loc":["body","alias"],"msg":"Input should be a valid string","input":123}]}`입니다. 다른 별칭 오류와 형식과 문구가 다릅니다.
- 수정 제안: alias 타입 검증을 pydantic에 맡기지 말고 직접 처리해서 `{"detail":"alias는 문자열이어야 합니다."}`를 422로 반환하세요.

참고: `alias:""`는 422이고 문구는 "별칭은 4자 이상 30자 이하여야 합니다."로 E-3과 같습니다. 이 항목은 이상이 없습니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)
