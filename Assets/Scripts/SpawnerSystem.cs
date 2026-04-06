using Unity.Entities;
using Unity.Burst;
using Unity.Collections;
using Unity.Transforms;

// [UpdateInGroup(typeof(InitializationSystemGroup))]
public partial struct SpawnerUpdateJob: ISystem
{
    public void OnCreate(ref SystemState state)
        => state.RequireForUpdate<Spawner>();

    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        var ecb = new EntityCommandBuffer(Allocator.Temp);

        foreach (var (spawner, xform) in SystemAPI.Query<RefRW<Spawner>, RefRO<LocalToWorld>>())
        {
            spawner.ValueRW.timer += SystemAPI.Time.DeltaTime;

            if (spawner.ValueRO.timer < spawner.ValueRO.Spawn_delay)
                return;
            spawner.ValueRW.timer = 0f;

            for (int i = 0; i < spawner.ValueRO.Spawn_count; i++)
            {
                var instances = ecb.Instantiate(spawner.ValueRO.sweeper);
                ecb.SetComponent(instances, LocalTransform.FromPosition(xform.ValueRO.Position));
            }
        }
            
        ecb.Playback(state.EntityManager);
        ecb.Dispose();
    }
}
