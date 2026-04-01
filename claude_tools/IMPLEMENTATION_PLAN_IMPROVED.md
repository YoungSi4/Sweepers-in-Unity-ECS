# Improved Implementation Plan — claude_tools

**Based on Review Feedback**  
**Date**: 2026-04-01  
**Feature**: claude_tools (Agentic Orchestrator)  
**Phase**: DO → Refined Implementation  
**Priority**: High (safety & robustness)

---

## Executive Summary

The Review Agent identified 4 key improvements needed to the `request_to_plan_todo.py` implementation:
1. **Subprocess Safety** — Remove `shell=True` parameter (2 min)
2. **Prompt Clarity** — Eliminate redundant user request duplication (5 min)
3. **State Management** — Track execution state to prevent re-runs (10 min)
4. **Idempotency** — Cache outputs by request hash (5 min)

**Total Effort**: ~22 minutes  
**Risk Level**: Low (fixes + enhancements, no breaking changes)  
**Testing Strategy**: Unit tests + integration test with demo

---

## Implementation Tasks (Ordered by Effort)

### Task 1: Fix Subprocess Safety Issue ⚠️ CRITICAL
**File**: `claude_tools/request_to_plan_todo.py` (Line 93)  
**Effort**: 2 minutes  
**Priority**: CRITICAL (security)

#### Issue
```python
# ❌ UNSAFE (current)
result = subprocess.run(cmd_string, shell=True, capture_output=True, text=True)
```
When `shell=True` is used, the subprocess module spawns a shell process, which is dangerous with untrusted input (even though list args are used, the principle is violated).

#### Solution
```python
# ✅ SAFE (proposed)
result = subprocess.run(cmd, capture_output=True, text=True)  # Remove shell=True
```

#### Validation
- [ ] Verify `cmd` variable is a list (not a string)
- [ ] Test basic agent execution works
- [ ] Confirm no shell metacharacters are interpreted

---

### Task 2: Eliminate Prompt Redundancy
**File**: `claude_tools/request_to_plan_todo.py` (Lines 218-222)  
**Effort**: 5 minutes  
**Priority**: MEDIUM (clarity)

#### Issue
The user request appears **twice** in the revised_planning_prompt:
```python
# ❌ REDUNDANT (current)
revised_planning_prompt = f"""
You are a requirements specialist...

ORIGINAL REQUIREMENT:
{user_request}

Now, incorporate the Review Agent's feedback...

REQUIREMENT:
{user_request}
"""
```

#### Solution
Consolidate into single REQUIREMENT section:
```python
# ✅ IMPROVED (proposed)
revised_planning_prompt = f"""
You are a requirements specialist...

REQUIREMENT:
{user_request}

REVIEW FEEDBACK:
{review_feedback}

Now, incorporate this feedback...
"""
```

#### Benefits
- Reduces token consumption in Claude API calls
- Clearer prompt structure for the agent
- Easier to maintain and extend

---

### Task 3: Implement State Management 🔄
**File**: `claude_tools/request_to_plan_todo.py`  
**Effort**: 10 minutes  
**Priority**: HIGH (reliability)

#### Issue
No tracking to prevent duplicate agent runs. Running the same request multiple times will re-execute all 5 agents unnecessarily.

#### Solution
Add two methods to the orchestrator class:

```python
def load_state(self, request_hash: str) -> dict:
    """Load execution state for a given request."""
    state_file = Path(f".orchestrator_state/{request_hash}.state.json")
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {
        "planning": "pending",
        "review": "pending",
        "revised_planning": "pending",
        "todo": "pending",
        "keyword": "pending",
        "output_file": None
    }

def save_state(self, request_hash: str, phase: str, status: str, output_file: str = None):
    """Save execution state for a given request."""
    state_file = Path(f".orchestrator_state/{request_hash}.state.json")
    state_file.parent.mkdir(exist_ok=True)
    state = self.load_state(request_hash)
    state[phase] = status
    if output_file:
        state["output_file"] = output_file
    state_file.write_text(json.dumps(state, indent=2))
```

#### Integration Points
1. In `run_workflow()`, check state at the beginning:
```python
def run_workflow(self, user_request: str) -> str:
    request_hash = self.get_request_hash(user_request)
    state = self.load_state(request_hash)
    
    if state.get("keyword") == "completed":
        cached_output = state.get("output_file")
        print(f"✅ Using cached output: {cached_output}")
        return cached_output
```

2. After each agent runs successfully:
```python
self.save_state(request_hash, "planning", "completed")
self.save_state(request_hash, "review", "completed")
# ... etc
```

#### Directory Structure
```
.orchestrator_state/
├── a1b2c3d4e5f6g7h8_request_hash.state.json
├── x9y8z7w6v5u4t3s2.state.json
└── ...
```

---

### Task 4: Implement Idempotency via Request Hashing 🔐
**File**: `claude_tools/request_to_plan_todo.py`  
**Effort**: 5 minutes  
**Priority**: HIGH (user experience)

#### Issue
Same user request run twice produces two separate output files. No mechanism to detect and reuse previously computed results.

#### Solution
Add request hashing and caching:

```python
import hashlib

def get_request_hash(self, user_request: str) -> str:
    """Generate a deterministic hash of the user request."""
    return hashlib.sha256(user_request.encode()).hexdigest()[:16]

def load_cached_output(self, request_hash: str) -> Optional[str]:
    """Load a previously generated output file for this request."""
    state_file = Path(f".orchestrator_state/{request_hash}.state.json")
    if state_file.exists():
        state = json.loads(state_file.read_text())
        output_file = state.get("output_file")
        if output_file and Path(output_file).exists():
            return output_file
    return None
```

