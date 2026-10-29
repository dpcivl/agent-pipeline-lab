---
seq: 14
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T02:24:21.613Z"
agent: "reviewer"
agent_id: "a00ed3da5d1f40b84"
turn: 1
reply_to: 9
chars: 5287
tokens_est: 2376
wait_s: null
---

## 결과: 지적 5건 (blocker 0, major 0, minor 5)

F1 리뷰 1라운드 결과, 수용 기준(AC-1~AC-23)을 어기거나 데이터를 손상시키거나 고정 계약을 위반한 곳은 찾지 못했습니다. 지적한 5건은 모두 minor입니다.

- **고정 계약**: `create_app(settings=None)`의 시그니처를 유지했고, 스키마 준비와 라우터 등록을 모두 마친 앱을 돌려줍니다. `config.py`는 변경이 없습니다. conftest의 `settings`, `app`, `client` 픽스처는 그대로 두고 `count_links`와 `insert_link`만 추가했습니다.
- **템플릿과 목업**: 네 화면 모두 목업과 구조, 문구, class, id, `<title>`이 일치합니다. `style.css`는 네 목업의 `<style>` 내용과 똑같고, `copy.js`도 목업 스크립트와 같습니다.
- **implementer의 판단 4가지는 모두 적절합니다.**
  - **`aria-describedby="url-error url-hint"`**: 화면 구현의 기준인 목업(`F1-input-error.html:17`)과 같고, 접근성 면에서도 계획서 문구보다 낫습니다.
  - **`web.py`의 `TEMPLATES_DIR` 별도 정의**: 순환 import를 피하려는 방법으로 타당합니다. 다만 `main.py`에 쓰이지 않는 값이 남았습니다(R-2).
  - **D-3을 `isspace()`와 C0/C1 제어 문자로 넓게 해석**: "공백·제어 문자를 거절한다"는 결정의 취지 안에 있습니다.
  - **`urlsplit`의 `ValueError`를 422로 처리**: 이 처리가 없으면 500이 나므로 맞는 선택입니다.
  - 남은 문제는 이 판단들이 문서와 테스트에 반영되지 않았다는 점입니다(R-3, R-4).

## 지적 목록

### R-1 [minor] D-7의 "ASCII URL은 그대로 나간다"는 전제가 사실과 다름
- 위치: `src/shortlink/web.py:70`, `docs/plans/F1-plan.md:175`(D-7)
- 문제: Starlette `RedirectResponse`는 `quote(url, safe=":/%#?=@[]!$&'()*+,;")`를 적용합니다(`.venv/Lib/site-packages/starlette/responses.py:218`). 그래서 ASCII라도 `< > " { } | \ ^` 백틱은 퍼센트 인코딩됩니다.
  - 예: AC-20의 `https://example.com/<script>alert(1)</script>`는 생성에 성공합니다. 그런데 리다이렉트할 때 `Location`은 `https://example.com/%3Cscript%3Ealert(1)%3C/script%3E`가 되어, 글자 그대로의 원래 URL이 아닙니다.
  - 이 경우를 고정하는 테스트도 없습니다. `tests/test_redirect.py`의 AC-10 테스트는 모두 safe 문자만 씁니다.
- 근거: AC-10은 "`Location` 헤더에 원래 URL"을 요구하고, D-7은 "ASCII URL은 그대로 나감(AC-10)"이라고 적었습니다.
- 수정 제안: 지금 동작을 유지하는 쪽을 권합니다. 이 문자들은 RFC 3986에서 URI에 그대로 쓸 수 없어 인코딩이 맞고, 브라우저 동작도 같습니다.
  - 결정 기록에서 D-7을 "URI에 쓸 수 없는 문자(비ASCII와 `<>\"{}|\\^` 백틱)는 퍼센트 인코딩된다"로 바로잡습니다.
  - `tests/test_redirect.py`에 이런 URL에 대해 `unquote(location) == url`을 확인하는 테스트를 추가합니다.

### R-2 [minor] 쓰이지 않거나 중복된 코드
- 위치: `src/shortlink/main.py:26`(`TEMPLATES_DIR`), `src/shortlink/web.py:23-29`(`TEMPLATES_DIR`, `get_templates`)
- 문제:
  - `main.TEMPLATES_DIR`는 어디서도 쓰지 않습니다. 같은 경로가 `web.TEMPLATES_DIR`에 한 번 더 정의되어 있습니다.
  - 스켈레톤 인터페이스였던 `get_templates()`는 구현만 있고 호출하는 곳이 없습니다. 라우트는 모듈 전역 `templates`를 직접 씁니다.
