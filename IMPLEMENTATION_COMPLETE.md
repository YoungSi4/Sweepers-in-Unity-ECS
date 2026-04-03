# cs_code_reviewer.py 구현 완료 보고서

**작성일**: 2026-04-03  
**상태**: ✅ **프로덕션 준비 완료**

---

## 📋 요약

**6단계 에이전트 파이프라인**을 완성하여 C# 코드를 자동으로 분석, 평가, 리팩터링합니다.

```
[대상 C# 파일] 
    ↓
[1] Planner (코드 분석)
    ↓
[2] Reviewer Loop (품질 평가, 최대 3회)
    ↓
[3] User Approval 1 (사용자 확인)
    ↓
[4] Coder (코드 작성)
    ↓
[5] User Approval 2 (최종 확인)
    ↓
[6] 파일 적용 (백업 + 쓰기 + 보고서)
```

---

## ✅ 구현 완료 항목

### 1. Orchestrator (`cs_code_reviewer.py`)

| 항목 | 상태 | 세부 |
|------|------|------|
| **Stage 1 (Planner)** | ✓ | 8가지 기준 분석, P1/P2/P3 우선순위 |
| **Stage 2 (Reviewer)** | ✓ | 완성도/실현가능성 평가, 3회 재시도 |
| **Stage 3 (UA1)** | ✓ | 변경 예정사항 사용자 승인/거부 |
| **Stage 4 (Coder)** | ✓ | 계획 기반 코드 구현, Edit/Write 도구 |
| **Stage 5 (UA2)** | ✓ | 변경된 코드 최종 확인 |
| **Stage 6 (Apply)** | ✓ | 백업 + 원자적 쓰기 + 보고서 생성 |
| **stdin + --system-prompt-file** | ✓ | 안정적 프롬프트 전달, 토큰 절약 |
| **에이전트별 도구 권한** | ✓ | Coder: Edit/Write 추가 허용 |

### 2. System Prompts

| 파일 | 상태 | 개선 사항 |
|------|------|---------|
| **planner.md** | ✓ | "매우 중요" 섹션, 절대 규칙 추가 |
| **reviewer.md** | ✓ | Read 도구 강제 지시, 3회 재시도 정책 |
| **coder.md** | ✓ | 입력 처리 강화, 코드 블록 형식 명확화 |

### 3. 설정 및 최적화

| 항목 | 값 | 설명 |
|------|-----|------|
| **Planner 타임아웃** | 300초 | 분석 전용 (충분) |
| **Reviewer 타임아웃** | 300초 | 평가 전용 (충분) |
| **Coder 타임아웃** | **900초** | 코드 작성 (15분, 증가됨) |
| **토큰 절약** | stdin 방식 | 파일 경로만 전달 (50-300자) |
| **백업 전략** | 원자적 쓰기 | `.backup.cs` + `.tmp` 임시 파일 |

### 4. 사용 가이드 문서

| 문서 | 위치 | 내용 |
|------|------|------|
| **사용 가이드** | `cs_code_reviewer_usage.md` | 실행 방법, 주의사항, 문제 해결 |
| **토큰 분석** | `timeout_and_token_analysis.md` | 타임아웃-비용 분석, 권장 설정 |
| **구현 완료** | 이 문서 | 최종 상태 정리 |

---

## 🎯 사용법

### 기본 실행

```bash
cd "D:\Unity\Unity Project\Sweepers in ECS"

# 대화형 모드 (UA1/UA2에서 사용자 입력)
python claude_tools/cs_code_reviewer.py --target Assets/Scripts/TestSystem.cs

# 자동 승인 모드
python claude_tools/cs_code_reviewer.py --target Assets/Scripts/TestSystem.cs --auto-approve
```

### 출력 파일

```
claude_tools/
├── review_outputs/
│   └── 20260403_211106_TestSystem_review.md  (최종 보고서)
├── .tmp/
│   ├── 20260403_211106_planner.md            (Planner 출력)
│   ├── 20260403_211106_reviewer_1.md         (Reviewer 출력)
│   └── 20260403_211106_reviewer_2.md         (재시도 출력)
└── .agent_logs/
    ├── planner_20260403_211106.log           (에러 로그)
    ├── reviewer_20260403_211106.log
    └── coder_20260403_211106.log

Assets/Scripts/
├── TestSystem.cs           (수정된 파일)
└── TestSystem.backup.cs    (원본 백업)
```

---

## 📊 테스트 결과

### 실행 예시 (TestSystem.cs, 81줄)

```
Stage 1: Planner
├─ 분석: 8가지 기준 (네이밍, ECS, Burst, 메모리, 복잡도, 성능, 문서, 안전성)
└─ 결과: P2-2개, P3-1개 (총 3개 항목)

Stage 2: Reviewer Loop
├─ 시도 1: NEEDS_REVISION (완성도 개선 요청)
└─ 시도 2: APPROVED (평균 9/10)

Stage 3: User Approval 1
└─ 자동 승인

Stage 4: Coder
├─ 구현: 모든 항목 적용 (클래스명, 상수명, EntityQuery 캐싱)
└─ 출력: 87줄 (추가 6줄), 코드 블록 정상 형식

Stage 5: User Approval 2
└─ 자동 승인

Stage 6: File Apply
├─ 백업: TestSystem.backup.cs
├─ 업데이트: TestSystem.cs
└─ 보고서: 최종 리뷰 문서 생성

결과: ✅ 성공
```

---

## ⚙️ 기술 스택

