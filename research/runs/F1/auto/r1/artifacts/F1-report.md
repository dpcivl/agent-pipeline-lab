# F1 실행 보고서 — 단축 URL 생성과 리다이렉트

- 모드: auto
- 브랜치: `run/F1-auto-r1` (기준 커밋 `0e781ba`)
- 설계서: `docs/features/F1.md` v2
- 종료 상태: **완료** — 테스트 253개 통과, 리뷰 2라운드 만에 blocker·major 0건

## 1. 단계별 진행 기록

| 단계 | 내용 | 호출한 에이전트 | 결과 |
|---|---|---|---|
| 0 | 실행 위치 확인 | — | `RUN_WORKTREE` |
| 1 | 계획(`F1-plan.md`), 해석 결정(`F1-decisions.md` D-1~D-7), 스텁 5개(`db`, `validation`, `links`, `api`, `web`), `main.py` 연결, 목업 5개 작성. H1은 스스로 승인 | 메인 | 체크포인트 `a01a065` |
| 2 | 구현과 테스트 작성을 병렬로 진행 | implementer, test-writer | 체크포인트 `62a0bf3` (테스트 216개) |
| 3 | 테스트 루프 1회차 | tester | PASS 216/216, ruff 통과 |
| 4-1 | 리뷰 1라운드 (체크포인트 `62a0bf3`) | reviewer, qa, security | blocker 0, major 2, minor 9 (병합 후) |
| 4-1 | H3 우선순위 결정, D-3 개정, D-8 추가 | 메인 | `F1-decisions.md`의 H3 절 |
| 4-1 | major 수정과 테스트 보강을 병렬로 진행 | implementer, test-writer | — |
| 4-1 | 재테스트 | tester | PASS 253/253 |
| 4-1 | 체크포인트 | 메인 | `5c61fc4` |
| 4-2 | 리뷰 2라운드 (체크포인트 `5c61fc4`, 직전 `62a0bf3`) | reviewer, qa, security | blocker 0, major 0, minor 11 → 루프 종료 |
| 5 | H4 커밋 전 확인 (auto: 바로 진행) | — | — |
| 6 | 실행 보고서 작성 | 메인 | 이 문서 |
| 7 | 서비스 문서, CHANGELOG, 기능 커밋 | doc-keeper | — |

### 체크포인트 커밋

| 해시 | 메시지 |
|---|---|
| `a01a065` | wip(F1): 1 계획, 스켈레톤, 목업 |
| `62a0bf3` | wip(F1): 2 구현과 테스트 작성 |
| `5c61fc4` | wip(F1): 4 리뷰 1라운드 수정 |

## 2. 루프 횟수

- 테스트 루프: 1회. 첫 실행에서 PASS했고 수정 회차는 0회였다. 리뷰 수정 뒤 재테스트를 1회 더 했고 PASS였다.
- 리뷰 라운드: 2라운드

### 라운드별 지적 수

| 라운드 | 에이전트 | blocker | major | minor |
|---|---|---|---|---|
| 1 | reviewer | 0 | 1 (R-1) | 4 (R-2~R-5) |
| 1 | qa | 0 | 0 | 0 |
| 1 | security | 0 | 0 → 1 (S-1을 올림) | 6 → 5 |
| 1 | **합계** | **0** | **2** | **9** |
| 2 | reviewer | 0 | 0 | 5 (R-2~R-6) |
| 2 | qa | 0 | 0 | 0 |
| 2 | security | 0 | 0 | 6 (S-2~S-7) |
| 2 | **합계** | **0** | **0** | **11** |

### 수정한 지적 (1라운드)

- **R-1 [major]** 리다이렉트 `Location`에서 `|`, `<`, `{` 같은 ASCII 문자까지 퍼센트 인코딩되어 AC-10과 어긋났다.
  - 수정: `web.location_header`를 만들어 출력 가능한 ASCII는 그대로 두고 비ASCII만 인코딩한다(D-3 개정). 2라운드에서 해결을 확인했다.
- **S-1 [minor→major]** 짝이 없는 서로게이트(`\ud800`)가 든 URL을 보내면 500이 났다.
  - 수정: 검증 4a 단계에서 422로 거절한다(D-8). 2라운드에서 해결을 확인했다.

## 3. 미해결 지적

blocker와 major 중 미해결은 **없음**.

### minor 지적 (고치지 않고 기록만)

