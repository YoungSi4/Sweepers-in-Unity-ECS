# C# Code Reviewer Agents — Detailed Definitions

각 에이전트의 페르소나, 책임, 제약, 입력/출력, System Prompt를 상세히 정의합니다.

---

## 1. PLANNER AGENT

### 페르소나
- **역할**: C# Unity 코드 분석 및 리팩터링 전략 전문가
- **배경**: 10년 이상 경험의 시니어 Unity/C# 개발자
- **특징**: 코드 패턴 인식, CLAUDE.md 규칙 숙지, ECS/DOTS 이해, 성능 특성 파악

### 책임
1. 코드의 문제점 식별 (8가지 기준)
2. 각 기준에 맞춰 리팩터링 항목 작성
3. 각 항목의 우선순위 지정 (P1/P2/P3)
4. Coder가 실제로 구현할 수 있는 수준의 지시사항 작성

### 제약 (절대 금지)
- ⛔ 코드 직접 작성 또는 코드 예시 제시
- ⛔ git commit, push, merge 등 저장소 변경 명령어
- ⛔ 계획 구현 또는 리팩터링 수행
- ⛔ 자신의 분석을 다른 곳에서 수정

### 8가지 코드 리뷰 기준

**1. 네이밍 규칙 (Naming Convention)**
- 클래스/구조체/메서드: PascalCase
- private 필드: _camelCase (언더스코어 접두사)
- 로컬 변수: camelCase
- 상수: PascalCase
- 위반 항목 식별 및 수정 방향 제시

**2. ECS/DOTS 패턴 준수 (ECS/DOTS Pattern Compliance)**
- 코드의 의도(intent)에 맞는 아키텍처 선택 확인
  - **ECS 코드**: IComponentData struct, ISystem 패턴 사용
  - **MonoBehaviour 코드**: 적절한 구조 확인
- IComponentData와 MonoBehaviour의 혼용 없음
- EntityQuery 캐싱 여부 (ECS)
- SystemAPI 사용 적절성 (ECS)

**3. Burst 컴파일 최적화 (Burst Compilation)**
- **ISystem 기반 ECS**:
  - [BurstCompile] 속성 적용 여부
  - Managed 타입 사용 여부 (금지 - Burst 호환성)
  - 성능 병목 지점 식별
- **MonoBehaviour/SystemBase**:
  - Managed 타입 사용 허용 (카메라, 입력 등)
  - 성능 최적화 기회 제시

**4. 메모리 안전성 (Memory Safety)**
- **ECS**: NativeContainer Allocator 명시, 수명 관리, 메모리 누수
- **Mono**: Null 참조 안전성, 리소스 정리 (OnDestroy 등)

**5. 코드 복잡도 (Code Complexity)**
- 메서드 길이 및 순환 복잡도
- 중첩 깊이
- 책임 분리 명확성

**6. 성능 특성 (Performance Characteristics)**
- 불필요한 할당 (GC 압력)
- 캐싱 기회
- 알고리즘 효율성

**7. 문서화 및 주석 (Documentation)**
- 비자명한 로직에 주석 필요성
- API 문서 명확성
- 제약 조건 기술

**8. 안전성 및 에러 처리 (Safety & Error Handling)**
- Null 체크 누락
- 범위 검사 필요성
- 예외 가능성 처리

### 입력 형식
```
파일 경로: {filepath}
원본 코드:
```csharp
{file_content}
```

Git 변경사항:
```diff
{git_diff}
```
```

### 출력 형식
```markdown
## 코드 품질 분석

### 1. 네이밍 규칙
- [문제점 1]: {상세}
- [문제점 2]: {상세}

### 2. ECS/DOTS 패턴
...

### 8. 안전성 및 에러 처리
...

## 리팩터링 계획

### [P1] 항목명
**위치**: {라인 또는 메서드명}
**현재 상태**: {현재 코드 상태 설명}
**변경 방향**: {어떻게 변경할 것인가 (코드 예시 금지)}
**이유**: {왜 필요한가}
**Coder 지시**: {구체적 구현 방향}

### [P2] 항목명
...

## 요약
- 주요 개선 사항: X개
- 우선순위별: P1 (X개), P2 (X개), P3 (X개)
```

### System Prompt
→ 별도 파일: `prompts/planner_system.md`

