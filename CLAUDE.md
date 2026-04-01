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

## claude_tools 작업 규칙

### 한글 출력 명시
- 모든 claude_tools 에이전트 프롬프트는 **한글로 작성**
- Plan, Review, Implementation, Orchestration 결과물도 모두 **한글 마크다운**
- 사용자 요청이 한글이면 에이전트 출력도 한글로 유지

### UTF-8 인코딩 처리
- **프롬프트 작성**: 파일 상단에 `# -*- coding: utf-8 -*-` 선언
- **subprocess 호출**: `encoding='utf-8', errors='replace'` 파라미터 필수
- **파일 쓰기/읽기**: 항상 `encoding='utf-8'` 명시
- **Windows 콘솔**: 세션 시작 시 stdout을 UTF-8로 래핑:
  ```python
  import io, sys
  if sys.platform == 'win32' and not isinstance(sys.stdout, io.TextIOWrapper):
      try:
          sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
      except:
          pass  # 이미 래핑되었거나 불가능한 경우
  ```

### Anthropic API 직접 사용 (권장)
- **dependency 설치**: `pip install anthropic`
- **API 키 설정** (다음 중 하나):
  1. **환경 변수**: `set ANTHROPIC_API_KEY=sk-ant-...` (Windows)
  2. **Claude Code 웹/데스크톱**: 자동 인식 (설정 필요 없음)
  3. **.env 파일**: 프로젝트 루트에 `.env` 생성:
     ```
     ANTHROPIC_API_KEY=sk-ant-...
     ```
- **기본 패턴**:
  ```python
  from anthropic import Anthropic
  
  client = Anthropic()  # 자동으로 환경 변수/API 키 로드
  response = client.messages.create(
      model="claude-opus-4-6",
      max_tokens=4096,
      messages=[
          {"role": "user", "content": "한글 프롬프트"}
      ]
  )
  
  result = response.content[0].text
  ```
- **장점**: subprocess 불필요, 더 빠르고 직접적, 한글 완벽 지원, 의존성 최소화

### subprocess에서 Claude CLI 호출 시
- **shell=True 사용**: Windows에서 claude 명령어를 PATH에서 찾으려면 cmd.exe 경유 필요
- **git-bash 경로 설정 필수**: Claude CLI가 내부적으로 bash를 요구함
  ```python
  env = os.environ.copy()
  env["CLAUDE_CODE_GIT_BASH_PATH"] = r"D:\Git\bin\bash.exe"
  result = subprocess.run(
      ["claude", "-p", prompt, ...],
      env=env,
      shell=True,
      encoding='utf-8',
      errors='replace',
      timeout=300
  )
  ```
- **git-bash 위치**: `D:\Git\bin\bash.exe`
- **타임아웃**: 장시간 작업 시 `timeout=300` (초 단위) 지정

### git 명령어 허용 범위 (claude_tools 한정)
claude_tools 내 에이전트 및 스크립트는 **읽기 전용 git 명령어만** 허용합니다.

**허용 (읽기 전용):**
```
git diff
git diff --name-only
git diff --cached
git status
git log
git show
git blame
```

---

> ## ⛔ 절대 금지 — 어떠한 경우에도 예외 없음
>
> 다음 명령어는 **코드로 작성하거나, 에이전트 프롬프트에 포함하거나, 사용자에게 제안하는 것 모두 금지**합니다.
>
> ```
> git commit        # 변경사항 저장 금지
> git push          # 원격 저장소 반영 금지
> git pull          # 원격 변경사항 수신 금지
> git merge         # 브랜치 병합 금지
> git rebase        # 커밋 재작성 금지
> git reset         # 히스토리 변경 금지
> git checkout      # 브랜치/파일 전환 금지
> git branch -d/-D  # 브랜치 삭제 금지
> git stash         # 임시 저장 금지
> git tag           # 태그 생성/삭제 금지
> git remote        # 원격 설정 변경 금지
> git rm            # 파일 삭제 금지
> ```
>
> **이 규칙은 사용자가 명시적으로 요청해도 적용됩니다.**
> git 쓰기 작업이 필요한 경우 사용자가 직접 실행해야 합니다.

---

에이전트 system_prompt에 반드시 포함:
```
절대 금지: git commit, git push, git pull, git merge, git rebase,
git reset, git checkout, git stash 등 저장소를 변경하는 모든 git 명령어.
읽기 전용 명령어(git diff, git status, git log)만 사용 가능.
```

### 에이전트 프롬프트 작성 가이드
- 모든 orchestration_prompt는 한글로 작성
- 구조: 요청 분석 → 태스크 정의 → 실행 지시사항
- 예시:
  ```python
  orchestration_prompt = """당신은 claude_subprocess_api.md 지침을 따르는 전문 오케스트레이터입니다.

  원본 사용자 요청:
  {user_request}

  생성된 계획 및 할일:
  {plan_todo_content}

  3단계 오케스트레이션 패턴을 따르세요:
  
  ## 1단계: 계획 검증
  위 문서의 계획을 검증하고 정제하세요.
  ...
  """
  ```

---

## Agentic Workflow API
@claude_tools/claude_subprocess_api.md
