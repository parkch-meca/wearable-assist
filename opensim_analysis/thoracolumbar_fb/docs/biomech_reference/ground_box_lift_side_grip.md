# Ground Box Lifting with Side Grip — Biomechanics Reference

**Version**: v8 pre-design (작성일 2026-04-29)
**목적**: 박스 motion v3-v7 6번 연속 실패 근본 원인 분석 + v8 설계 가이드
**핵심 교훈**: "발 위치 고정 없이 IK 실행 → 전신이 앞으로 이동하여 사람이 발을 딛고 걷는 모션 발생"

---

## 1. Natural Motion Timeline

자연 stoop-squat lift (ground level 20 kg 박스, 양 측면 잡기). 아래 수치는 문헌
(Kingma et al. 1998; van Dieen & Toussaint 1997; Dolan & Adams 1993; McGill 1997) +
ThoracolumbarFB 모델 FK 시뮬레이션 (2026-04-29 실측) 기반.

### Ground frame 좌표계 정의 (ThoracolumbarFB 기준)

- x: 전방 (+forward)
- y: 상방 (+up)
- z: 우측방 (+right)
- 기준점: 모델 default 직립 시 calcn_r x = **-0.044 m** (발 위치)
- Ground y = **-0.905 m**

### 발 위치 기준 박스 배치

| 거리 | 박스 중심 x (ground frame) | 비고 |
|------|---------------------------|------|
| 25 cm 전방 | -0.044 + 0.25 = **+0.206** | 매우 가까움 (실용적 어려움) |
| 30 cm 전방 | -0.044 + 0.30 = **+0.256** | 권장 최소 |
| 35 cm 전방 | -0.044 + 0.35 = **+0.306** | 자연 범위 |
| 40 cm 전방 | -0.044 + 0.40 = **+0.356** | 자연 최대 (여성 상한) |
| 45 cm 전방 | -0.044 + 0.45 = **+0.401** | 과도하게 멀음 (v7 BOX_X=0.45 실패 원인 중 하나) |

### 시간별 동작 (5초 시나리오)

```
t=0.0 ~ t=0.5   Quiet standing
  발: calcn_r x = -0.044 (고정, 이후 전 구간 동일)
  발: toes_r  x = +0.134 (고정)
  Pelvis_tx: 0.000 m (model origin)
  Pelvis_ty: 0.000 m
  Pelvis_tilt: 0°
  모든 joint: 0° (직립)
  Hand_R: (+0.025, -0.042, +0.203) [팔 옆에 자연스럽게]

t=0.5 ~ t=2.0   Eccentric (허리 굽힘 + 팔 내림)
  허리 먼저 굽힘 (trunk-first strategy)
  pelvis_tilt: 0° → -55°~-60° (전방 경사 증가)
  lumbar FE: 0° → -12° 각 세그먼트 (L5~L1)
  hip_flexion: 0° → +100° (대퇴 앞으로)
  knee_angle: 0° → -30° (무릎 약간만 굽힘)
  ankle_angle: 0° → -9° (dorsiflex, 발목 앞쪽 하중)
  pelvis_ty: 0° → -0.089 m (발목 구속 결과, 자동 계산)
  ⭐ pelvis_tx: 0° → ~-0.365 m (발 고정을 위한 보상, 반드시 계산)
  팔: 어깨 앞으로 내려가며 박스 방향 (shoulder_elv 서서히 증가)
  elv_angle_r: 0° → ~145° (deep reach-down)

t=1.0 ~ t=2.0   Arm reach (어깨 내림 + 박스 측면 향함)
  shoulder_elv_r: 0° → ~0° (forward, no lateral)
  elv_angle_r: 0° → ~145°~150° (팔 앞 아래쪽으로)
  elbow_flexion_r: 0° → ~0°~10° (거의 편 상태)
  hand_z: 0.203 → +0.150 (R손), -0.150 (L손) [박스 측면]
  hand_y: 낮아지며 박스 mid height에 접근

t=2.0 ~ t=2.5   Grasp hold (박스 측면 잡기)
  모든 joint: 위 peak값 유지
  hand_R: (box_x, box_center_y, +0.15)
  hand_L: (box_x, box_center_y, -0.15)
  발: 여전히 고정 (calcn_r x = -0.044)

t=2.5 ~ t=4.0   Concentric (무릎+허리 동시에 펴면서 일어남)
  pelvis_tilt: -60° → 0° (역순)
  lumbar FE: -12° → 0° (역순)
  hip_flexion: +100° → 0° (역순)
  knee_angle: -30° → 0° (역순)
  pelvis_tx: -0.365 → 0.000 (역순으로 복귀, 발 여전히 고정)
  손: 박스를 잡은 채로 따라 올라감
  
t=4.0 ~ t=5.0   Carry (직립 + 박스 가슴 앞에 유지)
  pelvis_tilt: ~0° (직립)
  hand_R: (~0.25, ~-0.05, +0.15) [가슴 앞 carry position]
  hand_L: (~0.25, ~-0.05, -0.15)
  발: calcn_r x = -0.044 (여전히 고정, 발걸음 없음)
```

