---
seq: 17
sender: "test-writer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T04:51:37.648Z"
agent: "test-writer"
agent_id: "a3c9dd2bf4b0cc4ad"
turn: 2
reply_to: 15
chars: 2967
tokens_est: 1268
wait_s: null
---

## 결과: 완료

리뷰 1라운드에서 바뀐 D-3(개정)과 D-8에 맞춰 tests/를 보강했다. `uv run ruff check tests`와 `uv run ruff format tests`는 통과했고, `uv run pytest -q`는 253개가 모두 통과했다(implementer가 src를 이미 고친 상태). src는 건드리지 않았고 커밋도 하지 않았다.

## 변경 파일
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\support.py: `MSG_SURROGATE = "URL에 쓸 수 없는 문자가 들어 있습니다."` 상수를 추가했다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_redirect.py: 기존 D-3 테스트(퍼센트 인코딩을 `unquote`로 풀어 비교하던 것)를 개정 규칙의 정확한 값 비교 테스트 2개로 바꿨다. `unquote` import도 지웠다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_web.py: `test_ac20_script_url_is_stored_verbatim_and_redirects`가 `Location == SCRIPT_URL`을 정확히 비교하도록 고쳤다. 사실과 다른 주석도 "printable ASCII such as < and > is sent verbatim"으로 고쳤고, 쓰지 않게 된 `unquote` import를 지웠다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_api_validation.py: D-8 API 테스트를 추가했다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_validation.py: D-8 단위 테스트를 추가했고, 검사 순서 표에 4a 관련 항목을 넣었다.

## 수용 기준과 테스트 대응
- AC-10 / D-3(개정) 출력 가능한 ASCII는 글자 그대로: `test_d3_printable_ascii_location_is_sent_verbatim`
  - 7개 입력: `?a=1|2&b={x}`, `<script>alert(1)</script>`, `` \ ^ ` " | { } < > `` 를 모두 섞은 값, 따옴표·대괄호, `%20`, `%ED%95%9C`, 잘못된 `%zz%`
  - 모두 `Location == 요청값`을 확인한다.
- AC-10 / D-3(개정) 비ASCII만 UTF-8 퍼센트 인코딩: `test_d3_only_non_ascii_characters_are_percent_encoded_in_location`
  - 한글 경로+쿼리는 `/%ED%95%9C%EA%B8%80?q=%EA%B0%92`, `가`는 `%EA%B0%80`, 이모지는 `%F0%9F%98%80`로 나가는지 본다.
  - `a%20b/한|{x}<y>`처럼 이미 인코딩된 부분과 ASCII 특수문자가 섞인 값은 한글만 인코딩되는지 본다.
  - 응답의 `url` 필드가 요청값 그대로인지, Location이 ASCII인지도 확인한다.
- AC-20 + D-3: `test_ac20_script_url_is_stored_verbatim_and_redirects`: 폼으로 만든 `<script>` URL의 Location이 글자 그대로다.
- D-8 API: `test_d8_unpaired_surrogate_is_rejected_with_422_and_stores_nothing`
  - 6개 입력: `\ud800`, `\udbff`, `\udc00`, `\udfff`, `\ud83d`, `\ude00\ud83d`.
  - JSON 원문(`content=`)을 직접 보내고, 본문이 ASCII이고 백슬래시-u 이스케이프를 담는지 확인한다.
  - 응답은 422 `{"detail": "URL에 쓸 수 없는 문자가 들어 있습니다."}`이고 `links` 행 수는 0이다.
- D-8 순서(API): `test_d8_surrogate_is_reported_before_space_and_scheme_problems`: `\ud800 x`와 `ftp://...\ud800`은 둘 다 서로게이트 문구가 나온다.
- D-8 정상 쌍: `test_d8_valid_surrogate_pair_in_json_is_a_normal_character`: JSON의 `\ud83d\ude00` 쌍은 정상 문자(U+1F600)로 해석되어 201이다.
- D-8 단위: `test_d8_unpaired_surrogate_is_rejected`(경계 4개 × 앞/중간/뒤), `test_d8_review_example_is_rejected`(`"https://a.com/" + U+D800`), `test_d8_astral_character_is_not_a_surrogate`
- 검사 순서(길이 > 서로게이트 > 공백·제어 문자 > 스킴): `test_checks_run_in_the_documented_order`
  - 길이 2049자+서로게이트는 길이 문구가 나온다.
  - 서로게이트+공백, 서로게이트+개행은 서로게이트 문구가 나온다.
  - `ftp://`+서로게이트는 서로게이트 문구가 나온다.

## 설계서 해석이 필요했던 부분
- 지시문은 D-8을 "짝 없는" 서로게이트로 설명한다. 그래서 JSON에서 `\ud83d\ude00`처럼 짝이 맞는 이스케이프는 정상 문자로 받아들이는 테스트를 하나 더 넣었다. 구현이 짝이 맞는 경우까지 거절하면 이 테스트가 실패한다.
- 소스 안에서는 서로게이트를 `chr(0xD800)`으로 만들었다. 이스케이프 시퀀스 해석이 도구 단계에서 달라지는 문제를 피하려는 것이다. API 테스트는 raw 문자열로 백슬래시-u 이스케이프를 JSON 원문에 넣는다.

## 남은 문제와 질문
- 없음.
