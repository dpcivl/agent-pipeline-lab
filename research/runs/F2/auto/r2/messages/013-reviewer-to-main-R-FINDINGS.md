---
seq: 13
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T08:23:15.311Z"
agent: "reviewer"
agent_id: "a86f8f7f6c2753f24"
turn: 1
reply_to: 8
chars: 5542
tokens_est: 2632
wait_s: null
---

## 결과: 지적 4건 (blocker 0, major 0, minor 4)

검토 범위는 `git diff 663d5ad b42b3bb` 전체(src 9개, tests 7개, 계획과 목업)다. 파일은 수정하지 않았고, 테스트도 다시 돌리지 않았다(394개 통과는 메인 보고를 그대로 따름).

**문제없음으로 확인한 것**
- 별칭 검증: 검사 순서(문자열 → 길이 → 문자 → 하이픈 → 예약어)와 문구 상수가 계획 3.1과 같다. ASCII만 허용하는 `fullmatch`라서 끝의 `\n`, 전각 숫자, 아랍 숫자도 막힌다.
- 저장: `create(alias)`는 INSERT 한 번만 하고, 충돌 시 재시도하지 않고 `AliasTakenError`를 던진다. `record_click`은 SQL 안에서 `clicks + 1`로 늘리고, 같은 트랜잭션에서 다시 읽는다.
- F1 DB 이전: `PRAGMA table_info`로 열을 확인하고 `ALTER TABLE`로 추가하므로 여러 번 불러도 안전하다. 기존 행은 `clicks=0`, `last_accessed_at=NULL`로 시작한다. `test_migration.py`가 F1 스키마로 직접 만든 DB에서 302, 0부터 세기, 재시작 뒤 유지, 별칭 409까지 확인한다.
- F1 호환:
  - `Link`에 새로 붙은 필드는 기본값이 있어 F1 호출부가 그대로 동작한다.
  - `GET /{code}`는 코드 형식으로 미리 거르지 않고 DB 조회로 판단한다.
  - F1 테스트 파일은 수정되지 않았다. `test_repository.py`와 `test_validation.py`는 뒤에 테스트를 덧붙이기만 했다.
- 라우트: `/links/{code}/stats`와 `/stats/{code}`는 두 단계 경로라서 `GET /{code}`와 겹치지 않는다.
- 템플릿과 목업:
  - `home.html`, `result.html`, `stats.html`의 구조, 문구, class, `<title>`, aria 속성이 F2 목업 6개와 같다. 오류 대상 칸에만 `aria-invalid`가 붙는다.
  - `style.css`는 F2 목업의 `<style>` 블록과 diff를 떠 보니 "공통 스타일 끝" 주석 한 줄만 다르다.
  - `|safe`는 쓰지 않았다.
- 테스트 강도: AC-1~AC-22가 모두 경계값까지 단언한다. 3/4/30/31자, 예약어 9개와 대문자 예약어, 무작위 코드와 같은 별칭의 409, 대소문자 구분, 거절 뒤 행 수, 동시 클릭 40회, 이스케이프와 속성 탈출을 모두 다룬다. AC-23은 기존 F1 테스트가 그대로 통과하는 것으로 확인된다.

## 지적 목록

### R-1 [minor] 비문자열 alias의 422 본문이 계획·목업 문구와 다르고, MSG_ALIAS_NOT_STRING에 API에서 도달할 수 없음 (알려진 판단)
- 위치: `src/shortlink/api.py:30`, `src/shortlink/validation.py:29`, `tests/test_aliases.py:175`
- 문제:
  - `alias: StrictStr | None`이라서 `{"alias": 123}`은 Pydantic 단계에서 FastAPI 기본 422 본문(`detail`이 목록)을 받는다. `validate_alias`의 1번 규칙과 `MSG_ALIAS_NOT_STRING` 문구는 API 경로에서 실행되지 않는다.
  - 같은 이유로 `{"url": "ftp://x", "alias": 1}`처럼 둘 다 틀리면 `MSG_SCHEME`가 아니라 기본 본문이 나간다. D-2의 "URL 먼저"가 이 경우에는 지켜지지 않는다.
- 근거:
  - 계획 3.3: "422: … `alias`가 문자열이 아님(숫자, 배열 등) … 검증 실패 본문은 `{"detail": "<문구>"}`"
  - 목업 `F2-index.html` 문구 표: "1. 문자열 아님 (API만) 422 alias는 문자열이어야 합니다."
  - 반대로 계획 3.3은 `StrictStr | None`을 직접 지정하고 있어 계획 안에서도 서로 맞지 않는다. F1 `url`도 같은 구조다(F1 계획 3.3은 "그 밖의 형식 오류는 FastAPI 기본 422 본문").
  - 설계서 AC-5와 AC-9는 상태 코드 422와 저장 없음만 요구하고, 이 둘은 지켜진다.