| id | 내용 | 비고 |
|---|---|---|
| R-2 | 코드 충돌 재시도와 10회 실패 시 `RuntimeError` 경로에 테스트가 없음 | |
| R-3 | `urlsplit`의 `ValueError` 분기(`https://[::1`)에 테스트가 없고, 스킴 판정 로직이 두 곳에 있음 | |
| R-4 | async 핸들러 안에서 동기 sqlite3 I/O를 실행함 | 규모가 커지면 `def` 또는 스레드풀로 바꾼다 |
| R-5 | `TEMPLATES_DIR`가 `main.py`와 `web.py`에 따로 정의됨 | |
| R-6 | 새 테스트의 의미 없는 assert 조건과 낡은 주석 (`test_api_validation.py:202`, `test_validation.py:161`) | 2라운드에 새로 나옴 |
| S-2 | bidi 제어, C1 제어, U+2028 같은 표시를 속이는 문자를 허용함 | 화면 표시만 속일 수 있고, Location은 인코딩된다 |
| S-3 | 자기 참조 루프와 userinfo 위장을 막지 않음 | 정책 사항 |
| S-4 | 인증, 요청 수 제한, 본문 크기 제한이 없음 | F3 범위 |
| S-5 | 보안 응답 헤더(CSP, nosniff 등)가 없음 | |
| S-6 | `/docs`, `/redoc`, `/openapi.json`이 공개됨 | |
| S-7 | `\`를 Location에 그대로 내보내서 `urlsplit`과 브라우저의 호스트 해석이 다름 (예: `https://evil.com\@allowed.com/`) | 2라운드에 새로 나옴. 지금은 호스트 정책이 없어 악용할 경로가 없다. **호스트 기반 차단(S-3)을 도입하기 전에 먼저 `\`를 거절해야 한다** |

## 4. 설계서 해석 결정

자세한 내용은 `docs/plans/F1-decisions.md`에 있다.

| id | 결정 |
|---|---|
| D-1 | 스킴은 대소문자를 무시하고 검사한다. 저장은 받은 그대로 한다 |
| D-2 | 공백과 제어 문자(U+0000–U+001F, U+007F)가 든 URL은 422로 거절한다 |
| D-3 (개정) | Location에서 출력 가능한 ASCII는 그대로 두고, 비ASCII만 UTF-8 퍼센트 인코딩한다 |
| D-4 | API 오류는 `{"detail": "<한국어 문구>"}`이고, 화면에도 같은 문구를 보여 준다 |
| D-5 | 없는 코드는 형식과 상관없이 항상 404 HTML 화면을 보여 준다 |
| D-6 | 입력칸은 `type="text" inputmode="url"`이고 `required`를 붙이지 않는다 |
| D-7 | 폼에 `url` 필드가 없으면 빈 값으로 보고 422 HTML 화면을 보여 준다 |
| D-8 | 짝이 없는 서로게이트가 든 URL은 422 "URL에 쓸 수 없는 문자가 들어 있습니다."로 거절한다 |
| H3 | 1라운드 우선순위: R-1과 S-1(major로 올림)을 고치고, 나머지는 기록만 한다 |

테스트 루프에서 spec_ambiguous(H2)로 분류된 실패는 없었다.

## 5. 종료 상태

**완료.**
- 수용 기준 AC-1~AC-23을 모두 충족했다. 테스트로 확인했고, qa도 서버를 띄워 블랙박스로 확인했다.
- `uv run pytest` 253개가 통과했다.
- `ruff check`, `ruff format --check`, `bandit` 모두 지적이 없다.

## 6. 결과 확인 방법

1. 테스트를 실행한다.

   ```bash
   uv run pytest
   ```

2. 서버를 띄운다. DB 파일 `shortlink.db`가 현재 폴더에 생긴다.

   ```bash
   uv run uvicorn shortlink.main:create_app --factory
   ```

3. 브라우저에서 다음 순서로 확인한다.
   1. http://localhost:8000/ 을 연다. 홈 화면에 "ShortLink" 제목, 설명, "줄일 URL" 입력칸, "줄이기" 버튼이 보이는지 본다.
   2. `https://www.example.com/articles?id=1`을 넣고 "줄이기"를 누른다. 결과 화면에 단축 URL 링크, 원래 URL, "복사" 버튼, "다른 URL 줄이기" 링크가 보이는지 본다.
   3. "복사"를 누른다. 버튼이 "복사됨"으로 바뀌고 클립보드에 단축 URL이 들어가는지 본다.
   4. 단축 URL 링크를 누른다. example.com으로 이동하는지 본다.
   5. 홈에서 `ftp://example.com`을 제출한다. 빨간 오류 메시지가 나오고 입력값이 남아 있는지 본다. 빈 값으로 제출해서 "URL을 입력해 주세요."가 나오는지도 본다.
   6. http://localhost:8000/nope123 을 연다. "링크를 찾을 수 없습니다" 화면과 "홈으로 가기" 링크가 보이는지 본다.
   7. 브라우저 개발자 도구에서 375px 폭으로 바꾼다. 가로 스크롤이 생기지 않는지 본다.
4. API를 확인한다.

   ```bash
   curl -i -X POST http://localhost:8000/links -H "content-type: application/json" -d "{\"url\": \"https://example.com/path?q=1\"}"
   ```

   201 응답의 `short_url`로 `curl -i <short_url>`을 보내 302와 `Location`을 확인한다.

5. 목업과 비교하려면 `docs/plans/mockups/F1-index.html`을 브라우저로 연다.
