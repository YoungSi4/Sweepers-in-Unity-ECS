# cs_code_reviewer.py 사용 가이드 및 주의사항

## 기본 실행

```bash
# 기본 실행 (대화형 승인)
python claude_tools/cs_code_reviewer.py --target Assets/Scripts/TestSystem.cs

# 자동 승인 모드
python claude_tools/cs_code_reviewer.py --target Assets/Scripts/TestSystem.cs --auto-approve
```

---

## ⚠️ 주의사항

### 1. 파일 크기 제한

**문제**: 파일이 크거나 복잡하면 에이전트가 타임아웃될 수 있습니다.

| 에이전트 | 타임아웃 | 권장 파일 크기 |
|---------|--------|------------|
| **Planner** | 300초 | < 500줄 |
| **Reviewer** | 300초 | < 500줄 |
| **Coder** | 600초 | < 300줄 |

**해결 방법**:
- 큰 파일은 먼저 분할하세요
- 필요시 타임아웃을 증가시킬 수 있습니다 (cs_code_reviewer.py 수정)

```python
# 라인 131: Planner 타임아웃
planner_output = self._run_planner()  # timeout=300

# 라인 287: Reviewer 타임아웃  
reviewer_output = self._run_reviewer(planner_output, attempt)  # timeout=300

# 라인 328: Coder 타임아웃
output = self._run_subprocess_agent("coder", ..., timeout=600)  # timeout=600
```

---

### 2. Coder 코드 블록 형식 필수

**문제**: `returncode=143` 또는 `코드 블록을 찾을 수 없음` 에러

이는 Coder 출력이 올바른 형식을 따르지 않을 때 발생합니다.

**올바른 형식**:
```
## 리팩터링된 코드

```csharp
using System;
// ... 전체 코드
```

## 변경 사항 요약
```

**잘못된 형식** (에러 발생):
```
# 코드

```csharp
// 코드 내용
```

# 변경사항
```

**확인 사항**:
- ✓ `# 리팩터링된 코드` 섹션 직후에 코드 블록 필수
- ✓ 정확히 ` ```csharp` 로 시작 (공백 금지, 약자 금지)
- ✓ 정확히 ` ``` ` 로 종료
- ✓ 코드는 50자 이상 (검증 조건)
- ✓ C# 특성 포함 (`using`, `class`, `public`, `struct` 등)

---

### 3. Reviewer 최대 3회 재시도

**문제**: 3회 모두 실패하면 파이프라인 중단

```
>>> Reviewer 시도 1/3
>>> Reviewer 시도 2/3
>>> Reviewer 시도 3/3 ← 실패하면 여기서 종료
```

**Reviewer가 NEEDS_REVISION을 반복하는 이유**:
- Planner 계획이 부족한 완성도
- Planner 계획이 실현 불가능
- 명확한 Coder 지시가 없음

**해결 방법**:
- Planner 시스템 프롬프트 강화 (`.claude/agents/planner.md`)
- Planner 지시 재검토
- 파일 크기 감소 (더 간단한 코드만 분석)

---

### 4. 에이전트 출력 파싱 의존성

**Planner 출력**:
- 정확한 마크다운 구조 필수
- `## 리팩터링 계획` 섹션 필수
- `### [P1]` / `### [P2]` / `### [P3]` 형식 권장

**Reviewer 출력**:
- 정확히 `APPROVED` 또는 `NEEDS_REVISION` 포함 필수
- 평가 점수 형식이 명시되어야 함
- 최대 3회 재시도 후 `APPROVED` 없으면 실패

**Coder 출력**:
- 정확히 ` ```csharp ` + 코드 + ` ``` ` 필수
- 변경 사항 요약 권장

---

### 5. 동시 실행 불가

**문제**: 여러 파일을 동시에 분석하면 안 됩니다.

```bash
# ❌ 동시 실행 (리소스 충돌, 파일 덮어쓰기 위험)
python cs_code_reviewer.py --target File1.cs &
python cs_code_reviewer.py --target File2.cs &

# ✓ 순차 실행 (안전)
python cs_code_reviewer.py --target File1.cs
python cs_code_reviewer.py --target File2.cs
```

**이유**:
- 임시 디렉토리 (`claude_tools/.tmp/`) 경로 충돌
- 백업 파일 덮어쓰기 위험
- 에이전트 로그 섞임

---

### 6. Git 상태 확인

**사전 확인**:
```bash
cd "D:\Unity\Unity Project\Sweepers in ECS"
git status  # 커밋할 변경사항 없어야 함
```

**백업 파일 위치**:
```
Assets/Scripts/
├── TestSystem.cs         ← 수정된 파일
└── TestSystem.backup.cs  ← 원본 백업
```

