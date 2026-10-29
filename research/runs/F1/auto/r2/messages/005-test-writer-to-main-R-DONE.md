---
seq: 5
sender: "test-writer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T05:13:28.487Z"
agent: "test-writer"
agent_id: "ac6963e1736f78e26"
turn: 1
reply_to: 3
chars: 5146
tokens_est: 1748
wait_s: null
---

## 결과: 완료

AC-1~AC-23과 D-1~D-5에 대응하는 테스트를 모두 작성했습니다. 작성 중 implementer의 구현이 이미 `src/`에 들어와 있어서 `uv run pytest`를 돌렸고 89개가 모두 통과했습니다. `uv run ruff check tests`는 통과했고 `uv run ruff format tests`도 실행했습니다. 구현을 보고 테스트를 맞추지는 않았고, 설계서와 계획서 기준으로 썼습니다.

## 변경 파일
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\tests\conftest.py: `count_links` 픽스처만 추가했습니다. `settings.db_path`의 `links` 테이블 행 수를 sqlite3로 직접 셉니다. 기존 `settings`, `app`, `client`는 그대로입니다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\tests\test_api.py: AC-1~AC-15와 D-1~D-4 테스트입니다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\tests\test_web.py: AC-16~AC-23과 D-5, D-7 테스트입니다. `html.parser` 기반의 작은 헬퍼로 공백과 속성 순서에 영향받지 않게 확인합니다.

## 수용 기준과 테스트 대응
- AC-1: `test_ac1_create_returns_201_with_four_fields`
- AC-2: `test_ac2_code_is_seven_alphanumeric_chars_and_short_url_uses_base_url`, `test_ac2_short_url_follows_configured_base_url`
- AC-3: `test_ac3_response_url_is_exactly_the_request_url` (쿼리, 대소문자 섞인 URL, 비ASCII, `%20`을 parametrize)
- AC-4: `test_ac4_http_url_is_accepted`
- AC-5: `test_ac5_non_http_scheme_is_rejected` (4개 URL parametrize, 오류 문구 확인)
- AC-6: `test_ac6_missing_non_string_or_empty_url_is_rejected` (`{}`, 다른 키, null, 빈 문자열, 숫자, 리스트), `test_d4_broken_or_non_object_json_body_is_422`
- AC-7: `test_ac7_url_without_host_is_rejected`
- AC-8: `test_ac8_url_of_exactly_2048_chars_is_accepted`, `test_ac8_url_of_2049_chars_is_rejected`
- AC-9: AC-5~AC-8과 D-2 각 거절 테스트 안에서 `count_links() == 0`을 확인합니다. 추가로 `test_ac9_all_rejected_requests_leave_nothing_stored`, `test_ac9_rejection_does_not_disturb_later_creation`이 있습니다.
- AC-10: `test_ac10_get_code_redirects_to_original_url`, `test_ac10_redirect_keeps_ascii_characters_exactly` (모두 `follow_redirects=False`)
- AC-11: `test_ac11_unknown_code_returns_404`, `test_ac11_unknown_code_is_404_even_after_other_links_exist`
- AC-12: `test_ac12_same_url_twice_gives_different_codes_that_both_redirect`, `test_ac12_duplicate_urls_are_not_merged_in_storage`
- AC-13: `test_ac13_hundred_consecutive_codes_are_all_distinct`
- AC-14: `test_ac14_code_still_redirects_after_app_is_recreated_with_same_db`, `test_ac14_recreating_the_app_does_not_wipe_existing_links`
- AC-15: `test_ac15_created_at_is_utc_iso8601_and_close_to_request_time`
- AC-16: `test_ac16_home_is_html_with_form_label_input_and_submit_button`, `test_ac16_home_shows_service_name_description_and_empty_input`
- AC-17: `test_ac17_valid_submission_shows_short_url_link_and_original_url`, `test_ac17_result_screen_uses_fixed_wording`, `test_ac17_form_submission_is_stored`
- AC-18: `test_ac18_result_screen_has_copy_button_and_link_back_home`, `test_ac18_short_url_link_is_visible_without_javascript`
- AC-19: `test_ac19_invalid_url_shows_422_error_and_keeps_input_value` (6가지 오류 유형), `test_ac19_empty_or_missing_url_field_shows_required_message`, `test_ac19_error_message_is_announced_and_linked_to_the_input`, `test_ac19_valid_submission_after_error_works`
- AC-20: `test_ac20_result_screen_escapes_html_special_characters`, `test_ac20_error_screen_escapes_html_special_characters`, `test_ac20_double_quotes_cannot_break_out_of_attributes`
- AC-21: `test_ac21_unknown_code_shows_404_html_with_message_and_home_link`
- AC-22: `test_ac22_home_has_lang_and_viewport`, `test_ac22_result_has_lang_and_viewport`, `test_ac22_error_has_lang_and_viewport`, `test_ac22_not_found_has_lang_and_viewport`, `test_ac22_every_screen_links_the_stylesheet_and_brand_home_link`
- AC-23: `test_ac23_code_from_form_result_redirects_to_original_url`, `test_ac23_form_and_api_share_the_same_store`
- D-1: `test_d1_uppercase_scheme_is_accepted_and_kept_as_is`
- D-2: `test_d2_whitespace_or_control_characters_are_rejected` (앞뒤 공백, 탭, 줄바꿈, CRLF, NUL, DEL, NBSP 등)
- D-3: `test_d3_redirect_percent_encodes_only_non_ascii_characters`, `test_d3_redirect_keeps_existing_percent_escapes_while_encoding_non_ascii`, `test_ac10_redirect_keeps_ascii_characters_exactly`, `test_ac23_form_link_with_non_ascii_url_redirects_with_percent_encoding`
- D-4: `test_d4_broken_or_non_object_json_body_is_422`, 그리고 AC-5~AC-8의 `{"detail": <문구>}` 비교
- D-5: `test_d5_any_unknown_path_is_the_same_404_html_screen`, `test_d5_not_found_is_html_even_for_json_clients`
- D-7: `test_d7_input_is_plain_text_without_browser_validation`