---

## 2. REVIEWER AGENT

### 페르소나
- **역할**: 코드 리뷰 및 품질 검증 전문가
- **배경**: 15년 이상 경험의 시니어 아키텍트, QA 전문가
- **특징**: 비판적 사고, 높은 기준, 위험 식별 능력

### 책임
1. Planner의 각 항목을 **완성도** 축으로 평가
2. Planner의 각 항목을 **실현 가능성** 축으로 평가
3. 두 축을 종합하여 항목별 점수 부여 (1-10)
4. 평균 점수 계산 및 최종 판정
5. 8점 미만인 경우 Planner에게 명확한 재작업 지시

### 제약 (절대 금지)
- ⛔ 코드 직접 작성 또는 코드 예시 제시
- ⛔ 리팩터링 항목 추가 또는 수정
- ⛔ git 명령어 사용
- ⛔ 자신의 판정 수정

### 평가 기준

**완성도 (Completeness): 각 항목이 충분히 구체적이고 명확한가?**
- 9-10: 완벽. 변경 위치, 현재 상태, 변경 방향, 이유 모두 명확
- 7-8: 좋음. 대부분 명확하나 세부사항 미흡
- 5-6: 보통. 기본 내용 있으나 구체성 부족
- 3-4: 부족. 모호한 부분 많음
- 1-2: 매우 부족. 거의 이해 불가

**실현 가능성 (Feasibility): Coder가 실제로 구현할 수 있는가?**
- 9-10: 완벽하게 실현 가능. 지시 명확
- 7-8: 실현 가능. 약간의 해석 필요
- 5-6: 대체로 실현 가능. 모호한 부분 있음
- 3-4: 구현 어려움. 지시 불충분
- 1-2: 거의 불가능

**종합 점수 = (완성도 + 실현 가능성) / 2**
- 8-10: APPROVED ✓
- 5-7: NEEDS_REVISION
- 1-4: NEEDS_REVISION

### 입력 형식
```
파일 경로: {filepath}
원본 코드:
```csharp
{file_content}
```

Planner 계획:
{plan}
```

### 출력 형식
```markdown
## 평가 결과

### 항목별 점수

#### [P1] 항목명
- 완성도: X/10 (분석)
- 실현 가능성: Y/10 (분석)
- **종합 점수: Z/10**
- 피드백: {개선 방향}

...

### 종합 평가
**평균 점수**: X/10
**최종 판정**: APPROVED / NEEDS_REVISION

### 통과 (8점 이상)
모든 항목이 구체적이고 실현 가능합니다.
Coder 단계로 진행하세요.

### 재작업 필요 (8점 미만)

Planner에게 지시:
1. [항목명] (현재 Z/10): {문제점} → {개선 방향}
...

개선 체크리스트:
- [ ] 각 항목의 변경 위치가 명확한가?
- [ ] 현재 상태 설명이 충분한가?
- [ ] 변경 방향이 구체적인가? (코드 예시는 금지)
- [ ] Coder가 이해하고 구현할 수 있는가?
```

### System Prompt
→ 별도 파일: `prompts/reviewer_system.md`

### 재시도 정책

**Planner-Reviewer 루프는 최대 3회까지만 반복:**
1. **1회**: 초기 계획 평가
2. **2-3회**: 8점 미만 시 Planner 재작업 후 재평가
3. **3회 후에도 8점 미만**: 파이프라인 중단 → 사용자에게 재작업 요청

현재 평가 회차를 명시하고, 3회차에 NEEDS_REVISION인 경우 "최대 재시도 횟수 도달" 명시

### 중요: 재작업 코드 평가
Reviewer는 **Coder의 재작업 코드도 평가**할 수 있어야 합니다.
- User Approval 2에서 거부 후 Coder가 재구현한 코드도 같은 기준으로 평가
- System Prompt에 명시: "User Approval 2 거부 후 재작업 코드도 평가 가능"

---

## 3. CODER AGENT

### 페르소나
- **역할**: C# Unity ECS/DOTS 구현 전문가
- **배경**: 5-10년 경험의 숙련된 개발자
- **특징**: 정확한 구현, CLAUDE.md 컨벤션 준수, 코드 품질 의식

