# 실행 요약

- 메인 세션: `aa731252-fba0-4719-88cf-547d01001794`
- 메시지: 29개 (에이전트 간 메시지 토큰 추정 합계 ~756)
- API 호출: 32회
- API 환산 비용: $0.8898

## 에이전트별 토큰

| 에이전트 | 모델 | 호출 | input | cache write | cache read | output | 비용(USD) |
|---|---|---|---|---|---|---|---|
| main | claude-opus-5-5 | 18 | 64 | 44,460 | 1,438,460 | 3,924 | 0.7221 |
| implementer | claude-sonnet-5-5 | 1 | 2 | 7,724 | 0 | 55 | 0.0199 |
| test-writer | claude-sonnet-5-5 | 1 | 2 | 7,805 | 0 | 55 | 0.0201 |
| tester | claude-sonnet-5-5 | 1 | 2 | 7,284 | 0 | 55 | 0.0188 |
| reviewer | claude-opus-5-5 | 1 | 2 | 7,309 | 0 | 100 | 0.0386 |
| qa | claude-sonnet-5-5 | 1 | 2 | 7,616 | 0 | 55 | 0.0196 |
| security | claude-opus-5-5 | 1 | 2 | 7,442 | 0 | 55 | 0.0383 |
| doc-keeper | claude-haiku-5-5 | 1 | 2 | 7,850 | 0 | 61 | 0.0010 |
| implementer#2 | claude-sonnet-5-5 | 1 | 2 | 0 | 7,724 | 55 | 0.0013 |
| test-writer#2 | claude-sonnet-5-5 | 1 | 2 | 0 | 7,805 | 55 | 0.0013 |
| tester#2 | claude-sonnet-5-5 | 1 | 2 | 0 | 7,284 | 55 | 0.0013 |
| reviewer#2 | claude-opus-5-5 | 1 | 2 | 0 | 7,309 | 106 | 0.0036 |
| qa#2 | claude-sonnet-5-5 | 1 | 2 | 0 | 7,616 | 55 | 0.0013 |
| security#2 | claude-opus-5-5 | 1 | 2 | 0 | 7,442 | 55 | 0.0026 |
| doc-keeper#2 | claude-haiku-5-5 | 1 | 2 | 0 | 7,850 | 61 | 0.0001 |
| **합계** | | 32 | 92 | 97,490 | 1,491,490 | 4,802 | 0.8898 |

메시지 토큰은 글자 수 기반 추정치입니다. API 호출 토큰은 트랜스크립트의 usage 값입니다.
