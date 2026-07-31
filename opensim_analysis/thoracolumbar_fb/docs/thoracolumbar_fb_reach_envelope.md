# ThoracolumbarFB Reach Envelope 진단 (2026-05-04)

**목적**: 박스 motion v3-v7 + v8/v8b/v8c 9번 연속 실패 근본 진단  
**모델**: MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim  
**박스 목표 좌표**: hand_R = (+0.256, -0.755, +0.150) [ground frame]

---

## 1. Arm Architecture (실측)

### 1.1 모델 관절 중심 위치 (직립 자세, ground frame)

| 부위 | x (m) | y (m) | z (m) |
|------|-------|-------|-------|
| GH joint center (shoulder_R parent) | +0.0003 | +0.5015 | +0.1706 |
| Elbow joint center (humerus_R in elbow context) | +0.0064 | +0.2111 | +0.1583 |
| Distal ulna (radioulnar parent) | +0.0068 | +0.1996 | +0.1783 |
| hand_R body origin | +0.0248 | -0.0424 | +0.2033 |
| calcn_r | -0.0442 | -0.9046 | +0.0914 |
| GH height above ground | - | 1.407 m | - |

### 1.2 세그먼트 길이 비교

| 세그먼트 | 모델 실측 | 인체측정 기준 (성인 남성) | 차이 |
|---------|---------|----------------------|------|
| Upper arm (GH→elbow) | **29.1 cm** | ~33 cm | **-3.9 cm (-11.8%)** |
| Forearm + proximal hand | 2.3 cm + 24.4 cm | ~28 cm forearm + ~7 cm | 구조 이상 |
| hand_R body (ulna→hand_R) | 24.4 cm | ~19 cm | +5.4 cm |
| Total (GH→hand_R) | **54.5 cm** | ~80 cm | **-25.5 cm (-31.9%)** |

### 1.3 핵심 발견: 모델 상완 구조 이상

```
실측:
  GH center:    (0.0003, 0.5015, 0.1706)
  Elbow center: (0.0064, 0.2111, 0.1583)  → 거리 = 29.1 cm (정상)
  Distal ulna:  (0.0068, 0.1996, 0.1783)  → elbow→ulna = 2.3 cm (이상!)
  hand_R:       (0.0248, -0.0424, 0.2033) → ulna→hand_R = 24.4 cm (이상!)

문제: "forearm" 세그먼트가 사실상 2.3 cm 뿐
     실제 전완 길이(28 cm)가 hand_R body에 포함된 구조
     → hand_R body = 전완 하부 + 손 복합체

결론: 전체 팔 reach = GH→hand_R = 54.5 cm
     인체측정 기준 80 cm 대비 25.5 cm (31.9%) 부족
```

---

## 2. Standing Reach Envelope (직립 자세)

### 2.1 전체 도달 범위

모든 arm joint 조합 (7,865 combinations) 스윕 결과:

```
shoulder_elv ∈ [0°, 155°], step 15°
elv_angle    ∈ [-90°, 155°], step 20°
shoulder_rot ∈ [-90°, 45°], step 30°
elbow_flex   ∈ [0°, 155°], step 15°

hand_R x range: [-0.544, +0.545] m
hand_R y range: [-0.044, +1.047] m
hand_R z range: [-0.375, +0.716] m
```

### 2.2 박스 목표 도달 가능성 (직립)

| 목표 좌표 | 가능 여부 | 비고 |
|---------|---------|------|
| x = +0.256 | YES (x 범위 내) | 전방 도달 가능 |
| y = -0.755 | **NO** | 직립에서 y min = -0.044 m |
| z = +0.150 | YES (z 범위 내) | 측면 도달 가능 |

**결론: 직립에서는 박스 목표 도달 불가 (y 방향 -711 mm 부족)**

### 2.3 z = 0.15 평면에서의 가장 가까운 도달점

```
Closest config: shoulder_elv=0, elv_angle=10, shoulder_rot=30, elbow_flex=0
Best hand_R: (+0.130, -0.027, +0.134)
Distance to target: 739 mm
→ 직립 상태에서 박스까지 739 mm 부족 (stoop 필수)
```

