# Validation Protocol v2 (Plan v2 Squat Lift)

**작성일**: 2026-05-26 (Day 3 오후)
**작성**: 메인 Claude Code (orchestrator)
**기반**: Plan v2 §5 + Day 2-3 산출물 (squat_lift_literature.md, squat_scenario_spec.md, variant_c_recommendation.md, squat_rom_measurement.md, hu2026_squat_validation_input.md)
**적용 범위**: Plan v2 Phase 2 (3 variants 병렬) + Phase 3 (Top 1-2 적용) 모든 작업

---

## §1. Pre-Validation (작업 전 체크리스트, 메인이 매번 적용)

작업 시작 전 ☐ 모두 통과 → 진행, 1+ ❌ → 즉시 STOP

- ☐ **Spec 명확** — 입력 (모델/모션), 출력 (산출 파일), 통과 기준 (numeric)
- ☐ **Reference 명시** — 학계 paper (PMID/DOI) 또는 이전 PASS 결과
- ☐ **Patch trigger 위험 평가** — §4 5종 trigger 사전 점검
- ☐ **Fail 시 fallback plan** — Variant 전환 / Spec 축소 / STOP 에스컬레이션
- ☐ **Timebox 명시** — 최대 N 시간/일, 초과 시 STOP

---

## §2. Mid-Validation (작업 중, agent 자가 + 메인)

- ☐ **Progress 합리** — Timebox 내 진행률 (50% 시점 50% 진행 예상)
- ☐ **자원 사용 합리** — CPU/GPU/디스크 모니터링 (Moco solve > 30분 시 점검)
- ☐ **새 가설/발견 빈도** — 시간당 3+ 신규 발견 = 위험 신호 (계획 부재 의심)
- ☐ **진행 vs STOP 결정** — 위험 발견 시 즉시 사용자 보고

---

## §3. Post-Validation (작업 후 통과 기준)

### 3.1 Numeric Criteria (모두 통과 필수)

| 항목 | 기준 | 출처 | 적용 시점 |
|------|------|------|---------|
| **Phase 1a regression** | max ΔES < 5 %p | forearm_v1 PASS 1.227 %p (`phase1a_forearm_v1_regression.md`) | Variant 조립 후, Squat solve 전 |

> ⛔ **정정 (2026-07-30)**: 이 절의 Hasenmaier 2026 "10–17 %" / "10–27 %"는 **%MVC 절대 포인트**이지 상대 감소율이 아니다. stoop 상대 감소율은 69.8→42.4 %MVC = **−39.3 %**, squat은 원문이 수준 간 유의차를 보고하지 않아 **대조 불가**. 상세는 `hu2026_squat_validation_input.md` R1 정정 박스 및 `five_motion_paper_draft.md` §4 참조.
| **Squat suit effect** | ES reduction 10-28% (24 N·m) | Hasenmaier 2026 squat 10-17%, Hu 2026 squat-included pooled 14.9-28.6% | Squat Moco solve 후 |
| **EMG-model validation** | r > 0.84 (cross-correlation) | Yan 2024 (PMID 39305855) | Subject-specific 시점 (현재 적용 보류) |
| **L5/S1 compression** | < 3400 N (NIOSH limit) | NIOSH 1981 spinal compression limit | Squat Moco solve 후 |
| **Pelvis_ty residual** | < 5% BW ≈ 37 N | Hicks 2015 (PMID 25474098) | Moco solve 후 |
| **Pelvis_tilt residual** | < 1% BW×height ≈ 12 N·m | Hicks 2015 | Moco solve 후 |
| **Reserve activation** | < 1.0 (saturation 회피) | Dembia 2020 | Moco solve 후 |
| **Solve time** | < 300s per condition | 경험값 (Phase 1a 140s) | Squat Moco solve 후 |
| **IK target error** | < 50 mm (hand → box) | 박스 v11 PASS 22/22 기준 | Stage 2 IK 후 |

### 3.2 Visual Criteria (사용자 강조 — 손 분리 issue 대응)