**리뷰 보고서 위치**:
```
claude_tools/review_outputs/
└── 20260403_211106_TestSystem_review.md
```

---

### 7. 에러 로그 확인

**에러 발생 시 로그 위치**:
```
claude_tools/.agent_logs/
├── planner_20260403_211106.log
├── reviewer_20260403_211106.log
└── coder_20260403_211106.log
```

**로그 확인**:
```bash
cat "claude_tools/.agent_logs/coder_*.log"  # Coder 에러 확인
```

---

## 🔧 문제 해결

### "코드 블록을 찾을 수 없음"
1. Coder 로그 확인: `claude_tools/.agent_logs/coder_*.log`
2. Coder 지시 문제 가능성
3. coder.md 시스템 프롬프트 재검토

### "Coder 실행 실패 (returncode=143)"
1. 타임아웃 → 파일 크기 확인, 타임아웃 증가
2. 메모리 부족 → Claude CLI 재시작 필요
3. 시스템 신호 → Claude CLI 프로세스 상태 확인

### "Reviewer: 최대 재시도 횟수 도달"
1. Planner 계획 품질 검토
2. 계획이 구체적인지 확인 (변경 위치, 현재 상태, 변경 방향, 이유 모두 명시)
3. 단순한 파일부터 테스트

### "User Approval 1/2 거부"
1. `--auto-approve` 플래그 사용으로 자동 승인
2. 변경사항이 예상과 다르면 거부 후 파이프라인 중단 (정상)

---

## 📊 성공적인 실행 예시

```bash
$ cd "D:\Unity\Unity Project\Sweepers in ECS"
$ python claude_tools/cs_code_reviewer.py --target Assets/Scripts/TestSystem.cs --auto-approve

[INFO] 대상 파일: D:\Unity\...\Assets\Scripts\TestSystem.cs
[INFO] 프로젝트 루트: D:\Unity\...

================================================================================
[INFO] Stage 1: Planner (코드 분석 & 리팩터링 계획)
================================================================================
[✓] Planner 출력 저장: .../.tmp/20260403_211106_planner.md

================================================================================
[INFO] Stage 2: Reviewer Loop (최대 3회)
================================================================================
>>> Reviewer 시도 1/3
[✓] Reviewer 승인 완료 (시도 1)

[INFO] Stage 3: User Approval 1 (변경 예정사항 확인)
================================================================================
[INFO] [UA1] 자동 승인 모드 → 승인

[INFO] Stage 4: Coder (리팩터링 코드 구현)
================================================================================
[✓] Coder 출력 저장

[INFO] Stage 5: User Approval 2 (변경된 코드 최종 확인)
================================================================================
[INFO] [UA2] 자동 승인 모드 → 승인

[INFO] Stage 6: 파일 적용 (백업 + 쓰기 + 보고서)
================================================================================
[✓] 백업 저장: ...TestSystem.backup.cs
[✓] 파일 업데이트: ...TestSystem.cs
[✓] 최종 보고서: .../20260403_211106_TestSystem_review.md

[✓] ✅ 리팩터링 완료!
```

---

## 🛠️ 커스터마이징

### 타임아웃 조정 (큰 파일)

파일이 1000줄 이상인 경우:

```python
# cs_code_reviewer.py 라인 131, 287, 328 수정
planner_output = self._run_planner(timeout=600)      # 기본값 300 → 600
reviewer_output = self._run_reviewer(..., timeout=600) # 기본값 300 → 600
_run_subprocess_agent(..., timeout=1200)              # 기본값 600 → 1200 (Coder)
```

### 에이전트별 도구 권한 확인

```python
# cs_code_reviewer.py 라인 256 (_run_subprocess_agent 메서드)

# Planner, Reviewer: Read,Glob,Grep (기본값)
allowed_tools="Read,Glob,Grep"

# Coder: Read,Glob,Grep,Edit,Write (확인됨 라인 331)
allowed_tools="Read,Glob,Grep,Edit,Write"
```

---

## ✅ 체크리스트

실행 전 확인사항:

- [ ] 대상 파일이 존재하는가?
- [ ] 파일 크기가 500줄 이내인가?
- [ ] git 상태가 깨끗한가 (uncommitted changes 없음)?
- [ ] Claude CLI가 설치되어 있는가? (`claude --version`)
- [ ] 스토리지 여유가 있는가? (백업 + 임시 파일)
- [ ] 인터넷 연결이 안정적인가?

---

## 문의사항

문제가 발생하면:

1. 에러 로그 확인: `claude_tools/.agent_logs/`
2. 임시 파일 확인: `claude_tools/.tmp/` (Planner/Reviewer 출력)
3. 보고서 확인: `claude_tools/review_outputs/` (최종 분석 결과)