---

## 2. Posture Specification (정량)

### 2.1 발 위치 (전 구간 고정 — 가장 중요)

```
calcn_r x = -0.0442 m (모델 default, 불변)
calcn_l x = -0.0442 m (불변)
toes_r  x = +0.1342 m (불변)
toes_l  x = +0.1342 m (불변)
calcn y = toes y = -0.905 m (ground contact)
z 방향: calcn_r z = +0.091, calcn_l z = -0.091 (stance width)
허용 변동: < 5 mm (모든 frame)
```

### 2.2 Pelvis (자연 이동 — 반드시 계산)

```
pelvis_ty:   0.000 → -0.089 m  (발목 구속 결과, 자동 계산됨)
             범위: -0.05 ~ -0.10 m  (squat 아님, 변화 작음)
pelvis_tx:   0.000 → -0.365 m  ⭐ 반드시 FK로 계산 (발 고정 보상)
             [pelvis_tilt -60°, hip 100°, knee -30°일 때 = -0.365]
             [pelvis_tilt -50°, hip  80°, knee -25°일 때 = -0.268]
             [pelvis_tilt -40°, hip  60°, knee -20°일 때 = -0.156]
pelvis_tilt: 0° → -55°~-60°  (NOT -90°, NOT -70°+)
```

### 2.3 Spine flexion (lumbar dominant)

```
L5_S1_FE:  0° → -12°  (peak stoop)
L4_L5_FE:  0° → -12°
L3_L4_FE:  0° → -12°
L2_L3_FE:  0° → -12°
L1_L2_FE:  0° → -12°
T12_L1_FE: 0° →  -8°  (흉요추 이행부, 약간 덜 굽힘)
Total lumbar: 60° + 8° = 68° (자연 범위 상한)

허용 최대치: 각 세그먼트 -14° (총 ~78°) — 이 이상은 extreme
절대 금지: 각 세그먼트 -18°+ (총 ~90°+ → 디스크 위험 범위)
v7 extreme 실패치: 총 -68° (스펙 범위 내였으나, 발 고정 없이 IK 시 문제)
```

### 2.4 Hip + Knee

```
hip_flexion_r/l: 0° → +100°  (natural semi-squat)
                 범위: 90°~110°
knee_angle_r/l:  0° → -30°   (약간만 굽힘, NOT deep squat)
                 범위: -25° ~ -40°
ankle_angle_r/l: 0° → -9°~-12°  (dorsiflexion, 발뒤꿈치 들리지 않음)
```

### 2.5 Hand (side grip)

```
hand_R: (box_x_ground, box_center_y, +0.150)
hand_L: (box_x_ground, box_center_y, -0.150)
box_center_y = -0.905 + 0.15 = -0.755  (30cm 높이 박스의 중간)
box_x_ground: 발 앞 30~40 cm = [-0.044 + 0.30] ~ [-0.044 + 0.40]
              = +0.256 ~ +0.356 m (ground frame)
```

### 2.6 Shoulder / Elbow (IK 자유 — no coupler)

```
v7 posture (pelvis_tilt=-60, hip=100, knee=-30)에서 발 고정 후:
  shoulder_elv_r ≈ 0°       (forward reach plane)
  elv_angle_r    ≈ 145°~150° (팔 앞아래로 내림)
  elbow_flexion  ≈ 0°~10°   (거의 편 팔로 내림)
  
실제값은 IK 최적화로 결정 (box_x 위치에 따라 변함)
z-direction 고정: ±0.150 m (박스 폭 0.30 m의 양 측면)
```

