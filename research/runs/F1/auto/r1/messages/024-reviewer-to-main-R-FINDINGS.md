---
seq: 24
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T04:53:19.429Z"
agent: "reviewer"
agent_id: "a449550ba56e63033"
turn: 2
reply_to: 20
chars: 3365
tokens_est: 1540
wait_s: null
---

## 결과: 지적 5건 (blocker 0, major 0, minor 5)
2라운드 결과: R-1(major)은 해결됐습니다. 이번 변경분에서 새로 나온 지적은 R-6(minor) 1건뿐입니다. 나머지 R-2~R-5는 기록만 하기로 한 minor입니다.

## 지적 목록

### R-6 [minor] 새 테스트의 사소한 정리 사항 (새 지적)
- 위치: `tests/test_api_validation.py:202`, `tests/test_validation.py:161`
- 문제:
  - (1) `assert "\\ud" in content or "\\ude" in content`에서 뒤쪽 조건은 의미가 없습니다. `"\\ude"`를 포함하는 문자열은 항상 `"\\ud"`도 포함하므로 앞쪽 조건만으로 결과가 정해집니다. 이 assert는 제품 동작이 아니라 테스트 입력을 검사합니다.
  - (2) 검사 순서 표 테스트에서 다른 줄의 주석은 4a/4b로 바뀌었는데, `("javascript:alert(1) x", MSG_CONTROL)`의 주석만 `# rule 4 before rule 5`로 남아 있습니다.
- 근거: 동작에는 영향이 없습니다. 읽는 사람이 헷갈릴 수 있는 정도입니다.
- 수정 제안: (1) `assert "\\ud" in content` 하나로 줄이거나 assert를 지웁니다. (2) 주석을 `# rule 4b before rule 5`로 고칩니다.

### R-2 [minor] 코드 충돌 시 재시도와 RuntimeError 경로에 테스트가 없음
- 위치: `src/shortlink/links.py:49-62`
- 1라운드와 같은 지적입니다. 이번 변경분에는 관련 수정이 없습니다.

### R-3 [minor] 잘못된 IPv6 authority를 처리하는 `except ValueError` 분기에 테스트가 없고, 스킴 판정 로직이 중복됨
- 위치: `src/shortlink/validation.py` (except ValueError 블록, 4a가 추가되면서 줄 번호가 3줄 밀림)
- 1라운드와 같은 지적입니다. 이번 변경분에는 관련 수정이 없습니다.

### R-4 [minor] async 핸들러 안에서 동기 sqlite3 I/O를 실행함
- 위치: `src/shortlink/api.py:36`, `src/shortlink/web.py` (shorten_form, follow)
- 1라운드와 같은 지적입니다. 이번 변경분에는 관련 수정이 없습니다.

### R-5 [minor] TEMPLATES_DIR가 main.py와 web.py에 각각 정의되어 있음
- 위치: `src/shortlink/web.py:19`, `src/shortlink/main.py:24`
- 1라운드와 같은 지적입니다. 이번 변경분에는 관련 수정이 없습니다.

## 이전 지적 확인 (2라운드부터)
- R-1: 해결 — 근거는 아래와 같습니다.
  - 구현: `web.py:28`의 `location_header`가 `quote(url, safe=<0x21-0x7E 전체>)`를 쓰고, `web.py:63`이 `Response(status_code=302, headers={"location": ...})`로 응답합니다.
    - 출력 가능한 ASCII는 `%`까지 safe에 들어 있어 이미 있는 `%xx`도 그대로 나갑니다. 비ASCII는 UTF-8 `%XX`로 바뀝니다.
    - 공백과 제어 문자는 D-2에서 이미 거절되므로 헤더 값은 항상 ASCII입니다.
    - 짝 없는 서로게이트도 이제 D-8에서 거절되므로 `quote`(errors='strict')에서 인코딩 오류가 날 일이 없습니다.
  - 문서: D-3 개정 문구와 계획 3.5가 실제 동작과 맞습니다.
  - 테스트: `test_d3_printable_ascii_location_is_sent_verbatim`이 `| { } < > \ ^ \` "`, 이미 있는 `%xx`, 짝 없는 `%`를 다룹니다. `test_d3_only_non_ascii_characters_are_percent_encoded_in_location`은 한글, 이모지, ASCII와 `%xx`가 섞인 경우를 다루며 Location 값을 정확히 비교합니다. 1라운드에서 지적한 test_web.py의 잘못된 주석과 `unquote` 비교도 정확한 값 비교로 바뀌었습니다.
- R-2: 미해결(minor, 기록만)
- R-3: 미해결(minor, 기록만)
- R-4: 미해결(minor, 기록만)
- R-5: 미해결(minor, 기록만)

## 변경분 검토 메모 (S-1/D-8)
- `validation.py:37`의 4a 검사(U+D800–U+DFFF)는 길이 검사 다음, 공백·제어 문자 검사 앞에 있습니다. 계획서 3.2 표(4a/4b)와 D-8의 순서와 같습니다.
- 테스트도 충분합니다. 단위 테스트는 경계 코드 포인트 4개를 위치 3곳(앞, 중간, 끝)에 넣어 보고, 검사 순서와 정상 문자 U+1F600도 확인합니다. API 테스트는 JSON 이스케이프로 서로게이트를 보내 422가 나오는지, 아무것도 저장되지 않는지, 순서가 맞는지, 짝이 맞는 서로게이트 쌍은 201이 나오는지 확인합니다. 그 밖에 정확성 문제는 찾지 못했습니다.
- 참고(security 범위): D-3 개정으로 `\`도 Location에 그대로 나갑니다. 그래서 `https://example.com\@evil.com` 같은 값이 들어오면 Python `urlsplit`과 브라우저가 호스트를 다르게 해석합니다. 1라운드 참고 메모와 같은 내용이며, 코드 품질 리뷰의 심각도에는 반영하지 않았습니다.

관련 파일:
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\web.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\src\shortlink\validation.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_redirect.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_api_validation.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_validation.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_web.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\docs\plans\F1-decisions.md
