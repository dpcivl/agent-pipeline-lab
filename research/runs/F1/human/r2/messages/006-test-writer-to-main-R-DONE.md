---
seq: 6
sender: "test-writer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T06:37:20.120Z"
agent: "test-writer"
agent_id: "ad935d2d159d0c840"
turn: 1
reply_to: 4
chars: 5193
tokens_est: 1925
wait_s: null
---

## 결과: 완료

`uv run ruff check tests`와 `uv run ruff format tests`는 모두 통과했습니다. `uv run pytest`는 이 환경에서 실행 파일이 보안 정책(os error 4551)에 막혀 `uv run python -m pytest -q`로 대신 돌렸고, 170개가 모두 통과했습니다. 작업 중에 다른 에이전트의 구현이 워크트리에 들어와 있어서, 스텁 상태가 아니라 실제 구현에 대해 돌린 결과입니다. 이 결과는 설계서·계획 기준으로 쓴 테스트가 현재 구현과도 일치한다는 뜻입니다. `src/`는 수정하지 않았고 `tests/conftest.py`도 건드리지 않았습니다.

## 변경 파일
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\tests\helpers.py`: 테스트 공용 도구입니다. `count_links(settings)`는 sqlite3로 `links` 행 수를 직접 셉니다. `Page`는 표준 `html.parser`로 요소와 속성을 찾아서, 속성 순서·공백·따옴표 스타일·`&#34;` 같은 이스케이프에 의존하지 않게 합니다. `short_link_from_result`는 결과 화면에서 단축 URL 링크와 코드를 뽑습니다.
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\tests\test_api_links.py`: AC-1~AC-9, AC-13, AC-15와 D-1, D-4의 API 쪽 테스트입니다.
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\tests\test_redirect.py`: AC-10~AC-12, AC-14와 D-6(Location)을 다룹니다. 리다이렉트는 모두 `follow_redirects=False`로 확인합니다.
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\tests\test_web.py`: AC-16~AC-23 화면 테스트입니다.
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\tests\test_validation.py`: `validate_url` 단위 테스트입니다. 규칙 표, 검사 순서, 경계값, D-1~D-4를 확인합니다.
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\tests\test_codes.py`: `generate_code` 단위 테스트입니다.

## 수용 기준과 테스트 대응
- AC-1: `test_create_returns_201_with_the_four_fields`
- AC-2: `test_code_is_seven_alphanumeric_characters`, `test_short_url_is_base_url_plus_code`, `test_short_url_uses_configured_base_url_without_double_slash`. 단위 테스트는 `test_codes.py`에 있습니다.
- AC-3: `test_response_url_is_the_request_url_verbatim`. 쿼리, 대소문자, 프래그먼트, 비ASCII, `<>"'`를 parametrize했습니다.
- AC-4: `test_http_url_is_accepted`
- AC-5: `test_non_http_scheme_is_rejected`. 네 가지 스킴을 parametrize했습니다.
- AC-6: `test_missing_non_string_or_empty_url_is_rejected`와 `test_body_that_is_not_a_json_object_is_rejected`. 필드 없음, null, 빈 문자열, 숫자, 불리언, 목록, 객체, JSON이 아닌 본문, JSON 배열을 확인합니다.
- AC-7: `test_url_without_host_is_rejected`
- AC-8: `test_url_of_2048_characters_is_created`, `test_url_of_2049_characters_is_rejected`, `test_length_limit_counts_characters_not_bytes`. 폼과 리다이렉트 쪽 경계값 테스트도 있습니다.
- AC-9: `test_rejected_request_stores_nothing`과 대조군 `test_rejection_leaves_earlier_links_untouched`. 폼 쪽은 AC-19 테스트에서 확인합니다.
- AC-10: `test_known_code_redirects_with_302_and_location`, `test_location_is_the_stored_url_verbatim_for_ascii`, `test_location_percent_encodes_only_non_ascii_characters`
- AC-11: `test_unknown_code_returns_404`, `test_unknown_code_returns_404_even_when_other_codes_exist`
- AC-12: `test_same_url_twice_gives_two_codes_that_both_redirect`. 폼 쪽은 `test_form_made_codes_are_distinct_for_the_same_url`입니다.
- AC-13: `test_hundred_consecutive_codes_are_all_different`
- AC-14: `test_code_still_redirects_after_app_is_recreated_with_same_db`. 같은 `settings`로 `create_app`을 다시 만들어 새 `TestClient`로 확인합니다.
- AC-15: `test_created_at_is_utc_iso_8601_close_to_request_time`
- AC-16: `test_home_is_html_with_form_label_input_and_submit_button`, `test_home_shows_service_name_and_tagline`, `test_home_has_no_error_message_and_empty_input`
- AC-17: `test_valid_form_submission_shows_short_url_link_and_original_url`, `test_form_submission_is_stored_in_the_database`, `test_form_keeps_the_url_verbatim_on_the_result_screen`
- AC-18: `test_result_page_has_copy_button_and_link_back_home`
- AC-19: `test_invalid_form_submission_shows_error_and_keeps_the_value`, `test_error_screen_still_has_the_form`, `test_each_invalid_value_gets_its_message_and_is_not_stored`, `test_missing_url_field_is_an_input_error_not_a_server_error`
- AC-20: `test_script_in_a_valid_url_is_escaped_on_the_result_screen`, `test_script_in_an_invalid_value_is_escaped_on_the_error_screen`, `test_quotes_and_tags_cannot_break_out_of_the_input_value`, `test_quotes_and_ampersands_in_a_valid_url_are_shown_as_typed`
- AC-21: `test_unknown_code_shows_html_not_found_screen`
- AC-22: `test_every_screen_has_lang_ko_and_viewport_meta`. 홈, 결과, 입력 오류, 찾을 수 없음 네 화면을 확인합니다.
- AC-23: `test_code_made_by_the_form_redirects_to_the_original_url`

