#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C# Code Reviewer & Refactoring Tool — 6-Stage Agentic Pipeline

Architecture: Parent Agent (Orchestrator) + Sub-Agents via Claude CLI
- Parent: cs_code_reviewer.py (orchestration via subprocess, user interaction)
- Sub-Agents: .claude/agents/planner.md, reviewer.md, coder.md (Claude Code managed)
- User Approvals: Terminal-based decision points

Pipeline: Planner → Reviewer → UA1 → Coder → UA2 → File Apply
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import io
import shutil
import argparse
import shlex
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class CsCodeReviewer:
    """6-stage C# code review & refactoring orchestrator"""

    def __init__(self, project_root: str, auto_approve: bool = False):
        self.project_root = Path(project_root)
        self.claude_bin = "claude"
        self.output_dir = Path("claude_tools") / "review_outputs"
        self.output_dir.mkdir(exist_ok=True)
        self.auto_approve = auto_approve

    def call_agent(
        self,
        agent_name: str,
        user_message: str
    ) -> str:
        """Sub-agent 호출 via Claude CLI (docs/prompts에서 시스템 프롬프트 로드)"""

        print(f"\n>> {agent_name.upper()} Agent 실행 중...\n")

        try:
            # docs/prompts/{agent_name}.md에서 시스템 프롬프트 로드
            agent_prompt_path = self.project_root / "docs" / "prompts" / f"{agent_name}.md"

            system_prompt = ""
            if agent_prompt_path.exists():
                system_prompt = agent_prompt_path.read_text(encoding='utf-8')

            # 최종 프롬프트: system prompt + user message
            final_message = f"{system_prompt}\n\n---\n\n{user_message}"

            # Claude CLI 호출 (stdin + Read tool 순차 실행)
            # 1. stdin으로 프롬프트 전달 (EOF 후 종료)
            # 2. Claude가 Read tool로 파일 접근
            cmd_str = (
                f'claude -p '
                f'--model claude-haiku-4-5-20251001 '
                f'--tools Read '
                f'--add-dir {shlex.quote(str(self.project_root))}'
            )

            env = os.environ.copy()
            env["CLAUDE_CODE_GIT_BASH_PATH"] = r"D:\Git\bin\bash.exe"

            result = subprocess.run(
                cmd_str,
                input=final_message,  # stdin으로 전달, EOF 자동 발생
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300,
                shell=True,
                cwd=str(self.project_root),
                env=env
            )

            output = result.stdout

            if result.returncode != 0:
                print(f"[FAIL] {agent_name} Agent 실패 (returncode={result.returncode})")
                if result.stderr:
                    print(f"       stderr: {result.stderr[:1000]}")
                return None

            if not output or len(output.strip()) == 0:
                print(f"[FAIL] {agent_name} Agent: 빈 출력 반환")
                return None

            print(f"[OK] {agent_name} Agent 완료")
            return output

        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] {agent_name} Agent 타임아웃 (300초)")
            return None
        except Exception as e:
            print(f"[ERROR] {agent_name} Agent 오류: {e}")
            return None

    def run_planner(
        self,
        filepath: str,
        code: str,
        diff: str
    ) -> str:
        """Stage 1: Planner — 코드 분석 & 리팩터링 계획

        파일 경로를 주고 Claude가 직접 Read tool로 읽도록
        """

        user_message = f"""당신은 C# 코드 분석 및 리팩터링 전략 전문가(planner 에이전트)입니다.

파일: {filepath}

위 파일을 읽고, 8가지 기준(네이밍, ECS/DOTS, Burst, 메모리, 복잡도, 성능, 문서화, 안전성)으로 분석하여
리팩터링 계획을 [P1]/[P2]/[P3] 우선순위로 작성해주세요.
코드 예시는 금지됩니다. 변경 방향만 설명하세요."""

        return self.call_agent("planner", user_message)

    def run_reviewer(
        self,
        filepath: str,
        code: str,
        plan: str
    ) -> str:
        """Stage 2: Reviewer — 완성도 & 실현가능성 평가 (8점 이상 = APPROVED)"""

        user_message = f"""당신은 코드 리뷰 및 품질 검증 전문가(reviewer 에이전트)입니다.

파일: {filepath}

위 파일을 읽고, 다음 Planner 계획을 평가하세요:

Planner 분석 및 계획:
{plan}

---

Planner의 각 항목을 평가하세요:
1. 완성도 (Completeness): 1-10점
2. 실현 가능성 (Feasibility): 1-10점
3. 종합 점수 = (완성도 + 실현 가능성) / 2

**통과 기준**: 평균 8점 이상 → 출력에 "APPROVED" 포함
**재작업**: 8점 미만 → 출력에 "NEEDS_REVISION" 포함

각 항목별 점수와 이유를 상세히 제시해주세요."""

        return self.call_agent("reviewer", user_message)

    def show_ua1(
        self,
        filepath: str,
        plan: str,
        review: str
    ) -> str:
        """Stage 3: User Approval 1 — 변경 예정사항 확인"""

        print("\n" + "="*70)
        print("변경 예정 사항 (User Approval 1)")
        print("="*70)
        print(f"\n파일: {filepath}")
        print(f"\nPlanner 계획:\n{plan}")
        print(f"\nReviewer 평가:\n{review}")
        print("\n" + "="*70)

        # auto_approve 모드면 자동 승인
        if self.auto_approve:
            choice = "승인"
            print("[자동 모드] 변경사항 승인")
        else:
            try:
                choice = sys.stdin.readline().strip()
                if not choice:
                    choice = "거부"
            except EOFError:
                choice = "거부"

        print("="*70 + "\n")

        return choice if choice in ["승인", "거부"] else "거부"

    def run_coder(
        self,
        filepath: str,
        code: str,
        plan: str,
        review: str,
        rework_feedback: dict = None
    ) -> str:
        """Stage 4: Coder — 리팩터링 코드 구현 (초기 또는 재작업)"""

        if rework_feedback is None:
            # 초기 구현
            user_message = f"""당신은 C# Unity ECS/DOTS 구현 전문가(coder 에이전트)입니다.

파일: {filepath}

위 파일을 읽고, 다음 계획과 피드백을 100% 반영하여 리팩터링된 완전한 C# 코드를 작성해주세요.

Planner 최종 계획:
{plan}

Reviewer 피드백:
{review}

---
CLAUDE.md의 컨벤션(PascalCase, _camelCase, IComponentData, ISystem, BurstCompile 등)을 모두 준수하세요.

출력 형식:
## 리팩터링된 코드

```csharp
[전체 리팩터링된 코드]
```

## 변경 사항 요약

### [P1] 항목명
- 변경 내용: {{구체적 변경}}
- 라인: {{변경된 라인 범위}}
- 이유: {{Planner 계획의 이유}}

...

## 구현 완성도
- 계획 대비 구현율: 100%"""
        else:
            # 재작업
            user_message = f"""당신은 C# Unity ECS/DOTS 구현 전문가(coder 에이전트)입니다.

파일: {filepath}

위 파일을 읽고, 다음 피드백을 반영하여 코드를 재구현해주세요.

Planner 최종 계획:
{plan}

이전 구현:
```csharp
{rework_feedback['previous_code']}
```

사용자 피드백:

문제 항목:
{rework_feedback['problems']}

개선 방향:
{rework_feedback['improvements']}

추가 피드백:
{rework_feedback.get('extra', '없음')}

---

사용자의 피드백을 100% 반영하여 코드를 재구현해주세요.

출력 형식:
## 재작업된 코드

```csharp
[재구현된 전체 코드]
```

## 변경 사항 (재작업)

### [항목명] 수정 사항
- 문제점: {{사용자 지적}}
- 변경 내용: {{어떻게 개선했는가}}
- 라인: {{변경된 라인 범위}}

...

## 반영된 피드백
- {{피드백 1}}: {{어떻게 반영했는가}}
- {{피드백 2}}: {{어떻게 반영했는가}}"""

        return self.call_agent("coder", user_message)

    def show_ua2(
        self,
        filepath: str,
        code: str,
        coder_output: str
    ) -> dict:
        """Stage 5: User Approval 2 — 변경된 코드 최종 검토 + 재작업 로직"""

        print("\n" + "="*70)
        print("변경된 코드 확인 (User Approval 2)")
        print("="*70)
        print(f"\n파일: {filepath}\n")
        print(f"Coder 구현:\n{coder_output}")
        print("\n" + "="*70)

        # auto_approve 모드면 자동 승인
        if self.auto_approve:
            choice = "승인"
            print("[자동 모드] 구현 승인")
        else:
            try:
                choice = sys.stdin.readline().strip()
                if not choice:
                    choice = "승인"
            except EOFError:
                choice = "승인"

        if choice == "거부":
            try:
                sub_choice = sys.stdin.readline().strip()
                if not sub_choice:
                    sub_choice = "폐기"
            except EOFError:
                sub_choice = "폐기"

            print("="*70 + "\n")

            if sub_choice == "재작업":
                print("문제점 상세 입력\n")
                try:
                    problems = sys.stdin.readline().strip()
                    improvements = sys.stdin.readline().strip()
                    extra = sys.stdin.readline().strip()
                except EOFError:
                    problems = ""
                    improvements = ""
                    extra = ""

                # Coder 출력에서 코드 추출
                previous_code = code
                if "```csharp" in coder_output:
                    try:
                        previous_code = coder_output.split("```csharp")[1].split("```")[0].strip()
                    except:
                        pass

                return {
                    "choice": "재작업",
                    "problems": problems,
                    "improvements": improvements,
                    "extra": extra,
                    "previous_code": previous_code
                }
            else:
                return {"choice": "폐기"}
        else:
            print("="*70 + "\n")
            return {"choice": "승인"}

    def apply_to_file(
        self,
        filepath: str,
        coder_output: str
    ):
        """Stage 6: 파일 적용 — 백업 + 원자적 쓰기 + 보고서 생성"""

        path = Path(filepath)

        # 리팩터링 코드 추출
        refactored_code = coder_output
        if "```csharp" in coder_output:
            try:
                refactored_code = coder_output.split("```csharp")[1].split("```")[0].strip()
            except:
                pass

        # 1. 백업
        backup_path = path.with_suffix('.backup.cs')
        shutil.copy2(str(path), str(backup_path))

        # 2. 원자적 쓰기
        tmp_path = f"{path}.tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(refactored_code)
        os.replace(tmp_path, path)

        # 3. 보고서 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"{timestamp}_{path.stem}_review.md"
        report_content = f"""# 리팩터링 완료 보고서

## 파일
{filepath}

## 메타데이터
- 완료 시간: {datetime.now().isoformat()}
- 백업: {backup_path}

## 변경 사항
{coder_output}
"""
        with open(str(report_path), 'w', encoding='utf-8') as f:
            f.write(report_content)

        print("\n" + "="*70)
        print("[OK] 리팩터링 완료")
        print(f"   파일: {filepath}")
        print(f"   백업: {backup_path}")
        print(f"   보고서: {report_path}")
        print("="*70 + "\n")

    def review_file(self, filepath: str):
        """전체 6단계 파이프라인 실행"""

        print("\n" + "="*70)
        print("[C# CODE REVIEWER] 파이프라인 시작")
        print("="*70)
        print(f"\n대상 파일: {filepath}\n")

        # 파일 읽기
        path = Path(filepath)
        if not path.exists():
            print(f"[FAIL] 파일을 찾을 수 없음: {filepath}")
            return

        code = path.read_text(encoding='utf-8')

        # Git diff 읽기
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD", filepath],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            diff = result.stdout if result.returncode == 0 else ""
        except:
            diff = ""

        # ========== Stage 1 & 2: Planner → Reviewer 루프 ==========
        planner_attempts = 0
        max_attempts = 3
        plan = None
        review = None

        while planner_attempts < max_attempts:
            planner_attempts += 1
            print(f"\n[Attempt {planner_attempts}/{max_attempts}]")

            plan = self.run_planner(filepath, code, diff)
            if not plan:
                print("[FAIL] Planner 실패")
                return

            review = self.run_reviewer(filepath, code, plan)
            if not review:
                print("[FAIL] Reviewer 실패")
                return

            # DEBUG: Reviewer 출력 확인
            print(f"\n[DEBUG] Reviewer 출력 (전체 길이: {len(review)}글자):")
            print(f"[DEBUG] 마지막 500글자:\n{review[-500:]}\n")

            # APPROVED 여부 판정
            is_approved = "APPROVED" in review.upper()

            if is_approved:
                print("[OK] Reviewer 승인")
                break
            else:
                print("[WARN] Reviewer: 재작업 필요")
                if planner_attempts < max_attempts:
                    print("   → Planner 재실행 중...\n")

        if planner_attempts >= max_attempts:
            print(f"[FAIL] {max_attempts}회 시도 후에도 승인 실패")
            return

        # ========== Stage 3: User Approval 1 ==========
        ua1_choice = self.show_ua1(filepath, plan, review)
        if ua1_choice == "거부":
            print("[FAIL] User Approval 1: 거부됨 - 파이프라인 중단")
            return

        # ========== Stage 4 & 5: Coder → User Approval 2 루프 ==========
        rework_feedback = None
        coder_iteration = 0

        while True:
            coder_iteration += 1
            print(f"\n[Coder Iteration {coder_iteration}]")

            coder_output = self.run_coder(
                filepath,
                code,
                plan,
                review,
                rework_feedback
            )
            if not coder_output:
                print("[FAIL] Coder 실패")
                return

            ua2_result = self.show_ua2(filepath, code, coder_output)

            if ua2_result["choice"] == "승인":
                print("[OK] User Approval 2: 승인됨")
                # ========== Stage 6: 파일 적용 ==========
                self.apply_to_file(filepath, coder_output)
                break
            elif ua2_result["choice"] == "폐기":
                print("[FAIL] User Approval 2: 거부됨 (폐기) - 파이프라인 중단")
                break
            else:  # 재작업
                print("[WARN] User Approval 2: 재작업 요청")
                rework_feedback = {
                    "problems": ua2_result["problems"],
                    "improvements": ua2_result["improvements"],
                    "extra": ua2_result.get("extra", ""),
                    "previous_code": ua2_result.get("previous_code", code)
                }
                print("   → Coder 재구현 중...\n")

        print("\n" + "="*70)
        print("[C# CODE REVIEWER] 파이프라인 완료")
        print("="*70 + "\n")


def main():
    """메인 엔트리 포인트"""

    parser = argparse.ArgumentParser(
        description="C# Code Reviewer & Refactoring Tool"
    )
    parser.add_argument(
        "--target",
        type=str,
        help="리뷰 대상 C# 파일 경로 (예: Assets/Scripts/Systems/MoveSystem.cs)"
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="User Approval 1 & 2 자동 승인 (테스트 모드)"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    reviewer = CsCodeReviewer(str(project_root), auto_approve=args.auto_approve)

    if args.target:
        reviewer.review_file(args.target)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
