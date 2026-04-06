using Unity.Entities;
using Unity.Burst;
using Unity.Collections;
using Unity.Transforms;
using Unity.Mathematics;

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
                continue;
            spawner.ValueRW.timer = 0f;

            var rand = new Random(spawner.ValueRO.Random_seed);

            for (int i = 0; i < spawner.ValueRO.Spawn_count; i++)
            {
                var instance = ecb.Instantiate(spawner.ValueRO.sweeper);
                ecb.SetComponent(instance, LocalTransform.FromPosition(xform.ValueRO.Position));

                // set speed randomly
                ecb.SetComponent(instance, Sweeper.Random(rand.NextUInt(), spawner.ValueRO.Sweeper_speed));
            }
        }
            
        ecb.Playback(state.EntityManager);
        ecb.Dispose();
    }
}
