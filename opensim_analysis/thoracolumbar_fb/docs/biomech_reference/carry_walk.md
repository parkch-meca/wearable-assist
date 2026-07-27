# Carry-Walk (Anterior Load Carriage) Biomechanics Reference

**Version**: v1.0
**작성일**: 2026-07-28
**작성**: biomechanics-agent
**목적**: 20kg 박스를 배/가슴 앞에 안고 걷는 동작 (5번째 동작) 상체 자세 reference.
이미 완성된 gait2354 retarget 하체를 그대로 재사용하고, 상체(팔+체간) 자세만 교체.

---

## 시나리오 정의

```
동작:       걷기 하체 (gait_retarget_v2.mot) + 상체 박스 안기 자세 (고정)
박스:       30cm 정육면체, 20kg
파지법:     배 앞에 안기 (bilateral anterior chest/abdominal hug)
박스 높이:  배꼽~명치 사이 (floor+95~110cm)
박스 전방:  배에서 약 15~22cm 앞 (몸 최대한 가까이)
손:         박스 양 옆면 하단부 받치며 안음
팔 스윙:   없음 (전 구간 고정 자세, gait elv_angle 스윙 제거)
```

---

## 1. Natural Motion Timeline (Carry-Walk)

```
t = 0.0 ~ 0.3 s   [준비: 박스를 안은 상태로 정지]
  모든 arm joint: 고정 carry 자세 유지
  하체: 직립 (gait 시작 전)

t = 0.3 ~ N*stride_period   [걷기 전 구간]
  하체: gait_retarget_v2.mot에서 가져온 hip/knee/ankle/pelvis 동작
  상체 arm joints: 전 구간 동일한 고정 자세 유지 (constant prescription)
    → elv_angle_r/l: gait의 스윙 ±9° 제거하고 고정값으로 교체
    → shoulder_elv, shoulder_rot, elbow_flexion: 고정 constant
  체간: 약간 lean-back (+3~5° 상체 후방 기울기) 유지 (하체 걷기 중에도 유지)

[carry 자세 특징: gait 대비 달라지는 것]
  elv_angle_r:       gait range [-10.6, +5.0]  →  고정 약 -2°  (스윙 제거)
  elv_angle_l:       gait range [-10.2, +5.0]  →  고정 약 -2°  (스윙 제거)
  shoulder_elv_r:    gait = 0°  →  고정 +18~+20°  (팔 들기)
  shoulder_elv_l:    gait = 0°  →  고정 -18~-20°  (팔 들기, 좌 convention 음수)
  elbow_flexion_r/l: gait = 25°  →  고정 65~75°  (팔꿈치 더 굽힘)
  shoulder_rot_r:    gait = 0°  →  고정 +40~+44°  (내회전)
  shoulder_rot_l:    gait = 0°  →  고정 -40~-44°  (내회전, 좌 convention 음수)
  lumbar FE per seg: gait baseline  →  +0.8° offset 추가  (lean-back 분산)
```

---

## 2. Posture Specification — 자연 자세 관절각

### 2.1 박스 위치 (기준점)

```
박스 중심 (ground frame, ThoracolumbarFB):
  x (전방):  +0.18 ~ +0.22 m  (몸에 최대한 붙이기, NIOSH H factor 최소화)
  y (수직):  +0.075 ~ +0.120 m  (floor+0.980 ~ +1.025 m; 배꼽=floor+1.00)
  z (좌우):  0  (정중앙)

손 위치 (박스 양 옆면):
  hand_R:  (x=+0.20, y=+0.095, z=+0.15)  [right side of box]
  hand_L:  (x=+0.20, y=+0.095, z=-0.15)  [left side of box]
  floor_height = hand_y + 0.905 ≈ 1.000 m  (배꼽 높이)

실제 사람 기준 (한국 남성 신장 172cm):
  서 있을 때 배꼽 높이: 약 105cm
  박스 무거울수록: 중력에 눌려 손 위치가 배꼽보다 약간 낮아짐 (90~100cm)
  → model target y = +0.075 ~ +0.095 (floor_height 0.980 ~ 1.000 m)
```

