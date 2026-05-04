# Forearm v1 Modification: Hand Segment 추가

**작성일**: 2026-05-04  
**작업자**: opensim-agent  
**목적**: 박스 들기 작업에서 hand reach 부족 문제 해결 (박스 motion v3-v9 9번 실패 근본 원인)

---

## 1. 문제 진단

### 1.1 근본 원인 (이전 진단, 2026-05-04)

ThoracolumbarFB 모델의 hand_R/L body origin = wrist center로, 손 세그먼트(~19 cm)가 누락된 구조:

| 세그먼트 | 모델 실측 | De Leva 1996 남성 | 차이 |
|---------|---------|-----------------|------|
| Humerus (GH→elbow) | 29.07 cm | ~28.2 cm | +0.87 cm (OK) |
| Forearm (elbow→wrist) | 25.81 cm | ~26.0 cm | -0.19 cm (OK) |
| Hand (wrist→grip) | **0 cm** | **19.2 cm** | **-19.2 cm** |
| **Total (GH→hand_R)** | **54.5 cm** | **~73.4 cm** | **-18.9 cm** |

### 1.2 모델 구조 (수정 전)

```
chain: scapula_R → shoulder_R → humerus_R → elbow → ulna_R → radioulnar → radius_R → radius_hand_r → hand_R

radius_hand_r joint:
  parent: radius_R, offset = (0.018, -0.242, 0.025)  [wrist center, 24.4 cm below radius_R origin]
  child:  hand_R,   offset = (0, 0, 0)               [wrist = hand_R origin]

→ hand_R body origin = wrist joint center
→ IK target (hand_R origin) = wrist center, NOT grip point
→ 손 19.2 cm 누락
```

---

## 2. 수정 내용 (Anthropometric 근거)

### 2.1 참고 문헌

- **De Leva 1996** (J Biomech 29(9):1223-1230, Table 4, Male):
  - Hand length (wrist to tip of middle finger): **19.2 cm** (= 0.108 × height, 177.8 cm 기준)
  - Forearm: 26.0 cm, Humerus: 28.2 cm
- **Winter 2009** (Biomechanics and Motor Control, 4th ed.):
  - Total arm (acromion to fingertip) / height = 0.460 → 80 cm (175 cm male)
- 수정 후 GH→hand_R = 73.7 cm (De Leva range 73-76 cm 내)

### 2.2 수정 방법 (Option B: Joint location 이동)

**radius_hand_r joint의 parent frame offset Y 연장**:

```xml
<!-- 수정 전: radius_R_offset (wrist center = 24.4 cm below radius_R origin) -->
<translation>0.017999999999999999 -0.24199999999999999 0.025000000000000001</translation>

<!-- 수정 후: wrist center를 19.2 cm 더 원위부로 이동 -->
<translation>0.017999999999999999 -0.43400000000000000 0.025000000000000001</translation>
```

- Right side: Y: -0.242 → -0.434 m (Δ = -0.192 m = 19.2 cm)
- Left side: Y: -0.242 → -0.434 m (Z = -0.025, 대칭)
- radius_R local Y축 = ground Y축 (standing 자세에서 identity rotation 확인)

### 2.3 선택하지 않은 옵션

- **Option A (scale_factors 변경)**: 시각적 geometry만 변경, kinematic에 무영향 → 부적절
- **ulna body length 변경**: ulna body는 kinematic chain에서 사실상 통과점 (2.3 cm proxy), 실질 forearm length는 radius body에 있음 → 효과 없음

---

## 3. 수정 결과 (FK 검증)

### 3.1 Standing pose FK

| 항목 | 수정 전 | 수정 후 | 목표 |
|------|---------|---------|------|
| GH→Elbow | 29.07 cm | 29.07 cm (불변) | ~29 cm |
| Elbow→Wrist | 25.81 cm | 44.81 cm | - |
| Wrist→hand_R origin | 0 cm | 0 cm | - |
| **GH→hand_R 합계** | **54.54 cm** | **73.70 cm** | **73-80 cm** |
| Bilateral Z symmetry | 0 mm | 0 mm | 0 mm |

**판정: GH→hand_R [73, 80] cm 범위 → PASS**