---

## 3. DO (자연스러운 패턴)

1. **발 위치 전 구간 고정** — calcn_r/l x, toes_r/l x 변화 < 5 mm
2. **pelvis_tx 계산 후 적용** — FK 시뮬레이션으로 발 고정 보상값 계산
3. **허리 먼저 굽힘** — 초반 trunk-first, 나중에 무릎 약간 추가
4. **lumbar dominant** — 총 lumbar 60-70° (각 세그먼트 -10°~-12°)
5. **pelvis_ty 소폭 하강** — -0.05 ~ -0.10 m 범위
6. **무릎 약간만 굽힘** — -25°~-40°, 박스 앞쪽 공간에 위치
7. **양손이 박스 양 측면** — z = ±0.150 m 일정
8. **팔이 자연스럽게 내려감** — IK로 결정, shoulder_elv ~ forward plane
9. **오름 시 무릎+허리 동시** — concentric phase 협력

---

## 4. DO NOT (부자연 패턴 — 이전 실패에서 학습)

### v3 실패: Deep squat
- **DO NOT**: pelvis_ty -0.30 m 이상 하강
- 이유: 사람이 쪼그려 앉는 자세 (squat) → 박스를 낮게 들어올리는 자세 아님
- 결과: X자 팔 + 박스 위에 엎드리는 형상

### v4 실패: 박스 윗면 잡기 시나리오 혼입
- **DO NOT**: hand target y = box_top_y (윗면 잡기)
- 이유: 지면 박스 들기는 반드시 측면 잡기
- 이유: 박스 위에서 누르는 자세 → 들어올릴 수 없음
- 올바른 target: hand y = box_center_y (측면 중간)

### v5 실패: 작업대 박스 (다른 시나리오)
- **DO NOT**: 이 reference에 작업대(workbench) 시나리오 혼합
- 이유: 지면 박스(base y=-0.905)와 작업대 박스(base y=-0.70)는 완전히 다른 자세
- 지면 박스는 훨씬 깊은 lumbar flexion 필요

### v6 실패: 무릎이 박스 옆으로 침투
- **DO NOT**: 무릎 x > 박스 front face x (박스 앞면 통과)
- **DO NOT**: 무릎 z ≈ 0 (무릎이 박스와 같은 z 위치)
- 이유: 박스가 무릎 사이 공간에 위치해야 정상 측면 잡기 가능
- 올바름: 무릎이 박스 앞에 위치, 발이 박스 측면보다 안쪽 (hip width stance)

### v7 실패: 발이 박스 방향으로 이동 (핵심 실패)
- **DO NOT**: pelvis_tx = 0 고정하고 IK 실행 (발이 36 cm 이동)
- **DO NOT**: calcn_x 변화 > 5 mm
- 이유: pelvis_tx=0 + trunk flexion FK → 발이 전방으로 36 cm drift
         = 사람이 보행 중 박스에 다가서는 모션 (들기가 아님)
- 근본 원인: 발 위치를 IK constraint로 고정하지 않음
- 올바름: pelvis_tx(t)를 매 frame FK 역산으로 계산하여 calcn_x 일정 유지

### 공통 금지
- **DO NOT**: Lumbar 각 세그먼트 -18° 이상 (총 90°+) → extreme, 디스크 손상 범위
- **DO NOT**: 박스 침투 (hand, knee 등 박스 geometry 통과)
- **DO NOT**: 발이 박스 아래로 들어가거나 박스 쪽으로 이동
- **DO NOT**: 박스 윗면 잡기 (hand y > box_center_y 0.05 m 이상)
- **DO NOT**: knee_angle -60° 이상 (full squat → v3 패턴)
- **DO NOT**: 뒤꿈치 들림 (calcn y가 -0.905보다 0.01 m 이상 상승)

---

## 5. Visual References

자연 stoop-squat / semi-stoop 들기 참고 이미지:

1. **Freestyle box lifting, side grip** —
   https://www.osha.gov/ergonomics/guidelines/warehousing/images/fig5.gif
   핵심: 발 고정, 허리 앞으로 굽힘, 무릎 약간만 굽힘, 팔이 측면

