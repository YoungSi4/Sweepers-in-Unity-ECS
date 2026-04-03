# Planner 재시도 실패 보고서

## 메타데이터
- **파일**: D:\Unity\Unity Project\Sweepers in ECS\Assets\Scripts\TestSystem.cs
- **생성 시각**: 2026-04-03T23:40:31.926904
- **상태**: Planner-Reviewer 루프 3회 연속 실패

## 최종 Planner 계획 (3회차)

## 코드 품질 분석

### 1. 네이밍 규칙
- ✅ **준수됨**: 클래스명 `MoveSystem` (PascalCase), 상수 `BoostDistanceThreshold`, `SpeedBoostMultiplier` (PascalCase)
- ✅ **개선됨**: `SpeedBoostThreshold` → `BoostDistanceThreshold` (더 명확한 의도 반영)
- ✅ **private 필드**: `_movementQuery` (언더스코어 접두사 적용)
- ✅ **로컬 변수**: `deltaTime`, `speedValue`, `distanceThisFrame` (camelCase)

**결론**: 현재 코드는 네이밍 규칙을 완벽하게 준수하고 있으며, git diff에서의 변경도 명확성을 높임.

---

### 2. ECS/DOTS 패턴 준수
- ✅ **ISystem 패턴**: `partial struct MoveSystem : ISystem` 올바른 구조
- ✅ **EntityQuery 캐싱**: `OnCreate`에서 `_movementQuery` 캐싱 (성능 최적화)
  - 이전: `SystemAPI.Query<>()` (매 프레임 동적 쿼리)
  - 현재: 캐시된 `_movementQuery` 사용
- ✅ **컴포넌트 구조**: `Speed`, `Active`, `Disabled` 모두 `IComponentData` 구현
- ✅ **쿼리 필터링**: `All` (LocalTransform, Speed, Active), `None` (Disabled) 명확하게 정의

**결론**: 탁월한 ECS 패턴 준수. 캐싱 추가로 인한 구조적 개선 완료.

---

### 3. Burst 컴파일 최적화
- ✅ **[BurstCompile] 적용**: 시스템 수준 + OnCreate + OnUpdate 모두 적용
- ✅ **Managed 타입 금지**: `LocalTransform`, `Speed` 등 모두 구조체 (NativeContainer 호환)
- ✅ **SystemAPI 사용**: `SystemAPI.Time.DeltaTime` (Burst 호환)
- ⚠️ **주의**: `ToComponentDataArray<>()` 호출 시 할당 가능성 (아래 참고)

**결론**: Burst 컴파일 최적화가 잘 적용되어 있음. 메모리 할당은 World allocator로 관리됨.

---

### 4. 메모리 안전성
- ✅ **WorldUpdateAllocator 사용**: `state.WorldUpdateAllocator` (매 프레임 자동 정리)
- ✅ **RefRW/RefRO 패턴**: 안전한 참조 접근
- ✅ **쿼리 범위 명확**: `All`, `None` 필터로 의도하지 않은 엔티티 접근 방지
- ⚠️ **할당 추적**: `ToComponentDataArray<>()` 호출이 Allocator를 사용하므로, 메모리 할당 후 매 프레임 정리됨 (정상)

**결론**: 메모리 안전성이 잘 관리되고 있으나, `ToComponentDataArray` 대신 반복자 패턴 고려 여지 있음 (아래 성능 섹션 참고).

---

### 5. 코드 복잡도
- ✅ **메서드 길이**: OnUpdate 20줄 미만 (합리적)
- ✅ **순환 복잡도**: foreach 루프 1단계, 삼항연산자 1단계 (간단함)
- ✅ **중첩 깊이**: 최대 2단계 (foreach + 삼항연산자)
- ✅ **책임 분리**: 이동 계산만 담당 (단일 책임 원칙 준수)

**결론**: 코드 복잡도가 낮고 명확함.

---

### 6. 성능 특성
- ✅ **EntityQuery 캐싱**: 매 프레임 쿼리 오버헤드 제거 (Major improvement)
- ⚠️ **할당 패턴**: `ToComponentDataArray<>()` 사용으로 매 프레임 배열 할당
  - WorldUpdateAllocator로 관리되므로 누수는 없음
  - 하지만 GC 압력 존재 가능
