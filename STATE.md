# Project state

갱신: 2026-10-10 KST

## 현재 단계

**Phase 1 완료 — Mac 로컬 결정론적 비교 실험을 구현하고 실제 결과를 보존했다.**

연구 질문은 유지한다. 다섯 공개 개발 사례에서는 B1/B2가 실행 횟수 하한에 도달했다.
AI가 추가로 해결할 미해결 사례는 아직 관측되지 않았다. Phase 2로 자동 확장하지 않는다.

## 프로젝트와 적용 지침

- 실제 작업 경로: `/Users/yangjunmo/effici-lab/intent-revalidation-starter`.
- 이미 압축 해제된 자료 폴더를 독립 프로젝트로 사용했고 이 안에 `git init`을 실행했다.
- 로컬 Git 저장소에는 아직 commit과 remote가 없다. 외부 GitHub 저장소와 라이선스는 미정이다.
- 프로젝트의 AGENTS.md, RESEARCH.md, 초기 STATE.md, START_HERE.md, README.md와 개발 입력을 읽었다.
- 기본 Codex home의 `/Users/yangjunmo/.codex/AGENTS.md`는 실제 0바이트였다.
  AGENTS.override.md와 /, /Users, /Users/yangjunmo, /Users/yangjunmo/effici-lab의 AGENTS.md는 없었다.
- 대화에 적용된 Hephaestus 지침 전문과 Python programming 지침을 확인했다.
  전역 설정은 지침 파일 경로 관련 항목만 확인했다. 다른 운영 프로젝트를 연구에 연결하지 않았다.
- 자동 Python LSP는 사용 불가로 보고됐다. 실제 CLI basedpyright 검사는 0 errors/warnings/notes로 통과했다.

## 완료 산출물

- 표준 라이브러리의 load → normalize → aggregate → render 파이프라인.
- 관련 요구 필드·실제 입력 바이트·코드·환경·계약 버전 기반 B1 캐시와 과거 후보 전체 검색.
- 실제 역할 계약 검사 기반 B2, 전체 재실행 B0.
- requirement revision, task, attempt, 불변 artifact, assessment와 event의 별도 기록.
- 내용 해시, provenance, 실제 소비·채택·공개, 현재 결과 참조와 원래 생성 revision.
- D4/D5의 start → change → complete 이후 정책 활성화; 실제 로컬 늦은 계산 비용.
- 독립 CSV/보고서 내용 검사와 전체 이벤트 이력 감사.
- 현재 캐시에서 가능한 후보/새 실행 조합을 열거하는 실행 횟수 참조 계산기.
- 사례별 실제 보고서, 비용·시간·검사·실패 계수, 비교 Markdown 보고서.
- 46개 의미 있는 테스트와 CLI 도움말·잘못된 입력·기존 결과 보호 확인.

## 실제 실행 기록

환경: CPython 3.14.5, Darwin 25.6.0, arm64. 런타임 의존성은 표준 라이브러리다.

작업 경로에서 실행:

```bash
python3 -m src.intent_revalidation --run-id phase1-20261010-01
uv run pytest -q --junitxml=runs/phase1-20261010-01/verification-tests.xml
uv run ruff check src tests
uv run ruff format --check src tests
uv run basedpyright
```

- 실험: exit 0, `Final contracts satisfied: 15/15`.
- 테스트: 46 passed in 0.69s. Ruff/formatting 통과, 타입 진단 0건.
- Python discipline scanner: 21개 파일에서 위반 없음.
- `--help`: exit 0.
- 없는 입력 파일 지정: exit 2, 명시적 No such file 오류.
- 같은 run ID 재실행: exit 2, File exists 오류. 원래 실행은 보존된다.
- 선행 통합 실행 `runs/phase1-integration-01`도 당시 코드 스냅샷과 함께 남겼다.

최종 증거:

- [비교 보고서](runs/phase1-20261010-01/report.md)
- [전체 지표](runs/phase1-20261010-01/metrics.json)
- [명령·환경·코드와 입력 해시](runs/phase1-20261010-01/manifest.json)
- [검증 명령의 실제 출력](runs/phase1-20261010-01/verification.json)
- [테스트 XML](runs/phase1-20261010-01/verification-tests.xml)

코드 manifest SHA256:
`fd36f612113d762a0386b676822d731d6ea971e0f7a168bf4e09e7446bddd890`

