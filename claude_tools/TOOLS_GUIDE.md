# Claude Tools Usage Guide

이 폴더의 도구들 사용 방법을 설명합니다.

---

## 📚 도구 목록

| 도구 | 설명 | 사용 시나리오 |
|------|------|-------------|
| `request_to_plan_todo.py` | 사용자 요청 → Plan & Todo 생성 | 새 기능/작업 계획 수립 |
| `request_orchestrator.py` | Plan & Todo → 구현 오케스트레이션 | 계획을 실제 코드로 구현 |
| `cs_code_reviewer.py` | C# 코드 자동 리뷰 & 리팩터링 | Assets/Scripts C# 파일 검토 |

---

## 🛠️ request_to_plan_todo.py

사용자 요청을 받아 **구조화된 Implementation Plan + Todo Checklist**로 변환합니다.

### 사용법

```bash
cd "D:\Unity\Unity Project\Sweepers in ECS"
python claude_tools/request_to_plan_todo.py "당신의 요청 여기에"
```

### 예시

```bash
python claude_tools/request_to_plan_todo.py "코드 리뷰 및 리팩터링 자동화 도구를 만들고 싶어요"
```

### 출력

```
claude_tools/outputs/{YYYYMMDD_HHMMSS}_{keyword}.md

예: claude_tools/outputs/20260402_143000_refactoring.md
```

### 파이프라인

```
1. Planning Agent (분석 & 계획)
2. Review Agent (피드백)
3. Revised Planning Agent (개선된 계획)
4. Todo Agent (할일 목록)
5. Keyword Extraction (파일명 생성)

↓
Output: 통합된 Plan + Todo 문서
```

---

## 🎯 request_orchestrator.py

`request_to_plan_todo.py`의 결과물(Plan & Todo)을 받아 **실제 구현**으로 오케스트레이션합니다.

### 사용법

```bash
python claude_tools/request_orchestrator.py "{plan_todo_file_path}"
```

### 예시

```bash
python claude_tools/request_orchestrator.py "claude_tools/outputs/20260402_143000_refactoring.md"
```

### 파이프라인

```
1. Plan & Todo 분석
2. Planning Validation
3. Implementation
4. Review & Approval
5. Deployment (또는 Re-work)
```

---

## 🔍 cs_code_reviewer.py

Assets/Scripts 경로의 C# 파일을 자동으로 리뷰하고 리팩터링을 제안합니다.

### 사용법

```bash
python claude_tools/cs_code_reviewer.py --target Assets/Scripts/Systems/MoveSystem.cs
```

### 옵션

```bash
# 특정 파일 리뷰
python claude_tools/cs_code_reviewer.py --target {file_path}

# 변경된 모든 C# 파일 리뷰
python claude_tools/cs_code_reviewer.py --all
```

### 6-Stage 파이프라인

```
1. Planner        → 코드 분석 (8가지 기준)
2. Reviewer       → 완성도/실현가능성 평가
3. User Approval 1 → 변경 예정사항 확인
4. Coder          → 리팩터링 코드 구현
5. User Approval 2 → 변경된 코드 최종 검토
6. File Apply     → 파일에 변경사항 적용
```

### 상세 문서

- **아키텍처**: `docs/cs_code_reviewer_architecture.md`
- **에이전트 정의**: `docs/cs_code_reviewer_agents.md`
- **System Prompts**: `docs/prompts/`

---

## 📖 API 문서

### claude_subprocess_api.md

Claude CLI를 subprocess로 호출하는 안전한 방법:
- Input Sanitization (보안)
- Data Integrity (무결성)
- Sensitive Output Handling (출력 추적)
- State Management (상태 관리)
- Failure Recovery (실패 복구)

---

## 🔧 환경 설정

### 필수 설정

```python
# Windows에서 Claude CLI 호출 시 필수
env["CLAUDE_CODE_GIT_BASH_PATH"] = r"D:\Git\bin\bash.exe"
```

### 인코딩

```bash
set PYTHONIOENCODING=utf-8
```

### Anthropic API

도구들이 Claude CLI를 통해 실행되므로, Claude Code 설정에서 API 키가 활성화되어 있어야 합니다.

---

## 📁 폴더 구조

```
claude_tools/
├── request_to_plan_todo.py      (도구)
├── request_orchestrator.py        (도구)
├── cs_code_reviewer.py            (도구, 예정)
├── claude_subprocess_api.md       (API 문서)
└── TOOLS_GUIDE.md                 (이 파일)

docs/                              (설계 & 아키텍처)
├── cs_code_reviewer_architecture.md
├── cs_code_reviewer_agents.md
└── prompts/
    ├── planner_system.md
    ├── reviewer_system.md
    ├── coder_system.md
    ├── user_approval_1.md
    └── user_approval_2.md
```

---

## 💡 사용 시나리오

### 시나리오 1: 새 기능 기획

```bash
# Step 1: 요청을 Plan & Todo로 변환
python claude_tools/request_to_plan_todo.py "Turn/Energy 시스템 추가"

# Step 2: Plan & Todo 검토 후 구현
python claude_tools/request_orchestrator.py "claude_tools/outputs/20260402_*.md"
```

### 시나리오 2: 기존 코드 리뷰

```bash
# Step 1: 코드 리뷰 시작
python claude_tools/cs_code_reviewer.py --target Assets/Scripts/Systems/MoveSystem.cs

# Step 2: Planner 분석 → Reviewer 평가 → User Approval 1
#         → Coder 구현 → User Approval 2 → File Apply
```

---

## ⚠️ 주의사항

1. **파이프라인 순차성**: 도구들은 순차 실행됨 (병렬 실행 불가)
2. **git 명령어**: 읽기 전용만 허용 (commit, push 불가)
3. **출력 언어**: 모든 도구의 출력은 **한글 마크다운**
4. **인코딩**: UTF-8 필수 (Windows 환경에서 주의)

---

## 🚀 시작하기

```bash
# 환경 확인
python --version                    # Python 3.8 이상
which claude                        # Claude CLI 설치 확인

# 첫 번째 도구 실행
python claude_tools/request_to_plan_todo.py "테스트 요청"
```

---

## 📞 문제 해결

| 문제 | 원인 | 해결 |
|------|------|------|
| Claude CLI 못 찾음 | PATH 설정 미흡 | Claude Code 설치 확인 |
| 인코딩 에러 | UTF-8 미설정 | `PYTHONIOENCODING=utf-8` 설정 |
| git bash 에러 | CLAUDE_CODE_GIT_BASH_PATH 미설정 | 코드에서 env 변수 설정 |
| 타임아웃 | 요청 너무 복잡 | 작은 단위로 분할 |

---

Last updated: 2026-04-02
