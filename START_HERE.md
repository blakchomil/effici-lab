# Mac에서 연구 레포 시작하기

초기 배포 묶음은 연구 문서와 개발 예제였다. 2026-10-10 Mac Codex 작업에서 Phase 1 실행 엔진과 실제 결과를 추가했다.
현재 고정 폴더는 `/Users/yangjunmo/effici-lab/intent-revalidation-starter`이며 재현 명령은 [README.md](README.md)에 있다.
아래 폴더 생성 절차는 새 위치에서 시작할 때의 안내다. 현재 작업을 재개할 때는 [STATE.md](STATE.md)의 다음 연구 판단부터 이어간다.

## 1. 고정 폴더 만들기

다운로드한 파일을 `~/Downloads/intent-revalidation-starter.zip`에 둔다.

제안 폴더: `~/Projects/intent-revalidation-research`

이 이름은 설명용 작업 이름이다. 브랜드나 GitHub 이름의 중복 여부를 확정한 이름은 아니다.

터미널에서 아래 블록을 실행한다. 같은 경로가 이미 있으면 덮어쓰지 않고 멈춘다.

```bash
(
  set -e
  project_dir="$HOME/Projects/intent-revalidation-research"
  archive_path="$HOME/Downloads/intent-revalidation-starter.zip"

  if [ ! -f "$archive_path" ]; then
    printf '%s\n' "먼저 Downloads에 intent-revalidation-starter.zip을 저장해 주세요."
    exit 1
  fi

  if [ -e "$project_dir" ]; then
    printf '%s\n' "대상 폴더가 이미 있습니다. 기존 내용을 확인하거나 새 폴더명을 사용해 주세요."
    exit 1
  fi

  mkdir -p "$project_dir"
  unzip "$archive_path" -d "$project_dir"
  cd "$project_dir"
  git init
  codex
)
```

이 명령은 Mac에 Git과 Codex가 설치되어 있고 `codex` 명령으로 실행할 수 있다는 전제다. 여기서 사용자 Mac의 설치 상태를 확인한 것은 아니다.

재개할 때는 아래 두 줄이면 된다.

```bash
cd "$HOME/Projects/intent-revalidation-research"
codex
```

## 2. 지침은 세 파일로 시작한다

| 파일 | 담당하는 내용 |
| --- | --- |
| `AGENTS.md` | 목적을 유지하며 작업하는 방식 |
| `RESEARCH.md` | 연구 질문, 비교 실험, 성공·중단 기준 |
| `STATE.md` | 현재 상태, 실제 실행 증거, 다음 작업 |

세 파일은 이미 채워져 있다. 첫 세션을 지침서 작성에 다시 쓰지 않아도 된다.

새 프로젝트 폴더를 만든다고 Codex의 전역 설정이 사라지는 것은 아니다. 공식 문서는 기본 Codex home의 `AGENTS.override.md` 또는 `AGENTS.md`와 프로젝트 경로의 지침을 읽는다고 설명한다. Codex home은 보통 `~/.codex`이며 설정에 따라 달라질 수 있다. 프로젝트의 `RESEARCH.md`, `STATE.md`는 이 프로젝트의 지시대로 명시적으로 읽는다. [S1]

기존 개인 지침의 적용 범위를 먼저 확인한다. 연구를 위해 전역 지침을 삭제하거나 자동 승인 설정을 바꿀 필요는 없다. 실제 충돌이 있다면 어떤 문장과 적용 범위가 충돌하는지 확인한 후 해결한다.

## 3. Codex 첫 프롬프트

아래 전체를 붙여 넣는다.

