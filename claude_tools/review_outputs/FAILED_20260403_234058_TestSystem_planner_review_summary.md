# Planner 재시도 실패 보고서

## 메타데이터
- **파일**: D:\Unity\Unity Project\Sweepers in ECS\Assets\Scripts\TestSystem.cs
- **생성 시각**: 2026-04-03T23:45:33.235962
- **상태**: Planner-Reviewer 루프 3회 연속 실패

## 최종 Planner 계획 (3회차)

## 코드 품질 분석

### 1. 네이밍 규칙
**현재 상태**: 매우 양호
- ✅ 클래스/구조체: `TestSystem`, `Speed`, `Active`, `Disabled` — PascalCase 준수
- ✅ 메서드: `OnCreate`, `OnUpdate` — PascalCase 준수
- ✅ private 필드: `_movementQuery` — 언더스코어 접두사 적용
- ✅ 상수: `BoostDistanceThreshold`, `SpeedBoostMultiplier` — PascalCase 준수
- ✅ 로컬 변수: `deltaTime`, `speedValue`, `distanceThisFrame` — camelCase 준수

**지적 사항**:
- 클래스명 `TestSystem`은 의도(움직임 처리)를 반영하지 못함 → `MoveSystem`이 더 명확 (git diff에서 이미 변경됨)

---

### 2. ECS/DOTS 패턴 준수
**현재 상태**: 부분적 개선 필요
- ✅ 컴포넌트: `IComponentData` struct 패턴 준수 (Speed, Active, Disabled)
- ✅ 시스템: `partial struct` + `ISystem` 인터페이스 구현
- ⚠️ **EntityQuery 사용**: 현재 코드는 **SystemAPI.Query를 사용하지 않음**
  - 실제 구현을 보니 이미 `_movementQuery` 필드와 EntityQuery 캐싱이 적용됨 (git diff 확인)
  - 그러나 `ToComponentDataArray()` 사용은 성능 고려가 필요함 (아래 참고)

---

### 3. Burst 컴파일 최적화
**현재 상태**: 양호
- ✅ `[BurstCompile]` 속성이 클래스와 메서드 레벨에 적용됨
- ✅ Managed 타입 사용 안 함 (Unity.Mathematics, LocalTransform 등 모두 Burst 호환)
- ⚠️ **성능 고려점**:
  - `ToComponentDataArray()` 호출은 **프레임마다 배열 할당**을 유발할 수 있음
  - NativeArray 반환이므로 GC 압력은 낮지만, 동적 할당 여전히 존재
  - `state.WorldUpdateAllocator` 사용은 맞지만, 더 효율적 패턴이 있을 수 있음

---

### 4. 메모리 안전성
**현재 상태**: 안전함
- ✅ EntityQuery 캐싱으로 매 프레임 쿼리 오버헤드 제거
- ✅ NativeArray는 WorldUpdateAllocator로 관리 (자동 정리)
- ✅ Null 참조 위험 없음 (ECS 구조 특성상)
- ✅ 컴포넌트 접근은 `RefRW`, `RefRO`로 안전하게 관리

---

### 5. 코드 복잡도
**현재 상태**: 우수
- ✅ `OnCreate`: 4줄 (간단한 초기화)
- ✅ `OnUpdate`: 20줄 (단일 책임, 선형 흐름)
- ✅ 중첩 깊이: 3단계 (foreach → if-else 조건부)
- ✅ 책임 분리: 이동 로직만 처리 (속도, 부스트 계산, Y 위치 업데이트)

---

### 6. 성능 특성
**현재 상태**: 양호하나 최적화 기회 존재
- ✅ EntityQuery 캐싱: O(1) 쿼리 비용
- ✅ 루프 내부: O(N) 복잡도 (N = 활성 엔티티)
- ⚠️ **`math.abs()` 호출**: 매 프레임 절댓값 계산 (Speed 검증 시 한 번만 하면 충분할 수도)
- ⚠️ **`ToComponentDataArray()` 패턴**: 버퍼 할당/복사 비용이 있을 수 있음
  - 대안: `SystemAPI.Query` + ForEach 구문 (더 효율적)

