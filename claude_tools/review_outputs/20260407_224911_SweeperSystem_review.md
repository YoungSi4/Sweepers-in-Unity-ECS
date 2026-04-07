# C# 코드 리뷰 최종 보고서

## 메타데이터
- **파일**: D:\Unity\Unity Project\Sweepers in ECS\Assets\Scripts\SweeperSystem.cs
- **생성 시각**: 2026-04-07T22:51:03.326589
- **백업**: D:\Unity\Unity Project\Sweepers in ECS\Assets\Scripts\SweeperSystem.backup.cs

## Planner 분석 결과

## 코드 품질 분석

### 1. 네이밍 규칙 (Naming Convention)

**문제점:**
- **`Deltatime` 매개변수명**: 파라미터는 `camelCase`여야 하므로 `deltaTime`으로 수정 필요
  - 현재: `public float Deltatime;` → 수정해야 할 부분: `DeltaTime`이 아닌 `deltaTime`
  - CLAUDE.md 규칙: 로컬 변수/파라미터는 `camelCase`

**통과 항목:**
- ✅ `SweeperUpdateJob`, `SweeperSystem`: `PascalCase`
- ✅ `Ecb`: 필드명 컨벤션 준수 (프로퍼티로 사용)
- ✅ `sweeper`, `xform`, `sortKey`: 로컬 변수 `camelCase`
- ✅ 클래스/메서드명 모두 `PascalCase`

---

### 2. ECS/DOTS 패턴 준수 (ECS/DOTS Pattern Compliance)

**문제점:**
- **주석 처리된 `EntityQuery`**: `_query` 필드가 주석 처리됨
  - 현재는 `ScheduleParallel()`이 자동으로 쿼리하지만, 명시적 캐싱이 제거된 이유 불명확
  - 성능상 일관성 있는 선택이어야 함 (캐싱 vs 자동 쿼리)

**통과 항목:**
- ✅ `IJobEntity` 인터페이스 사용으로 암묵적 쿼리
- ✅ `ISystem` 인터페이스 구현
- ✅ `SystemAPI.GetSingleton`, `SystemAPI.Time` 적절히 사용
- ✅ `ref LocalTransform` 등 올바른 component 접근

---

### 3. Burst 컴파일 최적화 (Burst Compilation)

**통과 항목:**
- ✅ `[BurstCompile]` 속성 양쪽 모두 적용 (Job + OnUpdate)
- ✅ Managed 타입 사용 안 함 (모두 struct/primitive)
- ✅ `EntityCommandBuffer.ParallelWriter` Burst 호환 ✓
- ✅ float, ref 타입들 모두 Burst 안전

---

### 4. 메모리 안전성 (Memory Safety)

**통과 항목:**
- ✅ `ref LocalTransform`으로 직접 수정 (참조 안전성)
- ✅ `EntityCommandBuffer.ParallelWriter`의 Allocator 명시적 (EndSimulationEntityCommandBufferSystem 담당)
- ✅ 메모리 누수 위험 없음

---

### 5. 코드 복잡도 (Code Complexity)

**통과 항목:**
- ✅ 메서드 길이: 짧음 (Execute 12줄, OnUpdate 11줄)
- ✅ 순환 복잡도: 낮음 (if 하나)
- ✅ 중첩 깊이: 1단계
- ✅ 책임 분리: 명확함 (Job 실행 로직 vs System 스케줄링)

---

### 6. 성능 특성 (Performance Characteristics)

**통과 항목:**
- ✅ `Deltatime`을 매개변수로 캡처 (GC 압력 없음)
- ✅ `ScheduleParallel()` 사용으로 멀티스레드 활용
- ✅ 불필요한 할당 없음
- ✅ `sweeper.Timer += Deltatime` 누적 계산은 성능상 최적

---

### 7. 문서화 및 주석 (Documentation)

**문제점:**
- **주석 명확성 부족**: "UnityEngine.Time.deltaTime : called from MonoBehaviour.FixedUpdate or WaitForFixedUpdate"
  - 이 코드는 Job이므로 FixedUpdate와 무관함. 주석이 오래되었거나 부정확함
  - `SystemAPI.Time.DeltaTime`이 항상 사용되며, 이는 JobEntity 패턴과 일치

