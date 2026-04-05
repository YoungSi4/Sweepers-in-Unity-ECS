using Unity.Burst;
using Unity.Entities;
using Unity.Transforms;

[BurstCompile]
partial struct SweeperUpdateJob : IJobEntity
{
    public float Elapsed;

    void Execute(in Sweeper sweeper, ref LocalTransform xform)
    {
        var dX = sweeper.Speed * Elapsed;
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
            Elapsed = (float)SystemAPI.Time.ElapsedTime
        };
        job.ScheduleParallel();
    }
}
