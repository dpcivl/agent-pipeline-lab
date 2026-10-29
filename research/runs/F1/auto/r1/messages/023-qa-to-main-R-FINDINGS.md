---
seq: 23
sender: "qa"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T04:53:05.048Z"
agent: "qa"
agent_id: "a60810b096cc659b6"
turn: 2
reply_to: 21
chars: 2189
tokens_est: 971
wait_s: null
---

## 결과: 지적 0건 (blocker 0, major 0, minor 0)
2라운드 확인 결과입니다. 체크포인트 5c61fc4(HEAD)를 포트 8765와 임시 DB로 띄워 확인했고, 끝난 뒤 서버를 종료했습니다. 포트 8765 LISTEN 0건, `git status` 변경 없음을 확인했습니다.
변경분은 `git diff 62a0bf3..5c61fc4 --stat`로 봤습니다. 소스는 validation.py와 web.py, 나머지는 문서와 테스트였습니다.

## 수용 기준 검증
| 수용 기준 | 요청 | 기대 | 실제 | 판정 |
|---|---|---|---|---|
| D-3 개정: 출력 가능한 ASCII는 그대로 | 생성 후 GET. url은 `https://example.com/?a=1\|2&b={x}` | Location이 글자 그대로 | `location: https://example.com/?a=1\|2&b={x}` | 통과 |
| D-3 개정 | url은 `https://example.com/<script>alert(1)</script>` | 그대로 | `location: https://example.com/<script>alert(1)</script>` | 통과 |
| D-3 개정 | url은 `https://example.com/a%20b` | `%20`이 그대로 | `location: https://example.com/a%20b` | 통과 |
| D-3 개정: 비ASCII만 UTF-8 퍼센트 인코딩 | url은 `https://example.com/í한글`(`í`와 한글을 JSON 이스케이프로 전송) | 비ASCII만 인코딩 | `location: https://example.com/%C3%AD%ED%95%9C%EA%B8%80` | 통과 |
| D-3 개정 (웹 폼) | 폼에 `https://a.com/?q=1\|2&b={x}`를 제출 | 200 | 200 결과 화면 | 통과 |
| AC-23 | 폼으로 `https://a.com/%ED%95%9C%EA%B8%80?q=\|`(퍼센트 인코딩된 한글)를 제출한 뒤 코드로 GET | 302, 한글만 인코딩 | `location: https://a.com/%ED%95%9C%EA%B8%80?q=\|` | 통과 |
| D-8 서로게이트 거절 | POST /links 본문 `{"url":"https://a.com/\ud800"}` | 422, `URL에 쓸 수 없는 문자가 들어 있습니다.` | 422 `{"detail":"URL에 쓸 수 없는 문자가 들어 있습니다."}` | 통과 |
| D-8 짝이 맞는 이모지 | `https://a.com/😀`(😀) | 201 | 201, url은 `https://a.com/😀`, GET은 302 `location: https://a.com/%F0%9F%98%80` | 통과 |
| D-8 저장 안 됨 | 위 요청들을 모두 보낸 뒤 DB 행 수 확인 | 거절된 요청은 저장되지 않음 | 성공한 요청 10건만 저장됨(거절된 `\ud800` 요청은 행이 없음). 행 수는 읽기 전용으로 열어 센 값 | 통과 |
| AC-1 (회귀) | POST /links `{"url":"https://example.com/path?q=1"}` | 201 | 201, 필드 4개 모두 있음 | 통과 |
| AC-10 (회귀) | GET /{code} | 302 + Location | 302, `location`이 원래 URL과 같음 | 통과 |
| AC-17 (회귀) | 폼으로 올바른 URL 제출 | 200, 단축 URL 링크 | 200, `<a id="short-url" href="http://127.0.0.1:8765/loQe5fp">` | 통과 |

참고 사항
- 폼으로 `%ED%A0%80`(퍼센트 디코딩하면 잘못된 UTF-8)를 보냈을 때도 500 없이 200이 왔습니다.
- 쌍따옴표, 캐럿, 백틱, 역슬래시가 든 URL의 Location도 확인하려 했지만, JSON 원문을 잘못 만들어(`\x` 이스케이프 오류) 422가 나와서 검증하지 못했습니다. 이 항목은 미확인입니다.
- 폼으로 한글 원문을 직접 전달한 요청은 Windows 셸 인코딩 때문에 값이 깨져 신뢰할 수 없어서 판정에서 뺐습니다. 퍼센트 인코딩으로 다시 보낸 결과가 위 AC-23 행입니다.

## 지적 목록
없음.

## 이전 지적 확인 (2라운드부터)
- 1라운드 지적이 없어 확인할 항목이 없습니다.
