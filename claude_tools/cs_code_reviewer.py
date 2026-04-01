#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C# Code Review & Refactoring Tool
Assets/Scripts 경로의 C# 스크립트를 읽고 변경사항을 확인하여
코드 리뷰 및 리팩터링을 수행합니다.

Pipeline: planner → reviewer → coder

- planner : 코드 분석 및 리팩터링 계획 수립 (코드 직접 작성 금지)
- reviewer: 계획 및 코드 품질 검토 (코드 직접 작성 금지)
- coder   : 계획 기반 실제 코드 수정 (계획 수정 금지, 구현만 담당)

Usage:
    python cs_code_reviewer.py [--target <파일경로>] [--all]

    --target : 특정 .cs 파일 지정 (예: Assets/Scripts/Systems/MoveSystem.cs)
    --all    : Assets/Scripts 내 모든 변경된 .cs 파일 대상

Output:
    claude_tools/review_outputs/{timestamp}_{filename}_review.md
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import io

# Fix Windows console encoding
if sys.platform == 'win32' and not isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass


class CsCodeReviewer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.scripts_dir = self.project_root / "Assets" / "Scripts"
        self.output_dir = Path("claude_tools") / "review_outputs"
        self.logs_dir = Path(".agent_logs")
        self.output_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Git 유틸리티                                                        #
    # ------------------------------------------------------------------ #

    def get_changed_cs_files(self) -> list:
        """git diff로 Assets/Scripts 내 변경된 .cs 파일 목록 반환"""
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=str(self.project_root)
        )
        staged = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=str(self.project_root)
        )

        all_files = result.stdout.split('\n') + staged.stdout.split('\n')
        cs_files = [
            f.strip() for f in all_files
            if f.strip().endswith('.cs') and 'Assets/Scripts' in f
        ]
        return list(set(cs_files))

    def get_git_diff(self, filepath: str) -> str:
        """특정 파일의 git diff 반환"""
        result = subprocess.run(
            ["git", "diff", "HEAD", "--", filepath],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=str(self.project_root)
        )
        if not result.stdout:
            # staged 변경사항 확인
            result = subprocess.run(
                ["git", "diff", "--cached", "--", filepath],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=str(self.project_root)
            )
        return result.stdout

    def get_file_content(self, filepath: str) -> str:
        """파일 전체 내용 반환"""
        full_path = self.project_root / filepath
        if not full_path.exists():
            return f"[파일 없음: {filepath}]"
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    # ------------------------------------------------------------------ #
    #  Agent 실행                                                          #
    # ------------------------------------------------------------------ #

    def run_agent(self, agent_type: str, system_prompt: str, user_prompt: str) -> str:
        """Claude CLI subprocess로 agent 호출"""

        cmd = [
            "claude",
            "-p", user_prompt,
            "-s", system_prompt,
            "--model", "claude-haiku-4-5-20251001",
            "--cwd", str(self.project_root),
            "--allowedTools", "Read,Glob,Grep"
        ]

        print(f"\n>> [{agent_type.upper()} AGENT] 실행 중...")

        try:
            env = os.environ.copy()
            env["CLAUDE_CODE_GIT_BASH_PATH"] = r"D:\Git\bin\bash.exe"
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=180,
                shell=True,
                env=env
            )

            # 로그 저장
            timestamp = datetime.now().isoformat().replace(':', '-')
            log_file = self.logs_dir / f"{agent_type}_{timestamp}.log"
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"STDERR:\n{result.stderr}\n\nSTDOUT:\n{result.stdout}")

            if result.returncode != 0:
                print(f"[오류] {agent_type} agent 실패")
                print(f"       로그: {log_file}")
                if result.stderr:
                    print(f"       에러: {result.stderr[:200]}")
                return None

            print(f"[완료] {agent_type} agent 완료")
            return result.stdout

        except subprocess.TimeoutExpired:
            print(f"[타임아웃] {agent_type} agent 180초 초과")
            return None
        except Exception as e:
            print(f"[오류] {agent_type} agent 예외: {e}")
            return None

    # ------------------------------------------------------------------ #
    #  Agent 페르소나 & 프롬프트 (TODO: 추후 구체화)                        #
    # ------------------------------------------------------------------ #

    def run_planner(self, file_content: str, git_diff: str, filepath: str) -> str:
        """
        Planner Agent
        역할: 코드 분석 및 리팩터링 계획 수립
        제약: 코드를 직접 작성하지 않음
        페르소나: TODO - 추후 구체화
        """
        system_prompt = """당신은 코드 분석 및 리팩터링 계획 전문가입니다.
코드를 분석하고 개선 계획을 수립하는 것이 역할입니다.

중요 제약:
- 절대 코드를 직접 작성하지 않습니다
- 계획과 지시사항만 작성합니다
- 구체적인 코드 예시 대신 변경해야 할 부분과 이유를 설명합니다"""

        user_prompt = f"""다음 C# 파일을 분석하고 리팩터링 계획을 수립하세요.

파일 경로: {filepath}

파일 전체 내용:
```csharp
{file_content}
```

Git 변경사항 (diff):
```diff
{git_diff if git_diff else "(변경사항 없음 - 신규 파일 또는 미추적 파일)"}
```

다음 항목을 포함하는 리팩터링 계획을 작성하세요:

## 코드 품질 분석
- 현재 코드의 문제점 목록

## CLAUDE.md 컨벤션 위반 여부
- 네이밍 규칙 (PascalCase, _camelCase 등)
- ECS/DOTS 패턴 준수 여부
- BurstCompile 적용 여부

## 리팩터링 계획
- 수정해야 할 항목 (우선순위 포함)
- 각 항목별 수정 이유

## 주의사항
- Coder agent가 구현 시 주의할 점"""

        return self.run_agent("planner", system_prompt, user_prompt)

    def run_reviewer(self, file_content: str, git_diff: str, plan: str, filepath: str) -> str:
        """
        Reviewer Agent
        역할: 계획 검토 및 코드 품질 검증
        제약: 코드를 직접 작성하지 않음
        페르소나: TODO - 추후 구체화
        """
        system_prompt = """당신은 코드 리뷰 및 아키텍처 검증 전문가입니다.
계획의 적절성을 검토하고 코드 품질 문제를 발견하는 것이 역할입니다.

중요 제약:
- 절대 코드를 직접 작성하지 않습니다
- 리뷰 피드백과 승인/거부 의견만 작성합니다
- 추가 발견된 문제점과 계획 보완 사항을 명시합니다"""

        user_prompt = f"""Planner가 수립한 계획을 검토하고 코드를 리뷰하세요.

파일 경로: {filepath}

코드:
```csharp
{file_content}
```

Git 변경사항:
```diff
{git_diff if git_diff else "(변경사항 없음)"}
```

Planner 계획:
{plan}

다음 항목을 포함하는 리뷰 결과를 작성하세요:

## 계획 검토
- 계획이 적절한지 평가
- 누락된 개선사항 있으면 추가

## 코드 리뷰
- Planner가 발견하지 못한 추가 문제점
- 성능 및 메모리 안전성 검토
- ECS/DOTS 패턴 정합성

## 최종 승인
- APPROVED / NEEDS_REVISION
- 승인 또는 수정이 필요한 이유"""

        return self.run_agent("reviewer", system_prompt, user_prompt)

    def run_coder(self, file_content: str, plan: str, review: str, filepath: str) -> str:
        """
        Coder Agent
        역할: 계획 기반 실제 코드 수정
        제약: 계획을 수정하지 않고 구현만 담당
        페르소나: TODO - 추후 구체화
        """
        system_prompt = """당신은 C# Unity ECS/DOTS 구현 전문가입니다.
Planner의 계획과 Reviewer의 피드백을 받아 코드를 구현하는 것이 역할입니다.

중요 제약:
- 계획을 수정하거나 새로운 계획을 세우지 않습니다
- 주어진 계획과 리뷰 피드백에 따라 구현만 담당합니다
- CLAUDE.md 컨벤션을 철저히 준수합니다"""

        user_prompt = f"""Planner 계획과 Reviewer 피드백을 바탕으로 코드를 리팩터링하세요.

파일 경로: {filepath}

원본 코드:
```csharp
{file_content}
```

Planner 계획:
{plan}

Reviewer 피드백:
{review}

다음을 포함하는 리팩터링 결과를 작성하세요:

## 수정된 코드
전체 리팩터링된 코드를 ```csharp 코드블록으로 작성하세요.

## 변경 사항 요약
- 어떤 부분을 왜 수정했는지 목록으로 작성

## 미적용 항목
- 계획 중 적용하지 않은 항목과 이유 (있는 경우)"""

        return self.run_agent("coder", system_prompt, user_prompt)

    # ------------------------------------------------------------------ #
    #  파이프라인 실행                                                      #
    # ------------------------------------------------------------------ #

    def write_atomic(self, path, content):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = f"{path}.tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp, path)

    def review_file(self, filepath: str) -> str:
        """단일 파일 리뷰 파이프라인 실행"""
        print(f"\n{'='*70}")
        print(f"[CS CODE REVIEWER] {filepath}")
        print(f"{'='*70}")

        # 파일 정보 수집
        file_content = self.get_file_content(filepath)
        git_diff = self.get_git_diff(filepath)

        # 1. Planner
        plan = self.run_planner(file_content, git_diff, filepath)
        if not plan:
            print("[오류] Planner 실패 → 중단")
            return None

        # 2. Reviewer
        review = self.run_reviewer(file_content, git_diff, plan, filepath)
        if not review:
            print("[오류] Reviewer 실패 → 중단")
            return None

        # 3. Coder
        result = self.run_coder(file_content, plan, review, filepath)
        if not result:
            print("[오류] Coder 실패 → 중단")
            return None

        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = Path(filepath).stem
        output_file = self.output_dir / f"{timestamp}_{filename}_review.md"

        report = f"""# 코드 리뷰 보고서 — {filename}

**파일**: `{filepath}`
**생성 시간**: {datetime.now().isoformat()}

---

## Planner 분석 및 계획

{plan}

---

## Reviewer 검토 결과

{review}

---

## Coder 리팩터링 결과

{result}
"""

        self.write_atomic(str(output_file), report)
        print(f"\n[저장됨] {output_file}")
        return str(output_file)

    def run(self, target_file: str = None, review_all: bool = False):
        """전체 실행"""
        if target_file:
            self.review_file(target_file)
        elif review_all:
            changed = self.get_changed_cs_files()
            if not changed:
                print("[안내] 변경된 C# 파일이 없습니다.")
                return
            print(f"\n[안내] 변경된 파일 {len(changed)}개 발견:")
            for f in changed:
                print(f"  - {f}")
            for f in changed:
                self.review_file(f)
        else:
            print("사용법:")
            print("  python cs_code_reviewer.py --target Assets/Scripts/Systems/MoveSystem.cs")
            print("  python cs_code_reviewer.py --all")


def main():
    target_file = None
    review_all = False

    if "--target" in sys.argv:
        idx = sys.argv.index("--target")
        if idx + 1 < len(sys.argv):
            target_file = sys.argv[idx + 1]
    elif "--all" in sys.argv:
        review_all = True

    project_root = Path(__file__).parent.parent
    reviewer = CsCodeReviewer(str(project_root))
    reviewer.run(target_file=target_file, review_all=review_all)


if __name__ == "__main__":
    main()
