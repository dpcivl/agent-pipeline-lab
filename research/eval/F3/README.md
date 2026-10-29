<!-- EVAL-CANARY-F3-a35abd6a9f5f3b84 -->
# F3 숨은 수용 테스트

F3 설계서(`docs/features/F3.md` v1)의 AC-1~AC-21을 공개 HTTP 인터페이스로만 검사하는 채점용 테스트입니다. 모든 파이프라인 결과물을 같은 기준으로 채점합니다. 앱은 고정 계약(`shortlink.main.create_app`, `shortlink.config.Settings`)과 F3가 추가하는 `Settings` 필드 `api_keys`, `rate_limit_per_minute`로만 만들고, 구현 내부(모듈, 테이블, 세션 방식)는 보지 않습니다.

## 실행

채점할 구현의 저장소 루트에서:

```
uv run pytest research/eval/F3 -q
```

AC-22(F1·F2 호환)는 이 폴더가 아니라 F1·F2 평가 테스트를 함께 실행해 확인합니다.

```
uv run pytest research/eval/F1 research/eval/F2 research/eval/F3 -q
```

- 앱은 `create_app(Settings(db_path=<임시 경로>, base_url="http://testserver", api_keys=(KEY_A, KEY_B), rate_limit_per_minute=10000))`로 만듭니다. 키 둘은 소유자 둘입니다. AC-13·14만 `rate_limit_per_minute=3`인 앱을 씁니다.
- 클라이언트는 `TestClient(app, follow_redirects=False)`를 감싼 `RecordingTestClient`입니다. 받은 응답을 모두 모아 두고, 키 노출 검사(`assert_no_key_leak`)는 그 응답 전부의 본문과 헤더(이름·값)에 등록된 키 문자열이 없는지 봅니다.
- 파일: `conftest.py`(픽스처), `f3_support.py`(상수, HTML 파서, 폼 처리 도우미; 여러 평가 폴더를 함께 돌릴 때 `conftest` 이름 충돌을 피하려고 따로 둠), `test_f3_auth_expiry.py`(AC-1~7, 41개), `test_f3_delete_rate.py`(AC-8~14, 25개), `test_f3_manage.py`(AC-15~21, 26개). 총 92개.
- 대기 시간: 만료 테스트는 세션 픽스처 `expiry_world` 하나를 함께 씁니다. 2~3초 뒤 만료되는 링크를 만들고 만료 전 상태를 기록한 뒤, 만료 시각 0.6초 뒤까지 한 번만 잠듭니다(약 2.6~3.6초). 그 밖에는 `sleep`이 없습니다.
- 추가 의존성은 없습니다(pytest, 표준 라이브러리, FastAPI/Starlette 기본 제공분).

## AC별 테스트

