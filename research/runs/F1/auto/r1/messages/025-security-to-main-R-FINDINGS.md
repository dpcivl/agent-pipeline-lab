---
seq: 25
sender: "security"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T04:54:21.152Z"
agent: "security"
agent_id: "a184f4afb29f737c5"
turn: 2
reply_to: 22
chars: 5767
tokens_est: 2791
wait_s: null
---

## 결과: 지적 6건 (blocker 0, major 0, minor 6)

S-1은 고쳐졌고, 새 Location 처리는 헤더 주입이나 응답 분할을 만들지 않습니다. 다만 백슬래시를 그대로 내보내면서 새 문제가 하나 생겨 S-7로 올립니다. S-7은 지금 F1에서는 실제로 악용되지 않아 minor로 매겼고, 1라운드 지적 중 S-1이 해결되어 전체 건수는 6건입니다.

점검 범위와 방법:
- 범위는 `git diff 62a0bf3..5c61fc4`입니다. 소스 변경은 `validation.py` 서로게이트 검사와 `web.py`의 `location_header` 두 곳입니다.
- `uv run bandit -r src -q`의 지적은 0건입니다(종료 코드 0).
- 프로브 스크립트 두 개로 확인했습니다. 경로는 `<HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-dev-agent-pipeline-lab-runs-F1-auto-r1\596f5b0b-4686-4b10-a66a-5c1df0187553\scratchpad\probe2.py`와 같은 폴더의 `probe3.py`입니다. DB는 이 폴더에 만들었고 확인 뒤 지웠습니다. 저장소 파일은 수정하지 않았습니다.
- 브라우저(WHATWG) 해석은 이 환경에 node가 없어 실행하지 못했습니다. 아래 ③의 브라우저 동작은 URL 표준 규칙에 따른 분석입니다.

### ② 새 Location 처리: 헤더 주입이나 응답 분할 없음
- `location_header`는 `quote(url, safe=0x21–0x7E)`입니다. 그래서 출력 가능한 ASCII 밖의 문자는 입력 검증과 상관없이 모두 퍼센트 인코딩됩니다.
- 0x00–0xFF 전체와 몇몇 유니코드 문자를 넣어 봤습니다. 출력에 0x21–0x7E 밖의 바이트는 하나도 없었습니다.
  - ASCII 범위: NUL은 `%00`, TAB은 `%09`, LF는 `%0A`, CR은 `%0D`, 공백은 `%20`, DEL은 `%7F`가 됩니다.
  - latin-1 범위: U+0080은 `%C2%80`, U+0085는 `%C2%85`, U+00A0은 `%C2%A0`, U+00FF는 `%C3%BF`가 됩니다(UTF-8 기준).
  - 그 밖: U+2028은 `%E2%80%A8`, U+202E는 `%E2%80%AE`, U+FEFF는 `%EF%BB%BF`가 됩니다.
- 검증을 거치지 않은 값을 DB에 직접 넣고도 확인했습니다.
  - `https://a.com/\r\nSet-Cookie: x=1`은 Location `https://a.com/%0D%0ASet-Cookie:%20x=1`이 되고 `Set-Cookie` 헤더는 생기지 않습니다.
  - `\nX: y`, `\x00`, 공백, `\xe9\x85`도 모두 인코딩되어 헤더가 하나만 나갑니다.
  - 따라서 D-3 개정의 근거(공백과 제어 문자는 D-2에서 이미 거절됨)에 기대지 않고도 안전합니다.
