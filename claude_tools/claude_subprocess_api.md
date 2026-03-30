# Claude Subprocess API — Agentic Workflow 안전 가이드

## 개요

이 문서는 Claude CLI를 subprocess로 호출하여 3단계 에이전트 파이프라인(Plan → Implementation → Review)을 안전하게 실행하는 방법을 정의합니다.

---

## Safety Principles (안전 원칙)

### 1. Input Sanitization — 보안

**위험**: Shell metacharacters (`;`, `|`, `&&`, `$()` 등)가 포함된 사용자 입력이 subprocess 인자로 전달될 때 command injection 발생 가능.

**원칙:**
- 사용자 입력을 `shlex.quote()`로 항상 이스케이프
- 프롬프트 문자열에 백슬래시, 따옴표, 개행 문자 안전하게 처리
- 절대 user input을 shell 명령어로 직접 조합하지 말 것

**구현 예시:**
```python
import shlex

# ❌ 위험한 방식
cmd = f'claude -p "{user_input}"'  # command injection 위험

# ✅ 안전한 방식
cmd = ["claude", "-p", user_input]  # 리스트 형식 (자동 이스케이프)
subprocess.run(cmd, ...)
```

---

### 2. Data Integrity — 데이터 무결성

**위험**: 에이전트 간 파일 전달 중 파일이 손상되거나, 동시에 여러 에이전트가 같은 파일에 쓸 때 데이터 일관성 문제.

**원칙:**
- 파일 쓰기 전에 원본 파일의 해시(SHA256) 계산 및 기록
- 파일 읽기 후 해시 검증으로 무결성 확인
- 동시성 제어: 에이전트는 **순차 실행만** (병렬 실행 금지)
- 파일 쓰기는 원자적(atomic)으로: 임시 파일 → rename

**구현 예시:**
```python
import hashlib

def hash_file(path):
    """파일의 SHA256 해시 계산"""
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def write_atomic(path, content):
    """원자적 파일 쓰기"""
    tmp_path = f"{path}.tmp"
    with open(tmp_path, 'w') as f:
        f.write(content)
    os.replace(tmp_path, path)  # atomic rename

# 사용
original_hash = hash_file("plan.md")
plan_content = read_plan()
plan_hash = hash_file("plan.md")
assert original_hash == plan_hash, "Data integrity check failed"
```

---

### 3. Sensitive Output Handling — 출력 추적

**위험**: 에이전트 출력(stdout)에 디버그 로그, 에러 메시지, API 토큰 같은 민감 정보가 포함될 때, 이것이 다음 에이전트의 입력(프롬프트)으로 그대로 포함되면 정보 유출.

**원칙:**
- 에이전트 출력을 그대로 다음 에이전트에게 전달하지 말 것
- 필요한 부분(예: plan.md의 특정 섹션)만 명시적으로 추출
- 출력 로그는 별도 파일에 저장 (프롬프트에 포함 X)
- 민감 정보 필터링 (토큰, 경로, 내부 구조 관련 정보)

**구현 예시:**
```python
def extract_safe_output(agent_output, marker_start, marker_end):
    """안전한 출력 추출 (마커 기반)"""
    try:
        start = agent_output.find(marker_start)
        end = agent_output.find(marker_end, start)
        if start != -1 and end != -1:
            return agent_output[start + len(marker_start):end].strip()
    except:
        pass
    return None

# 사용: Plan Agent 출력에서 실제 plan.md 내용만 추출
plan_content = extract_safe_output(plan_output, "# Plan:", "---")
```

---

### 4. State Management — 상태 관리

**위험**: 에이전트가 중복 실행되거나, 실행 상태가 불명확해서 일부만 완료된 상태에서 다음 단계가 진행되는 경우.

**원칙:**
- 각 에이전트 실행의 상태(pending, running, completed, failed)를 별도 파일에 추적
- 동일 기능에 대해 2회 이상 실행되지 않도록 idempotency 체크
- 상태 파일 형식: `{feature_name}.state.json`

**구현 예시:**
```python
import json
from pathlib import Path

def load_state(feature_name):
    """실행 상태 로드"""
    state_file = Path(f".orchestrator_state/{feature_name}.state.json")
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {"plan": "pending", "impl": "pending", "review": "pending"}

def save_state(feature_name, phase, status):
    """실행 상태 저장"""
    state_file = Path(f".orchestrator_state/{feature_name}.state.json")
    state_file.parent.mkdir(exist_ok=True)
    state = load_state(feature_name)
    state[phase] = status
    state_file.write_text(json.dumps(state, indent=2))

# 사용
state = load_state("turn_system")
if state["plan"] == "completed":
    print("Plan already completed, skipping...")
else:
    run_plan_agent(...)
    save_state("turn_system", "plan", "completed")
```

