---
seq: 5
sender: "test-writer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T07:17:40.611Z"
agent: "test-writer"
agent_id: "ad449d73f4906be98"
turn: 1
reply_to: 3
chars: 5691
tokens_est: 1905
wait_s: null
---

## 결과: 완료

작성 중 implementer의 구현이 `src/`에 반영되어, 최종 실행에서 `uv run python -m pytest -q` 452개 전부 통과했다(F1 기존 테스트 포함, 수정 없음). `ruff check tests`와 `ruff format tests`도 통과했다. 실행 중 한 번 실패가 있었는데, 시각 두 개가 같은 초라서 `<time>` 검색이 2건 나온 내 테스트 오류였다. 문서 순서로 비교하도록 고쳤다. 구현 쪽 결함은 발견하지 못했다.

## 변경 파일
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r1\tests\conftest.py: 픽스처만 추가했다. `read_clicks`(한 코드의 clicks를 DB 파일에서 직접 읽음), `total_clicks`(clicks 합계), `create_f1_database`(F1 3열 스키마 DB 생성). 기존 `settings`, `app`, `client`, `count_links`는 그대로다.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r1\tests\test_alias_api.py: AC-1~9 (API 별칭).
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r1\tests\test_alias_web.py: AC-10, 11 (폼 별칭, 422/409 화면).
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r1\tests\test_stats_api.py: AC-12~16, 20, E-10 동시 클릭.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r1\tests\test_stats_web.py: AC-17~19, 21, 22.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r1\tests\test_alias_validation.py: `validate_alias` 단위 테스트(규칙 순서, 문구, 상수).
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r1\tests\test_migration.py: F1 DB 이전, `init_schema`와 `migrate_schema` 반복 호출.
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r1\tests\test_repository.py: F2 테스트만 뒤에 추가했다(별칭 충돌, `record_click`, 동시성). import 줄에 `threading`과 `AliasConflictError`를 더했다.

`HTMLParser` 기반 `Page` 헬퍼는 `test_alias_web.py`와 `test_stats_web.py`에 각각 복사해 두었다. `test_web.py`는 건드리지 않았고 새 공용 모듈도 만들지 않았다.

