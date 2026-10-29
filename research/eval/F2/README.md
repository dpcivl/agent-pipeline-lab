<!-- EVAL-CANARY-F2-13315d954563022c -->
# F2 숨은 수용 테스트

F2 설계서(`docs/features/F2.md` v1)의 AC-1~AC-22를 공개 HTTP 인터페이스로만 검사하는 채점용 테스트입니다. 모든 파이프라인 결과물을 같은 기준으로 채점합니다. 앱은 고정 계약(`shortlink.main.create_app`, `shortlink.config.Settings`)으로만 만들고, 구현 내부(모듈, 테이블 이름·컬럼, 클릭 저장 방식)는 보지 않습니다. F1 테스트 모음에서 아무것도 가져오지 않습니다.

## 실행

채점할 구현의 저장소 루트에서:

```
uv run pytest research/eval/F2 -q
uv run pytest research/eval/F1 research/eval/F2 -q   # AC-23 포함 전체 채점
```

- 테스트마다 새 임시 `db_path`를 쓰고 `base_url="http://testserver"`로 앱을 만듭니다. `TestClient(follow_redirects=False)`.
- `app_factory`·`make_client` 픽스처는 부를 때마다 같은 `db_path`에 새 앱을 만듭니다(AC-20의 재시작).
- 파일: `conftest.py`(픽스처, HTML 파서, SQLite 행 수 스냅샷), `test_f2_alias.py`(AC-1~11, 110개), `test_f2_stats.py`(AC-12~22, 42개). 총 152개.
- 추가 의존성은 없습니다(pytest, 표준 라이브러리, FastAPI/Starlette 기본 제공분).

## AC별 테스트