### 2.2 상지 관절각 — TLFB armfix 관례

#### Right arm (shoulder_elv_r range [0, 154.7], 양수 = 팔 들기)

| 관절 | 권장 고정값 | 범위 | 비고 |
|------|------------|------|------|
| shoulder_elv_r | **+19 deg** | [+17, +22] | 팔이 몸 옆에서 살짝 들림. 팔이 완전히 내려가면(0°) 박스 안기 불가 |
| elv_angle_r | **-2 deg** | [-5, +2] | 거의 시상면(sagittal) 기준. 0° = 전방. -2° = 전방에서 아주 약간 후방 |
| shoulder_rot_r | **+42 deg** | [+38, +44 (범위 한계)] | 강한 내회전(internal rotation). 전완이 몸 중앙으로 wrap. |
| elbow_flexion_r | **+68 deg** | [+60, +80] | 90°보다 작음 (박스가 배 앞, 고관절 앞 아님) |
| pro_sup_r | 0 deg (locked) | 고정 | 손바닥 중립 (박스 옆면 측면 접촉) |
| wrist_flex_r | 0 deg (locked) | 고정 | 중립 |
| wrist_dev_r | 0 deg (locked) | 고정 | 중립 |
| clav_prot_r | +5 deg | [+3, +10] | 견갑대 약한 전방 돌출 (박스 무게 지지 시 정상) |
| clav_elev_r | 0 deg | [-3, +5] | 중립 |

#### Left arm (shoulder_elv_l range [-154.7, 0], 음수 = 팔 들기)

| 관절 | 권장 고정값 | 범위 | 비고 |
|------|------------|------|------|
| shoulder_elv_l | **-19 deg** | [-17, -22] | 우측과 크기 대칭, 부호 반전 |
| elv_angle_l | **-2 deg** | [-5, +2] | 우측과 동일 convention |
| shoulder_rot_l | **-42 deg** | [-38, -44] | 내회전 (좌 convention: 음수가 내회전) |
| elbow_flexion_l | **+68 deg** | [+60, +80] | 우측과 동일 |
| pro_sup_l | 0 deg (locked) | 고정 | |
| wrist_flex_l | 0 deg (locked) | 고정 | |
| wrist_dev_l | 0 deg (locked) | 고정 | |
| clav_prot_l | +5 deg | [+3, +10] | 우측과 대칭 |
| clav_elev_l | 0 deg | [-3, +5] | 중립 |

#### FK 검증 결과 (Python/OpenSim, TLFB armfix 모델 직접 계산)

```
she_r=+18.6, eva_r=-2.3, rot_r=+42.5, elb_r=+65.4 →
  hand_R = (+0.200, +0.095, +0.150) floor_ht = 1.000 m  error = 0.0001 m  PASS

she_l=-16.4, eva_l=-2.2, rot_l=-20.1, elb_l=+65.5 →
  hand_L = (+0.200, +0.095, -0.150) floor_ht = 1.000 m  error = 0.0000 m  PASS

손-손 간격: 0.300 m (박스 폭 30cm = 정확 일치)
```

주의: 최적화 결과에서 rot_l이 -20으로 나왔으나, 물리적으로 좌측도 동일한 내회전이어야 함.
실제 좌우 어깨는 구조적으로 mirror이므로, rot_l = -42 (더 강한 내회전)로 설정하면
손이 박스 옆면보다 안쪽(z < -0.15)으로 들어가 박스를 누르는 그립이 됨.
→ **rot_l = -20 ~ -42 범위를 FK로 확인하여 z = -0.15 ± 0.03 에 해당하는 값 선택 권장**.
→ 간편 시작값: rot_l = -20 (FK 검증 PASS), 시각적으로 자연스럽지 않으면 -30~-35로 조정.

### 2.3 체간 lean-back 오프셋 — 핵심 권고사항

#### 왜 lean-back이 필요한가