**모든 Grid PNG 생성 시 다음 5개 체크리스트 적용** (메인 자가 검증 1차 + 사용자 채팅 2차):

| 항목 | 기준 | Fail 시 |
|------|------|--------|
| ☐ **모든 body 부위 visible** | head, neck, torso, pelvis, R/L arm (humerus+forearm+hand), R/L leg (femur+tibia+foot) 모두 mesh 표시 | mesh 누락 → STOP |
| ☐ **Mesh 연결 자연** | 관절부 끊김 없음, 손 분리 없음 (forearm-hand 결합), foot-tibia 결합 | 분리 시 → STOP (forearm_v1 patch 재검증) |
| ☐ **자세 자연** | 일반인이 보고 "사람이 박스 들고 있다" 인식 가능 | 부자연 → biomechanics-agent 재호출 |
| ☐ **근육 path 합리** | ES 경로가 척추 따라 자연, deltoid 어깨 자연, 비정상 교차 없음 | 비정상 → opensim-agent 재호출 |
| ☐ **일반인 이해 가능** | 동작 설명 없이 box squat lift 인식 가능 | 이해 불가 → motion 재설계 |

### 3.3 Patch 감지 (§4 5종 trigger 평가)

각 작업 종료 시 §4 5종 trigger 점검 — 1+ 발동 시 STOP 에스컬레이션

---

## §4. 정량 Patch Trigger (사용자 제안 + Plan v2 §5.4)

자동 감지 → 메인이 STOP 에스컬레이션 → 사용자 결정

### Trigger 1: 같은 .osim 파일에 5일 내 5+ commit
- **감지**: `git log --since="5 days ago" --oneline -- "*.osim"` 5+ entries
- **의미**: 모델 자체 문제 의심 (단발 fix 누적)
- **대응**: Variant 자체 재검토 (다른 시드로 전환)

### Trigger 2: 같은 IK target 3번 조정
- **감지**: 동일 coordinate/marker IK weight 3+ 변경 (script diff)
- **의미**: Spec 자체가 잘못 (literature reference 재확인 필요)
- **대응**: literature-agent 재호출 → spec 재검증

### Trigger 3: 같은 모듈/같은 종류 fix 3번 누적
- **감지**: 동일 파일에 동일 함수/블록 3+ 수정 (예: pelvis_ty residual fix 3번)
- **의미**: 근본 원인 잘못 진단 (증상만 가리기)
- **대응**: 근본 원인 재분석 (사용자 협의)

### Trigger 4: 단일 phase 14일 초과
- **감지**: Phase 1/2/3 timebox 14일 (Plan v2 §8)
- **의미**: Timebox 위반 = 계획 부재
- **대응**: Phase 종료 강제 + 부분 결과로 다음 phase 전환

### Trigger 5: 3 variants 모두 fail
- **감지**: A/B/C 모두 Phase 1a regression 또는 Squat Moco FAIL
- **의미**: 전체 paradigm 재검토 필요 (model 한계 아닐 가능성)
- **대응**: Backup path (Blender) 사전 학습 또는 Squat 시나리오 spec 축소

---

## §5. STOP 에스컬레이션 절차

§4 1+ trigger 발동 또는 §3 visual/numeric 1+ ❌:

1. **메인이 즉시 작업 중단** — 추가 시도 금지
2. **사용자에게 보고** (200 words 이내):
   - 발동 trigger 또는 fail 항목
   - 직접 증거 (log/file path/numeric)
   - 가능한 fallback 옵션 2-3개
3. **사용자 결정 대기** — 단독 진행 금지
4. **결정 후 진행**

⚠️ **메인 단독 결정 금지**: 변경 path, backup paradigm 전환은 사용자 승인 필수

---

## §6. Day 2-3 결과 통합 (validation 입력)

### 6.1 Squat 시나리오 spec (squat_scenario_spec.md)
- Weight: 15 kg (NIOSH LI = 1.27)
- Position: ground level, 35 cm horizontal
- Peak: hip 110°, knee 115°, lumbar sum 25°, trunk 35°
- Duration: 4s (descent 1.5 + grasp 1.0 + ascent 1.5)

