# Request to Plan & Todo API

Safe agentic orchestrator API for converting user requests into structured implementation plans and actionable todo lists using Claude AI.

## Overview

The `request_to_plan_todo.py` tool executes a 5-stage agentic pipeline to transform any user request into:
1. A detailed **Implementation Plan** (with phases, components, and testing requirements)
2. A granular **Todo Checklist** (with acceptance criteria and dependencies)

Both outputs are combined into a single Markdown file with a semantic keyword in the filename.

---

## Pipeline

The tool runs 5 agents sequentially (each with a distinct persona and role):

```
User Request
    ↓
[1] PLANNING AGENT (시니어 아키텍트)
    → Analyzes request, identifies components, proposes strategy
    ↓
[2] REVIEW AGENT (아키텍처 검증 전문가)
    → Reviews plan for gaps, clarity, feasibility
    ↓
[3] REVISED PLANNING AGENT (요구사항 정련 전문가)
    → Incorporates feedback, produces final implementation plan
    ↓
[4] TODO AGENT (프로젝트 매니저)
    → Decomposes plan into granular, trackable tasks
    ↓
[5] KEYWORD AGENT (요청 요약기)
    → Extracts one keyword from the user request
    ↓
SINGLE OUTPUT FILE: {YYYYMMDD_HHMMSS}_{keyword}.md
├── Implementation Plan (from Agent 3)
└── Todo Checklist (from Agent 4)
```

---

## Agent Definitions

### [1] Planning Agent — 시니어 아키텍트 (Senior Architect)

**Persona**: Senior software architect and strategic planner with 10+ years of experience

**Role**: Deeply analyze user requests and produce structured initial plans

**Responsibilities**:
- Decompose the request into core components and sub-problems
- Identify dependencies, risks, and execution order
- Propose an implementation strategy
- Flag edge cases and potential blockers

**Allowed Tools**: `Read`, `Glob`, `Grep`

**Output Style**: Numbered, structured analysis (concise and technical)

---

### [2] Review Agent — 아키텍처 검증 전문가 (Architecture Validator)

**Persona**: Meticulous code reviewer and architecture validation expert

**Role**: Critically examine implementation plans and provide actionable feedback

**Responsibilities**:
- Identify gaps, missing components, or unclear assumptions
- Verify the approach is feasible and well-ordered
- Challenge assumptions with specific alternatives
- Rate completeness, clarity, and feasibility

**Allowed Tools**: `Read`, `Glob`, `Grep`

**Output Style**: Numbered feedback points (direct and specific, critique only—no rewrites)

---

### [3] Revised Planning Agent — 요구사항 정련 전문가 (Requirements Specialist)

**Persona**: Expert implementation planner who synthesizes architectural feedback into refined plans

**Role**: Produce a final, improved plan incorporating all review feedback

**Responsibilities**:
- Address every feedback point from Review Agent
- Structure the plan into clear phases with components and interfaces
- Include testing and validation requirements per phase
- Make the plan detailed enough to hand off to an implementer

**Allowed Tools**: `Read`, `Glob`, `Grep`

**Output Style**: Complete refined plan with phases, components, and implementation steps (no questions—direct output)

---

### [4] Todo Agent — 프로젝트 매니저 (Project Manager)

**Persona**: Expert project manager and task decomposition specialist

**Role**: Convert implementation plans into granular, trackable todo lists

**Responsibilities**:
- Break each plan phase into tasks completable in 1-4 hours
- Add clear acceptance criteria to every task
- Mark task dependencies and recommended execution order
- Group tasks under phase headers with time estimates

**Allowed Tools**: `Read`, `Glob`, `Grep`

**Output Style**: Markdown checklist format (`- [ ]`), no summaries or questions—full list

---

### [5] Keyword Agent — 요청 요약기 (Request Summarizer) — NEW

**Persona**: Concise naming specialist

**Role**: Extract the single most important English noun or verb from the user's request

**Responsibilities**:
- Identify the core concept or action in the request
- Output exactly one lowercase word (no spaces, punctuation, or explanation)

**Allowed Tools**: None

**Output Style**: Single word only

**Examples**:
- "Create a turn-based combat system" → `combat`
- "Add user authentication" → `authentication`
- "Build an inventory system" → `inventory`
- "Code review and refactoring automation" → `refactoring`

**Fallback**: If extraction fails, output is `task`

---

## Output Format

