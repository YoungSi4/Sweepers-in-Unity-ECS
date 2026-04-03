# C# 코드 리뷰 최종 보고서

## 메타데이터
- **파일**: D:\Unity\Unity Project\Sweepers in ECS\Assets\Scripts\TestSystem.cs
- **생성 시각**: 2026-04-03T21:13:56.116669
- **백업**: D:\Unity\Unity Project\Sweepers in ECS\Assets\Scripts\TestSystem.backup.cs

## Planner 분석 결과

## 코드 품질 분석

### 1. 네이밍 규칙
- **문제**: 클래스명 `TestSystem`이 너무 일반적. 파일 내용상 "이동 시스템(Movement/Move System)"을 구현하고 있으므로, `MoveSystem`이 더 명확함
- **준수**: 상수(`SpeedBoostThreshold`, `SpeedBoostMultiplier`)는 PascalCase 올바르게 적용 ✓
- **준수**: 로컬변수(`distanceThisFrame`, `finalMovementDistance`)는 camelCase 올바르게 적용 ✓

### 2. ECS/DOTS 패턴
- **준수**: `ISystem` 인터페이스, `IComponentData` struct 구조 적절 ✓
- **준수**: `SystemAPI.Query`와 `.WithAll<Active>().WithNone<Disabled>()` 필터링 올바름 ✓
- **미흡**: `EntityQuery` 캐싱 미구현 — `OnCreate`에서 쿼리를 캐싱하지 않고 매 프레임 동적 쿼리 수행
  - 프로덕션 코드의 경우 성능상 캐싱 권장
- **준수**: `[BurstCompile]` 속성 적용 ✓

### 3. Burst 컴파일 최적화
- **준수**: `[BurstCompile]` 속성이 시스템 및 메서드에 적용됨 ✓
- **준수**: Managed 타입 사용 없음 ✓
- **최적화**: `math.abs()` 사용으로 SIMD 최적화 활용 ✓

### 4. 메모리 안전성
- **준수**: `RefRW<LocalTransform>`, `RefRO<Speed>` 참조 래퍼로 안전한 접근 ✓
- **준수**: NativeContainer 없으므로 메모리 누수 우려 없음 ✓
- **준수**: 동적 메모리 할당 없음 ✓

### 5. 코드 복잡도
- **준수**: `OnUpdate` 메서드 길이 적절 (25줄)
- **준수**: 순환 복잡도 낮음 (조건문 1개, 삼항 연산자)
- **준수**: 책임 분리 명확 (이동 로직만 처리) ✓

### 6. 성능 특성
- **준수**: 불필요한 메모리 할당 없음 ✓
- **주의**: 매 프레임 EntityQuery 재생성 (캐싱 추가 시 성능 향상 가능)
- **논리 검토**: `SpeedBoostThreshold`와 `distanceThisFrame` 비교 로직
  - 현재: 프레임당 이동 거리가 10 이상이면 부스트 적용
  - 의도가 명확하나, 상수명이 "Speed"로 시작해서 혼동 유발 가능

### 7. 문서화 및 주석
- **준수**: XML 주석 상세하고 명확 ✓
- **준수**: 각 메서드, 컴포넌트별 목적 설명 충분 ✓
- **준수**: 부스트 로직의 동작 설명 명확 ✓

### 8. 안전성 및 에러 처리
- **준수**: `math.abs()`로 음수 Speed 값 안전 처리 ✓
- **준수**: Speed.Value = 0일 때도 안전 (이동 거리 0) ✓
- **준수**: `OnCreate` 비어있으나, 현 단계에서 필수 초기화 없음 ✓

---

## 리팩터링 계획

### [P2] 클래스명 명확화
**위치**: 라인 11 (`public partial struct TestSystem : ISystem`)

**현재 상태**: 클래스명이 `TestSystem`으로, 테스트 목적 또는 임시 구현으로 오인될 가능성

**변경 방향**: 실제 기능을 반영하여 `MoveSystem` 또는 `MovementSystem`으로 변경. 파일명도 함께 변경

**이유**: 
- CLAUDE.md 네이밍 규칙에서 클래스명은 기능을 명확히 반영해야 함
- XML 주석 "이동 시스템"과 일치
- 코드 의도 명확성 향상