---

### 7. 문서화 및 주석
**현재 상태**: 매우 우수
- ✅ 클래스 레벨 XML 주석 (`<summary>`)
- ✅ 상수 설명 (BoostDistanceThreshold, SpeedBoostMultiplier)
- ✅ 필드 주석 (_movementQuery)
- ✅ 메서드 주석 (OnCreate, OnUpdate)
- ✅ 로직 설명 (속도값 절댓값 처리, 부스트 조건 등)

---

### 8. 안전성 및 에러 처리
**현재 상태**: 안전하나 방어 강화 가능
- ✅ Null 참조 불가능 (ECS 구조)
- ✅ Burst 호환 타입만 사용
- ⚠️ **Speed 값 검증 부족**: 음수 Speed가 들어오면?
  - `math.abs()`로 처리하지만, Authoring에서 유효성 검사 권장
- ⚠️ **BoostDistanceThreshold 검사**: 음수 threshold는 논리 오류 가능
  - 상수는 양수로 고정되어 있으므로 현재 안전

---

## 리팩터링 계획

### [P1] 클래스명 변경: TestSystem → MoveSystem
**위치**: 클래스 선언 (라인 11)
**현재 상태**: `public partial struct TestSystem : ISystem`
**변경 방향**: 클래스명을 시스템의 실제 기능(이동 처리)을 명확히 반영하는 이름으로 변경
**이유**: 
- 네이밍 규칙: 클래스명은 의도를 명확히 표현해야 함
- `TestSystem`은 테스트 목적임을 시사하나, 실제로는 게임 로직의 핵심 시스템
- 향후 코드 리뷰/유지보수에서 혼동 방지
**Coder 지시**: 
- 클래스명 `TestSystem` → `MoveSystem`으로 변경
- git diff에서 이미 변경됨 (현재 코드와 비교하면 변경 필요)

---

### [P1] 상수명 일관성: SpeedBoostThreshold → BoostDistanceThreshold
**위치**: 라인 14
**현재 상태**: `private const float BoostDistanceThreshold = 10.0f;`
**변경 방향**: 상수명이 이미 올바르게 적용됨 (git diff에 반영)
**이유**: 
- 이전명 `SpeedBoostThreshold`는 "속도의 부스트 임계값"이라 모호함
- `BoostDistanceThreshold`는 "부스트가 적용되는 거리 임계값"을 명확히 표현
- 코드 의도 명확화
**Coder 지시**: 
- 이미 git diff에서 변경됨 (상태 확인)
- 확정 필요 시 별도 처리

---

### [P2] EntityQuery 캐싱 적용 및 쿼리 패턴 최적화
**위치**: 라인 20, 26-35 (OnCreate), 44-46 (OnUpdate)
**현재 상태**: 
- `_movementQuery` 필드 선언됨
- `OnCreate`에서 EntityQuery 캐싱됨
- `OnUpdate`에서 `_movementQuery.ToComponentDataArray()` 사용
**변경 방향**: 
- EntityQuery 캐싱은 이미 적용됨 (git diff 반영됨)
- `ToComponentDataArray()` 패턴 검토 및 필요시 `SystemAPI.Query` 패턴으로 전환 검토
**이유**: 
- 매 프레임 배열 할당/복사 비용 고려
- `SystemAPI.Query` + ForEach가 더 효율적일 가능성
- Burst 호환성 및 성능 프로파일링 필요
**Coder 지시**: 
- git diff 적용 상태 확인
- 필요시 대안 패턴 성능 비교 (나중 최적화 단계)

---

