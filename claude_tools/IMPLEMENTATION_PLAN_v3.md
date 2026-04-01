# Claude Tools — Improved Implementation Plan v3

**Status**: DO Phase — Consolidated Review Feedback (v2 + cs_code_reviewer.py)  
**Date**: 2026-04-01  
**Previous Plan**: IMPLEMENTATION_PLAN_v2.md  
**Effort Estimate**: ~35 minutes  
**Risk Level**: LOW

---

## 목표

v2 플랜의 4개 이슈를 유지하면서, 신규 추가된 `cs_code_reviewer.py`의 이슈까지 통합한 완성 계획.

---

## 이슈 현황 (전체 3개 파일)

| # | 이슈 | 파일 | 위치 | 심각도 |
|---|------|------|------|--------|
| 1 | `shell=True` in subprocess | request_orchestrator.py | 158 | CRITICAL |
| 2 | `shell=True` in subprocess | cs_code_reviewer.py | 136 | CRITICAL |
| 3 | No state management / caching | request_to_plan_todo.py | SafeOrchestrator | HIGH |
| 4 | Prompt redundancy (`{user_request}` 2회) | request_to_plan_todo.py | ~258 | MEDIUM |
| 5 | Coder 결과가 소스 파일에 미적용 | cs_code_reviewer.py | review_file() | HIGH |
| 6 | Agent 페르소나 TODO 미완성 | cs_code_reviewer.py | 174, 222, 271 | LOW |

---

## 구현 태스크 (우선순위 순)

---

### Phase 1: Security — `shell=True` 제거 (5분)

**1-A. request_orchestrator.py:158**

```python
# Before (DANGEROUS)
result = subprocess.run(
    ["claude", "-p", orchestration_prompt, "--model", "claude-haiku-4-5-20251001"],
    capture_output=True, text=True,
    encoding='utf-8', errors='replace',
    timeout=300,
    shell=True,   # ← 제거
    env=env
)

# After
result = subprocess.run(
    ["claude", "-p", orchestration_prompt, "--model", "claude-haiku-4-5-20251001"],
    capture_output=True, text=True,
    encoding='utf-8', errors='replace',
    timeout=300,
    env=env
)
```

**1-B. cs_code_reviewer.py:136**

```python
# Before (DANGEROUS)
result = subprocess.run(
    cmd,
    capture_output=True, text=True,
    encoding='utf-8', errors='replace',
    timeout=180,
    shell=True,   # ← 제거
    env=env
)

# After
result = subprocess.run(
    cmd,
    capture_output=True, text=True,
    encoding='utf-8', errors='replace',
    timeout=180,
    env=env
)
```

**검증**: 두 파일 모두 `grep -n "shell=True"` → 결과 없어야 함

---

### Phase 2: Reliability — State Management + Caching (15분)

**위치**: `request_to_plan_todo.py` — `SafeOrchestrator` 클래스에 메서드 추가

#### 2-A. Import 추가 (파일 상단)
```python
import hashlib
import json
from typing import Optional
```

#### 2-B. 메서드 추가 (`__init__` 직후)
```python
def get_request_hash(self, user_request: str) -> str:
    return hashlib.sha256(user_request.encode()).hexdigest()[:12]

def load_state(self, request_hash: str) -> dict:
    state_file = Path(f".orchestrator_state/{request_hash}.state.json")
    if state_file.exists():
        return json.loads(state_file.read_text(encoding='utf-8'))
    return {
        "planning_agent": "pending",
        "review_agent": "pending",
        "revised_planning_agent": "pending",
        "todo_generation_agent": "pending",
        "keyword_extraction_agent": "pending",
        "output_file": None
    }

def save_state(self, request_hash: str, phase: str, status: str, output_file: str = None):
    state_file = Path(f".orchestrator_state/{request_hash}.state.json")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state = self.load_state(request_hash)
    state[phase] = status
    if output_file:
        state["output_file"] = output_file
    tmp = f"{state_file}.tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, state_file)

def load_cached_output(self, request_hash: str) -> Optional[str]:
    state_file = Path(f".orchestrator_state/{request_hash}.state.json")
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding='utf-8'))
        out = state.get("output_file")
        if out and Path(out).exists():
            return out
    return None
```

