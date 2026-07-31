# Plan v2 — Squat Lift Universal Model

**작성일**: 2026-05-26
**상태**: 사용자 승인 대기
**선행 결정**: 2026-05-11 박스 closure → "범용 모델 진짜 시작" path

---

## 0. 목표 (확정)

**1차 task**: Squat lift (Yan 2024 형식)
**Vision**: 다양한 작업(lift, walk, carry, transfer) 확장 가능한 **범용 model 첫 task**
**Deliverable**: Squat lift Moco 결과 + ES suit effect 정량 + 다음 task로 확장 가능한 model spec

**Scope 명시**:
- IN: Squat lift motion 생성, IK, Moco solve, suit effect 분석, Phase 1a regression
- OUT: 박스 v11b residual 추가 fix (옵션 1 closure 유지), Blender 분리 paradigm (보류)

---

## 1. Team 구조 (확정)

### 1.1 기존 agent (5개, 강화 없이 그대로 활용)
| Agent | 색상 | 역할 |
|---|---|---|
| biomechanics-agent | orange | Squat lift 자연 동작 reference, EMG 문헌 |
| opensim-agent | green | 모델 편집, IK, Moco 환경 |
| moco-analysis-agent | purple | Moco solve, ES analysis |
| viz-agent | cyan | 3D rendering, Grid PNG, Stage 4 검증 |
| paper-agent | yellow | Methods/Results 정리 |

### 1.2 새 agent (2개만 추가)
| Agent | 색상 | 역할 | 트리거 |
|---|---|---|---|
| **literature-agent** | blue | 2023-2026 paper 깊이 학습, 검증된 model/method spec 정리 | "literature", "paper", "사전 학습" |
| **parallel-explorer-agent** | violet | N개 variant 병렬 조립/실행/비교 | "병렬", "variants", "parallel" |

### 1.3 Orchestrator + Validation = 메인 Claude Code (저)
- 새 agent로 분리하지 않음 (subagent 간 직접 호출 제약)
- 메인이 직접 담당: agent 호출 순서, validation 체크리스트, patch 패턴 감지, STOP 결정 에스컬레이션

---

## 2. Phase 1 — 사전 학습 + Audit (3-4일)

### Day 1 — 기존 docs Audit (메인 직접)

다음 7개 문서 audit하여 **gap matrix** 작성:
1. `literature_synthesis.md`
2. `alternative_fullbody_models.md`
3. `alternative_models_local.md`
4. `hybrid_model_pros_cons.md`
5. `closest_reference_papers.md`
6. `model_enhancement_feasibility.md`
7. `model_modification_feasibility.md`

산출: `docs/agent_team_kb_audit.md`
- 각 문서 cover 항목 / Squat lift 적용 가능성 / **gap** (보강 필요 항목)

### Day 2-3 — literature-agent: Gap 보강

**Squat lift 특화 학습** (gap에 따라 조정):
- Yan 2024 (squat vs stoop EMG) 정밀 인용
- Hu 2026 (suit assist) squat 적용 가능성
- Predictive simulation for squat (SCONE, Moco)
- Squat lift kinematics (hip-knee-ankle 협응)
- Anthropometric (De Leva 1996) squat 적용

산출: `docs/agent_team_kb_squat_gap.md`
- 검증된 spec (numeric)
- Variants 3개 후보 최종 확정 (§3.1)
- 권장 IK target / contact / GRF 형태

### Day 4 — Validation Protocol + Patch Trigger 정의 (메인)

산출: `docs/validation_protocol_v2.md`
- §3 validation 체크리스트
- §4 정량 patch trigger
- §5 STOP 에스컬레이션 기준

⭐ **Phase 1 End — CHEOL HOON님 시각 검증** (gap matrix + variants 3개 후보 + validation protocol)

---

## 3. Phase 2 — 병렬 Variants (1-2주)

### 3.1 Variants 3개 (Phase 1 audit 후 최종 확정, 현 시점 시드 후보)

| ID | 모델 | 근거 | Squat 적합성 가설 |
|---|---|---|---|
| **A: Baseline** | ThoracolumbarFB v2.0 + forearm_v1 (`...no_coupler_forearm_v1.osim`) | 박스 v11 22/22 PASS, Phase 1a regression PASS (ΔES 1.227 %p), 검증 완료 | Squat은 박스 lifting과 달리 arm reach 덜 critical → 그대로 PASS 가능성 |
| **B: Hybrid H1** | ThoracolumbarFB + humerus scale-up + forearm_v1 | `hybrid_model_pros_cons.md` H1 권장 | Squat + carry까지 보장, arm reach 60 cm |
| **C: literature 1순위** | Phase 1 audit 결과로 확정 (LaiUhlrich 2023 + TLFB 척추 차용 등) | literature-agent 권장 | 야심찬 hybrid, 학술 새로움 |

### 3.2 각 variant 실행 (parallel-explorer-agent + 기존 agent 협업)

병렬 (3개 동시):
1. **Stage 1 - Squat motion 생성** (biomechanics-agent → opensim-agent)
2. **Stage 2 - IK 검증** (opensim-agent + viz-agent)
3. **Stage 3 - Phase 1a regression** (moco-analysis-agent, ΔES < 5 %p)
4. **Stage 4 - Squat Moco solve (B_noload)** (moco-analysis-agent)
5. **Stage 5 - Grid PNG 생성** (viz-agent, CLAUDE.md Grid Protocol)

