#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Request Orchestrator — 2-Stage Pipeline

Stage 1: request_to_plan_todo.py (5-agent pipeline)
  Convert user request → Plan & Todo document
  Planning → Review → Revised Planning → Todo → Keyword

Stage 2: Claude CLI 3-phase orchestration
  Plan & Todo → Planning validation → Implementation → Review

Usage:
    python request_orchestrator.py "요청 내용" [--type code|document|architecture|system]

Output:
    claude_tools/orchestrator_outputs/{timestamp}_{keyword}_orchestration.md
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import io

# Fix Windows console encoding (only if not already wrapped)
if sys.platform == 'win32' and not isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass  # Already wrapped or cannot wrap


class RequestOrchestrator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.output_dir = Path("claude_tools") / "orchestrator_outputs"
        self.output_dir.mkdir(exist_ok=True)

    def write_atomic(self, path, content):
        """원자적 파일 쓰기"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = f"{path}.tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp_path, path)

    def stage1_generate_plan_todo(self, user_request: str) -> str:
        """
        Stage 1: request_to_plan_todo 실행 (5-agent pipeline)
        User request → Plan & Todo document
        """
        print("\n" + "="*70)
        print("[1단계] 요청 → 계획 & 할일 생성 (5-agent pipeline)")
        print("="*70)
        print(f"\n사용자 요청:\n{user_request}\n")

        # request_to_plan_todo.py import 및 실행
        sys.path.insert(0, str(Path(__file__).parent))
        from request_to_plan_todo import SafeOrchestrator

        orchestrator = SafeOrchestrator(str(self.project_root))
        result = orchestrator.run_workflow(user_request)

        if not result:
            print("[오류] 계획 & 할일 생성 실패")
            return None

        print(f"\n[완료] 계획 & 할일 생성됨: {result}")

        with open(result, 'r', encoding='utf-8') as f:
            plan_todo_content = f.read()

        return plan_todo_content

    def stage2_orchestrate_implementation(self, user_request: str, plan_todo_content: str, output_type: str = "document") -> str:
        """
        Stage 2: Claude CLI 3-phase orchestration
        Plan & Todo → Implementation → Review
        """
        print("\n" + "="*70)
        print("[2단계] 계획 & 할일 → 오케스트레이션 (계획→구현→검토)")
        print("="*70)

        orchestration_prompt = f"""당신은 claude_subprocess_api.md 지침을 따르는 전문 오케스트레이터입니다.

원본 사용자 요청:
{user_request}

생성된 계획 및 할일:
{plan_todo_content}

## 지시사항: 3단계 오케스트레이션 패턴을 따르세요.

### 1단계: 계획 검증
위 문서의 계획을 검증하고 정제하세요.
- 계획의 실행 가능성 확인
- 누락된 부분 확인
- 필요한 조정사항 파악
결과: 정제된 계획 및 조정 사항 (있으면 명시)

### 2단계: 구현
정제된 계획을 기반으로 실제 산출물을 생성하세요.
산출물 타입: {output_type}

타입별 생성 기준:
- "code": 깔끔하고 문서화된 코드 (테스트 포함)
- "document": 계획을 따르는 포괄적인 마크다운 문서
- "architecture": 시스템 아키텍처 다이어그램 및 상세 설계
- "system": API 스펙과 배포 가이드가 포함된 시스템 설계

포함 필수 사항:
- 명확한 파일 구조
- 계획과 일치하는 구현 세부사항
- 테스트 케이스 또는 검증 기준
- 주석과 설명 문서

### 3단계: 검토
구현이 다음을 만족하는지 확인하세요:
1. 원본 사용자 요청과의 일치 ✓
2. 계획 및 할일 구조와의 일치 ✓
3. 품질 기준 충족 ✓
4. 완성도 ✓

최종 검토 결과:
- 완료된 내용
- 품질 평가
- 누락되거나 개선 가능한 부분

---