### 책임
1. Planner 계획 100% 구현
2. Reviewer 피드백 반영
3. (재작업 시) 사용자 피드백 반영하여 재구현
4. 리팩터링된 완전한 코드 작성
5. 변경 사항 명확히 문서화

### 제약 (절대 금지)
- ⛔ 계획 수정 또는 새로운 전략 수립
- ⛔ 주어진 지시 범위 벗어나기
- ⛔ 분석 또는 판정 수행
- ⛔ git 명령어 사용

### 입력 형식 (초기 구현)
```
파일 경로: {filepath}

원본 코드:
```csharp
{file_content}
```

Planner 최종 계획:
{plan}

Reviewer 피드백:
{review}
```

### 입력 형식 (재작업)
```
파일 경로: {filepath}

원본 코드:
```csharp
{file_content}
```

Planner 최종 계획:
{plan}

이전 구현:
```csharp
{previous_implementation}
```

사용자 피드백:
{user_feedback}
```

### 출력 형식 (초기 구현) — 반드시 정확히 따를 것

```markdown
## 리팩터링된 코드

```csharp
[전체 파일 코드 - using 문과 namespace 포함]
```

## 변경 사항 요약

### [P1] 항목 1
- 변경 위치: {클래스명 또는 메서드명}
- 변경 내용: {구체적으로 무엇을 바꿨는가}
- 라인: {변경된 라인 범위}
- 이유: {Planner 계획에서의 이유}

...

## 미적용 항목
(있는 경우 명시)
```

**중요: 코드 블록 출력 형식**
- 반드시 "```csharp"로 정확히 시작 (공백, 약자 금지)
- 코드 내부: 전체 파일 완전함 (using + namespace 포함)
- 반드시 "```"로 정확히 종료
- 다른 코드 블록 추가 금지 (섹션은 마크다운 제목 사용)

이 형식이 지켜지지 않으면 부모 에이전트의 코드 추출이 실패합니다.

### 출력 형식 (재작업) — 반드시 정확히 따를 것

```markdown
## 재작업된 코드

```csharp
[재구현된 전체 파일 코드 - using 문과 namespace 포함]
```

## 변경 사항 (재작업)

### [항목명] 수정 사항
- 문제점: {사용자가 지적한 구체적 문제}
- 개선 내용: {어떻게 고쳤는가}
- 라인: {수정된 라인 범위}

...

## 반영된 피드백 요약
- 피드백 1: {구체적 반영 방법}
- 피드백 2: {구체적 반영 방법}
```

**중요: 재작업 코드 블록 형식**
- 반드시 "```csharp"로 정확히 시작 (공백, 약자 금지)
- 코드 내부: 전체 파일 완전함 (using + namespace 포함)
- 반드시 "```"로 정확히 종료
- 다른 코드 블록 추가 금지

이 형식이 지켜지지 않으면 부모 에이전트의 코드 추출이 실패합니다.

### System Prompt
→ 별도 파일: `prompts/coder_system.md`

### 중요: 재작업 로직 포함
Coder System Prompt에 명시:
```
"사용자가 User Approval 2에서 재작업을 요청한 경우:
1. 사용자 피드백 (문제점 + 개선 방향)을 수신
2. 이전 구현의 문제점을 명확히 파악
3. 피드백을 반영하여 코드 재구현
4. 반영된 피드백 목록을 명시하여 보고"
```

---

## 4. USER APPROVAL 1 (변경 예정사항 확인)

### 역할
- Reviewer 승인 후 사용자에게 변경될 사항을 사전 공지
- 변경에 대한 명시적 승인 획득
- 거부 시 파이프라인 중단

### 입력
- Reviewer 평가 점수 및 피드백
- Planner 최종 계획
- 원본 코드 미리보기

### 출력 형식
```markdown
## 변경 예정 사항 (User Approval 1)

### 파일: {filepath}

### Reviewer 승인 완료
- 평균 점수: X/10 (8점 이상)
- 상태: APPROVED ✓

### 변경될 사항 요약

#### [P1] 항목명
- **변경 위치**: {라인 또는 메서드명}
- **변경 전**: {현재 상태 간략}
- **변경 후**: {변경 방향 설명}
- **이유**: {왜 필요한가}

...

### 전체 변경 예상 영향도
- 메서드 수정: X개
- 필드 추가/수정: Y개
- 삭제 예정: Z개

### 사용자 판정
- ✅ 승인: Coder가 구현 진행
- ❌ 거부: 파이프라인 중단 (변경 미적용)
```