---

### 5. Failure Recovery & Handoff — 실패 복구 및 핸드오프

**위험**: 에이전트 타임아웃, 에러, 리뷰 실패 시 부분 변경된 코드가 남거나, 같은 문제가 반복 발생.

**원칙:**
- Implementation Agent 실패 시 `git reset --hard` 롤백
- 실패 지점, 에러 메시지, 문제 원인을 `fail_report_handoff` 문서로 생성
- fail_report는 다음 재시도 시 에이전트가 참고하여 같은 실수 방지
- fail_report 파일명: `YYMMDD_HHMM_fail_report_{number}.md` (연번)

**구조:**
```
fail_report_handoffs/
├── 240330_1430_fail_report_1.md   (첫 번째 실패)
├── 240330_1445_fail_report_2.md   (두 번째 실패)
└── 240331_0900_fail_report_3.md
```

**fail_report 형식:**
```markdown
# Fail Report — [기능명]

## 메타데이터
- **Timestamp**: 2024-03-30 14:30
- **Feature**: turn_system
- **Phase**: implementation
- **Agent**: Implementation Agent
- **Attempt**: 1

## 실패 원인
[구체적 에러 메시지 또는 문제 설명]

## 에러 발생 지점
- 파일: Assets/Scripts/Components/EnergyComponent.cs
- 라인: 15
- 코드 내용: [문제 코드]

## 분석
[무엇이 잘못되었는가]

## 예방 방법
[다음 시도 시 이렇게 하면 방지 가능]

## 참고
- Related Fail Report: fail_report_handoffs/240330_1400_fail_report_1.md
- CLAUDE.md 컨벤션: [관련 섹션]
```

**구현 예시:**
```python
import os
from datetime import datetime

def generate_fail_report(feature_name, phase, error_msg, attempted_code=""):
    """실패 보고서 자동 생성"""
    # 기존 fail_report 개수 세기
    fail_dir = Path("fail_report_handoffs")
    fail_dir.mkdir(exist_ok=True)
    existing = len(list(fail_dir.glob(f"*_fail_report_*.md")))
    report_num = existing + 1

    # 파일명: YYMMDD_HHMM_fail_report_{number}.md
    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    report_path = fail_dir / f"{timestamp}_fail_report_{report_num}.md"

    # 보고서 내용
    content = f"""# Fail Report — {feature_name}

## 메타데이터
- **Timestamp**: {datetime.now().isoformat()}
- **Feature**: {feature_name}
- **Phase**: {phase}
- **Report Number**: {report_num}

## 실패 원인
{error_msg}

## 에러 발생 지점
```
{attempted_code}
```

## 다음 시도 시 확인사항
1. CLAUDE.md 컨벤션 재검토
2. 기존 fail_report 참고 ({report_num - 1}번 보고서가 있다면)
3. 해당 에러 메시지 전체를 에이전트 프롬프트에 포함

---
**Generated at**: {datetime.now()}
"""

    report_path.write_text(content)
    return str(report_path)

def rollback_changes(feature_name):
    """git 변경사항 롤백"""
    subprocess.run(["git", "reset", "--hard", "HEAD"], check=True)
    print(f"✅ Git changes rolled back for {feature_name}")
```

**실제 워크플로우 통합:**
```python
def run_workflow_with_recovery(user_request):
    """실패 복구 로직이 포함된 워크플로우"""

    feature_name = "extracted_feature_name"  # 사용자 요청에서 추출

    # ... Plan Agent 실행 (일반적으로 읽기만이라 실패 가능성 낮음) ...

    # Implementation Agent 실행 + 실패 처리
    try:
        impl_output = run_agent("implementation", ...)
        if not impl_output:
            # 실패
            error_msg = "Implementation Agent returned empty output"
            report = generate_fail_report(feature_name, "implementation", error_msg)
            rollback_changes(feature_name)
            print(f"❌ Implementation failed. Report: {report}")
            return False
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        report = generate_fail_report(feature_name, "implementation", error_msg)
        rollback_changes(feature_name)
        print(f"❌ Implementation crashed. Report: {report}")
        return False

    # Review Agent 실행 (실패하면 코드는 이미 커밋되었으므로 별도 처리)
    review_output = run_agent("review", ...)
    if "REVIEW PASSED" not in review_output:
        # 리뷰 실패 → fail_report 생성만 (코드 롤백 X)
        error_msg = f"Review found issues:\n{review_output}"
        report = generate_fail_report(feature_name, "review", error_msg)
        print(f"⚠️ Review failed. Report: {report}")
        return False

    return True
```

