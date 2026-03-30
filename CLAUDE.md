# Sweepers in ECS — Claude Code 작성 지침

## 프로젝트 개요

- **게임명**: Sweepers in ECS
- **엔진**: Unity 6 (6000.3.11f1)
- **렌더 파이프라인**: URP (Universal Render Pipeline)
- **아키텍처**: DOTS / ECS (Entity Component System)
- **언어**: C# (.NET)

## 핵심 패키지

| 패키지 | 버전 | 용도 |
|---|---|---|
| com.unity.render-pipelines.universal | 17.3.0 | URP 렌더링 |
| com.unity.inputsystem | 1.19.0 | 입력 처리 |
| com.unity.ai.navigation | 2.0.11 | AI 내비게이션 |
| com.unity.timeline | 1.8.11 | 컷씬/타임라인 |
| com.unity.burst | (간접 의존) | 고성능 컴파일 |
| com.unity.mathematics | (간접 의존) | SIMD 수학 라이브러리 |
| com.unity.collections | (간접 의존) | NativeContainer |

## 폴더 구조

```
Assets/
├── Scenes/          # Unity 씬 파일
├── Scripts/         # C# 스크립트
│   ├── Components/  # ECS 컴포넌트 (IComponentData 등)
│   ├── Systems/     # ECS 시스템 (ISystem 등)
│   ├── Authoring/   # Baker/Authoring MonoBehaviour
│   └── Hybrid/      # ECS와 연결되는 MonoBehaviour
├── Settings/        # URP 렌더러 에셋
└── ...
```

## 코드 컨벤션

### 일반 C# 규칙
- 클래스/구조체/메서드: `PascalCase`
- 필드(private): `_camelCase` (언더스코어 접두사)
- 로컬 변수/파라미터: `camelCase`
- 상수: `PascalCase` (const/static readonly)
- 인터페이스: `IFoo` 형태 유지

### ECS / DOTS 규칙
- 컴포넌트는 `IComponentData`를 구현하는 `struct`로 작성
- 시스템은 `ISystem` 인터페이스 사용 (class 기반 `SystemBase`보다 선호)
- `Burst.CompileAttribute`를 최대한 활용해 성능 확보
- `NativeArray`, `NativeList` 등 NativeContainer 사용 시 `Allocator` 명시
- `EntityQuery`는 `OnCreate`에서 캐싱하여 재사용
- Authoring 컴포넌트는 `Baker<T>`를 통해 ECS 데이터로 변환

### 예시 패턴

```csharp
// 컴포넌트
public struct Speed : IComponentData
{
    public float Value;
}

// 시스템
[BurstCompile]
public partial struct MoveSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        float dt = SystemAPI.Time.DeltaTime;
        foreach (var (transform, speed) in
            SystemAPI.Query<RefRW<LocalTransform>, RefRO<Speed>>())
        {
            transform.ValueRW.Position.y += speed.ValueRO.Value * dt;
        }
    }
}

// Authoring
public class SpeedAuthoring : MonoBehaviour
{
    public float speed = 5f;

    class Baker : Baker<SpeedAuthoring>
    {
        public override void Bake(SpeedAuthoring authoring)
        {
            var entity = GetEntity(TransformUsageFlags.Dynamic);
            AddComponent(entity, new Speed { Value = authoring.speed });
        }
    }
}
```

## 작업 시 주의사항

- `.meta` 파일은 Unity가 자동 생성하므로 직접 편집하지 말 것
- `Library/`, `Temp/`, `obj/` 폴더는 git에 포함하지 말 것 (이미 gitignore 처리됨)
- URP 설정(`Assets/Settings/`)을 변경할 때는 PC/Mobile 렌더러를 구분하여 적용
- `Packages/manifest.json` 변경 후 Unity 에디터를 재시작해야 적용됨
- DOTS 패키지 추가 시 `com.unity.entities` 등을 manifest.json에 명시적으로 추가 필요

## 금지 사항

- MonoBehaviour `Update()`에서 heavy한 로직 실행 금지 — ECS 시스템으로 이전
- `GameObject.Find`, `FindObjectOfType` 런타임 사용 금지 — 직접 참조 또는 ECS Query 활용
- `BurstCompile` 시스템 내에서 관리형(Managed) 타입 사용 금지
- 불필요한 `Allocator.Persistent` NativeContainer 생성 금지 — 수명 관리 명확히 할 것
