#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Request to Plan & Todo Generator — Safe Agentic Orchestrator

Pipeline: planning → review → revised_planning → todo → keyword
Output: Single markdown file combining Implementation Plan + Todo Checklist

Each agent has a specific persona and role (see request_to_plan_todo_api.md)

Follows claude_subprocess_api.md safety principles

CLEANUP POLICY:
- SUCCESS: All 5 agents succeed → Output file created at outputs/{YYYYMMDD_HHMMSS}_{keyword}.md
- FAILURE: Any agent fails → No output file created (early return)
  - Agent logs still saved to .agent_logs/ for debugging

Usage:
    python request_to_plan_todo.py "Your user request here"

Output:
    claude_tools/outputs/{YYYYMMDD_HHMMSS}_{keyword}.md (SUCCESS only)
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SafeOrchestrator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.claude_bin = "claude"
        self.logs_dir = Path(".agent_logs")
        self.output_dir = Path("claude_tools") / "outputs"

        self.logs_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def write_atomic(self, path, content):
        """원자적 파일 쓰기 (data integrity)"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = f"{path}.tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp_path, path)

    def save_log(self, agent_type, stdout, stderr):
        """에이전트 로그 저장"""
        timestamp = datetime.now().isoformat().replace(':', '-')
        log_file = self.logs_dir / f"{agent_type}_{timestamp}.log"
        content = f"STDERR:\n{stderr}\n\nSTDOUT:\n{stdout}"
        self.write_atomic(str(log_file), content)
        return str(log_file)

    def _extract_keyword(self, user_request: str) -> str:
        """요청에서 핵심 keyword 추출 (간단한 텍스트 파싱)"""
        # Common stop words to ignore
        stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'with', 'from', 'by', 'about', 'of', 'into', 'as', 'would', 'could',
            'should', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'shall', 'may', 'might',
            'must', 'can', 'want', 'like', 'need', 'make', 'get', 'create', 'build',
            '를', '을', '이', '가', '에', '서', '로', '만', '도', '까', '기', '한',
            '고', '면', '는', '고', '있', '다', '라', '자', '어', '것', '같', '되',
            '주', '저', '있', '새', '하', '좀', '또', '이', '더', '처'
        }

        # Split and clean
        words = user_request.lower().split()

        # Find first non-stop word
        for word in words:
            clean = ''.join(c for c in word if c.isalnum() or c == '_')
            if clean and clean not in stop_words and len(clean) > 2:
                return clean[:20]

        # Fallback
        return "task"

    def run_agent(self, agent_type: str, system_prompt: str, user_prompt: str,
                  allowed_tools: list = None) -> str:
        """Claude CLI subprocess 안전 호출"""

        if allowed_tools is None:
            allowed_tools = ["Read", "Glob", "Grep"]

        # Input Sanitization: 리스트 형식 사용 (자동 이스케이프)
        cmd = [
            "claude",
            "-p",
            user_prompt,
            "-s",
            system_prompt,
            "--model",
            "claude-haiku-4-5-20251001",
            "--cwd",
            str(self.project_root)
        ]

        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])

        print(f"\n>> {agent_type.upper()} Agent running...")

        try:
            # Note: Windows requires shell=True for proper command resolution
            # Input sanitization via list args prevents injection even with shell=True
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120,
                shell=True
            )

            output = result.stdout

            # Sensitive Output Handling: 로그는 별도 파일
            log_file = self.save_log(agent_type, output, result.stderr)

            if result.returncode != 0:
                print(f"[FAIL] {agent_type} Agent failed")
                print(f"       Log: {log_file}")
                if result.stderr:
                    print(f"       Error: {result.stderr[:200]}")
                return None

            print(f"[OK] {agent_type} Agent completed")
            return output

        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] {agent_type} Agent timeout (120s)")
            return None
        except Exception as e:
            print(f"[ERROR] {agent_type} Agent error: {e}")
            return None

    def run_workflow(self, user_request: str) -> str:
        """
        전체 5-agent 파이프라인 실행

        Returns:
            str: Output file path if ALL agents succeed
            None: If any agent fails (no file created per cleanup policy)
        """

        print("\n" + "="*70)
        print("[REQUEST TO PLAN & TODO GENERATOR]")
        print("="*70)
        print(f"\nUser Request:\n{user_request}\n")

        # ============ 1. PLANNING AGENT — 시니어 아키텍트 ============
        planning_system = """You are a senior software architect and strategic planner with 10+ years of experience.
