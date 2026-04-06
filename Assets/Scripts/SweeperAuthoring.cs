using UnityEngine;
using Unity.Entities;

public struct Sweeper : IComponentData
{
    public float Speed;
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
