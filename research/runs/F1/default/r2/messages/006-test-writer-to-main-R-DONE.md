---
seq: 6
sender: "test-writer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T02:20:38.149Z"
agent: "test-writer"
agent_id: "af5f645dbd4eb649c"
turn: 1
reply_to: 4
chars: 5740
tokens_est: 2035
wait_s: null
---

## 결과: 완료

`uv run ruff check tests`와 `ruff format --check tests`는 통과했고, `uv run pytest --collect-only -q`는 수집 오류 없이 224개를 수집했습니다. implementer 구현이 이미 들어와 있어 `uv run pytest -q`는 224개 모두 통과했습니다. `src/`는 수정하지 않았습니다.

## 변경 파일
- `tests/conftest.py`: 기존 `settings`, `app`, `client`는 그대로 두고 픽스처 `count_links`(sqlite3로 `links` 행 수 직접 조회)와 `insert_link`(코드를 지정해 직접 INSERT)를 추가했습니다. 둘 다 `app`에 의존해 스키마 준비를 보장합니다.
- `tests/html_helpers.py`: 표준 라이브러리 `html.parser` 기반 HTML 검사 헬퍼(`parse_html`, `find`, `find_all`, `text`)입니다. 공백·속성 순서·따옴표 스타일에 민감하지 않게 하려고 만들었습니다.
- `tests/test_api_links.py`: `POST /links`(AC-1~9, 13, 15)
- `tests/test_redirect.py`: 리다이렉트와 영속성(AC-10~12, 14)
- `tests/test_web.py`: 화면 4종과 폼(AC-16~23, 폼 경유 AC-9, AC-8, AC-12)
- `tests/test_validation.py`: `validate_url` 단위 테스트(문구, 검사 순서, 경계값)
- `tests/test_repository.py`: 저장소, 충돌 재시도, `init_db`, `format_timestamp`
- `tests/test_codes.py`: `generate_code`, `is_valid_code`, `build_short_url` 단위 테스트. 계획 5절에는 없는 추가 파일입니다.

## 수용 기준과 테스트 대응
- AC-1: `test_api_links.py::test_create_returns_201_with_all_fields`
- AC-2: `test_code_is_seven_alphanumeric_characters`, `test_short_url_is_base_url_plus_code`, `test_short_url_uses_configured_base_url_without_double_slash`
- AC-3: `test_response_url_is_identical_to_request` (9개 URL, 응답과 저장값 모두 확인)
- AC-4: `test_http_url_is_accepted`
- AC-5: `test_non_http_scheme_is_rejected` (네 스킴 외에 스킴 없음, `//host`, `file:` 포함)
- AC-6: `test_missing_or_non_string_url_is_rejected` (필드 없음, 숫자, null, 빈 문자열, bool, 리스트, 객체, 다른 필드명), `test_non_json_body_is_rejected`, `test_json_array_body_is_rejected`
- AC-7: `test_url_without_host_is_rejected`
- AC-8: `test_url_of_exactly_2048_characters_is_created`, `test_url_of_2049_characters_is_rejected`, `test_url_of_2047_characters_is_created`, `test_form_accepts_2048_characters_and_rejects_2049`, `test_validation.py`의 경계값 테스트(글자 수 기준 포함)
- AC-9: `test_rejected_requests_store_nothing`, `test_rejected_request_does_not_disturb_stored_links`, `test_successful_request_is_stored`, 거절 테스트마다 `count_links()` 확인, `test_web.py::test_invalid_form_input_stores_nothing`
- AC-10: `test_redirect.py::test_redirect_returns_302_with_original_url`, `test_redirect_for_2048_character_url`
- AC-11: `test_unknown_code_returns_404`, `test_path_that_cannot_be_a_code_returns_404`, `test_code_lookup_is_case_sensitive`, `test_unknown_code_is_not_created_by_lookup`
- AC-12: `test_same_url_twice_gives_different_codes_that_both_redirect`, `test_same_url_twice_is_stored_as_two_links`, `test_web.py::test_form_submitting_same_url_twice_gives_distinct_codes`
- AC-13: `test_api_links.py::test_hundred_consecutive_codes_are_distinct`
- AC-14: `test_code_survives_creating_the_app_again`, `test_creating_the_app_again_keeps_existing_links`, `test_new_app_can_create_and_old_app_can_resolve`, `test_repository.py::test_links_persist_across_repository_instances`
- AC-15: `test_created_at_is_utc_iso8601_close_to_request_time`
- AC-16: `test_web.py::test_home_is_html_200`, `test_home_has_post_form_to_root`, `test_home_input_has_label_and_lives_in_form`, `test_home_submit_button_says_shorten`, `test_home_shows_service_name_and_description`, `test_home_has_no_error_message`
- AC-17: `test_result_screen_shows_short_link_and_original_url`, `test_result_screen_has_heading`, `test_result_screen_stores_link_once`, `test_result_screen_labels_the_original_url`, `test_result_screen_keeps_url_unchanged`
- AC-18: `test_result_screen_has_copy_button`, `test_result_screen_has_link_back_home`
- AC-19: `test_invalid_form_input_shows_422_error_screen`, `test_invalid_form_input_is_kept_in_input_field`, `test_invalid_form_input_stores_nothing` (각각 8개 입력), `test_error_screen_is_the_home_form_again`, `test_missing_url_field_in_form_is_treated_as_empty`, `test_error_message_shows_only_first_failed_rule`
- AC-20: `test_result_screen_escapes_html_in_url`, `test_error_screen_escapes_html_in_url`, `test_error_screen_escapes_html_in_value_without_scheme`, `test_error_screen_value_cannot_break_out_of_attribute`, `test_result_screen_cannot_be_injected_through_url`
- AC-21: `test_unknown_code_shows_not_found_screen`, `test_not_found_screen_links_home`, `test_not_found_screen_for_non_code_path`
- AC-22: `test_every_screen_has_lang_ko_and_viewport` (홈, 결과, 입력 오류, 찾을 수 없음), `test_every_screen_declares_utf8_and_title_and_home_link`, `test_screen_titles_match_mockups`
- AC-23: `test_form_created_code_redirects_to_original_url`, `test_shortened_link_href_path_resolves`
- 보조(충돌 재시도): `test_repository.py::test_collision_is_retried_with_a_new_code`, `test_collision_never_overwrites_existing_link`, `test_success_on_the_last_allowed_attempt`, `test_gives_up_after_max_attempts`, `test_single_attempt_limit`, `test_retry_works_across_repository_instances`

