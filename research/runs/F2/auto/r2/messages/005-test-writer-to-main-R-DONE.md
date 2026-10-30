---
seq: 5
sender: "test-writer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T08:18:17.190Z"
agent: "test-writer"
agent_id: "addded36c42b16b35"
turn: 1
reply_to: 3
chars: 5055
tokens_est: 1972
wait_s: null
---

## 결과: 완료
테스트 394개가 전부 통과합니다. 수집 오류도 없고 `uv run ruff check tests`와 `uv run ruff format tests`도 통과했습니다. 작업 중에 implementer의 구현이 `src/`에 들어와서, 마지막 실행은 스텁이 아니라 실제 구현에 대한 결과입니다. 테스트는 설계서와 계획 기준으로 썼고 구현에 맞춰 고치지 않았습니다. `src/`는 수정하지 않았습니다.

## 변경 파일
- `tests/conftest.py`: 확장만 했습니다. 픽스처 `read_click_state(code)`를 추가했습니다. DB 파일에서 `(clicks, last_accessed_at)`을 직접 읽고, 없는 코드면 None을 돌려줍니다. 기존 `settings`, `app`, `client`, `count_links`는 그대로입니다.
- `tests/test_aliases.py`: 새 파일. AC-1~9.
- `tests/test_stats.py`: 새 파일. AC-12~16, 20.
- `tests/test_web_f2.py`: 새 파일. AC-10, 11, 17, 18, 19, 21, 22. HTML 파서 `Page`는 `test_web.py`의 것을 복사해 이 파일 안에 뒀습니다. 마크업 순서와 공백에는 묶이지 않게 요소를 파싱해서 확인합니다.
- `tests/test_migration.py`: 새 파일. sqlite3로 F1 3열 DB를 직접 만들고 행 2개를 넣은 뒤 `create_app`을 호출합니다. 기존 링크 302, clicks 0에서 시작, 리다이렉트 뒤 1, 통계 화면, 이전 DB에서 새 링크·별칭·409를 확인합니다. 열 추가와 기존 행의 기본값(0, NULL)도 확인합니다. `init_schema`를 반복 호출해도 안전한지, 클릭 수가 유지되는지, 새 DB의 5열 순서도 확인합니다.
- `tests/test_validation.py`: `validate_alias` 테스트를 추가했습니다. 문구·상수 값, 규칙 순서 1<2<3<4<5의 인접 쌍, 통과 시 입력 그대로 반환, 예약어 대소문자 무시를 확인합니다. 길이는 바이트가 아니라 문자 수로 셉니다. 전각 숫자, 아랍 숫자, 끝의 `\n`도 문자 규칙에서 막힙니다.
- `tests/test_repository.py`: `AliasTakenError` 충돌, 충돌 시 저장 없음·재시도 없음(`code_factory`를 호출하지 않음), 무작위 코드와의 충돌, 대소문자 구분 공존, `record_click`을 추가했습니다. `record_click`은 증가, `last_accessed_at` 형식과 UTC 초 단위, 다른 링크 불변, 없는 코드 None, `get()`이 클릭을 세지 않음, 새 저장소에서의 유지, 40건 동시 호출에서 클릭 유실 없음을 확인합니다. F1 테스트는 고치지 않았습니다.

