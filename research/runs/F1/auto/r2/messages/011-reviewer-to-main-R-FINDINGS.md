---
seq: 11
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T05:16:22.816Z"
agent: "reviewer"
agent_id: "af6cc410cc44344fc"
turn: 1
reply_to: 8
chars: 4531
tokens_est: 2245
wait_s: null
---

## 결과: 지적 4건 (blocker 0, major 1, minor 3)

검토 범위는 `git diff e8f75ad..166f2b6` 전체(src, templates, static, tests, plan/decisions/mockups)입니다. 규칙에 따라 읽기만 했고, 서버 실행이나 pytest/ruff 실행은 하지 않았습니다. 이전 판단의 근거는 코드를 읽어서 얻었고, 설치된 Starlette 소스도 함께 읽었습니다.

AC-1~AC-23은 코드와 테스트 모두 빠짐없이 대응합니다. 고정 계약도 지켰습니다. `create_app` 시그니처는 그대로이고, 스키마 준비와 라우터 등록이 이 함수 안에서 끝납니다. `Settings`는 바뀌지 않았고, conftest에는 `count_links` 픽스처만 추가되었습니다. 템플릿 4개는 목업 4개와 마크업 구조, 클래스 이름, 문구, `<title>`이 일치하고, style.css는 목업 `<style>` 블록에서 목업 전용 부분을 뺀 것과 같습니다. `|safe`와 `Markup`은 쓰지 않았고 자동 이스케이프가 켜져 있습니다. D-1~D-9 결정에는 문제가 없다고 봅니다. D-2(공백·제어 문자 거절)와 D-3(비ASCII만 퍼센트 인코딩)은 Location 헤더 안전성 측면에서 근거가 타당합니다.

## 지적 목록

### R-1 [major] 짝 없는 서로게이트가 든 URL이 검증을 통과해 POST /links가 500을 냄 (implementer 질문에 대한 판단)
- 위치: src/shortlink/validation.py:37-48, src/shortlink/api.py:24·33, src/shortlink/storage.py:53-56
- 문제: 질문에 적힌 문제가 실제로 생깁니다. `{"url": "https://example.com/\ud800"}`처럼 JSON 이스케이프로 보내도 되고, 본문에 UTF-8로 인코딩된 서로게이트 바이트 `ED A0 80`을 그대로 넣어도 됩니다. 두 경우 모두 `request.json()`이 짝 없는 서로게이트가 든 `str`를 돌려줍니다. Starlette는 `json.loads(body)`를 호출하고, 표준 `json.loads`는 bytes를 `'surrogatepass'`로 디코딩합니다. 이 문자는 `isspace()`가 아니고 `ord >= 0x20`이라서 D-2 검사에 걸리지 않습니다. `urlsplit`과 `hostname`도 예외 없이 통과합니다. 그 결과 `repository.create()`에서 sqlite3가 파라미터를 UTF-8로 바꾸다 `UnicodeEncodeError`를 내고, 아무도 잡지 않아 500이 됩니다. 커밋 전에 실패하므로 저장은 되지 않습니다. 폼 경로(`POST /`)는 영향이 없습니다. Starlette formparsers.py:115의 `unquote_plus`가 기본값 `errors='replace'`로 U+FFFD로 바꾸기 때문입니다.
- 근거: 클라이언트 입력만으로 미처리 예외와 500을 일으킬 수 있습니다. 이런 문자열은 UTF-8로 저장할 수 없으니 "URL은 받은 그대로 저장"도 지킬 수 없습니다. 거절하는 수밖에 없고, D-4의 방침에 맞추면 잘못된 입력은 422여야 합니다. 설계서의 거절 목록에는 없는 경우이므로 결정 기록도 필요합니다.
- 수정 제안: `validate_url`의 D-2 검사 근처에서 서로게이트(U+D800~U+DFFF)를 거절하고 422를 돌려주세요. 예를 들면 `try: value.encode("utf-8") except UnicodeEncodeError: raise URLValidationError(...)`입니다. 문구는 기존 "URL에 공백이나 제어 문자를 넣을 수 없습니다."를 다시 쓰거나 "URL에 사용할 수 없는 문자가 있습니다." 같은 새 문구를 정하면 됩니다. `validate_url` 안에 두어야 API와 폼이 같은 규칙을 씁니다. `docs/plans/F1-decisions.md`에 D-10으로 기록하고, test_api.py에 테스트 두 개를 추가해 주세요. 하나는 `content=b'{"url": "https://example.com/\\ud800"}'`를 보내 422와 행 수 0을 확인하고, 다른 하나는 원시 바이트 `\xed\xa0\x80`을 넣은 경우를 확인합니다.

