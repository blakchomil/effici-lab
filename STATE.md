# Project state

갱신: 2026-10-10 KST

## 현재 단계

**Phase 1과 Phase 2 진입 비교 완료, 실제 유지관리자 요청의 인간 확인 후 지원 현황 보고서 비교도 실행했다.**

연구 질문은 유지한다. 다섯 공개 개발 사례에서는 B1/B2가 실행 횟수 하한에 도달했다.
보존된 Phase 1 metrics를 사용하는 두 번째 작업에서도 B1/B2가 실행 횟수 하한에 도달했다.
AI가 추가로 해결할 미해결 사례는 아직 관측되지 않았다. Phase 2 AI 비교, Phase 3 자연어 평가,
Phase 4 외부 통합을 완료했다고 주장하지 않는다.
새 사례에서도 공통 확인 답변 파서와 B1/B2가 충분했다. 같은 사례의 다섯 반복을 독립된 사용자 사례로
세지 않으며, 확인 질문의 효과나 자연어 일반화도 입증하지 않았다.

## 프로젝트와 적용 지침

- 실제 작업 경로: `/Users/yangjunmo/effici-lab/intent-revalidation-starter`.
- 이미 압축 해제된 자료 폴더를 독립 프로젝트로 사용했고 이 안에 `git init`을 실행했다.
- 공개 GitHub 저장소: [blakchomil/effici-lab](https://github.com/blakchomil/effici-lab).
- 기본 브랜치는 `main`, 원격은 `origin`이며 로컬 브랜치가 `origin/main`을 추적한다. 현재 라이선스는 MIT다.
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

실험 당시에는 실제 소스 파일 manifest와 code_snapshot을 코드 버전 증거로 남겼다.
이 기록은 공개 첫 커밋 `91e405a179de035b96f16aa4cf3177bb5c8898e2`에 원본 그대로 포함했다.

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
- Phase 1 당시 라이브러리·adapter·React 보드·서버 통합·라이선스 선택·지원 신청은 수행하지 않았다.
  이후 MIT를 적용했으며 나머지 항목은 여전히 미수행이다.

## 공개와 지원에 대한 판단

장기 목표는 유용한 오픈소스 연구를 만들고 OpenAI open-source support에 지원하는 것이다.
지원 여부를 연구 성과 지표로 바꾸지는 않는다.

2026-10-10 KST 공식 원문 확인:
[프로그램 안내](https://developers.openai.com/community/codex-for-oss),
[신청 양식](https://openai.com/form/codex-for-oss/).

공개 GitHub URL이 신청에 필요하며 사용·생태계 중요성·유지보수 근거를 검토한다.
지금 초기 연구 저장소를 만드는 것은 이르지 않다.
사용자 요청에 따라 공개명 `effici-lab`으로 Phase 1 코드와 실행 결과를 공개했다. 공개 당시 라이선스는 미정이었고 이후 MIT를 적용했다.
현재 결과만으로 지원 적격성이나 합격 가능성을 확인하지 않았다.

## 공개 저장소 등록 기록

2026-10-10 KST, 사용자의 공개 등록 요청에 따라 GitHub의 `blakchomil` 계정에 등록했다.

- `gh repo create blakchomil/effici-lab --public --source=. --remote=origin --push`: exit 0.
- `gh repo view`: visibility=`PUBLIC`, default branch=`main` 확인.
- 첫 커밋: `91e405a179de035b96f16aa4cf3177bb5c8898e2` — Implement Phase 1 artifact revalidation experiment.
- 코드·테스트·입력·문서·두 실행 기록의 588개 파일을 게시했다. 로컬 환경과 내부 에이전트 작업 폴더는 제외했다.
- 기록된 코드·입력·산출물 해시를 공개 전 점검했으며 두 실행 기록의 원본을 보존했다.
- README의 재현 절차를 `git clone`과 저장소 루트 기준으로 갱신했다.
- 별도 임시 폴더에서 공개 저장소를 새로 clone한 뒤 `python3 -m src.intent_revalidation`을 실행했다.
  exit 0, `Final contracts satisfied: 15/15`. 검증용 새 실행은 임시 clone 안에 있으며 기존 연구 기록을 덮어쓰지 않았다.
- 코드 동작은 변경하지 않았다. 이전 46개 테스트와 정적 검사 기록은 유효하다.

## 다음 한 가지 연구 작업

**외부 개발자 한 명의 독립 재현과 실제 작업 적용 기록을 확보한다.**

공개 과제 #2의 기준으로 외부 사람의 환경·명령·결과와 설치·사용의 마찰을 기록한다.
유지관리자 에이전트나 CI를 외부 사람으로 세지 않는다. 참여자 없는 상태를 재현 성공으로 바꾸지 않는다.

## 후속 진입 실험: 연구 보고서 변경

사용자 선택: 추가 유료 API 없이 현재 Codex 환경에서 가능한 범위를 사용하고,
이 연구에서 만든 보고서·실험 산출물 변경을 우선한다. 이 실험 당시 라이선스는 미정이었다.

- 원본: 보존된 `runs/phase1-20261010-01/metrics.json`의 실제 15개 측정 결과.
- 작업: select → summary → render. 원본 Phase 1 실행을 다시 돌리지 않는다.
- 변경: 제목, 열 순서, D4/D5만 선택, 처음 요구로 복귀. 보고서 작업에서 제안한 공개 개발 사례다.
  실제 사용자 실패를 관측한 사례나 비공개 평가로 주장하지 않는다.
- 역할별 요구 필드·실제 입력 바이트·단계 의존 코드·환경·계약을 사용하는 B1과 역할 계약을 실행하는 B2.
- 원본 metrics 바이트에서 기대값을 별도로 재구성하는 독립 평가기, 모든 중간 결과의 실제 소비·공개 감사.
- 공통 초기 보고서 3단계를 한 번 실행해 각 정책에 복제한다. 이후에는 각 정책의 순차 캐시 이력만 사용한다.
- 실행 attempt는 독립 UUID ID, artifact는 별도 ID, 단계는 논리적 역할이다. 과거 산출물과 생성 revision을 보존한다.

실제 최종 명령:

```bash
python3 -m src.intent_revalidation.report_workflow --run-id report-followup-20261010-02
uv run pytest -q --junitxml=runs/report-followup-20261010-02/verification-tests.xml
uv run ruff check src tests
uv run ruff format --check src tests
uv run basedpyright
```

- CLI: exit 0, `Report workflow contracts satisfied: 12/12`.
- 전체 테스트: 77 passed in 1.13s. Ruff/formatting 통과, 타입 진단 0건.
- Python discipline scanner: 36개 파일에서 위반 없음.
- 실제 원본 CLI 회귀 실행: exit 0, `Final contracts satisfied: 15/15`.
- 새 CLI 도움말 exit 0; 기존 결과·없는 입력·잘못된 JSON·안전하지 않은 ID는 각각 exit 2.
- 없는/잘못된 입력은 실행 폴더를 만들지 않았다. 최종 코드 스냅샷의 16개 파일 해시와 실제 소스 일치를 확인했다.
- 원본 metrics와 복제한 source_metrics의 바이트가 일치했다. 이전 Phase 1 두 실행 기록에는 변경이 없다.

| 변경 | B0 새 단계 | B1 새 단계 | B2 새 단계 | 현재 캐시의 참조 하한 |
| --- | ---: | ---: | ---: | ---: |
| 제목 | 3 | 1 | 1 | 1 |
| 열 순서 | 3 | 1 | 1 | 1 |
| D4/D5만 선택 | 3 | 3 | 3 | 3 |
| 원래 요구 복귀 | 3 | 0 | 0 | 0 |

전체 최종 요구 12/12 충족. B1/B2 각각 잘못된 캐시 사용 0/14 노출 이벤트, 잘못된 중간 소비·계보 위반 0건.
공통 초기 생성과 별도로 변경 후 새 보고서 단계는 B0=12회, B1/B2=각각 5회였다.
최소값은 검사·시간·달러 비용의 하한이 아니라 새 단계 실행 횟수의 유한 참조값이다.
B2의 계약 검사는 기대 역할 내용을 재계산한다. 검사 비용과 정책 wall time은 실제 측정했으며,
겹치는 내부 시간을 총비용에 두 번 더하지 않는다. 한 번의 작은 로컬 측정으로 안정적인 비용 우위를 주장하지 않는다.
원본 실험 재실행·모델 호출·토큰·외부 API 비용은 0이다. 로컬 달러 비용은 추정하지 않았다.

최종 증거:

- [비교 보고서](runs/report-followup-20261010-02/report.md)
- [전체 지표](runs/report-followup-20261010-02/metrics.json)
- [명령·환경·코드·원본 해시](runs/report-followup-20261010-02/manifest.json)
- [실제 검증 출력](runs/report-followup-20261010-02/verification.json)
- [테스트 XML](runs/report-followup-20261010-02/verification-tests.xml)

코드 manifest SHA256: `7038bc2662311211d232cf0ca2130a87c93a68635573291288e939295d4a77e6`.
원본 metrics SHA256: `ade7dd40dee5b3dcfb782a1141ebc89da7f57a0d509deecdf8a0d1100418eb20`.
선행 `report-development-01`, `report-followup-20261010-01`도 당시 코드와 함께 보존했다.
후자는 12/12 실행·77개 테스트를 통과했지만 모듈 길이 검사에서 실패했다. 파일을 역할별로 분리한 뒤
새 ID의 최종 실행과 전체 검사를 통과했다. 선행 실행의 코드를 덮어쓰지 않았다.

CI를 Linux/Python 3.13과 macOS/Python 3.14에 구성했다. 고정 커밋의 Actions와 읽기 권한을 사용하며
테스트·정적 검사·두 실제 CLI 실행을 수행한다. GitHub의 두 job에서 모든 단계가 실제 success로 완료됐다.
검증한 revision: `4a72806d06abc7fc1c97a9774a06ecd80352c673`.
[실제 CI 실행](https://github.com/blakchomil/effici-lab/actions/runs/38029232478),
[검증 기록](runs/report-followup-20261010-02/ci-verification.json).
후속 코드·테스트·세 실행 기록·문서와 CI를 공개 저장소 main에 게시했다.
관측 범위는 구조화된 요구·동기 로컬 실행·공개 개발 사례다. 자연어 해석, 숨겨진 평가,
외부 워크플로와 원격 병렬 복구는 미검증이다.

## 지원 준비와 관측된 요청 사례

사용자가 라이선스·유지관리·실제 효용의 증거 부족을 지적하고 지금 보완하도록 요청했다.
MIT LICENSE와 프로젝트 메타데이터, CONTRIBUTING.md, CHANGELOG.md, 초기 개발 릴리스 자료를 추가하고 공개했다.
지속적인 유지관리 이력이나 외부 이용자를 새로 확보했다고 주장하지 않는다.

실제 요청 원문과 별도로 제안한 보고서 변경 해석을 [사례](examples/support-readiness/request.md)에 기록했다.
실제 baseline snapshot은 `ffb7d62771f3e1e3801ec783e5a9696d8ac291a7`이며 당시 커밋 6개와 CI 성공,
라이선스·이슈·PR·릴리스 없음이 확인됐다. 당시 관측을 현재 상태로 재작성하지 않는다.

[실제 probe 결과](examples/support-readiness/runs/observed-02/result.json): 초기 3단계 생성 뒤 제목 변경은
B1이 2단계를 재사용하고 1단계를 실행했다. 독립 감사에서 최종 역할 계약 충족과 잘못된 사용 0건을 확인했다.
라이선스·유지관리·크레딧 필요성 열 3개는 현재 interface가 지원하지 않아 명시적으로 거절됐다.
이는 구조화된 입력·출력 기능의 부족이며 강한 재사용 정책의 실패나 AI 필요성으로 해석하지 않는다.
별도 저장소 사실을 입력으로 제공한 단순 체크리스트가 대안이다. 인간 작업 시간 절감은 측정하지 않았다.

실행: `PYTHONPATH=. uv run examples/support-readiness/probe.py examples/support-readiness/runs/observed-02`.
원본 실험 재실행·평가 대상 모델 호출·외부 API 비용은 0이며 구현 대화의 모델 비용은 측정 범위에서 제외했다.
[실제 검증 출력](examples/support-readiness/runs/observed-02/verification.json)도 보존했다.
CI와 타입·정적 검사 범위에 실제 probe 코드를 포함했고, 과거 코드 스냅샷만 검사 대상에서 제외했다.

observed-02 당시에는 자연어 의미의 인간 확인·해석 비교와 외부 개발자 재현이 후속 과제였다.
아래 후속 실행에서 의미 확인과 결정론적 작업 비교를 진행했다. 이를 자연어 정확성 평가로 취급하지 않는다.

2026-10-10 KST 공개 보완 완료:

- GitHub API가 MIT License를 인식했다.
- [공개 과제 #1](https://github.com/blakchomil/effici-lab/issues/1): 관측 요청의 의미 확인과 결정론적 해석·질문 대조군.
- [공개 과제 #2](https://github.com/blakchomil/effici-lab/issues/2): 외부 개발자의 독립 재현과 실제 기록.
- [v0.1.0 초기 개발 prerelease](https://github.com/blakchomil/effici-lab/releases/tag/v0.1.0)를 게시했다.
  태그는 실제 검증한 `27f0fda46379a7ed168a97346f84a11cb7793194`를 가리킨다.
- 이 커밋의 새 clone에서 77 tests passed in 1.05s, Ruff/formatting/type 검사, 원본 15/15·보고서 12/12·관측 probe exit 0.
- [같은 커밋의 Linux/macOS CI](https://github.com/blakchomil/effici-lab/actions/runs/38030712011)에서 모든 단계가 성공했다.
- [실제 검증 출력](docs/releases/v0.1.0-verification.json)과 테스트 XML을 릴리스 파일로 첨부했다.
  새 clone은 유지관리자 에이전트의 실행이며 외부 개발자의 독립 재현으로 세지 않는다.

추가 유료 API 호출은 하지 않았다. 이 보완은 초기 공개 준비이며 지속적 유지관리·외부 이용·AI 크레딧 필요성·
지원 프로그램 선정을 입증하지 않는다. 실제 외부 참여가 필요한 과제 #2는 열린 상태로 유지한다.

## 인간이 확인한 지원 현황 보고서 변경

사용자가 다음 답변을 직접 선택했다.
“지원 준비 현황으로 변경: 현재 라이선스·CI·릴리스 사실을 반영하고, 외부 재현·AI 우위처럼 아직 입증하지 못한 항목도 명시”.
질문에는 기존 수치·출처 보존 조건이 포함됐다. 원문 요청, 실제 질문·선택지·답변, 연구자 추가 입력을
구분해 보존했다. 이는 유지관리자에게 유도한 확인 답변이 있는 공개 개발 사례이며 외부 의견이나 숨겨진 평가가 아니다.

현재 사실은 `5066fa41e5d4cde50322f3795437c0565cfc8163`의 MIT, 해당 revision의 실제 CI success,
`27f0fda46379a7ed168a97346f84a11cb7793194`의 v0.1.0 개발 prerelease를 별도 snapshot에 기록했다.
외부 재현·AI 우위는 미입증으로 명시했다. 과거 pre-license snapshot은 수정하지 않았다.
CLI는 이 고정 사실을 재생하며 실행 시 GitHub에 접속하지 않는다.

공통 초기 숫자 보고서 3단계를 새로 측정해 실행하고 기존 observed-02 보고서와 바이트 일치를 확인한 뒤,
각 정책에 복제했다. 과거 production cache를 불러온 것으로 주장하지 않는다.
규칙/clarification 두 라벨은 같은 확인 선택 파서를 공유한다. 별개 자연어 알고리즘이나 질문의 효용을 비교하지 않았다.
확인된 B0와 두 라벨 각각의 B1/B2를 다섯 번 순환 순서로 실행했다. 한 요청의 반복이지 25개의 사용자 사례가 아니다.

| 조합 | 최종 충족 | 매번 새 단계 | 매번 숫자 단계 재사용 | 잘못된 재사용 |
| --- | ---: | ---: | ---: | ---: |
| confirmed B0 | 5/5 | 4 | 0 | 0 |
| rule B1 | 5/5 | 1 | 3 | 0/35 |
| rule B2 | 5/5 | 1 | 3 | 0/35 |
| clarification B1 | 5/5 | 1 | 3 | 0/35 |
| clarification B2 | 5/5 | 1 | 3 | 0/35 |

숫자 3단계의 가능한 계획을 독립적으로 열거하고, 현재 캐시에 없는 지원 현황 문서의 필수 조합 1회를
더한 실행 횟수 하한은 매번 1이다. 시간·달러 최적해가 아니다. B2는 매번 역할 내용을 재계산하는 검사 3회를
별도 계수·측정했다. 기존 숫자의 의미와 최종 문서의 원문 바이트 보존, 모든 실제 소비·공개, 실행 시도와
입력·코드·환경 근거를 감사했다. 이 확인된 사례에서 단순한 결정론적 방법이 충분하다는 부정 결과를 보존한다.

최종 실제 실행:

```bash
uv run python -m src.intent_revalidation.readiness_workflow --run-id readiness-20261010-01
uv run pytest -q --junitxml=runs/readiness-20261010-01/verification-tests.xml
uv run ruff check src tests examples
uv run ruff format --check src tests examples
uv run basedpyright
```

25/25, 145 tests passed in 2.03s, 정적 검사·formatting·타입 검사 통과.
Python 규칙 검사 15개 새 파일에 위반 없음. CLI 도움말 exit 0, 기존 run·없는 입력·잘못된 metrics·미응답·위험 ID는
각각 exit 2. 부정 입력은 결과 폴더를 만들지 않았다. 원본 metrics와 입력·코드 snapshot 해시도 일치했다.
code SHA256 `3b0c29106dd489f011ce189241cb9f713253890cf83412ce52a98a6e42d833cc`.

[최종 보고서](runs/readiness-20261010-01/report.md), [지표](runs/readiness-20261010-01/metrics.json),
[manifest](runs/readiness-20261010-01/manifest.json), [실제 검증 출력](runs/readiness-20261010-01/verification.json).
readiness-development-20261010-01은 입력 상대 경로 기록 오류로 정책 실행 전 실패했고 당시 코드·실패 기록을 보존했다.
readiness-development-20261010-02는 감사 보완 전 성공한 개발 실행으로, 최종 실행이 이를 덮어쓰지 않았다.

입력 준비·초기 seed·clone·정책 wall·사후 평가 시간을 분리했다. 내부 중첩 시간을 합산하지 않는다.
실제 확인 질문 1회와 답변 기록 재생을 구분했다. 사람 대기·수정 시간과 구현 모델 비용·로컬 달러 비용은 미측정이다.
원본 실험 재실행·평가 모델 호출·토큰·추가 유료 API 비용은 0이다. 밀리초 단위의 반복으로 안정적인 총비용
절감·일반화·외부 효용·AI 우위를 주장하지 않는다. 새 CLI를 Linux/macOS CI에 연결했다.