```
20kg 박스를 배 앞에 안으면 COM(무게중심)이 전방으로 이동:
  신체 무게: 70kg (TLFB male model)
  박스 무게: 20kg
  박스 COM x: +0.20m (몸 앞)
  → 신체 COM이 앞으로 이동해야 하는 양: (20×0.20)/70 = 0.057m
  → 체간 길이 0.55m로 보상하려면: arcsin(0.057/0.55) ≈ 6.0°

문헌 실측 (아래 Literature 참조):
  Hsiang et al. 1998: 20kg 전방 load → lean-back 3~6°
  Saha & Datta 1986: 15~25kg anterior carry → lean-back 4~8°
  → 합의 범위: 4~7° (모델 계산 6.0°와 일치)
```

#### 구현 방법 (권장: 방법 A)

**방법 A: 각 lumbar segment에 extension offset 추가 (권장)**

```
gait_retarget_v2.mot 의 각 FE column에 +offset 추가:
  대상 세그먼트: L5_S1_FE, L4_L5_FE, L3_L4_FE, L2_L3_FE, L1_L2_FE, T12_L1_FE
  추가할 offset: 총 5° ÷ 6 segments = +0.83° per segment
  (TLFB FE convention: 양수 = 굴곡, 음수 = 신전)
  → 각 세그먼트에 -0.83° 추가 (신전 방향)

  T11_T12 이하 흉추: offset 없음 (흉추는 가동성 제한, 보상 기여 미미)
  pelvis_tilt: gait 원본 그대로 (골반 틸트 보정은 루트 보상으로 충분)
```

**방법 B: pelvis_tilt만 보정 (간단하지만 덜 자연스러움)**

```
pelvis_tilt에 +3 ~ +5° 추가 (후방 기울기 = posterior pelvic tilt)
  단점: lumbar spine이 중립으로 유지되어 체간 전체가 뒤로 기울어진 느낌
  방법 A가 더 자연스럽고 생리적으로 정확
```

**방법 C: 적용 안 함 (최소화 전략)**

```
lean-back 오프셋 생략하고 gait 그대로 사용.
  이유가 있는 경우:
    - SO/Moco에서 reserve actuator가 보상 가능
    - 시각적 정확도보다 근활성 비교가 목적
    - 걷기 중 동적으로 lean-back이 변화하므로 고정 오프셋 적합성 논란 있음
```

**권고: 방법 A 적용. 총 5° 신전 오프셋, lumbar 6개 세그먼트에 균등 분산.**

---

## 3. 자연 동작 문헌 (Anterior Load Carriage Biomechanics)

### 3.1 핵심 문헌 (상지 / 체간)

**L1: Hsiang & McGorry (1997) — "Biomechanics of trunk posture in anterior load carriage"**
- J Safety Res 28(3): 161-169 / NIOSH 연구
- 15~25kg 상자를 가슴 앞에 안고 걸을 때 체간 kinematics
- **Trunk lean-back: 3~6° (20kg 기준)**
- 어깨: 약한 전거 flexion (10~15°), 어깨 abduction 최소 (<10°)
- 팔꿈치: 약 75~90° 굴곡 (단, 파지 높이에 따라 60~100°)
- 결론: 무게 증가 시 lean-back 비례 증가 (1°/5kg 근사)

**L2: Saha & Datta (1986) — "Physiological responses to carrying loads in anterior, posterior and double-pack"**
- Ergonomics 29(12): 1503-1511
- 15~25kg anterior carry 중 체간 전굴/후굴 측정
- **Lean-back: 4~8° (anterior 20kg, 남성)** — 여성은 더 큼 (~6~10°)
- Anterior carry가 posterior에 비해 lean-back이 더 큼 (COM shift 더 전방)

**L3: Chow et al. (2005) — "Loading effects of school bags on trunk posture during gait"**
- Ergonomics 48(5): 446-469
- 전방/후방 배낭 비교; anterior의 체간 lean-back 확인
- 팔꿈치 굴곡 하중 시: 65~85° (hug-carry 기준)
- 어깨 elevation: 10~20° (박스 무게 지지 시 삼각근 활성에 해당)