### [P2] Speed 컴포넌트 유효성 검사 강화
**위치**: Speed 컴포넌트 (라인 69-73)
**현재 상태**: `public float Value;` (제약 없음)
**변경 방향**: 
- Authoring 단계에서 Speed 값이 음수가 아님을 검증
- 또는 런타임 방어 로직 추가 (BurstCompile 호환 방식)
**이유**: 
- `math.abs()`로 보정하고 있으나, 설계상 Speed는 항상 양수여야 함
- 잘못된 값 입력 시 논리 오류 방지
- 문서에도 "항상 양수 값으로 설정하세요"라고 명시되어 있음
**Coder 지시**: 
- Speed Authoring Baker에서 입력값 유효성 검사 추가
- 또는 컴포넌트 초기화 시 절댓값 강제 적용

---

### [P2] 상수값 설정 문서화 및 조정 기능 추가
**위치**: 라인 14, 17 (상수 정의)
**현재 상태**: 
- `BoostDistanceThreshold = 10.0f` (고정값)
- `SpeedBoostMultiplier = 2.0f` (고정값)
**변경 방향**: 
- 상수를 조정 가능한 구조로 변경 고려 (예: 게임 밸런싱)
- 또는 설정값으로 관리
**이유**: 
- 게임 밸런싱 상 부스트 거리/배수를 조정할 필요 가능성 높음
- 하드코딩된 상수는 유지보수성 저하
- 테스트/튜닝 단계에서 자주 변경됨
**Coder 지시**: 
- 현재는 상수로 충분하나, 향후 Config 구조체 도입 시 이전 계획
- 또는 별도 Config 컴포넌트(BakerAuthoring) 통합 고려

---

### [P3] 문서 표현 정정: WithNone → None 필터
**위치**: 라인 84 (Disabled 컴포넌트 주석)
**현재 상태**: `/// Active와 독립적으로 사용되며, Disabled가 우선합니다 (WithNone 필터).`
**변경 방향**: 주석 표현을 현재 구현(EntityQueryDesc)과 일치시켜 "None 필터"로 정정
**이유**: 
- 이전 코드는 `SystemAPI.Query().WithNone<Disabled>()` 패턴 사용
- 현재 코드는 `EntityQueryDesc` + `None = new ComponentType[]` 사용
- 문서와 구현의 일관성 유지
**Coder 지시**: 
- Disabled 컴포넌트 주석의 "(WithNone 필터)" → "(None 필터)"로 정정
- git diff에 이미 반영됨 (확정 필요)

---

### [P3] OnCreate 초기화 로직 보강
**위치**: 라인 26-34 (OnCreate 메서드)
**현재 상태**: EntityQuery 초기화만 수행
**변경 방향**: 
- 향후 시스템 초기화가 필요한 경우(예: 통계 초기화, 성능 프로파일러) 확장 가능하도록 구조화
**이유**: 
- 현재는 단순하지만, 복잡한 시스템으로 성장할 수 있음
- 주석에서 "향후 확장" 의도 명시됨
**Coder 지시**: 
- 현재 구현으로 충분하나, 코드 아키텍처상 주석 유지
- 필요시 별도 헬퍼 메서드로 분리 고려

---

## 요약

| 분류 | 상태 | 항목 수 |
|------|------|--------|
| **주요 개선 사항** | 7개 리팩터링 항목 | |
| **P1 (즉시 필요)** | 클래스명 변경, 상수명 정정 | 2개 |
| **P2 (중요)** | EntityQuery 최적화, 유효성 검사, 설정 구조화 | 3개 |
| **P3 (선택)** | 문서 정정, 초기화 보강 | 2개 |

### 핵심 개선점
1. **네이밍**: `TestSystem` → `MoveSystem` (의도 명확화)
2. **성능**: EntityQuery 캐싱 이미 적용됨 (git diff 반영)
3. **안전성**: Speed 유효성 검사 강화 권장
4. **문서**: 주석과 구현 일관성 정정
5. **유지보수성**: 밸런싱 상수 조정 구조 고려

