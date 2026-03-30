#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Request to Plan & Todo Generator — Safe Agentic Orchestrator

Pipeline: planning -> review -> revised planning -> todo
Follows claude_subprocess_api.md safety principles

Usage:
    python request_to_plan_todo.py "Your user request here"

Output:
    claude_tools/outputs/{timestamp}_plan_todo.md
"""

import subprocess
import json
import sys
import hashlib
import os
from pathlib import Path
from datetime import datetime
import shlex
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SafeOrchestrator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.claude_bin = "claude"
        self.state_dir = Path(".orchestrator_state")
        self.fail_dir = Path("fail_report_handoffs")
        self.logs_dir = Path(".agent_logs")
        self.output_dir = Path("claude_tools") / "outputs"

        self.state_dir.mkdir(exist_ok=True)
        self.fail_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def hash_file(self, path):
        """파일 무결성 검사용 해시"""
        if not os.path.exists(path):
            return None
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

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
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
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
        """전체 파이프라인 실행"""

        print("\n" + "="*70)
        print("[PLAN & TODO GENERATOR]")
        print("="*70)
        print(f"\nUser Request:\n{user_request}\n")

        # ============ 1. PLANNING AGENT ============
        planning_system = """You are a senior product architect and strategic planner with 10+ years of experience.
Your task is to analyze user requests deeply and create comprehensive plans.
Focus on:
- Breaking down the request into core components
- Identifying dependencies and execution order
- Considering edge cases and potential issues
- Providing clear, structured output

Always output your plan in a clear, numbered format."""

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
            return None

        # ============ 2. REVIEW AGENT ============
        review_system = """You are a meticulous reviewer and quality assurance expert.
Your task is to critically examine plans and provide constructive feedback.
Focus on:
- Identifying gaps or unclear points
- Questioning assumptions
- Suggesting improvements
- Ensuring comprehensiveness

Provide specific, actionable feedback."""

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
            return None

        # ============ 3. REVISED PLANNING AGENT ============
        revised_system = """You are an expert planner who incorporates feedback expertly.
Your task is to revise the original plan based on review feedback.
Focus on:
- Incorporating all valid suggestions
- Improving clarity and structure
- Ensuring logical flow
- Maintaining feasibility

Output a comprehensive, refined plan."""

        revised_prompt = f"""Revise and improve this plan based on the review feedback:

ORIGINAL REQUEST:
{user_request}

ORIGINAL PLAN:
{planning_output}

REVIEW FEEDBACK:
{review_output}

Create a REVISED PLAN that:
1. Incorporates the feedback from the review
2. Improves clarity and comprehensiveness
3. Maintains logical flow and dependencies
4. Is ready to be converted into actionable todos

Output the complete revised plan with numbered sections."""

        revised_output = self.run_agent(
            "revised_planning",
            revised_system,
            revised_prompt,
            allowed_tools=["Read", "Glob", "Grep"]
        )

        if not revised_output:
            return None

        # ============ 4. TODO AGENT ============
        todo_system = """You are an expert task decomposer and project manager.
Your task is to convert strategic plans into concrete, actionable todos.
Focus on:
- Breaking down into specific, measurable tasks
- Setting clear acceptance criteria
- Establishing proper sequencing
- Making tasks self-contained and actionable

Output todos in a well-structured, easy-to-follow format."""

        todo_prompt = f"""Convert this revised plan into a comprehensive todo list:

ORIGINAL REQUEST:
{user_request}

REVISED PLAN:
{revised_output}

Create a detailed TODO LIST that:
1. Breaks down each plan section into concrete tasks
2. Includes clear acceptance criteria for each task
3. Shows task dependencies with ordering
4. Uses checkboxes for tracking
5. Groups related tasks under clear categories

Format as a markdown checklist that can be used for project tracking."""

        todo_output = self.run_agent(
            "todo",
            todo_system,
            todo_prompt,
            allowed_tools=["Read", "Glob", "Grep"]
        )

        if not todo_output:
            return None

        # ============ 5. ASSEMBLE FINAL OUTPUT ============
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"{timestamp}_plan_todo.md"

        final_output = f"""# Plan & Todo Generation — {timestamp}

## User Request
{user_request}

---

## [PLAN] Revised Planning

{revised_output}

---

## [TODO] Todo List

{todo_output}

---

## [SUMMARY] Generation Summary
- Planning: [OK] Generated initial plan
- Review: [OK] Reviewed and provided feedback
- Revised Planning: [OK] Incorporated feedback
- Todo: [OK] Generated actionable tasks
- Generated at: {datetime.now().isoformat()}
"""

        self.write_atomic(str(output_file), final_output)

        print("\n" + "="*70)
        print("[SUCCESS] WORKFLOW COMPLETED")
        print("="*70)
        print(f"\n[OUTPUT] Saved to: {output_file}")

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
        print(f"   Check logs in: {orchestrator.logs_dir}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