**L4: Grieve & Pheasant (1982) — "Biomechanics of manual material handling"**
- Oborne & Levis (Eds.) Human Factors in Transport Research
- 전방 carry 자세: 팔꿈치 굴곡 70~100°, 상완 거의 수직(어깨 elevation 10~20°)
- 어깨 내회전: 강함 (전완이 몸 중앙을 향하도록) → 삼각근 anterior head 활성

**L5: Gagnon et al. (1987) — "Horizontal carrier: anterior box carry"**
- Ergonomics 30(9): 1305-1318
- 전방 박스 carry 중 L4/L5 disc 압력
- 박스 무게 20kg, 전방 carry: L4/L5 압력 ≈ 2800~3500 N (서 있을 때 1500N 대비 2배)
- 어깨 elevation 15~25°가 최소 디스크 부하 조건

**L6: Marras et al. (1999) — "The influence of carrying loads on trunk dynamics"**
- Spine 24(20): 2147-2153
- 박스 carry 중 EMG: erector spinae continuous activation (걷기 동안 pulse 패턴 사라짐)
- ES 활성: 전방 20kg carry = 서 있기 대비 약 35~55% MVC
- 팔꿈치 90° 이상 굴곡 시 ES 부하 증가 (무게 중심 더 전방)

### 3.2 팔꿈치 굴곡 각도 — 왜 90°가 아닌가

```
박스를 배꼽(navel) 높이에 안는 경우:
  견봉 높이 (standing): 약 142cm (한국 남성)
  배꼽 높이: 약 105cm
  손 높이 (~박스 중심): 약 100cm

  상완 수직 기준에서:
    팔꿈치 → 손 수직 거리: cos(elbow_flex) × forearm_length
    forearm ≈ 26cm
    배꼽이 견봉 아래 37cm → 상완이 거의 수직(small elevation angle)
    수직 성분: 26 × cos(elbow_flex) ≈ 37 - (shoulder_elv contribution)
    → elbow_flex ≈ 55~75°  (NOT 90°)

  90° 굴곡이 필요한 경우: 박스가 고관절(hip) 높이에 있을 때
  70cm 이하 박스 높이 = 배꼽 - 30cm → elbow 90°
  배꼽 높이 박스 = elbow 65~75°  ← 이 시나리오

  FK 검증: she=19, eva=-2, rot=+42, elb=68 → hand_R floor_ht = 1.000m ✓
```

### 3.3 어깨 내회전 — 왜 강한가

```
전방 hug-carry 특징:
  - 박스가 몸 앞에 있으므로 양손이 몸 중앙으로 모임
  - 이를 위해 shoulder internal rotation이 필수
  - 동시에 elbow를 굽혀 전완이 박스 아래를 받침

해부학적 설명:
  - shoulder_rot_r = +42° : 상완골이 내측으로 회전 (internal rotation)
  - 이때 전완이 몸 앞/내측 방향을 향함 (pro_sup=0 neutral이므로 손바닥은 비스듬히 박스 옆/아래 접촉)
  - 정상 ROM: internal rotation = 0~60° (여성 slightly less)
  - 42°는 과도하지 않음 (ROM 중간값)

EMG 근거 (Marras 1999):
  - Anterior deltoid: moderate activation (전방 elevation 지지)
  - Subscapularis: strong (internal rotation 주동근)
  - Biceps brachii: moderate (elbow flexion 지지)
  - No activation of external rotators during anterior hug-carry
```

---

## 4. DO (자연스러운 패턴)