- AC-1: `test_hidden_ac01_alias_becomes_code_and_short_url`(올바른 별칭 7개: `my-link`, `MyLink`, `Abc1234`, `1234`, `a-b-c`, `ab--cd`, `Release-2026-10`), `test_hidden_ac01_alias_short_url_follows_configured_base_url`
- AC-2: `test_hidden_ac02_alias_redirects_to_original`(AC-1과 같은 별칭 7개), `test_hidden_ac02_alias_and_random_codes_coexist`
- AC-3: `test_hidden_ac03_no_alias_gives_seven_char_code`, `test_hidden_ac03_form_without_alias_gives_seven_char_code`, `test_hidden_ac03_form_blank_alias_gives_seven_char_code`
- AC-4: `test_hidden_ac04_alias_length_bounds_accepted`(4자, 30자, 생성과 리다이렉트), `test_hidden_ac04_alias_length_bounds_rejected`(1, 2, 3, 31, 40자)
- AC-5: `test_hidden_ac05_rejects_disallowed_characters`(공백, `_`, `/`, `.`, 한글, 한글 섞임, `?`, `#`, `%`, `+`, `@`, `:`, 끝 줄바꿈, 탭), `test_hidden_ac05_rejects_leading_or_trailing_hyphen`(앞, 뒤, 양쪽, 하이픈만)
- AC-6: `test_hidden_ac06_rejects_reserved_alias`(예약어 9개 모두)
- AC-7: `test_hidden_ac07_duplicate_alias_conflicts`(다른 URL, 같은 URL), `test_hidden_ac07_duplicate_alias_conflicts_repeatedly`, `test_hidden_ac07_alias_equal_to_existing_random_code_conflicts`
- AC-8: `test_hidden_ac08_aliases_are_case_sensitive`, `test_hidden_ac08_case_variants_in_any_order`, `test_hidden_ac08_exact_case_still_conflicts`, `test_hidden_ac08_other_case_is_not_found_before_creation`
- AC-9: `test_hidden_ac09_alias_storage_is_observable_precondition`(정상 생성은 행이 늘어나는지 확인하는 전제), `test_hidden_ac09_rejected_422_stores_nothing`(거절 유형 12개), `test_hidden_ac09_rejected_409_stores_nothing`, `test_hidden_ac09_rejected_alias_is_not_routable`, `test_hidden_ac09_alias_rejected_for_bad_url_stays_free`, `test_hidden_ac09_rejections_leave_empty_db_unchanged`. db_path의 모든 테이블 행 수를 테이블 이름 가정 없이 비교합니다.
- AC-10: `test_hidden_ac10_home_form_has_labeled_alias_field`, `test_hidden_ac10_alias_label_text`, `test_hidden_ac10_form_alias_used_in_result_short_url`, `test_hidden_ac10_form_alias_is_case_sensitive`
- AC-11: `test_hidden_ac11_invalid_alias_form_shows_422`, `test_hidden_ac11_invalid_alias_form_keeps_values`(각각 짧음, 긺, 공백, `_`, 한글, 앞 하이픈, 예약어, 마크업 8개), `test_hidden_ac11_duplicate_alias_form_shows_409`, `test_hidden_ac11_duplicate_alias_form_keeps_values`, `test_hidden_ac11_form_alias_equal_to_random_code_shows_409`, `test_hidden_ac11_invalid_url_with_alias_keeps_both_values`, `test_hidden_ac11_form_rejection_stores_nothing`(422 3개, 409 1개)
- AC-12: `test_hidden_ac12_new_link_stats`, `test_hidden_ac12_new_alias_link_stats`, `test_hidden_ac12_short_url_follows_configured_base_url`, `test_hidden_ac12_form_created_link_has_stats`
- AC-13: `test_hidden_ac13_three_redirects_count_three`, `test_hidden_ac13_each_redirect_adds_one`, `test_hidden_ac13_alias_redirects_are_counted`, `test_hidden_ac13_counts_are_per_link`, `test_hidden_ac13_case_variant_aliases_counted_separately`, `test_hidden_ac13_last_accessed_does_not_go_back`
- AC-14: `test_hidden_ac14_stats_api_does_not_count_on_new_link`, `test_hidden_ac14_stats_api_does_not_count_after_clicks`, `test_hidden_ac14_stats_page_does_not_count`
- AC-15: `test_hidden_ac15_unknown_codes_do_not_count`, `test_hidden_ac15_unknown_codes_do_not_change_existing_counts`
- AC-16: `test_hidden_ac16_unknown_code_stats_api_404`(빈 DB, 3개), `test_hidden_ac16_unknown_code_stats_api_404_when_others_exist`
- AC-17: `test_hidden_ac17_stats_page_for_new_link`, `test_hidden_ac17_stats_page_after_clicks`, `test_hidden_ac17_stats_page_for_random_code`, `test_hidden_ac17_stats_page_shows_short_url`
- AC-18: `test_hidden_ac18_unknown_code_stats_page_404`(2개), `test_hidden_ac18_case_variant_stats_page_404`
- AC-19: `test_hidden_ac19_result_page_links_to_stats`, `test_hidden_ac19_result_page_links_to_alias_stats`
- AC-20: `test_hidden_ac20_clicks_survive_new_app`, `test_hidden_ac20_alias_clicks_survive_new_app`, `test_hidden_ac20_unclicked_link_survives_new_app`
- AC-21: `test_hidden_ac21_stats_page_escapes_url`(특수문자 URL 4개), `test_hidden_ac21_stats_page_escapes_url_after_clicks`
- AC-22: `test_hidden_ac22_stats_page_has_lang_ko`, `test_hidden_ac22_stats_page_has_viewport_meta`(새 링크, 접근한 링크, 없는 코드 3개 화면)
- AC-23: 이 폴더에 테스트가 없습니다. F1 숨은 테스트(`research/eval/F1`)를 같은 구현에 함께 실행해 확인합니다.

## 판정 기준에서 일부러 정한 해석

