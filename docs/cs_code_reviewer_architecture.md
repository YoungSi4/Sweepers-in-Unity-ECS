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
    ↓ (≥8점)
[3. User Approval 1] 변경 예정사항 사용자 확인 & 승인 ← ⭐ 사용자 개입
    ↓ (✅ 승인)
[4. Coder] Planner 계획 & Reviewer 피드백 기반 코드 구현
    ↓
[5. User Approval 2] 변경된 코드 사용자 확인 & 최종 승인 ← ⭐ 사용자 개입
    │
    ├─→ (✅ 승인) → [6. 파일 적용] (백업 + 기록)
    ├─→ (❌ 폐기) → 변경사항 버림 [종료]
    └─→ (⚠️ 재작업) → 피드백 입력 → [4. Coder] 재구현 → [5. User Approval 2] (반복)
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

### ✅ 재작업 피드백 루프
User Approval 2에서 거부 시:
- **폐기**: 변경사항 버림
- **재작업**: 문제점 + 개선 방향 입력 → Coder 재구현 → User Approval 2 (반복)

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
| 5. UA2 | 최종 확인 | 변경 전/후 코드 | 승인/거부/재작업 | 파일적용 (✅) / 폐기 (❌) / Coder 재구현 (⚠️) |
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

## 데이터 흐름

```
원본 코드
  ↓
Planner: 8가지 기준 분석
  ├─ 문제점 목록
  ├─ 리팩터링 항목 (P1/P2/P3)
  └─ 구현 지시사항 (코드 예시 X)
  ↓
Reviewer: 항목별 평가
  ├─ 완성도 점수
  ├─ 실현 가능성 점수
  └─ 평균 점수 (통과/재작업)
  ↓
User Approval 1: 변경 예정사항 확인
  ├─ 변경 항목 요약
  ├─ 영향도 분석
  └─ 사용자 승인 여부
  ↓
Coder: 코드 구현
  ├─ 리팩터링된 완전한 코드
  ├─ 변경 전/후 비교
  └─ 변경 통계 (라인 수)
  ↓
User Approval 2: 최종 확인
  ├─ 변경 코드 상세 제시
  ├─ 구현 완성도 평가
  └─ 사용자 최종 판정 (승인/거부/재작업)
  ↓ (✅ 승인)
파일 적용: 자동 기록
  ├─ 원본 백업 (.backup.cs)
  ├─ 파일에 새 코드 기록
  └─ 최종 보고서 생성
```

---

## 사용 방법

```bash
# 특정 파일 리뷰
python cs_code_reviewer.py --target Assets/Scripts/Systems/MoveSystem.cs

# 변경된 모든 C# 파일 리뷰
python cs_code_reviewer.py --all

# 출력
claude_tools/review_outputs/{timestamp}_{filename}_review.md
```

---

## 문서 구조

- **cs_code_reviewer_architecture.md** (본 문서) - 전체 개요
- **cs_code_reviewer_agents.md** - 각 에이전트 상세 정의
- **prompts/planner_system.md** - Planner System Prompt
- **prompts/reviewer_system.md** - Reviewer System Prompt
- **prompts/coder_system.md** - Coder System Prompt
- **prompts/user_approval_1.md** - User Approval 1 프롬프트
- **prompts/user_approval_2.md** - User Approval 2 프롬프트
