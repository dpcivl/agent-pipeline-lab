---
seq: 6
sender: "test-writer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T23:56:50.379Z"
agent: "test-writer"
agent_id: "af331b1f347ae9d90"
turn: 1
reply_to: 4
chars: 7122
tokens_est: 2331
wait_s: null
---

## 결과: 완료
F2 수용 기준 테스트 3개 파일과 conftest 확장을 작성했습니다. 작업 중 implementer의 src 변경이 이미 들어와서, 전체 `uv run python -m pytest`가 405 passed(F1 포함)입니다. 새 테스트 230개도 모두 통과했습니다. `uv run ruff check src tests`는 통과했고 `uv run ruff format tests`는 변경 없음입니다. `pytest --collect-only`로 확인한 수집 오류는 없습니다. git 커밋은 하지 않았고 src와 기존 F1 테스트 파일은 건드리지 않았습니다.

## 변경 파일
- `tests/test_aliases.py`: API 별칭 AC-1~9, validate_alias 단위, repository AliasTakenError. 135개
- `tests/test_stats.py`: 통계 API와 클릭 AC-12~16, AC-20, F1 스키마 마이그레이션, record_click. 35개
- `tests/test_web_f2.py`: 화면 AC-10, 11, 17~19, 21, 22 (HTML 파싱, 목업 문구 기준). 60개
- `tests/conftest.py`: 확장만 했습니다. 픽스처 `link_row(code)`(DB에서 한 행을 dict로 읽음)와 `set_clicks(code, n)`(DB의 clicks를 직접 씀)을 추가했습니다. `settings`, `app`, `client`, `count_links`는 그대로입니다.

## 수용 기준과 테스트 대응
- AC-1: `test_valid_alias_creates_link_with_alias_as_code`, `test_assorted_valid_aliases_are_used_as_given`, `test_alias_is_stored_exactly_as_given` (test_aliases)
- AC-2: `test_alias_redirects_to_original_url`, `test_aliases_of_any_valid_shape_redirect`, `test_unknown_alias_shaped_path_is_still_404`
- AC-3: `test_missing_alias_field_makes_seven_char_code`, `test_null_alias_makes_seven_char_code`
- AC-4: `test_alias_length_boundaries` (3, 4, 30, 31자), `test_empty_alias_string_is_a_length_error`, `test_length_is_counted_in_characters_not_bytes`
- AC-5: `test_alias_with_bad_characters_or_edge_hyphen_is_422`(17개 parametrize: 공백, `_`, `/`, `.`, 4자 한글, 전각, 개행, 하이픈 시작·끝 등), `test_alias_error_body_is_detail_with_the_rule_message`, `test_non_string_alias_is_422`
- AC-6: `test_reserved_alias_is_422`(9개), `test_reserved_alias_in_other_case_is_422`, `test_reserved_word_inside_a_longer_alias_is_allowed`
- AC-7: `test_duplicate_alias_is_409_and_first_link_still_redirects`, `test_duplicate_alias_with_the_same_url_is_still_409`, `test_alias_equal_to_an_existing_random_code_is_409`
- AC-8: `test_alias_is_case_sensitive`, `test_same_case_alias_is_still_a_duplicate`
- AC-9: `test_rejected_alias_stores_nothing`, `test_conflict_stores_nothing`, `test_invalid_url_with_valid_alias_stores_nothing_and_frees_the_alias`, `test_invalid_url_is_reported_before_invalid_alias`, `test_invalid_alias_is_reported_before_conflict_check`
- AC-10: `test_home_form_has_labeled_alias_input`, `test_home_alias_input_follows_the_mockup`, `test_form_with_alias_shows_result_with_alias_short_url`, `test_form_alias_creates_a_working_redirect`, `test_form_without_alias_makes_a_random_seven_char_code`, `test_form_alias_of_only_a_space_is_a_rule_violation` (test_web_f2)
- AC-11: `test_invalid_alias_shows_422_page_with_message_and_kept_values`(10개), `test_duplicate_alias_shows_409_page_with_message_and_kept_values`, `test_invalid_alias_marks_only_the_alias_input_as_invalid`, 목업 문구 테스트 2개, `test_invalid_url_with_alias_keeps_both_values_and_marks_url`, `test_invalid_url_and_invalid_alias_show_only_the_url_message`, `test_alias_error_page_escapes_and_keeps_the_value_inside_the_attribute`
- AC-12: `test_new_link_has_zero_clicks_and_null_last_access`, `test_new_alias_link_has_stats_under_the_alias` (test_stats)
- AC-13: `test_three_redirects_make_three_clicks_and_set_last_access`, `test_each_redirect_adds_exactly_one_click`, `test_alias_redirects_are_counted_under_the_alias`, `test_clicks_are_counted_per_link`, `test_clicks_and_last_access_are_stored_in_the_database`
- AC-14: `test_reading_stats_api_does_not_change_clicks`, `test_reading_stats_api_of_a_new_link_keeps_zero_and_null`, `test_reading_stats_screen_does_not_change_clicks`
- AC-15: `test_unknown_code_does_not_change_any_click_count`, `test_unknown_code_creates_no_row_and_no_stats`, `test_case_variant_of_alias_is_a_miss_and_counts_nothing`
- AC-16: `test_stats_for_unknown_code_is_404_json`, `test_stats_lookup_is_case_sensitive`
- AC-17: `test_stats_screen_for_new_link_shows_zero_clicks_and_no_access_yet`, `test_stats_screen_shows_the_clicks_and_last_access_after_visits`, `test_stats_screen_lists_the_four_items_from_the_mockup`, `test_stats_screen_without_access_has_no_time_element_for_last_access`, `test_stats_screen_formats_clicks_with_thousands_separator`(5개), `test_stats_screen_has_link_back_to_the_home_form`, `test_stats_screen_works_for_f1_style_random_code`
- AC-18: `test_stats_screen_for_unknown_code_is_404_page`, `test_stats_404_page_is_the_same_screen_as_the_f1_not_found_page`, `test_stats_screen_lookup_is_case_sensitive`, `test_stats_screen_for_unknown_code_creates_nothing`
- AC-19: `test_result_page_has_stats_link_for_random_code`, `test_result_page_has_stats_link_for_alias`, `test_result_stats_link_leads_to_a_working_stats_screen`, `test_result_page_keeps_f1_links`
- AC-20: `test_clicks_survive_a_new_app_on_the_same_database`, `test_alias_survives_a_new_app_on_the_same_database`, `test_init_schema_is_safe_to_call_repeatedly_and_keeps_clicks`
- AC-21: `test_stats_screen_escapes_html_in_the_original_url`, `test_stats_screen_escapes_quotes_and_ampersands_in_the_url`
- AC-22: `test_stats_screens_have_lang_ko_and_viewport_meta`(통계, 통계 404), `test_error_pages_have_lang_ko_and_viewport`(422, 409 홈 화면). 보안 헤더 `test_stats_screens_have_csp_and_nosniff`와 `test_stats_screen_links_the_shared_stylesheet`는 추가로 넣었습니다.
- AC-23: 기존 F1 테스트를 수정하지 않고 같은 실행에 포함했습니다. 전체 405개가 통과했습니다.
- 보조 테스트
  - validate_alias 단위: `test_validate_alias_returns_valid_input_unchanged`, `..._rejects_with_the_rule_message`, `..._checks_rules_in_documented_order`, `test_alias_constants_match_the_design`. `"abcd\n"`을 거절하는 케이스도 포함합니다.
  - F1 스키마 마이그레이션: `test_f1_database_keeps_working_and_counts_from_zero`, `..._accepts_new_links_and_aliases`, `..._survives_repeated_startup`, `..._gets_the_new_columns`, `test_new_database_has_the_new_columns` (test_stats)
  - repository AliasTakenError: `test_create_with_alias_*`, `test_create_with_taken_alias_raises_and_keeps_the_existing_row`, `test_alias_equal_to_existing_random_code_raises_alias_taken` (test_aliases)
  - repository record_click: `test_record_click_*`, `test_get_does_not_count_a_click`, `test_record_click_is_atomic_under_parallel_calls` (test_stats)