```text
이 저장소에서 “사용자 요구 변경 이후 산출물의 유효성을 검증하고 필요한 작업만 다시 실행하는 연구”를 시작하자.

먼저 실제로 적용되는 전역·프로젝트 지침을 확인하고 AGENTS.md, RESEARCH.md, STATE.md, examples/dev_cases.json을 읽어라. 확인하지 못한 환경이나 지침은 미확인이라고 적어라. 기존 운영 시스템에 한정된 지침은 그 적용 범위를 확인하고, 이 독립 연구의 목적을 다른 운영 목적과 혼동하지 마라.

이번 작업은 RESEARCH.md의 Phase 1을 완료하는 것이다. 목표와 완료 조건을 짧게 확인한 뒤 실제 파일을 구현하고 실행 결과까지 남겨라. 지침서를 늘리는 작업으로 끝내지 마라.

구현:
1. examples/usage.csv를 입력으로 load → normalize → aggregate → render 파이프라인을 Python 표준 라이브러리 우선으로 구현한다.
2. 요구 revision, task, 실행 attempt, 불변 artifact, 역할별 유효성 평가를 구분한다. provenance, 내용 해시, 소비 역할, 실행 이벤트를 기록한다.
3. B0 전체 재실행, B1 관련 요구 필드·입력·코드 기반의 세분화된 캐시, B2 실행 가능한 계약 검증 후 선택적 재실행을 구현한다. B1/B2가 사용할 정보를 부당하게 줄이지 마라.
4. 개발 사례 5개를 실제 실행한다. HTML 변경, 기간 변경, 의미상 무변경, 이전 revision의 유효한 집계가 늦게 도착하는 경우, 무효한 보고서가 늦게 도착하는 경우다. D4/D5는 이벤트 1~3을 모두 재생한 뒤 정책을 실행하는 개발 검증이다.
5. 과거 결과는 현재 역할의 계약을 충족하면 재사용할 수 있다. 오래된 revision이라는 이유만으로 모두 버리지 말고, 늦게 도착했다는 이유만으로 현재 완료 상태를 덮어쓰지도 마라.
6. 작은 작업 그래프에서 현재 보유 캐시와 허용 연산으로 만들 수 있는 유효 계획을 열거하는 참조 계산기를 만든다. 이 참조 계산기는 평가용이며 정책에 정답을 주는 도구가 아니다.
7. 정답을 “특정 행동 라벨을 골랐는지”로만 채점하지 말고, 최종 요구 충족과 실제 사용된 artifact의 유효성을 독립적으로 확인한다.
8. 총 단계 실행, 검사, 변환, 실제 시간과 실패를 기록하고 정책별 결과를 Markdown으로 비교한다. 최초 유효 결과까지의 시간과 남은 실행이 종료·취소될 때까지의 총비용을 구분한다. 인위적 sleep으로 절감 효과를 만들지 마라.
9. 의미 있는 오류 사례를 테스트하고 실제 실행 명령·결과 경로를 README.md와 STATE.md에 기록한다.

이번 단계에서 AI 정책, React UI, 범용 오케스트레이터, 서버 배포는 구현하지 않는다. 이들은 후속 연구다.
필요한 통상적인 로컬 수정과 검증은 자율적으로 마쳐라. 새 외부 서비스나 유료 호출이 없어도 Phase 1은 완료할 수 있어야 한다.

마지막에는 실제로 만든 것, 실행 결과, 비교군의 강점과 한계, AI가 추가로 해결할 여지가 확인되었는지를 보고하라.
아직 비교군으로 해결되지 않는 문제가 없다면 없다고 적어라. Phase 1을 AI의 효과나 독창성 입증으로 포장하지 마라.
```

## 4. 첫 세션에서 받아야 할 결과

- 실제로 재실행할 수 있는 명령과 생성된 보고서.
- 각 요구 변경에서 무엇을 재사용·검증·재실행했는지와 근거.
- 비교군별 최종 요구 충족 여부와 실제 작업·검증 비용.
- 늦게 도착한 결과를 처리한 이벤트 기록.
- “AI가 추가로 풀 문제가 남았는가?”에 대한 관측에 근거한 답.

계획만 작성했거나 화면만 그렸다면 첫 단계는 아직 끝난 것이 아니다.

## 5. 다음 세션

```text
AGENTS.md, RESEARCH.md, STATE.md와 직전 실험 결과를 읽고 이어서 진행하자.
현재 가설을 바꿀 필요가 있는지 증거로 판단해라.
STATE.md에 기록된 다음 작업부터 시작하고, 연구 범위를 넓히기 전에 그것이 어떤 미해결 관측을 설명하는지 적어라.
```

## 출처

[S1] OpenAI, Custom instructions with AGENTS.md. 확인: 2026-10-10 KST.
https://learn.chatgpt.com/docs/agent-configuration/agents-md