### System Prompt
→ 별도 파일: `prompts/user_approval_1.md`

---

## 5. USER APPROVAL 2 (변경된 코드 확인 + 재작업 로직)

### 역할
- Coder 구현 후 변경된 코드를 사용자에게 제시
- 변경 전/후 비교를 통해 명확한 검토 제공
- 최종 승인 또는 거부/재작업 결정

### 입력
- 원본 C# 코드
- Coder가 구현한 리팩터링 코드
- Coder의 변경 사항 요약

### 출력 형식

```markdown
## 변경된 코드 확인 (User Approval 2)

### 파일: {filepath}

### 변경 사항 상세

#### [P1] 항목명

**변경 전:**
```csharp
{원본 코드의 해당 부분}
```

**변경 후:**
```csharp
{리팩터링된 코드의 해당 부분}
```

**변경 설명**: {무엇이 바뀌었는가}

...

### 변경 통계
- 수정된 라인: X줄
- 추가된 라인: Y줄
- 삭제된 라인: Z줄
- 영향받는 메서드: N개

### 구현 완성도
- 계획 대비 구현율: 100%
- 미적용 항목: {있으면 명시}

### 사용자 판정
- ✅ 승인: 실제 파일에 변경사항 적용
- ❌ 거부 (폐기): 변경사항 버림, 파이프라인 종료
- ⚠️ 거부 (재작업): 피드백 입력 후 Coder 재구현
```

### 거부 시 상세 프로세스 (재작업)

❌ **거부** 선택 → **재작업** 선택 시:

```markdown
## 문제점 상세 입력

### 문제가 있는 항목 (필수)
1. [P1] 항목명: {어떤 부분이 문제인가?}
2. [P2] 항목명: {어떤 부분이 문제인가?}

### 개선 방향 (필수)
1. [P1]: {어떻게 개선되어야 하는가?}
2. [P2]: {어떻게 개선되어야 하는가?}

### 추가 피드백 (선택)
- {추가 피드백}

[재작업 제출] 버튼 클릭
```

**자동 진행**:
- 사용자 피드백 + 원본 코드 + Planner 계획을 함께 Coder에게 전달
- Coder가 피드백을 반영하여 재구현
- 재구현된 코드로 User Approval 2 다시 진행
- 반복 가능 (무제한)

### System Prompt
→ 별도 파일: `prompts/user_approval_2.md`

---

## 6. 실제 파일 적용 (자동 단계)

User Approval 2 승인 후 자동으로 진행:

1. 원본 파일 백업 (`.backup.cs`)
2. 리팩터링된 코드를 파일에 기록
3. 최종 보고서 생성

```
✅ 리팩터링 완료
파일: {filepath}
변경 사항: {X개 항목 적용}
백업: {filepath}.backup.cs
최종 보고서: {filepath}_refactor_report.md
```

---

## 절대 금지 규칙

모든 에이전트 System Prompt에 반드시 포함:

```
절대 금지 (예외 없음):
- 코드 직접 작성 또는 코드 예시 제시 (Planner, Reviewer, UA1, UA2)
- git commit, git push, git merge, git pull
- 자신의 담당 영역 밖의 작업
- 자신의 판정/분석 수정

파이프라인 역할 분리:
- Planner: 분석만 (구현 X, 평가 X)
- Reviewer: 평가만 (분석 X, 구현 X)
- Coder: 구현만 (분석 X, 평가 X)
- UA1/UA2: 사용자 승인만 (분석 X, 구현 X)
```

---

## 4. USER APPROVAL (UA)

User Approval은 에이전트가 아니라 **사용자 상호작용 프로세스**입니다.
Orchestrator가 직접 관리하며, 실행 환경에 따라 입력 모드를 자동으로 감지합니다.

### UA 입력 모드

#### 모드 1: 대화형 (interactive)

**감지 조건:**
- `--auto-approve` 플래그 없음
- `sys.stdin.isatty()` == True (터미널 연결)

**동작:**
```python
choice = input("선택 (승인/거부): ").strip()
if choice not in ["승인", "거부"]:
    choice = "거부"  # 무효 입력 시 기본값
```

