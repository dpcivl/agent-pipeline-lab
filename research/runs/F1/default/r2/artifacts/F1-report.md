# F1 실행 보고서 — 단축 URL 생성과 리다이렉트 (default 모드)

- 설계서: `docs/features/F1.md` v2
- 브랜치: `run/F1-default-r2` (기능 시작 직전 커밋 `2a793e9`)
- 종료 상태: **완료** — 테스트 224개 통과, 리뷰 1라운드에서 blocker/major 0건

## 1. 단계별 진행 기록

| 단계 | 내용 | 호출한 에이전트 | 결과 |
|---|---|---|---|
| 0 | 실행 위치 확인 | 없음 | `RUN_WORKTREE` |
| 1 | 계획(`F1-plan.md`), 스켈레톤(스텁 8개 모듈, `main.py` 확장), 목업 4개와 인덱스 | 없음 (메인 직접) | 375px 폭에서 가로 스크롤 없음 확인 |
| H1 | 계획·목업 승인 (default = human) | 사람 | 수정 없이 승인 |
| 2 | 구현과 테스트 작성 (병렬) | implementer, test-writer | 둘 다 완료. 테스트 224개 |
| 3 | 테스트 루프 1회차 | tester | PASS (224/0/0), ruff 통과 |
| 4 | 리뷰 1라운드 (병렬) | reviewer, qa, security | blocker 0, major 0, minor 10 → 루프 종료 |
| H3 | 리뷰 1라운드 후 (default = auto) | 메인 | 수정할 blocker/major 없음, minor는 기록만 (D-13) |
| H4 | 커밋 전 확인 (default = auto) | 메인 | 바로 진행 |
| 6 | 실행 보고서, 결정 기록(`F1-decisions.md`) | 없음 (메인 직접) | 이 문서 |
| 7 | 서비스 문서, CHANGELOG, 기능 커밋 | doc-keeper | 아래 기능 커밋 |

### 체크포인트 커밋

| 해시 | 메시지 |
|---|---|
| `52454a2` | wip(F1): 1 계획, 스켈레톤, 목업 |
| `62afa74` | wip(F1): 2 구현과 테스트 작성 (리뷰 1라운드 체크포인트) |

테스트 루프와 리뷰 루프에서 수정이 없었기 때문에 3단계와 4단계 체크포인트는 만들지 않았습니다.

## 2. 루프 집계

- 테스트 루프: 1회 (1회차에 PASS, 실패 분류 없음)
- 리뷰 라운드: 1라운드

| 라운드 | reviewer | qa | security | 합계 |
|---|---|---|---|---|
| 1 | blocker 0 / major 0 / minor 5 | 0 / 0 / 0 | 0 / 0 / 5 | blocker 0 / major 0 / minor 10 |

중복으로 합친 지적은 없습니다. 각 지적이 서로 다른 문제를 다룹니다.

## 3. 미해결 지적

없음 (blocker/major 0건).

## 4. minor 지적 목록 (고치지 않고 기록만 함)

