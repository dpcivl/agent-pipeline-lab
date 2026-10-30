---
seq: 6
sender: "test-writer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-30T00:44:13.076Z"
agent: "test-writer"
agent_id: "a8b445add493b81db"
turn: 1
reply_to: 4
chars: 7378
tokens_est: 2526
wait_s: null
---

## 결과: 완료
`uv run ruff check tests`와 `uv run ruff format tests`는 통과했다. `uv run pytest`는 현재 src(implementer 작업분)에서 393개 전부 통과했다. 새로 쓴 F2 테스트와 기존 F1 테스트가 함께 통과하므로 AC-23 회귀 확인은 충족한다. 커밋은 하지 않았다.

## 변경 파일
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\tests\html_helpers.py`: 새 파일. 화면 테스트용 HTML 파서 `Page`, `get_page`, `assert_html`. `test_web.py`의 `Page`와 같은 방식이고 `find_class`와 `index_of`를 더했다. `test_web.py`는 건드리지 않았다.
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\tests\test_aliases.py`: 새 파일. 별칭 API 테스트.
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\tests\test_stats.py`: 새 파일. 클릭 수 세기와 통계 API 테스트.
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\tests\test_web_f2.py`: 새 파일. F2 화면 테스트.
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\tests\test_migration.py`: 새 파일. F1 스키마(열 3개) DB 파일로 `create_app`을 시작하는 테스트. sqlite 연결은 항상 `closing`으로 닫는다.
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\tests\test_validation.py`: `validate_alias` 단위 테스트를 추가했다.
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r2\tests\test_repository.py`: `create(alias)`, `AliasTakenError`, `record_click` 테스트를 추가했다.
- `tests/conftest.py`는 수정하지 않았다. 기존 `count_links`만으로 충분했다.

## 수용 기준과 테스트 대응
- AC-1: `test_aliases.py::test_valid_alias_creates_link_with_alias_as_code_and_short_url`
- AC-2: `test_alias_redirects_with_302_to_original_url`, `test_aliases_of_any_valid_length_redirect_not_only_7_chars`
- AC-3: `test_missing_alias_field_gives_random_seven_char_code`, `test_null_alias_gives_random_seven_char_code`
- AC-4: `test_alias_outside_length_range_is_422`(3자, 31자), `test_alias_at_length_boundary_is_created`(4자, 30자), `test_empty_string_alias_is_422_in_the_api`
- AC-5: `test_alias_with_forbidden_characters_or_edge_hyphen_is_422`(16개 parametrize), `test_hyphens_inside_the_alias_are_allowed`, `test_alias_is_not_trimmed_or_normalized`
- AC-6: `test_reserved_alias_is_422`(9개), `test_reserved_alias_gets_the_reserved_message`, `test_reserved_alias_in_other_case_is_also_422`, `test_reserved_alias_still_serves_the_real_route`
- AC-7: `test_duplicate_alias_is_409_and_first_link_is_unchanged`, `test_same_url_and_same_alias_twice_is_still_409`, `test_existing_random_code_as_alias_is_409`
- AC-8: `test_aliases_are_case_sensitive`, `test_other_case_of_an_existing_alias_is_not_a_duplicate_and_not_found`
- AC-9: `test_rejected_requests_store_nothing`, `test_rejected_alias_cannot_be_used_afterwards`. 위 422/409 테스트에도 `count_links` 확인이 들어 있다.
- 보조(`test_aliases.py`, D2-2 등): 비문자열 `alias` 422, URL 오류가 별칭 오류보다 먼저, 잘못된 URL과 올바른 별칭이면 저장 없음.
- AC-10: `test_web_f2.py::test_home_form_has_labeled_alias_input`, `test_home_alias_input_follows_the_mockup`, `test_home_alias_input_does_not_block_server_validation`, `test_home_keeps_url_input_and_submit_button_and_orders_fields`, `test_form_with_alias_shows_alias_in_result_short_url`, `test_alias_made_with_the_form_redirects`, `test_empty_alias_field_gives_random_code`, `test_form_without_alias_field_still_works`
- AC-11: `test_invalid_alias_shows_422_page_with_message_and_kept_values`(7개 parametrize), `test_invalid_alias_marks_only_the_alias_input_as_invalid`, `test_duplicate_alias_shows_409_page_with_message_and_kept_values`, `test_duplicate_alias_keeps_the_existing_link`, `test_duplicate_of_random_code_from_the_form_is_409`, `test_invalid_url_with_alias_marks_url_input_and_keeps_alias`, `test_url_error_comes_before_alias_error`, `test_alias_error_comes_before_duplicate_error`, `test_error_page_escapes_and_keeps_alias_value`, `test_error_page_escapes_and_keeps_url_value_with_alias`
- AC-12: `test_stats.py::test_new_link_stats_has_zero_clicks_and_no_last_access`, `test_stats_of_alias_link_uses_alias_as_code_and_short_url`
- AC-13: `test_three_redirects_give_three_clicks_and_a_last_access_time`, `test_clicks_grow_one_by_one`, `test_alias_redirects_are_counted`, `test_clicks_are_counted_per_link`, `test_redirect_response_is_unchanged_by_counting`
- AC-14: `test_reading_stats_api_does_not_count_clicks`, `test_reading_stats_does_not_change_existing_counts_or_last_access`, `test_stats_screen_does_not_count_clicks`
- AC-15: `test_unknown_code_requests_do_not_count_for_any_link`, `test_unknown_code_after_clicks_keeps_the_count`
- AC-16: `test_stats_of_unknown_code_is_404_json`, `test_stats_api_for_unknown_code_creates_nothing`
- AC-17: `test_web_f2.py::test_stats_screen_shows_clicks_original_url_and_never_accessed`, `test_stats_screen_follows_the_mockup_wording`, `test_stats_screen_shows_created_time_in_time_element`, `test_stats_screen_after_clicks_shows_count_and_last_access`, `test_stats_screen_shows_click_count_without_thousands_separator`, `test_stats_screen_works_for_mixed_case_alias`
- AC-18: `test_stats_screen_for_unknown_code_is_404_page`, `test_stats_screen_for_unknown_code_creates_nothing`
- AC-19: `test_result_page_has_stats_link_for_random_code`, `test_result_page_has_stats_link_for_alias`, `test_result_page_places_stats_link_before_back_link`, `test_stats_link_on_result_page_leads_to_the_stats_screen`
- AC-20: `test_stats.py::test_clicks_survive_creating_the_app_again_with_the_same_db`
- AC-21: `test_web_f2.py::test_stats_screen_escapes_html_in_the_original_url`, `test_stats_screen_escapes_quotes_and_ampersands_in_the_original_url`
- AC-22: `test_f2_screens_have_lang_ko_viewport_and_security_headers`(통계, 통계 404, 별칭 오류, 중복, 별칭 결과 5개 화면에서 lang, viewport, CSP, nosniff 확인), `test_stats_screen_links_the_stylesheet_that_has_f2_styles`
- AC-23: 기존 `tests/test_*.py`를 수정 없이 그대로 두었고 전체 통과했다.
- 보조 `test_validation.py`: 상수와 문구(`test_alias_constants_match_the_spec`, `test_alias_messages_match_the_mockups`), 허용값, 비문자열, 길이, 문자, 예약어(대소문자 무시), 검사 순서 4개, 유니코드 숫자 거절.
- 보조 `test_repository.py`: `create(alias)`, 중복 시 `AliasTakenError`(`.alias`), 기존 무작위 코드와 같은 별칭, 대소문자 구분, 무작위 코드가 별칭과 겹치면 재시도, `record_click`(없는 코드 `None`, 증가, 시각 범위와 UTC·초 단위, 다른 링크 영향 없음, `get`은 안 셈), 스레드 8개로 40번 호출해도 수가 빠지지 않는 동시성 테스트.
- 보조 `test_migration.py`: 열 추가, 기존 행 보존(`clicks=0`, `last_accessed_at=NULL`), 기존 링크 302, 통계 0에서 1로 증가, 통계 화면, 옛 코드와 같은 별칭은 409, 앱 재시작 후 클릭 수 유지, `init_schema` 반복 호출(마이그레이션 DB와 새 DB 모두), 새 DB 열 기본값.

## 설계서 해석이 필요했던 부분
- 설계서와 계획서에서 읽어낸 것이라 비교한 문구는 모두 `validation.py` 상수를 import했다. 다만 `test_alias_messages_match_the_mockups`는 문구 원문을 직접 고정한다. 상수가 목업과 달라지는 것을 잡으려는 의도다.
- 계획 3.1의 검사 순서 때문에 3자 예약어 `api`와 `API`는 길이 규칙(`MSG_ALIAS_LENGTH`)에서 먼저 걸리고, `openapi.json`은 문자 규칙(`MSG_ALIAS_CHARS`)에서 걸린다. AC-6 테스트는 예약어 9개 모두 "422"만 확인한다. 문구까지 확인하는 `MSG_ALIAS_RESERVED` 테스트는 길이와 문자 규칙을 통과하는 7개에만 건다.
- 계획 3.4의 `error_field`에 따라 URL 오류면 URL 칸에, 별칭 오류와 409면 별칭 칸에만 `aria-invalid="true"`가 붙는지 확인한다. 오류 문구는 `<p id="form-error" role="alert">` 하나다.
- 통계 화면의 보이는 시각은 `display_timestamp()` 형식(`YYYY-MM-DD HH:MM:SS UTC`)이고 `<time datetime>`은 API의 `created_at`·`last_accessed_at`과 같다. 이를 D2-6대로 확인한다.
- 이 문서 어디에도 없는 임의 판단: 클릭 수에 천 단위 구분이 없는지 확인하려고 `UPDATE links SET clicks = 1234`로 DB를 직접 바꿔 "1234"가 보이는지 본다. 목업 주석(F2-stats.html)과 계획 3.4의 "천 단위 구분 없이"가 근거다.

## 남은 문제와 질문
- 계획 3.4와 목업은 오류 문구 id를 `form-error`로 정했는데, 이 테스트는 그에 맞춰 썼다. F1 시절 `home.html`은 `url-error`였다. 현재 구현은 통과하므로 이미 맞춰져 있다.
- `html_helpers.py`는 테스트 모듈이 아니라 헬퍼라서 `from html_helpers import ...`로 쓴다. `tests`에 `__init__.py`가 없는 pytest 기본(prepend) 임포트 방식을 전제로 한다.
- 샌드박스 훅이 프로젝트 밖(스크래치패드) 쓰기를 막아서, 기존 파일(`test_repository.py`, `test_validation.py`)에 추가할 때는 프로젝트 안에서 Edit으로 직접 이어 붙였다.
