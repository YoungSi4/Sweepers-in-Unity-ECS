using System.Collections.Generic;
using Unity.Collections;
using Unity.Entities;
using UnityEngine;

public class MonoSpawnerPool
{
    private Stack<MonoSweeper> sweeperPool = new Stack<MonoSweeper>();
    public GameObject Prefab;

    public void Init(int pool_size, GameObject prefab)
    {
        Prefab = prefab;

        for (int i = 0; i < pool_size; i++)
        {
            AddObj();
        }
    }

    public int PoolSize()
    {
        return sweeperPool.Count;
    }

    public void AddObj()
    {
        var temp = GameObject.Instantiate(Prefab).GetComponent<MonoSweeper>();
        temp.enabled = false;
        sweeperPool.Push(temp);
    }

    public void PushObj(MonoSweeper sweeper)
    {
        sweeperPool.Push(sweeper);
    }

    public MonoSweeper EnableObj()
    {
        if (sweeperPool.Count <= 0)
        {
            AddObj();
        }

        var sweeper = sweeperPool.Peek();
        sweeperPool.Pop();
        return sweeper;
    }

}

public class MonoSpawner : MonoBehaviour
{
    private MonoSpawnerPool SweeperPool;

    public float Spawn_delay = 0.2f;
    public float timer = 0f;
    public int Spawn_count = 2;
    public GameObject prefab;
    public float Time_to_destroy = 30f;
    public int initPoolSize = 100;

    private void Awake()
    {
        SweeperPool = new MonoSpawnerPool();
        SweeperPool.Init(initPoolSize, prefab);
    }

    void Update()
    {
        timer += Time.deltaTime;
        if (timer < Spawn_delay)
            return;
        timer = 0f;

        MonoSweeper temp = SweeperPool.EnableObj();
        temp.enabled = true;
        temp.Init(transform.position, this);
    }

    public void PushSweeper(MonoSweeper sweeper)
    {
        SweeperPool.PushObj(sweeper);
        sweeper.enabled = false;
    }
}
