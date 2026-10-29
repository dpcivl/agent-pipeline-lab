# 실행 요약

- 메인 세션: `2d77494c-7ae7-4df3-af5a-2c55ae728f99`
- 메시지: 29개 (에이전트 간 메시지 토큰 추정 합계 ~756)
- API 호출: 33회
- API 환산 비용: $0.9064

## 에이전트별 토큰

| 에이전트 | 모델 | 호출 | input | cache write | cache read | output | 비용(USD) |
|---|---|---|---|---|---|---|---|
| main | claude-opus-5-5 | 19 | 66 | 44,902 | 1,500,799 | 3,554 | 0.7307 |
| implementer | claude-sonnet-5-5 | 1 | 2 | 8,238 | 0 | 55 | 0.0211 |
| test-writer | claude-sonnet-5-5 | 1 | 2 | 8,303 | 0 | 55 | 0.0213 |
| tester | claude-sonnet-5-5 | 1 | 2 | 7,676 | 0 | 55 | 0.0197 |
| reviewer | claude-opus-5-5 | 1 | 2 | 7,746 | 0 | 55 | 0.0398 |
| qa | claude-sonnet-5-5 | 1 | 2 | 8,145 | 0 | 55 | 0.0209 |
| security | claude-opus-5-5 | 1 | 2 | 7,927 | 0 | 55 | 0.0407 |
| doc-keeper | claude-haiku-5-5 | 1 | 2 | 8,258 | 0 | 61 | 0.0011 |
| implementer#2 | claude-sonnet-5-5 | 1 | 2 | 0 | 8,238 | 55 | 0.0014 |
| test-writer#2 | claude-sonnet-5-5 | 1 | 2 | 0 | 8,303 | 55 | 0.0014 |
| tester#2 | claude-sonnet-5-5 | 1 | 2 | 0 | 7,676 | 55 | 0.0013 |
| reviewer#2 | claude-opus-5-5 | 1 | 2 | 0 | 7,746 | 55 | 0.0027 |
| qa#2 | claude-sonnet-5-5 | 1 | 2 | 0 | 8,145 | 55 | 0.0014 |
| security#2 | claude-opus-5-5 | 1 | 2 | 0 | 7,927 | 55 | 0.0027 |
| doc-keeper#2 | claude-haiku-5-5 | 1 | 2 | 0 | 8,258 | 61 | 0.0001 |
| **합계** | | 33 | 94 | 101,195 | 1,557,092 | 4,336 | 0.9064 |

메시지 토큰은 글자 수 기반 추정치입니다. API 호출 토큰은 트랜스크립트의 usage 값입니다.
