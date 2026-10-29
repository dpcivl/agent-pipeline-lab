# agent-pipeline-lab

사람과 Claude Code 서브에이전트가 함께 기능을 개발하는 파이프라인을 직접 만들어 보고, 에이전트끼리 주고받는 프롬프트와 토큰 사용량을 측정하는 연구 저장소입니다.

## 알고 싶은 것

- 에이전트끼리 실제로 어떤 프롬프트를 주고받는가
- 그 소통에 토큰이 얼마나 드는가
- 기능 하나를 끝까지 만드는 데 비용이 얼마인가
- 사람이 개입할 때와 하지 않을 때 결과물과 비용이 어떻게 다른가
- 에이전트끼리의 소통에서 사람이 배울 수 있는 효율적인 프롬프팅 패턴은 무엇인가

## 파이프라인

```
설계서(사람) → 계획·스켈레톤(메인) → 승인(사람)
→ [구현 ∥ 테스트 작성] → 테스트 루프 → [리뷰 ∥ QA ∥ 보안] 리뷰 루프
→ 문서·커밋 → 보고서
```

실험 대상은 URL 단축 API(ShortLink)이고, 기능 3개를 순서대로 만듭니다.

## 문서

| 문서 | 내용 |
|---|---|
| [docs/01-research-plan.md](docs/01-research-plan.md) | 연구 목표, 방법, 진행 단계, 공개 정책 |
| [docs/00-pipeline-design.md](docs/00-pipeline-design.md) | 파이프라인과 측정 방법의 상세 설계 |
| [docs/insights/](docs/insights/) | 에이전트 간 소통에서 찾은 프롬프트 패턴 카드 |
| [docs/journal/](docs/journal/) | 연구 일지 |
| [research/](research/) | 측정 도구와 실험 데이터 |

## 폴더 구조

```
docs/
├── 00-pipeline-design.md   상세 설계
├── 01-research-plan.md     연구 계획서
├── features/               기능 설계서 (사람 작성)
├── plans/                  구현 계획과 결정 기록 (메인 세션 작성)
├── insights/               프롬프트 패턴 카드와 예시
└── journal/                연구 일지
research/
├── hooks/                  에이전트 호출 실시간 기록
├── tools/                  수집·채점·비식별화 스크립트
├── config/                 단가표 등 설정
├── logs/                   실시간 원본 로그 (비공개)
└── runs/                   실행별 결과
```

서비스 코드(`src/`, `tests/`)와 에이전트 정의(`.claude/agents/`)는 세팅 단계에서 추가됩니다.

## 상태

설계 단계입니다. 진행 상황은 [연구 계획서의 현재 상태](docs/01-research-plan.md#10-현재-상태-2026-10-29)를 보세요.
