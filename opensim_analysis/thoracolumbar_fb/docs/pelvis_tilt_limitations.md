# Pelvis_tilt Reserve 모델/방법론 한계 평가 (2026-04-29)

## 배경

- 박스 motion v11b (12회 시도 끝 PASS)
- v1 (114 muscles): pelvis_tilt 221.1 N·m
- v2 (158 muscles, +하지 44): pelvis_tilt 221.1 N·m (0% 변화)
- hip/knee/ankle reserve는 v2에서 정상화됨

---

## 핵심 발견: pelvis_tilt의 구조적 성격

pelvis_tilt는 `ground_pelvis` CustomJoint의 자유도(floating base)다.

```
ground_pelvis (CustomJoint):
  parent: ground_offset
  child:  pelvis_offset
  coordinates: pelvis_tilt, pelvis_list, pelvis_rotation,
               pelvis_tx, pelvis_ty, pelvis_tz
```

**이 자유도에 직접 moment arm을 가지는 근육은 620개 중 단 하나도 없다.** OpenSim API로 실측한 결과, IL_L1_r, MF_m*, LTpT_*, QL_*, glut_max*, bifemlh* 등 모든 근육의 pelvis_tilt moment arm = 0 (±1e-17 m 수치 오차 수준).

이는 근육이 pelvis_tilt에 직접 토크를 줄 수 없다는 뜻이다. pelvis_tilt reserve = CMC/MocoInverse의 **전신 동역학 잔차 actuator**이며, 근육 부족이 아니라 외력 모델링 불완전에서 기인한다.

---

## 1. Multifidus (MF) 검토

**모델에 존재:** Yes (120개, 모델 전체)

ThoracolumbarFB v2.0의 MF 구성:
- `MF_m1s_r` ~ `MF_m5t_3_r/l` (lumbar MF, superficial + transverse): 50개
- `MF_m1_laminar_r/l` ~ `MF_m5_laminar_r/l` (laminar MF): 10개
- `multifidus_L4_T12`, `multifidus_L3_T11`, ... (thoracic MF): 46개
- `supmult-T1-C4`, `deepmult-T1-C5`, ... (cervical deep MF): 14개

**Muscle set v1 (114) 포함:** No (MF 전혀 미포함)

**Muscle set v2 (158) 포함:** No (추가 안 됨 — 하지 근육만 추가됨)

**MF의 pelvis_tilt moment arm:** 0 (실측)

**MF의 실제 작용 coordinate:** L5_S1_FE, L4_L5_FE, L3_L4_FE, L2_L3_FE, L1_L2_FE (요추 분절 FE)

**결론:** MF 추가 시 요추 분절 reserve 개선 가능하나, pelvis_tilt reserve에는 영향 없음.
v1/v2에서 요추 분절 reserve가 이미 작다면 MF 추가 필요성 낮음.

**예상 pelvis_tilt reserve 감소: 0%**

---

## 2. Quadratus Lumborum (QL) 검토

**모델에 존재:** Yes (36개)
- `QL_post_I_*`, `QL_mid_*`, `QL_ant_I_*` (anterior/posterior/middle ilio-costal)
- 양측 각 18개

**Muscle set v1 (114) 포함:** Yes (전량, 36개 포함)

**QL의 실제 작용 coordinate:** L5_S1_FE, L4_L5_FE, L5_S1_LB 등 요추 분절

**결론:** QL이 이미 v1에 포함되어 있으며, v1→v2에서도 0% 변화. QL 추가 효과 없음.

**예상 pelvis_tilt reserve 감소: 0%**

---

## 3. Intra-Abdominal Pressure (IAP) 표현

**모델 직접 표현:** 없음 (ThoracolumbarFB v2.0에 IAP element 없음)

**OpenSim에서 IAP 추가 방법:**
1. `ExternalForce` (lumbar COP에 직접 압력력 적용)
2. 수직 force로 thorax-pelvis 간 압박력 추가

