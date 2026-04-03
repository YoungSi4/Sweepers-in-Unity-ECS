# C# Code Reviewer Architecture — Overview

Assets/Scripts 경로의 C# 스크립트를 자동으로 리뷰하고 리팩터링하는 **6단계 에이전트 파이프라인**입니다.

---

## 전체 파이프라인

```
[C# 파일 입력]
    ↓
[1. Planner] 8가지 기준으로 코드 분석 & 계획 수립
    ↓
[2. Reviewer] 완성도(1-10) + 실현가능성(1-10) 평가 → 8점 이상 APPROVED
    │
    ├─ (<8점, 최대 3회) → Planner 재작업 → [2. Reviewer] 재평가 (반복)
    │
    └─ (≥8점, 또는 3회 실패) → [3. User Approval 1]
    ↓
[3. User Approval 1] 변경 예정사항 사용자 확인 & 승인 ← ⭐ 사용자 개입
    │
    ├─→ (✅ 승인) → [4. Coder]
    └─→ (❌ 거부) → [종료]
    ↓
[4. Coder] Planner 계획 & Reviewer 피드백 기반 코드 구현
    ↓
[5. User Approval 2] 변경된 코드 사용자 확인 & 최종 승인 ← ⭐ 사용자 개입
    │
    ├─→ (✅ 승인) → [6. 파일 적용]
    └─→ (❌ 거부) → 폐기 또는 중단 → [종료]
    ↓
[6. 파일 적용] 원본 파일 백업, 새 코드 기록, 보고서 생성
    ↓
[완료]
```

---

## 핵심 특징

### ✅ 사용자 검증 2단계
1. **User Approval 1**: 변경될 사항을 **사전에 확인**
2. **User Approval 2**: 변경된 코드를 **사후에 확인**

### ✅ Reviewer 점수 시스템
- **완성도** (1-10): 계획이 충분히 구체적인가?
- **실현 가능성** (1-10): Coder가 실제로 구현할 수 있는가?
- **통과 기준**: 평균 ≥8점
- **재시도 정책**: Planner-Reviewer 루프는 최대 3회까지만 반복
  - 1회: 초기 계획 검증
  - 2-3회: 8점 미만 시 Planner 재작업 후 재평가
  - 3회 후 여전히 8점 미만 → 파이프라인 중단, 사용자에게 재작업 요청

### ✅ 사용자 거부 처리
User Approval 2에서 거부 시:
- **폐기**: 변경사항 버림, 파이프라인 중단

### ✅ 아키텍처 유연성
- **ECS (ISystem)**: 엄격한 기준 (Managed 타입 금지)
- **MonoBehaviour**: 유연한 기준 (Managed 타입 허용)

---

## 파이프라인 단계별 요약

| 단계 | 역할 | 입력 | 출력 | 다음 단계 |
|------|------|------|------|---------|
| 1. Planner | 분석 & 계획 | 코드 + git diff | 리팩터링 계획 | Reviewer |
| 2. Reviewer | 평가 (1-10) | 코드 + 계획 | 점수 + 피드백 | UA1 (≥8점) / Planner 재작업 (<8점) |
| 3. UA1 | 사용자 확인 | 계획 요약 | 승인/거부 | Coder (✅) / 중단 (❌) |
| 4. Coder | 구현 | 계획 + 피드백 | 리팩터링 코드 | UA2 |
| 5. UA2 | 최종 확인 | 변경 전/후 코드 | 승인/거부 | 파일적용 (✅) / 중단 (❌) |
| 6. 파일 적용 | 자동 기록 | 리팩터링 코드 | 백업 + 파일 수정 | 완료 |

---

## 코드 리뷰 기준 (8가지)

Planner가 분석하는 항목:

1. **네이밍 규칙** - PascalCase, _camelCase, camelCase 준수
2. **ECS/DOTS 패턴** - MonoBehaviour vs ISystem 아키텍처 선택
3. **Burst 컴파일** - ECS는 엄격, MonoBehaviour는 유연
4. **메모리 안전성** - NativeContainer (ECS) vs Null 참조 (Mono)
5. **코드 복잡도** - 메서드 길이, 순환 복잡도, 책임 분리
6. **성능 특성** - GC 압력, 캐싱 기회, 알고리즘 효율
7. **문서화 & 주석** - 비자명한 로직의 설명
8. **안전성 & 에러 처리** - Null 체크, 범위 검사, 예외 처리

---

## 에이전트 호출 방식 (stdin + --system-prompt-file)

**목표: 토큰 절약**

각 subprocess 에이전트는:
1. stdin으로 **파일 경로만** 받음 (코드 내용 미포함)
2. `--system-prompt-file`로 System Prompt 로드
3. Read 도구로 **필요한 파일들을 직접 읽음**