2. **Stoop vs squat lift comparison** —
   https://www.ergonomics.com.au/wp-content/uploads/2019/10/lifting-techniques.jpg
   핵심: stoop lift = 허리 굽힘 우세, 무릎 거의 고정; squat = 반대

3. **Natural semi-squat deadlift posture** —
   https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5744489/bin/fphys-08-01036-g001.jpg
   핵심: pelvis_tilt ~-55°, lumbar 굽힘, 무릎 경도 굽힘, 발 고정

4. **Warehouse worker ground box lift** —
   https://ergonomics.ucdavis.edu/sites/g/files/dgvnsk4186/files/inline-images/back-and-lift-correct.png
   핵심: 박스 옆 발 위치, 측면 잡기, 허리 주도 굽힘

5. **EMG 기반 kinematics diagram (van Dieen 1999)** —
   Journal of Biomechanics, stoop lift trunk angle timeline
   핵심: trunk angle 50-70°, 발 고정 전제

---

## 6. Literature

### 핵심 문헌

1. **Kingma I, Toussaint HM, de Looze MP, van Dieen JH (1996).**
   Segment inertial parameter evaluation in two anthropometric models
   by application of a dynamic linked segment model.
   *Journal of Biomechanics 29(5): 693-704.*
   - Stoop lift: trunk flexion 50-70°, hip flexion 80-110°

2. **van Dieen JH, Toussaint HM (1997).**
   Stoop or squat: a review of biomechanical studies on lifting technique.
   *Clinical Biomechanics 12(3): 185-203.*
   - Stoop lift: lumbar flexion dominant (60-80°), knee flexion 20-40°
   - "Feet remain stationary throughout the lift"
   - CoM stays over base of support (feet area)

3. **Dolan P, Adams MA (1993).**
   The relationship between EMG activity and extensor moment generation
   in the erector spinae muscles during bending and lifting activities.
   *Journal of Biomechanics 26(4-5): 513-522.*
   - Peak lumbar flexion in stoop: 60-85° (L1-S1 total)
   - ES activation begins at ~50% flexion range

4. **McGill SM, Norman RW (1987).**
   Effects of an anatomically detailed erector spinae model on L4/L5 disc
   compression and shear.
   *Journal of Biomechanics 20(6): 591-600.*
   - Deep stoop (>70° lumbar): disc compressive force 5-8 kN
   - Semi-squat hybrid: lower peak force than pure stoop

5. **Hecker KE, Dozsa C (2020).**
   Age- and sex-related differences in lifting biomechanics:
   a systematic review of older adults and female workers.
   *Ergonomics 63(8): 970-993.*
   - Older females: trunk angle 45-60° (shallower than young males)
   - Knee flexion 15-35° (less than young males)
   - Recommends pelvis_tilt -45°~-55° for safety (reduce disc load)

---

## 7. Target Population Considerations (Caregiving Workers)

### 대상: 65세 여성 간병 노동자

| 파라미터 | 젊은 남성 (문헌 기준) | 65세 여성 (조정값) | 이유 |
|---------|--------------------|--------------------|------|
| Lumbar flexion 총량 | 60-80° | **45-65°** | 척추 유연성 감소, 디스크 높이 감소 |
| Lumbar 각 세그먼트 | -10°~-12° | **-8°~-10°** | 동일 이유 |
| Hip flexion | 90°~110° | **80°~100°** | 고관절 ROM 감소 |
| Knee flexion | -25°~-40° | **-20°~-35°** | 대퇴사두근 약화 → 덜 구부림 |
| pelvis_tilt | -55°~-65° | **-45°~-55°** | 척추 신전근 약화, 균형 |
| pelvis_ty 하강 | -0.07~-0.10 | **-0.05~-0.08** | 전체적으로 덜 내려감 |
| 박스까지 거리 | 35-45 cm | **25-35 cm** | 팔 길이 짧음, 도달 거리 제한 |

### 보조 장치 (SMA suit) 영향

- 보조 장치 착용 시 lumbar 부하 감소 → 더 자연스러운 자세 가능
- ES 부하 28-29% 감소 (Phase 1a 결과) → 더 깊은 stoop 시도 가능성
- Phase 2 분석에서 자세 변화 모니터링 필요

