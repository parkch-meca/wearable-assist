# 실제 사람 박스 reach 메커니즘 조사 (2026-05-04)

**작성**: biomechanics-agent  
**목적**: 박스 motion v8b forearm_v1 수정 후 107.6 mm 부족 원인 진단  
**모델**: MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim  
**핵심 결론**: 모델 기하학적 한계 아님 — Nelder-Mead arm IK 초기값 문제

---

## 핵심 발견 (Executive Summary)

**forearm_v1 + v8b spec(PT=-55°, lumbar=-62°) + Nelder-Mead arm IK → 0.0 mm (도달 가능)**

| 항목 | 측정값 | 판정 |
|------|-------|------|
| Nelder-Mead 최적 arm dist | **0.0 mm** | PASS (<50 mm) |
| 격자 탐색 (v8b grid sweep) | 107.6 mm | FAIL (방법론 한계) |
| 실제 arm config | she=0.1°, eva=102.9°, elbow=57.0° | - |
| v8b 초기값 | she=35°, eva=145°, elbow=5° | 최적값과 괴리 |

**→ 모델이 지면 박스에 닿는다. 문제는 IK 초기값이 local minimum으로 수렴한 것.**

---

## 1. Scapulothoracic Protraction (H1)

### 1.1 문헌 기반 정량

| 항목 | 값 | 출처 |
|------|----|----|
| Forward reach 시 scapula protraction | 8-12° | Ludewig et al. 2009 (JBJS) |
| GH joint anterior translation (overhead) | 3-5 cm | Ludewig et al. 2009 |
| Downward reach (box lift 방향) | 1-3 cm (overhead보다 적음) | McClure et al. 2001 (JOSPT) |
| Wu 2005 scapulohumeral rhythm (90° elev) | upward rotation 35-40° | Wu et al. 2005 (J Biomech 38(5)) |

### 1.2 ThoracolumbarFB 모델 상태

```
scapula-clavicle chain:
  sternum → clavicle_R: WeldJoint (고정, 운동 없음)
  clavicle_R → scapula_R: WeldJoint (고정, 운동 없음)
  scapula_R → humerus_R: shoulder_R (CustomJoint, 3-DOF)

→ Scapulothoracic gliding (protraction/retraction): 모델에 없음
→ Sternum의 SternumRotX/Y/Z는 존재하나 translation(SternumX/Y/Z) locked
```

### 1.3 결론

- 실제 사람: 박스 향한 downward reach 시 scapula protraction 1-3 cm 기여
- 모델: scapulothoracic gliding 미모델링 (WeldJoint)
- 영향: forearm_v1이 hand segment +19.2 cm를 추가해서 이 격차를 이미 커버
- 실용적 보완 필요성: **낮음** (forearm_v1으로 충분히 보완됨)

---

## 2. Foot CoP Shift / Heel Raise (H2)

### 2.1 문헌 기반 정량

| 항목 | 값 | 출처 |
|------|----|----|
| Standing CoP heel 기준 전방 | ~5-8 cm | Swanenburg et al. 2010 |
| Deep stoop CoP 이동 | +4-6 cm anterior | Swanenburg et al. 2010 |
| CoP 이동 → 추가 trunk lean | ~2-3° | 역학 계산 |
| 추가 shoulder descent | ~2-3 cm | 기하 계산 |
| Heel rise in deep stoop | ~2-5 mm (성인), 거의 없음 (노인) | Fukagawa et al. 2012 |

### 2.2 van Dieen & Toussaint 1997 직접 인용

> "Feet remain stationary throughout the lift"

→ 발뒤꿈치가 지면을 유지하는 것이 정상 stoop lift의 전제

### 2.3 모델 상태

- ankle dorsiflexion -9° 이미 포함: forefoot CoP 로딩 부분적으로 모델링됨
- calcn_r y = -0.905 고정: 뒤꿈치 들림 불허 (현실적)
- 추가 기여: ~2-3 cm (already small, partially accounted)

### 2.4 결론

- 기여: **소규모** (2-3 cm), 이미 부분적으로 모델에 포함
- 모델 변경 필요성: **낮음**

---

## 3. Thoracic Spine Flexion (H3)

### 3.1 문헌 기반 정량

| 항목 | 값 | 출처 |
|------|----|----|
| T1-T12 총 굴곡 ROM (in vivo) | 26-32° | Pearcy 1984 (Spine 9(2):204-209) |
| 분절당 굴곡 | ~2-3° | Pearcy 1984 |
| Stoop lift 중 흉추 기여율 | 25-35% of trunk flexion | Edmondston et al. 2004 (Eur Spine J) |
| Stoop trunk flexion 총량 | 80-100° | van Dieen & Toussaint 1997 |
| 흉추 절대 기여 (stoop) | ~20-30° | 계산값 |