입력 CSV SHA256:
`4efd3b6603da0fea4fd586fe1747da96d2f19eaa67af2a6be0d5a4638debcb81`

Git commit 대신 실제 소스 파일 manifest와 code_snapshot을 코드 버전 증거로 남겼다.

## 관측 결과

| 정책 | 최종 요구 충족 | 변경 후 새 단계 실행 | 역할 계약 검사 | 바이트 검사 | 실제 잘못된 캐시 사용 |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0 | 5/5 | 20 | 0 | 0 | 0 |
| B1 | 5/5 | 5 | 0 | 15 | 0/20 노출 이벤트 |
| B2 | 5/5 | 5 | 19 | 0 | 0/20 노출 이벤트 |

- 사례별 최소 새 실행은 D1=1, D2=2, D3=0, D4=1, D5=1이다. B1/B2 모두 일치했다.
- 공통 초기 단계 실행은 총 17회다. 사례별 한 번 실행해 정책 워크스페이스로 복제했다.
- D4/D5의 늦은 실행은 각 정책당 각각 1회로, 초기·정책 실행과 별도로 비용을 기록했다.
- D4의 이전 revision 집계는 B1/B2가 재평가 후 채택했다.
- D5의 이전 Markdown 보고서는 과거 산출물로 보존했고 현재 HTML 결과로 채택하지 않았다.
- 1월 api/storage = 4000/2000 cents, 2월 = 10000/5000 cents. 보고서의 기간·단위·형식도 검사했다.
- 실행 시간은 보고서에 실제 측정값으로 남겼다. 검사·연결 비용이 있으므로 실행 75% 감소를 총비용 75% 절감으로 해석하지 않는다.
- 이 다섯 사례에 한정하면 강한 결정론적 방법으로 충분했다.

## 알려진 한계

- 6행 합성 입력, 공개 개발 사례 5개, 선형 그래프와 구조화된 요구만 검증했다.
- 자연어 요구 해석, AI 정책, 비공개 평가·프로세스 격리, 다른 작업 종류와 일반화는 미검증이다.
- 각 정책을 한 번씩 고정 순서로 실행했다. 작은 시간 차이는 안정적인 성능 개선 증거가 아니다.
- D4/D5는 동기 로컬 이벤트 재생이며 실제 원격 병렬 작업의 취소·재시작을 검증하지 않았다.
- 시간 하한이 아닌 실행 횟수 하한이다. 내부 검사/키 시간이 정책 판단 시간에 포함되므로 두 번 더하지 않는다.
- 원격 API 비용·모델 호출·토큰은 0이다. 로컬 자원의 달러 비용은 추정하지 않았다.
- 감사는 신뢰하는 로컬 계측의 역할·캐시 출처 표시를 사용한다. 적대적 이벤트/provenance를 검증한 것은 아니다.
- 실행 실패 시 실패 이력을 남기고 실험이 중단된다. 실패하는 전체 워크플로 사이의 완성된 비교는 지원하지 않는다.
- 라이브러리·adapter·React 보드·서버 통합·공개 저장소·라이선스·지원 신청은 수행하지 않았다.

## 공개와 지원에 대한 판단

장기 목표는 유용한 오픈소스 연구를 만들고 OpenAI open-source support에 지원하는 것이다.
지원 여부를 연구 성과 지표로 바꾸지는 않는다.

2026-10-10 KST 공식 원문 확인:
[프로그램 안내](https://developers.openai.com/community/codex-for-oss),
[신청 양식](https://openai.com/form/codex-for-oss/).

공개 GitHub URL이 신청에 필요하며 사용·생태계 중요성·유지보수 근거를 검토한다.
지금 초기 연구 저장소를 만드는 것은 이르지 않다.
공개명·라이선스와 초기 연구 범위 표현을 정한 뒤 Phase 1 코드를 공개할 수 있다.
현재 결과만으로 지원 적격성이나 합격 가능성을 확인하지 않았다.

## 다음 한 가지 연구 작업

**B1/B2로 이미 해결되지 않는 대표적인 실제 요구 변경 사례가 있는지 한 가지 확인한다.**

관측된 사용 상황과 실패를 먼저 기록하고, 더 단순한 규칙으로도 해결되는지 대조한다.
그 증거가 없으면 AI 정책의 우위를 전제로 Phase 2를 시작하지 않는다.