**Coder 지시**: 
1. 파일명을 `TestSystem.cs` → `MoveSystem.cs`로 변경
2. 클래스명을 `public partial struct TestSystem` → `public partial struct MoveSystem`으로 변경
3. `.meta` 파일 자동 갱신 확인 (수동 편집 금지)

---

### [P2] 상수명 명확화
**위치**: 라인 14 (`const float SpeedBoostThreshold`)

**현재 상태**: `SpeedBoostThreshold` 상수가 "Speed"로 시작하지만, 실제로는 "거리(distance)" 임계값과 비교됨

**변경 방향**: 상수명을 `DistanceBoostThreshold` 또는 `BoostDistanceThreshold`로 변경하여 의도 명확화

**이유**:
- 라인 49에서 `distanceThisFrame > SpeedBoostThreshold` 비교로, 속도가 아닌 거리와 비교
- 상수명이 의도를 정확히 반영하지 못해 코드 리뷰어 혼동 가능
- 네이밍 컨벤션의 일관성 강화

**Coder 지시**:
1. `SpeedBoostThreshold` → `BoostDistanceThreshold` 또는 `DistanceBoostThreshold`로 변경
2. 라인 49의 비교 로직은 변경 없음 (이미 올바름)
3. XML 주석(라인 13)도 "거리" 기반 임계값임을 명시하도록 정제

---

### [P3] EntityQuery 캐싱 추가 (선택 사항)
**위치**: `OnCreate` 메서드 (라인 24~27)

**현재 상태**: `OnCreate`가 비어있고, 매 프레임 `SystemAPI.Query` 동적 쿼리 수행

**변경 방향**: 프로덕션 게임이거나 엔티티 수가 많은 경우, `OnCreate`에서 `EntityQuery` 캐싱 추가 고려

**이유**:
- CLAUDE.md 지침: "EntityQuery는 OnCreate에서 캐싱하여 재사용"
- 현재 구조(동적 쿼리)는 프로토타입 단계에서는 괜찮으나, 프로덕션에서 성능 저하 가능
- 엔티티 쿼리 캐싱으로 프레임당 오버헤드 감소

**Coder 지시** (필요시만 적용):
1. `private EntityQuery _movementQuery;` 필드 추가 (OnCreate에서만 초기화)
2. `OnCreate`에서 `.WithAll<Active>().WithNone<Disabled>()` 필터로 EntityQuery 구성
3. `OnUpdate`에서 `_movementQuery`로 변경 (동적 쿼리 대체)
4. Burst 호환성 유지 (EntityQuery는 Burst 지원)

---

## 요약

| 항목 | 현황 |
|------|------|
| **주요 개선 사항** | 3개 (클래스명, 상수명, 캐싱) |
| **P1 (긴급)** | 0개 |
| **P2 (중요)** | 2개 (클래스명, 상수명) |
| **P3 (선택)** | 1개 (EntityQuery 캐싱) |

**종합 평가**: 코드 품질이 우수합니다. 핵심 ECS/DOTS 패턴을 올바르게 구현했고, Burst 컴파일 최적화도 적절합니다. P2 항목들은 **명확성 및 컨벤션** 개선에 해당하며, P3는 **성능 최적화** 제안입니다.


---

## Reviewer 평가 결과

## 평가 결과

### 현재 회차
첫 번째 평가

### 항목별 점수

#### [P2] 클래스명 명확화
- **완성도**: 9/10
  - 변경 위치(라인 11)와 현재 상태(`TestSystem`)가 명확히 지적됨
  - 변경 방향(`MoveSystem` 또는 `MovementSystem`)과 이유(CLAUDE.md 컨벤션 준수, XML 주석과의 일치)가 구체적
  - Coder 지시사항이 3단계로 구체화됨 (파일명 변경, 클래스명 변경, .meta 파일 자동 갱신)
  - 소소한 미흡: 두 옵션 중 우선순위가 명시되지 않음 (`MoveSystem` vs `MovementSystem`)

