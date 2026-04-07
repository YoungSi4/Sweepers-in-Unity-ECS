//using Unity.Burst;
//using Unity.Entities;
//using Unity.Transforms;
//// using UnityEngine;

//[BurstCompile]
//partial struct SweeperUpdateJob : IJobEntity
//{
//    public float Deltatime;
//    public EntityCommandBuffer.ParallelWriter Ecb;

//    void Execute([ChunkIndexInQuery] int sortKey, Entity entity, ref Sweeper sweeper, ref LocalTransform xform)
//    {
//        sweeper.Timer += Deltatime;
//        if (sweeper.Timer > sweeper.TimeToDestroy)
//        {
//            Ecb.DestroyEntity(sortKey, entity);
//            return;
//        }

//        // UnityEngine.Time.deltaTime : called from MonoBehaviour.FixedUpdate or WaitForFixedUpdate
//        xform.Position.x += sweeper.Speed * Deltatime;
//    }
//}

//public partial struct SweeperSystem : ISystem
//{
//    // private EntityQuery _query;

//    [BurstCompile]
//    public void OnUpdate(ref SystemState state)
//    {
//        var ecbSystem = SystemAPI.GetSingleton<EndSimulationEntityCommandBufferSystem.Singleton>();
//        var ecb = ecbSystem.CreateCommandBuffer(state.WorldUnmanaged).AsParallelWriter();

//        var job = new SweeperUpdateJob()
//        {
//            Deltatime = (float)SystemAPI.Time.DeltaTime,
//            Ecb = ecb
//        };
//        job.ScheduleParallel();
//    }
//}
