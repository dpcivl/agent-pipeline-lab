# research — 측정 도구와 실험 데이터

| 폴더 | 내용 | git 공개 |
|---|---|---|
| `hooks/` | 에이전트 호출을 실시간 기록하는 Claude Code hook 스크립트 | 공개 |
| `tools/` | 트랜스크립트 수집(`collect.py`), 채점(`score.py`), 비식별화 스크립트 | 공개 |
| `config/` | 모델 단가표(`pricing.json`), 메시지 코드북(`message-codebook.md`), Claude Code 설정 템플릿(`claude-settings.json`) | 공개 |
| `logs/` | hook이 남기는 실시간 원본 로그. `logs/events/`에 이벤트마다 파일 하나 | **비공개** (.gitignore) |
| `runs/` | 실행별 결과. `runs/F{n}/{auto\|human}/r{k}/` | 일부 공개 (아래 참고) |

## runs/ 하위 구조와 공개 범위

```
runs/F1/auto/r1/
├── session.txt        # 메인 세션 id, Claude Code 버전, 설정 파일 해시
├── transcripts/       # 원본 JSONL 사본 — 비공개 (.gitignore)
├── messages/          # 에이전트 간 메시지 원문, 메시지 한 개당 파일 하나 (비식별화 후) — 공개
├── messages.jsonl     # 위 메시지의 분석용 한 줄 형식
├── flow.md            # 메시지 흐름 시퀀스 다이어그램 (자동 생성)
├── annotations.csv    # 메시지 코딩 결과 (코드북 기준)
├── usage.csv          # 에이전트 실행별 토큰
├── edges.csv          # 통신 엣지별 토큰
├── score.json         # 평가 테스트·정적 지표·블라인드 평가 결과
├── human-log.md       # 사람 개입 기록 (collect.py 자동 생성 + 연구자 메모)
└── summary.md         # 실행 요약
```

원본 트랜스크립트에는 로컬 경로, 계정 정보, 환경 정보가 들어 있습니다. 공개 저장소에는 비식별화 스크립트를 거친 `messages/`만 올립니다.