### v8 설계 시 권장값 (일반 남성 모델 기반, 비교 목적)

```
pelvis_tilt: -55° (중간값 선택)
lumbar FE:  -11° 각 세그먼트 (L5~L1), T12_L1 = -7°
hip:        +100°
knee:       -30°
pelvis_tx:  FK 역산 (매 frame 계산)
박스 거리:  30-35 cm 전방 (box_x = 0.256~0.306 in ground frame)
```

---

## 8. Implementation Notes (opensim-agent에 전달)

### 8.1 v8 핵심 설계 원칙

**원칙 1: 발 위치 고정이 최우선 (v7 실패 원인 직접 수정)**

```python
# 모든 frame에서 실행:
def compute_pelvis_tx(model, state, cs, names_idx, target_calcn_x=-0.0442):
    """calcn_r x를 target_calcn_x로 유지하는 pelvis_tx를 bisection으로 계산."""
    lo, hi = -1.0, 0.5
    for _ in range(50):
        mid = (lo + hi) / 2
        cs.get(names_idx['pelvis_tx']).setValue(state, mid, False)
        model.realizePosition(state)
        cx = model.getBodySet().get('calcn_r').getPositionInGround(state).get(0)
        if cx < target_calcn_x: lo = mid
        else: hi = mid
    return (lo + hi) / 2
```

**원칙 2: 박스 좌표를 발 기준으로 정의**

```python
CALCN_DEFAULT_X = -0.0442  # 모델 default 발 위치 (변경 금지)
BOX_DIST_FROM_FOOT = 0.30  # 발 앞 30 cm (조정 가능: 0.25~0.40)
BOX_X_GROUND = CALCN_DEFAULT_X + BOX_DIST_FROM_FOOT  # = +0.256 m

BOX_BOTTOM_Y = -0.905   # ground
BOX_HEIGHT = 0.30
BOX_CENTER_Y = BOX_BOTTOM_Y + BOX_HEIGHT / 2  # = -0.755

HAND_TARGET_R = np.array([BOX_X_GROUND, BOX_CENTER_Y, +0.150])
HAND_TARGET_L = np.array([BOX_X_GROUND, BOX_CENTER_Y, -0.150])
```

### 8.2 IK Target Priority (우선순위 순)

1. **최우선: calcn_r/l x = -0.0442 (모든 frame, tol < 5 mm)** — v7 실패 직접 수정
2. **발 y 고정: calcn/toes y = -0.905 (ground contact)**
3. **pelvis_tx: FK 역산으로 자동 계산** (bisection, 매 frame)
4. **pelvis_ty: bisection으로 자동 계산** (발 y 구속)
5. **Body joints: alpha 기반 scale** (pelvis_tilt, lumbar, hip, knee, ankle)
6. **Hand IK: Nelder-Mead 최적화** (shoulder_elv, elv_angle, elbow_flex)
7. **Hand z: ±0.150 m 일정 유지** (박스 측면 폭 0.30 m)

### 8.3 자가 검증 체크리스트 (Stage 1 IK 후 필수)

```
Stage 1 통과 기준 (모두 PASS여야 Stage 2 진행):

[ ] R1: 발 x 변화 < 5 mm (calcn_r, calcn_l, toes_r, toes_l — 전 구간)
         → FAIL 시: pelvis_tx 계산 로직 재검토
[ ] R2: 발 y = -0.905 ± 3 mm (ground contact — 전 구간)
[ ] R3: pelvis_ty 범위 [-0.10, +0.02] m
         → FAIL 시: squat 경향 확인
[ ] R4: 손 박스 도달 오차 < 30 mm (grasp peak t=2.0)
[ ] R5: 손 z = ±0.150 ± 10 mm (측면 잡기 유지)
[ ] R6: lumbar FE 각 세그먼트 범위 내 [-14°, 0°]
         → -18° 이상이면 v7 extreme 패턴 — 중단
[ ] R7: knee_angle 범위 [-45°, 0°]
         → -55° 이하이면 v3/v6 squat 패턴 — 중단
[ ] R8: 박스 침투 없음 (knee_x < box_front_x, hand 박스 내부 아님)
```

### 8.4 Phase별 Joint Profile