- AC-1: `test_hidden_ac01_create_with_registered_key_returns_201`(키 A, B), `test_hidden_ac01_create_with_registered_key_and_alias`, `test_hidden_ac01_create_without_key_still_returns_201`, `test_hidden_ac01_create_without_key_when_no_keys_registered`
- AC-2: `test_hidden_ac02_unregistered_key_rejected_and_not_stored`(모르는 키, 등록 키의 앞부분, 뒤에 글자 추가, 대문자, 소문자, 두 키를 쉼표로 이은 값), `test_hidden_ac02_any_key_rejected_when_no_keys_registered`, `test_hidden_ac02_only_configured_keys_are_registered`
- AC-3: `test_hidden_ac03_api_and_screens_never_show_key`(생성 201·409·422, 홈, 결과, 리다이렉트, 통계 API·화면, 삭제 403·404·204, 삭제 뒤 404), `test_hidden_ac03_expired_page_and_stats_never_show_key`. 관리 화면 테스트(AC-15~19)도 모두 끝에서 같은 검사를 합니다.
- AC-4: `test_hidden_ac04_future_expiry_returns_201_with_same_instant`, `test_hidden_ac04_far_future_expiry_returns_same_instant`, `test_hidden_ac04_redirects_before_expiry`, `test_hidden_ac04_expiry_without_api_key`, `test_hidden_ac04_create_without_expiry_has_null_expires_at`
- AC-5: `test_hidden_ac05_past_or_now_expiry_rejected`(10년 전, 1분 전, 지금), `test_hidden_ac05_fixed_past_expiry_rejected`, `test_hidden_ac05_malformed_expiry_rejected`(7개 형식)
- AC-6: `test_hidden_ac06_expired_link_returns_410_page`, `test_hidden_ac06_expired_link_does_not_count_clicks`
- AC-7: `test_hidden_ac07_stats_not_expired_before_expiry`, `test_hidden_ac07_stats_expired_after_expiry`, `test_hidden_ac07_future_expiry_stays_not_expired`, `test_hidden_ac07_no_expiry_stats_null_and_false`, `test_hidden_ac07_stats_screen_still_visible_after_expiry`
- AC-8: `test_hidden_ac08_owner_delete_returns_204_then_404_everywhere`, `test_hidden_ac08_owner_delete_random_code`
- AC-9: `test_hidden_ac09_delete_without_key_is_401`(소유 링크, 소유자 없는 링크), `test_hidden_ac09_delete_with_unregistered_key_is_401`
- AC-10: `test_hidden_ac10_delete_by_other_owner_forbidden`, `test_hidden_ac10_delete_ownerless_link_forbidden`, `test_hidden_ac10_form_created_link_has_no_owner`
- AC-11: `test_hidden_ac11_delete_unknown_code_is_404`, `test_hidden_ac11_delete_twice_second_is_404`
- AC-12: `test_hidden_ac12_deleted_alias_can_be_reused`, `test_hidden_ac12_reused_alias_belongs_to_new_owner`
- AC-13: `test_hidden_ac13_fourth_api_creation_is_429_shared_with_form`(API, 화면, 키 있는 API 뒤 4번째 API), `test_hidden_ac13_fourth_form_creation_is_429_shared_with_api`(화면, API, 화면 뒤 4번째 화면), `test_hidden_ac13_limit_counts_per_client_ip`
- AC-14: `test_hidden_ac14_redirect_and_stats_work_after_limit`, `test_hidden_ac14_reads_do_not_use_up_the_limit`
- AC-15: `test_hidden_ac15_manage_returns_html`, `test_hidden_ac15_manage_has_password_api_key_field`, `test_hidden_ac15_api_key_field_labeled`, `test_hidden_ac15_key_form_posts_to_manage`
- AC-16: `test_hidden_ac16_list_shows_only_own_links`(소유자 A, B), `test_hidden_ac16_list_row_contents`, `test_hidden_ac16_owner_without_links_sees_none`
- AC-17: `test_hidden_ac17_wrong_key_shows_401_error`(모르는 키, 등록 키의 앞부분)
- AC-18: `test_hidden_ac18_delete_from_manage_screen`, `test_hidden_ac18_cannot_delete_others_link_from_manage_screen`(다른 소유자 링크, 소유자 없는 링크)
- AC-19: `test_hidden_ac19_list_escapes_original_url`, `test_hidden_ac19_expired_link_marked_in_list`
- AC-20: `test_hidden_ac20_home_links_to_manage`
- AC-21: `test_hidden_ac21_screen_has_lang_ko`, `test_hidden_ac21_screen_has_viewport_meta`(키 입력, 목록, 틀린 키 401, 삭제 뒤 목록, 만료 410 화면 5개)
- AC-22: 이 폴더에 없음. F1·F2 평가 테스트를 함께 실행해 확인합니다(F1·F2 픽스처는 새 필드를 주지 않으므로 F3 기본값 `api_keys=()`, `rate_limit_per_minute=30`으로 돕니다).

## 판정 기준에서 일부러 정한 해석

