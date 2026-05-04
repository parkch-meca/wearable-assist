# Phase 1a Regression Test: forearm_v1

**작성일**: 2026-05-04  
**목적**: forearm_v1 모델 수정 후 ES 근육 활성화 동등성 검증

---

## 1. 실험 설정

| 항목 | 값 |
|------|---|
| 기준 모델 | `MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler.osim` |
| 검증 모델 | `MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim` |
| 동작 | `stoop_synthetic_v5.mot` (제자리 stoop, Phase 1a) |
| 시간 범위 | t = [1.0, 3.0] s (smoke mode) |
| Mesh interval | 25 intervals |
| 근육 수 | 114개 (Phase 1a muscle list) |
| GRF | `stoop_grf_v5.xml` (양발 합력) |

---

## 2. 결과

### 2.1 Overall

| 지표 | 값 |
|------|---|
| 분석된 근육 수 | 114 |
| 최대 ΔActivation | **1.227 %p** (IL_R10_r) |
| 평균 ΔActivation | ~0.18 %p |
| Pearson R (peak acts) | 0.999977 |
| Solve 상태 | Solve_Succeeded |
| 실행 시간 | 50.3 s |

### 2.2 ES 근육 Top 10 (|ΔActivation| 기준)

| 근육 | no_coupler | forearm_v1 | Δ (%p) |
|------|-----------|-----------|--------|
| IL_R10_r | 0.9196 | 0.9319 | 1.227 |
| IL_R10_l | 0.8969 | 0.9073 | 1.039 |
| LTpT_R10_l | 0.4369 | 0.4439 | 0.704 |
| IL_R7_r | 0.2676 | 0.2733 | 0.574 |
| IL_R9_r | 0.3900 | 0.3956 | 0.561 |
| LTpT_T1_r | 0.3083 | 0.3131 | 0.480 |
| IL_R6_r | 0.2119 | 0.2160 | 0.406 |
| IL_R9_l | 0.3706 | 0.3745 | 0.394 |
| IL_R8_r | 0.2292 | 0.2329 | 0.363 |
| LTpT_T3_r | 0.2465 | 0.2501 | 0.356 |

### 2.3 역방향 변화 (forearm_v1이 낮은 경우)

일부 근육(IL_L1_r, IL_L2_r 등)은 forearm_v1에서 미소하게 낮음 (Δ < 0.2 %p).  
이는 COM 이동으로 인한 하중 재분배 결과로 생리학적으로 타당.

---

## 3. PASS/FAIL 판정

| 기준 | 결과 |
|------|------|
| max ΔES < 5 %p | **PASS** (1.227 %p) |
| max ΔES < 10 %p | PASS |
| Solve 성공 | Yes |
| 전체 판정 | **PASS** |

---

## 4. 해석

forearm_v1에서 IL_R10 계열의 활성화가 소폭 증가 (~1.2 %p). 예상 원인:

1. hand_R body의 COM이 19 cm 더 원위부로 이동 → 전신 관성 텐서 미소 변화
2. stoop 동작에서 팔이 자연스럽게 늘어지므로 팔 위치 변화 = gravity loading 증가
3. 결과적으로 ES 부하 미소 증가 (1.2 %p ≈ 수치적 noise 수준)

이론적 예측: forearm 수정은 stoop 동작에서 ES에 거의 영향 없음 (팔 중력 moment arm 변화 < 1%)

실제 결과: max ΔES 1.227 %p (Coupler 제거 수준 1.16 %p와 유사)

---

## 5. 그림

`docs/images/phase1a_forearm_v1_regression.png`:
- Top 20 근육 |ΔActivation| bar chart (모두 < 5 %p)
- IL_R10_r/l time series (no_coupler vs forearm_v1)
- LTpL_L5 time series
- Peak activation scatter (R=0.999977)

---

## 6. 결론 및 다음 단계

**forearm_v1 모델 채택 결정: PASS**

| 수정 사항 | ES 영향 | 결론 |
|---------|--------|------|
| +19.2 cm hand segment | max ΔES 1.227 %p | PASS |
| Coupler 제거 (참고) | max ΔES 1.16 %p | PASS |

다음 단계:
- Step 3: 박스 motion v10 설계 (biomechanics-agent 호출)
  - forearm_v1 모델 사용
  - 목표 자세: PT=-55°, lumbar=-75°, hip=100°, knee=-30°
  - 도달 가능성 확인 완료 (dist=26.3 mm)
- Step 4: viz-agent 시각 검증 (Stage 4)
- Step 5: moco-analysis-agent (Phase 2 박스 Moco 실행)

---

*실행 스크립트*:
- `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/run_moco_phase1a_forearm_v1.py`
- `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/compare_phase1a_forearm_v1.py`

*결과 파일*:
- `/data/wearable-assist/results/phase1a_smoke_forearm_v1/solution.sto`