```
Orchestrator:
  파일 경로 → stdin
      ↓
Claude CLI:
  - .claude/agents/{agent_name}.md 로드 (--system-prompt-file)
  - stdin에서 user_prompt 수신
  - 에이전트 실행
      ↓
에이전트 (Read 도구 사용):
  - 파일 경로에서 원본 코드 읽음
  - 임시 파일 경로에서 계획/피드백 읽음
  - 분석/평가/구현 수행
```

**예시:**

Planner:
```
stdin: "대상 파일: Assets/Scripts/TestSystem.cs\n\n위 파일을 Read 도구로 읽어 분석하세요."

에이전트가 Read로:
  - Assets/Scripts/TestSystem.cs 읽음
  - 분석 수행
```

Reviewer:
```
stdin: "대상 파일: Assets/Scripts/TestSystem.cs\nPlanner 계획 파일: .tmp/planner.md\n\n위 파일들을 Read로 읽어 평가하세요."

에이전트가 Read로:
  - Assets/Scripts/TestSystem.cs 읽음
  - .tmp/planner.md 읽음
  - 평가 수행
```

---

## Stage 6: 파일 적용 (자동 처리)

User Approval 2에서 승인 시 자동으로 수행됩니다.

### 처리 절차

1. **코드 추출 및 검증**
   - Coder 출력에서 ```csharp...``` 범위 추출
   - 정규표현식 (견고한 버전):
     ```python
     pattern = r'```csharp\s*\n(.*?)\n```'
     match = re.search(pattern, coder_output, re.DOTALL)
     if match:
         code = match.group(1).strip()
     ```
   - 검증:
     - 코드가 50자 이상인가? (최소 검증)
     - C# 문법 특성이 포함되어 있는가? (using, class, public 등)
   - 추출 실패 시 에러 로깅 및 파이프라인 중단

2. **원본 파일 백업**
   - 경로: `{filename}.backup.cs`
   - 위치: 원본 파일과 같은 디렉토리
   - 목적: 실수로 인한 파일 손상 복구

3. **파일 갱신 (원자적 쓰기)**
   - 임시 파일에 새 코드 작성
   - 원본 파일을 임시 파일로 교체 (원자적)
   - 목적: 부분 쓰기로 인한 파일 손상 방지

4. **최종 보고서 생성**
   - 위치: `claude_tools/review_outputs/{timestamp}_{filename}_review.md`
   - 내용:
     - 원본 파일 경로
     - 변경 시각
     - 백업 파일 위치
     - Planner 분석 결과
     - Reviewer 평가 점수
     - Coder 변경 사항 요약
     - (선택) git diff 요약

### 파일명 규칙

| 파일 | 규칙 | 예시 |
|------|------|------|
| **원본** | 기존 유지 | `MoveSystem.cs` |
| **백업** | `{name}.backup.cs` | `MoveSystem.backup.cs` |
| **보고서** | `{timestamp}_{name}_review.md` | `20260403_143000_MoveSystem_review.md` |

### 에러 처리

#### Coder 출력 형식 오류

코드 추출 실패 시:
```
[FAIL] Coder 출력 형식 오류

예상 형식:
```csharp
[전체 파일 코드]
```

다시 확인:
- "```csharp"로 정확히 시작
- 다른 코드블록 없음
- "```"로 정확히 종료

→ 파이프라인 중단, 사용자 피드백 요청
```

#### Planner 3회 재시도 실패

Reviewer가 3회 연속 8점 미만인 경우:

**동작:**
1. Planner-Reviewer 루프 중단
2. 최종 보고서 생성: `claude_tools/review_outputs/FAILED_{timestamp}_{filename}_planner_review_summary.md`
3. 파이프라인 중단, 사용자에게 보고서 제시

**최종 보고서 형식:**

```markdown
# Planner 재시도 실패 보고서

## 메타데이터
- **파일**: {filepath}
- **생성 시각**: {timestamp}
- **상태**: Planner-Reviewer 루프 3회 연속 실패

## 최종 Planner 계획 (3회차)

{planner_plan_full_text}

---

## Reviewer 최종 평가 (3회차)

### 평가 결과

**평균 점수**: X/10 (8점 미만 - 통과 기준 미달)

### 항목별 점수

#### [P1] 항목명
- 완성도: X/10 (분석)
- 실현 가능성: Y/10 (분석)
- **종합 점수: Z/10**
- 피드백: {개선 사항}

#### [P2] 항목명
...

### 개선 필요 사항

Planner가 다시 개선해야 할 항목 (Reviewer 피드백):
1. [항목명] (현재 Z/10): {문제점} → {권장 개선 방향}
...

---

## 권장 사항

### 원인 분석

Planner 계획이 3회 연속 거부된 주요 이유:
- 항목별 변경 위치가 명확하지 않음
- 현재 상태 설명이 불충분함
- 변경 방향이 너무 추상적임
- Coder가 구현하기에 지시사항이 모호함

### 다음 단계

1. **Planner 계획 수동 개선**
   - 위의 "개선 필요 사항"을 참고하여 계획 재작성
   - 각 항목의 변경 위치, 현재 상태, 변경 방향을 더 구체적으로