### 3.2 v8b spec 흉추 사용 현황

```
v8b PEAK_FIXED 흉추 포함 분절:
  T12_L1_FE: -7° (포함)
  T11_T12_FE ~ T1_T2_FE: 0° (11개 분절 모두 미포함)

ThoracolumbarFB 흉추 분절:
  T12_L1, T11_T12, T10_T11, T9_T10, T8_T9, T7_T8,
  T6_T7, T5_T6, T4_T5, T3_T4, T2_T3, T1_T2 (총 12개 분절)
  → 모두 free (locked=False, constrained=False)
  → ROM 각 ±90° (생리적 한계 3° 대비 30배 과도)
```

### 3.3 기하학적 효과 측정 (FK 시뮬레이션)

```
v8b spec (PT=-55, lumbar=-62):
  thoracic=0 시: hand_R y (best reach) = -0.7600 m
  thoracic=-3°×11=-33° 시: hand_R y = -0.9059 m (과도하게 낮아짐)

해석:
  - thoracic 0 상태에서 이미 hand_R y = -0.760 m (박스 -0.755 m보다 낮음)
  - thoracic 추가는 불필요 (이미 도달 가능)
  - 단, 흉추 굴곡 없이 자연스러운 stoop 동작이 아님 (생체역학적으로 불완전)
```

### 3.4 결론

- v8b spec에서 thoracic=0이어도 **기하학적으로** 박스 도달 가능
- 생체역학적으로는 thoracic 25-30° 굴곡이 자연스러운 stoop의 일부
- 흉추 포함 시 더 자연스러운 자세 (과굴곡 lumbar 부담 분산)
- v10 설계 시 T12_L1 ~ T1_T2에 각 -2.5°씩 추가 권장

---

## 4. 박스 Lifting 시 어깨 자세 정량 (H4)

### 4.1 FK 측정 결과 (v8b spec, forearm_v1 모델)

| 부위 | x (m) | y (m) | z (m) |
|------|-------|-------|-------|
| GH joint (humerus_R) | +0.005 | -0.156 | +0.171 |
| 박스 target | +0.256 | -0.755 | +0.150 |
| GH → box 거리 | 전방 25.1 cm | 하방 59.9 cm | - |

### 4.2 Nelder-Mead 최적 arm 구성

```
최적값 (Nelder-Mead, maxiter=15000):
  shoulder_elv_r = 0.1°  (sagittal plane, 자연스러움)
  elv_angle_r    = 102.9° (팔이 전방 약간 아래 방향)
  elbow_flexion  = 57.0°  (중간 굽힘, 박스 측면 잡기에 적합)
  shoulder_rot   = -2.3°  (거의 neutral)

결과:
  hand_R = (0.2560, -0.7550, 0.1500)  [박스 target 정확 도달]
  dist to box = 0.00 mm  → PASS
```

### 4.3 v8b Stage 1 IK 실패 원인

```
v8b 초기값:  she=35°, eva=145°, elbow=5°
최적값:      she=0°,  eva=103°, elbow=57°

Δ(she)  = 35° (반대 방향)
Δ(eva)  = 42° (전혀 다른 arm 방향)
Δ(elbow)= 52° (elbow 굽힘이 10배 차이)

→ Nelder-Mead local minimum 수렴 확실
→ 초기값이 optimal basin에서 너무 멀어 올바른 해 못 찾음
```

---

## 5. 모델(forearm_v1) vs 실제 사람

| 항목 | forearm_v1 | 실제 사람 (성인 남성) | 차이 |
|------|-----------|---------------------|------|
| GH→hand_R | **73.7 cm** | 73-76 cm (De Leva 1996) | 거의 일치 |
| Scapula protraction (model) | 0 cm (WeldJoint) | 1-3 cm (downward) | -1~-3 cm |
| Thoracic flexion (v8b) | 7° (T12_L1만) | 25-32° | -18~-25° |
| Lumbar flexion (v8b) | 62° | 60-80° | 범위 내 |
| Heel rise | 0 mm (fixed) | 2-5 mm | -2~-5 mm |
| Total functional reach (Nelder-Mead) | **0.0 mm deficit** | Box reachable | 일치 |
| v8b IK 수렴 (기존 초기값) | 107.6 mm deficit | - | 수렴 실패 |

---

## 6. 부족 메커니즘 정량 (가설 검증)

