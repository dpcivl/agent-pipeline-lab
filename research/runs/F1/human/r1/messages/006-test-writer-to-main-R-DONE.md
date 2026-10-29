---
seq: 6
sender: "test-writer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T05:31:53.043Z"
agent: "test-writer"
agent_id: "ad099a69ee132ab3c"
turn: 1
reply_to: 4
chars: 4594
tokens_est: 1638
wait_s: null
---

## 결과: 완료
`uv run ruff check tests`와 `uv run ruff format tests`는 통과했습니다. implementer가 그 사이 src/ 구현을 끝내 놓았고, `uv run python -m pytest`는 152개 전부 통과했습니다. `uv run pytest`는 이 환경의 응용 프로그램 제어 정책이 `pytest.exe` 실행을 막아서(os error 4551) 돌리지 못했습니다. 그래서 `uv run python -m pytest`로 실행했습니다. src/는 수정하지 않았습니다.

## 변경 파일
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\conftest.py: 확장만 했습니다. `count_links` 픽스처를 추가했고, 기존 `settings`, `app`, `client`는 그대로입니다. 이 픽스처는 `settings.db_path`의 `links` 행 수를 sqlite3로 직접 세고 호출마다 연결을 닫습니다(`contextlib.closing`).
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_api_links.py: AC-1~9, 13, 15와 D-1, D-2, 형식 오류 본문 테스트.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_redirect.py: AC-10, 11, 12, 14와 D-4(ASCII 글자 그대로, 한글 퍼센트 인코딩).
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_web.py: AC-16~23. HTML은 `html.parser`로 파싱해서 속성과 문구 위주로 검사합니다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_validation.py: MSG_* 문구, 규칙 순서, D-1, D-2, D-3, 2048/2049 경계.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_repository.py: 저장과 조회, `code_factory` 충돌 재시도, 계속 충돌하면 RuntimeError, `format_timestamp`.

## 수용 기준과 테스트 대응
- AC-1: `test_create_returns_201_and_four_fields`
- AC-2: `test_code_is_seven_alphanumeric_chars_and_short_url_uses_base_url`
- AC-3: `test_response_url_is_exactly_the_request_url` (쿼리, 대문자, 퍼센트 인코딩, 대문자 스킴, 한글, `<>"` 6종)
- AC-4: `test_http_url_is_accepted`
- AC-5: `test_non_http_scheme_is_rejected` (설계서 예시 4개, 본문은 `{"detail": MSG_SCHEME}`)
- AC-6: `test_missing_non_string_or_empty_url_is_rejected`와 `test_malformed_or_non_object_body_is_rejected`. 필드 없음, 다른 필드명, 숫자, null, 배열, bool, 빈 문자열과 깨진 JSON, 객체가 아닌 본문을 확인합니다.
- AC-7: `test_url_without_host_is_rejected`
- AC-8: `test_url_of_2048_chars_is_created`, `test_url_of_2049_chars_is_rejected`
- AC-9: `test_rejected_requests_store_nothing` (9가지 거절 사유, 거절 뒤 행 수 0), 대조군 `test_accepted_request_is_stored`
- AC-10: `test_existing_code_redirects_with_302_and_location`
- AC-11: `test_unknown_code_returns_404`
- AC-12: `test_same_url_twice_gives_different_codes_that_both_redirect`
- AC-13: `test_100_consecutive_creations_give_distinct_codes`
- AC-14: `test_redirect_survives_creating_the_app_again_with_the_same_db`
- AC-15: `test_created_at_is_utc_iso8601_within_a_minute_of_request`
- AC-16: `test_home_page_has_form_with_labeled_url_input_and_submit_button`, `test_home_page_shows_service_name_and_tagline`
- AC-17: `test_valid_form_shows_result_with_short_url_link_and_original_url`, `test_result_page_keeps_short_url_link_without_javascript`
- AC-18: `test_result_page_has_copy_button_and_link_back_home`
- AC-19: `test_invalid_form_shows_422_page_with_message_and_kept_value` (6가지 입력, 행 수 0), `test_invalid_form_page_matches_mockup_wording`, `test_form_without_url_field_is_treated_as_empty`
- AC-20: `test_result_page_escapes_html_in_the_url`, `test_error_page_escapes_html_in_the_submitted_value`, `test_error_page_value_cannot_break_out_of_the_attribute`
- AC-21: `test_unknown_code_shows_404_page_with_notice_and_home_link`
- AC-22: `test_every_screen_has_lang_ko_and_viewport_meta` (홈, 결과, 오류, 404 네 화면)
- AC-23: `test_code_created_by_form_redirects_to_the_original_url`
- D-1: `test_uppercase_scheme_is_accepted_and_kept`(API), `test_scheme_is_case_insensitive_and_value_is_kept`(검증)
- D-2: `test_whitespace_or_control_chars_are_rejected`(API), `test_whitespace_and_control_characters_are_rejected`(검증)
- D-3: `test_length_counts_characters_not_bytes`
- D-4: `test_ascii_location_is_the_stored_url_character_for_character`, `test_non_ascii_url_redirects_with_percent_encoded_location`, `test_korean_path_location_value` (`https://example.com/경로`는 302이고 Location은 `https://example.com/%EA%B2%BD%EB%A1%9C`)
- D-7: `test_home_input_does_not_block_server_validation`
- D-8: `test_format_timestamp_is_utc_iso8601_with_z`

## 설계서 해석이 필요했던 부분
- AC-6 "문자열이 아니거나": 계획 3.3은 이 경우의 422 본문을 FastAPI 기본 본문으로 정했습니다. 그래서 상태 코드 422만 확인하고, 빈 문자열일 때만 `{"detail": MSG_EMPTY}`를 확인합니다.
- AC-15 "1분 이상 차이 나지 않는다": 요청 전후 시각과의 차이가 1분 미만인지 확인합니다. 초 단위 절사를 감안해 요청 전후 ±1초 범위도 함께 확인합니다.
- 계획 3.2 "최대 10회 후 RuntimeError": 10번 시도하는 것인지 최초 1회에 재시도 10회인지 모호합니다. 그래서 호출 횟수는 `1 < 호출 수 <= MAX_ATTEMPTS + 1`로 느슨하게 잡았습니다. 9번 충돌 뒤 10번째에 성공하는 경우는 반드시 성공해야 한다고 검사합니다.
- AC-17 "원래 URL이 보인다": 파싱한 본문 텍스트에 원문이 들어 있는지로 확인했습니다. 원래 URL이 링크인지는 요구하지 않습니다.
- AC-18 복사 버튼: 계획 3.4의 `data-copy`가 단축 URL과 같은지도 함께 검사합니다. 설계서에는 없고 계획 쪽 사항입니다.

## 남은 문제와 질문
- 없음. 다만 `uv run pytest` 직접 실행은 위에서 말한 정책 차단 때문에 확인하지 못했습니다. 테스트 코드 문제가 아니라 환경 문제입니다.
