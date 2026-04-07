# -*- coding: utf-8 -*-
"""
C# Code Reviewer — 6단계 에이전트 파이프라인 (Orchestrator)

파이프라인:
1. Planner: 코드 분석 & 리팩터링 계획
2. Reviewer Loop (최대 3회): 완성도/실현가능성 평가
3. UA1 (사용자 입력): 변경 예정사항 확인
4. Coder: 리팩터링 코드 구현
5. UA2 (사용자 입력): 변경된 코드 최종 확인
6. 파일 적용: 백업 + 원자적 쓰기 + 보고서
"""

import sys
import os
import argparse
import subprocess
import re
import shutil
import json
import io

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# Windows UTF-8 지원
if sys.platform == 'win32':
    try:
        import io
        if not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass


class Logger:
    """간단한 로깅"""

    @staticmethod
    def info(msg: str):
        print(f"[INFO] {msg}")

    @staticmethod
    def success(msg: str):
        print(f"[✓] {msg}")

    @staticmethod
    def error(msg: str):
        print(f"[✗] {msg}", file=sys.stderr)

    @staticmethod
    def warning(msg: str):
        print(f"[!] {msg}")


class UAInputModeManager:
    """사용자 승인 입력 모드 감지 및 처리"""

    def __init__(self, auto_approve: bool):
        self.auto_approve = auto_approve
        self.mode = self._detect_mode()

    def _detect_mode(self) -> str:
        """실행 환경에 따라 입력 모드 감지"""
        if self.auto_approve:
            return "auto_approve"
        elif sys.stdin.isatty():
            return "interactive"
        else:
            return "non_interactive"

    def get_approval(self, stage: str) -> str:
        """사용자 승인 획득 (stage: "UA1" 또는 "UA2")"""
        if self.mode == "auto_approve":
            Logger.info(f"[{stage}] 자동 승인 모드 → 승인")
            return "승인"
        elif self.mode == "interactive":
            choice = input(f"[{stage}] 선택 (승인/거부): ").strip()
            return "승인" if choice == "승인" else "거부"
        else:  # non_interactive
            Logger.warning(f"[{stage}] stdin 없음 (비대화형 모드) - 기본값: 거부")
            return "거부"


