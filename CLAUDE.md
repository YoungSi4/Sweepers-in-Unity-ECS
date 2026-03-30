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

## 토큰 최적화

Claude Code는 제한된 토큰 예산으로 작동합니다. 토큰을 낭비하지 않으려면:

### 응답 효율성
- 불필요한 설명 제거 — "지금 파일을 읽겠습니다" 같은 보고 제외
- 코드 변경만 명시 — 변경 전후 비교나 대체 방안 설명 금지 (사용자가 diff 확인 가능)
- 한 번에 여러 관련 파일 변경 — 개별 변경 여러 번보다 배치 처리
- 질문이 있으면 최소한의 물음으로 정리 (AskUserQuestion 사용 시 짧은 선택지)

### 도구 사용 최적화
- Glob, Grep, Read를 리스트 형식으로 배치 실행 (여러 호출을 한 번에)
- Agent 도구 남용 금지 — Glob/Grep 만으로 가능한 작업은 직접 수행
- 파일 읽기 전 필요 범위 확정 (limit/offset 활용으로 전체 파일 읽기 피하기)

### 프롬프트 작성
- 코드 예시는 작은 스니펫만 포함 (전체 파일 X)
- 반복 설명 금지 — 이전 메시지에서 말한 내용 재설명 X
- 마크다운 테이블/리스트로 정보 압축 (문단 문장 형식보다 효율)

### 메모리 및 컨텍스트
- 자동 메모리(`~/.claude/projects/*/memory/`)에 재사용 정보 저장
- 큰 코드 스니펫이나 출력은 메모리에 링크로만 기록

---

## GUI 출력 지양

Claude Code와 상호작용할 때는 **텍스트 기반 인터페이스**만 사용합니다. 그래픽 요소나 선택 UI는 토큰을 낭비하고 자동화를 방해합니다.

### 금지 사항
- AskUserQuestion에서 `preview` 필드 사용 금지 (다중 라인 선택지 시각화)
- 이모지 과다 사용 (필요하지 않으면 제거 — 사용자가 명시 요청 시에만)
- 마크다운 `<details>` 태그 등 숨김 영역 생성 금지
- 실행 결과 요약표, 진행 상황 바, 컬러 코드 등 시각적 요소 최소화

### 권장 방식
- 선택지는 텍스트 옵션만 제시 (`option 1`, `option 2`, ...)
- 질문은 간결한 텍스트 목록 형식
- 필요시 마크다운 코드 블록으로 구조화
- 결과는 숫자, 파일명, 상태 텍스트로만 표현

### AskUserQuestion 사용 규칙
- multiSelect 필드 최소화 (true일 때도 선택지는 최소 2개, 최대 4개)
- preview 필드는 절대 사용 금지
- 한 번에 질문은 최대 3개 (더 많으면 순차 질문)
- 선택지 설명은 1줄 (2줄 이상 금지)

---

## Agentic Workflow API
@claude_tools/claude_subprocess_api.md