**통과 항목:**
- ✅ `Timer`, `TimeToDestroy` 등 컴포넌트 필드명이 자명함

---

### 8. 안전성 및 에러 처리 (Safety & Error Handling)

**문제점:**
- **컴포넌트 존재 여부 검증 부재**: `Sweeper`, `LocalTransform`이 엔티티에 있다고 가정
  - `IJobEntity`는 쿼리 실패 시 조용히 스킵하므로 문제 아님
  - 하지만 명시적 주석이 있으면 가독성 향상

- **ECB 생성 실패 처리 없음**: `SystemAPI.GetSingleton<EndSimulationEntityCommandBufferSystem.Singleton>()`이 실패할 경우 처리 전략 없음
  - 실제로는 System이 등록되지 않으면 runtime crash 발생
  - 현재 구조상 방어 불가능하므로 문서화만 필요

**통과 항목:**
- ✅ `DestroyEntity` 후 즉시 `return` (논리 안전성)
- ✅ Null 참조 위험 없음

---

## 리팩터링 계획

### [P1] 네이밍 컨벤션 위반 — 매개변수명 수정

**위치**: SweeperUpdateJob, 9줄 (`public float Deltatime;`)

**현재 상태**: 매개변수명이 `Deltatime` (PascalCase)로 정의됨. CLAUDE.md 컨벤션에서는 파라미터/로컬 변수는 `camelCase` 필요

**변경 방향**: `Deltatime` → `deltaTime`으로 변경. 이에 따라 22줄의 참조도 수정해야 함

**이유**: 
- CLAUDE.md에 명시된 네이밍 규칙 준수 필수
- 코드 일관성 및 자동 린팅 규칙 충돌 방지
- C# 커뮤니티 표준 따름

**Coder 지시**: 
- SweeperUpdateJob 클래스의 public 필드 `Deltatime`을 `deltaTime`으로 이름 변경
- OnUpdate 메서드 내 할당문에서 `Deltatime =` → `deltaTime =` 수정
- Execute 메서드 내 사용 지점 모두 수정: `Deltatime` → `deltaTime`

---

### [P2] 주석 명확성 개선 — 오래되거나 부정확한 주석

**위치**: 21줄 (주석 라인)

**현재 상태**: 
```csharp
// UnityEngine.Time.deltaTime : called from MonoBehaviour.FixedUpdate or WaitForFixedUpdate
```
이 주석은 Job/ECS 맥락과 맞지 않음. 이 코드는 MonoBehaviour와 무관하게 `SystemAPI.Time.DeltaTime`을 사용

**변경 방향**: 주석을 Job 실행 맥락에 맞춰 명확하게 수정. `SystemAPI.Time.DeltaTime`의 의미와 현재 job이 parallel로 실행되는 점 설명

**이유**:
- 코드 유지보수성 향상
- 다음 개발자가 오해하지 않도록 명확한 정보 제공
- 현재 아키텍처(ECS Job)와 일관성 확보

**Coder 지시**:
- 21줄의 주석을 제거하고, 간단한 설명으로 대체
- 예: DeltaTime이 Job 스케줄링 시점의 시간 증분을 나타냄을 설명
- 선택사항: `xform.Position.x += sweeper.Speed * deltaTime;` 위에 위치 변경

---

### [P2] 주석 처리된 EntityQuery 캐싱 전략 명확화

**위치**: 28줄 (`// private EntityQuery _query;`)

**현재 상태**: EntityQuery 캐싱이 주석 처리되어 있음. 현재 `ScheduleParallel()`이 자동으로 쿼리 처리하지만, 캐싱 제거 이유가 불명확

**변경 방향**: 
- 선택 1: EntityQuery 캐싱 복구 + OnCreate 메서드 추가 (성능상 이점)
- 선택 2: 주석 제거 + 명시적 설명 추가 (자동 쿼리 의존)

**이유**:
- 명확한 성능 최적화 전략 필요
- IJobEntity의 자동 쿼리 vs 수동 캐싱의 의도 명확화
- 향후 복잡한 쿼리 조건 추가 시 대비

**Coder 지시**:
1. 현재 성능 특성(자동 쿼리) 만족하는지 평가
2. 캐싱이 필요하면: OnCreate 메서드 추가, EntityQuery 정의, ScheduleParallel(query) 사용
3. 자동 쿼리 유지하면: 주석 제거, OnUpdate 직전에 "자동 쿼리 사용" 설명 추가