## 설계서 해석이 필요했던 부분
- AC-17 "원래 URL이 보인다": 원래 URL이 링크인지는 검사하지 않았습니다. 파싱한 문서 텍스트에 URL이 들어 있는지만 봅니다(계획서의 `<p class="original-url">` 마크업은 고정하지 않았습니다).
- AC-18 "복사 버튼": 텍스트가 `복사`인 `<button>`이 정확히 하나이고, `data-copy`가 단축 URL인지까지 확인합니다. `data-copy`는 계획서 4장의 마크업 요점에서 가져왔습니다.
- AC-19의 접근성 속성(`p role="alert"`, 입력칸 `aria-invalid="true"`와 `aria-describedby`): 설계서가 아니라 계획서 4장과 목업 기준입니다. `test_ac19_error_message_is_announced_and_linked_to_the_input` 한 곳에만 모아 두었습니다. 이 마크업이 바뀌면 이 테스트만 고치면 됩니다.
- 추가한 테스트 중 수용 기준이 아니라 계획서에서 온 것들입니다. 각 파일 맨 아래의 `/static/style.css` 서빙 확인과 `/links`가 web 라우터에 가려지지 않는지 확인(계획서 2장 라우터 순서), 모든 화면의 스타일시트 링크와 브랜드 링크(계획서 4장), D-7(입력칸 `type="text"`, `required` 없음)입니다.
- AC-15 시각 비교: `created_at`이 초 단위로 잘리므로 "요청 전후 ±60초 이내"로 확인합니다.

## 남은 문제와 질문
- 없음. 다만 AC-22 중 "폭 375px에서 가로 스크롤 없음"은 HTML 응답만으로 검증할 수 없어 테스트하지 않았습니다(AC 번호가 있는 항목은 `lang`과 viewport까지입니다).