2. **재시도**
   ```bash
   python cs_code_reviewer.py --target {filepath}
   ```

3. **자동 리팩터링 포기**
   - 이 파일은 수동 검토가 필요한 것으로 판단
   - 직접 코드 분석 및 리팩터링 수행

---

## 첨부: 원본 코드

{original_file_content}
```

**파일 저장 위치:**
```
claude_tools/review_outputs/FAILED_{timestamp}_{filename}_planner_review_summary.md
```

예: `claude_tools/review_outputs/FAILED_20260403_143000_MoveSystem_planner_review_summary.md`

---

## User Approval 1 (UA1) — 변경 예정사항 확인

변경될 코드 사항에 대해 사용자의 사전 승인을 획득합니다.

### UA1 출력 형식

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

### UA1 사용자 입력

- **승인**: Coder 단계로 진행
- **거부**: 파이프라인 중단

### UA1 입력 모드 (자동 감지)

- **대화형**: `input()` 대기
- **자동 승인** (`--auto-approve`): 자동 "승인"
- **비대화형** (stdin 없음): 기본값 "거부"

---

## User Approval 2 (UA2) — 변경된 코드 최종 확인

Coder의 구현 결과물을 검토하고 최종 판정합니다.

### UA2 출력 형식

```
================================================================================
변경된 코드 확인 (User Approval 2)
================================================================================

파일: {filepath}

변경 전 (원본):
```csharp
{original_code}
```

변경 후 (리팩터링):
```csharp
{refactored_code}
```

Coder 변경 사항 요약:
{coder_changes_summary}

================================================================================
변경을 승인하시겠습니까?
선택 (승인/거부):

거부 선택 시 옵션:
폐기 - 변경사항 버림, 파이프라인 중단
```

### UA2 사용자 입력

- **승인**: 파일 적용 (Stage 6) 진행
- **거부 → 폐기**: 파이프라인 중단, 변경사항 버림

### UA2 입력 모드 (자동 감지)

- **대화형**: `input()` 대기
- **자동 승인** (`--auto-approve`): 자동 "승인"
- **비대화형** (stdin 없음): 기본값 "거부"

---

## User Approval 입력 모드 (공통)

Orchestrator는 실행 환경에 따라 자동으로 입력 모드를 감지합니다:

### 모드 1: 대화형 (기본)
- **조건**: 터미널에서 직접 실행
- **동작**: `input()` 대기 (사용자 입력 대기)
- **사용 시기**: 개발 중 수동 리뷰
- **예시**: `python cs_code_reviewer.py --target file.cs`

### 모드 2: 자동 승인
- **조건**: `--auto-approve` 플래그 사용
- **동작**: 모든 User Approval에서 자동 "승인"
- **사용 시기**: 테스트, 신뢰할 수 있는 코드 배치 처리
- **예시**: `python cs_code_reviewer.py --target file.cs --auto-approve`

### 모드 3: 비대화형 (안전 모드)
- **조건**: stdin 없음 (파이프, 백그라운드, CI/CD)
- **동작**: `input()` 대신 안전한 기본값 사용
  - UA1 (변경 예정사항): 기본값 "거부" (보수적)
  - UA2 (최종 확인): 기본값 "거부" (보수적)
- **사용 시기**: 자동화 파이프라인, CI/CD 환경
- **예시**: `python cs_code_reviewer.py --target file.cs < /dev/null`

### 입력 모드 감지 로직

```python
import sys

class InputModeDetector:
    @staticmethod
    def detect(auto_approve: bool) -> str:
        """실행 환경에 따라 입력 모드 감지"""
        if auto_approve:
            return "auto_approve"
        elif sys.stdin.isatty():  # 터미널 연결
            return "interactive"
        else:  # stdin 없음
            return "non_interactive"
```

---

## 사용 방법

```bash
# 대화형 모드 (기본) — 터미널에서 수동 승인
python cs_code_reviewer.py --target Assets/Scripts/Systems/MoveSystem.cs

# 자동 승인 모드 — 모든 단계 자동 진행
python cs_code_reviewer.py --target Assets/Scripts/Systems/MoveSystem.cs --auto-approve

# 비대화형 모드 (CI/CD) — stdin 없음, 안전 기본값
python cs_code_reviewer.py --target Assets/Scripts/Systems/MoveSystem.cs < /dev/null

# 출력
claude_tools/review_outputs/{timestamp}_{filename}_review.md
```

---

## 문서 구조

- **cs_code_reviewer_architecture.md** (본 문서) - 전체 개요
- **cs_code_reviewer_agents.md** - 각 에이전트 상세 정의
- **.claude/agents/planner.md** - Planner Agent System Prompt
- **.claude/agents/reviewer.md** - Reviewer Agent System Prompt
- **.claude/agents/coder.md** - Coder Agent System Prompt
- **.claude/prompts/user_approval_1.md** - User Approval 1 출력 형식
- **.claude/prompts/user_approval_2.md** - User Approval 2 출력 형식
