---
seq: 16
sender: "implementer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T05:18:32.667Z"
agent: "implementer"
agent_id: "a46510386cb9984ad"
turn: 2
reply_to: 14
chars: 940
tokens_est: 486
wait_s: null
---

## 결과: 완료
## 변경 파일
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\src\shortlink\validation.py: `validate_url`에 서로게이트 검사를 추가함. U+D800~U+DFFF 문자가 하나라도 있으면 `URLValidationError("URL에 쓸 수 없는 문자가 있습니다.")`를 낸다. 위치는 공백·제어 문자 검사 바로 다음, `urlsplit`과 스킴 검사 앞이다. 함수 docstring의 검사 순서도 갱신함.
- 그 밖의 파일은 바꾸지 않았다. 검사가 `validate_url` 안에 있어서 API와 폼이 같은 규칙을 쓴다.

## 구현한 수용 기준
- 이번 수정은 R-1/S-1/Q-1 지적(D-10, 계획서 표 4-1행)에 대한 것이다. AC-9(거절된 요청은 저장하지 않음)와 AC-19를 서로게이트 입력에도 지키게 됨: `validation.py`.
- TestClient로 직접 확인한 결과:
  - JSON 이스케이프 `"\ud800"`를 보내면 422이고 `detail`은 `URL에 쓸 수 없는 문자가 있습니다.`
  - 원시 UTF-8 서로게이트 바이트 `\xed\xa0\x80`를 본문에 넣어도 422이고 같은 문구
  - 정상 비ASCII URL(`https://예시.com/😀`, 이모지는 정상적인 비BMP 문자)은 여전히 201
  - 두 거절 뒤 저장소의 링크 수는 정상 요청 1건뿐이라 거절 요청은 저장되지 않음
- `uv run ruff check src`는 통과했고 `uv run ruff format src`는 변경 없음. pytest는 돌리지 않았다(tests/는 건드리지 않음).

## 계획에 없던 판단
- 없음

## 남은 문제와 질문
- 없음. S-3(다른 Cc/Cf 문자 거절)과 그 밖의 minor 지적은 지시대로 반영하지 않았다.
