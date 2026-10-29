---
seq: 14
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T06:40:24.059Z"
agent: "reviewer"
agent_id: "a6e4a1b6120d02eff"
turn: 1
reply_to: 9
chars: 4258
tokens_est: 2088
wait_s: null
---

## 결과: 지적 4건 (blocker 0, major 0, minor 4)

F1 1라운드 리뷰입니다(체크포인트 92f903f, 범위 `git diff 8b7193b..92f903f`). 막을 만한 문제(blocker, major)는 없습니다. 이 리뷰에서는 테스트를 다시 돌리지 않았고, 아래 내용은 코드를 읽고 판단한 것입니다.

**확인한 내용**
- **수용 기준:** AC-1~AC-23이 모두 코드와 테스트로 충족됩니다.
- **해석 결정:** 계획의 D-1~D-9를 따릅니다.
- **고정 계약:** `create_app(settings=None)`, `/static` 경로, `conftest` 픽스처를 지킵니다.
- **템플릿과 목업:** 4개 화면의 구조, 클래스, 문구, `<title>`이 목업과 같습니다. 홈과 입력 오류 화면에 헤더가 없는 것도 목업과 같습니다. `style.css`는 목업의 style 블록과 한 글자도 다르지 않고, `copy.js`도 목업 스크립트와 같습니다.
- **입력칸 출력:** `home.html`의 `{%- if %}` 공백 제어로 오류가 없을 때와 있을 때 모두 `<input>`이 올바르게 렌더링됩니다.

**구현자가 계획 없이 한 판단 4가지 (모두 타당)**
1. **lone surrogate를 `MSG_INVALID_CHARS`로 거절:** 타당합니다. 거르지 않으면 sqlite3에 넣을 때 `UnicodeEncodeError`가 나서 500이 됩니다. 다만 문구가 실제 원인과 맞지 않고 문서와 테스트에 반영되지 않았습니다(R-1, R-2).
2. **`urlsplit`의 `ValueError`를 `MSG_NO_HOST`로 거절:** 500을 막는다는 점에서 타당합니다. 다만 스킴 검사보다 먼저 실행되어 계획에 정한 검사 순서와 어긋납니다(R-1).
3. **`api.py`에 `MSG_NOT_OBJECT` 추가:** 타당합니다. API에만 쓰는 문구라 `api.py`에 두는 것이 맞고, D-4의 `{"detail": "<한국어 문구>"}` 형식도 지킵니다.
4. **`web.py`에서 `Jinja2Templates` 직접 생성:** 타당합니다. `main`이 `web`을 import하므로 순환 import를 피하는 선택입니다. 템플릿 경로가 두 곳에 정의되는 문제만 남습니다(R-4).

## 지적 목록

### R-1 [minor] `validate_url`의 추가 예외 분기가 검사 순서를 바꾸고, 문구와 문서가 실제 동작과 다름
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\src\shortlink\validation.py:49-58` (docstring 32-39)
- 문제:
  - `urlsplit`가 `ValueError`를 던지면 스킴 검사(계획의 5번)보다 먼저 `MSG_NO_HOST`가 나옵니다. 예를 들어 `ftp://[abc`는 `MSG_BAD_SCHEME`이 아니라 "도메인이 없습니다"를 받습니다.
  - NFKC 정규화에서 걸리는 netloc(예: `https://example.com\uFF03@x`)은 도메인이 있는데도 "도메인이 없습니다"라고 안내합니다.
  - lone surrogate는 공백도 제어 문자도 아닌데 "공백이나 제어 문자를 넣을 수 없습니다"라고 안내합니다.
  - 두 분기 모두 docstring의 검사 순서 1~6과 계획 3절 표에 없습니다.