- 올바른 별칭: 설계서 규칙(4~30자, `[A-Za-z0-9-]`, 하이픈으로 시작·끝 금지, 예약어 아님)을 모두 지키면 생성되어야 합니다. 그래서 숫자만 있는 `1234`, 하이픈이 연속인 `ab--cd`도 201을 기대합니다.
- AC-5 "허용하지 않는 문자": 설계서 예시(공백, `_`, `/`, `.`, 한글)에 더해 ASCII 문장부호(`?`, `#`, `%`, `+`, `@`, `:`)와 탭, 끝 줄바꿈(`mylink\n`, 정규식 `$` 실수 검출)도 422를 기대합니다. 끝 줄바꿈은 API에서만 검사합니다.
- AC-7: 설계서 "이미 쓰이는 코드나 별칭이면 409"에 따라, 이미 있는 무작위 7자 코드와 같은 별칭도 409입니다.
- AC-8: 대소문자 구분이므로 `My-Link`만 있을 때 `GET /my-link`, 통계 API, 통계 화면은 모두 404입니다.
- AC-3 폼 빈 별칭: 홈 화면의 별칭 입력칸은 "선택"이고 브라우저는 빈 입력칸도 `alias=`로 보내므로, 폼에서 별칭이 빈 문자열이면 별칭을 주지 않은 것으로 보고 7자 코드를 기대합니다. (API의 `"alias": ""`는 아래처럼 검사하지 않습니다.)
- AC-9: 422 거절에는 별칭 규칙 위반뿐 아니라 별칭이 올바르고 URL이 잘못된 경우도 넣었습니다. 그 별칭은 소비되지 않아 뒤에 같은 별칭으로 만들 수 있어야 합니다. 409 거절 뒤에는 기존 링크의 URL이 그대로인지 리다이렉트로 확인합니다.
- AC-10 라벨: 별칭 입력칸은 `name="url"`이 든 `<form method="post" action="/">` 안에 있어야 하고, 감싸는 `<label>` 또는 `for=id` `<label>`이 붙어야 합니다. 라벨 문구는 라벨 텍스트에 "별칭 (선택)"이 들어 있는지 공백을 무시하고 따로 봅니다.
- AC-11 오류 메시지: 문구가 정해져 있지 않으므로, 오류 화면에 홈 화면에 없는 텍스트 조각(제출한 URL·별칭 자체 제외)이 하나 이상 있는지로 판단합니다. 입력칸 값은 `name="url"`, `name="alias"`인 `<input>`의 `value`(또는 `<textarea>` 내용)가 제출값과 같은지 봅니다. 마크업이 든 별칭은 이스케이프(F1 요구사항)도 함께 확인합니다.
- AC-11: 이미 있는 무작위 코드와 같은 별칭을 폼으로 주면 409, 올바른 별칭과 잘못된 URL을 폼으로 주면 422이고 두 값 모두 입력칸에 남아야 합니다.
- AC-12: `created_at`은 생성 응답의 `created_at`과 1초 이내로 같아야 합니다(표현 차이 허용). `clicks`는 bool이 아닌 정수여야 하고, `last_accessed_at` 키는 있어야 하며 값이 `null`이어야 합니다.
- AC-13: `last_accessed_at`은 F1 `created_at`과 같은 형식(`YYYY-MM-DDTHH:MM:SS`, 소수 초 선택, `Z` 또는 `+00:00`)이고, 요청 시각과 1분 이내, `created_at`보다 이르지 않아야 합니다(1초 여유). 다음 접근 뒤 값이 뒤로 가지 않아야 합니다.
- AC-14: "통계 조회는 클릭 수를 늘리지 않습니다"를 통계 화면(`GET /stats/{code}`) 조회에도 적용합니다. 클릭 수는 리다이렉트 횟수와 같아야 하기 때문입니다.
- AC-17 클릭 수 표시: 화면의 텍스트 노드(script/style 제외)를 하나씩 따로 보고, 어느 노드에 클릭 수가 독립된 숫자로 있는지 봅니다. 노드를 이어 붙이지 않으므로 `<p>4</p><p>2026-10-29…</p>`처럼 요소 사이에 공백이 없어도 "42026…"으로 읽히지 않습니다. 날짜·시각 조각(`-`, `:`, `.`, `/`에 붙은 숫자)은 숫자로 치지 않습니다. 오탐을 줄이려고 숫자가 없는 별칭과 URL을 쓰고, 0회(새 링크)와 5회를 확인합니다. 접근한 뒤에는 "아직 없음"이 없어야 합니다. 단축 URL은 텍스트나 링크 `href`에 있으면 인정합니다.
- 화면 문구("별칭 (선택)", "아직 없음", "통계 보기", "링크를 찾을 수 없습니다")는 공백을 모두 지우고 비교합니다. 문구가 여러 요소로 나뉘거나 요소 사이 공백이 없어도 같은 결과가 나옵니다.
- AC-18: F1의 찾을 수 없음 화면과 같은 기준입니다. 안내 문구 "링크를 찾을 수 없습니다"와 홈 링크(`href`가 `/`, `http://testserver/`, `http://testserver` 중 하나)를 봅니다.
- AC-19: "통계 보기" 링크는 `href`가 `/stats/{code}` 또는 `http://testserver/stats/{code}`이고 링크 텍스트에 "통계 보기"가 있어야 합니다. 그 링크를 따라가면 200 통계 화면이어야 합니다.
- AC-20: 새 앱에서도 클릭 수와 `last_accessed_at` 값이 같아야 하고, 새 앱에서의 클릭이 이어서 더해져야 합니다.
- AC-21: 페이지 자체 스크립트와 구별하려고 표식(`__f2xss`)이 든 유효 URL을 씁니다. 원문 `<script>window.__f2xss` 문자열이 HTML에 없고, 파싱한 `<script>` 내용과 `on*` 속성에 표식이 없어야 하며, 원래 URL이 화면 텍스트로 그대로 복원되어야 합니다.