### 6.2 TLFB+forearm_v1 ROM 결과 (squat_rom_measurement.md)
- Hip: ±120° (Squat 110° **PASS**, 여유 10°)
- Knee: -120°~+10° (Squat -115° **PASS**, 여유 5°)
- Ankle: R ±90°, L ±60° (Squat -20° **PASS**)
- Lumbar: ±90°/seg (Squat -5°/seg **PASS**)
- Pelvis_ty: [-1.0, +2.0] m (Squat -0.30 m **PASS**)
- **결론**: Variant A baseline ROM 확장 불필요, 시나리오 spec 그대로 적용 가능

### 6.3 Variant 최종 spec (variant_c_recommendation.md)

| Variant | 모델 | 상태 | 비교 기준 |
|---------|------|------|---------|
| **A baseline** | TLFB+forearm_v1 (no_coupler) | 검증 완료 (Phase 1a 28%), ROM PASS | Squat 통과 가능성 높음 |
| **B Hybrid** | TLFB + humerus scale-up | 박스 reach 보강 (Squat에는 영향 작음 예상) | 옵션 |
| **C Akhavanfar 2024** | Enhanced FATLS (SimTK, OpenSim 4.4, MIT) | Bruno 2015 동일 조상, dynamic 9 tasks r>0.9 | Day 3 priority: SimTK download + forearm_v1+Coupler patch 재적용 + Phase 1a regression |

⚠️ Variant C 호환 X (Phase 1a regression > 5 %p) 시 fallback → 시드 B (TLFB hip/knee ROM 10° 확장)

### 6.4 Validation reference paper (hu2026_squat_validation_input.md)
- R1: **Hasenmaier 2026 (P3)** — squat 단독 ES 10-17% ↓ (우리 핵심 validation)
- R2: **Kingma 2021 (P7)** — squat L4/L5 compression 3509 N (>stoop 2783 N)
- R3: **Yan 2024 (P1)** — EMG-model r 0.84-0.98 validation
- R4: **Park 2002 (P6)** — ROM baseline

---

## §7. 매주 점검 (매주 금요일, 사용자)

보고 양식:
1. 진행 phase (1/2/3) + Day N
2. Validation 결과 (pre/mid/post 통과율 + 항목별)
3. Patch trigger 평가 (0 발동 / N 발동 + 어느 것)
4. 다음 주 plan
5. STOP 위험 평가 (낮음/중/높음)

---

## §8. 다음 작업 (Day 4 = Phase 1 종료)

Day 4 작업:
1. 본 protocol 사용자 검토 + 승인
2. Plan v2 §2 Phase 1 End ⭐ 사용자 시각 검증 통과
3. Phase 2 시작 spec 확정:
   - Variant A/B/C 조립 spec (parallel-explorer-agent 호출)
   - 병렬 실행 timebox (Week 1: 조립+regression 5일, Week 2: Squat Moco+비교 5일)
4. ⭐ Phase 1 종료 → Phase 2 진행 사용자 승인

---

## §9. Open Issue (사용자 검토 시 참고)

1. **Akhavanfar 모델 다운로드 + patch 재적용 1-2일** — Phase 1 종료 전에 할지, Phase 2 Day 1-2에 포함할지 결정
2. **deep squat IK 안정성** — 박스 v11 medium squat까지만 검증, deep squat 신규
3. **Suit 효과 squat < stoop 예상** — Hasenmaier 10-17% < Phase 1a 28% — 정직 보고 필요
4. **Variant B 시드 정의 모호** — Hybrid H1 (humerus scale) vs ROM 확장 (deep squat용) — Phase 2 시작 전 명확화
5. **여성 65세 caregiving target** — 직접 cohort paper 없음, Phase 2 후속 별도 검색

---

*Plan v2 Phase 1 Day 3 종료 시점 validation protocol draft. 사용자 검토 후 Day 4 종료 + Phase 2 시작.*
