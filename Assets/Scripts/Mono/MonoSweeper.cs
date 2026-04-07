using UnityEngine;

public class MonoSweeper : MonoBehaviour
{
    public float Speed = 40f;
    public float TimeToDestroy = 30f;
    public float Timer = 0f;

    void Update()
    {
        Timer += Time.deltaTime;
        if (Timer > TimeToDestroy)
        {
            Destroy(gameObject);
            return;
        }


        transform.position = transform.position + new Vector3(Speed * Time.deltaTime, 0, 0);
    }
}