지금 바로 오케스트레이션을 시작하세요:
1단계: 계획을 검증하세요
2단계: 산출물을 구현하세요
3단계: 결과를 검토하세요
"""

        print("\n>> Claude CLI로 오케스트레이션 실행 중...")

        result = subprocess.run(
            [
                "claude",
                "-p",
                orchestration_prompt,
                "--model",
                "claude-haiku-4-5-20251001"
            ],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300,
            shell=False
        )

        if result.returncode != 0:
            print(f"\n[오류] 오케스트레이션 실패")
            if result.stderr:
                print(f"에러: {result.stderr[:300]}")
            return None

        orchestration_result = result.stdout

        print(f"\n[완료] 오케스트레이션 완료")
        print(f"\n결과 미리보기 (처음 500자):\n{orchestration_result[:500]}...")

        return orchestration_result

    def save_orchestration_output(self, user_request: str, plan_todo_content: str, orchestration_result: str, output_type: str):
        """최종 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 파일명 keyword 추출 (Plan & Todo 문서 제목에서)
        keyword = "output"
        for line in plan_todo_content.split('\n'):
            if line.startswith('# '):
                keyword = line.replace('# ', '').split(' — ')[0].lower()
                keyword = ''.join(c for c in keyword if c.isalnum() or c == '_')[:20]
                break

        output_file = self.output_dir / f"{timestamp}_{keyword}_orchestration.md"

        final_output = f"""# 오케스트레이션 결과 — {timestamp}

## 원본 사용자 요청
{user_request}

---

## 생성된 계획 및 할일 (1단계: 5-agent pipeline)
{plan_todo_content}

---

## 오케스트레이션 산출물 (2단계: 계획→구현→검토)

{orchestration_result}

---

## 메타데이터
- 생성 시간: {datetime.now().isoformat()}
- 산출물 타입: {output_type}
- 파이프라인: request_orchestrator
  - 1단계: request_to_plan_todo (5-agent pipeline)
  - 2단계: Claude CLI 3-phase orchestration
"""

        self.write_atomic(str(output_file), final_output)
        return str(output_file)

    def run(self, user_request: str, output_type: str = "document") -> str:
        """전체 오케스트레이션 실행"""
        print("\n" + "="*70)
        print("[요청 오케스트레이터] 전체 파이프라인")
        print("="*70)

        plan_todo_content = self.stage1_generate_plan_todo(user_request)
        if not plan_todo_content:
            return None

        orchestration_result = self.stage2_orchestrate_implementation(
            user_request, plan_todo_content, output_type
        )
        if not orchestration_result:
            return None

        output_file = self.save_orchestration_output(
            user_request, plan_todo_content, orchestration_result, output_type
        )

        print("\n" + "="*70)
        print("[완료] 오케스트레이션 파이프라인 완성")
        print("="*70)
        print(f"\n[산출물] 저장됨: {output_file}")

        return output_file


def main():
    """메인 엔트리 포인트"""
    if len(sys.argv) < 2:
        print("사용법: python request_orchestrator.py '<요청 내용>' [--type code|document|architecture|system]")
        print("\n예시:")
        print("  python request_orchestrator.py '사용자 관리 REST API 만들기' --type code")
        print("  python request_orchestrator.py '시스템 아키텍처 문서화' --type document")
        sys.exit(1)

    user_request = sys.argv[1]

    output_type = "document"
    if "--type" in sys.argv:
        idx = sys.argv.index("--type")
        if idx + 1 < len(sys.argv):
            output_type = sys.argv[idx + 1]

    project_root = Path(__file__).parent.parent

    orchestrator = RequestOrchestrator(str(project_root))
    result = orchestrator.run(user_request, output_type)

    if result:
        print(f"\n[완료] 전체 오케스트레이션 완료:")
        print(f"     산출물: {result}\n")
        sys.exit(0)
    else:
        print("\n[오류] 오케스트레이션 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
