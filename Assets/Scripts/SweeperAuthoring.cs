using UnityEngine;
using Unity.Entities;
using Unity.Mathematics;

public struct Sweeper : IComponentData
{
    public float Speed;
    public float TimeToDestroy;
    public float Timer;

    public static Sweeper Random(uint seed, float speed, float time_to_destroy)
        => new Sweeper() {
            Speed = new Unity.Mathematics.Random(seed).NextFloat(speed, speed + 1),
            TimeToDestroy = time_to_destroy
        };
}

public class SweeperAuthoring : MonoBehaviour
{
    public float _speed = 1.0f;
    public float _time_to_destroy = 20f;
    public float _timer = 0f;

    class Baker : Baker<SweeperAuthoring> {
        public override void Bake(SweeperAuthoring authoring)
        {
            var data = new Sweeper()
            {
                Speed = authoring._speed,
                TimeToDestroy = authoring._time_to_destroy,
                Timer = authoring._timer
            };
            AddComponent(GetEntity(TransformUsageFlags.Dynamic), data);
        }
    }
}
