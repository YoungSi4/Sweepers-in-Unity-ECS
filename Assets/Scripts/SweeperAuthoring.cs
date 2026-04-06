using UnityEngine;
using Unity.Entities;
using Unity.Mathematics;

public struct Sweeper : IComponentData
{
    public float Speed;
    public static Sweeper Random(uint seed, float speed)
        => new Sweeper() {
            Speed = new Unity.Mathematics.Random(seed).NextFloat(speed, speed + 1)};
}

public class SweeperAuthoring : MonoBehaviour
{
    public float _speed = 1.0f;

    class Baker : Baker<SweeperAuthoring> {
        public override void Bake(SweeperAuthoring authoring)
        {
            var data = new Sweeper() { Speed = authoring._speed };
            AddComponent(GetEntity(TransformUsageFlags.Dynamic), data);
        }
    }
}