#### 2-C. `run_workflow()` 시작 부분에 캐시 체크 추가
```python
def run_workflow(self, user_request: str) -> str:
    request_hash = self.get_request_hash(user_request)
    cached = self.load_cached_output(request_hash)
    if cached:
        print(f"[캐시 히트] 기존 결과 재사용: {cached}")
        return cached

    # ... 기존 5-agent 파이프라인 코드 유지 ...
    
    # 각 에이전트 완료 후 상태 저장 (5곳에 추가):
    # self.save_state(request_hash, "planning_agent", "completed")
    # self.save_state(request_hash, "review_agent", "completed")
    # self.save_state(request_hash, "revised_planning_agent", "completed")
    # self.save_state(request_hash, "todo_generation_agent", "completed")
    # self.save_state(request_hash, "keyword_extraction_agent", "completed", output_file)
```

**검증**: 동일 요청 2회 실행 → 2번째에 "[캐시 히트]" 출력

---

### Phase 3: Code Clarity — Prompt 중복 제거 (5분)

**위치**: `request_to_plan_todo.py` ~line 258 (`revised_prompt`)

현재 `revised_prompt`는 구조가 명확하고 `{user_request}` 한 번만 포함됨 (ORIGINAL REQUEST: 블록).  
`{user_request}` 중복 여부를 grep으로 먼저 확인:

```bash
grep -n "user_request" claude_tools/request_to_plan_todo.py
```

실제로 중복 확인 시 아래 구조로 정리:
```python
revised_prompt = f"""Create an improved implementation plan based on review feedback.

REQUIREMENT:
{user_request}

ORIGINAL PLAN:
{planning_output}

REVIEW FEEDBACK:
{review_output}

..."""
```

**검증**: `grep -c "user_request" revised_prompt` → 1 이어야 함

---

### Phase 4: cs_code_reviewer — Coder 결과 적용 (10분)

**현재 동작**: Coder agent의 출력(리팩터링된 코드)이 마크다운 보고서에만 저장됨.  
실제 `.cs` 파일은 변경되지 않음 → 사용자가 수동으로 코드를 복사해야 함.

**두 가지 선택지** (사용자 확인 필요):

**Option A — 현재 유지 (Dry Run 모드)**: 보고서만 생성, 파일 미수정  
→ `review_file()` 하단에 안내 메시지 추가:
```python
print(f"\n[안내] 수정된 코드는 보고서를 확인하세요: {output_file}")
print(f"       자동 적용을 원하면 --apply 플래그를 사용하세요.")
```

**Option B — 자동 적용 (`--apply` 플래그)**: Coder 출력에서 코드블록 추출 후 원본 파일 덮어쓰기  
```python
def apply_coder_result(self, filepath: str, coder_output: str):
    """Coder 결과에서 csharp 코드블록 추출 후 파일에 적용"""
    import re
    match = re.search(r'```csharp\n(.*?)```', coder_output, re.DOTALL)
    if not match:
        print("[경고] 코드블록을 찾을 수 없음 — 파일 미수정")
        return False
    refined_code = match.group(1)
    full_path = self.project_root / filepath
    self.write_atomic(str(full_path), refined_code)
    print(f"[적용됨] {filepath}")
    return True
```

**권장**: Option B + `--apply` 플래그로 선택적 활성화 (기본값: dry run)

---

### Phase 5: cs_code_reviewer — 페르소나 완성 (선택, 5분)

주석에 "TODO - 추후 구체화"로 남겨진 3개 Agent 페르소나를 구체화.

| Agent | 현재 | 개선 포인트 |
|-------|------|------------|
| Planner | 일반적 설명 | CLAUDE.md 컨벤션 명시 (ISystem, BurstCompile, NativeContainer) |
| Reviewer | 일반적 설명 | ECS 성능 패턴 체크리스트 추가 |
| Coder | 일반적 설명 | Burst-safe 타입만 사용 제약 명시 |

---

## 테스트 전략

### 단위 테스트 (`claude_tools/test_improvements.py`)