- 판단: 수용 기준 위반은 아니고 F1과도 일관되므로 minor다. 다만 계획·목업과 구현이 어긋난 채 남아 있고, 테스트는 상태 코드만 봐서 어느 쪽이 맞는지 고정되어 있지 않다.
- 수정 제안 (둘 중 하나로 문서와 코드를 맞춘다):
  - (권장) 현재 동작을 유지한다. 계획에 결정 D-12를 추가한다: "비문자열 alias는 F1 url과 같이 FastAPI 기본 422 본문. `MSG_ALIAS_NOT_STRING`은 `validate_alias` 단독 호출용". 목업 index의 "(API만)" 행도 고친다. `test_alias_that_is_not_a_string_is_rejected`에 `isinstance(response.json()["detail"], list)` 단언을 넣어 동작을 고정한다.
  - 또는 문구 본문을 내보낸다. `alias: object = None`으로 받아 `validate_alias`에 넘기거나, `RequestValidationError` 핸들러를 둔다. 이 경우 F1 url과 동작이 달라지므로 F1 쪽도 같이 정해야 한다.

### R-2 [minor] 동시 리다이렉트에서 last_accessed_at이 최대 1초 뒤로 갈 수 있음
- 위치: `src/shortlink/repository.py:114-118`
- 문제:
  - 현재 시각을 트랜잭션 밖(쓰기 잠금을 얻기 전)에서 계산해 `?`로 넘긴다.
  - 경합 순서: 요청 A가 `…:01`을 계산하고 잠금을 기다린다. 그사이 요청 B가 `…:02`로 먼저 갱신한다. 이어서 A가 `…:01`로 덮어쓴다. 결과적으로 "마지막 접근 시각"이 실제 마지막 접근보다 이른 값이 된다.
  - 클릭 수는 SQL 안에서 늘리므로 정확하다.
- 근거: 계획 3.2는 "클릭을 잃지 않게" SQL 안에서 늘리라고 한다. 시각도 같은 원칙으로 다루는 편이 맞다.
- 수정 제안: `last_accessed_at = MAX(COALESCE(last_accessed_at, ''), ?)`로 바꾼다. 같은 형식의 ISO 문자열이라 사전순 비교가 곧 시간순이다. 또는 SQL의 `strftime('%Y-%m-%dT%H:%M:%SZ','now')`로 시각을 계산한다. 영향이 작아서 다음 라운드로 미뤄도 된다.

### R-3 [minor] init_schema의 열 확인과 ALTER가 원자적이지 않음 (여러 워커가 동시에 시작할 때)
- 위치: `src/shortlink/db.py:43-47`
- 문제:
  - Python sqlite3는 DDL 앞에 트랜잭션을 자동으로 열지 않는다. 그래서 `PRAGMA table_info` 조회와 `ALTER TABLE` 사이가 보호되지 않는다.
  - F1 DB로 `uvicorn --workers N`처럼 여러 프로세스가 동시에 `create_app()`을 실행하면, 두 프로세스가 모두 "열 없음"을 본다. 늦게 ALTER한 쪽이 `sqlite3.OperationalError: duplicate column name`으로 시작에 실패한다.
  - 이 상태에서 다시 시작하면 정상 동작한다. 단일 프로세스 기본 실행 명령에서는 문제가 생기지 않는다.
- 근거: 계획 D-11 "앱 시작 시 자동 이전", 3.2 "여러 번 불러도 안전해야 한다". 동시에 부르는 경우는 다루지 않았다.
- 수정 제안 (다음 중 하나):
  - 이전 부분을 `BEGIN IMMEDIATE` … `COMMIT`으로 감싼다. SQLite DDL은 트랜잭션에 들어간다.
  - ALTER의 `OperationalError` 중 "duplicate column"만 무시하고 넘어간다.
  - 덧붙여 `clicks`만 있고 `last_accessed_at`이 없는 부분 이전 상태도 테스트 하나로 고정해 두면 좋다.

### R-4 [minor] web.py 독스트링이 F2 동작을 반영하지 않음
- 위치: `src/shortlink/web.py:134` (`follow_link`), 모듈 독스트링 3-9줄
- 문제:
  - `follow_link`의 독스트링은 여전히 "302 … if the code exists, else 404"뿐이다. 리다이렉트마다 클릭을 센다는 것(`record_click`), 404는 세지 않는다는 것(AC-15)이 빠져 있다.
  - 모듈 독스트링도 "following docs/plans/mockups/F1-*.html"이고, `home.html` 설명에 별칭 입력칸과 409 화면이 없다.
- 근거: 같은 파일의 `stats_page`와 `shorten_form`은 F2 동작을 독스트링에 적었다. 이 둘만 남아 있어 읽는 사람이 GET에 부수 효과(DB 쓰기)가 있다는 것을 놓치기 쉽다.
- 수정 제안: `follow_link` 독스트링에 "Counts one click via record_click (none on 404); see F2 plan D-9"를 넣는다. 모듈 독스트링의 목업 참조를 `F1-*.html`, `F2-*.html`로 고친다.

## 참고 (지적 아님)
- 폼에 공백만 든 별칭(`"    "`)은 D-1/D-3에 따라 422(문자 규칙)가 되고, 구현도 그렇게 동작한다. 다만 이 경계를 확인하는 테스트는 없다. 필요하면 `test_web_f2.py`에 하나 추가하면 된다.
- `docs/service.md`는 아직 F1만 설명한다. 갱신은 doc-keeper 담당(`.claude/agents/doc-keeper.md`)이라 이번 리뷰 범위에서 뺐다.

## 관련 파일
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\api.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\repository.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\db.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\web.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\src\shortlink\validation.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\tests\test_aliases.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\docs\plans\F2-plan.md
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F2-auto-r2\docs\plans\mockups\F2-index.html