### File Naming

**Format**: `{YYYYMMDD}_{HHMMSS}_{keyword}.md`

Where:
- `YYYYMMDD` = Year (4 digits) + Month (2 digits) + Day (2 digits)
- `HHMMSS` = Hour (00-23) + Minute (00-59) + Second (00-59)
- `keyword` = Single word from Keyword Agent output

**Example**: `20260401_152030_refactoring.md`

### File Location

```
claude_tools/outputs/{YYYYMMDD_HHMMSS}_{keyword}.md
```

### File Contents

```markdown
# {Keyword} — {YYYYMMDD_HHMMSS}

## User Request
{Original user request}

---

## Implementation Plan

{Complete plan from Revised Planning Agent}
- Phases (Phase 1, Phase 2, etc.)
- Components and interfaces
- Testing and validation requirements
- Effort/timeline estimates

---

## Todo Checklist

{Complete checklist from Todo Agent}
- Grouped by phases
- Checkboxes (- [ ])
- Acceptance criteria
- Dependencies
- Time estimates

---

## Metadata
- Generated at: {Full ISO timestamp}
- Pipeline: planning → review → revised_planning → todo → keyword
- Keyword: {keyword}
```

---

## Usage

### Basic Usage

```bash
cd "D:/Unity/Unity Project/Sweepers in ECS"
export PYTHONIOENCODING=utf-8
export CLAUDE_CODE_GIT_BASH_PATH="D:\Git\usr\bin\bash.exe"  # Windows only

python claude_tools/request_to_plan_todo.py "Your request here"
```

### Example

```bash
python claude_tools/request_to_plan_todo.py "Create an automated code review and refactoring tool for Unity ECS systems"
```

**Output**:
```
[OK] Output file created at:
   claude_tools/outputs/20260401_152030_refactoring.md
```

---

## Requirements

### Production Use (request_to_plan_todo.py)

1. **Claude CLI** v2.1.71 or later
   ```bash
   npm install -g claude-code
   ```

2. **Git Bash** (Windows only)
   - Download from https://git-scm.com/downloads
   - Set environment variable:
     ```bash
     set CLAUDE_CODE_GIT_BASH_PATH=D:\Git\usr\bin\bash.exe
     ```

3. **Python** 3.8 or later
   - Verify: `python --version`

### Environment Setup

```bash
# Windows
set PYTHONIOENCODING=utf-8
set CLAUDE_CODE_GIT_BASH_PATH=D:\Git\usr\bin\bash.exe

# macOS/Linux
export PYTHONIOENCODING=utf-8
```

---

## Configuration

### Model Selection

Currently configured for:
- **Production**: `claude-haiku-4-5-20251001` (fast, cost-effective)

Can be customized in `request_to_plan_todo.py`:
```python
"--model", "claude-opus-4-6"  # More capable, slower
```

### Timeout

Default: 120 seconds per agent

To increase:
```python
result = subprocess.run(..., timeout=300)  # 5 minutes
```

---

## Safety Principles (from claude_subprocess_api.md)

### 1. Input Sanitization
- Subprocess called with list arguments (automatic escaping)
- No shell metacharacters in user input
- Prevents command injection

### 2. Data Integrity
- Atomic file writes (tmp → rename)
- Sequential execution (no parallel agents)
- Ensures no partial/corrupt outputs

### 3. Sensitive Output Handling
- Logs stored separately (`.agent_logs/`)
- Debug output not passed between agents
- Controlled information flow

### 4. Failure Recovery
- Detailed error logs on failure
- All errors logged to `.agent_logs/`
- Original request preserved for debugging

---

## Output Examples

### Example 1: Combat System

**Request**: "Create a turn-based combat system for the ECS game with health, damage, and turn management"

**Output File**: `20260401_151000_combat.md`

Contains:
- Implementation Plan: 4 phases (Data Structures, Core Systems, Integration, Testing)
- Todo Checklist: 50+ tasks with acceptance criteria and dependencies

### Example 2: Refactoring Tool

**Request**: "Create an automated code review and refactoring tool for Unity ECS systems"

**Output File**: `20260401_152030_refactoring.md`

Contains:
- Implementation Plan: Architecture, components, analysis rules
- Todo Checklist: Analysis system, rule engine, report generation tasks

---

## Troubleshooting

### Claude CLI Not Found

```
[ERROR] planning Agent error: [WinError 2] File not found
```

