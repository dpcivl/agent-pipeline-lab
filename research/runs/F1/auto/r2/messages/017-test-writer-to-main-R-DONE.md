---
seq: 17
sender: "test-writer"
receiver: "main"
type: "R-DONE"
timestamp: "2026-10-29T05:18:45.933Z"
agent: "test-writer"
agent_id: "ac6963e1736f78e26"
turn: 2
reply_to: 15
chars: 1264
tokens_est: 618
wait_s: null
---

## 결과: 완료
D-10 회귀 테스트를 `tests/test_api.py`에 추가했습니다. `uv run ruff check tests`와 `uv run ruff format tests`를 실행했고 둘 다 문제 없습니다. 전체 `uv run pytest`는 96개 통과입니다. 이 실행은 implementer의 `src/shortlink/validation.py` 수정이 이미 들어간 상태에서 한 것입니다.

## 변경 파일
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-auto-r2\tests\test_api.py: D-10 테스트 3개(케이스 7개)를 추가했습니다. 위치는 `test_d2_...`와 `test_ac9_all_rejected_...` 사이입니다.
- 이전 보고의 다른 파일(`conftest.py`, `test_web.py`)은 이번에 바꾸지 않았습니다.

## 수용 기준과 테스트 대응
- D-10 JSON 이스케이프 서로게이트: `test_d10_json_escaped_surrogate_is_rejected`
  - 케이스 4개: `\ud800`이 경로에 있는 경우, 낮은 서로게이트 `\udfff`, 호스트 부분(`http://\ud800.com/`), 스킴 앞.
  - 모두 422, 본문 `{"detail": "URL에 쓸 수 없는 문자가 있습니다."}`, `count_links() == 0`을 확인합니다.
- D-10 원시 바이트: `test_d10_raw_surrogate_bytes_are_rejected`
  - 케이스 2개: 경로와 호스트에 `b'\xed\xa0\x80'`을 그대로 넣습니다.
  - 422, `detail`이 문자열, 행 수 0을 확인합니다.
- 추가로 `test_d10_valid_surrogate_pair_escape_is_still_accepted`를 넣었습니다. `\ud83d\ude00`은 짝이 맞는 이스케이프라서 한 글자(U+1F600)이고, 201로 생성되어 `url`이 그대로 돌아오는지 확인합니다. 과잉 거절을 막는 회귀 테스트입니다.

## 설계서 해석이 필요했던 부분
- 원시 바이트 케이스는 `detail` 문구를 고정하지 않았습니다. 본문이 UTF-8로 디코딩되지 않으면 "깨진 JSON"(D-4)으로 처리될 수도 있고 D-10 문구로 처리될 수도 있는데, 결정 문서가 어느 쪽인지 정하지 않았기 때문입니다. 422와 행 수 0만 요구합니다.
- 폼 경로 테스트는 요청하신 대로 넣지 않았습니다.

## 남은 문제와 질문
- 없음