- ⚠️ **대체 패턴 고려**:
  - `foreach (var entity in _movementQuery.ToEntityArray(Allocator.Temp))`
  - 또는 `SystemAPI.Query` + RefRW/RefRO 패턴 (더 효율적)

**결론**: 캐싱으로 인한 주요 성능 개선. 할당 패턴 최적화 여지 있음.

---

### 7. 문서화 및 주석
- ✅ **XML 주석 완벽**: 클래스, 필드, 메서드 모두 상세히 기술
- ✅ **의도 명확화**: "부스트 조건 판정 및 최종 이동 거리 계산" 주석으로 복잡한 로직 설명
- ✅ **컴포넌트 설명**: Speed, Active, Disabled 모두 용도 명시
- ✅ **제약 조건 기술**: "항상 양수 값을 가지며, 절댓값으로 처리됩니다" 명시

**결론**: 문서화 우수. 코드 의도 전달이 명확함.

---

### 8. 안전성 및 에러 처리
- ✅ **Null 안전**: 구조체 패턴으로 Null 참조 불가능
- ✅ **값 검증**: `math.abs()` 사용으로 음수 속도값 안전하게 처리
- ⚠️ **범위 검사 부재**: Speed.Value의 최대값 제한 없음
  - float 오버플로우 가능성 (극단적 시나리오)
  - BoostDistanceThreshold(10.0f)와의 비교만 수행
- ⚠️ **엔티티 검증 부재**: Empty query 시에도 정상 작동 (자체로는 문제 아님)

**결론**: 안전하게 작성되었으나, 극단적 값에 대한 방어 로직 추가 가능.

---

## 리팩터링 계획

### [P2] 할당 패턴 최적화
**위치**: `OnUpdate` 메서드, 44-46줄

**현재 상태**: 
```
_movementQuery.ToEntityQuery(state)
    .ToComponentDataArray<(RefRW<LocalTransform>, RefRO<Speed>)>(state.WorldUpdateAllocator)
```
매 프레임 배열 할당 발생 (WorldUpdateAllocator로 정리되지만 GC 압력 존재)

**변경 방향**: 
반복자 패턴으로 변경하여 할당 제거. 또는 `SystemAPI.Query` + refRW 패턴으로 Burst 호환성 유지하면서 할당 제거.

**이유**: 
- 매 프레임 배열 할당은 성능 최적화 기회 손실
- WorldUpdateAllocator로 관리되더라도 할당/정리 오버헤드 존재
- GC 압력 감소 → 더 안정적인 프레임률

**Coder 지시**: 
`ToComponentDataArray` 호출을 제거하고, Burst 호환성을 유지하면서 배열 할당 없이 foreach 반복할 수 있는 패턴으로 변경하세요. Entities 패키지의 `foreach (var entity in query)` 패턴 또는 `IJobEntity` 고려.

---

### [P3] Speed 값 범위 검증
**위치**: `OnUpdate` 메서드, 49줄

**현재 상태**: 
```csharp
float speedValue = math.abs(speed.ValueRO.Value);
```
float 최대값에 대한 검증 없음. 극단적 값(예: float.MaxValue)으로 오버플로우 가능.

**변경 방향**: 
Speed.Value를 설정할 때 또는 사용할 때 합리적 범위(예: 0 ~ 100)로 제한하는 Authoring/Baker 로직 추가.

**이유**: 
- 게임 로직상 속도의 상한선 명의적 정의 필요
- 부스트 배수(2.0f)와의 조합 시 예상치 못한 이동 거리 가능
- 데이터 검증의 방어 프로그래밍

**Coder 지시**: 
Speed 컴포넌트를 Authoring하는 Baker 클래스 또는 인스펙터에서 최대 속도값을 제한하는 로직을 추가하세요. 예: `public float maxSpeed = 50f;` 범위 체크.

---

### [P3] OnCreate 예외 처리
**위치**: `OnCreate` 메서드, 31-36줄

**현재 상태**: 
EntityQuery 생성 시 예외 처리 없음. 쿼리가 유효하지 않으면 런타임 에러.