- `"`, `<`, `>`, `` ` ``, `{`, `|`가 그대로 나가는 점은 문제가 아닙니다. 모두 RFC 9110 필드 값에 쓸 수 있는 문자이고, 302 응답은 본문이 0바이트라 HTML로 렌더링될 곳이 없습니다.
- 참고(지적 아님):
  - DB에 `javascript:alert(1)`이 있으면 Location에 그대로 나갑니다. 1라운드의 Starlette 방식도 같았고, 브라우저는 Location의 `javascript:`를 실행하지 않습니다. 이 경로는 생성 시 검증으로 막혀 있습니다.
  - DB에 서로게이트가 있으면 `quote`가 `UnicodeEncodeError`를 냅니다. 하지만 sqlite3는 이런 값을 저장하지도 읽어 오지도 못하므로 실제로는 도달할 수 없습니다.

### ③ 백슬래시: 1라운드보다 나빠졌음
- 1라운드에서는 `\`가 `%5C`로 나갔습니다. `https://<EMAIL>/`을 브라우저는 userinfo `evil.com%5C`, 호스트 `allowed.com`으로 해석하고, 이는 Python `urlsplit`의 hostname(`allowed.com`)과 같았습니다.
- 지금은 `\`가 그대로 나갑니다. WHATWG URL 파서는 http/https에서 `\`를 `/`처럼 다룹니다. 그래서 `https://evil.com\@allowed.com/`으로 브라우저가 실제로 가는 곳은 `evil.com`이고, 검증기(`urlsplit`)는 여전히 호스트를 `allowed.com`으로 봅니다.
- `https://evil.com\<EMAIL>/`도 같은 패턴입니다. 이렇게 서버의 URL 해석과 브라우저의 해석이 달라졌습니다. 아래 S-7로 기록합니다.

## 지적 목록

### S-2 [minor] 표시를 속이는 유니코드 문자 허용(bidi 제어, C1 제어, 줄 구분자)
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\validation.py:39`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\templates\result.html:14`
- 취약점: 1라운드와 같습니다. U+202E, C1 제어 문자, U+2028 등이 저장되고 결과 화면에 표시됩니다. Location에서는 계속 인코딩되므로 헤더 주입은 없습니다.
- 공격 시나리오: RLO 문자로 결과 화면의 "원래 URL"을 뒤집어 보이게 합니다.
- 수정 제안: 1라운드와 같습니다. C1 제어와 Cf/Zl/Zp/Zs 범주 문자를 거절합니다.

### S-3 [minor] 오픈 리다이렉트 악용 방지 장치 없음(자기 참조 루프, userinfo 위장)
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\web.py:63`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\validation.py:53-56`
- 취약점: 1라운드와 같습니다. 정책 사항입니다.
- 공격 시나리오: 리다이렉트 루프를 만들거나, `https://<EMAIL>/` 형태로 목적지를 위장합니다.
- 수정 제안: 1라운드와 같습니다. 호스트 판정은 S-7의 백슬래시 문제를 먼저 해결한 뒤에 도입해야 합니다.

### S-4 [minor] 인증, 요청 수 제한, 요청 본문 크기 제한 없음(F3 범위)
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\api.py:23`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\web.py:40`
- 취약점: 1라운드와 같습니다.
- 공격 시나리오: 링크를 대량 생성하거나, 큰 본문으로 메모리를 소모시킵니다.
- 수정 제안: 1라운드와 같습니다. F3에서 다룹니다.

### S-5 [minor] 보안 응답 헤더 없음
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\main.py:28-37`
- 취약점: 1라운드와 같습니다.
- 공격 시나리오: 클릭재킹이 가능하고, 이스케이프 실수에 대한 2차 방어선이 없습니다.
- 수정 제안: 1라운드와 같습니다. CSP, nosniff, Referrer-Policy를 추가합니다.

### S-6 [minor] API 문서 엔드포인트가 공개됨
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\main.py:30`
- 취약점: 1라운드와 같습니다.
- 공격 시나리오: API 구조가 노출되고, 외부 CDN 스크립트에 의존합니다.
- 수정 제안: 1라운드와 같습니다. 운영 환경에서는 docs, redoc, openapi URL을 끕니다.

### S-7 [minor] 백슬래시를 그대로 내보내 검증기와 브라우저의 호스트 해석이 달라짐(신규)
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\web.py:22`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\web.py:28-30`, `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\validation.py:43`
- 취약점: `_LOCATION_SAFE`에 `\`가 들어가 Location에 `\`가 그대로 나갑니다. 브라우저는 http/https URL의 `\`를 `/`로 해석하고, `urllib.parse.urlsplit`은 일반 문자로 해석합니다. 실제 예는 다음과 같습니다.

  | 입력 | urlsplit hostname | 1라운드 Location | 지금 Location | 브라우저 목적지 |
  |---|---|---|---|---|
  | `https://evil.com\@allowed.com/` | `allowed.com` | `https://<EMAIL>/` | `https://evil.com\@allowed.com/` | `evil.com` |

  1라운드 방식에서는 브라우저 목적지도 `allowed.com`이라 검증기와 같았습니다.
- 공격 시나리오:
  - 지금 F1에는 호스트 기반 정책이 없어 어디로든 리다이렉트할 수 있으므로 새로 악용할 수 있는 경로는 없습니다. 그래서 minor로 매겼습니다.
  - 하지만 S-3을 고치면서 `parts.hostname`으로 자기 도메인을 차단하거나 차단 목록을 넣으면, `https://blocked.com\@allowed.com/` 형태로 그 검사를 그대로 우회할 수 있습니다. 그 시점에는 major가 됩니다.
  - 결과 화면에 보이는 원래 URL도 사람이 읽기에 목적지(`allowed.com`처럼 보임)를 착각하게 합니다.
- 수정 제안(둘 중 하나):
  - (권장) `validate_url`에서 `\`가 든 URL을 422로 거절합니다. `\`는 RFC 3986 URL에 쓸 수 없는 문자이고, 이렇게 하면 AC-10의 "글자 그대로"를 다른 문자에서 유지하면서 해석 차이가 사라집니다. D-2나 D-3에 결정을 기록합니다.
  - 또는 `_LOCATION_SAFE`에서 `\`만 빼서 `%5C`로 내보냅니다. 1라운드와 같은 동작입니다.

## 이전 지적 확인 (2라운드부터)
- S-1: 해결 — `validation.py:37`에서 U+D800–U+DFFF를 공백·제어 문자 검사보다 먼저 422로 거절합니다. 재현 결과는 다음과 같습니다.
  - `{"url":"https://a.com/\ud800"}`와 `\udfff`는 422(`URL에 쓸 수 없는 문자가 들어 있습니다.`)가 돌아오고, 저장된 행이 없습니다.
  - 올바른 서로게이트 쌍 `\ud83d\ude00`(이모지)은 201로 정상 생성됩니다. 과하게 막지 않습니다.
- S-2: 미해결(minor, 기록만) — 변경 없음.
- S-3: 미해결(minor, 기록만) — 변경 없음. 백슬래시 관련 악화는 S-7로 분리했습니다.
- S-4: 미해결(minor, 기록만) — 변경 없음. F3 범위입니다.
- S-5: 미해결(minor, 기록만) — 변경 없음.
- S-6: 미해결(minor, 기록만) — 변경 없음.
