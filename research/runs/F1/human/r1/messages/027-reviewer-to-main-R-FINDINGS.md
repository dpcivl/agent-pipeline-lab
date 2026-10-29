---
seq: 27
sender: "reviewer"
receiver: "main"
type: "R-FINDINGS"
timestamp: "2026-10-29T06:14:14.725Z"
agent: "reviewer"
agent_id: "a99e7ca7e2a22575b"
turn: 2
reply_to: 23
chars: 2388
tokens_est: 1053
wait_s: null
---

## 결과: 지적 1건 (blocker 0, major 0, minor 1)

검토 범위는 `git diff 9f6fab9..f1200fd`입니다(src, tests, 그리고 함께 바뀐 docs/plans/F1-plan.md와 mockups/F1-index.html). 정적 검토만 했고, 테스트와 서버는 직접 실행하지 않았습니다.

변경분에서 확인한 것:
- `security.py`(D-10): 미들웨어를 `create_app`에서 mount와 라우터 등록보다 먼저 붙이므로 `/static`을 포함한 모든 응답에 적용됩니다.
- CSP `default-src 'self'`가 우리 화면을 막지 않습니다. 템플릿 4개에는 인라인 `<script>`, `<style>`, `style=` 속성이 없고, 자원은 `/static/style.css`와 `/static/copy.js`(같은 출처)뿐입니다. 폼은 `action="/"`이라 `form-action 'self'`를 만족합니다.
- `/docs`, `/redoc`, oauth2-redirect 경로는 하드코딩하지 않고 `app.*_url`에서 읽습니다. 꺼져 있으면 None이 집합에 들어가지만 비교에는 해가 없습니다.
- 고정 계약(`create_app(settings=None)`)은 유지됩니다.

### R-4 [minor] 복사 가드 테스트가 수정 전 코드에서도 통과함
- 위치: `tests/test_web.py:369-374` (`test_copy_script_guards_missing_clipboard_api`)
- 문제: `assert "navigator.clipboard" in response.text`는 수정 전 `copy.js`에도 있던 문자열입니다(`navigator.clipboard.writeText(...)`). 그래서 D-11 가드를 지워도 이 테스트는 계속 통과하고, 회귀를 잡지 못합니다.
- 근거: 9f6fab9의 `src/shortlink/static/copy.js:4`에 이미 `navigator.clipboard.writeText`가 있습니다.
- 수정 제안: 가드 자체를 확인하도록 바꿉니다. 예를 들면 `assert "!navigator.clipboard" in response.text`이고, 필요하면 가드 분기 안에 실패 문구가 있는지도 확인합니다. 문자열 검사라는 한계는 그대로이니 실제 브라우저 동작은 qa 확인에 맡깁니다.

## 이전 지적 확인
- R-1: 해결.
  - `validation.py:56-59`에서 규칙 4 다음, 스킴 검사 전에 `url.encode("utf-8")`가 실패하면 `MSG_INVALID_ENCODING`으로 거절합니다. 계획 3.1 표 규칙 5와 D-9에 맞습니다.
  - 순서 테스트는 길이 > 문자 > 인코딩 > 스킴 > 호스트 순서를 모두 확인합니다. API 테스트는 원문 JSON의 `\ud800`, `\udc80`, `\udbff\u0041`이 422로 거절되고 `count_links()==0`인지 확인하고, 짝이 맞는 `\ud83d\ude00`은 201이 되는 대조군도 있습니다.
  - 검증을 통과한 URL만 저장되므로 `web.py:41`의 `quote`에서 터질 경로도 함께 막혔습니다.
  - 목업 index 오류 문구 표도 갱신됐습니다.
  - 사소한 점: 계획 D-9 행이 출처를 "리뷰 1라운드 M-1"로 적었는데, 리뷰 지적 id는 R-1입니다. 문서 표기만의 문제입니다.
- R-2: 해결. `copy.js:4-7`에서 `navigator.clipboard`나 `writeText`가 없으면 바로 계획의 실패 문구를 표시하고 끝냅니다(D-11). 목업 구조와 문구는 바뀌지 않았습니다. 다만 이 수정을 지키는 테스트는 R-4처럼 약합니다.
- R-3: 해결. `tests/test_repository.py:97`이 `assert len(calls) == LinkRepository.MAX_ATTEMPTS`로 고정됐습니다.

관련 파일:
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\security.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\validation.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\src\shortlink\static\copy.js
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_web.py
- <HOME>\Documents\dev\agent-pipeline-lab-runs\F1-human-r1\tests\test_repository.py