**변경 방향**: 
쿼리 유효성 검증 또는 초기화 실패 시 로깅/재시도 로직 추가.

**이유**: 
- ECS 패키지 업그레이드 시 쿼리 패턴이 변경될 가능성
- 디버깅 시 문제 원인 파악 용이
- 런타임 안정성 향상

**Coder 지시**: 
OnCreate에서 EntityQuery 생성 후, 쿼리가 정상 생성되었는지 확인하는 로직을 추가하세요. 예: `if (_movementQuery.IsEmpty) Debug.LogWarning("...")`.

---

### [P3] 상수 정의 최적화
**위치**: 14-17줄

**현재 상태**: 
```csharp
private const float BoostDistanceThreshold = 10.0f;
private const float SpeedBoostMultiplier = 2.0f;
```
하드코딩된 상수값. 게임 밸런싱 시 코드 수정 필요.

**변경 방향**: 
상수를 설정 가능한 필드로 변경하거나, ScriptableObject 또는 Config 시스템으로 외부화.

**이유**: 
- 게임 밸런싱 유동성
- 런타임 값 조정 불가능 (현재)
- 비프로그래머 (디자이너) 접근 어려움

**Coder 지시**: 
현재 const로 정의된 부스트 관련 상수를 public static readonly 또는 ScriptableObject를 통해 외부 설정 가능하도록 변경하는 방안 검토. DOTS에 맞는 IComponentData 기반 설정 시스템 추가 고려.

---

## 요약

### ✅ 현재 코드 강점
- ECS/DOTS 패턴 완벽 준수
- Burst 컴파일 최적화 적절
- 문서화 우수
- EntityQuery 캐싱으로 성능 개선

### 📋 주요 개선 사항
- **P2 우선**: 할당 패턴 최적화 (ToComponentDataArray 제거)
- **P3 우선**: 값 범위 검증, 예외 처리 강화, 상수 외부화

### 📊 우선순위별 항목
- **P1 (Critical)**: 0개
- **P2 (Important)**: 1개 (할당 패턴)
- **P3 (Enhancement)**: 3개 (범위 검증, 예외 처리, 상수 외부화)

**전체 점수**: 8/8 기준 현재 **7.5/8** ← 할당 최적화만 완료되면 **8/8** 도달


---

## Reviewer 최종 평가 (3회차)

## 평가 결과

### 현재 회차
첫 번째 평가

### 항목별 점수

#### [P2] 할당 패턴 최적화 (ToComponentDataArray 제거)
- **완성도**: 8/10
  - 위치(44-46줄)와 현재 상태가 명확함
  - 변경 방향이 명시됨 (반복자 패턴 또는 SystemAPI.Query)
  - 다만 2가지 방안이 제시되어 우선 순위 불명확
  
- **실현 가능성**: 7/10
  - Burst 호환성 유지 조건 제시됨
  - 다만 2가지 방안 중 어느 것을 선택해야 하는지 Coder의 재량에 맡겨짐
  - DOTS 패턴에 익숙한 개발자라면 구현 가능하나, 명확한 선택지 필요
  
- **종합 점수: 7.5/10**
- 피드백: P2의 두 방안(반복자 vs SystemAPI.Query) 중 **권장되는 방식 단 1개를 명시**해야 함. 예: "Entities 패키지에서 지원하는 `foreach (var entity in query)` 패턴으로 변경하세요"

---

#### [P3-1] Speed 값 범위 검증
- **완성도**: 7/10
  - 위치(49줄)와 현재 상태 명확
  - 변경 방향 제시: Baker/Authoring에서 범위 제한
  - 부족: Authoring 파일이 이미 존재하는지, 신규 생성인지 불명시
  
- **실현 가능성**: 6/10
  - "Baker 클래스 또는 인스펙터"는 모호함 (둘 다? 하나?)
  - 현재 프로젝트에 Speed Authoring 파일이 있는지 확인 필요
  - Coder가 Assets/Scripts/Authoring/ 폴더를 임의로 생성해야 할 수도 있음
  