### 변경 적용 상태
- **git diff 기준**: 대부분의 리팩터링이 이미 계획됨 (TestSystem → MoveSystem, EntityQuery 캐싱 등)
- **현재 코드(TestSystem.cs)**: 중간 상태로 보이며, git diff 적용 여부 확인 필요


---

## Reviewer 최종 평가 (3회차)

## 평가 결과

### 현재 회차
첫 번째 평가

### 항목별 점수

#### [P1] 클래스명 변경: TestSystem → MoveSystem
- 완성도: 4/10 
  - 변경 위치와 방향은 명시되었으나, **실제 코드(TestSystem.cs)를 보면 이미 `MoveSystem`으로 되어 있음** (라인 11)
  - 계획 문서가 git diff 기준과 현재 코드 간 상태 불일치를 명확히 구분하지 않음 → 혼동 야기
  
- 실현 가능성: 3/10
  - Coder가 이미 완료된 항목을 다시 실행하도록 지시하면 불필요한 작업 발생
  - "git diff에서 이미 변경됨 (현재 코드와 비교하면 변경 필요)" 표현이 모순적

- **종합 점수: 3.5/10**
- 피드백: **P1 항목 재검토 필요** — 현재 코드가 이미 MoveSystem이므로, 이 항목은 "완료" 상태로 표시하거나 제거할 것

---

#### [P1] 상수명 일관성: SpeedBoostThreshold → BoostDistanceThreshold
- 완성도: 5/10
  - 변경 방향은 명확하나, 실제 코드를 보면 이미 `BoostDistanceThreshold`로 적용됨 (라인 14)
  - 계획 문서가 "이미 git diff에 반영됨" 이라고만 했지, 현재 상태를 명확히 하지 않음

- 실현 가능성: 3/10
  - 이미 완료된 항목으로 보임 → Coder에게 불필요한 작업 지시
  - "확정 필요 시 별도 처리" 표현은 결정 기준 불명확

- **종합 점수: 4/10**
- 피드백: **상태 명확화 필요** — "현재 코드 기준 이미 적용됨 / 미적용" 중 하나로 명시

---

#### [P2] EntityQuery 캐싱 적용 및 쿼리 패턴 최적화
- 완성도: 6/10
  - 현재 상태 설명은 상세함 (라인 20, 26-35, 44-46)
  - 변경 방향이 모호함: "필요시 대안 패턴 성능 비교 (나중 최적화 단계)" → **지금 변경할 것인지 나중에 할 것인지 불명확**
  - `SystemAPI.Query` 패턴으로의 전환이 권고인지 필수인지 불분명

- 실현 가능성: 6/10
  - 구현 지시사항이 추상적: "필요시 대안 패턴 성능 비교"는 Coder 판단에 맡김
  - 현재 `ToComponentDataArray()` 패턴의 성능 영향도를 정량화하지 않음
  - 변경 범위가 명확하지 않음 (OnUpdate 메서드 전체 리팩터링인가?)

- **종합 점수: 6/10**
- 피드백: **결정 필요** — P2 항목: (1) "반드시 SystemAPI.Query로 변경" 또는 (2) "현재 패턴 유지, 성능 모니터링" 명시할 것

---

#### [P2] Speed 컴포넌트 유효성 검사 강화
- 완성도: 5/10
  - 변경 위치는 지시했으나 (라인 69-73, Authoring Baker), **Speed Authoring 코드가 제공되지 않음**
  - "Authoring 단계에서 검증" 또는 "런타임 방어 로직" 중 어느 방식을 택할지 불명확
  - 구현 수준 (어느 정도의 검증? 에러 처리는?) 미정