### R-2 [minor] async 핸들러 안에서 동기 sqlite3 I/O를 호출함
- 위치: src/shortlink/api.py:33, src/shortlink/web.py:51·62
- 문제: `async def` 핸들러가 `repository.create()`와 `get()`을 직접 부릅니다. 이 메서드들은 `sqlite3.connect`, INSERT, commit을 동기로 실행하므로 그동안 이벤트 루프가 멈춥니다. 디스크가 느리거나 쓰기 잠금을 기다리는 동안(sqlite 기본 timeout 5초) 다른 요청도 모두 함께 멈춥니다.
- 근거: FastAPI의 async 핸들러는 이벤트 루프 위에서 바로 실행됩니다. 계획서가 `async def`를 정한 이유는 `await request.json()`과 `await request.form()` 때문이었고, DB 호출을 루프에서 실행하라는 의도는 아니었습니다.
- 수정 제안: `await run_in_threadpool(repo.create, url)`처럼 감싸 주세요(`starlette.concurrency`). `follow`는 await할 것이 없으니 `def`로 바꿔도 됩니다. F1 규모에서는 당장 장애가 날 수준은 아니어서 minor로 분류했습니다.

### R-3 [minor] 복사가 실패하거나 클립보드 API가 없으면 사용자에게 아무 반응이 없음
- 위치: src/shortlink/static/copy.js:5-7, 13
- 문제: `navigator.clipboard`가 없을 때와 `writeText`가 거부됐을 때 모두 아무 일도 하지 않습니다. `navigator.clipboard`는 보안 컨텍스트에서만 제공되므로 localhost가 아닌 http 배포(`SHORTLINK_BASE_URL=http://...`)에서는 없습니다. 이런 환경에서는 버튼을 눌러도 아무 반응이 없어 사용자가 복사됐는지 알 수 없습니다.
- 근거: 설계서는 "복사" 버튼이 단축 URL을 클립보드에 복사한다고 정했습니다. 오류 없이 넘어가는 것은 의도된 동작(주석)이지만, 이 경우 기능 자체가 조용히 사라집니다.
- 수정 제안: 실패할 때 단축 URL 링크의 텍스트를 선택해 수동 복사를 돕거나, `document.execCommand("copy")`로 대체하세요. 아니면 "복사하지 못했습니다" 같은 짧은 상태 문구를 보여 주세요. 목업은 성공 경로만 정했으므로, 문구를 추가한다면 결정 기록에 남겨 주세요.

### R-4 [minor] 템플릿 디렉터리 경로가 두 곳에 정의됨
- 위치: src/shortlink/main.py:25 (`TEMPLATES_DIR`, 사용되지 않음), src/shortlink/web.py:14
- 문제: main.py의 `TEMPLATES_DIR`는 스켈레톤에 처음부터 있던 상수인데 어디서도 쓰지 않습니다. 실제 템플릿 객체는 web.py에서 같은 경로를 다시 계산해 씁니다. 그래서 경로의 기준이 둘로 갈립니다.
- 근거: 나중에 경로를 바꿀 때 한쪽만 고칠 위험이 있습니다. main이 web을 import하므로 web이 main에서 가져오면 순환 import가 됩니다.
- 수정 제안: 경로 상수를 순환이 없는 모듈(예: 새 `shortlink/paths.py`나 `shortlink/__init__.py`)로 옮겨 main.py와 web.py가 함께 쓰게 하세요. 아니면 main.py의 상수를 쓰지 않는 상수라고 주석으로 밝혀 두세요. main.py는 고정 계약 파일이지만 상수를 옮기는 것은 확장 범위에 들어갑니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)

관련 파일:
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\src\shortlink\validation.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\src\shortlink\api.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\src\shortlink\storage.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\src\shortlink\web.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\src\shortlink\main.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\src\shortlink\static\copy.js
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\docs\plans\F1-decisions.md
