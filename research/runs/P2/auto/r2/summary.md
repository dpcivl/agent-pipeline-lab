# 실행 요약

- 메인 세션: `5d4f7c0d-1c20-4899-82ad-01224cc4c748`
- 메시지: 29개 (에이전트 간 메시지 토큰 추정 합계 ~756)
- API 호출: 33회
- API 환산 비용: $0.8473

## 에이전트별 토큰

| 에이전트 | 모델 | 호출 | input | cache write | cache read | output | 비용(USD) |
|---|---|---|---|---|---|---|---|
| main | claude-opus-5-5 | 19 | 66 | 36,692 | 1,530,951 | 3,775 | 0.6755 |
| implementer | claude-sonnet-5-5 | 1 | 2 | 8,011 | 0 | 55 | 0.0206 |
| test-writer | claude-sonnet-5-5 | 1 | 2 | 8,092 | 0 | 55 | 0.0208 |
| tester | claude-sonnet-5-5 | 1 | 2 | 7,571 | 0 | 55 | 0.0195 |
| reviewer | claude-opus-5-5 | 1 | 2 | 7,596 | 0 | 55 | 0.0391 |
| qa | claude-sonnet-5-5 | 1 | 2 | 7,903 | 0 | 55 | 0.0203 |
| security | claude-opus-5-5 | 1 | 2 | 7,729 | 0 | 55 | 0.0398 |
| doc-keeper | claude-haiku-5-5 | 1 | 2 | 8,137 | 0 | 61 | 0.0010 |
| implementer#2 | claude-sonnet-5-5 | 1 | 2 | 0 | 8,011 | 55 | 0.0014 |
| test-writer#2 | claude-sonnet-5-5 | 1 | 2 | 0 | 8,092 | 55 | 0.0014 |
| tester#2 | claude-sonnet-5-5 | 1 | 2 | 0 | 7,571 | 55 | 0.0013 |
| reviewer#2 | claude-opus-5-5 | 1 | 2 | 0 | 7,596 | 55 | 0.0026 |
| qa#2 | claude-sonnet-5-5 | 1 | 2 | 0 | 7,903 | 55 | 0.0013 |
| security#2 | claude-opus-5-5 | 1 | 2 | 0 | 7,729 | 55 | 0.0027 |
| doc-keeper#2 | claude-haiku-5-5 | 1 | 2 | 0 | 8,137 | 55 | 0.0001 |
| **합계** | | 33 | 94 | 91,731 | 1,585,990 | 4,551 | 0.8473 |

메시지 토큰은 글자 수 기반 추정치입니다. API 호출 토큰은 트랜스크립트의 usage 값입니다.