**Solution**: Install Claude CLI globally
```bash
npm install -g claude-code
claude --version
```

### Git Bash Error (Windows)

```
Claude Code on Windows requires git-bash...
```

**Solution**: Set the environment variable
```bash
set CLAUDE_CODE_GIT_BASH_PATH=D:\Git\usr\bin\bash.exe
```

### Agent Timeout (120s)

```
[TIMEOUT] planning Agent timeout (120s)
```

**Solutions**:
1. Simplify the user request (shorter, more specific)
2. Increase timeout in code: change `timeout=120` to `timeout=300`
3. Check Claude API rate limits (reset at 3am Asia/Seoul)

### Encoding Errors

```
UnicodeDecodeError: 'cp949' codec can't decode...
```

**Solution**: Set environment variable before running
```bash
set PYTHONIOENCODING=utf-8
python claude_tools/request_to_plan_todo.py "Your request"
```

---

## Design Decisions

### Sequential Agents (Not Parallel)
- Simplifies state management
- Ensures data dependencies flow correctly
- Easier debugging and error handling

### Single Output File (Not Multiple)
- Plan and Todo in one document (no redundancy)
- Easier to share and version control
- Single source of truth

### Keyword in Filename
- Semantic naming (more readable than timestamps alone)
- Enables quick pattern searching (`ls *refactoring*.md`)
- Helps with file organization

### Atomic File Writes
- Write to temp file first, then rename (atomic)
- Prevents partial/corrupt outputs on failure
- Follows `claude_subprocess_api.md` best practices

### Separate Logs
- `.agent_logs/` contains all execution logs
- No sensitive data leaks into output files
- Easier debugging and re-execution

---

## Customization

### Extending the Pipeline

Add a new agent stage:

```python
custom_system = """You are an expert in {domain}.
Your role is to {specific_goal}."""

custom_prompt = f"""Analyze this: {previous_output}"""

custom_output = self.run_agent(
    "custom_stage",
    custom_system,
    custom_prompt,
    allowed_tools=["Read", "Grep"]
)
```

### Modifying Agent Behavior

Edit `system_prompt` in `request_to_plan_todo.py`:

```python
planning_system = """You are a {custom_persona}.
Your role is to {custom_role}."""
```

---

## Architecture Notes

### Why Haiku Model?

`claude-haiku-4-5-20251001` was chosen for:
- **Speed**: ~3-5 seconds per agent (total ~15-20 seconds)
- **Cost**: Significantly cheaper than Opus/Sonnet
- **Capability**: Sufficient for planning, review, and todo generation

### Why Sequential, Not Parallel?

Parallel execution would:
- Create state management complexity
- Make error recovery harder
- Require careful synchronization

Sequential ensures:
- Clear data flow (output of Agent N → input of Agent N+1)
- Deterministic behavior
- Easier debugging

---

## Files Reference

```
claude_tools/
├── request_to_plan_todo.py           (Production tool - this API)
├── request_to_plan_todo_demo.py      (Demo version with mock data)
├── request_to_plan_todo_api.md        (This file - API documentation)
├── claude_subprocess_api.md           (Safety principles & architecture)
├── outputs/
│   ├── 20260401_152030_refactoring.md (Example output)
│   └── {YYYYMMDD_HHMMSS}_{keyword}.md (Generated outputs)
└── .agent_logs/
    ├── planning_{timestamp}.log
    ├── review_{timestamp}.log
    ├── revised_planning_{timestamp}.log
    ├── todo_{timestamp}.log
    └── keyword_{timestamp}.log
```

---

## Next Steps

1. **Quick Test**: Run with a simple request
   ```bash
   python request_to_plan_todo.py "Create a login system"
   ```

2. **Check Output**: View the generated Markdown file
   ```bash
   cat claude_tools/outputs/20260401_*.md
   ```

3. **Integrate**: Use in CI/CD, automation scripts, or IDE hooks

4. **Customize**: Modify agent personas for your domain

---

## References

- `claude_subprocess_api.md` — Complete safety principles and orchestrator pattern
- `CLAUDE.md` — Project conventions and best practices
- `request_to_plan_todo.py` — Implementation source code
- `request_to_plan_todo_demo.py` — Mock demo version for testing

---

**Last Updated**: 2026-04-01
**Status**: ✅ Production ready with 5-agent pipeline
**API Version**: 1.0