---

## 3. Stoop Reach Envelope (발 고정 조건)

### 3.1 자세 격자 320개 조합 스윕 결과

```
pelvis_tilt ∈ [-30°, -45°, -55°, -65°, -75°]
hip_flexion ∈ [60°, 80°, 100°, 110°]
knee_angle  ∈ [0°, -15°, -30°, -45°]
lumbar_FE   ∈ [-30°, -50°, -60°, -75°] (각 세그먼트 균등 분배)
발 anchor: calcn_r x = -0.0442 (모든 frame 고정)
```

**Reachable (dist < 50 mm): 16개 / 320개 (5%)**

### 3.2 상위 결과 (distance to target 기준)

| pelvis_tilt | hip | knee | lumbar_total | pelvis_tx | pelvis_x | shoulder_y | box_dist | min_mm | 가능? |
|-------------|-----|------|-------------|---------|---------|----------|--------|--------|------|
| **-75** | **110** | **-45** | **-60** | -0.169 | -0.072 | -0.270 | 0.328 | **9.5** | **YES** |
| -65 | 100 | -45 | -75 | -0.170 | -0.065 | -0.260 | 0.321 | 22.4 | YES |
| -65 | 110 | -45 | -75 | -0.311 | -0.205 | -0.291 | 0.461 | 27.7 | YES |
| -75 | 110 | -30 | -60 | -0.292 | -0.195 | -0.251 | 0.451 | 28.6 | YES |
| -75 | 100 | -30 | -75 | -0.143 | -0.046 | -0.281 | 0.302 | 30.3 | YES |
| -75 | 80  | -30 | -75 | +0.158 | +0.256 | -0.304 | 0.000 | 35.8 | YES |

**Best reachable posture: pelvis_tilt=-75°, hip=110°, knee=-45°, lumbar=-60°**

### 3.3 v8 시리즈 스펙 (-55°/-45° 범위)과의 비교

v8 시리즈 설계 조건 (pelvis_tilt=-55°, hip=100°, knee=-30°, lumbar=-60°):

```
pelvis_tx: -0.435 m
pelvis_x:  -0.324 m (pelvis가 박스보다 0.580 m 후방)
shoulder_y: -0.147 m (어깨가 ground 아래!)
min_dist to target: 141.4 mm
→ 141 mm 부족 → 박스 도달 불가
```

이것이 v8/v8b/v8c 실패의 직접적 원인.

### 3.4 성공 자세의 특성

성공한 16개 중 공통 패턴:
- pelvis_tilt 반드시 -65° 이상 (대부분 **-75°**)
- hip_flexion 100° 이상
- knee_angle -30° ~ -45°
- lumbar_total -60° ~ -75°

**이 자세는 biomechanics-agent 스펙 (pelvis_tilt max -60°, knee max -40°)을 벗어남**

---

## 4. Foot Anchor 변경 효과

```
기준 자세: pelvis_tilt=-55°, hip=100°, knee=-30°, lumbar=-60°
```

| target_calcn_x | pelvis_tx | pelvis_x | shoulder_y | pelvis→box | min_mm | 가능? |
|---------------|---------|---------|----------|---------|--------|------|
| -0.0442 (default) | -0.435 | -0.324 | -0.147 | 0.580 | 141.4 | NO |
| +0.0058 (+5cm) | -0.385 | -0.274 | -0.147 | 0.530 | 136.1 | NO |
| +0.1058 (+15cm) | -0.285 | -0.174 | -0.147 | 0.430 | 104.5 | NO |

**결론: 발을 앞으로 15 cm 이동해도 여전히 104 mm 부족**  
발 위치 변경으로는 해결 불가.

---

## 5. Pelvis Backward Shift 메커니즘

### 5.1 각 관절의 pelvis 후방 이동 기여도