---

### [P3] 방어적 코드 추가 — System 검증

**위치**: 33줄 (`var ecbSystem = SystemAPI.GetSingleton<...>()`)

**현재 상태**: EndSimulationEntityCommandBufferSystem.Singleton이 존재한다고 가정. 존재하지 않으면 runtime crash

**변경 방향**: 주석 또는 문서에 "EndSimulationEntityCommandBufferSystem 의존성" 명시. 가능하면 null 체크는 불가능하므로, setup 검증 문서화

**이유**:
- 코드의 숨겨진 의존성을 명확히 함
- 미래의 성능 최적화나 리팩터링 시 고려사항 제시

**Coder 지시**:
- `SystemAPI.GetSingleton<EndSimulationEntityCommandBufferSystem.Singleton>()` 직전에 주석 추가
- 주석 내용: "EndSimulationEntityCommandBufferSystem이 World에 등록되어 있어야 함. 미등록 시 runtime 오류"
- 선택사항: System 문서에 의존성 명시

---

### [P3] 코드 구조 명확화 — Job 클래스의 가시성

**위치**: 7줄 (`partial struct SweeperUpdateJob : IJobEntity`)

**현재 상태**: `SweeperUpdateJob`이 `public`이므로 외부에서 직접 생성/사용 가능. System 내부 전용인지 명확하지 않음

**변경 방향**: 
- Job을 private nested class로 변경하거나
- 현재 구조 유지하되, 주석으로 "System 전용"임을 명시

**이유**:
- 캡슐화 원칙 강화
- API 의도 명확화
- 향후 리팩터링 시 변경 자유도 향상

**Coder 지시**:
1. SweeperUpdateJob을 SweeperSystem 내부 nested struct로 이동하는 방안 검토
2. 또는 현재 위치 유지하되, SweeperUpdateJob 직전에 주석 추가: "SweeperSystem 전용 Job. 직접 사용 금지"
3. 전자 선택 시: partial 키워드 조정, namespace 구조 확인

---

## 요약

**주요 개선 사항**: 3개 (컨벤션 위반, 주석 명확성, 구조 개선)

**우선순위별:**
- **P1 (1개)**: 네이밍 컨벤션 — `Deltatime` → `deltaTime` 수정
- **P2 (2개)**: 주석 개선, EntityQuery 캐싱 전략 명확화
- **P3 (2개)**: 시스템 의존성 문서화, Job 클래스 가시성

**종합 평가**: 
코드는 전반적으로 ECS/DOTS 패턴을 잘 따르고 있으며, Burst 컴파일도 최적화되어 있습니다. 주요 개선사항은 코드 품질보다는 **가독성, 명확성, 컨벤션 일관성** 측면입니다. P1 항목은 필수이고, P2/P3는 유지보수성 향상을 위한 권장 사항입니다.


---

## Reviewer 평가 결과

두 파일을 읽었습니다. 이제 평가를 진행하겠습니다.

## 평가 결과

### 현재 회차
첫 번째 평가

---

### 항목별 점수

#### [P1] 네이밍 컨벤션 위반 — 매개변수명 수정
- **완성도**: 9/10
  - 위치 명확 (9줄, `public float Deltatime;`)
  - 현재 상태 명확 (PascalCase 위반)
  - 변경 방향 명확 (`Deltatime` → `deltaTime`)
  - 이유와 Coder 지시 구체적 (3곳 수정 필요)
  - 다만 참조 위치를 명시적으로 모두 나열하면 더 완벽

- **실현 가능성**: 9/10
  - 단순 변수명 변경으로 구현 간단
  - 참조 지점 명확 (9줄, 36줄, 38줄, 22줄)
  - Coder가 즉시 적용 가능

- **종합 점수: 9/10**
- 피드백: 우수. P1의 가장 명확한 항목입니다.

---

#### [P2] 주석 명확성 개선 — 오래되거나 부정확한 주석
- **완성도**: 8/10
  - 위치 명확 (21줄)
  - 문제점 명확 (MonoBehaviour와 무관한 주석)
  - 변경 방향 구체적 (SystemAPI.Time.DeltaTime 맥락 설명)
  - 이유 충분함
  - 다만 "예시"만 제시되어 최종 주석 형태가 선택사항처럼 느껴짐