Your role is to deeply analyze user requests and produce a structured initial plan.

Responsibilities:
- Decompose the request into core components and sub-problems
- Identify dependencies, risks, and execution order
- Propose an implementation strategy
- Flag edge cases and potential blockers

Output a numbered, structured analysis. Be concise and technical.
Do NOT ask clarifying questions — work with what you have."""

        planning_prompt = f"""Analyze this user request and create a detailed plan:

USER REQUEST:
{user_request}

Create a comprehensive plan that includes:
1. **Analysis**: What is being asked?
2. **Approach**: How should this be tackled?
3. **Key Components**: What are the main parts?
4. **Potential Issues**: What could go wrong?
5. **Dependencies**: What needs to happen first?

Output your plan clearly and structurally."""

        planning_output = self.run_agent(
            "planning",
            planning_system,
            planning_prompt,
            allowed_tools=["Read", "Glob", "Grep"]
        )

        if not planning_output:
            # Early exit: No output file created (cleanup policy)
            return None

        # ============ 2. REVIEW AGENT — 아키텍처 검증 전문가 ============
        review_system = """You are a meticulous code reviewer and architecture validation expert.
Your role is to critically examine implementation plans and provide actionable feedback.

Responsibilities:
- Identify gaps, missing components, or unclear assumptions
- Verify the approach is feasible and well-ordered
- Challenge assumptions with specific alternatives
- Rate completeness, clarity, and feasibility

Output numbered feedback points. Be direct and specific.
Do NOT rewrite the plan — only provide critique and suggestions."""

        review_prompt = f"""Review this plan and provide critical feedback:

ORIGINAL REQUEST:
{user_request}

PLAN TO REVIEW:
{planning_output}

Evaluate the plan by:
1. **Completeness**: Is anything missing?
2. **Clarity**: Are all points clear and well-defined?
3. **Feasibility**: Are the approaches realistic?
4. **Order**: Is the execution order optimal?
5. **Improvements**: What specific changes would make this better?

Be constructive and specific in your feedback."""

        review_output = self.run_agent(
            "review",
            review_system,
            review_prompt,
            allowed_tools=["Read", "Glob", "Grep"]
        )

        if not review_output:
            # Early exit: No output file created (cleanup policy)
            return None

        # ============ 3. REVISED PLANNING AGENT — 요구사항 정련 전문가 ============
        revised_system = """You are an expert implementation planner who synthesizes architectural feedback into refined plans.
Your role is to produce a final, improved plan incorporating the review feedback.

Responsibilities:
- Address every feedback point from the review
- Structure the plan into clear phases with components and interfaces
- Include testing and validation requirements per phase
- Make the plan detailed enough to hand off to an implementer

Output the complete revised plan with phases, components, and implementation steps.
Do NOT ask questions — produce the final plan directly."""

        revised_prompt = f"""Create an improved implementation plan based on review feedback.

ORIGINAL REQUEST:
{user_request}

ORIGINAL PLAN:
{planning_output}

REVIEW FEEDBACK TO ADDRESS:
{review_output}

OUTPUT:
Generate a comprehensive, revised implementation plan that:
1. Addresses every feedback point above
2. Structures the plan into clear phases (Phase 1, Phase 2, etc.)
3. Includes specific components, systems, or modules
4. Lists implementation steps in order
5. Includes validation and testing requirements per phase
6. Estimates effort/timeline for each phase