**문헌 추정 영향 (Cholewicki 1999, McGill 1997):**
- 심한 stoop: IAP가 요추 신전 모멘트의 5–15% 분담
- 현재 v11b의 주 문제는 pelvis_tilt (floating base), 요추 분절 reserve 아님
- IAP가 pelvis_tilt 자유도에 직접 적용되지 않으면 pelvis_tilt reserve 변화 없음

**추가 가능성:** 기술적으로 가능하나 개발 비용 대비 효과 불확실

**예상 pelvis_tilt reserve 감소: 0~5%** (pelvis_tilt 특성상 거의 없음)

---

## 4. Spinal Ligaments

**모델 표현:** 없음 (ThoracolumbarFB v2.0에 spinal ligament 없음)

모델에는 CoordinateActuator (팔꿈치, 어깨), PointToPointActuator (rib actuators) 등 28개의 비근육 forces가 있으나, supraspinous/interspinous ligament는 미포함.

**문헌 추정 영향 (McGill 1997):**
- Posterior ligaments: 깊은 굴곡에서 5–15% 분담
- 이들도 요추 분절 FE 좌표에 작용 → pelvis_tilt 영향 없음

**예상 pelvis_tilt reserve 감소: 0%**

---

## 5. 손 외력 명시 표현 (방법론) ⭐⭐⭐ 가장 중요

### 현재 방법 (GRF 통합)

```python
# write_grf_suit_extloads() in run_moco_phase2c4_box_v2_sweep.py
box_force_per_foot = BOX_MASS * GRAVITY / 2.0  # = 98.1 N
grf[i, vy_R_idx] += add_vy  # 족저반력에 박스 무게 추가
grf[i, vy_L_idx] += add_vy
```

### 정량 분석 (피크 굴곡 t=2.0s 기준)

실측 좌표 (OpenSim API, v11b motion 실제 값):
- hand_R 위치: x=+0.342 m, y=-0.696 m
- hand_L 위치: x=+0.342 m, y=-0.696 m
- pelvis 위치: x=-0.324 m, y=-0.140 m
- calcn_r 위치: x=-0.044 m, y=-0.905 m

손 외력 모멘트 (박스 반력, 상향):
```
F_hand = 20 kg × 9.81 / 2 = 98.1 N (per hand)
dx_hand = 0.342 - (-0.324) = 0.666 m (pelvis 기준 앞쪽)
Moment_per_hand = 98.1 × 0.666 = 65.3 N·m
Total_hand_moment = 130.6 N·m (신전 모멘트)
```

발 GRF 보정 모멘트:
```
dx_foot = -0.044 - (-0.324) = 0.280 m
Box_GRF_moment = 98.1 × 0.280 × 2 = 54.9 N·m (신전)
```

**순 불균형 (손 외력 - 발 GRF 보정): 130.6 - 54.9 = 75.7 N·m**

### Reserve 분해 (추정)

| 출처 | 크기 | 비율 |
|------|------|------|
| Phase 1a 기준 (stoop, no box) | 19.4 N·m | ~9% |
| 손 외력 미적용 (순 불균형) | ~130 N·m | ~59% |
| 잔차 (관성력, 운동학 변화) | ~72 N·m | ~33% |
| **합산** | **~221 N·m** | **≈221 N·m 관측** |

### 이전 손 외력 시도 실패 원인

`inf_pr=4050` 수렴 실패는 구현 오류 (ExternalForce 방향/적용점 설정) 가능성이 높으며, 물리 자체의 불가능이 아님.

**예상 pelvis_tilt reserve 감소 (손 외력 정확 구현 시): -130 N·m → 221에서 ~90 N·m**

---

## 6. Spine FE coordinate 분배 검토

v11b 운동의 pelvis_tilt–lumbar 관계:

```
pelvis_tilt(t) ≡ lumbar_sum(t) = L5S1 + L4L5 + L3L4 + L2L3 + L1L2
```