```python
import unittest
from pathlib import Path
import json
from request_to_plan_todo import SafeOrchestrator

class TestImprovedOrchestrator(unittest.TestCase):

    def setUp(self):
        self.orch = SafeOrchestrator(str(Path.cwd()))

    def test_hash_deterministic(self):
        req = "Add turn system"
        self.assertEqual(self.orch.get_request_hash(req), self.orch.get_request_hash(req))

    def test_hash_unique(self):
        h1 = self.orch.get_request_hash("Request A")
        h2 = self.orch.get_request_hash("Request B")
        self.assertNotEqual(h1, h2)

    def test_state_roundtrip(self):
        h = "teststate123"
        self.orch.save_state(h, "planning_agent", "completed")
        state = self.orch.load_state(h)
        self.assertEqual(state["planning_agent"], "completed")

    def test_state_json_valid(self):
        h = "jsontest456"
        self.orch.save_state(h, "test_phase", "completed")
        data = json.loads(Path(f".orchestrator_state/{h}.state.json").read_text())
        self.assertIn("test_phase", data)

    def test_no_shell_true_orchestrator(self):
        """request_orchestrator.py에 shell=True 없음을 검증"""
        content = Path("request_orchestrator.py").read_text()
        self.assertNotIn("shell=True", content)

    def test_no_shell_true_reviewer(self):
        """cs_code_reviewer.py에 shell=True 없음을 검증"""
        content = Path("cs_code_reviewer.py").read_text()
        self.assertNotIn("shell=True", content)

if __name__ == '__main__':
    unittest.main()
```

**실행**:
```bash
cd "D:\Unity\Unity Project\Sweepers in ECS\claude_tools"
python -m pytest test_improvements.py -v
```

---

## 검증 체크리스트

**Phase 1 (Security)**
- [ ] `request_orchestrator.py`에 `shell=True` 없음
- [ ] `cs_code_reviewer.py`에 `shell=True` 없음
- [ ] 두 파일 모두 정상 실행됨

**Phase 2 (Reliability)**
- [ ] `.orchestrator_state/` 디렉토리 생성됨
- [ ] 동일 요청 2회 실행 → 2번째에 캐시 히트
- [ ] state JSON 파일의 모든 필드가 유효함

**Phase 3 (Clarity)**
- [ ] `revised_prompt`에 `user_request` 1회만 등장

**Phase 4 (Coder Apply)**
- [ ] `--apply` 없이 실행 → 보고서만 생성
- [ ] `--apply` 포함 시 → 원본 `.cs` 파일 수정됨
- [ ] 코드블록 없는 출력 → 안전하게 스킵

---

## 구현 로드맵

```
Phase 1 (5분)  → shell=True 제거 (2개 파일)
Phase 2 (15분) → state management + caching (request_to_plan_todo.py)
Phase 3 (5분)  → prompt 중복 제거 확인 및 정리
Phase 4 (10분) → cs_code_reviewer.py coder apply 기능 추가
Phase 5 (5분)  → [선택] 페르소나 구체화
테스트 (5분)   → pytest 6개 테스트 실행

총계: ~35분 (Phase 5 선택 시 40분)
```

---

## 위험 평가

| 위험 | 확률 | 완화 방안 |
|------|------|-----------|
| 기존 워크플로우 중단 | 매우 낮음 | 모두 additive 변경; state는 선택적 fallback |
| coder apply 잘못된 파일 덮어쓰기 | 낮음 | `--apply` 플래그 명시 필요; 자동 적용 금지 |
| 캐시 stale 문제 | 매우 낮음 | 요청 해시는 불변; 파일 변경 없음 |

**전체 위험도**: LOW

---

## Definition of Done

1. ✅ `shell=True` 3개 파일에서 모두 제거 (request_orchestrator, cs_code_reviewer, request_to_plan_todo 해당 시)
2. ✅ State management 메서드 4개 추가 (get_request_hash, load_state, save_state, load_cached_output)
3. ✅ run_workflow() 시작부에 캐시 체크 추가
4. ✅ revised_prompt의 user_request 중복 없음
5. ✅ cs_code_reviewer.py에 `--apply` 플래그 지원
6. ✅ pytest 6개 테스트 통과
7. ✅ 기존 기능 회귀 없음

---

**Plan Version**: 3  
**Created**: 2026-04-01  
**Supersedes**: IMPLEMENTATION_PLAN_v2.md  
**Status**: Ready for Implementation