- 관리 화면 사용은 브라우저처럼 합니다. `GET /manage`의 HTML에서 `name="api_key"`가 든 POST 폼을 찾아 다른 필드(CSRF 토큰 등)는 그대로, `api_key`에는 키를 넣어 그 폼의 `action`(상대 경로는 `/manage` 기준으로 해석, 경로가 `/manage`여야 함)으로 보냅니다. 쿠키는 TestClient가 유지하고, 관리 화면 폼 POST에는 `Origin: http://testserver`와 `Referer: http://testserver/manage`를 붙입니다. 3xx 응답은 GET으로 따라갑니다.
- 관리 화면 삭제(AC-18)는 숨은 필드 이름을 가정하지 않습니다. 목록 HTML에서 "삭제" 제출 버튼마다, 그 버튼의 조상 중 단축 URL(텍스트 또는 `href`)을 하나만 보여 주는 가장 가까운 요소를 그 링크의 줄로 봅니다. 버튼이 속한 폼(`form=` 속성 포함)이 `method=post`이고 `action`의 경로가 `/manage/delete`인지 확인한 뒤, 폼의 필드 값과 누른 버튼의 `name=value`를 그대로 보냅니다. 비어 있는 비밀번호 입력칸이 있으면 키를 다시 입력하는 방식으로 보고 그 칸에 키를 넣습니다.
- 다른 소유자 링크를 관리 화면으로 지우는 시도(AC-18)는 내 링크의 삭제 요청에서 내 코드가 들어 있는 곳(필드 값, `action`)을 상대 코드로 바꿔 보냅니다. 응답 상태는 보지 않고(5xx만 아니면 됨) 상대 링크가 여전히 302·통계 200인지 봅니다. 폼에 코드가 전혀 드러나지 않으면 바꿀 곳이 없으므로 상대 링크가 살아 있는지만 확인합니다.
- 관리 목록 줄 확인(AC-16): 단축 URL은 전체 URL(`http://testserver/<코드>`)이 텍스트나 `href`로 있어야 하고, 원래 URL은 텍스트로 있어야 합니다. 클릭 수는 61회 리다이렉트 뒤 그 줄의 숫자 토큰에 `61`이 있는지 봅니다(날짜·시각 숫자와 헷갈리지 않는 값). 만료 시각이 없는 줄에는 "없음"이 있어야 합니다.
- 다른 소유자·소유자 없는 링크가 "보이지 않는다"(AC-16)는 목록 HTML 원문에 그 별칭과 원래 URL 문자열이 전혀 없는 것으로 판단합니다.
- 관리 화면에서 키를 넣고 목록을 받는 응답과 삭제 성공 뒤 갱신된 목록은 `200`이어야 합니다(리다이렉트를 따라간 최종 응답 기준).
- 오류 메시지(AC-17)와 429 안내 문구(AC-13 화면 요청): 문구가 정해져 있지 않으므로, 기준 화면(`GET /manage` 또는 `GET /`)에 없는 텍스트 조각이 하나 이상 있는지로 판단합니다. 429 화면은 HTML이고 `/`로 POST하는 `name="url"` 폼(홈 화면)이 있어야 합니다.
- `Retry-After`는 API·화면 429 모두에 있어야 하고 값은 초 단위 정수 문자열이어야 합니다. 값의 크기는 보지 않습니다.
- "저장되지 않음"(AC-2, AC-13)은 DB를 직접 보지 않고, 거절된 요청에 넣은 별칭이 `GET /{별칭}`과 통계 API 모두 `404`인지로 봅니다(AC-2는 그 별칭으로 다시 만들 수 있는지도 확인). 요청 수 기록을 SQLite에 두는 구현도 공정하게 채점하기 위함입니다.
- 만료 시각 비교(AC-4, AC-7): 응답의 `expires_at`은 F1 `created_at`과 같은 기준으로 `Z` 또는 `+00:00`이 붙은 UTC ISO 8601이어야 하고, 보낸 값과 같은 시각이어야 합니다(소수 초 표기 차이는 허용).
- AC-5 "지금 시각"은 초 단위로 내림한 현재 시각을 보냅니다. 서버가 받을 때는 이미 지금이거나 과거이므로 `422`여야 합니다.
- AC-6 클릭 수: 만료 전에 한 번 리다이렉트한 클릭만 세어져 있어야 하고, 만료 뒤 `GET`을 몇 번 해도 그대로여야 합니다.
- AC-12: 지운 별칭으로 다시 만든 링크는 새 링크이므로 F2 기준대로 `clicks` 0, `last_accessed_at` `null`이어야 하고, 새로 만든 키의 소유입니다.
- AC-13 클라이언트 구분: TestClient의 `client=(host, port)`로 IP를 바꿔, 한 IP가 한도를 넘어도 다른 IP는 생성할 수 있는지 봅니다.
- 등록되지 않은 키(AC-2, AC-9, AC-17)에는 등록 키의 앞부분·대소문자 변형도 넣습니다. 접두어 비교나 대소문자 무시 비교를 잡기 위함입니다.

