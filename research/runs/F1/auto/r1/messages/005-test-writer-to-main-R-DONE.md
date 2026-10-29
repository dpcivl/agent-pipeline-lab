---
seq: 5
sender: "test-writer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T04:44:52.677Z"
agent: "test-writer"
agent_id: "a3c9dd2bf4b0cc4ad"
turn: 1
reply_to: 3
chars: 6513
tokens_est: 2119
wait_s: null
---

## 결과: 완료

F1 테스트 216개를 작성했고 `uv run ruff check tests`와 `uv run ruff format tests`는 통과했다. `uv run pytest --collect-only -q`로 수집 오류가 없는 것도 확인했다. 작성 중 implementer가 src를 구현해서, 마지막에 `uv run pytest -q`를 돌렸더니 216개가 모두 통과했다. src는 건드리지 않았고 커밋도 하지 않았다.

## 변경 파일
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\conftest.py: `settings`, `app`, `client`는 그대로 두고 `link_count` 픽스처만 추가했다. `settings.db_path`의 `links` 행 수를 sqlite3로 센다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\support.py: 오류 문구 상수, `make_url(length)`, `create_via_api`, `html.parser` 기반 `Page`를 모아 둔 헬퍼 모듈. 새 의존성은 없다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_api_create.py: 생성 성공 경로 테스트.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_api_validation.py: API 거절 경로, 저장 없음, D-1, D-2 테스트.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_redirect.py: 302/404와 D-3, D-5 테스트.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_persistence.py: 앱 재생성 후 리다이렉트와 스키마 준비 테스트.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_validation.py: `validate_url` 단위 테스트. 경계값, 검사 순서, 대소문자 스킴, 공백·제어 문자를 다룬다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r1\tests\test_web.py: 화면 테스트(AC-16~AC-23, D-6, D-7).

## 수용 기준과 테스트 대응
테스트 이름에 AC 번호가 들어 있다(`test_acN_*`).
- AC-1: `test_ac1_create_returns_201_with_all_fields`
- AC-2: `test_ac2_code_is_seven_alphanumeric_characters`, `test_ac2_short_url_is_base_url_slash_code`, `test_ac2_short_url_uses_configured_base_url_without_double_slash`
- AC-3: `test_ac3_response_url_is_exactly_the_requested_url`(8개 변형), `test_ac3_stored_url_is_not_normalized`
- AC-4: `test_ac4_http_url_is_created`
- AC-5: `test_ac5_non_http_scheme_is_rejected`(ftp/javascript/data/mailto), `test_ac5_url_without_scheme_is_rejected`, 단위 테스트 `test_ac5_*`
- AC-6: `test_ac6_missing_url_field_is_rejected`, `test_ac6_null_url_is_rejected`, `test_ac6_empty_string_is_rejected`, `test_ac6_non_string_url_is_rejected`, `test_ac6_body_that_is_not_a_json_object_is_rejected`
- AC-7: `test_ac7_url_without_host_is_rejected`, 단위 테스트 `test_ac7_no_host_gives_host_message`
- AC-8: `test_ac8_url_of_exactly_2048_characters_is_created`, `test_ac8_url_of_2049_characters_is_rejected`, `test_ac8_http_url_of_2049_characters_is_rejected`, 단위 테스트 `test_ac8_length_boundary_*`
- AC-9: `test_ac9_rejected_request_stores_nothing`(12개 본문), `test_ac9_rejections_do_not_disturb_existing_rows`
- AC-10: `test_ac10_known_code_redirects_with_302_and_location`, `test_ac10_following_the_redirect_goes_to_the_original_url`
- AC-11: `test_ac11_unknown_code_returns_404`, `test_d5_unknown_codes_of_any_shape_return_404_html`, `test_ac11_code_created_in_another_database_is_unknown`
- AC-12: `test_ac12_same_url_twice_gives_different_codes_and_both_redirect`
- AC-13: `test_ac13_hundred_consecutive_codes_are_all_distinct`
- AC-14: `test_ac14_code_still_redirects_after_app_is_recreated`, `test_ac14_all_links_survive_and_new_ones_can_be_added`, `test_ac14_link_created_through_the_form_survives_app_recreation`
- AC-15: `test_ac15_created_at_is_utc_iso8601_within_a_minute_of_request`
- AC-16: `test_ac16_home_returns_200_html_with_title_and_description`, `test_ac16_home_form_posts_to_root`, `test_ac16_home_url_input_has_a_label`, `test_ac16_home_has_submit_button_labelled_jurigi`, `test_ac16_home_input_is_empty_and_has_no_error`
- AC-17: `test_ac17_valid_submission_shows_result_with_short_url_link_and_original`, `test_ac17_result_screen_does_not_show_an_error`, `test_ac17_submission_is_stored_once`
- AC-18: `test_ac18_result_has_copy_button_for_the_short_url`, `test_ac18_result_has_link_back_home`
- AC-19: `test_ac19_invalid_submission_shows_422_with_message`, `test_ac19_invalid_submission_keeps_the_value_in_the_input`, `test_ac19_invalid_submission_stores_nothing`(각각 7개 입력 값), `test_ac19_error_screen_is_the_home_screen_with_form`
- AC-20: `test_ac20_result_screen_escapes_html_in_the_url`, `test_ac20_error_screen_escapes_html_in_the_submitted_value`, `test_ac20_quotes_cannot_break_out_of_the_input_attribute`, `test_ac20_quotes_in_a_valid_url_cannot_inject_attributes_on_the_result_screen`, `test_ac20_script_url_is_stored_verbatim_and_redirects`
- AC-21: `test_ac21_unknown_code_shows_404_html_with_notice_and_home_link`
- AC-22: `test_ac22_every_screen_declares_lang_ko_and_viewport`, `test_ac22_every_screen_links_the_stylesheet_and_it_is_served`(홈, 결과, 오류, 404 네 화면)
- AC-23: `test_ac23_code_made_through_the_form_redirects_to_the_original_url`, `test_ac23_form_and_api_share_one_store`, `test_ac23_form_follows_api_rules_for_http_and_uppercase_scheme`
- D-1: `test_d1_uppercase_scheme_is_accepted_and_kept_as_is`, 단위 테스트 `test_d1_scheme_check_ignores_case`
- D-2: `test_d2_space_and_control_characters_are_rejected`, 단위 테스트 `test_d2_space_or_control_character_is_rejected`
- D-3: `test_d3_non_ascii_url_redirects_with_percent_encoded_location`
- D-6: `test_d6_url_input_is_plain_text_without_required`
- D-7: `test_d7_missing_url_field_gives_html_422_not_json`, `test_d7_form_with_only_unrelated_fields_gives_html_422`
- 계획 3.1~3.4 (구현 계획 문서 기준): `test_create_app_prepares_links_table_without_any_request`, `test_create_app_twice_on_same_db_is_safe_and_keeps_rows`, `test_stored_row_matches_the_api_response`, `test_checks_run_in_the_documented_order`, `test_catch_all_code_route_does_not_shadow_other_routes`

