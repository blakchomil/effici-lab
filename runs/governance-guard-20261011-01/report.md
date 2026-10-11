# 로컬 거버넌스 도구 실제 CLI 검증

결과: 8/8

| 상황 | 결과 |
| --- | --- |
| before_verification_denied | True |
| verified_publication_allowed | True |
| changed_input_denied | True |
| recheck_restores_permission | True |
| changed_instruction_denied | True |
| failed_verification_denied | True |
| protected_denied_ordinary_allowed | True |
| current_instruction_reinjected | True |

실제 CLI·검증 명령·게시 스크립트를 실행한 도구 기능 검증이다.
훅 입력은 테스트 드라이버가 제공했다. 실제 Claude 압축·재시작·위임 평가가 아니다.
모델 호출은 없고, 세 방법의 AI 준수 효과 비교는 아직 미평가다.
[명령과 실제 출력](commands.json) · [지표](metrics.json) · [코드 스냅샷](manifest.json)

공개 사본의 개인 경로는 가렸다. 원본 기록은 로컬에 보존했으며 [가림 처리와 바이트 해시](publication-redaction.json)를 남겼다.