- 실현 가능성: 4/10
  - Authoring Baker 코드를 읽어야 하는데, TestSystem.cs에 Authoring이 없음 → 별도 파일 필요 (위치 불명확)
  - 음수 Speed를 거부할 것인가, 절댓값으로 강제할 것인가 → 선택 필요
  - Burst 호환성 고려 → 구현 난도 상향

- **종합 점수: 4.5/10**
- 피드백: **구현 범위 명확화 필수** — (1) Authoring 파일 경로 명시, (2) 음수 처리 방식 결정, (3) 에러 처리 레벨 정의

---

#### [P2] 상수값 설정 문서화 및 조정 기능 추가
- 완성도: 5/10
  - 변경 위치는 명확 (라인 14, 17)
  - 변경 방향이 "고려 사항"에 그침: "향후 Config 구조체 도입 시 이전 계획" → **현재는 하지 않는다는 뜻인가?**
  - 이 항목이 P2(중요)인 이유가 불명확

- 실현 가능성: 3/10
  - "현재는 상수로 충분" 이라고 하면서 왜 P2에 들어있는가?
  - "향후 Config 컴포넌트 도입" 은 이번 리팩터링 범위에 포함되나? 불명확
  - "별도 Config 컴포넌트(BakerAuthoring) 통합 고려" → 구현할 것인가? 미리 설계만 할 것인가?

- **종합 점수: 4/10**
- 피드백: **P2에 포함되어야 하는가 재검토** — 실제 코드 변경이 이번에 필요하다면 구체 지시 필요, 아니면 P3 또는 제외 권고

---

#### [P3] 문서 표현 정정: WithNone → None 필터
- 완성도: 8/10
  - 변경 위치 명확 (라인 84, Disabled 컴포넌트 주석)
  - 현재 상태 ← 변경 방향이 명확함
  - 변경 범위도 작고 명확 (주석 한 줄 수정)

- 실현 가능성: 8/10
  - Coder가 명확하게 이해 가능
  - 구현 난도 낮음 (텍스트 수정)
  - 부작용 없음

- **종합 점수: 8/10**
- 피드백: 잘 정의된 항목. Coder가 수행 가능함.

---

#### [P3] OnCreate 초기화 로직 보강
- 완성도: 4/10
  - "향후 시스템 초기화가 필요한 경우" 라고 하여 가정적임
  - "확장 가능하도록 구조화" 는 추상적 (구체적 변경점 없음)
  - "현재 구현으로 충분" 이라고 하면서 왜 항목에 포함되어 있는가?

- 실현 가능성: 3/10
  - 구체 지시사항 부족: "필요시 별도 헬퍼 메서드로 분리 고려" 는 Coder 판단에 맡김
  - OnCreate 메서드를 어떻게 변경할지 명확하지 않음
  - 현재 코드로도 충분하다면 변경 필요 없음 (낭비)

- **종합 점수: 3.5/10**
- 피드백: **이 항목 제외 권고** — 현재 코드가 충분하다고 했으므로, 실제 변경 지시가 있으면 P3로 유지, 아니면 제거

---

### 종합 평가

**평균 점수**: (3.5 + 4 + 6 + 4.5 + 4 + 8 + 3.5) / 7 = **4.8/10**

**최종 판정**: **NEEDS_REVISION**

---

## 재작업 필요 (8점 미만)

### Planner에게 지시

이 계획 문서는 **코드 분석 보고서** 형식으로, **실행 가능한 리팩터링 계획으로 부족**합니다.

#### 1. **상태 일관성 문제** (심각)

**현재 상황**:
- Planner 계획: "P1: 클래스명 변경 TestSystem → MoveSystem" 제시
- 실제 코드: 이미 `MoveSystem` 으로 적용됨 (라인 11)

**필수 수정**:
1. **git diff와 현재 코드 상태 명확히 분리**
   - "git diff 기준의 이전 코드" vs "현재 제공된 TestSystem.cs" 간 불일치 명시
   - P1 항목들이 이미 완료되었는지, 아직 미적용인지 결정
   - 불필요한 항목은 제거

