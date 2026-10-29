# F1 결정 기록 — 실행 중 생긴 해석과 판단

계획 단계의 해석 결정 D-1~D-9는 `docs/plans/F1-plan.md` 7절에 있습니다. 이 문서는 실행 중에 생긴 결정과 정정을 기록합니다. default 모드라서 H2(설계서 모호함)와 H3(리뷰 우선순위)는 메인 세션이 정했습니다.

| id | 출처 | 결정 | 이유 |
|---|---|---|---|
| D-7 정정 | 리뷰 R-1 | `Location`은 Starlette `RedirectResponse`가 `quote(url, safe=":/%#?=@[]!$&'()*+,;")`로 만듭니다. 그래서 비ASCII 문자뿐 아니라 URI에 그대로 쓸 수 없는 ASCII 문자(`<`, `>`, `"`, `{`, `}`, `|`, `\`, `^`, 백틱)도 퍼센트 인코딩됩니다. RFC 3986상 허용되는 문자만 쓴 URL은 글자 그대로 나갑니다(AC-10). | 이런 문자는 RFC 3986에서 URI에 그대로 쓸 수 없고, 브라우저 동작과도 같습니다. 인코딩된 값을 `unquote`하면 원래 URL과 같습니다. 동작은 바꾸지 않고 기록만 바로잡았습니다. |
| D-10 | implementer 판단, 리뷰 R-3 | D-3에서 거절하는 문자를 넓혔습니다. `str.isspace()`가 참인 문자(유니코드 공백 포함), ASCII 제어 문자(0x00~0x1F, 0x7F), C1 제어 문자(0x80~0x9F)를 모두 거절합니다. | 이런 문자는 모두 `Location`에 안전하게 넣을 수 없거나 유효한 URL이 아닙니다. D-3 결정의 취지 안에 있는 확장입니다. |
| D-11 | implementer 판단, 리뷰 R-3 | `urlsplit`이 `ValueError`를 내는 값(예: `http://[`)은 422로 거절합니다. 스킴이 http나 https이면 `MSG_NO_HOST`, 아니면 `MSG_SCHEME` 문구를 씁니다. | 500 대신 검증 실패로 처리하려는 것입니다. |
| D-12 | implementer 판단, 리뷰 R-3 | 입력 오류 화면의 입력칸에 `aria-describedby="url-error url-hint"`를 넣습니다. 오류가 없는 홈 화면은 `aria-describedby="url-hint"`입니다. | 목업 `F1-input-error.html`이 이렇게 되어 있습니다. 계획 4절의 `"url-error"` 표기보다 목업이 우선합니다. |
| D-13 | 리뷰 1라운드 (H3) | blocker와 major가 0건이라 수정 라운드를 열지 않았습니다. minor 10건(R-1~R-5, S-1~S-5)은 보고서에 기록만 했습니다. | 실행 절차 4단계 3항에 따른 것입니다. |