## 수용 기준과 테스트 대응
- AC-1: `test_valid_alias_gives_201_and_alias_is_the_code`, `test_short_url_uses_the_configured_base_url_for_aliases` (test_alias_api)
- AC-2: `test_alias_redirects_with_302_to_the_original_url`, `test_alias_of_30_chars_with_hyphens_redirects`, `test_seven_char_alias_redirects`
- AC-3: `test_request_without_alias_field_gets_a_random_seven_char_code`, `test_request_with_null_alias_gets_a_random_seven_char_code`
- AC-4: `test_alias_length_boundaries`(3, 4, 30, 31자), `test_empty_alias_string_is_rejected_as_a_length_violation`
- AC-5: `test_alias_with_disallowed_characters_is_rejected`(공백, `_`, `/`, `.`, 한글, `+`, 끝 줄바꿈, 앞뒤 공백, 전각 숫자), `test_alias_starting_or_ending_with_hyphen_is_rejected`
- AC-6: `test_reserved_alias_is_rejected`(9개 전부), `test_reserved_alias_gets_the_reserved_message`, `test_reserved_alias_comparison_ignores_case`
- AC-7: `test_duplicate_alias_gives_409_and_keeps_the_original_link`, `test_alias_equal_to_an_existing_random_code_gives_409`
- AC-8: `test_aliases_are_case_sensitive`, `test_alias_differing_only_in_case_is_not_found_before_it_is_created`
- AC-9: `test_rejected_alias_stores_nothing`, `test_non_string_alias_is_rejected_and_stores_nothing`, `test_conflict_stores_nothing_new`, `test_accepted_alias_stores_one_row`(대조군)
- AC-10: `test_home_form_has_a_labeled_alias_input`, `test_home_alias_input_matches_the_mockup`, `test_form_with_alias_shows_result_with_the_alias_in_the_short_url`, `test_alias_created_by_form_redirects_to_the_original_url` (test_alias_web)
- AC-11: `test_invalid_alias_shows_422_page_with_message_and_kept_values`(10가지 위반), `test_invalid_alias_page_matches_the_mockup`, `test_duplicate_alias_shows_409_page_with_message_and_kept_values`, `test_duplicate_alias_page_matches_the_mockup`, 값 이스케이프 테스트들
- AC-12: `test_new_link_stats_has_six_fields_zero_clicks_and_no_last_access` (test_stats_api)
- AC-13: `test_three_redirects_make_clicks_three_and_fill_last_accessed_at`, `test_each_redirect_adds_exactly_one`, `test_clicks_are_counted_per_link`
- AC-14: `test_stats_api_calls_do_not_add_clicks`, `test_stats_page_views_do_not_add_clicks`, `test_stats_api_calls_do_not_add_to_existing_clicks`
- AC-15: `test_unknown_code_does_not_change_any_clicks`(5가지 코드), `test_unknown_code_leaves_a_fresh_link_at_zero`, `test_unknown_code_does_not_create_a_row`
- AC-16: `test_stats_for_unknown_code_is_404_json`
- AC-17: `test_stats_page_for_a_new_link_shows_zero_clicks_url_and_no_last_access`, `test_stats_page_shows_click_count_and_last_access_after_visits` (test_stats_web)
- AC-18: `test_stats_page_for_unknown_code_is_404_html`, `test_stats_404_page_has_no_stats_list`
- AC-19: `test_result_page_has_stats_link_for_a_random_code`, `test_result_page_has_stats_link_for_an_alias`, `test_stats_link_from_the_result_page_leads_to_the_stats_screen`
- AC-20: `test_clicks_survive_a_new_app_on_the_same_database`, `test_counting_continues_after_a_new_app` (test_stats_api)
- AC-21: `test_stats_page_escapes_html_in_the_original_url`, `test_stats_page_escapes_quotes_and_ampersands_in_the_original_url`
- AC-22: `test_stats_page_has_lang_ko_and_viewport_meta`, `test_stats_page_for_a_visited_link_has_lang_ko_and_viewport_meta`, `test_stats_404_page_has_lang_ko_and_viewport_meta`
- AC-23: 기존 F1 테스트 전부 수정 없이 통과.
- 보조(규칙 순서와 문구): test_alias_validation.py 전체
- 보조(별칭 충돌, `record_click`): test_repository.py의 F2 구간
- 보조(F1 DB 이전): test_migration.py 전체

## 설계서 해석이 필요했던 부분
- 설계서에 오류 화면의 입력칸 표시 규칙이 직접 없다: 계획 3.4와 목업대로 `aria-invalid="true"`, `aria-describedby`에 `form-error`, `<p id="form-error" role="alert">`를 확인했다. 오류가 난 칸에만 붙는다고 보고, 별칭 오류에서는 URL 칸에 `aria-invalid`가 없음도 검사했다. URL 오류 우선 시에는 URL 칸이 표시된다고 봤다.
- AC-6 "`openapi.json`, `api`": 길이나 문자 규칙에 먼저 걸려도 422면 되는 것으로 본다(계획 4절 주석). 그래서 9개 전부는 "422이고 detail이 문자열"만 확인했다. 문구까지 확인하는 것은 예약어 규칙에 도달하는 7개와 대소문자 변형이다.
- 동시성 테스트 두 개(`test_concurrent_record_click_does_not_lose_counts`가 test_repository와 test_stats_api에 하나씩)는 E-10을 근거로 추가했다. 설계서 AC가 아니라 결정 기록에서 온 것이다. 스레드 8개에 각 10회 클릭이고, API 쪽은 스레드마다 별도 TestClient를 쓴다. 이 환경에서는 통과했지만 느린 환경에서 흔들릴 가능성이 조금 있다.

## 남은 문제와 질문
- 없음. 이전 테스트(test_migration.py)는 설계서가 "평가 테스트가 아니라 리뷰와 QA 항목"이라 한 부분이지만, 계획 4절에 따라 추가 보호용으로 작성했다.