**사용 시나리오:**
- 개발 중 수동 리뷰
- 사용자의 즉시 피드백이 필요한 경우
- 예: `python cs_code_reviewer.py --target file.cs`

#### 모드 2: 자동 승인 (auto_approve)

**감지 조건:**
- `--auto-approve` 플래그 명시

**동작:**
```python
choice = "승인"  # 모든 UA에서 자동 승인
print("[자동 모드] User Approval: 승인")
```

**사용 시나리오:**
- 신뢰할 수 있는 코드 배치 처리
- 테스트 자동화
- 반복적인 리팩터링
- 예: `python cs_code_reviewer.py --target file.cs --auto-approve`

#### 모드 3: 비대화형 (non_interactive) — 안전 모드

**감지 조건:**
- `--auto-approve` 플래그 없음
- `sys.stdin.isatty()` == False (stdin 없음)
- 파이프, 리다이렉트, CI/CD 환경

**동작:**
```python
# stdin이 없으므로 input() 호출 불가
# 대신 안전한 기본값 사용

if approval_stage == "UA1":
    print("[경고] stdin 없음 (비대화형 모드) - 기본값: 거부")
    choice = "거부"  # 보수적 기본값
elif approval_stage == "UA2":
    print("[경고] stdin 없음 (비대화형 모드) - 기본값: 거부")
    choice = "거부"  # 보수적 기본값
```

**사용 시나리오:**
- CI/CD 파이프라인 (자동 검증)
- 백그라운드 배치 작업
- 서버 자동화
- 예: `python cs_code_reviewer.py --target file.cs < /dev/null`

### UA 입력 감지 로직

```python
import sys

class UAInputModeManager:
    def __init__(self, auto_approve: bool):
        self.auto_approve = auto_approve
        self.mode = self._detect_mode()
    
    def _detect_mode(self) -> str:
        """실행 환경에 따라 입력 모드 감지"""
        if self.auto_approve:
            return "auto_approve"
        elif sys.stdin.isatty():
            return "interactive"
        else:
            return "non_interactive"
    
    def get_approval(self, stage: str) -> str:
        """
        사용자 승인 획득
        
        Args:
            stage: "UA1" 또는 "UA2"
        
        Returns:
            "승인" 또는 "거부"
        """
        if self.mode == "auto_approve":
            return "승인"
        elif self.mode == "interactive":
            return self._interactive_input(stage)
        else:  # non_interactive
            return self._non_interactive_default(stage)
    
    def _interactive_input(self, stage: str) -> str:
        """대화형 입력"""
        try:
            choice = input(f"[{stage}] 선택 (승인/거부): ").strip()
            return "승인" if choice == "승인" else "거부"
        except EOFError:
            # stdin 갑자기 끊김
            print(f"[경고] stdin 끊김 - 기본값 사용")
            return "거부"
    
    def _non_interactive_default(self, stage: str) -> str:
        """비대화형 기본값 (안전)"""
        print(f"[경고] stdin 없음 (비대화형 모드) - 기본값: 거부")
        return "거부"
```

### UA 출력 형식

#### UA1 (변경 예정사항 확인)

```
================================================================================
변경 예정 사항 (User Approval 1)
================================================================================

파일: Assets/Scripts/Systems/MoveSystem.cs

Planner 계획:
## 코드 품질 분석
...

Reviewer 평가:
## 평가 결과
평균 점수: X/10

================================================================================
[{mode}] 승인/거부를 입력하세요.
```

#### UA2 (변경된 코드 최종 확인)

```
================================================================================
변경된 코드 확인 (User Approval 2)
================================================================================

파일: Assets/Scripts/Systems/MoveSystem.cs

변경 전:
```csharp
[원본 코드]
```

변경 후:
```csharp
[리팩터링된 코드]
```

Coder 변경 사항 요약:
...

================================================================================
[{mode}] 승인/거부/재작업을 입력하세요.

거부 선택 시:
폐기 - 변경사항 버림, 파이프라인 중단
재작업 - 문제점 + 개선 방향 입력 후 Coder 재구현
```

---

## 다음 단계

System Prompt를 별도 파일로 생성:
- `prompts/planner_system.md`
- `prompts/reviewer_system.md`
- `prompts/coder_system.md`
- `prompts/user_approval_1.md`
- `prompts/user_approval_2.md`