- 근거: 계획 3절은 검사 순서를 "5 스킴 → 6 호스트"로 정했습니다. 상태 코드는 둘 다 422라서 수용 기준은 어기지 않습니다.
- 수정 제안:
  - `ValueError`를 잡을 때 스킴을 먼저 따로 확인합니다. 예: `value.partition(":")[0].lower() not in ALLOWED_SCHEMES`이면 `MSG_BAD_SCHEME`, 아니면 `MSG_NO_HOST`. 이렇게 하면 계획의 순서가 유지됩니다.
  - 두 분기를 docstring에 적고, 계획 6절에 D-10, D-11로 기록하도록 메인에 요청합니다. 계획 문서는 리뷰어나 구현자가 고치는 대상이 아닙니다.
  - 문구는 지금 것을 쓸 수도 있고, 일반 문구(예: "올바른 URL 형식이 아닙니다.")를 새로 만들 수도 있습니다. 어느 쪽이든 결정으로 남깁니다.

### R-2 [minor] 추가 분기와 D-9 재시도 경로를 검증하는 테스트가 없음
- 위치:
  - `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\tests\test_validation.py`
  - `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\tests\test_api_links.py`
  - (`src/shortlink/links.py:38-49`)
- 문제: 다음 경우를 다루는 테스트가 없습니다. `tests/`에서 `surrogate`, `IntegrityError`, `monkeypatch`를 검색해도 결과가 없습니다.
  - lone surrogate 입력(`{"url": "https://a.com/\ud800"}` → 422)
  - `urlsplit`의 `ValueError` 입력(`http://[abc` → 422)
  - D-9 코드 충돌 재시도(충돌 뒤 새 코드로 성공)
  - 10번 모두 충돌하는 경우(`RuntimeError`)
- 근거: 앞의 두 분기는 500을 막으려고 넣은 것인데, 테스트가 없으면 나중에 리팩터링할 때 조용히 다시 500이 될 수 있습니다. D-9는 계획에 적힌 결정인데 검증되지 않았습니다.
- 수정 제안: `test_validation.py`와 `test_api_links.py`에 두 입력을 넣은 parametrize 케이스를 추가합니다. `monkeypatch`로 `shortlink.links.generate_code`를 고정된 값 순서로 바꿔서 충돌 후 재시도와 10번 소진을 각각 검증하는 단위 테스트를 추가합니다.

### R-3 [minor] 아주 깊게 중첩된 JSON 본문이 422가 아니라 500이 됨
- 위치: `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\src\shortlink\api.py:28-31`
- 문제: `await request.json()`은 내부에서 `json.loads`를 씁니다. `[[[[...]]]]`처럼 수천 단계 중첩된 본문을 받으면 `RecursionError`가 나는데, 이것은 `ValueError`의 하위 클래스가 아니라서 잡히지 않고 500이 됩니다.
- 근거: 계획 3절 api.py 항목은 "본문이 JSON이 아니거나 객체가 아니면 422"로 정했습니다. 이 본문은 문법상 올바른 JSON 배열이므로 422여야 합니다. 서비스 거부(DoS) 측면은 security 담당입니다.
- 수정 제안: `except (ValueError, RecursionError):`로 넓혀서 `MSG_NOT_OBJECT`로 422를 돌려주고, 회귀 테스트(`content=b"[" * 100000`)를 하나 추가합니다.

### R-4 [minor] 템플릿 경로가 두 곳에 정의되고 `main.TEMPLATES_DIR`은 쓰이지 않음
- 위치:
  - `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\src\shortlink\web.py:18`
  - `<HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r2\src\shortlink\main.py:26`
- 문제: `web.py`가 `Path(__file__).resolve().parent / "templates"`를 따로 계산합니다. 그래서 `main.py`의 `TEMPLATES_DIR`은 아무 데서도 쓰이지 않는 상수가 됐고, 경로를 정하는 곳이 둘이 됐습니다.
- 근거: `web.py`에서 직접 생성하는 것은 순환 import를 피하려는 합리적인 선택입니다. 다만 나중에 경로를 바꾸면 한쪽만 고쳐질 위험이 있습니다.
- 수정 제안 (둘 중 하나):
  - 템플릿 경로 상수를 순환이 생기지 않는 모듈(예: `web.py` 자체나 새 `paths.py`)에 두고, `main.py`는 그것을 import해서 `TEMPLATES_DIR`이라는 이름을 유지합니다.
  - 지금 구조를 유지하고 `web.py`에 "`main.TEMPLATES_DIR`과 같은 경로"라는 주석을 남깁니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)