#### Integration
```python
def run_workflow(self, user_request: str) -> str:
    request_hash = self.get_request_hash(user_request)
    
    # Check for cached result
    cached = self.load_cached_output(request_hash)
    if cached:
        print(f"✅ Cache hit! Using {cached}")
        return cached
    
    # ... run all 5 agents ...
    # At the end, save the output file path to state
    self.save_state(request_hash, "keyword", "completed", output_file)
    return output_file
```

#### Benefits
- Identical requests reuse previous results instantly
- Reduces API costs and latency
- Better UX: "Cache hit! Using previous result"

---

## Implementation Sequence

Execute tasks in this order for maximum reliability:

```
1️⃣ Task 1 (Subprocess Safety)
   ↓ (2 min, critical security fix)
   
2️⃣ Task 3 (State Management) + Task 4 (Idempotency)
   ↓ (15 min, foundation for caching + deduplication)
   
3️⃣ Task 2 (Prompt Redundancy)
   ↓ (5 min, optimization & clarity)
   
4️⃣ Integration Test + Validation
   ↓ (10 min, verify all changes work together)
```

**Rationale**: Fix security first, then build reliability features, then optimize.

---

## Validation Checklist

After implementing all tasks:

- [ ] **Subprocess Safety**: Run `request_to_plan_todo.py` with sample request, confirm no shell errors
- [ ] **State Management**: Verify `.orchestrator_state/` directory is created with `.state.json` files
- [ ] **Idempotency**: Run same request twice, second execution should use cache
- [ ] **Prompt Clarity**: Verify Review Agent's feedback shows improvement in plan quality
- [ ] **Output Format**: Confirm output markdown file still follows `YYYYMMDD_HHMMSS_keyword.md` naming
- [ ] **Backward Compatibility**: Existing output files should still be readable

---

## Testing Strategy

### Unit Tests (New)
Create `claude_tools/test_request_to_plan_todo.py`:

```python
import unittest
from pathlib import Path
from request_to_plan_todo import SafeOrchestrator

class TestSafeOrchestrator(unittest.TestCase):
    
    def setUp(self):
        self.orchestrator = SafeOrchestrator()
    
    def test_request_hash_deterministic(self):
        """Same input produces same hash"""
        request = "Add a turn system"
        hash1 = self.orchestrator.get_request_hash(request)
        hash2 = self.orchestrator.get_request_hash(request)
        self.assertEqual(hash1, hash2)
    
    def test_state_save_and_load(self):
        """State persistence works correctly"""
        request_hash = self.orchestrator.get_request_hash("test")
        self.orchestrator.save_state(request_hash, "planning", "completed")
        state = self.orchestrator.load_state(request_hash)
        self.assertEqual(state["planning"], "completed")
    
    def test_subprocess_no_shell(self):
        """Subprocess runs without shell=True"""
        # Verify cmd is list, not string
        cmd = self.orchestrator.build_claude_command("test prompt")
        self.assertIsInstance(cmd, list)
        self.assertNotIn("shell=True", str(cmd))
```

### Integration Test
Run demo with state tracking:
```bash
cd claude_tools
python request_to_plan_todo.py "Add a new component system"
# Should produce: outputs/YYYYMMDD_HHMMSS_keyword.md
# Should create: .orchestrator_state/hash.state.json

# Run again with same request
python request_to_plan_todo.py "Add a new component system"
# Should output: "✅ Cache hit! Using outputs/..."
```

---

## Risk Assessment

| Task | Risk | Mitigation |
|------|------|-----------|
| Task 1: Subprocess Safety | Very Low | Removing `shell=True` only; cmd is already list |
| Task 2: Prompt Clarity | Very Low | Consolidating text; no logic change |
| Task 3: State Management | Low | File-based (atomic writes), no API calls |
| Task 4: Idempotency | Low | Read-only caching; no data mutation |

**Overall Risk**: ✅ **LOW** — All changes are additive or clarifying, no breaking changes.

---

## Success Criteria

✅ **Definition of Done**:
1. All 4 tasks implemented per specifications above
2. `.orchestrator_state/` directory with state files created
3. Cache hits on repeated requests (≥1 test)
4. Subprocess runs without shell=True
5. Prompt redundancy eliminated
6. All tests pass (unit + integration)
7. No regressions in output quality

---

## Next Steps After Implementation

1. **Merge this PR** with all 4 tasks completed
2. **Run CHECK phase** (design-implementation gap analysis)
3. **Generate REPORT** with metrics (e.g., "Idempotency hit rate: 85%")
4. **Consider Phase 5**: Extended features
   - Webhook support for async requests
   - Database logging (instead of file-based state)
   - Rate limiting / quota management

---

## Appendix: File Paths Reference

| Component | File | Lines |
|-----------|------|-------|
| Main Implementation | `claude_tools/request_to_plan_todo.py` | All |
| API Documentation | `claude_tools/request_to_plan_todo_api.md` | N/A |
| Safety Principles | `claude_tools/claude_subprocess_api.md` | All |
| Tests (New) | `claude_tools/test_request_to_plan_todo.py` | (to create) |
| State Directory | `.orchestrator_state/` | N/A |

---

**Plan Created**: 2026-04-01 14:30  
**Review Status**: ✅ Addresses all Review Agent feedback  
**Ready for Implementation**: YES
