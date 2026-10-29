# F1 숨은 수용 테스트

F1 설계서(`docs/features/F1.md` v2)의 AC-1~AC-23을 공개 HTTP 인터페이스로만 검사하는 채점용 테스트입니다. 모든 파이프라인 결과물을 같은 기준으로 채점합니다. 앱은 고정 계약(`shortlink.main.create_app`, `shortlink.config.Settings`)으로만 만들고, 구현 내부(모듈, 테이블 이름, 코드 생성 방식)는 보지 않습니다.

## 실행

채점할 구현의 저장소 루트에서:

```
uv run pytest research/eval/F1 -q
```

- 테스트마다 새 임시 `db_path`를 쓰고 `base_url="http://testserver"`로 앱을 만듭니다. `TestClient(follow_redirects=False)`.
- 파일: `conftest.py`(픽스처, HTML 파서, SQLite 행 수 스냅샷), `test_f1_api.py`(AC-1~15, 57개), `test_f1_web.py`(AC-16~23, 50개). 총 107개.
- 추가 의존성은 없습니다(pytest, 표준 라이브러리, FastAPI/Starlette 기본 제공분).

## AC별 테스트

- AC-1: `test_ac01_create_returns_201_with_fields`
- AC-2: `test_ac02_code_is_seven_alphanumerics`, `test_ac02_short_url_is_base_url_slash_code`, `test_ac02_short_url_follows_configured_base_url`
- AC-3: `test_ac03_url_returned_verbatim` (6개 URL: 끝 슬래시 없음, 대소문자, `%2F`·`%20`, `..` 경로, 프래그먼트, 포트)
- AC-4: `test_ac04_http_url_is_accepted`
- AC-5: `test_ac05_rejects_non_http_scheme` (ftp, javascript, data, mailto, file, 스킴 없음), `test_ac05_rejects_javascript_scheme`
- AC-6: `test_ac06_rejects_missing_url_field`, `test_ac06_rejects_non_string_url` (int, float, null, bool, list, object), `test_ac06_rejects_empty_string`
- AC-7: `test_ac07_rejects_url_without_host` (`https://`, `http://`, `https:///path`)
- AC-8: `test_ac08_accepts_2048_chars`(생성과 리다이렉트), `test_ac08_rejects_2049_chars`, `test_ac08_rejects_much_longer_url`
- AC-9: `test_ac09_storage_is_observable_precondition`(정상 생성은 행이 늘어나는지 확인하는 전제), `test_ac09_rejected_request_stores_nothing`(거절 유형 7개), `test_ac09_rejected_requests_leave_db_unchanged_from_empty`. db_path의 모든 테이블 행 수를 테이블 이름 가정 없이 비교합니다.
- AC-10: `test_ac10_redirects_with_302_to_original`(AC-3과 같은 URL 6개), `test_ac10_redirects_http_url`
- AC-11: `test_ac11_unknown_code_returns_404`(7자, 짧은 코드, 긴 코드), `test_ac11_unknown_code_404_when_other_codes_exist`
- AC-12: `test_ac12_same_url_twice_gives_different_codes`
- AC-13: `test_ac13_hundred_codes_are_unique`
- AC-14: `test_ac14_redirect_survives_new_app_on_same_db`, `test_ac14_new_app_still_returns_404_for_unknown`
- AC-15: `test_ac15_created_at_is_utc_iso8601_and_recent`
- AC-16: `test_ac16_home_returns_html`, `test_ac16_home_has_post_form_to_root`, `test_ac16_url_field_has_label`, `test_ac16_submit_button_says_shorten`
- AC-17: `test_ac17_result_page_shows_short_link_and_original`, `test_ac17_short_link_uses_configured_base_url`, `test_ac17_accepts_http_url`
- AC-18: `test_ac18_result_page_has_copy_button`, `test_ac18_result_page_links_home_to_shorten_another`
- AC-19: `test_ac19_invalid_url_shows_422_error_page`, `test_ac19_invalid_url_keeps_submitted_value`, `test_ac19_invalid_url_shows_error_message`, `test_ac19_invalid_url_stores_nothing`(각각 ftp, javascript, mailto, 호스트 없음, 빈 문자열, 2,049자), `test_ac19_missing_url_field_rejected_and_not_stored`
- AC-20: `test_ac20_result_page_escapes_special_characters`(유효 URL 3개), `test_ac20_error_page_escapes_special_characters`(무효 URL 2개)
- AC-21: `test_ac21_not_found_page`
- AC-22: `test_ac22_page_has_lang_ko`, `test_ac22_page_has_viewport_meta` (홈, 결과, 입력 오류, 찾을 수 없음 4개 화면)
- AC-23: `test_ac23_form_created_code_redirects`