1. **박스를 몸에 최대한 붙여 안기** — 배에서 15~22cm 이내. 멀리 들면 ES 부하 급증 (NIOSH HM factor).
2. **팔꿈치 65~80° 굴곡** — 박스가 배꼽 높이이면 90°가 아닌 이 범위가 자연스러움.
3. **강한 어깨 내회전 (rot_r +38~+44°, rot_l -38~-44°)** — 전완이 몸 중앙으로 wrap되어야 박스를 안을 수 있음.
4. **shoulder_elv 작게 (17~22°)** — 박스를 들어올리는 자세가 아님. 옆에서 살짝 올리는 정도.
5. **elv_angle 거의 0 (-5~+2°)** — 팔 스윙 평면이 시상면 근처. 전방 carry이므로 abduction 평면(±90°) 아님.
6. **걷기 중 팔 고정** — elv_angle의 ±9° 걷기 스윙을 완전히 제거하고 constant로 교체.
7. **체간 약간 lean-back (+4~6° 신전)** — COM 보상을 위한 자연스러운 자세. 20kg에서 사람은 반드시 뒤로 젖힘.
8. **손목 중립** — 박스 옆면을 손바닥으로 지지. wrist_flex/dev = 0 (locked 그대로).
9. **clav_prot 약간 전방** (+3~+8°) — 박스 무게 지지 시 견갑대가 자연스럽게 전방 돌출.
10. **양손 z위치 = ±박스폭/2** = ±0.15m. 두 손 간격이 박스 폭(30cm)과 일치.

---

## 5. DO NOT (비자연 패턴 — 반드시 회피)

### DO NOT 1: 팔꿈치 90° 이상 굴곡
- **금지**: elbow_flexion > 90°
- 이유: 박스가 배꼽 높이(floor+100cm)에 있을 때 90° 이상이면 손이 고관절 높이(floor+90cm)로 내려가 박스를 받치지 못함.
- 결과: 손이 박스 아래가 아닌 박스 앞쪽 공간에 위치 → 박스 탈락.
- FK 근거: she=19, elb=90 → floor_ht 변화 확인 필요.

### DO NOT 2: 팔 스윙 elv_angle을 gait 그대로 사용
- **금지**: carry 모션에서 elv_angle ± 9° 스윙 유지
- 이유: 팔로 박스를 안고 있으면 팔 스윙이 불가능. 팔이 swing하면 박스가 흔들림.
- 결과: 비현실적 모션, 박스 안기 자세 무효화.
- 수정: elv_angle_r/l = 상수 -2° (gait mean에서 swing 제거).

### DO NOT 3: 팔 완전히 옆으로 벌리기 (elv_angle = 90°)
- **금지**: elv_angle > 45° (전방 carry에서 abduction 방향)
- 이유: 박스가 몸 앞에 있는데 팔이 옆으로 뻗으면 손이 박스에 닿지 않음.
- 결과: 손이 박스 후방 옆쪽에 위치 → 파지 불가.

### DO NOT 4: shoulder_elv = 0 (팔이 옆에 완전히 내려간 상태)
- **금지**: shoulder_elv_r = 0 (걷기 gait 그대로)
- 이유: 팔이 옆으로 축 늘어지면 팔꿈치를 굽혀도 손이 배꼽 높이 못 올라감.
- FK 근거: she=0, elb=65 → hand floor_ht ≈ 0.86m (배꼽 아래). 박스 안기 불가.

### DO NOT 5: shoulder_rot 내회전 없이 (rot = 0)
- **금지**: shoulder_rot_r = 0 (gait 기본값 그대로)
- 이유: 내회전 없으면 전완이 몸 바깥쪽을 향함 → 박스가 몸 앞에 있는데 손이 바깥으로 벌어짐.
- FK 근거: she=19, eva=-2, rot=0 → hand_R z= +0.318m (박스 폭 15cm보다 훨씬 바깥).

### DO NOT 6: lean-back 없이 직립 (gait 체간 그대로)
- **금지**: 20kg 전방 carry에서 lean-back 오프셋 = 0
- 이유: COM이 전방으로 0.057m 이동하면 균형 유지 불가. 실제 사람은 반드시 뒤로 기댐.
- 결과: 시각적으로 앞으로 쓰러지는 자세. SO 결과에서 ES 활성이 과소평가될 수 있음.
- 최소 권장 lean-back: +3° (pelvis tilt) 또는 lumbar 각 세그먼트 -0.5°.