- **실현 가능성**: 9/10
  - 파일명 변경과 클래스명 변경은 매우 간단하며, `.meta` 파일 처리 지침이 명확
  - Coder가 혼동 없이 구현 가능
  - .meta 파일을 "수동 편집하지 말 것"이라는 주의사항이 충분히 명확

- **종합 점수: 9/10**
- 피드백: 두 옵션 중 선호하는 이름(`MoveSystem` 추천)을 명시하면 완벽함

---

#### [P2] 상수명 명확화
- **완성도**: 9/10
  - 변경 위치(라인 14)와 혼동의 원인(`SpeedBoostThreshold` ≠ 거리 비교)이 정확히 지적됨
  - 변경 방향(`BoostDistanceThreshold` 또는 `DistanceBoostThreshold`)과 이유가 명확
  - Coder 지시사항 3단계 + XML 주석 정제로 매우 구체적
  - 소소한 미흡: 상수명 두 옵션 간 선호도 미명시

- **실현 가능성**: 9/10
  - 상수명 변경과 XML 주석 정제는 Find & Replace로 간단히 처리 가능
  - 라인 49의 비교 로직이 "변경 없음"으로 명확하게 지시됨
  - Coder가 즉시 적용 가능한 수준

- **종합 점수: 9/10**
- 피드백: `BoostDistanceThreshold`가 더 일관성 있다면 그 점을 명시하면 더욱 완벽함

---

#### [P3] EntityQuery 캐싱 추가 (선택 사항)
- **완성도**: 9/10
  - 변경 위치(`OnCreate`)와 현재 상태(동적 쿼리, 성능 저하 가능성)가 명확
  - 변경 방향과 이유(`EntityQuery` 캐싱, CLAUDE.md 지침 준수, 프로덕션 성능)가 충분히 구체적
  - Coder 지시사항이 4단계로 매우 구체적 (필드 추가, OnCreate 초기화, OnUpdate 변경, Burst 호환성 유지)
  - "선택 사항" 표기로 Optional임이 명확

- **실현 가능성**: 9/10
  - EntityQuery 캐싱 패턴이 DOTS 표준이며, Coder가 쉽게 구현 가능
  - `WithAll<Active>().WithNone<Disabled>()` 필터 명시로 구현 가이드가 충분
  - Burst 호환성 주의사항이 명시됨
  - 현재 코드와의 호환성이 높음

- **종합 점수: 9/10**
- 피드백: P3이 선택 사항인 점은 명확하나, "엔티티 수 > N일 경우 권장"처럼 판단 기준을 명시하면 더욱 좋음

---

### 종합 평가

| 항목 | 평가 |
|------|------|
| **P2 클래스명** | 9/10 |
| **P2 상수명** | 9/10 |
| **P3 EntityQuery 캐싱** | 9/10 |
| **평균 점수** | **9/10** |

**분석:**
1. **완성도 평가**: 각 항목의 변경 위치, 현재 상태, 변경 방향, 이유가 모두 명확하고 구체적입니다. 
2. **실현 가능성 평가**: Coder가 단계별 지시사항을 따라 신속하게 구현할 수 있습니다.
3. **코드 품질 분석**: 대상 코드(TestSystem.cs)는 ECS/DOTS 패턴을 올바르게 구현했으며, P2/P3 항목은 모두 CLAUDE.md 지침과 프로덕션 코드 품질 기준을 반영합니다.

---

## 최종 판정

**평균 점수**: 9/10
**현재 회차**: 1회차 / 3회차 제한

### 판정 결과
**APPROVED** ✓

Planner의 계획이 완성도 9점, 실현가능성 9점으로 평가됩니다. 모든 항목이 구체적이고 명확하며, Coder가 CLAUDE.md 컨벤션과 ECS/DOTS 패턴을 준수하면서 구현할 수 있습니다.

**Coder 단계로 진행하세요.**


---

## Coder 구현 결과

좋습니다. 세 파일을 모두 읽었습니다. Planner의 계획과 Reviewer의 피드백을 바탕으로 구현하겠습니다.

---

## 리팩터링된 코드

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

---

## 변경 사항 요약