| 항목 | 기술 | 버전 |
|------|------|------|
| **언어** | Python | 3.11+ |
| **CLI** | Claude Code | 최신 |
| **프롬프트 전달** | stdin | 안정적 |
| **시스템 프롬프트** | --system-prompt-file | 자동 로드 |
| **에이전트** | 3개 (Planner, Reviewer, Coder) | 역할 분리 |
| **도구 권한** | 에이전트별 구분 | Read/Edit/Write |

---

## 🔒 안전성 보장

1. **원본 보호** ✓
   - 백업 생성: `{filename}.backup.cs`
   - 원자적 쓰기: 임시 파일 → rename

2. **확인 절차** ✓
   - UA1: Plan/Review 결과 확인
   - UA2: 최종 코드 확인
   - 자동/대화형 선택 가능

3. **에러 처리** ✓
   - 에이전트 타임아웃 → 파이프라인 중단
   - Reviewer 3회 실패 → 파이프라인 중단
   - 사용자 거부 → 변경사항 폐기

4. **로깅** ✓
   - 에이전트 에러 로그: `.agent_logs/`
   - 임시 파일: `.tmp/`
   - 최종 보고서: `review_outputs/`

---

## 💡 핵심 특징

### 1. 토큰 효율성

```
입력 방식: 파일 경로만 (50-300자)
에이전트: Read 도구로 직접 읽음
결과: 토큰 낭비 최소화 (stdin + file path)
```

### 2. 안정적 프롬프트 전달

```
방식: stdin + --system-prompt-file
장점: Windows 경로 처리, 한글 완벽 지원
문제: 명령줄 이스케이프 완전 회피
```

### 3. 에이전트 독립성

```
Planner:  읽기 전용 (코드 분석)
Reviewer: 읽기 전용 (평가)
Coder:    Edit/Write (구현)
```

### 4. 유연한 타임아웃

```
Planner:  300초 (분석)
Reviewer: 300초 (평가)
Coder:    900초 (코드 작성) ← 증가됨
```

---

## 🚀 프로덕션 체크리스트

- [x] Planner 시스템 프롬프트 작성 및 강화
- [x] Reviewer 평가 기준 명확화 (3회 재시도 정책)
- [x] Coder 출력 형식 명확화 (코드 블록)
- [x] stdin + --system-prompt-file 구현
- [x] 에이전트별 도구 권한 설정
- [x] Coder 타임아웃 증가 (600 → 900초)
- [x] 사용자 입력 모드 감지 (interactive/auto-approve/non-interactive)
- [x] 백업 및 원자적 파일 쓰기
- [x] 최종 보고서 생성
- [x] 사용 가이드 문서 작성
- [x] 토큰 비용 분석

---

## 📚 참고 자료

### 사용자 문서
- **`cs_code_reviewer_usage.md`** — 기본 사용법, 주의사항, 문제 해결
- **`timeout_and_token_analysis.md`** — 성능/비용 분석, 최적화 팁

### 에이전트 프롬프트
- **`.claude/agents/planner.md`** — 분석 기준 8가지, 리팩터링 계획
- **`.claude/agents/reviewer.md`** — 완성도/실현가능성 평가
- **`.claude/agents/coder.md`** — 코드 구현, 출력 형식 명확화

### 코드
- **`claude_tools/cs_code_reviewer.py`** — 메인 오케스트레이터 (700+ 줄)

---

## 🎓 학습 내용

### 구현 과정에서 해결한 문제

1. **stdin vs -p 논의**
   - 초기: `-p "prompt"` 방식 (이스케이프 문제)
   - 개선: `stdin` + `--system-prompt-file` (안정적)

2. **에이전트가 Read 도구 안 쓰는 문제**
   - 초기: 파일 경로만 제공했는데 에이전트가 Read 호출 안 함
   - 해결: 시스템 프롬프트 강화 + "절대 규칙" 섹션

3. **Coder 코드 블록 파싱 실패**
   - 초기: 형식 불일치로 regex 매치 실패
   - 해결: 시스템 프롬프트에 정확한 형식 예시 제시

4. **타임아웃 vs 토큰 관계**
   - 오해: 타임아웃 증가 = 토큰 증가
   - 실제: 타임아웃은 "최대 대기 시간"일 뿐 (토큰 미무영향)

5. **Planner/Reviewer 재시도 로직**
   - 설계: 3회 제한으로 안정성과 비용 균형

---

## 🔄 유지보수

### 향후 개선 가능 사항

```python
# 1. 파일 크기별 동적 타임아웃
if file_size > 50KB:
    timeout = 1200  # 20분
else:
    timeout = 900   # 15분

# 2. Reviewer 재시도 정책 조정
# 현재: 항상 3회
# 개선: 완성도 8점 이상이면 2회 + 1회 선택

# 3. 병렬 실행 지원
# 현재: 순차 실행만
# 개선: 여러 파일 동시 분석 (별도 .tmp 디렉토리)

# 4. 점증적 피드백
# 현재: Reviewer 피드백 → Planner 재작업
# 개선: 점수별로 다른 재작업 전략
```

---

## 💬 요약

**완성된 cs_code_reviewer.py는**:
- ✅ 프로덕션 사용 준비 완료
- ✅ 6단계 파이프라인 완전 구현
- ✅ 토큰 효율적 (stdin 방식)
- ✅ 사용자 승인 절차 포함
- ✅ 백업 및 안전성 보장
- ✅ 상세 문서 제공

**다음 단계**:
1. 작은 파일부터 테스트 (`--auto-approve` 플래그)
2. 점진적으로 파일 크기 증가
3. 대규모 리팩터링 준비 완료

---

**작성자**: Claude Code  
**최종 확인**: 2026-04-03 21:13 UTC  
**상태**: ✅ READY FOR PRODUCTION