| id | 출처 | 내용 | 후속 제안 |
|---|---|---|---|
| R-1 | reviewer | D-7의 "ASCII URL은 그대로 나간다"는 전제가 사실과 다름. `<`, `>` 같은 ASCII 문자도 `Location`에서 퍼센트 인코딩됨. 이 경우를 고정하는 테스트 없음 | 결정 기록 정정(`F1-decisions.md` D-7 정정에 반영함). `unquote(location) == url`을 확인하는 테스트 추가 |
| R-2 | reviewer | `main.TEMPLATES_DIR`와 `web.get_templates()`가 쓰이지 않거나 중복됨 | 하나로 정리 |
| R-3 | reviewer | 실행 중 결정이 기록되지 않음. `validate_url`의 docstring 4단계가 실제 검사 범위보다 좁게 적혀 있음 | 결정 기록은 `F1-decisions.md`의 D-10~D-12로 반영함. docstring 수정은 남음 |
| R-4 | reviewer | 유니코드 공백·C1 제어 문자 거절과 `urlsplit`의 `ValueError` 분기에 테스트가 없음 | 단위 테스트와 API 422 테스트 추가 |
| R-5 | reviewer | 결과 화면 테스트가 `copy.js` 연결, "원래 URL은 링크가 아님", 각 화면의 `style.css` 연결을 확인하지 않음 | 단언 추가 |
| S-1 | security | 요청 본문 크기에 상한이 없고, 422 응답이 입력 전체를 다시 돌려줌 (30MB JSON을 보내면 30MB 응답) | 본문 크기 상한(예: 16KB 초과 시 413). 422 응답의 `input`을 빼거나 자름 |
| S-2 | security | `POST /`에 multipart 파일을 보내면 422 JSON에 UploadFile 내부 구조가 드러남. 화면 형식도 일관되지 않음 | `RequestValidationError` 처리기 추가. 웹 경로는 HTML 422로 응답 |
| S-3 | security | `/docs`, `/redoc`, `/openapi.json`이 누구에게나 공개됨 | 설정으로 끌 수 있게 하거나 공개를 유지한다는 결정을 기록 |
| S-4 | security | 보안 응답 헤더(CSP, `nosniff`, `frame-ancestors`, `Referrer-Policy`)가 없음 | 미들웨어 추가 (인라인 스크립트가 없어 엄격한 CSP를 바로 적용할 수 있음) |
| S-5 | security | 폭 없는 문자나 형식 문자(Cf: U+200B, U+202E, U+FEFF), 전각 호스트, 범위를 벗어난 포트가 검증을 통과함 | Cf 문자를 거절 대상에 추가하고 포트를 검증함. IDN 처리 방침을 결정 |

security가 범위 밖으로 참고만 적은 항목: 오픈 리다이렉트 정책, CSRF(F3에서 인증 도입 시), 요청 수 제한·인증·별칭(F2·F3).

## 5. 설계서 해석 결정 목록

계획 단계 (`F1-plan.md` 7절):

- D-1: API 422 응답 본문은 FastAPI 표준 `{"detail": [...]}` 형식으로 통일
- D-2: `GET /{code}` 404는 항상 HTML 화면
- D-3: 공백이나 제어 문자가 든 URL은 422로 거절 (앞뒤 공백도 잘라내지 않고 거절)
- D-4: 스킴은 대소문자를 무시하고 비교. 저장은 받은 그대로
- D-5: 길이는 Python `len()` 기준 글자 수
- D-6: `created_at`은 초 단위에 `Z` 접미사
- D-7: 비ASCII URL 허용. `Location`은 퍼센트 인코딩됨 (실행 중 정정, 아래 참고)
- D-8: 폼에 `url` 필드가 없으면 빈 문자열로 처리
- D-9: 7자 영숫자가 아닌 경로는 DB 조회 없이 404 화면

실행 중 (`F1-decisions.md`):

- D-7 정정: URI에 그대로 쓸 수 없는 ASCII 문자도 퍼센트 인코딩됨 (R-1)
- D-10: D-3의 거절 대상을 유니코드 공백과 C0/C1 제어 문자까지 넓힘 (implementer)
- D-11: `urlsplit`의 `ValueError`를 422로 처리 (implementer)
- D-12: 입력 오류 화면의 `aria-describedby`는 목업을 따름 (implementer)
- D-13: 리뷰 1라운드 후 minor는 기록만 함 (H3, 메인)

H2(설계서 모호함)로 넘어간 테스트 실패는 없었습니다.

## 6. 종료 상태

**완료.** AC-1~AC-23을 모두 만족합니다. test-writer의 테스트와 qa의 블랙박스 검증이 같은 결과를 냈습니다. 최종 상태에서 `uv run pytest`는 224개를 통과했고, `uv run ruff check src tests`도 통과했습니다. 미해결 지적은 없습니다. 후속 작업으로 남길 만한 것은 4절의 minor 10건입니다.
