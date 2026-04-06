using Unity.Burst;
using Unity.Entities;
using Unity.Transforms;
// using UnityEngine;

[BurstCompile]
partial struct SweeperUpdateJob : IJobEntity
{
    public float Deltatime;

    void Execute(in Sweeper sweeper, ref LocalTransform xform)
    {
        // Time.deltaTime : called from MonoBehaviour.FixedUpdate or WaitForFixedUpdate
        var dX = sweeper.Speed * Deltatime;
        xform.Position.x += dX;
    }
}

public partial struct SweeperSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        var job = new SweeperUpdateJob()
        {
            Deltatime = (float)SystemAPI.Time.DeltaTime
        };
        job.ScheduleParallel();
    }
}
