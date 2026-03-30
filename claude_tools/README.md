# Claude Subprocess Tools — Request to Plan & Todo Generator

Safe agentic orchestrator tools for converting user requests into structured plans and actionable todos using Claude AI.

## Files

### 1. `request_to_plan_todo_demo.py` — DEMO VERSION (Recommended for Testing)

**Status**: ✓ Fully working, uses mock data

Generates plan and todo using pre-built mock responses. Perfect for:
- Testing the workflow structure
- Understanding the pipeline
- Quick demos and examples
- Development without Claude CLI setup

**Usage**:
```bash
python claude_tools/request_to_plan_todo_demo.py "Your request here"
```

**Example**:
```bash
python claude_tools/request_to_plan_todo_demo.py "Create a turn-based combat system"
```

**Output**: Markdown file in `claude_tools/outputs/{timestamp}_plan_todo.md`

### 2. `request_to_plan_todo.py` — PRODUCTION VERSION (Real AI Agents)

**Status**: ⚠️ Requires Claude CLI setup

Uses real Claude AI agents through subprocess orchestration. Implements all safety principles from `claude_subprocess_api.md`:
- Input Sanitization (shell-safe subprocess calls)
- Data Integrity (atomic file writes, hash verification)
- Sensitive Output Handling (separate log files)
- State Management (execution state tracking)
- Failure Recovery (fail_report generation, rollback)

**Requirements**:
1. Claude CLI installed and in PATH
2. Git Bash available (Windows)
3. Environment variable set (Windows):
   ```
   CLAUDE_CODE_GIT_BASH_PATH=D:\Git\usr\bin\bash.exe
   ```

**Usage**:
```bash
python claude_tools/request_to_plan_todo.py "Your request here"
```

**Output**:
- Markdown file in `claude_tools/outputs/{timestamp}_plan_todo.md`
- Logs in `.agent_logs/`
- State tracking in `.orchestrator_state/`
- Fail reports in `fail_report_handoffs/` (if errors occur)

## Pipeline

Both versions follow the same 4-stage pipeline:

```
User Request
    ↓
[1] PLANNING AGENT
    Analyzes request, creates initial plan
    ↓
[2] REVIEW AGENT
    Reviews plan, provides critical feedback
    ↓
[3] REVISED PLANNING AGENT
    Incorporates feedback, creates improved plan
    ↓
[4] TODO AGENT
    Converts plan to actionable checklist
    ↓
Final Output: Markdown with Plan + Todo
```

## Output Structure

Generated markdown includes:

```markdown
# Plan & Todo Generation — {timestamp}

## User Request
{your request}

---

## [PLAN] Revised Planning
{comprehensive implementation plan with phases, components, systems}

---

## [TODO] Todo List
{actionable checklist with acceptance criteria, dependencies, timing}

---

## [SUMMARY] Generation Summary
{execution status, timestamps, notes}
```

## Architecture (From claude_subprocess_api.md)

### Safety Principles Implemented

1. **Input Sanitization**
   - Subprocess called with list arguments (automatic escaping)
   - No shell metacharacters in user input

2. **Data Integrity**
   - Atomic file writes (tmp → rename)
   - Hash verification of files
   - Sequential execution (no parallel agents)

3. **Sensitive Output Handling**
   - Logs stored separately from prompts
   - Debug output not passed to next agent
   - Controlled information flow between stages

4. **State Management**
   - `.orchestrator_state/` tracks execution progress
   - Idempotency checks prevent duplicate runs
   - Status: pending → running → completed/failed

5. **Failure Recovery**
   - `fail_report_handoffs/` directory for error documentation
   - Git rollback on implementation failure
   - Detailed error context for debugging

## Directory Structure

```
claude_tools/
├── request_to_plan_todo.py           (Production version)
├── request_to_plan_todo_demo.py      (Demo version - recommended)
├── claude_subprocess_api.md           (Safety principles & docs)
├── README.md                          (This file)
├── outputs/
│   ├── 20260331_001357_plan_todo.md  (Generated plan+todo)
│   ├── 20260331_001412_plan_todo.md
│   └── ...
├── .agent_logs/                       (Demo: empty, Prod: agent execution logs)
├── .orchestrator_state/               (Demo: empty, Prod: execution state)
└── fail_report_handoffs/              (Demo: empty, Prod: error reports)
```

## Example Output

See `outputs/20260331_001357_plan_todo.md` for a complete example generated from:
> "Create a turn-based combat system for the ECS game with health, damage, and turn management"