## 설계서 해석이 필요했던 부분
- AC-3 "글자 그대로": 응답 JSON의 `url`과 DB에 저장된 값이 요청 문자열과 같은지로 확인했다. 리다이렉트 `Location`은 D-3에 따라 ASCII URL은 그대로, 비ASCII나 `<`처럼 헤더에 그대로 못 넣는 문자는 퍼센트 인코딩을 풀어서 비교했다.
- AC-15 "1분 이상 차이 나지 않는다": 요청 직전과 직후의 `datetime.now(UTC)`에서 각각 60초를 넘지 않는지 확인했다.
- AC-6 "문자열이 아니거나": 숫자 외에 bool, 리스트, 객체, `null`도 422로 보고 테스트했다. `null`은 "없음"으로 보고 문구는 계획 3.2를 따랐다.
- AC-7 "호스트가 없음": `https://` 외에 `http:///path`, `https://:8080/x`, `https://?q=1`도 넣었다. 계획 3.2가 `hostname`이 비어 있는지로 판단하라고 해서 같은 규칙으로 봤다.
- AC-20 "원문 `<script>` 태그가 그대로 나오지 않는다": 구현이 `<script src="/static/copy.js">`를 쓸 수 있어서 `<script>`라는 글자 자체를 막지 않았다. 대신 응답에 `<script>alert(1)</script>` 원문이 없고 `&lt;script&gt;alert(1)&lt;/script&gt;`가 있는지, 파싱한 결과에 페이로드를 실행하는 script 요소나 `on*` 속성이 없는지 확인했다.
- AC-22 viewport: 계획 3.6에는 정확한 문자열이 있다. 공백 같은 사소한 차이로 깨지지 않게 `width=device-width`와 `initial-scale=1`을 정규식으로 확인했다.

## 남은 문제와 질문
- 없음. 다만 `test_ac22_every_screen_links_the_stylesheet_and_it_is_served`와 `test_catch_all_code_route_does_not_shadow_other_routes`는 설계서 AC가 아니라 계획 3.6과 2절의 고정 요소(`/static/style.css` 링크와 서빙, 라우트 순서)에 근거한다. 계획이 바뀌면 이 두 테스트가 먼저 영향을 받는다.