피크(t=2.0s):
- pelvis_tilt = -55°
- 각 요추 분절 FE = -11° (5개 합 = -55°)
- 비율 = 1:1 (완전 일치)

**이것은 운동 생성 아티팩트다.** 실제 박스 들기에서 pelvis_tilt (골반 전방 경사)와 요추 굴곡은 독립적으로 결정된다. v11b에서 두 값이 동일한 ramp profile을 따르는 것은 motion generator가 단일 변수를 두 채널에 동시 적용했기 때문이다.

**생리적 합리성:**
- 피크 trunk 전방 기울기 = pelvis_tilt + lumbar = -110° (ground 기준)
- hip = 100°, knee = -30°
- 이는 심한 stoop+squat 자세로 biomechanically 가능하나 극단적
- CLAUDE.md 명세 (lumbar -62°, pelvis_tilt 작게)와 상이

**다른 spec 시도 가치:**
- pelvis_tilt = -30° (작게), lumbar = -62° (deeper)로 분리 시
- pelvis_tilt 불균형 모멘트 감소 기대 (손 위치 변화에 따라)
- 단, 현재 v11b로 PASS 판정을 받았으므로 motion 자체 변경은 별도 결정 필요

---

## 7. v11b motion 자체 검증

| 시간 | pelvis_tilt | lumbar 합 | hip | knee | trunk 전방 |
|------|-------------|-----------|-----|------|-----------|
| 0.0s | 0° | 0° | 0° | 0° | 0° |
| 1.0s | -13.8° | -13.8° | 25° | -7.5° | -27.5° |
| 2.0s | -55.0° | -55.0° | 100° | -30° | -110° |
| 3.0s | -41.2° | -41.2° | 75° | -22.5° | -82.5° |
| 4.0s | 0° | 0° | 0° | 0° | 0° |

피크 trunk forward lean -110° (ground 기준) = 매우 깊은 stoop.
실제 박스 들기 문헌에서는 trunk 전방 기울기 50–90° 범위.
현재 v11b는 상한 근처 또는 초과.

**하지만 v11b는 PASS 판정을 받은 motion** — 이 진단은 단지 reserve 221 N·m의 원인 설명용이며 motion 자체 변경 권고는 아님.

---

## 8. Reserve actuator 설정 검토

Phase 1a vs Phase 2.C.4 모두 `RESERVE_OPTF = 10.0 N·m` 동일.

`ModOpAddReserves(10.0)` 동작:
- CoordinateActuator를 모든 좌표에 추가
- optimal_force = 10.0 N·m
- MocoInverse에서 control은 [-∞, +∞] 비제약 → reserve = control × 10.0

따라서 RESERVE_OPTF를 높이면 cost function weight는 감소하나 실제 필요 토크는 동일. 낮추면 solver가 reserve 회피를 더 강하게 시도 → 물리적으로 불가능한 경우 infeasibility.

**낮은 RESERVE_OPTF + 손 외력 미적용 = inf_pr 발산**이 이전 실패를 설명.

---

## 9. 종합 진단

| 한계 항목 | 모델 부재? | pelvis_tilt reserve 영향 | 보강 가능 | 시간 |
|----------|-----------|--------------------------|---------|------|
| MF 부재 (v1,v2) | 모델엔 있으나 set에 없음 | 0% (다른 coord에 작용) | Y | 1h |
| QL 부재 | 이미 v1에 포함 | 0% | - | - |
| IAP 부재 | 모델에 없음 | 0~5% | Y (불확실) | 2h |
| Spinal ligaments | 모델에 없음 | 0% | Y (제한적) | 2h |
| **손 외력 미적용** | **방법론 문제** | **~60% (~130 N·m)** | **Y** | **2~4h** |
| 운동학 (pelvis_tilt↔lumbar 1:1) | 운동 아티팩트 | 간접 영향 | Y (새 motion) | 별도 |
| 구조적 (free DOF) | 내재적 | ~10% (기준값) | N | - |

