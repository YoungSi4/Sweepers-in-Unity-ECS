using System.Collections.Generic;
using System.Threading;
using Unity.Entities;
using Unity.Mathematics;
using UnityEngine;

public struct Spawner : IComponentData
{
    public float Spawn_delay;
    public float timer;
    public int Spawn_count;
    public Entity sweeper;
    public float Sweeper_speed;
    public quaternion Sweeper_stand;
    public Unity.Mathematics.Random Rand;
    public float Time_to_destroy;

    //public Pool pool;

    //public struct Pool : IComponentData
    //{
    //    public Sweeper sweeper;
    //    public Stack<Sweeper> container;
    //}
}

public class SpawnerAuthoring : MonoBehaviour
{
    public float _spawnDelay = 1.0f;
    public GameObject _Prefab = null;
    public int _spawnCount = 1;
    public float _timer = 0f;
    public uint _randomSeed = 10;

    public float _sweeper_speed = 5f;
    public float _time_to_destroy = 30f;

    class Baker : Baker<SpawnerAuthoring>
    {
        public override void Bake(SpawnerAuthoring authoring)
        {
            var data = new Spawner()
            {
                Spawn_delay = authoring._spawnDelay,
                sweeper = GetEntity(authoring._Prefab, TransformUsageFlags.Dynamic),
                Spawn_count = authoring._spawnCount,
                timer = authoring._timer,
                Sweeper_speed = authoring._sweeper_speed,
                Sweeper_stand = quaternion.EulerXYZ(0, math.PI, 0),
                Rand = new Unity.Mathematics.Random(authoring._randomSeed),
                Time_to_destroy = authoring._time_to_destroy
            };
            // spawner is invisible but I choose renderable
            AddComponent(GetEntity(TransformUsageFlags.Dynamic), data);
        } // bake
    } // baker class
}