## 판정 기준에서 일부러 정한 해석

- AC-15: `created_at`은 `YYYY-MM-DDTHH:MM:SS`에 소수 초(선택)와 `Z` 또는 `+00:00`이 붙은 형식을 모두 UTC ISO 8601로 인정합니다. 시간대 표시가 없는 값은 UTC임을 알 수 없으므로 실패입니다.
- AC-5: 스킴이 아예 없는 `example.com/path`도 "스킴이 http/https가 아님"으로 보고 422를 기대합니다.
- AC-17·AC-23: 단축 URL 링크는 `href`가 `<base_url>/<7자 코드>` 전체 URL과 같아야 합니다(설계서 "href가 단축 URL"). 원래 URL은 화면 텍스트(script/style 제외)에 있어야 합니다.
- AC-18·AC-21: 홈 링크는 `href`가 `/`, `http://testserver/`, `http://testserver` 중 하나이면 인정합니다. "복사" 버튼은 `<button>` 또는 `<input type="button|submit">`의 문구로 찾습니다.
- AC-19 오류 메시지: 문구가 정해져 있지 않으므로, 오류 화면에 홈 화면에 없는 텍스트 조각(제출한 값 자체 제외)이 하나 이상 있는지로 판단합니다. 입력칸 값은 `name="url"`인 `<input>`의 `value`(또는 `<textarea>` 내용)가 제출값과 같은지 봅니다.
- AC-19 필드 누락: "폼 제출은 API와 같은 검증 규칙"에 따라 `url` 필드 없이 POST `/`하면 422이고 저장이 없어야 합니다. 이 경우 응답 형식(HTML 여부)은 검사하지 않습니다.
- AC-20: 페이지 자체의 `<script>`(복사 버튼용)와 구별하려고 표식(`__f1xss`)이 든 페이로드를 씁니다. 원문 `<script>window.__f1xss` 문자열이 HTML에 없고, 파싱한 `<script>` 내용과 `on*` 속성에 표식이 없어야 합니다. 결과 화면은 원래 URL이 텍스트로, 오류 화면은 입력칸 값으로 그대로 복원되는지도 확인합니다. 유효 URL 페이로드는 공백 없이 스킴·호스트·길이 규칙을 모두 만족하므로 200이어야 합니다.

## 일부러 검사하지 않은 것 (설계서가 정하지 않음)

- 422 응답 본문 형식과 오류 메시지 문구 (API, 웹 모두)
- 코드 생성 방식(무작위성의 품질, 충돌 시 재생성 로직). 100개 고유성만 봅니다.
- 앞뒤 공백이 있는 URL, 대문자 스킴(`HTTPS://`), 공백·비ASCII 문자가 든 URL을 받을지 거절할지
- 비ASCII URL의 `Location` 헤더 인코딩
- JSON이 아닌 본문, JSON 객체가 아닌 본문(배열 등)에 대한 응답
- 웹 폼으로 같은 URL을 두 번 만들 때 코드가 달라야 하는지 (중복 비합치 규칙은 `POST /links` 절에만 있음)
- 홈 화면의 서비스 이름과 한 줄 설명의 구체 문구 (AC에 없음)
- CSS, 클래스 이름, 마크업 구조, 공백, 속성 순서
- 폭 375px에서 가로 스크롤이 없는지 (레이아웃 측정 불가, viewport meta 존재만 확인)
- "복사" 버튼의 실제 클립보드 동작 (브라우저 JavaScript 필요)
- `/static` 경로 제공 여부
- 응답 헤더 중 `Location` 외 항목(캐시 헤더 등), 404 JSON API 응답 본문