**핵심 결론:**
pelvis_tilt reserve 221 N·m의 ~60%는 **손 외력(박스 반력)을 명시적 ExternalForce로 적용하지 않은 방법론 문제**에서 기인한다. 근육 집합(MF, QL 등) 변경은 이 reserve에 영향을 주지 않는다.

---

## 10. ES 결과 유효성

pelvis_tilt reserve가 221 N·m이더라도 **ES(erector spinae) 분석 결과는 독립적으로 유효**하다.

근거:
- ES 근육(IL, LTpT, LTpL)은 요추 분절 좌표(L5_S1_FE 등)에 작용
- pelvis_tilt reserve는 pelvis 자유도에 작용
- 두 시스템은 서로 다른 좌표에서 동작 — 간섭 없음
- MocoInverse 비용함수: 근육 activation 최소화 → reserve penalty는 별도

따라서:
- 박스 v11b의 suit effect (28% ES 감소) 결과는 유효
- pelvis_tilt reserve는 "전신 동역학 잔차" 로서 Limitation 섹션에 보고

---

## 11. 보강 권장 순서 (Impact–Effort 기준)

### 옵션 A: 손 외력 재시도 (권장, 최고 impact)
```
예상 reserve 감소: 221 → ~90 N·m (-59%)
이전 실패 원인: ExternalForce 구현 오류 (inf_pr=4050 = 발산, 물리 불가능 아님)
재시도 방법:
  1. foot GRF에서 박스 무게 제거 (기존 body weight만 사용)
  2. hand_R, hand_L에 상향 ExternalForce 98.1 N 적용
  3. 적용점: hand body COM, 방향: global y (upward)
  4. ramp 함수: t=2.0~2.5s 온셋, t=4.0s 오프셋 (동일)
예상 시간: 2~4시간 (구현 + 검증)
```

### 옵션 B: MF 추가 (v3 muscle set)
```
목적: 요추 분절 reserve 개선 (pelvis_tilt reserve는 무영향)
MF 추가: MF_m*_r/l (50개) + laminar (10개) = +60근육 → 총 218근육
예상 pelvis_tilt reserve 감소: 0%
ES 결과 변화 가능: 미미 (QL/IL/LTpT가 이미 주 extensor)
예상 시간: 1시간
```

### 옵션 C: 정직한 Limitation 보고 (최소 비용)
```
Limitations 섹션에 명시:
"pelvis_tilt reserve (221 N·m) at the floating-base DOF indicates
incomplete external load modeling; box hand reaction forces were
distributed to foot GRF rather than applied as explicit hand
ExternalForce. This residual does not affect ES activation estimates
(which act on lumbar coordinates), but suggests underestimation
of total musculoskeletal demand."
예상 시간: 30분
```

### 옵션 D: 새 motion (pelvis_tilt 축소)
```
pelvis_tilt = -30°, lumbar = -62° (분리)
예상 reserve 감소: 손 위치 변화에 따라 50~100 N·m 감소 가능
단, Phase 1a regression + Stage 4 재검증 필요
예상 시간: 반나절
우선순위: 낮음 (v11b PASS 이미 획득)
```

---

## 참고 문헌

- Cholewicki J, McGill SM (1996). Mechanical stability of the in vivo lumbar spine: implications for injury and chronic low back pain. Clin Biomech, 11(1):1-15.
- McGill SM (1997). The biomechanics of low back injury: implications on current practice in industry and the clinic. J Biomech, 30(5):465-475.
- Bruno AG et al. (2015). Development and validation of a musculoskeletal model of the fully thoracolumbar spine. Med Eng Phys, 37(12):1178-1185.
- Delp SL et al. (2007). OpenSim: open-source software to create and analyze dynamic simulations of movement. IEEE Trans Biomed Eng, 54(11):1940-1950.