---

## Claude CLI 레퍼런스

### 기본 호출 형식

```bash
claude [OPTIONS] [PROMPT]
```

### 주요 옵션

| 옵션 | 약자 | 설명 | 예시 |
|------|------|------|------|
| `--print` | `-p` | 비인터랙티브 모드로 실행 (응답을 stdout으로 출력) | `claude -p "..."` |
| `--system-prompt` | `-s` | 시스템 프롬프트 설정 (페르소나 정의) | `-s "You are a senior architect..."` |
| `--model` | `-m` | 사용할 모델 지정 | `-m claude-opus-4-6` |
| `--output-format` | | 출력 형식 지정 | `--output-format json` |
| `--allowedTools` | | 에이전트가 사용할 수 있는 도구 목록 | `--allowedTools "Edit,Write,Read,Bash"` |
| `--cwd` | | 작업 디렉토리 설정 | `--cwd /path/to/project` |

---

## 에이전트 그룹 정의

### 구조: Plan → Implementation → Review

세 에이전트는 순차 파이프라인으로 동작하며, 각 단계의 출력이 다음 단계의 입력이 됩니다.

```
┌─────────────────────┐
│   User Request      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│  [1] Plan Agent (Architect)     │
│  → Analyze & Design              │
│  → Output: plan.md               │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ [2] Implementation Agent        │
│  → Implement (plan.md as input)  │
│  → Output: Code Changes          │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  [3] Review Agent (QA/Architect)│
│  → Verify & Review               │
│  → Output: review.md             │
└─────────────────────────────────┘
```

---

## 에이전트 정의

### 1️⃣ Plan Agent — 시니어 ECS 아키텍트

**페르소나:** 시니어 소프트웨어 아키텍트이자 Unity ECS/DOTS 전문가. 10년 이상의 게임 개발 경험과 대규모 시스템 설계 경험.

**역할:**
- 사용자 요청 분석
- 기존 코드 및 아키텍처 리뷰
- 구현 전략 수립 (태스크 분해, 접근법 선택)
- 위험 요소 및 주의사항 도출
- `plan.md` 문서 작성

**Input:** 사용자 요청 설명

**Output: `plan.md`**
```markdown
# Plan: [기능명]

## 요구사항 분석
- [분석 내용]

## 설계 접근법
- [접근법 설명]

## 구현 태스크
1. [태스크 1]
2. [태스크 2]

## 주의사항
- [주의사항 1]
```

---

### 2️⃣ Implementation Agent — ECS/DOTS 전문 개발자

**페르소나:** 숙련된 C# 게임 개발자이자 DOTS/ECS 시스템 전문가. Burst 컴파일, NativeContainer, SystemAPI를 능숙하게 다룸.

**역할:**
- Plan 문서 해석
- 설계에 따른 코드 구현
- CLAUDE.md 컨벤션 준수 (PascalCase, IComponentData, ISystem, BurstCompile 등)
- 실제 코드 변경 (Edit, Write, Bash를 통해 파일 수정)

**Input:** Plan Agent가 생성한 plan.md

**Output:** 실제 코드 변경 (Assets/Scripts/ 하위)

---

### 3️⃣ Review Agent — 코드 품질 및 아키텍처 검토자

**페르소나:** 경험 많은 코드 리뷰어이자 아키텍처 검증 전문가. 컨벤션 준수, 성능 특성, 보안, ECS 패턴 정합성을 철저히 검증.

**역할:**
- Implementation Agent의 코드 검증
- CLAUDE.md 컨벤션 준수 여부 확인
- ECS/DOTS 패턴 정합성 검증
- 성능 및 메모리 안전성 검토

**Input:** 구현된 코드 (git diff, 파일 내용)

**Output: `review.md`**
```markdown
# Code Review: [기능명]

## ✅ 통과 항목
- [통과한 항목 1]

## ⚠️ 개선 필요
- [문제 1]: [설명] → [권고사항]

## 📋 체크리스트
- [x] CLAUDE.md 컨벤션 준수
- [x] ECS 패턴 정합성
```

---

## Python Orchestrator 패턴

### 기본 구조

