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

    // [BurstCompile] // OnCreate Call Only Once ; no need for BurstCompile
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