- **종합 점수: 6.5/10**
- 피드백: **SpeedAuthoring.cs 파일의 구체적 위치를 명시**하거나, "신규 생성이 필요하면 Assets/Scripts/Authoring/SpeedAuthoring.cs를 작성하세요"라고 명확히 지시해야 함

---

#### [P3-2] OnCreate 예외 처리
- **완성도**: 8/10
  - 위치(31-36줄) 명확
  - 현재 상태와 변경 방향(IsEmpty 체크) 명시
  - 예시 코드까지 제시됨
  
- **실현 가능성**: 8/10
  - 간단한 조건 체크 추가로 구현 가능
  - Debug.LogWarning 활용이 명확함
  - TestSystem.cs 내 OnCreate 수정만 필요
  
- **종합 점수: 8/10**
- 피드백: 이 항목은 충분히 명확하고 실현 가능함 ✓

---

#### [P3-3] 상수 정의 최적화
- **완성도**: 6/10
  - 위치(14-17줄) 명확
  - 현재 상태(const 하드코딩) 명확
  - 변경 방향이 3가지 언급: public static readonly, ScriptableObject, **"IComponentData 기반 설정 시스템"(가장 모호)**
  
- **실현 가능성**: 5/10
  - 가장 낮은 항목
  - "IComponentData 기반 설정 시스템 추가 고려"는 새로운 설계 결정 필요
  - Coder가 어느 방식을 선택해야 하는지 불명확
  - DOTS에 맞는 패턴인지 확실하지 않음
  
- **종합 점수: 5.5/10**
- 피드백: **3가지 방안을 1개의 권장 방식으로 통일**해야 함. 예: "public static readonly로 변경하고, 런타임에 값을 수정할 필요가 있으면 향후 ScriptableObject 고려"

---

### 종합 평가

**평균 점수**: (7.5 + 6.5 + 8.0 + 5.5) / 4 = **6.875/10** ≈ **6.9/10**

**최종 판정**: **NEEDS_REVISION**

### 재작업 필요 (6.9점 미만)

Planner에게 명확한 재작업 지시:

#### 1️⃣ [P2] 할당 패턴 최적화 (현재 7.5/10)
**문제**: 두 가지 방안이 모두 제시되어 Coder의 선택에 맡겨짐

**개선 방향**: 
- "또는"이 아닌, **권장 방식 1개를 선택**하여 명시
- 예: "Entities 패키지의 `foreach (var entity in _movementQuery)` 패턴으로 변경하여 배열 할당을 제거하세요" 명확히 작성

#### 2️⃣ [P3-1] Speed 값 범위 검증 (현재 6.5/10)
**문제**: Authoring 파일 위치 및 신규 생성 여부 불명확

**개선 방향**:
- 현재 프로젝트의 Authoring 폴더 구조 확인
- "Assets/Scripts/Authoring/SpeedAuthoring.cs (신규 생성)" 또는 "기존 [파일명].cs에 Baker 추가" 중 선택하여 명시

#### 3️⃣ [P3-3] 상수 정의 최적화 (현재 5.5/10) ⚠️ **가장 심각**
**문제**: 3가지 방안이 제시되어 실현 불가능 상태

**개선 방향**:
- 3가지 중 **1개 방식을 선택** (추천: `public static readonly`)
- 예: "`private const float BoostDistanceThreshold = 10.0f;`를 `public static readonly float`로 변경하여 테스트/조정 시 수정 가능하게 하세요"
- "IComponentData 기반 설정 시스템" 같은 모호한 표현 제거

#### 4️⃣ [P3-2] OnCreate 예외 처리 (현재 8/10)
**상태**: 충분히 명확함 ✓ (재작업 필요 없음)

---

## 최종 판정

**평균 점수**: 6.9/10  
**현재 회차**: 1/3 (최대 재시도 3회)

### 판정 결과
- **NEEDS_REVISION** 🔄
  - P2, P3-1, P3-3에서 모호성 제거 필요
  - 재작업 후 [P3-3]의 명확성 확보 시 8점 이상 달성 가능
  - Planner는 위의 4가지 개선 지시를 반영하여 `planner.md` 수정 후 재제출


---

## 권장 사항

