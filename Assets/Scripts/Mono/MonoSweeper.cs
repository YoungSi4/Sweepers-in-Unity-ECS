using UnityEngine;

public class MonoSweeper : MonoBehaviour
{
    public float Speed = 40f;
    public float TimeToDestroy = 30f;
    public float Timer = 0f;
    private MonoSpawner Spawner;

    void Update()
    {
        Timer += Time.deltaTime;
        if (Timer > TimeToDestroy)
        {
            Spawner.PushSweeper(this);
        }

        transform.position = transform.position + new Vector3(Speed * Time.deltaTime, 0, 0);
    }
    
    public void Init(Vector3 pos, MonoSpawner spawner)
    {
        Spawner = spawner;

        var temp_pos = transform.position;
        temp_pos.x = pos.x;
        temp_pos.y = pos.y;
        temp_pos.z = pos.z;
        transform.position = temp_pos;
    }
}