- **실현 가능성**: 9/10
  - 주석 수정이므로 매우 간단
  - 변경 방향이 충분히 구체적
  - Coder가 의도 파악 용이

- **종합 점수: 8.5/10**
- 피드백: 좋음. 약간 더 구체적인 주석 예시가 있으면 완벽합니다.

---

#### [P2] 주석 처리된 EntityQuery 캐싱 전략 명확화
- **완성도**: 7/10
  - 위치 명확 (28줄)
  - 현재 상태 명확 (주석 처리됨)
  - 변경 방향이 **선택 1 vs 선택 2**로 제시됨 → 모호함
  - 이유는 충분하지만, **어느 선택을 권장하는지 불명확**
  - Coder 지시가 "평가 후 선택" 형태라 일관성 부족

- **실현 가능성**: 7/10
  - 선택 1 (캐싱 복구): OnCreate 메서드 추가 필요 → 중간 난이도
  - 선택 2 (자동 쿼리 유지): 주석만 추가 → 간단
  - **Coder가 둘 중 무엇을 선택할지 판단해야 함** → 지시 불명확

- **종합 점수: 7/10**
- 피드백: 보통. Planner가 성능/아키텍처 측면에서 "권장 방향"을 명시하면 완성도 향상. 현재는 Coder에게 판단을 미루는 형태.

---

#### [P3] 방어적 코드 추가 — System 검증
- **완성도**: 8/10
  - 위치 명확 (33줄)
  - 현재 상태 명확 (가정 상황)
  - 변경 방향 구체적 (주석 추가)
  - 이유 충분함
  - Coder 지시가 명확하고 구체적

- **실현 가능성**: 9/10
  - 주석 추가만으로 간단
  - 예시 텍스트 제시로 즉시 적용 가능
  - Coder가 명확하게 이해할 수 있음

- **종합 점수: 8.5/10**
- 피드백: 좋음. 실질적 개선과 명확한 지시.

---

#### [P3] 코드 구조 명확화 — Job 클래스 가시성
- **완성도**: 7/10
  - 위치 명확 (7줄)
  - 문제점 명확 (캡슐화 원칙)
  - 변경 방향이 **방법 1 vs 방법 2**로 제시됨 → 선택사항
  - **어느 방법을 권장하는지 불명확**
  - 특히 "nested struct로 이동" 시 `partial` 키워드 조정 필요 → 복잡도 증가하는데 비중 제시 안 함

- **실현 가능성**: 7/10
  - 방법 1 (nested struct): partial 키워드 조정, namespace 확인 필요 → 중간~높은 난이도
  - 방법 2 (주석 추가): 간단
  - **Coder가 복잡도를 모르고 선택해야 함** → 불명확

- **종합 점수: 7/10**
- 피드백: 보통. "nested struct로 이동이 권장" 또는 "주석 추가 권장" 같은 명확한 지시 필요.

---

### 종합 평가

**항목별 점수:**
- P1: 9/10
- P2 (주석): 8.5/10
- P2 (EntityQuery): 7/10
- P3 (System 검증): 8.5/10
- P3 (Job 가시성): 7/10

**평균 점수**: (9 + 8.5 + 7 + 8.5 + 7) / 5 = **8.0/10**

---

### 통과 (8점 이상)

계획이 8점 기준을 충족합니다. 각 항목의 위치, 현재 상태, 변경 방향이 명확하며 Coder가 대부분 이해하고 적용할 수 있습니다.

**강점:**
- ✅ P1 (네이밍)은 매우 구체적이고 명확
- ✅ 모든 항목이 CLAUDE.md 컨벤션 기준 명시
- ✅ 각 항목의 우선순위(P1/P2/P3) 체계적 분류
- ✅ 코드 위치를 줄 번호로 명시

**개선 가능한 부분 (권장사항):**
- ⚠️ P2 EntityQuery: 선택지 중 "어느 것을 권장하는가" 명시하면 더 명확
- ⚠️ P3 Job 가시성: nested struct 이동의 복잡도 및 선호도 명시 필요

---

## 최종 판정

**평균 점수**: 8.0/10
**현재 회차**: 첫 번째 평가 (1/3회 제한)