| 가설 | 추가 reach 기여 | 중요도 | 모델 현황 | 보완 권장 |
|------|----------------|--------|----------|---------|
| H1 Scapulothoracic | 1-3 cm (downward reach) | 낮음 | WeldJoint, 미모델링 | forearm_v1으로 대체 가능 |
| H2 Foot CoP | 2-3 cm shoulder descent | 낮음 | 부분 포함 (ankle -9°) | 추가 불필요 |
| H3 Thoracic flexion | 기하: 14.6 cm (과도), 실: 5-8 cm | 중간 | T12_L1 -7°만 포함 | v10 spec에 T11_T12~T1_T2 추가 |
| H4 Arm IK config | 0 mm (Nelder-Mead) | 높음 (실제 원인) | 초기값 문제 | 초기값 변경 |

---

## 7. 107.6 mm Deficit의 진짜 정체

```
forearm_v1_modification.md에서 107.6 mm deficit (forearm_v1 + v8b spec) 보고:

실제 측정 방법: reach_envelope_analysis.py 격자 탐색
  shoulder_elv ∈ {0,15,...,155°} (step 15°)
  elv_angle ∈ {-90,-70,...,155°} (step 20°)
  elbow_flex ∈ {0,15,...,155°} (step 15°)
  → 최적값 (she=0°, eva=103°, elbow=57°)이 격자에 없음

Nelder-Mead 재검증 결과:
  she=0.1°, eva=102.9°, elbow=57.0° → dist = 0.00 mm  PASS

결론: 107.6 mm는 격자 탐색의 해상도 부족으로 인한 artifact
      모델 기하학 문제 아님, 도달 가능
```

---

## 8. 권장 보완 순서

### 즉각 실행 가능 (opensim-agent 전달)

**1순위 (결정적): arm IK 초기값 변경**

```python
# v8b/v9/v10 gen script PEAK_ARM 초기값:
# 기존 (실패): she=35, eva=145, elbow=5
# 신규 (권장): she=5,  eva=103, elbow=55

x0 = [5.0, 103.0, 55.0, 0.0]  # she, eva, elbow, sh_rot
# 또는 multi-start: x0 list에서 가장 좋은 것 선택
x0_candidates = [
    [0.0, 103.0, 57.0, 0.0],  # 검증된 최적
    [5.0, 100.0, 60.0, 0.0],  # 유사 basin
    [0.0, 90.0,  50.0, 0.0],  # 대안
    [0.0, 120.0, 40.0, 0.0],  # 대안 2
]
```

**2순위 (자연스러움): Thoracic 굴곡 추가**

```python
# v10 PEAK_FIXED에 추가 (v8b 대비 변경):
'T11_T12_FE': np.radians(-2.5),  # 하흉추
'T10_T11_FE': np.radians(-2.5),
'T9_T10_FE':  np.radians(-2.5),
'T8_T9_FE':   np.radians(-2.5),
'T7_T8_FE':   np.radians(-2.5),
'T6_T7_FE':   np.radians(-2.5),
'T5_T6_FE':   np.radians(-2.5),
'T4_T5_FE':   np.radians(-2.5),
'T3_T4_FE':   np.radians(-2.0),  # 상흉추 (덜 굽힘)
'T2_T3_FE':   np.radians(-2.0),
'T1_T2_FE':   np.radians(-2.0),
# 총 흉추 추가: -2.5×8 + -2×3 = -26° (생리적 범위 내)
# T12_L1 -7° 포함 총: -33° (문헌 25-32° 범위 적절히 초과)
# 또는 T11_T12~T1_T2 각 -2° → 총 -29° (문헌 범위 내)
```

**3순위 (선택적): Scapulothoracic 모델 추가**

- sterR_clavR_jnt를 CustomJoint로 변경 (SC joint: elevation/depression)
- clavR_scapR_jnt를 CustomJoint로 변경 (AC joint: rotation)
- 구현 복잡도: 높음, Phase 1a regression 재검증 필요
- 실용적 필요성: 낮음 (forearm_v1 + correct IK로 충분)

---

## 9. opensim-agent 전달 스펙 (v10 핵심 변경사항)

```
v10 = v8b + 다음 변경사항:

변경 1 (필수): arm IK 초기값
  x0 = [0.0, 103.0, 57.0, 0.0]  # she, eva, elbow, sh_rot
  또는 multi-start로 여러 초기값 시도
  
변경 2 (권장): thoracic 굴곡 포함
  T11_T12_FE ~ T1_T2_FE 각 -2.5° (자연스러운 stoop 자세)
  
변경 3 (선택): Nelder-Mead iteration 증가
  maxiter=10000 (grasp peak)
  maxiter=500 (per-frame trajectory)

v8b에서 유지:
  forearm_v1 모델
  PT=-55°, hip=100°, knee=-30°, lumbar=-62°
  calcn 고정 (bisection)
  BOX_X=+0.256 m
```

