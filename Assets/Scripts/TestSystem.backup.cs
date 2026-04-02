using Unity.Entities;
using Unity.Mathematics;
using Unity.Transforms;

// 테스트용 ECS 시스템 - 리팩터링 기회가 있는 코드
public partial struct TestSystem : ISystem
{
    // 문제점 1: Burst 컴파일 속성 누락
    public void OnUpdate(ref SystemState state)
    {
        float dt = SystemAPI.Time.DeltaTime;

        // 문제점 2: 복잡한 쿼리 로직
        foreach (var (transform, speed) in
            SystemAPI.Query<RefRW<LocalTransform>, RefRO<Speed>>()
                .WithAll<Active>()
                .WithNone<Disabled>())
        {
            // 문제점 3: 변수명이 모호함
            var val = speed.ValueRO.Value;
            var x = dt * val;

            // 문제점 4: 매직 넘버 사용
            if (x > 10.0f)
            {
                transform.ValueRW.Position.y += x * 2f;
            }
            else
            {
                transform.ValueRW.Position.y += x;
            }
        }
    }
}

// 문제점 5: 네이밍 규칙 위반 (public 필드)
public struct Speed : IComponentData
{
    public float Value;
}

// 문제점 6: 문서화 부재
public struct Active : IComponentData
{
}

// 문제점 7: 불필요한 MonoBehaviour 혼용 가능성
public struct Disabled : IComponentData
{
}