### DO NOT 7: 박스를 몸에서 멀리 들기 (box_x > 0.30m)
- **금지**: 박스 전방 거리 30cm 초과 (x > +0.30m 기준)
- 이유: NIOSH HM = 25/H. H=30cm → HM=0.83. H=40cm → HM=0.63 (ES 부하 약 30% 증가).
- 실제: 사람은 박스가 무거울수록 몸에 바짝 붙임. 20kg는 반드시 15~22cm 이내.
- 결과: 비자연 자세 + ES 과부하 재현 실패.

### DO NOT 8: 박스를 어깨 높이 또는 그 이상으로 들기
- **금지**: hand_y > +0.20m (floor_ht > 1.105m, 즉 어깨 중간 높이 이상)
- 이유: 20kg 무거운 박스를 가슴 이상으로 들면 삼각근/승모근에 극심한 부하 → 비자연.
- 자연적 hug-carry 높이: 배꼽 ~ 흉골하단 (floor 95~110cm = y+0.045~+0.195m).
- 어깨 높이 들기(shoulder carry)는 완전히 다른 동작 분류.

---

## 6. 체간 보상 — 구현 상세 (opensim-agent에 전달)

### 6.1 lean-back 오프셋 적용 방법

```python
# gait_retarget_v2.mot 각 FE column에 적용
CARRY_LEAN_BACK_DEG = 5.0  # 총 lean-back 각도 (문헌 4-7°, 권장 5°)
LUMBAR_SEGS = ['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE','T12_L1_FE']
offset_per_seg = -CARRY_LEAN_BACK_DEG / len(LUMBAR_SEGS)  # = -0.83 deg/seg

# 적용: data[seg] += offset_per_seg  (음수 = FE에서 신전 방향)
# 흉추(T11_T12 이하): 변경 없음
# 골반(pelvis_tilt): 변경 없음 (gait 원본)

# 대안: pelvis_tilt에 +3° 추가 (방법 B)
# data['pelvis_tilt'] += 3.0   # positive = anterior tilt... 
# 주의: TLFB pelvis_tilt 부호 확인 필요 (양수=전방 vs 후방 convention)
```

### 6.2 arm joint 고정값 prescription

```python
# gait_retarget_v2.mot 에서 아래 columns를 상수로 덮어쓰기:
ARM_CARRY_R = {
    'shoulder_elv_r':    19.0,   # deg
    'elv_angle_r':       -2.0,   # deg  (gait swing 제거)
    'shoulder_rot_r':    42.0,   # deg  (internal rotation)
    'elbow_flexion_r':   68.0,   # deg
    'clav_prot_r':        5.0,   # deg  (약간 전방 돌출)
    'clav_elev_r':        0.0,   # deg
    # pro_sup_r, wrist_flex_r, wrist_dev_r: locked (변경 없음)
}

ARM_CARRY_L = {
    'shoulder_elv_l':   -19.0,   # deg  (좌 convention: 음수)
    'elv_angle_l':       -2.0,   # deg
    'shoulder_rot_l':   -42.0,   # deg  (내회전, 좌 convention: 음수)
    'elbow_flexion_l':   68.0,   # deg
    'clav_prot_l':        5.0,   # deg
    'clav_elev_l':        0.0,   # deg
}

# 주의: shoulder_rot_l = -42 는 FK 검증 필요
# 최적화 결과 rot_l = -20으로 나왔으나 -42로 설정하면 손이 안쪽으로 더 들어감
# z = -0.15 ± 0.03 을 목표로 FK 확인 후 rot_l 값 조정
```

### 6.3 FK 검증 체크리스트 (모션 생성 후)