## 일부러 검사하지 않은 것 (설계서가 정하지 않음)

- 오류 응답 본문 형식과 문구(401·403·404·409·422·429 JSON, 관리 화면 오류 문구, 429 안내 문구)
- `DELETE` 204 응답 본문, 관리 화면 삭제가 거절될 때의 상태 코드와 화면
- 키 비교가 실제로 타이밍 공격에 안전한지(응답 시간 측정은 불안정), 로그에 키가 남는지(공개 인터페이스 밖)
- 관리 화면에서 키를 전달하는 방법(쿠키, 서명 토큰, 재입력 등)과 결정 기록 문서. 결과만 봅니다: 키가 응답에 그대로 나오지 않고, 삭제가 동작하고, 남의 링크는 지워지지 않는지.
- 응답 본문·헤더에 키가 변형되어(해시, 일부 가림, base64 등) 나오는 경우. "그대로" 나오는지만 봅니다.
- 등록되지 않은 키로 보낸 값(관리 화면 틀린 키 포함)이 응답에 다시 나오는지
- 빈 `X-API-Key` 값을 "키 없음"으로 볼지 "등록되지 않은 키"로 볼지
- 키 검사·검증·요청 수 제한의 우선순위(예: 등록되지 않은 키 + 잘못된 URL, 키 없음 + 없는 코드 삭제)
- 401·422로 거절된 생성 요청이 요청 수 한도에 들어가는지, 관리 화면·삭제 요청이 한도를 쓰는지
- 1분이 지난 뒤 한도가 풀리는지(60초 대기가 필요해 제외), `Retry-After` 값의 크기
- `X-Forwarded-For` 같은 프록시 헤더 처리
- `expires_at`에 `+00:00`·`+09:00` 같은 오프셋, 소수 초, 시간대 없는 값, 날짜만 있는 값, 숫자(유닉스 시각), 빈 문자열, `null`을 줄 때의 동작
- 만료된 링크의 `last_accessed_at` 변화, 만료된 링크를 삭제할 수 있는지, 만료된 별칭을 다시 쓸 수 있는지
- 관리 목록의 생성 시각과 (지나지 않은) 만료 시각 표시 형식, 줄 순서, 링크가 없을 때의 문구
- `Settings.from_env()`의 `SHORTLINK_API_KEYS`, `SHORTLINK_RATE_LIMIT` 해석(공개 HTTP 인터페이스 밖)
- CSS, 마크업 구조, 폭 375px 레이아웃
- `Secure` 속성 쿠키: 테스트는 `http://testserver`로 요청하므로, 관리 화면 세션 쿠키를 항상 `Secure`로만 주는 구현은 쿠키가 다시 오지 않아 AC-18 등에서 실패합니다. 구현 자신의 `tests/` 픽스처도 같은 `http://testserver`를 쓰므로 공정하다고 봅니다.
