---
seq: 23
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T05:19:38.177Z"
agent: "reviewer"
agent_id: "af6cc410cc44344fc"
turn: 2
reply_to: 20
chars: 1848
tokens_est: 832
wait_s: null
---

## 결과: 지적 1건 (blocker 0, major 0, minor 1)

R-1은 해결되었습니다. 이번 변경분(`git diff 166f2b6..36183ce`)에서는 minor 1건만 나왔습니다. 규칙대로 읽기 전용으로만 확인했고, 테스트(96개 통과)는 다시 돌리지 않았습니다.

## 지적 목록

### R-5 [minor] 원시 서로게이트 바이트 테스트가 오류 문구를 확인하지 않음
- 위치: tests/test_api.py `test_d10_raw_surrogate_bytes_are_rejected` (추가된 블록의 두 번째 테스트)
- 문제: 이 테스트는 `isinstance(response.json()["detail"], str)`만 확인합니다. 같은 파일의 JSON 이스케이프 테스트와 D-2 테스트는 `== {"detail": MSG_...}`로 문구까지 맞춰 봅니다.
- 근거: 표준 `json.loads(bytes)`는 `'surrogatepass'`로 디코딩합니다. 그래서 `\xed\xa0\x80`도 `\ud800`이 든 `str`이 되고, `validate_url`의 D-10 검사에 걸려 `URL에 쓸 수 없는 문자가 있습니다.`가 나와야 합니다. 그런데 지금 단언으로는 다른 경로로 422가 나도 통과합니다. 예를 들어 Starlette가 디코딩 방식을 바꿔 본문 형식 오류(D-9 문구)가 나오는 경우입니다. 그러면 D-10 경로가 실제로 검증되지 않습니다.
- 수정 제안: `assert response.json() == {"detail": MSG_SURROGATE}`로 강화하세요. 일부러 느슨하게 둔 것이라면 이유를 주석으로 남겨 주세요.

## 이전 지적 확인
- R-1: 해결.
  - src/shortlink/validation.py에 D-2 검사 바로 다음, `urlsplit` 앞에 `any(0xD800 <= ord(char) <= 0xDFFF ...)` 검사가 들어가 422를 돌려줍니다.
  - `validate_url`에 있으므로 API와 폼이 같은 규칙을 씁니다.
  - 테스트가 다루는 경우: JSON 이스케이프(상위·하위 서로게이트, 호스트 위치, 스킴 앞), 원시 UTF-8 바이트, 정상 서로게이트 쌍 `\ud83d\ude00` 허용. 원시 바이트 테스트의 단언이 약한 점은 R-5로 따로 적었습니다.
  - 문서: 결정 D-10(docs/plans/F1-decisions.md), 계획서 검사 순서 표 4-1 행(docs/plans/F1-plan.md), 목업 목록 문구(docs/plans/mockups/F1-index.html)가 같은 문구와 같은 순서로 맞습니다.
  - D-10 결정 자체도 타당하다고 봅니다. 그대로 저장할 수 없는 값이라 거절이 유일한 선택입니다.
- R-2: 미반영(minor)
- R-3: 미반영(minor)
- R-4: 미반영(minor)

관련 파일:
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\src\shortlink\validation.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\tests\test_api.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\docs\plans\F1-decisions.md
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\docs\plans\F1-plan.md
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\docs\plans\mockups\F1-index.html