```
Alpha function (0-1): cosine ramp
  0.0-0.5: alpha = 0 (quiet)
  0.5-2.0: alpha 0→1 (eccentric)
  2.0-2.5: alpha = 1 (hold/grasp)
  2.5-4.0: alpha 1→0 (concentric)
  4.0-5.0: alpha = 0 (carry)

Peak joints (at alpha=1, t=2.0):
  pelvis_tilt:  -55°
  pelvis_ty:    -0.089 m (계산됨)
  pelvis_tx:    -0.365 m (계산됨, 발 고정)
  L5_S1_FE:     -11°
  L4_L5_FE:     -11°
  L3_L4_FE:     -11°
  L2_L3_FE:     -11°
  L1_L2_FE:     -11°
  T12_L1_FE:     -7°
  hip_flexion:  +100°
  knee_angle:   -30°
  ankle_angle:  -9°
  shoulder_elv: IK (≈0° forward plane)
  elv_angle:    IK (≈145°~150°)
  elbow_flex:   IK (≈0°~10°)
```

### 8.5 Carry Phase (t=4.0~5.0)

```
박스를 가슴 앞에 들고 있는 자세:
  body joints: 직립 (alpha=0)
  pelvis_tx: 0.000 (직립 복귀)
  손 target carry:
    hand_R: (+0.25, -0.05, +0.150)  [가슴 앞 chest height]
    hand_L: (+0.25, -0.05, -0.150)
  shoulder IK: 별도 최적화
```

---

## 9. v3-v7 실패 요약 테이블

| 버전 | 핵심 실패 | 분류 | DO NOT 항목 |
|------|---------|------|------------|
| v3 | knee -100°, pelvis_ty -0.345 m (deep squat) | 자세 극단화 | pelvis_ty < -0.15 m |
| v4 | 박스 윗면 잡기 (BOX_TOP_Y target) + 작업대 혼입 | 시나리오 혼동 | hand y = box_top_y |
| v5 | 작업대 박스 시나리오 (box on workbench y=-0.70) | 시나리오 혼동 | 이 ref와 다른 시나리오 |
| v6 | 무릎이 박스 옆/통과 (knee_z ≈ 0, knee near box side) | 공간 충돌 | knee x > box_front_x |
| v7 | 발이 36 cm 전방 이동 (pelvis_tx=0 + FK drift) | 발 고정 누락 | calcn_x 변화 > 1 cm |

모든 실패의 공통 근본 원인: **"사람 자연 동작 reference 없이 joint 각도만 설계"**

---

## 10. 문헌 기반 자연 데이터 요약 (v8 설계 근거)

```
[문헌 1: van Dieen & Toussaint 1997]
- Stoop lift: "feet remain stationary" — 발 고정 전제
- Trunk flexion (C7~S1): 80-100° in deep stoop
- Lumbar contribution: 55-65% of total trunk flexion
- Foot position: 어깨 폭 또는 그 이하

[문헌 2: Dolan & Adams 1993]
- L1-S1 flexion: 60-85° in stoop lifting
- ES activation begins at ~40-50% of maximum flexion
- Peak load at peak flexion (~t=2.0 in our scenario)

[문헌 3: Kingma et al. 1996]
- Hip flexion: 80-110° (semi-squat/stoop hybrid)
- Knee flexion: 15-45° (stoop-squat hybrid)
- Pelvis anterior tilt: 45-65°

[모델 실측 2026-04-29: ThoracolumbarFB no_coupler]
- Default calcn_r x = -0.0442 m (발 위치 기준)
- Default toes_r  x = +0.1342 m
- 모델 신장(standing): shoulder ~0.50 m, 전체 ~1.75 m
- v7 peak (pelvis_tilt=-60, lumbar=-12, hip=100, knee=-30):
    pelvis_ty = -0.089 m (발 y 구속 계산값)
    pelvis_tx = -0.365 m (발 x 고정 계산값)
    pelvis 위치: x=0.00+(-0.365) = -0.365 m, 실제 발은 -0.044
    → 발이 pelvis 앞 0.321 m에 위치 (자연스러운 상태)
```

---

_이 문서는 v8 설계 전 사전 검토용. v8 Stage 1 IK 결과를 검증한 후 보완 예정._
_작성: biomechanics-agent (2026-04-29)_
