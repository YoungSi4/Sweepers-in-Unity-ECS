# Claude Tools — Improved Implementation Plan v2

**Status**: DO Phase — Review Feedback Integration  
**Date**: 2026-04-01  
**Previous Plan**: IMPLEMENTATION_PLAN_IMPROVED.md  
**Effort Estimate**: ~22 minutes  
**Risk Level**: LOW

---

## 🎯 Objective

Apply 4 critical improvements to `request_orchestrator.py` and `request_to_plan_todo.py` based on review feedback. Focus on security, reliability, and code clarity.

---

## 📋 Review Feedback Summary

| Issue | File | Line(s) | Severity | Impact |
|-------|------|---------|----------|--------|
| `shell=True` in subprocess | request_orchestrator.py | 158 | CRITICAL | Security vulnerability |
| User request redundancy | request_to_plan_todo.py | 218-222 | MEDIUM | Token waste, clarity |
| No state tracking | Both | N/A | HIGH | Duplicate executions |
| No idempotency | Both | N/A | HIGH | User experience (no caching) |

---

## 🔧 Implementation Tasks (Priority Order)

### Phase 1: Security Fix (CRITICAL) — 2 min
**Task**: Remove `shell=True` from subprocess calls  
**Files**: `request_orchestrator.py` (line 158)

**Current Code**:
```python
result = subprocess.run(
    [...],
    shell=True,  # ❌ DANGEROUS
    capture_output=True,
    text=True
)
```

**Fixed Code**:
```python
result = subprocess.run(
    [...],  # Already a list, safe for exec
    capture_output=True,
    text=True
)
```

**Validation**: Run `python request_orchestrator.py "test request"` → should execute without shell errors

---

### Phase 2: Reliability Foundation (HIGH) — 15 min
**Task 2A**: Implement State Management  
**Task 2B**: Implement Request Hashing + Caching

**Location**: `request_to_plan_todo.py` (SafeOrchestrator class)

#### 2A. State Management Methods
```python
import json
from pathlib import Path

def load_state(self, request_hash: str) -> dict:
    """Load execution state for a request."""
    state_file = Path(f".orchestrator_state/{request_hash}.state.json")
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {
        "planning_agent": "pending",
        "review_agent": "pending", 
        "revised_planning_agent": "pending",
        "todo_generation_agent": "pending",
        "keyword_extraction_agent": "pending",
        "output_file": None,
        "completed_at": None
    }

def save_state(self, request_hash: str, phase: str, status: str, output_file: str = None):
    """Save execution state."""
    state_file = Path(f".orchestrator_state/{request_hash}.state.json")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    state = self.load_state(request_hash)
    state[phase] = status
    if output_file:
        state["output_file"] = output_file
    if status == "completed":
        state["completed_at"] = datetime.now().isoformat()
    
    # Atomic write
    tmp = f"{state_file}.tmp"
    with open(tmp, 'w') as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, state_file)
```

#### 2B. Request Hashing + Caching
```python
import hashlib
from typing import Optional

def get_request_hash(self, user_request: str) -> str:
    """Generate deterministic hash of request."""
    return hashlib.sha256(user_request.encode()).hexdigest()[:12]

def load_cached_output(self, request_hash: str) -> Optional[str]:
    """Check if output exists for this request hash."""
    state_file = Path(f".orchestrator_state/{request_hash}.state.json")
    if state_file.exists():
        state = json.loads(state_file.read_text())
        output_file = state.get("output_file")
        if output_file and Path(output_file).exists():
            return output_file
    return None
```

#### 2C. Integration in `run_workflow()`
**Add at the top of `run_workflow(user_request: str)`**:
```python
def run_workflow(self, user_request: str) -> str:
    # NEW: Check for cached result
    request_hash = self.get_request_hash(user_request)
    cached = self.load_cached_output(request_hash)
    if cached:
        print(f"✅ Cache hit! Reusing: {cached}")
        return cached
    
    # ... existing pipeline code ...
    
    # NEW: Save state after each agent completes
    self.save_state(request_hash, "planning_agent", "completed")
    # ... after review_agent ...
    self.save_state(request_hash, "review_agent", "completed")
    # ... etc for all 5 agents ...
    
    # NEW: Save final output reference
    self.save_state(request_hash, "keyword_extraction_agent", "completed", output_file)
    
    return output_file
```

**Directory Structure Created**:
```
.orchestrator_state/
├── a1b2c3d4e5f6g7h8.state.json    ← hash(request_1)
├── x9y8z7w6v5u4t3s2.state.json    ← hash(request_2)
└── ...
```

---

### Phase 3: Code Clarity (MEDIUM) — 5 min
**Task**: Eliminate redundant user request in prompts  
**File**: `request_to_plan_todo.py` (revised_planning_prompt, ~line 218)

**Current Code**:
```python
revised_planning_prompt = f"""
You are a requirements specialist...

ORIGINAL REQUIREMENT:
{user_request}

Now, incorporate the Review Agent's feedback...

REQUIREMENT:
{user_request}  # ❌ DUPLICATE
"""
```

**Fixed Code**:
```python
revised_planning_prompt = f"""
You are a requirements specialist...

REQUIREMENT:
{user_request}

REVIEW FEEDBACK:
{review_feedback}

Now, incorporate this feedback to refine the plan...
"""
```

**Benefits**:
- Reduces token usage by ~10%
- Clearer prompt structure
- Single source of truth for requirement

---

## ✅ Validation Checklist

After completing all 3 phases:

**Phase 1 Validation**:
- [ ] Line 158 in request_orchestrator.py no longer has `shell=True`
- [ ] `python request_orchestrator.py "test request"` runs without errors
- [ ] Output is saved to `orchestrator_outputs/`