class CSCodeReviewer:
    """C# 코드 리뷰 및 리팩터링 파이프라인 Orchestrator"""

    def __init__(self, filepath: Path, auto_approve: bool, project_root: Path):
        self.filepath = filepath
        self.auto_approve = auto_approve
        self.project_root = project_root
        self.ua_manager = UAInputModeManager(auto_approve)

        # 디렉토리 설정
        self.tmp_dir = project_root / "claude_tools" / ".tmp"
        self.output_dir = project_root / "claude_tools" / "review_outputs"
        self.log_dir = project_root / "claude_tools" / ".agent_logs"

        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 파일명
        self.filename = filepath.stem
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run(self) -> bool:
        """전체 파이프라인 실행"""
        try:
            Logger.info(f"대상 파일: {self.filepath}")
            Logger.info(f"프로젝트 루트: {self.project_root}")

            # 파일 존재 확인
            if not self.filepath.exists():
                Logger.error(f"파일을 찾을 수 없음: {self.filepath}")
                return False

            original_code = self.filepath.read_text(encoding='utf-8-sig', errors='replace')

            # Stage 1: Planner
            Logger.info("\n" + "="*80)
            Logger.info("Stage 1: Planner (코드 분석 & 리팩터링 계획)")
            Logger.info("="*80)
            planner_output = self._run_planner()
            if not planner_output:
                Logger.error("Planner 실행 실패")
                return False

            # Stage 2: Reviewer Loop (최대 3회)
            Logger.info("\n" + "="*80)
            Logger.info("Stage 2: Reviewer Loop (최대 3회)")
            Logger.info("="*80)
            reviewer_output = None
            for attempt in range(1, 4):
                Logger.info(f"\n>>> Reviewer 시도 {attempt}/3")
                reviewer_output = self._run_reviewer(planner_output, attempt)
                if not reviewer_output:
                    Logger.error(f"Reviewer 실행 실패 (시도 {attempt})")
                    return False

                # APPROVED 확인
                if "APPROVED" in reviewer_output:
                    Logger.success(f"Reviewer 승인 완료 (시도 {attempt})")
                    break

                # NEEDS_REVISION 확인
                if "NEEDS_REVISION" in reviewer_output:
                    if attempt < 3:
                        Logger.warning(f"Reviewer: 재시도 필요 (시도 {attempt}/3)")
                        # Planner 재작업 진행
                        Logger.info(">>> Planner 재작업 진행 중...")
                        planner_output = self._run_planner()
                        if not planner_output:
                            Logger.error("Planner 재작업 실패")
                            return False
                    else:
                        # 3회차 NEEDS_REVISION
                        Logger.error("최대 재시도 횟수 도달 (3/3)")
                        self._save_failed_report(planner_output, reviewer_output, original_code)
                        return False

            if not reviewer_output:
                Logger.error("Reviewer 출력 없음")
                return False

            # Stage 3: User Approval 1
            Logger.info("\n" + "="*80)
            Logger.info("Stage 3: User Approval 1 (변경 예정사항 확인)")
            Logger.info("="*80)
            ua1_approved = self._user_approval_1(planner_output, reviewer_output)
            if not ua1_approved:
                Logger.warning("User Approval 1 거부 → 파이프라인 중단")
                return False

            # Stage 4: Coder
            Logger.info("\n" + "="*80)
            Logger.info("Stage 4: Coder (리팩터링 코드 구현)")
            Logger.info("="*80)
            coder_output = self._run_coder(planner_output, reviewer_output)
            if not coder_output:
                Logger.error("Coder 실행 실패")
                return False

            # 코드 추출
            refactored_code = self._extract_code_from_output(coder_output)
            if not refactored_code:
                Logger.error("Coder 출력에서 코드 추출 실패")
                return False

            # Stage 5: User Approval 2
            Logger.info("\n" + "="*80)
            Logger.info("Stage 5: User Approval 2 (변경된 코드 최종 확인)")
            Logger.info("="*80)
            ua2_approved = self._user_approval_2(original_code, refactored_code, coder_output)
            if not ua2_approved:
                Logger.warning("User Approval 2 거부 → 변경사항 폐기")
                return False

            # Stage 6: 파일 적용
            Logger.info("\n" + "="*80)
            Logger.info("Stage 6: 파일 적용 (백업 + 쓰기 + 보고서)")
            Logger.info("="*80)
            if not self._apply_file(refactored_code, original_code, planner_output,
                                   reviewer_output, coder_output):
                Logger.error("파일 적용 실패")
                return False

            Logger.success("\n" + "="*80)
            Logger.success("✅ 리팩터링 완료!")
            Logger.success("="*80)
            return True

        except Exception as e:
            Logger.error(f"예상치 못한 에러: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _run_planner(self) -> Optional[str]:
        """Stage 1: Planner 실행

        파일 경로만 전달, 에이전트가 Read 도구로 직접 읽음 (토큰 절약)
        """
        try:
            # git diff 수집
            git_diff = self._get_git_diff()

            # git diff를 임시 파일에 저장 (크면 경로 전달)
            git_diff_path = None
            if git_diff and len(git_diff) > 500:
                git_diff_path = self.tmp_dir / f"{self.timestamp}_git_diff.txt"
                git_diff_path.write_text(git_diff, encoding='utf-8')

            # User Prompt: 파일 경로만 (에이전트가 Read로 읽음)
            user_prompt = f"""대상 파일: {self.filepath}

위 파일을 Read 도구로 읽어 8가지 기준으로 분석하고 리팩터링 계획을 수립하세요."""

            if git_diff:
                if git_diff_path:
                    user_prompt += f"\n\nGit 변경사항: {git_diff_path} (Read 도구로 읽으세요)"
                else:
                    user_prompt += f"\n\nGit 변경사항:\n{git_diff}"

            # Planner 실행
            output = self._run_subprocess_agent(
                "planner",
                user_prompt,
                timeout=300
            )

            if output:
                # 임시 파일에 저장
                tmp_path = self.tmp_dir / f"{self.timestamp}_planner.md"
                tmp_path.write_text(output, encoding='utf-8')
                Logger.success(f"Planner 출력 저장: {tmp_path}")

            return output

        except Exception as e:
            Logger.error(f"Planner 실행 중 에러: {e}")
            return None

    def _run_reviewer(self, planner_output: str, attempt: int) -> Optional[str]:
        """Stage 2: Reviewer 실행

        파일 경로와 Planner 계획 경로만 전달 (토큰 절약)
        """
        try:
            # Planner 계획을 임시 파일에 저장
            planner_path = self.tmp_dir / f"{self.timestamp}_planner.md"
            planner_path.write_text(planner_output, encoding='utf-8')

            # User Prompt: 파일 경로만 (에이전트가 Read로 읽음)
            user_prompt = f"""대상 파일: {self.filepath}
Planner 계획 파일: {planner_path}

위 두 파일을 Read 도구로 읽어 완성도(1-10)와 실현가능성(1-10)을 평가하세요."""

            # Reviewer 실행
            output = self._run_subprocess_agent(
                "reviewer",
                user_prompt,
                timeout=300
            )

            # Reviewer 출력을 임시 파일에 저장 (추적성 강화)
            if output:
                tmp_path = self.tmp_dir / f"{self.timestamp}_reviewer_{attempt}.md"
                tmp_path.write_text(output, encoding='utf-8')
                Logger.info(f"Reviewer 임시 파일 저장: {tmp_path}")

            return output

        except Exception as e:
            Logger.error(f"Reviewer 실행 중 에러: {e}")
            return None

    def _run_coder(self, planner_output: str, reviewer_output: str) -> Optional[str]:
        """Stage 4: Coder 실행

        파일 경로와 계획/피드백 경로만 전달 (토큰 절약)
        """
        try:
            # 계획과 피드백을 임시 파일에 저장
            planner_path = self.tmp_dir / f"{self.timestamp}_planner.md"
            planner_path.write_text(planner_output, encoding='utf-8')

            reviewer_path = self.tmp_dir / f"{self.timestamp}_reviewer.md"
            reviewer_path.write_text(reviewer_output, encoding='utf-8')

            # User Prompt: 파일 경로만 (에이전트가 Read로 읽음)
            user_prompt = f"""대상 파일: {self.filepath}
Planner 계획 파일: {planner_path}
Reviewer 피드백 파일: {reviewer_path}

위 파일들을 Read 도구로 읽고 계획과 피드백을 반영하여 C# 리팩터링 코드를 작성하세요."""

            # Coder 실행 (Read,Glob,Grep,Edit,Write 도구 허용)
            # 타임아웃: 600초 → 900초 (15분)
            # 이유: Planner/Reviewer 완료 후 실패 방지, 복잡한 리팩터링 지원
            # 토큰 비용: 거의 변화 없음 (에이전트가 빨리 끝나면 타임아웃은 미사용)
            output = self._run_subprocess_agent(
                "coder",
                user_prompt,
                timeout=900,
                allowed_tools="Read,Glob,Grep,Edit,Write"
            )

            return output

        except Exception as e:
            Logger.error(f"Coder 실행 중 에러: {e}")
            return None

    def _run_subprocess_agent(self, agent_name: str, user_prompt: str, timeout: int, allowed_tools: str = "Read,Glob,Grep") -> Optional[str]:
        """Claude CLI subprocess 호출 (stdin + --system-prompt-file)

        - System prompt: --system-prompt-file로 .claude/agents/{agent_name}.md 로드
        - User prompt: stdin으로 전달 (복잡한 프롬프트 안정적 전달)
        - allowed_tools: 에이전트별 도구 권한 (기본값: Read,Glob,Grep)
        """
        try:
            env = os.environ.copy()
            env["CLAUDE_CODE_GIT_BASH_PATH"] = r"D:\Git\usr\bin\bash.exe"

            # System prompt 경로 결정
            system_prompt_path = self.project_root / ".claude" / "agents" / f"{agent_name}.md"
            if not system_prompt_path.exists():
                # Fallback: docs/prompts/ 확인
                system_prompt_path = self.project_root / "docs" / "prompts" / f"{agent_name}.md"
                if not system_prompt_path.exists():
                    Logger.error(f"System prompt 파일을 찾을 수 없음: {agent_name}")
                    return None

            # Claude CLI 명령: stdin으로 user_prompt 전달, --system-prompt-file로 system prompt 로드
            # Windows 경로에 공백이 있을 수 있으므로 큰따옴표로 감싸기
            system_prompt_str = str(system_prompt_path)
            cmd_str = f'claude -p --system-prompt-file "{system_prompt_str}" --model claude-haiku-4-5-20251001 --allowedTools {allowed_tools} --permission-mode bypassPermissions'

            Logger.info(f"Claude CLI 호출: {agent_name} (timeout={timeout}s)")
            Logger.info(f"System prompt: {system_prompt_path}")
            Logger.info(f"user_prompt 길이: {len(user_prompt)}")

            result = subprocess.run(
                cmd_str,
                input=user_prompt.encode('utf-8'),
                capture_output=True,
                timeout=timeout,
                cwd=str(self.project_root),
                env=env,
                shell=True  # Windows PATH 검색 지원
            )

            stdout = result.stdout.decode('utf-8', errors='replace')
            stderr = result.stderr.decode('utf-8', errors='replace')

            # 에러 로깅
            if stderr:
                log_path = self.log_dir / f"{agent_name}_{self.timestamp}.log"
                log_path.write_text(f"STDERR:\n{stderr}", encoding='utf-8')

            if result.returncode != 0:
                Logger.error(f"{agent_name} 실패 (returncode={result.returncode})")
                Logger.error(f"stderr: {stderr[:200]}")
                return None

            return stdout

        except subprocess.TimeoutExpired:
            Logger.error(f"{agent_name} 타임아웃 ({timeout}초)")
            return None
        except Exception as e:
            Logger.error(f"{agent_name} 호출 중 에러: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _user_approval_1(self, planner_output: str, reviewer_output: str) -> bool:
        """Stage 3: User Approval 1"""
        print("\n" + "="*80)
        print("변경 예정 사항 (User Approval 1)")
        print("="*80)
        print(f"\n파일: {self.filepath}\n")
        print(planner_output)
        print(f"\n{reviewer_output}")
        print("\n" + "="*80)

        choice = self.ua_manager.get_approval("UA1")
        return choice == "승인"

    def _user_approval_2(self, original_code: str, refactored_code: str,
                        coder_output: str) -> bool:
        """Stage 5: User Approval 2"""
        print("\n" + "="*80)
        print("변경된 코드 확인 (User Approval 2)")
        print("="*80)
        print(f"\n파일: {self.filepath}\n")

        print("변경 전 (원본):")
        print("```csharp")
        print(original_code[:500] + "..." if len(original_code) > 500 else original_code)
        print("```\n")

        print("변경 후 (리팩터링):")
        print("```csharp")
        print(refactored_code[:500] + "..." if len(refactored_code) > 500 else refactored_code)
        print("```\n")

        print("Coder 변경 사항 요약:")
        print(coder_output)
        print("\n" + "="*80)

        choice = self.ua_manager.get_approval("UA2")
        return choice == "승인"

    def _apply_file(self, refactored_code: str, original_code: str,
                   planner_output: str, reviewer_output: str,
                   coder_output: str) -> bool:
        """Stage 6: 파일 적용"""
        try:
            # 백업
            backup_path = self.filepath.with_suffix('.backup.cs')
            shutil.copy2(self.filepath, backup_path)
            Logger.success(f"백업 저장: {backup_path}")

            # 원자적 쓰기
            tmp_path = str(self.filepath) + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                f.write(refactored_code)
            os.replace(tmp_path, str(self.filepath))
            Logger.success(f"파일 업데이트: {self.filepath}")

            # 최종 보고서 생성
            report_path = self._save_final_report(
                original_code, refactored_code, planner_output,
                reviewer_output, coder_output, backup_path
            )
            Logger.success(f"최종 보고서: {report_path}")

            return True

        except Exception as e:
            Logger.error(f"파일 적용 중 에러: {e}")
            return False

    def _extract_code_from_output(self, output: str) -> Optional[str]:
        """Coder 출력에서 코드 추출"""
        pattern = r'```csharp\s*\n(.*?)\n```'
        match = re.search(pattern, output, re.DOTALL)

        if not match:
            Logger.error("코드 블록을 찾을 수 없음 (```csharp...``` 형식)")
            return None

        code = match.group(1).strip()

        # 최소 검증
        if len(code) < 50:
            Logger.error(f"코드가 너무 짧음 ({len(code)} 자)")
            return None

        # C# 특성 확인
        if not any(marker in code for marker in ['using', 'class', 'public', 'private', 'struct']):
            Logger.warning("C# 코드 특성이 부족함 (using/class/public 등)")

        return code

    def _save_final_report(self, original_code: str, refactored_code: str,
                          planner_output: str, reviewer_output: str,
                          coder_output: str, backup_path: Path) -> Path:
        """최종 보고서 저장"""
        report_path = self.output_dir / f"{self.timestamp}_{self.filename}_review.md"

        # 변경 통계
        original_lines = original_code.count('\n')
        refactored_lines = refactored_code.count('\n')
        added = max(0, refactored_lines - original_lines)
        deleted = max(0, original_lines - refactored_lines)

        content = f"""# C# 코드 리뷰 최종 보고서

## 메타데이터
- **파일**: {self.filepath}
- **생성 시각**: {datetime.now().isoformat()}
- **백업**: {backup_path}

## Planner 분석 결과

{planner_output}

---

## Reviewer 평가 결과

{reviewer_output}

---

## Coder 구현 결과

{coder_output}

---

## 변경 통계
- **원본 라인**: {original_lines}
- **리팩터링 라인**: {refactored_lines}
- **추가된 라인**: {added}
- **삭제된 라인**: {deleted}

---

## 원본 코드
```csharp
{original_code}
```

---

## 리팩터링된 코드
```csharp
{refactored_code}
```
"""

        report_path.write_text(content, encoding='utf-8')
        return report_path

    def _save_failed_report(self, planner_output: str, reviewer_output: str,
                           original_code: str) -> Path:
        """3회 실패 보고서 저장"""
        report_path = self.output_dir / f"FAILED_{self.timestamp}_{self.filename}_planner_review_summary.md"

        content = f"""# Planner 재시도 실패 보고서

## 메타데이터
- **파일**: {self.filepath}
- **생성 시각**: {datetime.now().isoformat()}
- **상태**: Planner-Reviewer 루프 3회 연속 실패

## 최종 Planner 계획 (3회차)

{planner_output}

---

## Reviewer 최종 평가 (3회차)

{reviewer_output}

---

## 권장 사항

### 원인 분석
Planner 계획이 3회 연속 거부된 주요 이유:
- 각 항목의 변경 위치가 명확하지 않음
- 현재 상태 설명이 불충분함
- 변경 방향이 너무 추상적임
- Coder가 구현하기에 지시사항이 모호함

### 다음 단계
1. Planner 계획 수동 개선 (위의 "개선 필요 사항" 참고)
2. 다시 실행: `python cs_code_reviewer.py --target {self.filepath}`
3. 또는 자동 리팩터링 포기 후 수동 검토

---

## 첨부: 원본 코드
```csharp
{original_code}
```
"""

        report_path.write_text(content, encoding='utf-8')
        return report_path

    def _get_git_diff(self) -> str:
        """git diff 수집"""
        try:
            result = subprocess.run(
                ["git", "diff", "--", str(self.filepath)],
                capture_output=True,
                cwd=str(self.project_root)
            )
            return result.stdout.decode('utf-8', errors='replace') if result.returncode == 0 else ""
        except Exception as e:
            Logger.warning(f"git diff 수집 실패: {e}")
            return ""

    def _load_agent_prompt(self, agent_name: str) -> str:
        """System Prompt 로드 (fallback)"""
        paths = [
            self.project_root / ".claude" / "agents" / f"{agent_name}.md",
            self.project_root / "docs" / "prompts" / f"{agent_name}.md",
        ]

        for path in paths:
            if path.exists():
                Logger.info(f"System Prompt 로드: {path}")
                return path.read_text(encoding='utf-8')

        raise FileNotFoundError(
            f"System Prompt를 찾을 수 없음: {agent_name}\n"
            f"검색 경로: {', '.join(str(p) for p in paths)}"
        )


def main():
    """메인 진입점"""
    parser = argparse.ArgumentParser(
        description="C# 코드 리뷰 및 리팩터링 파이프라인"
    )
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="대상 파일 경로 (예: Assets/Scripts/Systems/MoveSystem.cs)"
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="모든 User Approval 단계에서 자동 승인"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="프로젝트 루트 (기본값: 현재 디렉토리)"
    )

    args = parser.parse_args()

    # 프로젝트 루트 결정
    if args.project_root:
        project_root = Path(args.project_root)
    else:
        project_root = Path.cwd()

    # 대상 파일 경로 결정
    target_path = Path(args.target)
    if not target_path.is_absolute():
        target_path = project_root / target_path

    # 리뷰어 실행
    reviewer = CSCodeReviewer(target_path, args.auto_approve, project_root)
    success = reviewer.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
