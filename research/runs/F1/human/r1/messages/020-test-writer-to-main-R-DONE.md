---
seq: 20
sender: "test-writer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T06:12:58.060Z"
agent: "test-writer"
agent_id: "ad099a69ee132ab3c"
turn: 2
reply_to: 18
chars: 3436
tokens_est: 1395
wait_s: null
---

## 결과: 완료
리뷰 1라운드의 테스트 3건(M-1/D-9, R-3, S-3/D-10)을 반영했습니다. `uv run ruff check tests`와 `uv run ruff format tests`는 통과했습니다. 지금 시점의 src/에서 `uv run python -m pytest`는 175개 전부 통과했습니다. 먼저 `uv run pytest`로 실행했더니 이 환경의 응용 프로그램 제어 정책이 `pytest.exe`를 막아서 실패했고, 그래서 `python -m pytest`로 돌렸습니다. src/는 건드리지 않았습니다.

## 변경 파일
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_validation.py
  - 짝 없는 서로게이트 거절(`MSG_INVALID_ENCODING`)과 규칙 7개 순서 테스트를 추가했습니다.
  - 규칙 번호 주석을 새 순서에 맞췄고, 문구 상수 테스트에 `MSG_INVALID_ENCODING`을 넣었습니다.
  - 서로게이트 문자는 `chr(0xD800)` 등으로 만듭니다. 소스에 리터럴로 쓰면 ruff PT014가 중복으로 오탐하기 때문입니다.
  - 작업 중 이 파일을 한 번 잘못 덮어써 비운 적이 있어서 전체를 다시 작성했습니다. 기존 테스트는 모두 되살렸습니다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_api_links.py
  - 원문 JSON으로 서로게이트를 보내는 테스트를 추가했습니다.
  - POST /links의 201과 422 응답에 nosniff가 있는지 확인하는 테스트를 추가했습니다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_redirect.py: 302 응답의 nosniff 테스트를 추가했습니다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_web.py: 네 화면의 CSP와 nosniff, `/docs`에 CSP가 없는지, `copy.js` 가드 문자열 테스트를 추가했습니다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_repository.py: 계속 충돌하는 경우의 호출 횟수를 `len(calls) == LinkRepository.MAX_ATTEMPTS`로 고정했습니다(R-3).
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\conftest.py: 이번 라운드 변경 없음(1차에 추가한 `count_links`만 있습니다).

## 수용 기준과 테스트 대응
AC-1~AC-23은 1차 보고와 같습니다. 이번에 추가된 항목입니다.
- D-9 검증 단위: `test_unpaired_surrogate_is_rejected` (high, low, last, two-high, middle, leading 6가지)
- D-9 규칙 순서:
  - `test_order_invalid_char_before_invalid_encoding` (공백 또는 줄바꿈과 서로게이트가 같이 있으면 `MSG_INVALID_CHAR`)
  - `test_order_invalid_encoding_before_scheme` (`ftp://e.com/<서로게이트>`는 `MSG_INVALID_ENCODING`)
  - `test_order_invalid_encoding_before_host`
  - `test_order_length_before_invalid_encoding`
  - `test_message_constants_match_the_plan` (`MSG_INVALID_ENCODING` 문구 확인)
  - `test_valid_url_is_returned_unchanged` (U+1F600 😀가 든 URL은 통과)
- D-9 API: `test_unpaired_surrogate_in_json_is_rejected_with_422`
  - `\ud800`, `\udc80`, `\udbff\u0041`을 원문 JSON으로 보냅니다.
  - 422와 `{"detail": MSG_INVALID_ENCODING}`, `count_links() == 0`을 확인합니다.
- D-9 대조군: `test_valid_surrogate_pair_in_json_is_accepted` (`\ud83d\ude00`은 201이고 url은 `https://e.com/😀`)
- R-3: `test_persistent_collision_raises_runtime_error_and_keeps_existing_row`
- D-10 HTML 화면: `test_html_screens_have_csp_and_nosniff` (홈, 결과, 입력 오류 422, 404)
  - `default-src 'self'`, `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`를 확인합니다.
- D-10 JSON 응답: `test_json_response_has_nosniff_header` (201과 422)
- D-10 302 응답: `test_redirect_response_has_nosniff_header`
- D-10 `/docs`: `test_docs_page_has_no_csp_so_swagger_ui_can_load_its_cdn_assets` (200이고 CSP 헤더 없음)
- D-11(선택): `test_copy_script_guards_missing_clipboard_api` (`/static/copy.js`가 200이고 본문에 `navigator.clipboard`가 있음)

## 설계서 해석이 필요했던 부분
- 계획 5절 D-9는 "짝 없는 서로게이트"라고 했습니다. 짝이 맞는 `\ud83d\ude00` 표기는 정상 문자이므로 201이어야 한다고 보고 대조군 테스트를 넣었습니다. `\udbff\u0041`처럼 high 뒤에 low가 오지 않는 경우는 짝 없음으로 봐서 422입니다.
- D-10은 CSP 값에 `base-uri 'none'`, `form-action 'self'`도 포함한다고 하지만, 지시하신 대로 `default-src 'self'`와 `frame-ancestors 'none'` 포함 여부만 검사합니다. 나머지 지시어가 바뀌어도 깨지지 않습니다.
- D-11은 `copy.js` 본문에 `navigator.clipboard` 문자열이 있는지만 확인합니다. 가드의 실제 동작은 pytest로 검증할 수 없습니다.

## 남은 문제와 질문
- 없음. 단, `copy.js`를 `navigator.clipboard`가 없을 때를 처리하는 쪽으로 고쳐도, 이 문자열 테스트로는 그 처리가 맞는지 확인되지 않습니다.