## 설계서 해석이 필요했던 부분
- 설계서 "API 422 본문 형식 미지정": 계획 D-1에 따라 상태 코드 422만 확인하고 본문 형식은 검사하지 않았습니다.
- 계획 D-3(공백·제어 문자 거절), D-4(스킴 대소문자 무시), D-5(글자 수 기준 길이), D-7(비ASCII URL은 `Location`이 ASCII가 되고 `unquote`하면 원본과 같음), D-8(폼에 `url` 필드가 없으면 빈 문자열 취급), D-9(7자 영숫자가 아닌 경로는 404 화면): 계획 표대로 단위 테스트와 HTTP 테스트에 반영했습니다.
- AC-3 "글자 그대로": 응답의 `url`뿐 아니라 저장소에서 다시 읽은 값도 같은지 확인했습니다.
- AC-1 "네 필드를 돌려준다": 네 필드가 모두 있는지(상위집합)만 확인하고, 추가 필드가 없는지는 검사하지 않았습니다.
- AC-17 "원래 URL이 보인다": 화면 본문 텍스트에 원래 URL이 있는지만 확인합니다. 계획의 "텍스트, 링크 아님"은 단언하지 않았습니다.
- AC-19 "입력칸에 제출한 값이 남아 있다": 파싱한 `value` 속성이 제출 문자열과 글자 그대로 같은지 확인합니다. 앞 공백이 든 입력도 포함합니다.
- AC-20 "원문 `<script>` 태그가 그대로 나오지 않는다": 원문 문자열에 `<script>alert(1)`이 없고 `&lt;script&gt;`가 있는지, `alert`를 담은 `script` 요소가 없는지를 함께 확인합니다. 결과 화면은 유효한 URL로, 오류 화면은 `ftp://` 접두를 붙이거나 스킴 없는 값으로 검사합니다.
- `/static/style.css`가 200으로 제공되는지 확인하는 테스트 1개를 추가했습니다. 설계서 AC는 아니고 계획 2절(정적 파일 서빙, 마지막에 등록되는 `/{code}`가 가리지 않음)에 근거합니다.

## 남은 문제와 질문
- 없음. 실패하는 테스트는 없고, 계획 7절 해석 결정 외에 구현과 어긋난 지점도 없었습니다.