```
기준: calcn_r x = -0.0442 고정, pelvis→박스(+0.256) 거리

pelvis_tilt only (-55°, rest=0°):   pelvis_tx=+0.500  pelvis→box = 0.355 m
+ hip=100°:                          pelvis_tx=-0.671  pelvis→box = 0.816 m  (+0.461 m 악화!)
+ knee=-30°:                         pelvis_tx=-0.444  pelvis→box = 0.589 m  (-0.227 m 개선)
+ lumbar=-10° each:                  pelvis_tx=-0.444  pelvis→box = 0.589 m  (영향 없음)
+ ankle=-9°:                         pelvis_tx=-0.435  pelvis→box = 0.580 m  (미미)
```

### 5.2 v8 반직관 거동 진짜 원인

**"pelvis_tilt -55°보다 -45°일 때 pelvis가 더 뒤로 이동"의 원인:**

```
PT=-45, hip=100, kn=-30, L=-10:  pelvis_x = -0.453  pelvis→box = 0.709 m
PT=-55, hip=100, kn=-30, L=-10:  pelvis_x = -0.324  pelvis→box = 0.580 m
PT=-65, hip=100, kn=-30, L=-10:  pelvis_x = -0.187  pelvis→box = 0.443 m
```

**pelvis_tilt 덜 기울수록 hip이 더 뒤로 당김** — hip_flexion 100°가 고정된 상태에서  
pelvis가 덜 기우면 hip이 상체를 더 뒤로 당기는 구조  
→ 반직관적이지만 운동학적으로 정확한 결과

### 5.3 최대 기여 관절: Hip Flexion

```
hip=100° 추가 시:  pelvis→box 0.355 → 0.816 m (+0.461 m 급증)
knee=-30° 추가 시: pelvis→box 0.816 → 0.589 m (-0.227 m 개선)
lumbar 기여:        거의 없음 (±0.000 m)
```

**Hip flexion이 pelvis 후방 이동의 주범.**  
하지만 hip flexion 없이는 박스까지 torso가 내려갈 수 없음 → 딜레마.

---

## 6. 결론

### 6.1 ThoracolumbarFB 박스 lifting 부적합 정량 근거

| 항목 | 측정값 | 기준/필요값 | 부족량 |
|------|-------|-----------|-------|
| Total arm reach (GH→hand_R) | **54.5 cm** | ~80 cm (anthropometric) | **-25.5 cm** |
| v8 스펙 자세에서 박스까지 최소 거리 | **141 mm** | < 50 mm | **91 mm 초과** |
| 성공 가능 자세 | pelvis_tilt ≥ -65° | biomech spec: -55° ~ -60° | **스펙 위반** |
| 성공 자세 knee_angle | -45° | biomech spec: -25° ~ -40° | **squat 과도** |

### 6.2 모델의 근본 구조 문제

```
shoulder_elv_r 범위: [0°, 154.7°]
  → 팔을 아래쪽(downward-forward)으로 내리는 데 제약
  → elv_angle_r [-90°, 155°]로 보상하지만 총 reach = 54.5 cm
  → 인체 기준 80 cm 대비 31.9% 부족

ThoracolumbarFB는 척추(erector spinae) 분석 전문 모델:
  → 22개 척추 분절 (T1~S1), 620 muscles
  → 어깨/팔 architecture는 단순화됨
  → 박스 들기처럼 팔 reach가 핵심인 작업에 부적합
```

### 6.3 박스 lifting 적합/부적합 판정

| 작업 | ThoracolumbarFB 적합성 |
|------|----------------------|
| 제자리 stoop lift (v5, Phase 1a) | **적합** — 팔 reach 불필요, ES 분석이 목적 |
| 박스 들기 (v3-v8c, 지면 박스) | **부적합** — arm reach 31.9% 부족, 극단적 자세로만 가능 |
| Phase 2 박스 분석 목적 | biomechanics-agent 스펙 내 자세 불가능 |

---

_분석: opensim-agent (2026-05-04)_  
_스크립트: /data/wearable-assist/scripts/reach_envelope_analysis.py_
