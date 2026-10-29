# ShortLink

URL 단축 API입니다. Python 3.12, uv, FastAPI, SQLite(표준 라이브러리 sqlite3), pytest를 씁니다.

## 명령

- 테스트: `uv run pytest`
- 린트와 포맷: `uv run ruff check src tests`, `uv run ruff format src tests`
- 서버: `uv run uvicorn shortlink.main:create_app --factory`
- 의존성 추가: `uv add <패키지>` (pip는 쓰지 않습니다)

## 고정 계약 (이름과 시그니처 변경 금지, 확장만 허용)

- `src/shortlink/main.py`의 `create_app(settings=None)`: 라우터 등록과 DB 스키마 준비까지 끝난 앱을 반환합니다.
- `src/shortlink/config.py`의 `Settings`와 환경 변수 `SHORTLINK_DB_PATH`, `SHORTLINK_BASE_URL`
- `tests/conftest.py`의 `settings`, `app`, `client` 픽스처

## 문서

- 기능 설계서: `docs/features/`
- 구현 계획과 결정 기록: `docs/plans/`

## 작업 범위

- 자기 역할에 정해진 쓰기 영역 밖의 파일은 수정하지 않습니다.
- 이 저장소 밖의 경로는 읽지도 쓰지도 않습니다.
- `git push`는 하지 않습니다.