2. **이미 완료된 항목 정리**
   - ✅ 클래스명: MoveSystem (완료)
   - ✅ 상수명: BoostDistanceThreshold (완료)
   - ✅ EntityQuery 캐싱: 적용됨 (완료)
   - ❓ 다른 항목들은 실제 변경이 필요한가?

---

#### 2. **선택사항 vs 필수사항 구분** (중요)

**현재 문제**:
- P2 항목: "필요시", "고려", "검토" 등 모호한 표현 → **Coder가 어느 것을 해야 하는지 불명확**
- P3 항목: "현재 구현으로 충분" 이라고 하면서 항목에 포함 → **모순**

**필수 수정**:
1. **각 항목을 "필수(Must)" 또는 "선택(Nice-to-Have)"으로 명확히 표시**
   ```
   예:
   - [P2] Speed 유효성 검사 → 【필수】 또는 【선택】 명시
   - [P2] 상수값 설정 도입 → 【선택 / 향후】로 제거 권고
   ```

2. **P3 항목 재검토**:
   - P3-1 (주석 정정): 필수적으로 유지 (명확)
   - P3-2 (OnCreate 보강): 현재 구현으로 충분하다면 **제거** 권고

---

#### 3. **구현 지시 구체화** (중요)

**P2: Speed 유효성 검사 강화**
- 현재: "Authoring Baker에서 입력값 유효성 검사 추가" (위치 불명확)
- 필수 수정:
  - Speed Authoring 코드 위치 명시 (예: `Assets/Scripts/Authoring/SpeedAuthoring.cs`)
  - 음수 처리 정책 결정: (1) 거부할 것 vs (2) 절댓값 강제
  - 에러 처리 레벨: (1) Assert / (2) Warning / (3) Clamp 중 선택

**P2: 상수값 설정 문서화**
- 현재: "향후 Config 구조체 도입" (현재는 X)
- 필수 수정: **이번 리팩터링에 포함할 것인가 아닌가 명확히 결정**
  - 포함: "Config 컴포넌트 파일명, 구조 명시"
  - 미포함: **항목 제거** (P2 → 불필요)

**P3: OnCreate 보강**
- 현재: "향후 확장" (현재는 변경 없음)
- 결정: **이 항목도 제거하거나 구체 지시 필요**

---

#### 4. **개선 체크리스트**

- [ ] git diff 기준 코드 vs 현재 코드 간 상태 명확히 정리
- [ ] P1 항목이 이미 완료되었으면 ✅ 표시하거나 제거
- [ ] 각 항목을 【필수】【선택】으로 분류
- [ ] P2-P3 항목의 구현 범위 구체화 (파일명, 메서드명, 변경 라인 등)
- [ ] "현재 구현으로 충분" 항목은 제거
- [ ] Speed Authoring 파일 위치 및 수정 방식 명시
- [ ] 음수 처리, 에러 처리 등 설계 결정 명시

---

## 최종 판정

**평균 점수**: 4.8/10
**현재 회차**: 첫 번째 평가 / 3회 제한

### 판정 결과
- **NEEDS_REVISION** 

Planner는 다음 항목을 **반드시** 수정하여 재제출해야 합니다:

1. **git diff 상태와 현재 코드 간 불일치 해결**
2. **P1 항목 (완료된 것으로 보임) 정리**
3. **P2-P3 항목의 필수/선택 구분 및 구체 지시**
4. **Speed Authoring 파일 경로 및 수정 방식 명시**

---


---

## 권장 사항

### 원인 분석
Planner 계획이 3회 연속 거부된 주요 이유:
- 각 항목의 변경 위치가 명확하지 않음
- 현재 상태 설명이 불충분함
- 변경 방향이 너무 추상적임
- Coder가 구현하기에 지시사항이 모호함