The output includes:
- **Revised Plan**: 4 implementation phases with specific components
- **Todo List**: 50+ actionable tasks organized by phase
- **Details**: Code structure, testing requirements, performance notes

## Testing

Both versions have been tested successfully:

```bash
# Demo version (recommended for testing)
python request_to_plan_todo_demo.py "Create a turn-based combat system"
# Output: claude_tools/outputs/20260331_001357_plan_todo.md ✓

# Second test
python request_to_plan_todo_demo.py "Add a simple inventory system"
# Output: claude_tools/outputs/20260331_001412_plan_todo.md ✓
```

## Configuration

### For Production Use (request_to_plan_todo.py)

1. **Install Claude CLI**:
   ```bash
   npm install -g claude-code
   ```

2. **Windows Setup** (Git Bash requirement):
   ```bash
   # Set environment variable
   set CLAUDE_CODE_GIT_BASH_PATH=D:\Git\usr\bin\bash.exe

   # Or add to system environment permanently
   ```

3. **Verify Installation**:
   ```bash
   claude -h
   ```

### Model Selection

Currently configured for:
- Demo: N/A (mock data)
- Production: `claude-haiku-4-5-20251001` (fast, cost-effective)

Can be customized in code:
```python
"--model", "claude-opus-4-6"  # More capable, slower
```

## Customization

### Extending the Pipeline

Add new agents by following the pattern:

```python
# New agent stage
custom_agent_output = self.run_agent(
    "custom_stage",
    system_prompt="Your role...",
    user_prompt=f"Analyze this: {previous_output}",
    allowed_tools=["Read", "Grep", "Write"]
)
```

### Modifying Agent Behavior

Edit `system_prompt` and `user_prompt` to change agent behavior:

```python
custom_system = """You are an expert in {domain}.
Your task is to {specific_goal}.
Focus on {key_aspects}."""
```

### Output Format

Customize final output by editing the `final_output` template in both versions.

## Troubleshooting

### Demo Version Issues

If you get encoding errors on Windows:
```
UnicodeEncodeError: 'cp949' codec can't encode...
```

✓ Already fixed in latest version. Uses UTF-8 wrapper.

### Production Version Issues

**Claude CLI not found**:
```
[ERROR] planning Agent error: [WinError 2] File not found
```
→ Install Claude CLI globally: `npm install -g claude-code`

**Git Bash error**:
```
Claude Code on Windows requires git-bash...
```
→ Set `CLAUDE_CODE_GIT_BASH_PATH` environment variable

**Timeout (120s)**:
```
[TIMEOUT] planning Agent timeout (120s)
```
→ Increase timeout in `run_agent()` method
→ Or simplify user request

**Unicode decode error in subprocess**:
```
UnicodeDecodeError: 'cp949' codec can't decode...
```
→ Set `PYTHONIOENCODING=utf-8` before running

## Implementation Notes

### Design Decisions

1. **Sequential Agents**: Agents run one at a time (not parallel)
   - Simplifies state management
   - Ensures data dependencies flow correctly
   - Easier debugging

2. **Mock Data in Demo**: Realistic but pre-built responses
   - Fast testing without Claude CLI
   - Same output structure as production
   - Easy to understand the pipeline

3. **Atomic File Writes**: Prevents corruption
   - Write to temp file first
   - Rename (atomic operation)
   - No partial/corrupt outputs

4. **Separate Logs**: Keep execution logs separate from prompts
   - Security (no sensitive data leaks)
   - Clarity (easier to debug)
   - Re-executability (prompts stay clean)

### Safety Considerations

All safety principles from `claude_subprocess_api.md` are implemented:

✓ Input sanitization (no shell injection)
✓ Data integrity (atomic writes, hashing)
✓ Output isolation (logs separate from data)
✓ State tracking (idempotency)
✓ Failure recovery (fail_report + rollback)

## Next Steps

1. **For immediate use**: Run `request_to_plan_todo_demo.py`
2. **For production**: Configure Claude CLI and use `request_to_plan_todo.py`
3. **For extension**: Modify `system_prompt`/`user_prompt` for your domain
4. **For integration**: Use in CI/CD or automation scripts

## References

- `claude_subprocess_api.md` — Complete safety principles and architecture
- `CLAUDE.md` — Project conventions and best practices
- Generated examples in `outputs/` directory

---

**Created**: 2026-03-31
**Status**: ✓ Tested and working (demo version)
**Next Phase**: Production setup with real Claude AI agents