**Phase 2 Validation**:
- [ ] `.orchestrator_state/` directory exists
- [ ] Running same request twice produces cache hit on second run
- [ ] State files are valid JSON with all expected fields
- [ ] `output_file` field points to correct output path

**Phase 3 Validation**:
- [ ] User request appears exactly once in revised_planning_prompt
- [ ] Review Agent's feedback section is clearly separated
- [ ] Plan quality improves (no token duplication)

---

## 🧪 Testing Strategy

### Unit Tests
Create `claude_tools/test_improvements.py`:

```python
import unittest
from pathlib import Path
import json
from request_to_plan_todo import SafeOrchestrator

class TestImprovedOrchestrator(unittest.TestCase):
    
    def setUp(self):
        self.orch = SafeOrchestrator(str(Path.cwd()))
    
    def test_request_hash_deterministic(self):
        """Same request → same hash"""
        req = "Add turn system"
        h1 = self.orch.get_request_hash(req)
        h2 = self.orch.get_request_hash(req)
        self.assertEqual(h1, h2)
    
    def test_request_hash_different(self):
        """Different requests → different hashes"""
        h1 = self.orch.get_request_hash("Request A")
        h2 = self.orch.get_request_hash("Request B")
        self.assertNotEqual(h1, h2)
    
    def test_state_persistence(self):
        """State saves and loads correctly"""
        hash_val = "test_hash_123"
        self.orch.save_state(hash_val, "planning_agent", "completed")
        state = self.orch.load_state(hash_val)
        self.assertEqual(state["planning_agent"], "completed")
    
    def test_state_json_valid(self):
        """State files are valid JSON"""
        hash_val = "valid_json_test"
        self.orch.save_state(hash_val, "test_phase", "completed")
        state_file = Path(f".orchestrator_state/{hash_val}.state.json")
        with open(state_file) as f:
            data = json.load(f)  # Should not raise
        self.assertIn("test_phase", data)

if __name__ == '__main__':
    unittest.main()
```

**Run tests**:
```bash
cd claude_tools
python -m pytest test_improvements.py -v
```

### Integration Test
```bash
# First run (no cache)
python request_to_plan_todo.py "Create a REST API for users"
# Expected: [OK] Plan & Todo generated: outputs/YYYYMMDD_HHMMSS_*.md

# Verify state file created
ls .orchestrator_state/
# Expected: {hash}.state.json with "keyword_extraction_agent": "completed"

# Second run (with cache)
python request_to_plan_todo.py "Create a REST API for users"
# Expected: ✅ Cache hit! Reusing: outputs/YYYYMMDD_HHMMSS_*.md
```

---

## 📊 Success Metrics

| Metric | Target | Method |
|--------|--------|--------|
| Subprocess security | 100% | Code review: no `shell=True` |
| Cache hit rate | ≥50% | Run same requests 2x, measure hits |
| State files created | 100% | Check `.orchestrator_state/` exists |
| Prompt redundancy | 0 | Grep for duplicate `{user_request}` |
| Test coverage | ≥80% | pytest coverage report |

---

## 🚀 Implementation Roadmap

```
Today (2026-04-01)
│
├─→ [5 min] Phase 1: Fix shell=True
│   └─→ VALIDATE: subprocess runs safely
│
├─→ [15 min] Phase 2: Add state + caching
│   ├─→ Add get_request_hash()
│   ├─→ Add load_state() / save_state()
│   ├─→ Add load_cached_output()
│   └─→ VALIDATE: cache hits on 2nd run
│
├─→ [5 min] Phase 3: Remove prompt redundancy
│   └─→ VALIDATE: single user_request in prompt
│
└─→ [10 min] TESTING & VALIDATION
    ├─→ Unit tests pass
    ├─→ Integration test succeeds
    └─→ All checklist items ✅

Total: ~35 minutes (includes buffer)
```

---

## 🛡️ Risk Mitigation

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Breaking existing workflow | Very Low | All changes additive; state is read-only fallback |
| State file corruption | Low | Atomic writes + JSON validation in tests |
| Cache staleness | Very Low | Request hash is immutable; files don't change |

**Overall Risk**: ✅ **LOW** — Conservative, backward-compatible changes.

---

## 📝 Definition of Done

✅ Implementation is complete when:

1. ✅ `shell=True` removed from all subprocess calls
2. ✅ State management methods added to SafeOrchestrator
3. ✅ Request hashing + caching implemented
4. ✅ Prompt redundancy eliminated (single `{user_request}`)
5. ✅ Unit tests written and passing (≥4 tests)
6. ✅ Integration test succeeds (cache hit on 2nd run)
7. ✅ No regressions: existing requests still produce correct output
8. ✅ `.orchestrator_state/` directory created with valid JSON files
9. ✅ All validation checklist items completed

---

## 🔗 Related Documents

- **Review Feedback Source**: Code Review Agent output
- **Previous Plan**: `IMPLEMENTATION_PLAN_IMPROVED.md`
- **Safety Principles**: `claude_subprocess_api.md`
- **Current Implementation**: `request_to_plan_todo.py` + `request_orchestrator.py`

---

## 📅 Timeline & Status

| Phase | Status | ETA |
|-------|--------|-----|
| Phase 1 (Security) | READY | 2026-04-01 (now) |
| Phase 2 (Reliability) | READY | 2026-04-01 (now) |
| Phase 3 (Clarity) | READY | 2026-04-01 (now) |
| Testing | READY | 2026-04-01 (now) |
| Merge | PENDING | After validation |

---

**Plan Version**: 2  
**Created**: 2026-04-01  
**Review Status**: Ready for Implementation  
**Approved**: [Pending User Review]