```python
#!/usr/bin/env python3
"""
Agentic Orchestrator for Sweepers in ECS (안전 원칙 포함)
Plan Agent → Implementation Agent → Review Agent
"""

import subprocess
import json
import sys
import hashlib
import os
from pathlib import Path
from datetime import datetime

class SafeAgenticOrchestrator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.claude_bin = "claude"
        self.state_dir = Path(".orchestrator_state")
        self.fail_dir = Path("fail_report_handoffs")
        self.state_dir.mkdir(exist_ok=True)
        self.fail_dir.mkdir(exist_ok=True)

    def hash_file(self, path):
        """파일 무결성 검사용 해시"""
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def write_atomic(self, path, content):
        """원자적 파일 쓰기 (data integrity)"""
        tmp_path = f"{path}.tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp_path, path)

    def save_state(self, feature_name, phase, status):
        """상태 저장 (state management)"""
        state_file = self.state_dir / f"{feature_name}.state.json"
        state = json.loads(state_file.read_text()) if state_file.exists() else {}
        state[phase] = status
        state_file.write_text(json.dumps(state, indent=2))

    def load_state(self, feature_name):
        """상태 로드"""
        state_file = self.state_dir / f"{feature_name}.state.json"
        if state_file.exists():
            return json.loads(state_file.read_text())
        return {"plan": "pending", "impl": "pending", "review": "pending"}

    def generate_fail_report(self, feature_name, phase, error_msg, attempted_code=""):
        """fail_report_handoff 생성"""
        existing = len(list(self.fail_dir.glob("*_fail_report_*.md")))
        report_num = existing + 1
        timestamp = datetime.now().strftime("%y%m%d_%H%M")
        report_path = self.fail_dir / f"{timestamp}_fail_report_{report_num}.md"

        content = f"""# Fail Report — {feature_name}

## 메타데이터
- **Timestamp**: {datetime.now().isoformat()}
- **Feature**: {feature_name}
- **Phase**: {phase}
- **Report Number**: {report_num}

## 실패 원인
{error_msg}

## 에러 발생 코드
```
{attempted_code}
```

## 다음 시도 시 확인사항
1. CLAUDE.md 컨벤션 재검토
2. 이전 실패 보고서 검토
3. 에러 메시지 전체를 에이전트 프롬프트에 포함

**Generated at**: {datetime.now()}
"""
        self.write_atomic(str(report_path), content)
        return str(report_path)

    def rollback_changes(self):
        """git 롤백"""
        subprocess.run(["git", "reset", "--hard", "HEAD"], check=True)

    def run_agent(self, agent_type, system_prompt, user_prompt, allowed_tools=None, output_file=None):
        """Claude CLI subprocess 안전 호출"""

        # Input Sanitization: 리스트 형식 사용 (자동 이스케이프)
        cmd = [
            self.claude_bin,
            "-p",
            user_prompt,
            "-s", system_prompt,
            "--model", "claude-opus-4-6",
            "--cwd", str(self.project_root)
        ]

        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])

        print(f"\n▶ {agent_type.upper()} Agent 실행 중...\n")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            output = result.stdout

            if result.returncode != 0:
                print(f"❌ {agent_type} Agent 실패:\n{result.stderr}")
                return None

            # Sensitive Output Handling: 로그는 별도 파일에 저장
            log_file = Path(f".agent_logs/{agent_type}_{datetime.now().isoformat()}.log")
            log_file.parent.mkdir(exist_ok=True)
            log_file.write_text(f"STDERR:\n{result.stderr}\n\nSTDOUT:\n{output}")

            if output_file:
                self.write_atomic(output_file, output)
                print(f"✅ 결과 저장: {output_file}")

            return output

        except subprocess.TimeoutExpired:
            print(f"⏱️ {agent_type} Agent 타임아웃 (300초)")
            return None
        except Exception as e:
            print(f"❌ {agent_type} Agent 오류: {e}")
            return None

    def run_workflow(self, user_request, feature_name):
        """전체 워크플로우 (안전 원칙 포함)"""

        # State Management: 중복 실행 방지
        state = self.load_state(feature_name)
        if state.get("impl") == "completed" and state.get("review") == "completed":
            print(f"⚠️ {feature_name}는 이미 완료됨")
            return True

        # ============ 1. PLAN AGENT ============
        plan_system = """You are a senior game engine architect specializing in Unity ECS/DOTS."""
        plan_prompt = f"""Analyze and create a plan:\n{user_request}"""

        plan_output = self.run_agent("plan", plan_system, plan_prompt,
                                     allowed_tools=["Read", "Glob", "Grep"],
                                     output_file=str(self.project_root / "docs" / "plan.md"))

        if not plan_output:
            return False

        self.save_state(feature_name, "plan", "completed")
        print("\n" + "="*60 + "\n📋 PLAN 완료\n" + "="*60)

        # ============ 2. IMPLEMENTATION AGENT ============
        impl_system = """You are a skilled C# game developer specializing in Unity ECS/DOTS."""
        impl_prompt = f"""Implement based on plan:\n{plan_output}"""

        try:
            impl_output = self.run_agent("implementation", impl_system, impl_prompt,
                                        allowed_tools=["Edit", "Write", "Read", "Bash", "Glob", "Grep"])

            if not impl_output:
                error_msg = "Implementation Agent returned empty output"
                report = self.generate_fail_report(feature_name, "implementation", error_msg)
                self.rollback_changes()
                print(f"❌ Implementation failed. Report: {report}")
                return False

            self.save_state(feature_name, "impl", "completed")
            print("\n" + "="*60 + "\n✅ IMPLEMENTATION 완료\n" + "="*60)

        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            report = self.generate_fail_report(feature_name, "implementation", error_msg)
            self.rollback_changes()
            print(f"❌ Implementation crashed. Report: {report}")
            return False

        # ============ 3. REVIEW AGENT ============
        review_system = """You are a meticulous code reviewer with expertise in game architecture and ECS."""
        review_prompt = f"""Review the implementation:\n{impl_output}"""

        review_output = self.run_agent("review", review_system, review_prompt,
                                      allowed_tools=["Read", "Glob", "Grep"],
                                      output_file=str(self.project_root / "docs" / "review.md"))

        if not review_output or "REVIEW PASSED" not in review_output:
            error_msg = f"Review found issues:\n{review_output}"
            self.generate_fail_report(feature_name, "review", error_msg)
            print(f"⚠️ Review failed. See fail_report_handoffs/")
            return False

        self.save_state(feature_name, "review", "completed")
        print("\n" + "="*60 + "\n✅ REVIEW PASSED\n" + "="*60)
        return True

# ============ USAGE ============
if __name__ == "__main__":
    project_root = "D:\\Unity\\Unity Project\\Sweepers in ECS"

    user_request = "Add a Turn/Energy system to the game core loop."
    feature_name = "turn_energy_system"

    orchestrator = SafeAgenticOrchestrator(project_root)
    success = orchestrator.run_workflow(user_request, feature_name)

    sys.exit(0 if success else 1)
```