## 설계서 해석이 필요했던 부분
- 설계서는 오류 본문 형식을 정하지 않습니다. 계획 3절·D-4의 `{"detail": "<MSG_*>"}`를 기준으로, API 오류 테스트는 `detail`이 `validation.MSG_*` 상수와 같은지 확인합니다. 단, JSON이 아닌 본문과 JSON 배열 본문은 422만 확인합니다.
- "오류 메시지가 보이고"(AC-19): 계획 4절에 따라 `<p id="url-error" role="alert">`의 텍스트가 `MSG_*`와 같은지, 입력칸에 `value`와 `aria-invalid="true"`가 있는지 확인합니다. 따라서 이 id와 role은 구현의 계약입니다.
- "원래 URL이 보인다"(AC-17): 엔티티를 해제한 페이지 텍스트에 원문이 들어 있는지로 확인합니다. 링크 글자도 단축 URL과 같아야 한다고 봤습니다. 이는 목업 기준입니다.
- 이스케이프(AC-20): 결과 화면은 `https://example.com/<script>alert(1)</script>`, 오류 화면은 `<script>alert(1)</script>`를 제출합니다. HTML에 `<script>`가 없고 `&lt;script&gt;`가 있는지, 그리고 `src` 없는 인라인 `<script>` 요소가 없는지 확인합니다. 결과 화면이 `copy.js`를 `<script src=...>`로 불러오는 것은 허용합니다.
- D-1, D-3, D-7(`type`이 `text`이고 `required` 없음), D-8(404가 항상 HTML)도 계획의 해석 그대로 테스트했습니다.
- 계획·CLAUDE.md의 확인 사항 중 AC가 아닌 것도 몇 개 추가했습니다. `GET /links`는 404(계획 2절), `/static/style.css`는 200과 홈의 stylesheet 링크, 소문자 `base_url` 끝 슬래시 제거입니다.

## 남은 문제와 질문
- 없음. 테스트가 `helpers.py`를 `from helpers import ...`로 가져옵니다. `tests/`에 `__init__.py`가 없는 pytest 기본 설정에서만 동작하고, ruff 기본 설정에서는 import 정렬 시 third-party로 분류됩니다.