### 3.3 비교 기준 (정량 + 정성)

| 기준 | 정량 threshold | 정성 |
|---|---|---|
| Phase 1a regression | max ΔES < 5 %p | - |
| Squat Moco solve | Solve_Succeeded < 300s | - |
| Pelvis/joint residual | < 100 N (trans), < 30 N·m (rot) | - |
| ES activation pattern | Hu 2026 squat 범위 일치 | - |
| Visual | - | Stage 4 grid 자연성 |
| 사용자 검증 | - | 채팅 6 PNG (3 variants × 2 view) |

### 3.4 Top 1-2 선택

병렬 비교 보고서 (메인 orchestrator 작성):
- `docs/phase2_variants_comparison.md` (정량 + visual + 권장)
- Top 1-2 사용자 승인 후 Phase 3 진행

⭐ **Phase 2 End — CHEOL HOON님 시각 검증** (3 variants × Stage 4 grid + 비교 보고서)

---

## 4. Phase 3 — 채택 Model 적용 (2-3주)

선택된 1-2 model:
1. Squat lift 4 conditions Moco (B_noload / suit50/100/200, 정확 N·m 변환)
2. ES suit effect 분석 (5-phase, dose-response)
3. Stage 5 video clip (suit 비교)
4. paper-agent §2.D Squat lift section draft
5. 다음 task 확장 검토 (walk, carry, transfer)

⚠️ **Patch 패턴 trigger 발동 시 즉시 STOP → 사용자 협의**

⭐ **Phase 3 End — CHEOL HOON님 시각 검증 + §2.D draft 승인**

---

## 5. Validation Protocol (확정)

### 5.1 Pre-validation (작업 전, 메인이 매번 체크)
- ☐ Spec 명확? (입력/출력/criteria)
- ☐ Reference 명시? (literature 또는 이전 PASS)
- ☐ Patch 패턴 위험 평가? (정량 trigger §5.4)
- ☐ Fail 시 plan?

### 5.2 Mid-validation (작업 중)
- ☐ Progress 합리? (timeboxed)
- ☐ 자원 사용 합리? (CPU/GPU/시간)
- ☐ 새 가설/발견 빈도? (3+ 신규 발견/시간 = 위험)
- ☐ 진행 vs STOP 결정?

### 5.3 Post-validation (작업 후)
- ☐ Numeric: Phase 1a ΔES < 5 %p, Hu 2026 14.9-28.6%, reserve < 100 N
- ☐ Visual: 모든 body 가시, 자세 자연, 일반인 이해 가능
- ☐ Patch 감지 (§5.4 trigger 평가)

### 5.4 정량 Patch Trigger (사용자 제안 수용)
**자동 감지 → 메인이 STOP 에스컬레이션**:
1. **같은 .osim 파일에 5일 내 5+ commit** → "model 자체 문제 의심"
2. **같은 IK target 3번 조정** → "spec 자체가 잘못"
3. **같은 모듈/같은 종류 fix 3번 누적** (예: pelvis_ty residual 3번 수정) → "근본 원인 잘못 진단"
4. **단일 phase 14일 초과** → "timebox 위반"
5. **3 variants 모두 fail** → "전체 paradigm 재검토"

### 5.5 STOP 에스컬레이션
- Trigger 1+ 발동 → 메인이 즉시 사용자에게 보고
- 메인이 단독 결정 금지: 변경 path, backup paradigm 전환은 사용자 승인 필수

---

## 6. 매주 점검 (매주 금요일, 사용자)

보고 양식:
1. 진행 phase (1/2/3) + Day N
2. Validation 결과 (pre/mid/post 통과율)
3. Patch trigger 평가 (0 발동 / N 발동)
4. 다음 주 plan (수정 사항)
5. STOP 위험 평가 (낮음/중/높음)

---

## 7. Backup Path (보류)

**Blender + OpenSim 분리 paradigm** = §5.4 patch trigger 발동 시에만 결정.
- 사전 학습 별도 (1주+)
- 사용자 사전 승인 필수
- 현 시점 결정 X

---

## 8. 일정 요약

| Phase | 기간 | 주요 산출물 | End 검증 |
|---|---|---|---|
| 1 | 3-4일 | KB audit + gap 보강 + variants 3개 확정 + validation protocol | ⭐ 사용자 |
| 2 | 1-2주 | 3 variants 병렬 (regression + Squat Moco + Stage 4 grid) | ⭐ 사용자 |
| 3 | 2-3주 | Top 1-2 적용, 4 conditions, video, paper draft | ⭐ 사용자 |

**총 4-6주** (원안 4-6주 유지, 단 Phase 1 압축으로 효율적)

---

## 9. 결정 기록 (사용자 확정 2026-05-26)

1. 목표 task: **Squat lift** (범용 첫 task)
2. 새 agent: **2개** (literature, parallel-explorer)
3. Phase 1: **3-4일** (audit + gap)
4. Variants: **3개** (baseline + hybrid + literature 1순위)
5. Backup (Blender): **보류**
6. Patch trigger: **정량 5종** (§5.4)

---

## 10. 승인 후 첫 행동

승인 즉시 Phase 1 Day 1 시작:
1. 메인이 7개 문서 audit → `docs/agent_team_kb_audit.md` 작성
2. literature-agent .md 정의 (Day 1 종료)
3. parallel-explorer-agent .md 정의 (Day 1 종료)

⚠️ **자동 진행 X — 본 plan v2 승인 후만 Day 1 시작**