---

## 디렉토리 구조

```
D:\Unity\Unity Project\Sweepers in ECS\
├── CLAUDE.md
├── claude_tools/
│   └── claude_subprocess_api.md      (이 파일)
├── fail_report_handoffs/             (NEW)
│   ├── 240330_1430_fail_report_1.md
│   ├── 240330_1445_fail_report_2.md
│   └── ...
├── .orchestrator_state/              (NEW)
│   ├── turn_energy_system.state.json
│   └── ...
├── .agent_logs/                      (NEW, 디버깅용)
│   ├── plan_2024-03-30T14:30:00.log
│   └── ...
└── ... (기타 프로젝트 파일)
```

---

## 에이전트 간 데이터 전달 규칙

### 1. Plan → Implementation
**전달 방식:** 파일 기반 (plan.md)
**무결성:** 해시 검증, 동시성 제어

### 2. Implementation → Review
**전달 방식:** 코드 + 설명문 결합
**검증:** git diff, 파일 내용 확인

### 3. Review → 최종 결과
**Output:** review.md 또는 fail_report_handoff

---

## 체크리스트

**Orchestrator 구현 시 필수 항목:**
- [ ] Input Sanitization: subprocess 인자는 리스트 형식 사용
- [ ] Data Integrity: 파일 쓰기는 원자적(atomic), 읽기 후 해시 검증
- [ ] Sensitive Output: 디버그 로그는 별도 파일 저장, 프롬프트에 포함 X
- [ ] State Management: `.orchestrator_state/` 에서 실행 상태 추적
- [ ] Failure Recovery: Implementation 실패 시 rollback + fail_report 생성
- [ ] Fail Report Format: `fail_report_handoffs/YYMMDD_HHMM_fail_report_N.md`

---

## 확장 가능성

이 구조는 다음과 같이 확장 가능합니다:

```
Plan → Design → Implementation → Review → Deployment
       (선택사항: 복잡한 기능)

또는

Plan → RefactorReview → Implementation → QA → Merge
       (더 엄격한 품질 관리)
```

각 에이전트를 추가할 때는 동일한 패턴으로 system_prompt, allowed_tools, 실패 복구를 정의하면 됩니다.