- 근거: `grep`으로 확인한 결과, 두 이름 모두 정의 외의 참조가 없습니다.
- 수정 제안: 아래 둘 중 하나로 바꿉니다.
  - `main.TEMPLATES_DIR`를 지우고 `web.TEMPLATES_DIR`만 둡니다. `main`이 이미 `web`을 import하므로 필요하면 `web.TEMPLATES_DIR`를 참조하면 됩니다.
  - 또는 경로 상수를 작은 모듈(예: `shortlink/paths.py`)로 옮겨 두 곳이 함께 씁니다.

  `get_templates()`는 라우트에서 쓰도록 바꾸거나 지웁니다.

### R-3 [minor] 실행 중 내린 결정이 기록되지 않았고, 문서와 코드가 다름
- 위치: `src/shortlink/validation.py:39`(docstring 4단계), `docs/plans/F1-plan.md:125`, `docs/plans/F1-plan.md:171`(D-3)
- 문제: 아래 결정들이 어디에도 기록되지 않았습니다.
  - D-3을 Unicode 공백(`str.isspace`)과 C1 제어 문자(0x80~0x9F)까지 넓힌 것
  - `urlsplit`이 `ValueError`를 내면 스킴에 따라 `MSG_SCHEME`이나 `MSG_NO_HOST`로 422를 돌려주는 것
  - `aria-describedby`에 `url-hint`를 함께 넣은 것

  계획서 5행은 "실행 중 생기는 결정은 `docs/plans/F1-decisions.md`"라고 하지만, 그 파일이 없습니다. 또 `validate_url` docstring 4단계는 "ASCII control characters"라고 적었는데, 실제 검사(`_is_blocked_char`)는 더 넓습니다.
- 근거: 계획서 4절 125행은 `aria-describedby="url-error"`, D-3은 "ASCII 제어 문자"로 적혀 있습니다.
- 수정 제안:
  - 결정 기록에 D-10~D-12 정도로 이 세 가지를 남깁니다. 판단 자체는 모두 적절하므로 내용은 바꾸지 않습니다.
  - docstring 4단계를 "whitespace (incl. Unicode spaces) or C0/C1 control characters"로 고칩니다.

### R-4 [minor] implementer가 추가한 검증 분기에 테스트가 없음
- 위치: `tests/test_validation.py:101-156`
- 문제: 두 분기를 실행하는 테스트가 없습니다. 회귀가 생겨도 잡히지 않습니다.
  - D-3을 넓힌 부분: 예시 `"https://example.com/\u00a0"`, `"\u3000"`, `"\x85"`, `"\u2028"`
  - `urlsplit`의 `ValueError` 분기: `validation.py:53-61`. 예시 `"https://[::1"`, `"ftp://[::1"`
- 근거: 테스트에 있는 IPv6 사례는 정상 URL `"http://[::1]:8080/"` 하나뿐이고, 공백·제어 문자 사례는 ASCII뿐입니다.
- 수정 제안:
  - `test_whitespace_or_control_characters_are_rejected`의 parametrize에 Unicode 공백과 C1 사례를 추가합니다.
  - `"https://[::1"`는 `MSG_NO_HOST`, `"ftp://[::1"`는 `MSG_SCHEME`인지 확인하는 단위 테스트를 추가합니다.
  - API에서도 같은 값이 500이 아니라 422로 거절되는지 확인하는 테스트를 하나 추가합니다.

### R-5 [minor] 결과 화면 테스트가 복사 스크립트 연결과 "원래 URL은 링크가 아님"을 확인하지 않음
- 위치: `tests/test_web.py:157-181`
- 문제:
  - "복사" 버튼은 `copy.js`가 있어야 동작합니다. 그런데 결과 화면의 `<script src="/static/copy.js">` 존재와 `/static/copy.js`의 200 응답을 확인하는 테스트가 없습니다. 템플릿에서 스크립트 태그가 빠져도 테스트는 모두 통과합니다.
  - 계획서 4절은 원래 URL을 "텍스트, 링크 아님"으로 정했지만, `test_result_screen_labels_the_original_url`은 문구가 있는지만 봅니다.
  - 각 화면이 `/static/style.css`를 연결하는지도 확인하지 않습니다. 확인하는 것은 CSS 파일 응답뿐입니다.
- 근거: 설계서 61행 "복사 버튼은 단축 URL을 클립보드에 복사합니다(브라우저 JavaScript)", 계획서 126행
- 수정 제안: 다음 단언을 추가합니다.
  - 결과 페이지에 `script[src="/static/copy.js"]`가 있고, `GET /static/copy.js`가 200을 돌려준다.
  - `href`가 원래 URL인 `<a>`가 없다.
  - 네 화면 모두 `link[rel=stylesheet][href="/static/style.css"]`를 갖는다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)

관련 파일:
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-default-r2\src\shortlink\web.py`
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-default-r2\src\shortlink\main.py`
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-default-r2\src\shortlink\validation.py`
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-default-r2\tests\test_validation.py`
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-default-r2\tests\test_redirect.py`
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-default-r2\tests\test_web.py`
- `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-default-r2\docs\plans\F1-plan.md`