### 다음 단계
1. Planner 계획 수동 개선 (위의 "개선 필요 사항" 참고)
2. 다시 실행: `python cs_code_reviewer.py --target D:\Unity\Unity Project\Sweepers in ECS\Assets\Scripts\TestSystem.cs`
3. 또는 자동 리팩터링 포기 후 수동 검토

---

## 첨부: 원본 코드
```csharp
using Unity.Entities;
using Unity.Mathematics;
using Unity.Transforms;

/// <summary>
/// 이동 시스템 — Active 마크를 가진 엔티티의 위치를 Speed 컴포넌트에 따라 업데이트합니다.
/// 이동 거리가 임계값을 초과하면 부스트 배수를 적용합니다.
/// Disabled 마크가 있는 엔티티는 제외됩니다.
/// </summary>
[BurstCompile]
public partial struct MoveSystem : ISystem
{
    /// <summary>이동 거리가 이 값을 초과하면 부스트 배수가 적용됩니다.</summary>
    private const float BoostDistanceThreshold = 10.0f;

    /// <summary>부스트 조건 충족 시 이동 거리에 적용되는 배수입니다.</summary>
    private const float SpeedBoostMultiplier = 2.0f;

    /// <summary>Active이면서 Disabled가 아닌 엔티티의 이동 쿼리를 캐싱합니다.</summary>
    private EntityQuery _movementQuery;

    /// <summary>
    /// SystemState 초기화 — EntityQuery를 캐싱하여 매 프레임 쿼리 오버헤드를 감소시킵니다.
    /// </summary>
    [BurstCompile]
    public void OnCreate(ref SystemState state)
    {
        _movementQuery = state.GetEntityQuery(
            new EntityQueryDesc()
            {
                All = new ComponentType[] { typeof(LocalTransform), typeof(Speed), typeof(Active) },
                None = new ComponentType[] { typeof(Disabled) }
            });
    }

    /// <summary>
    /// 매 프레임 업데이트 — 캐싱된 쿼리를 통해 Active이면서 Disabled가 아닌 엔티티의 Y 위치를 업데이트합니다.
    /// </summary>
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        float deltaTime = SystemAPI.Time.DeltaTime;

        foreach (var (transform, speed) in
            _movementQuery.ToEntityQuery(state)
                .ToComponentDataArray<(RefRW<LocalTransform>, RefRO<Speed>)>(state.WorldUpdateAllocator))
        {
            // 속도값을 절댓값으로 처리 (항상 양수 이동 거리 계산)
            float speedValue = math.abs(speed.ValueRO.Value);

            // 프레임당 이동 거리 계산
            float distanceThisFrame = speedValue * deltaTime;

            // 부스트 조건 판정 및 최종 이동 거리 계산
            float finalMovementDistance = (distanceThisFrame > BoostDistanceThreshold)
                ? distanceThisFrame * SpeedBoostMultiplier
                : distanceThisFrame;

            // 위치 업데이트
            transform.ValueRW.Position.y += finalMovementDistance;
        }
    }
}

/// <summary>
/// 속도 컴포넌트 — 엔티티의 이동 속도를 나타냅니다.
/// 항상 양수 값을 가지며, 절댓값으로 처리됩니다.
/// </summary>
public struct Speed : IComponentData
{
    /// <summary>매 초 단위로 이동할 거리입니다. 항상 양수 값으로 설정하세요.</summary>
    public float Value;
}

/// <summary>
/// Active 마커 컴포넌트 — 이 마크를 가진 엔티티는 이동 시스템의 영향을 받습니다.
/// </summary>
public struct Active : IComponentData
{
}

/// <summary>
/// Disabled 마커 컴포넌트 — 이 마크를 가진 엔티티는 이동 시스템에서 제외됩니다.
/// Active와 독립적으로 사용되며, Disabled가 우선합니다 (None 필터).
/// </summary>
public struct Disabled : IComponentData
{
}
```