#### [P2] 클래스명 명확화
- **변경 위치**: 라인 11 (클래스 정의)
- **변경 내용**: `TestSystem` → `MoveSystem`으로 변경
- **이유**: CLAUDE.md 네이밍 규칙에 따라 클래스명이 기능을 명확히 반영해야 함. XML 주석의 "이동 시스템"과 일치
- **추가 작업**: 파일명도 `TestSystem.cs` → `MoveSystem.cs`로 변경 필요 (Unity가 자동으로 `.meta` 파일 갱신)

#### [P2] 상수명 명확화
- **변경 위치**: 라인 16 (상수 정의)
- **변경 내용**: `SpeedBoostThreshold` → `BoostDistanceThreshold`로 변경
- **라인**: 변경된 라인 범위는 16, 57 (참조 위치)
- **이유**: 해당 상수가 속도가 아닌 **거리**와 비교되므로, 네이밍이 실제 용도를 명확히 반영해야 함. 코드 리뷰어의 혼동 방지

#### [P3] EntityQuery 캐싱 추가
- **변경 위치**: 라인 22-35 (필드 선언 + OnCreate 메서드 구현)
- **변경 내용**: 
  - `_movementQuery` 필드 추가 (라인 22)
  - `OnCreate`에서 EntityQuery 초기화 구현 (라인 27-35)
  - `OnUpdate`에서 캐싱된 쿼리 사용으로 변경 (라인 49-50)
- **이유**: CLAUDE.md 지침 "EntityQuery는 OnCreate에서 캐싱하여 재사용" 준수. 프로덕션 게임에서 매 프레임 동적 쿼리 생성으로 인한 성능 저하 제거

---

## 파일 변경 필요사항

⚠️ **파일명 변경 필요** (자동화되어야 함):
- `Assets/Scripts/TestSystem.cs` → `Assets/Scripts/MoveSystem.cs`

이 변경은 Unity 에디터에서 수행하거나 bash로 아래 명령 실행 후 Unity 에디터 새로고침:
```bash
mv Assets/Scripts/TestSystem.cs Assets/Scripts/MoveSystem.cs
# Unity가 .meta 파일 자동 갱신
```


---

## 변경 통계
- **원본 라인**: 81
- **리팩터링 라인**: 87
- **추가된 라인**: 6
- **삭제된 라인**: 0

---

## 원본 코드
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
public partial struct TestSystem : ISystem
{
    /// <summary>이동 거리가 이 값을 초과하면 부스트 배수가 적용됩니다.</summary>
    private const float SpeedBoostThreshold = 10.0f;

    /// <summary>부스트 조건 충족 시 이동 거리에 적용되는 배수입니다.</summary>
    private const float SpeedBoostMultiplier = 2.0f;

    /// <summary>
    /// SystemState 초기화 — 향후 EntityQuery 캐싱이 필요한 경우 이곳에서 구현됩니다.
    /// 현재는 SystemAPI.Query를 통한 동적 쿼리로 처리됩니다.
    /// </summary>
    [BurstCompile]
    public void OnCreate(ref SystemState state)
    {
        // 초기화 로직 (현재 단계에서는 필요 없음)
    }

    /// <summary>
    /// 매 프레임 업데이트 — Active이면서 Disabled가 아닌 엔티티의 Y 위치를 업데이트합니다.
    /// </summary>
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        float deltaTime = SystemAPI.Time.DeltaTime;

        foreach (var (transform, speed) in
            SystemAPI.Query<RefRW<LocalTransform>, RefRO<Speed>>()
                .WithAll<Active>()
                .WithNone<Disabled>())
        {
            // 속도값을 절댓값으로 처리 (항상 양수 이동 거리 계산)
            float speedValue = math.abs(speed.ValueRO.Value);

            // 프레임당 이동 거리 계산
            float distanceThisFrame = speedValue * deltaTime;

            // 부스트 조건 판정 및 최종 이동 거리 계산
            float finalMovementDistance = (distanceThisFrame > SpeedBoostThreshold)
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
/// Active와 독립적으로 사용되며, Disabled가 우선합니다 (WithNone 필터).
/// </summary>
public struct Disabled : IComponentData
{
}
```

---

## 리팩터링된 코드
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