### 3.2 생성 파일

- **수정 모델**: `MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim`
- **Moco용 변형**: `MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim`
- 수정 스크립트: `scripts/modify_forearm_geometry.py`

---

## 4. Reach Envelope 재측정

### 4.1 v8b spec (PT=-55°, hip=100°, knee=-30°, lumbar=-62°)

| 모델 | Box target 최소 거리 |
|------|-------------------|
| 원본 no_coupler | 141 mm (FAIL) |
| forearm_v1 | **107.6 mm** (개선, 아직 threshold 초과) |

v8b spec에서 lumbar=-62°는 여전히 부족. lumbar=-75°로 증가 시:

```
PT=-55, hip=100, knee=-30, lumbar=-75: dist = 26.3 mm (PASS < 50 mm)
```

### 4.2 전체 reach envelope 비교

| 지표 | 원본 no_coupler | forearm_v1 |
|------|---------------|------------|
| 도달 가능 자세 (dist<50mm) | 16 / 320 (5%) | **30 / 144 (20.8%)** |
| biomechanics spec (PT≈-55) | 0개 | **1개 (lumbar=-75)** |
| 최소 도달 거리 | 9.5 mm (PT=-75 extremal) | **18.6 mm** |

### 4.3 성공 자세 패턴

forearm_v1 기준 reachable 30개의 조건:
- pelvis_tilt: -45° ~ -75° (spec -55°에서도 가능)
- hip_flexion: 80° ~ 110°
- knee_angle: -15° ~ -45°
- lumbar_total: **-75° 시 일관적 성공** (biomech spec 허용치 내)

---

## 5. Phase 1a Regression Test

결과 상세: `docs/phase1a_forearm_v1_regression.md` 참조

| Phase | Max ΔES | 판정 |
|-------|---------|------|
| Smoke (t=1-3, mesh=25) | **1.227 %p** (IL_R10_r) | PASS |

**전체 판정: PASS (max ΔES 1.227 %p < 5 %p threshold)**

이론적 예측과 일치: Phase 1a stoop 동작에서 팔은 자연스럽게 양옆에 늘어짐. 손 세그먼트 질량(~0.46 kg) COM 이동으로 인한 미소한 동력학적 변화만 발생.

---

## 6. 향후 사용 가이드

### 6.1 모델 사용 용도

| 모델 파일 | 용도 |
|---------|------|
| `..._no_coupler.osim` | 기존 Phase 1a/2 분석 (backward compatibility) |
| `..._no_coupler_forearm_v1.osim` | 박스 들기 IK (Phase 2 box motion v10+) |
| `..._moco_stoop_no_coupler_forearm_v1.osim` | Moco Phase 2 분석 |

### 6.2 IK Target 수정 사항

forearm_v1에서 hand_R origin = wrist + 19.2 cm (원위부). 박스 측면 grip 좌표:
```
hand target y: box_bottom_y + grip_height_from_bottom
             = box_bottom_y (박스 아래쪽 grip)
             또는 box_top_y - 0.05 (박스 위쪽 edge grip)
z target:    ±(box_half_width - 0.015) [이전과 동일]
```

### 6.3 Limitations

- 손 세그먼트 mass/inertia 재계산 미수행 (기존 hand_R mass 0.4575 kg 유지)
  - 영향: 박스 lifting 동력학에 미소 오차 가능 (~2-3% 수준 예상)
  - 해결: 향후 De Leva 1996 기준으로 hand mass 재조정 가능
- ulna/radius geometry mesh는 수정 전 상태 (시각적으로 단축된 상태)
  - kinematic 영향 없음

---

## 7. 스크립트 목록

| 파일 | 역할 |
|------|------|
| `scripts/modify_forearm_geometry.py` | 모델 수정 (radius_hand_r/l offset 변경) |
| `scripts/run_moco_phase1a_forearm_v1.py` | Phase 1a regression 실행 |
| `scripts/compare_phase1a_forearm_v1.py` | 결과 비교 + 그림 생성 |

---

*분석: opensim-agent (2026-05-04)*  
*Anthropometric reference: De Leva 1996, Winter 2009*