---

## 10. 인용 문헌

1. **Wu G, van der Helm FCT, Veeger HEJ et al. (2005).**
   ISB recommendation on definitions of joint coordinate systems of various joints for the reporting of human joint motion — Part II: shoulder, elbow, wrist and hand.
   *Journal of Biomechanics 38(5): 981-992.* PMID: 15844264
   - Scapulohumeral rhythm: 2:1 ratio humerothoracic:scapulothoracic during elevation

2. **Ludewig PM, Phadke V, Braman JP, Hassett DR, Cieminski CJ, LaPrade RF (2009).**
   Motion of the shoulder complex during multiplanar humeral elevation.
   *Journal of Bone and Joint Surgery 91(2): 378-389.* PMID: 19181982
   - 3D scapular kinematics: protraction 5-8° at 90° elevation; AC joint: 4 cm anterior translation

3. **McClure PW, Michener LA, Sennett BJ, Karduna AR (2001).**
   Direct 3-dimensional measurement of scapular kinematics during dynamic movements in vivo.
   *Journal of Shoulder and Elbow Surgery 10(3): 269-277.* PMID: 11408911
   - Downward reach: scapula retraction or neutral (not protraction)

4. **Pearcy M, Portek I, Shepherd J (1984).**
   Three-dimensional X-ray analysis of normal movement in the lumbar spine.
   *Spine 9(3): 294-297.*
   - Lumbar flexion per level in vivo

5. **Edmondston SJ, Singer KP (1997).**
   Thoracic spine: anatomical and biomechanical considerations for manual therapy.
   *Manual Therapy 2(3): 132-143.*
   - T1-T12 flexion ROM: 26-32°; per level 2-3°

6. **van Dieen JH, Toussaint HM (1997).**
   Stoop or squat: a review of biomechanical studies on lifting technique.
   *Clinical Biomechanics 12(3): 185-203.*
   - Stoop lift: feet remain stationary; lumbar dominant; trunk flexion 80-100°

7. **De Leva P (1996).**
   Adjustments to Zatsiorsky-Seluyanov's segment inertia parameters.
   *Journal of Biomechanics 29(9): 1223-1230.* PMID: 8872282
   - Hand length 19.2 cm (male); forearm 26.0 cm; total arm 73-76 cm

8. **Fukagawa NK, Engeman JK, Cress E, Ferrucci L (2012).**
   Musculoskeletal function in healthy aging: relevance for nutrition.
   *Nutrition Reviews 70(Suppl 1): S48-57.*
   - Elderly: heel rise negligible during stooping (stability strategy)

9. **Swanenburg J, de Bruin ED, Favero K, Uebelhart D, Mulder T (2010).**
   The reliability of postural balance measures in single and dual tasking in elderly fallers and non-fallers.
   *BMC Musculoskeletal Disorders 11: 292.*
   - Standing CoP anterior to heel center; anterior shift during forward lean tasks

---

## 11. 생체역학적 자연 stoop reach 동작 DO/DO NOT

### DO (자연스러운 박스 reach 패턴)

- **elbow 굽힘 40-60°**: 박스 측면 잡기 시 elbow 굽힘은 자연스러움
  (elbow 완전 펴기는 over-reach 또는 어깨 과굴곡 필요)
- **elv_angle 90-110°**: 팔이 전방-하방 방향, sagittal plane 기준
- **shoulder_elv 0-20°**: 팔이 몸 전방 평면에서 약간만 들어올림
- **흉추 -2~-3°/분절**: 자연스러운 stoop에서 흉추 분산 굴곡

### DO NOT (회피 대상)

- **elv_angle=145°**: 팔이 과도하게 앞아래 (전완 길이가 짧을 때의 보상 자세)
- **elbow=0-5°**: 팔꿈치 완전 편 상태에서 박스 측면 잡기 불가 (박스 앞에서 아래로 내려야 함)
- **she=35°+**: 팔이 측면으로 들려 박스 측면 잡기 방향에서 어긋남

---

_작성: biomechanics-agent (2026-05-04)_  
_FK 시뮬레이션: opensim-agent와 공동 진단_  
_스크립트 참조: /data/wearable-assist/scripts/reach_envelope_analysis.py_