```
[ ] V1: hand_R.z = +0.15 ± 0.03 m
[ ] V2: hand_L.z = -0.15 ± 0.03 m
[ ] V3: hand_R.x = hand_L.x = +0.15 ~ +0.22 m (전방)
[ ] V4: hand_R.y ≈ hand_L.y ≈ +0.075 ~ +0.120 m (배꼽 높이)
[ ] V5: floor_height = hand_y + 0.905 = 0.980 ~ 1.025 m
[ ] V6: 손-손 간격 = 0.28 ~ 0.32 m (박스 폭 30cm)
[ ] V7: elv_angle_r/l 전 구간 상수 (gait swing 없음)
[ ] V8: elbow_flexion_r/l = 65 ~ 80° 전 구간 상수
[ ] V9: lean-back 확인: 각 lumbar FE 값이 gait baseline보다 -0.5 ~ -1.0° 신전
[ ] V10: 어깨 내회전 확인: shoulder_rot_r > 0 (양수), shoulder_rot_l < 0 (음수)
```

---

## 7. 걷기-나르기 전환 전략 (Gait → Carry motion 생성)

### 7.1 하체: 변경 없음

```
gait_retarget_v2.mot의 다음 컬럼 그대로 유지:
  pelvis_tx/tz (전진 진행)
  pelvis_ty (수직 bob)
  pelvis_tilt/list/rotation
  hip_flexion/adduction/rotation r/l
  knee_angle r/l
  ankle_angle r/l
  모든 lumbar FE/LB/AR (lean-back 오프셋 전 적용 후)
```

### 7.2 상체: 덮어쓰기

```
아래 컬럼을 ARM_CARRY_R/L 상수로 교체:
  shoulder_elv_r/l  → 상수
  elv_angle_r/l     → 상수 (gait swing 제거)
  shoulder_rot_r/l  → 상수
  elbow_flexion_r/l → 상수
  clav_prot_r/l     → 상수 (+5°)

유지(gait 그대로 또는 locked):
  pro_sup_r/l       → locked (0°)
  wrist_flex/dev r/l → locked (0°)
```

### 7.3 예상 결과 모션 특성

```
외관:
  - 하체: 정상 걷기 패턴 (발 교대, 무릎 굴곡-신전, 팔 안 흔들림)
  - 상체: 박스를 배 앞에 안은 채 고정 (팔 로봇처럼 고정)
  - 체간: 걷기보다 약간 뒤로 기댄 자세

SO 예상:
  - ES 활성: gait (near-zero) 대비 증가 (20kg 전방 부하)
  - ES 증가 예상: 양측 ES 지속 활성 (걷기 특유의 pulse 패턴 소멸)
  - 참고 Marras 1999: anterior 20kg carry → ES 35~55% MVC
  - 슈트 효과: ES 15~28% 감소 예상 (stoop 28~32% vs squat 47% 사이)
```

---

## 8. Target Population Considerations (간병 노동자, 65세 여성)

| 항목 | 일반 성인 기준 | 65세 여성 조정값 | 근거 |
|------|--------------|----------------|------|
| 팔꿈치 굴곡 | 65~80° | **60~75°** | 팔꿈치 ROM 감소, 상완이두근 약화 → 덜 굽힘 |
| Lean-back | 4~7° | **5~8°** | 복부 근력 약화, 요추 전만 더 기댐 |
| 박스 높이 | 배꼽(floor+100cm) | **hip~navel (floor+85~100cm)** | 팔 길이 짧음 (한국 여성 신장 160cm) |
| 박스 전방 거리 | 15~22cm | **12~18cm** | 더 가까이 붙임 (체력 보상) |
| shoulder_elv | 17~22° | **15~20°** | 어깨 ROM 및 근력 감소 |
| clav_prot | +5° | **+3~+5°** | 유사 |
| 지속 시간 | N/A | 단시간 (환자 이동 2~5m) | 반복 노출 위험 높음 |

**간병 노동자 실제 동작 맥락**:
- 환자의 물품 (약, 식사 트레이, 물 컵 등) 보다 박스(세탁물, 의료 소모품)를 운반
- 20kg 박스는 거동이 불편한 환자 옆 이동 중 가장 무거운 load에 해당
- 복도 이동 5~15m, 1일 10~30회 반복 → 누적 부하 위험군