## 수용 기준과 테스트 대응
- AC-1: `test_aliases.py::test_valid_alias_becomes_the_code_and_the_short_url`
- AC-2: `test_aliases.py::test_alias_redirects_to_the_original_url`
- AC-3: `test_aliases.py::test_without_alias_field_a_seven_char_code_is_made`, `test_alias_null_is_the_same_as_no_alias`
- AC-4: `test_aliases.py::test_alias_of_3_or_31_chars_is_rejected`, `test_alias_of_4_or_30_chars_is_created`, `test_empty_alias_string_is_rejected_by_the_length_rule`
- AC-5: `test_aliases.py::test_alias_with_a_forbidden_character_is_rejected`(공백, `_`, `/`, `.`, 한글, 개행 등 11종), `test_alias_starting_or_ending_with_hyphen_is_rejected`, `test_alias_with_letters_digits_and_inner_hyphens_is_created`, `test_alias_that_is_not_a_string_is_rejected`(123 등)
- AC-6: `test_aliases.py::test_reserved_alias_is_rejected`(9개), `test_reserved_alias_gets_the_reserved_message`, `test_reserved_alias_in_other_case_is_rejected`(`Admin`, `LINKS` 등)
- AC-7: `test_aliases.py::test_duplicate_alias_is_rejected_with_409_and_the_first_link_stays`, `test_alias_equal_to_an_existing_random_code_is_409`
- AC-8: `test_aliases.py::test_aliases_differing_only_in_case_are_different`
- AC-9: `test_aliases.py::test_rejected_requests_store_nothing`. 각 422·409 테스트에서도 `count_links()`를 확인합니다.
- AC-10: `test_web_f2.py::test_home_form_has_a_labeled_alias_input`, `test_home_alias_input_shows_the_rule_hint_and_does_not_block_server_validation`, `test_form_with_alias_shows_the_alias_in_the_short_url`
- AC-11: `test_web_f2.py::test_form_with_invalid_alias_shows_422_with_message_and_kept_inputs`(9종), `test_form_with_duplicate_alias_shows_409_with_message_and_kept_inputs`, `test_form_alias_equal_to_an_existing_random_code_is_409`, `test_error_page_escapes_the_alias`
- AC-12: `test_stats.py::test_new_link_has_zero_clicks_and_no_last_access`
- AC-13: `test_stats.py::test_three_redirects_make_three_clicks_and_set_last_access`
- AC-14: `test_stats.py::test_reading_stats_does_not_count_a_click`, `test_stats_page_does_not_count_a_click`
- AC-15: `test_stats.py::test_unknown_code_does_not_change_any_click_count`
- AC-16: `test_stats.py::test_stats_api_for_unknown_code_is_404_json`
- AC-17: `test_web_f2.py::test_stats_page_shows_clicks_and_original_url_and_no_access_notice`, `test_stats_page_after_redirects_shows_the_count_and_the_last_access`
- AC-18: `test_web_f2.py::test_stats_page_for_unknown_code_is_a_404_html_page`
- AC-19: `test_web_f2.py::test_result_page_links_to_the_stats_page_of_the_random_code`, `test_result_page_links_to_the_stats_page_of_the_alias`
- AC-20: `test_stats.py::test_clicks_survive_creating_the_app_again_on_the_same_db`
- AC-21: `test_web_f2.py::test_stats_page_escapes_html_in_the_original_url`
- AC-22: `test_web_f2.py::test_stats_page_has_lang_ko_and_viewport_meta`
- AC-23: 기존 F1 테스트를 수정하지 않고 전체 실행에서 통과했습니다.

## 설계서 해석이 필요했던 부분
- 설계서 "별칭을 주지 않으면": 계획 D-1을 따랐습니다. API에서 필드 없음 또는 `null`은 별칭 없음, `""`는 422입니다. 폼에서는 빈 입력칸과 없는 필드 모두 별칭 없음입니다.
- 예약어 9개의 문구: `api`(3자)는 길이 규칙, `openapi.json`은 문자 규칙에 먼저 걸립니다(계획 D-5). 그래서 9개 전체는 상태 코드 422만 확인하고, 예약어 문구(`MSG_ALIAS_RESERVED`)는 길이·문자 규칙을 통과하는 단어와 대문자 변형에서만 확인했습니다.
- `alias`가 숫자·배열 등일 때의 422: 본문이 `{"detail": "<문구>"}`인지는 확인하지 않고 상태 코드와 저장 없음만 봤습니다. 이 경우 FastAPI 기본 검증 오류 모양이 나올 수 있어서 계획이 정하지 않은 부분입니다.
- "통계 화면에서 마지막 접근 시각이 없으면 `<time>`이 없다"는 계획 3.4의 `<span class="muted">아직 없음</span>` 구조에서 도출했습니다. `test_stats_page_shows_the_created_time_in_readable_and_iso_form`이 이를 가정합니다.

## 남은 문제와 질문
- 없음. 다만 `test_concurrent_clicks_are_not_lost`는 스레드 8개로 40번 호출하면서, 반환된 clicks가 1~40으로 서로 다른지도 확인합니다. 계획 3.2의 "한 트랜잭션에서 UPDATE 후 같은 트랜잭션에서 re-read"를 전제로 한 검사입니다. 구현이 트랜잭션 밖에서 다시 읽도록 바뀌면 이 마지막 단언이 불안정해질 수 있습니다.