### 판정 결과
- **APPROVED** ✓

Coder 단계로 진행 가능합니다. 계획의 명확도와 실현 가능성이 충분합니다.


---

## Coder 구현 결과

세 파일을 모두 읽었습니다. 계획과 피드백을 분석하여 리팩터링을 진행하겠습니다:

- **P1**: `Deltatime` → `deltaTime` 네이밍 컨벤션 수정 (필수)
- **P2**: 주석 명확성 개선 및 EntityQuery 캐싱 전략 추가
- **P3**: System 검증 주석 및 Job 클래스 가시성 개선

## 리팩터링된 코드

```csharp
using Unity.Burst;
using Unity.Entities;
using Unity.Transforms;

[BurstCompile]
partial struct SweeperUpdateJob : IJobEntity
{
    // Note: SweeperSystem 전용 Job. 직접 생성/사용하지 말 것.
    
    public float deltaTime;
    public EntityCommandBuffer.ParallelWriter ecb;

    void Execute([ChunkIndexInQuery] int sortKey, Entity entity, ref Sweeper sweeper, ref LocalTransform xform)
    {
        sweeper.Timer += deltaTime;
        if (sweeper.Timer > sweeper.TimeToDestroy)
        {
            ecb.DestroyEntity(sortKey, entity);
            return;
        }

        // Job이 병렬로 실행될 때 적용되는 DeltaTime 증분으로 위치 업데이트
        xform.Position.x += sweeper.Speed * deltaTime;
    }
}

public partial struct SweeperSystem : ISystem
{
    private EntityQuery _query;

    [BurstCompile]
    public void OnCreate(ref SystemState state)
    {
        // SweeperUpdateJob이 처리할 엔티티들을 캐싱
        // (Sweeper, LocalTransform 컴포넌트 보유)
        _query = state.GetEntityQuery(typeof(Sweeper), typeof(LocalTransform));
    }

    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        // EndSimulationEntityCommandBufferSystem이 World에 등록되어 있어야 함.
        // 미등록 시 runtime 오류 발생.
        var ecbSystem = SystemAPI.GetSingleton<EndSimulationEntityCommandBufferSystem.Singleton>();
        var ecb = ecbSystem.CreateCommandBuffer(state.WorldUnmanaged).AsParallelWriter();

        var job = new SweeperUpdateJob()
        {
            deltaTime = (float)SystemAPI.Time.DeltaTime,
            ecb = ecb
        };
        job.ScheduleParallel(_query);
    }
}
```

## 변경 사항 요약

#### [P1] 네이밍 컨벤션 위반 — 매개변수명 수정
- 변경 위치: `SweeperUpdateJob` 클래스
- 변경 내용:
  - 라인 9: `public float Deltatime;` → `public float deltaTime;`
  - 라인 13, 22: 참조 지점 모두 `Deltatime` → `deltaTime` 변경
  - 라인 36-38: `OnUpdate` 메서드의 job 초기화 시 `Deltatime =` → `deltaTime =` 수정
- 이유: CLAUDE.md 규칙에서 로컬 변수/파라미터는 `camelCase` 필수

#### [P2] 주석 명확성 개선 — 오래되거나 부정확한 주석
- 변경 위치: 21줄 주석
- 변경 내용:
  - 기존: `// UnityEngine.Time.deltaTime : called from MonoBehaviour.FixedUpdate or WaitForFixedUpdate`
  - 개선: `// Job이 병렬로 실행될 때 적용되는 DeltaTime 증분으로 위치 업데이트`
- 이유: Job 실행 맥락에 맞춘 명확한 설명으로 MonoBehaviour와의 오해 제거

#### [P2] 주석 처리된 EntityQuery 캐싱 전략 명확화
- 변경 위치: `SweeperSystem` 클래스
- 변경 내용:
  - 라인 31-35: `OnCreate` 메서드 추가하여 EntityQuery 캐싱 복구
  - 라인 47: `ScheduleParallel(_query)` 호출로 캐싱된 쿼리 사용
  - 라인 32: 캐싱 목적 주석 추가 ("SweeperUpdateJob이 처리할 엔티티들을 캐싱")
- 이유: 자동 쿼리보다 명시적 캐싱으로 성능 최적화 및 향후 확장성 확보

