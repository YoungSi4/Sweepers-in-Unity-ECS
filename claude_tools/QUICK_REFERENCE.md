# Quick Reference — Implementation Guide

**Phase**: DO (Implementation)  
**Feature**: claude_tools  
**Tasks**: 3 Phases (4 fixes)  
**Total Time**: ~22 min  
**Risk**: LOW

---

## 🎯 At a Glance

| Task | File | What | Why | Time |
|------|------|------|-----|------|
| 1 | request_orchestrator.py:158 | Remove `shell=True` | Security | 2m |
| 2A | request_to_plan_todo.py | Add `load_state()`, `save_state()` | Prevent re-runs | 10m |
| 2B | request_to_plan_todo.py | Add `get_request_hash()`, `load_cached_output()` | Enable caching | 5m |
| 3 | request_to_plan_todo.py:~218 | Remove duplicate `{user_request}` | Token efficiency | 5m |

---

## Phase 1: Fix `shell=True` (2 min)

**File**: `request_orchestrator.py`  
**Line**: 158

### Before
```python
result = subprocess.run(
    ["claude", "-p", orchestration_prompt, "--model", "claude-haiku-4-5-20251001"],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace',
    timeout=300,
    shell=True  # ❌ REMOVE THIS
)
```

### After
```python
result = subprocess.run(
    ["claude", "-p", orchestration_prompt, "--model", "claude-haiku-4-5-20251001"],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace',
    timeout=300
)
```

✅ Done!

---

## Phase 2A: State Management (10 min)

**File**: `request_to_plan_todo.py`  
**Class**: `SafeOrchestrator`  
**Add After**: `__init__()` method

### Step 1: Add imports
```python
import json
import hashlib
import os
from typing import Optional
from datetime import datetime
```

### Step 2: Add state methods
```python
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
    
    tmp = f"{state_file}.tmp"
    with open(tmp, 'w') as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, state_file)
```

### Step 3: Update `run_workflow()` to save state after each agent
```python
# After run_planning_agent() succeeds:
self.save_state(request_hash, "planning_agent", "completed")

# After run_review_agent() succeeds:
self.save_state(request_hash, "review_agent", "completed")

# ... and so on for all 5 agents ...

# At the end before return:
self.save_state(request_hash, "keyword_extraction_agent", "completed", output_file)
```

✅ State management ready!

---

## Phase 2B: Request Hashing + Caching (5 min)

**File**: `request_to_plan_todo.py`  
**Class**: `SafeOrchestrator`  
**Add After**: State management methods

### Step 1: Add hashing methods
```python
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

### Step 2: Update `run_workflow()` to use cache
**Add at top of `run_workflow(user_request: str)` method**:
```python
def run_workflow(self, user_request: str) -> str:
    # NEW: Check for cached result
    request_hash = self.get_request_hash(user_request)
    cached = self.load_cached_output(request_hash)
    if cached:
        print(f"✅ Cache hit! Reusing: {cached}")
        return cached
    
    # ... rest of existing code ...
```

**Also update the final return**:
```python
# Before returning output_file, save it to state:
self.save_state(request_hash, "keyword_extraction_agent", "completed", output_file)
return output_file
```

✅ Caching ready!

---

## Phase 3: Remove Prompt Redundancy (5 min)

**File**: `request_to_plan_todo.py`  
**Method**: `run_revised_planning_agent()`  
**Line**: ~218-222 (revised_planning_prompt)

### Before
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

### After
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

✅ Redundancy eliminated!

---

## 🧪 Quick Test

### Test 1: No shell=True
```bash
grep -n "shell=True" claude_tools/request_orchestrator.py
# Expected: No output (0 matches)
```

### Test 2: Cache Works
```bash
cd claude_tools

# First run
python request_to_plan_todo.py "Create REST API"
# Output: [OK] Plan & Todo generated: outputs/YYYYMMDD_HHMMSS_*.md

# Check state file
ls -la .orchestrator_state/
# Output: {hash}.state.json

# Second run (same request)
python request_to_plan_todo.py "Create REST API"
# Output: ✅ Cache hit! Reusing: outputs/YYYYMMDD_HHMMSS_*.md
```

### Test 3: No Redundancy
```bash
grep -c "{user_request}" claude_tools/request_to_plan_todo.py
# Expected: Each should appear exactly once in revised_planning_prompt
```

---

## 📊 Verification Checklist

After implementing all phases:

```
Phase 1 ✅
  [ ] request_orchestrator.py:158 has no shell=True
  [ ] subprocess.run() call works correctly
  
Phase 2 ✅
  [ ] load_state() method exists
  [ ] save_state() method exists
  [ ] get_request_hash() method exists
  [ ] load_cached_output() method exists
  [ ] run_workflow() checks cache at start
  [ ] run_workflow() saves state after each agent
  [ ] .orchestrator_state/ directory created on run
  
Phase 3 ✅
  [ ] revised_planning_prompt has single {user_request}
  [ ] {review_feedback} is clearly separated
  [ ] Prompt reads clearly without duplication

Testing ✅
  [ ] First run creates output file
  [ ] First run creates state JSON
  [ ] Second identical run uses cache
  [ ] State JSON is valid JSON (can be parsed)
  [ ] No regressions in output quality
```

---

## 🚨 Common Pitfalls

| Issue | Solution |
|-------|----------|
| State file not created | Ensure `state_file.parent.mkdir(parents=True, exist_ok=True)` is called |
| Cache not found on 2nd run | Check request hash is deterministic (test with same string) |
| `shell=True` left in code | Search all Python files for `shell=True` |
| Prompt still has duplicate | Use grep to find all `{user_request}` occurrences |

---

## 📞 Need Help?

1. **Subprocess question**: See `claude_subprocess_api.md`
2. **State format**: Check `.orchestrator_state/` example files
3. **Hash collision**: Run `test_improvements.py` unit tests
4. **Caching logic**: Review `load_cached_output()` flow

---

**Status**: READY FOR IMPLEMENTATION  
**Complexity**: LOW  
**Risk**: LOW  
**Time**: ~22 min