## 일부러 검사하지 않은 것 (설계서가 정하지 않음)

- 409·422·404 응답 본문 형식과 오류 메시지 문구 (API, 웹 모두)
- API에서 `"alias": ""`, `"alias": null`, 문자열이 아닌 별칭(숫자 등)을 "주지 않음"으로 볼지 422로 볼지
- 앞뒤 공백이 있는 별칭을 다듬을지 거절할지, 폼 입력값의 앞뒤 공백 처리
- 영문·숫자 이외의 유니코드 글자·숫자(악센트 문자, 전각 문자, 아랍 숫자 등). 설계서가 명시한 한글만 검사합니다.
- 예약어를 대소문자 바꿔 쓴 별칭(`Links`, `ADMIN` 등)의 처리
- 규칙 위반과 중복이 겹칠 때(예: 잘못된 URL과 이미 쓰이는 별칭) 422와 409 중 어느 것이 우선인지
- 통계 API의 추가 필드, 필드 순서, `created_at` 문자열이 생성 응답과 글자까지 같은지
- 통계 조회가 `last_accessed_at`을 바꾸는지 (AC-14는 `clicks`만 정함)
- `HEAD` 요청이나 리다이렉트 외 방법의 접근을 클릭으로 셀지, 동시 요청에서의 클릭 수 정확성
- 1초 안에 여러 번 접근할 때 `last_accessed_at`이 반드시 커져야 하는지 (뒤로 가지 않는지만 봄)
- 통계 화면의 생성 시각·마지막 접근 시각 표시 형식(현지화 여부), 항목 순서와 이름표 문구
- 특수문자가 든 URL로 리다이렉트할 때 `Location` 헤더의 인코딩
- F1 시절 데이터베이스 파일로 시작할 때의 호환성 (설계서가 리뷰와 QA로 확인한다고 정함)
- CSS, 클래스 이름, 마크업 구조, 공백, 속성 순서, 폭 375px 레이아웃