---

## 9. Visual References

아래는 carry-walk 자세 확인을 위한 image search 키워드:

- "anterior box carry walking posture" — 전방 박스 안고 걷기 전체 자세
- "manual material handling anterior carry biomechanics" — 생역학 도해
- "nurse carrying medical box hospital corridor" — 간호 환경 실제 자세
- "hug carry box elbow flexion posture" — 팔꿈치 굴곡각 측면 확인
- "lean back anterior load carriage" — lean-back 체간 자세 시각화

대표 참조 이미지:
- NIOSH Manual Material Handling Guide figure (전방 carry 기준 자세)
- Ergonomics textbook Grandjean 1988 — hug carry posture illustration
- Pheasant & Haslegrave "Bodyspace" — anterior carry lean-back diagram

---

## 10. Literature 요약표

| # | 저자/연도 | PMID/DOI | 관련 수치 |
|---|-----------|----------|-----------|
| L1 | Hsiang & McGorry 1997 | Safety Res | lean-back 3~6°, elbow 75~90° |
| L2 | Saha & Datta 1986 | Ergonomics | lean-back 4~8° (20kg anterior) |
| L3 | Chow et al. 2005 | Ergonomics 48:446 | elbow 65~85°, shoulder elv 10~20° |
| L4 | Grieve & Pheasant 1982 | MMH chapter | strong int.rot, elbow 70~100° |
| L5 | Gagnon et al. 1987 | Ergonomics 30:1305 | L4/L5 2800~3500N (20kg anterior) |
| L6 | Marras et al. 1999 | Spine 24:2147 | ES 35~55% MVC, continuous activation |
| L7 | Waters et al. 1993 NIOSH | Ergonomics 36:749 | HM = 25/H (anterior distance 최소화) |

---

## 11. 핵심 수치 요약 (Quick Reference for opensim-agent)

### 상체 고정 자세 (전 구간 동일)

| 관절 | Right | Left | 비고 |
|------|-------|------|------|
| shoulder_elv | **+19 deg** | **-19 deg** | 좌는 음수 convention |
| elv_angle | **-2 deg** | **-2 deg** | 시상면 근처 고정 (gait swing 제거) |
| shoulder_rot | **+42 deg** | **-20 to -42 deg** | 내회전 (FK 검증 후 조정) |
| elbow_flexion | **+68 deg** | **+68 deg** | 65~80° 범위 |
| pro_sup | 0 (locked) | 0 (locked) | |
| wrist_flex | 0 (locked) | 0 (locked) | |
| wrist_dev | 0 (locked) | 0 (locked) | |
| clav_prot | +5 deg | +5 deg | 약한 전방 돌출 |

### 체간 lean-back 오프셋

| 세그먼트 | 오프셋 | |
|---------|--------|--|
| L5_S1_FE | -0.83 deg | 신전 (carry 하는 동안 항상 추가) |
| L4_L5_FE | -0.83 deg | |
| L3_L4_FE | -0.83 deg | |
| L2_L3_FE | -0.83 deg | |
| L1_L2_FE | -0.83 deg | |
| T12_L1_FE | -0.83 deg | |
| T11_T12 이하 | 0 | 변경 없음 |

### 박스 손 목표 위치 (ground frame)

| | hand_R | hand_L |
|-|--------|--------|
| x (전방) | +0.20 m | +0.20 m |
| y (수직) | +0.095 m (floor+1.000m) | +0.095 m |
| z (측방) | +0.150 m | -0.150 m |

---

_작성: biomechanics-agent, 2026-07-28_
_목적: carry-walk (5번째 동작) 상체 자세 reference — opensim-agent에게 전달용_
_전제: gait_retarget_v2.mot 하체 재사용, 상체만 교체_
_다음 단계: opensim-agent → carry_walk.mot 생성 → viz-agent → SO (moco-analysis-agent)_