## 설계서 해석이 필요했던 부분
- 설계서에는 따로 해석할 문장이 없었고, 아래는 모두 계획서의 결정 D-F2-1~9를 그대로 따랐습니다.
  - D-F2-1: 폼에서 빈 `alias=`와 필드 생략은 별칭 없음입니다.
  - D-F2-2: API에서 `""`는 길이 규칙 위반 422입니다.
  - D-F2-3: 별칭은 대소문자를 그대로 씁니다.
  - D-F2-4: 예약어는 대소문자를 무시하고 비교합니다.
  - D-F2-5: URL 검증을 별칭 검증보다 먼저 합니다.
  - D-F2-6: 통계 API 404는 JSON입니다.
  - D-F2-7: 통계 화면 시각은 `YYYY-MM-DD HH:MM:SS UTC`이고 `<time datetime>`으로 감쌉니다.
  - D-F2-8: 클릭 수는 SQL `clicks = clicks + 1` 한 문장으로 원자적 증가합니다.
  - D-F2-9: 통계 화면의 단축 URL을 눌러 이동하면 그 클릭도 셉니다.
- 계획 3.1의 검사 순서 때문에 `openapi.json`은 문자 규칙(`MSG_ALIAS_CHARS`)에서, `api`는 길이 규칙(`MSG_ALIAS_LENGTH`)에서 먼저 걸립니다. 단위 테스트는 이 문구를 그대로 확인하고, 예약어 9개의 API 테스트는 422만 확인합니다.

## 남은 문제와 질문
- 없음
- 참고 1: 통계 화면 테스트는 목업의 마크업에 의존합니다. 클래스 `click-count`와 `result-label`, `<dl>`의 `dt` 라벨 4개("단축 URL", "원래 URL", "생성 시각", "마지막 접근"), `<time datetime>`입니다. 구현이 목업에서 벗어나면 이 테스트들이 실패합니다.
- 참고 2: 동시성 검증은 `record_click`을 스레드 6개로 30번 호출하는 repository 테스트로만 했습니다. 공유 TestClient를 스레드에서 쓰는 HTTP 동시성 테스트는 불안정할 수 있어서 넣지 않았습니다.
- 참고 3: Write 도구가 새 파일을 CRLF로 저장했고 ruff format은 이를 그대로 둡니다. 기존 파일의 줄바꿈과 다르면 필요할 때 통일해 주세요.
