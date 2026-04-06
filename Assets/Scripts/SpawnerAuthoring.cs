using System.Collections.Generic;
using System.Threading;
using Unity.Entities;
using UnityEngine;
using UnityEngine.Pool;

public struct Spawner : IComponentData
{
    public float Spawn_delay;
    public float timer;
    public int Spawn_count;
    public Entity sweeper;
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

    class Baker : Baker<SpawnerAuthoring>
    {
        public override void Bake(SpawnerAuthoring authoring)
        {
            var data = new Spawner()
            {
                Spawn_delay = authoring._spawnDelay,
                sweeper = GetEntity(authoring._Prefab, TransformUsageFlags.Dynamic),
                Spawn_count = authoring._spawnCount,
                timer = authoring._timer
            };
            // spawner is invisible but I choose renderable
            AddComponent(GetEntity(TransformUsageFlags.Renderable), data);
        } // bake
    } // baker class
}
