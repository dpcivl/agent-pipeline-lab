---
seq: 12
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-30T00:00:18.545Z"
agent: "reviewer"
agent_id: "a4da8d475ce801a88"
turn: 1
reply_to: 9
chars: 4599
tokens_est: 2214
wait_s: null
---

## 결과: 지적 4건 (blocker 0, major 0, minor 4)

F2 변경분(`git diff 79faa29..e9f25fe`)에서 수용 기준 위반, 계획 결정(D-F2-1~9)과 어긋나는 구현, F1 호환성 문제는 찾지 못했습니다. 지적 4건은 모두 minor입니다. `uv run ruff check src tests`와 `ruff format --check`는 통과했습니다. 테스트는 다시 돌리지 않았고, 메인이 알려 준 405개 통과 결과를 그대로 받아들였습니다.

## 지적 목록

### R-1 [minor] 스텁 시절 docstring이 남아 있어 실제 동작과 다름
- 위치: `src/shortlink/web.py:77`, `src/shortlink/web.py:3`, `src/shortlink/api.py:45-50`
- 문제:
  - `shorten_form` docstring에 "F2 (to add): ..."가 그대로 남아 있습니다. 이미 구현된 기능인데 할 일처럼 읽힙니다.
  - 모듈 docstring은 템플릿이 `docs/plans/mockups/F1-*.html`만 따른다고 적혀 있습니다.
  - `create_link` docstring은 본문을 `{"url": ...}`로만 설명하고, 422만 언급합니다. `alias` 필드와 409(`MSG_ALIAS_TAKEN`)는 빠져 있습니다.
- 근거: 계획 3.3절에 따르면 `POST /links`는 `alias`를 받고 중복이면 409를 돌려줍니다. 코드는 그렇게 동작하지만 문서 주석만 예전 상태입니다.
- 수정 제안: "(to add)"를 지우고 현재형으로 고칩니다. `create_link` docstring에 `alias` 처리(생략·null이면 무작위, `""`이면 422)와 409를 적습니다. 모듈 docstring에 F2 목업도 함께 적습니다.

### R-2 [minor] 통계 API 404 문구가 리터럴로 중복됨
- 위치: `src/shortlink/api.py:95` (docstring `:91`에도 같은 문자열)
- 문제: `"링크를 찾을 수 없습니다."`가 하드코딩되어 있습니다. 다른 사용자 노출 문구는 모두 `validation.py`의 `MSG_*` 상수로 관리합니다. `not_found.html` 제목도 같은 문구라서 한쪽만 바뀌면 화면과 API 문구가 달라집니다.
- 근거: D-F2-6이 이 문구를 고정 계약처럼 정했습니다. 테스트(`tests/test_stats.py:22`)도 같은 문자열을 따로 정의해 두고 있습니다.
- 수정 제안: `MSG_LINK_NOT_FOUND` 같은 상수를 만들어 api.py에서 씁니다. F3에서 리팩터링할 때 정리해도 됩니다.

### R-3 [minor] F1 DB 마이그레이션의 확인(PRAGMA)과 변경(ALTER)이 원자적이지 않음
- 위치: `src/shortlink/db.py:44-48`
- 문제: Python 3.12 sqlite3의 기본(레거시) 트랜잭션 모드는 DDL 앞에 BEGIN을 걸지 않습니다. 그래서 `PRAGMA table_info` 확인과 `ALTER TABLE ... ADD COLUMN`이 각각 자동 커밋으로 실행됩니다. 여러 프로세스가 F1 DB로 동시에 시작하면(예: `uvicorn --workers 2`) 둘 다 "컬럼 없음"으로 판단할 수 있습니다. 이때 늦게 실행된 쪽이 `OperationalError: duplicate column name: clicks`를 내고 앱 시작에 실패합니다.
- 근거: 계획 3.2절은 "`init_schema()`는 계속 여러 번 불러도 안전해야 한다"고 합니다. 순차 호출은 테스트(`test_init_schema_is_safe_to_call_repeatedly_and_keeps_clicks`, `test_f1_database_survives_repeated_startup`)로 확인되지만, 동시 시작은 보장되지 않습니다. 업그레이드할 때 딱 한 번 생기는 좁은 경쟁이라 minor로 봤습니다.
- 수정 제안: 둘 중 하나를 고릅니다.
  - 컬럼 확인과 ALTER를 `BEGIN IMMEDIATE ... COMMIT`으로 감쌉니다. SQLite에서는 DDL도 트랜잭션 안에서 실행할 수 있습니다.
  - ALTER의 `OperationalError` 중 "duplicate column name"만 무시합니다.