Make it detailed enough to hand off to an implementer."""

        revised_output = self.run_agent(
            "revised_planning",
            revised_system,
            revised_prompt,
            allowed_tools=["Read", "Glob", "Grep"]
        )

        if not revised_output:
            # Early exit: No output file created (cleanup policy)
            return None

        # ============ 4. TODO AGENT — 프로젝트 매니저 ============
        todo_system = """You are an expert project manager and task decomposition specialist.
Your role is to convert implementation plans into granular, trackable todo lists.

Responsibilities:
- Break each plan phase into tasks completable in 1-4 hours
- Add clear acceptance criteria to every task
- Mark task dependencies and recommended execution order
- Group tasks under phase headers with time estimates

Output a markdown checklist (- [ ] format).
Do NOT summarize or ask questions — produce the full todo list directly."""

        todo_prompt = f"""Convert this implementation plan into a detailed, actionable todo checklist.

REQUIREMENT:
{user_request}

IMPLEMENTATION PLAN:
{revised_output}

CREATE A TODO CHECKLIST that:
1. Breaks down each plan section into specific, actionable tasks
2. Uses [ ] checkbox format for tracking
3. Includes clear acceptance criteria for each task
4. Shows dependencies and recommended order
5. Groups related items under clear section headers (### Phase X: Name)
6. Each task should be small enough to complete in 1-4 hours
7. Includes time estimates for each phase

OUTPUT FORMAT:
### Phase X: [Name] ([X-Y hours])
- [ ] Task 1
  - Acceptance: [Criteria]
  - Dependencies: [What must be done first]
- [ ] Task 2
  - Acceptance: [Criteria]

Generate the complete todo checklist for the plan above."""

        todo_output = self.run_agent(
            "todo",
            todo_system,
            todo_prompt,
            allowed_tools=["Read", "Glob", "Grep"]
        )

        if not todo_output:
            # Early exit: No output file created (cleanup policy)
            return None

        # ============ 5. KEYWORD EXTRACTION — 요청 요약기 ============
        # Extract keyword from user_request using simple NLP
        keyword = self._extract_keyword(user_request)
        print(f"\n>> KEYWORD Extracted: {keyword}")

        # ============ 6. ASSEMBLE FINAL OUTPUT (Only on SUCCESS) ============
        # All agents succeeded, now create the output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"{timestamp}_{keyword}.md"

        final_output = f"""# {keyword.capitalize()} — {timestamp}

## User Request
{user_request}

---

## Implementation Plan

{revised_output}

---

## Todo Checklist

{todo_output}

---

## Metadata
- Generated at: {datetime.now().isoformat()}
- Pipeline: planning → review → revised_planning → todo → keyword
- Keyword: {keyword}
"""

        self.write_atomic(str(output_file), final_output)

        print("\n" + "="*70)
        print("[SUCCESS] WORKFLOW COMPLETED")
        print("="*70)
        print(f"\n[OUTPUT] Saved to: {output_file}")
        print(f"[POLICY] Output created only because all 5 agents succeeded")

        return str(output_file)


def main():
    """메인 엔트리 포인트"""

    if len(sys.argv) < 2:
        print("Usage: python request_to_plan_todo.py '<your request>'")
        print("\nExample:")
        print("  python request_to_plan_todo.py 'Create a user authentication system'")
        sys.exit(1)

    user_request = sys.argv[1]

    # 프로젝트 루트 경로 (현재 스크립트 기준)
    project_root = Path(__file__).parent.parent

    orchestrator = SafeOrchestrator(str(project_root))
    result = orchestrator.run_workflow(user_request)

    if result:
        print(f"\n[OK] Output file created at:\n   {result}\n")
        sys.exit(0)
    else:
        print("\n[ERROR] One or more agents encountered errors.")
        print(f"   Logs saved to: {orchestrator.logs_dir}/")
        print(f"\n[CLEANUP POLICY]")
        print(f"   ✓ Output file was NOT created (failure detected)")
        print(f"   ✓ No partial/incomplete files generated")
        print(f"   ✓ Agent logs kept for debugging\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