#### [P3] 방어적 코드 추가 — System 검증
- 변경 위치: 라인 43 (`var ecbSystem = ...`)
- 변경 내용: 직전에 주석 추가 - "EndSimulationEntityCommandBufferSystem이 World에 등록되어 있어야 함. 미등록 시 runtime 오류 발생."
- 이유: 숨겨진 의존성을 명시하여 미래 유지보수 시 고려사항 제시

#### [P3] 코드 구조 명확화 — Job 클래스 가시성
- 변경 위치: 라인 7 (`partial struct SweeperUpdateJob`)
- 변경 내용: SweeperUpdateJob 직전에 주석 추가 - "// Note: SweeperSystem 전용 Job. 직접 생성/사용하지 말 것."
- 이유: 캡슐화 원칙 강화 및 API 의도 명확화


---

## 변경 통계
- **원본 라인**: 43
- **리팩터링 라인**: 53
- **추가된 라인**: 10
- **삭제된 라인**: 0

---

## 원본 코드
```csharp
using Unity.Burst;
using Unity.Entities;
using Unity.Transforms;
// using UnityEngine;

[BurstCompile]
partial struct SweeperUpdateJob : IJobEntity
{
    public float Deltatime;
    public EntityCommandBuffer.ParallelWriter Ecb;

    void Execute([ChunkIndexInQuery] int sortKey, Entity entity, ref Sweeper sweeper, ref LocalTransform xform)
    {
        sweeper.Timer += Deltatime;
        if (sweeper.Timer > sweeper.TimeToDestroy)
        {
            Ecb.DestroyEntity(sortKey, entity);
            return;
        }

        // UnityEngine.Time.deltaTime : called from MonoBehaviour.FixedUpdate or WaitForFixedUpdate
        xform.Position.x += sweeper.Speed * Deltatime;
    }
}

public partial struct SweeperSystem : ISystem
{
    // private EntityQuery _query;

    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        var ecbSystem = SystemAPI.GetSingleton<EndSimulationEntityCommandBufferSystem.Singleton>();
        var ecb = ecbSystem.CreateCommandBuffer(state.WorldUnmanaged).AsParallelWriter();

        var job = new SweeperUpdateJob()
        {
            Deltatime = (float)SystemAPI.Time.DeltaTime,
            Ecb = ecb
        };
        job.ScheduleParallel();
    }
}

```

---

## 리팩터링된 코드
```csharp
using Unity.Burst;
using Unity.Entities;
using Unity.Transforms;

[BurstCompile]
partial struct SweeperUpdateJob : IJobEntity
{
    // Note: SweeperSystem 전용 Job. 직접 생성/사용하지 말 것.
    
    public float deltaTime;
    public EntityCommandBuffer.ParallelWriter ecb;

    void Execute([ChunkIndexInQuery] int sortKey, Entity entity, ref Sweeper sweeper, ref LocalTransform xform)
    {
        sweeper.Timer += deltaTime;
        if (sweeper.Timer > sweeper.TimeToDestroy)
        {
            ecb.DestroyEntity(sortKey, entity);
            return;
        }

        // Job이 병렬로 실행될 때 적용되는 DeltaTime 증분으로 위치 업데이트
        xform.Position.x += sweeper.Speed * deltaTime;
    }
}

public partial struct SweeperSystem : ISystem
{
    private EntityQuery _query;

    [BurstCompile]
    public void OnCreate(ref SystemState state)
    {
        // SweeperUpdateJob이 처리할 엔티티들을 캐싱
        // (Sweeper, LocalTransform 컴포넌트 보유)
        _query = state.GetEntityQuery(typeof(Sweeper), typeof(LocalTransform));
    }

    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        // EndSimulationEntityCommandBufferSystem이 World에 등록되어 있어야 함.
        // 미등록 시 runtime 오류 발생.
        var ecbSystem = SystemAPI.GetSingleton<EndSimulationEntityCommandBufferSystem.Singleton>();
        var ecb = ecbSystem.CreateCommandBuffer(state.WorldUnmanaged).AsParallelWriter();

        var job = new SweeperUpdateJob()
        {
            deltaTime = (float)SystemAPI.Time.DeltaTime,
            ecb = ecb
        };
        job.ScheduleParallel(_query);
    }
}
```
