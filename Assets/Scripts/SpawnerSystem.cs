using Unity.Entities;
using Unity.Burst;
using Unity.Collections;
using Unity.Transforms;
using Unity.Mathematics;

// [UpdateInGroup(typeof(InitializationSystemGroup))]
public partial struct SpawnerSystem: ISystem
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

            for (int i = 0; i < spawner.ValueRO.Spawn_count; i++)
            {
                var instance = ecb.Instantiate(spawner.ValueRO.sweeper);
                ecb.SetComponent(instance, LocalTransform.FromPositionRotation(xform.ValueRO.Position, spawner.ValueRO.Sweeper_stand));

                // set speed randomly
                ecb.SetComponent(instance, Sweeper.Random(spawner.ValueRW.Rand.NextUInt(), spawner.ValueRO.Sweeper_speed, spawner.ValueRO.Time_to_destroy));
            }
        }
    }
}
