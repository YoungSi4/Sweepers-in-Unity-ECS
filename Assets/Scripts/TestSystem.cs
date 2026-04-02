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