# User Approval 1 — 변경 예정사항 확인

변경될 코드 사항에 대해 사용자의 사전 승인을 획득합니다.

## 역할

- Reviewer 승인 후 사용자에게 변경될 사항을 사전 공지
- 변경에 대한 명시적 승인 획득
- 거부 시 파이프라인 중단

## 입력

- Reviewer 평가 점수 및 피드백
- Planner 최종 계획
- 원본 코드 미리보기

## 출력 형식

```
================================================================================
변경 예정 사항 (User Approval 1)
================================================================================

파일: {filepath}

Planner 코드 품질 분석:
{planner_analysis_section}

Planner 리팩터링 계획:
{planner_plan_section}

Reviewer 평가 결과:
{reviewer_evaluation_section}

**평균 점수**: X/10
**판정**: APPROVED ✓

================================================================================
변경을 진행하시겠습니까?
선택 (승인/거부):
```

## 사용자 입력

- **승인**: Coder 단계로 진행
- **거부**: 파이프라인 중단

## 입력 모드 (자동 감지)

- **대화형**: `input()` 대기 (터미널에서 직접 실행)
- **자동 승인** (`--auto-approve` 플래그): 자동 "승인"
- **비대화형** (stdin 없음): 기본값 "거부" (안전)

### 모드 감지 로직

```python
if auto_approve:
    mode = "auto_approve"
elif sys.stdin.isatty():  # 터미널 연결
    mode = "interactive"
else:  # stdin 없음
    mode = "non_interactive"
```