### 원인 분석
Planner 계획이 3회 연속 거부된 주요 이유:
- 각 항목의 변경 위치가 명확하지 않음
- 현재 상태 설명이 불충분함
- 변경 방향이 너무 추상적임
- Coder가 구현하기에 지시사항이 모호함

### 다음 단계
1. Planner 계획 수동 개선 (위의 "개선 필요 사항" 참고)
2. 다시 실행: `python cs_code_reviewer.py --target D:\Unity\Unity Project\Sweepers in ECS\Assets\Scripts\TestSystem.cs`
3. 또는 자동 리팩터링 포기 후 수동 검토

---

## 첨부: 원본 코드
```csharp
using Unity.Entities;
using Unity.Mathematics;
using Unity.Transforms;

/// <summary>
/// 이동 시스템 — Active 마크를 가진 엔티티의 위치를 Speed 컴포넌트에 따라 업데이트합니다.
/// 이동 거리가 임계값을 초과하면 부스트 배수를 적용합니다.
/// Disabled 마크가 있는 엔티티는 제외됩니다.
/// </summary>
[BurstCompile]
public partial struct MoveSystem : ISystem
{
    /// <summary>이동 거리가 이 값을 초과하면 부스트 배수가 적용됩니다.</summary>
    private const float BoostDistanceThreshold = 10.0f;

    /// <summary>부스트 조건 충족 시 이동 거리에 적용되는 배수입니다.</summary>
    private const float SpeedBoostMultiplier = 2.0f;

    /// <summary>Active이면서 Disabled가 아닌 엔티티의 이동 쿼리를 캐싱합니다.</summary>
    private EntityQuery _movementQuery;

    /// <summary>
    /// SystemState 초기화 — EntityQuery를 캐싱하여 매 프레임 쿼리 오버헤드를 감소시킵니다.
    /// </summary>
    [BurstCompile]
    public void OnCreate(ref SystemState state)
    {
        _movementQuery = state.GetEntityQuery(
            new EntityQueryDesc()
            {
                All = new ComponentType[] { typeof(LocalTransform), typeof(Speed), typeof(Active) },
                None = new ComponentType[] { typeof(Disabled) }
            });
    }

    /// <summary>
    /// 매 프레임 업데이트 — 캐싱된 쿼리를 통해 Active이면서 Disabled가 아닌 엔티티의 Y 위치를 업데이트합니다.
    /// </summary>
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        float deltaTime = SystemAPI.Time.DeltaTime;

        foreach (var (transform, speed) in
            _movementQuery.ToEntityQuery(state)
                .ToComponentDataArray<(RefRW<LocalTransform>, RefRO<Speed>)>(state.WorldUpdateAllocator))
        {
            // 속도값을 절댓값으로 처리 (항상 양수 이동 거리 계산)
            float speedValue = math.abs(speed.ValueRO.Value);

            // 프레임당 이동 거리 계산
            float distanceThisFrame = speedValue * deltaTime;

            // 부스트 조건 판정 및 최종 이동 거리 계산
            float finalMovementDistance = (distanceThisFrame > BoostDistanceThreshold)
                ? distanceThisFrame * SpeedBoostMultiplier
                : distanceThisFrame;

            // 위치 업데이트
            transform.ValueRW.Position.y += finalMovementDistance;
        }
    }
}

/// <summary>
/// 속도 컴포넌트 — 엔티티의 이동 속도를 나타냅니다.
/// 항상 양수 값을 가지며, 절댓값으로 처리됩니다.
/// </summary>
public struct Speed : IComponentData
{
    /// <summary>매 초 단위로 이동할 거리입니다. 항상 양수 값으로 설정하세요.</summary>
    public float Value;
}

/// <summary>
/// Active 마커 컴포넌트 — 이 마크를 가진 엔티티는 이동 시스템의 영향을 받습니다.
/// </summary>
public struct Active : IComponentData
{
}

/// <summary>
/// Disabled 마커 컴포넌트 — 이 마크를 가진 엔티티는 이동 시스템에서 제외됩니다.
/// Active와 독립적으로 사용되며, Disabled가 우선합니다 (None 필터).
/// </summary>
public struct Disabled : IComponentData
{
}
```