### R-4 [minor] `UPDATE ... RETURNING`은 SQLite 3.35 이상이 필요한데, 이 요구가 어디에도 적혀 있지 않음
- 위치: `src/shortlink/repository.py:113-119`
- 문제: `record_click`은 `RETURNING`을 씁니다. 이 PC의 SQLite는 3.53.1이라 괜찮습니다. 하지만 시스템 libsqlite3에 링크된 Python(예: Debian 11의 3.34)에서는 모든 리다이렉트가 500이 됩니다. `pyproject.toml`과 문서에 이 요구가 없습니다.
- 근거: 계획 3.2절이 RETURNING을 "사용 가능"으로 허용했으므로 쓴 것 자체는 문제가 아닙니다. 지적 대상은 이 실행 환경 요구가 문서에 없다는 점입니다.
- 수정 제안: 둘 중 하나를 고릅니다.
  - `docs/service.md`나 계획 결정 기록에 "SQLite 3.35+ 필요"를 적습니다.
  - 같은 트랜잭션 안에서 UPDATE 뒤 SELECT를 하도록 바꿉니다. `with conn` 안이므로 원자성은 유지됩니다.

## 확인했고 문제 없는 항목
- 별칭 검증(`validation.py`)
  - 규칙 순서와 문구 5개, `MSG_ALIAS_TAKEN`이 계획 3.1절 표와 같습니다.
  - `isascii()`와 `fullmatch`를 함께 써서, 줄바꿈으로 끝나는 별칭(`"abcd\n"`)과 한글·전각 문자를 거절합니다.
  - 예약어는 대소문자를 무시하고 비교합니다(D-F2-4). 공백 제거나 소문자 변환은 하지 않습니다(D-F2-3).
- API
  - `alias: StrictStr | None`: 생략과 null이면 무작위 코드, `""`이면 422입니다(D-F2-2).
  - 검사 순서는 URL → 별칭 → 409입니다(D-F2-5).
  - 통계 API는 6개 필드를 돌려주고, 없는 코드는 404 JSON입니다(D-F2-6).
- 저장
  - 별칭은 미리 SELECT하지 않고 INSERT 한 번의 PK 충돌로 판단합니다. 충돌하면 롤백합니다.
  - TEXT PRIMARY KEY의 BINARY 비교라서 대소문자를 구분합니다(AC-8).
  - `clicks = clicks + 1`로 원자적으로 증가시키고, 없는 코드는 아무것도 바꾸지 않습니다(AC-15).
  - `get()`은 클릭 수를 늘리지 않습니다.
- 리다이렉트
  - 코드 모양(7자 영숫자 등)으로 미리 거르지 않으므로 별칭 코드도 302로 리다이렉트됩니다.
  - 라우터 등록 순서와 두 단계 경로(`/stats/{code}`, `/links/{code}/stats`)가 `GET /{code}`와 겹치지 않습니다.
- F1 DB 호환
  - PRAGMA로 없는 컬럼만 추가합니다. 기존 행은 `clicks=0`, `last_accessed_at=NULL`입니다.
  - 테스트 4개(`tests/test_stats.py:304-372`)가 3컬럼 F1 DB로 앱 시작, 302 리다이렉트, 0→1 증가, 재시작 후 유지를 확인합니다.
- 템플릿과 목업
  - `home.html`, `result.html`, `stats.html`의 구조, 문구, 클래스, `aria-*`, `<time datetime>`, "아직 없음", 천 단위 쉼표, 제목이 F2 목업과 일치합니다. 홈 화면의 `aria-describedby`는 오류가 없을 때 `alias-hint`, 별칭 오류일 때 `form-error alias-hint`입니다.
  - `style.css`에 덧붙인 블록은 목업의 "F2 추가 스타일" 블록과 바이트 단위로 같습니다(md5 일치).
  - `required`, `pattern`, `maxlength`는 쓰지 않았습니다.
- 테스트
  - 계획 4절의 AC-1~AC-22 대응표를 모두 다룹니다. 각 AC는 경계값, 대소문자 변형, 저장 없음(`count_links`), 이스케이프, CSP·nosniff까지 확인합니다.
  - F1 테스트 파일은 고치지 않았습니다. `conftest.py`는 픽스처(`link_row`, `set_clicks`)만 추가해서 고정 계약 픽스처는 그대로입니다.

## 이전 지적 확인 (2라운드부터)
- 해당 없음 (1라운드)

관련 파일:
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r1\src\shortlink\web.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r1\src\shortlink\api.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r1\src\shortlink\db.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-human-r1\src\shortlink\repository.py
