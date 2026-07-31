# Squat Lift Scenario Specification (Plan v2)

**작성일**: 2026-05-26
**작성**: literature-agent (Day 2 작업 2)
**근거**: `squat_lift_literature.md` 8 paper + ThoracolumbarFB v2.0 + 박스 v11 closure 교훈

---

## 1. 결정 요약 (Top-line)

| 항목 | 값 | 근거 |
|------|-----|------|
| 박스 weight | **15 kg** | P2 Hu 2026, P3 Hasenmaier 2026, P6 Park 2002 모두 채택; literature 최빈값 |
| 박스 위치 (지면/pallet) | **지면 (ground level)** | P2, P3 표준; pallet 시나리오는 Phase 2 후속 |
| 박스 horizontal (발 ↔ 박스 중심) | **35 cm** | 박스 v11 closure 자연 범위 (30–40 cm), `ground_box_lift_side_grip.md` ground frame 기준 +0.306 m |
| 박스 mid-height | **30 cm** (box height 30 cm) | 박스 v11 standardized |
| Foot stance | **양발 동시 (parallel, shoulder-width)** | P3, P6, P7 모두 symmetric; staggered는 Phase 3 |
| Lift duration | **4 s total** | descent 1.5 s + grasp 1.0 s + ascent 1.5 s |
| Squat type | **medium-deep squat (knee flex 110–130°)** | P3 135°, P5/P6 ROM 인용; deep squat lumbar relief 최대화 |

---

## 2. Phase 분할 (4 s scenario)

```
t = 0.0 ~ 0.5 s   Quiet standing
  발: parallel stance, shoulder-width
  pelvis_tilt: 0°
  hip_flexion: 0°
  knee_angle: 0°
  ankle_angle: 0°
  lumbar (sum L1–L5): 0°
  손: 자연스럽게 옆

t = 0.5 ~ 2.0 s   Descent (eccentric squat down)
  hip_flexion: 0° → 110° (P3 base + medium-deep)
  knee_angle: 0° → -110° ~ -125° (deep squat, P3 135° upper bound)
  ankle_angle: 0° → -20° (dorsiflex, P6 기준 20–25°)
  pelvis_tilt: 0° → -35° (forward pelvis rotation, ≪ stoop -60°)
  lumbar sum: 0° → -25° (5° per segment × 5 = 25°, lordosis→flexion 50% loss per P6)
  pelvis_tx: 0° → ~-0.10 m (knee forward 보상; 박스 v11 발 고정 protocol 유지)
  pelvis_ty: 0° → ~-0.30 m (squat 하강, hip+knee 동시 굽힘)
  팔: shoulder_elv 점진적 forward+downward, elbow 거의 편 상태

t = 2.0 ~ 3.0 s   Grasp (박스 양 측면 잡기)
  joint 모두 peak 유지
  hand_R: (box_x ≈ +0.35, box_center_y ≈ -0.60, +0.15)
  hand_L: (box_x ≈ +0.35, box_center_y ≈ -0.60, -0.15)
  발: 고정 (calcn_r x = -0.044, 박스 v11 protocol 적용)

t = 3.0 ~ 4.0 s   Ascent (concentric squat up + 박스 carry)
  역순 (descent의 reverse)
  knee 먼저 펴고 hip 따라가는 squat strategy (knee-dominant)
  손은 박스를 잡은 채 카리(carry) 위치로
```

---

## 3. Numeric Target (Stage 1 IK용)

| Coordinate | t=0 | t=2.0 (peak) | t=4.0 | 근거 |
|------------|-----|-------------|------|------|
| hip_flexion_r/l | 0° | **+110°** | 0° | P3 squat baseline + medium-deep |
| knee_angle_r/l | 0° | **-115°** | 0° | P3 (135° upper), Squat depth 110–135° |
| ankle_angle_r/l | 0° | **-20°** | 0° | P6 dorsiflex 20–25° |
| pelvis_tilt | 0° | **-35°** | 0° | trunk inclination ~30–56° (P3); squat은 stoop보다 작음 |
| pelvis_ty | 0.0 | **-0.30 m** | 0.0 | squat 하강 (deep) |
| pelvis_tx | 0.0 | **-0.10 m** | 0.0 | knee forward 보상 + 발 고정 |
| lumbar L1–L5 (각) | 0° | **-5°** | 0° | sum -25°, segmental equal |
| shoulder_elv_r/l | 0° | ~10° | ~10° (carry) | forward reach |
| elv_angle_r/l | 0° | ~120° | ~80° | hand 박스 측면 도달 |
| elbow_flex_r/l | 0° | ~10° | ~80° (carry) | reach → carry transition |

⚠️ 위 값은 Day 3 opensim-agent의 hip/knee ROM 실측 후 조정 가능. 만약 TLFB v2.0 default hip ROM이 ≤ 100°이면 110° 불가 → 모델 ROM 확장 또는 Akhavanfar 모델 채택 필요.

---

## 4. Box position (ground frame, ThoracolumbarFB 좌표)

```
calcn_r x = -0.044 m (발, 고정)
toes_r  x = +0.134 m (발 끝)

박스 중심 x = -0.044 + 0.35 = +0.306 m
박스 중심 z = 0 (symmetric)
박스 중심 y (mid-height) = ground_y + box_height/2 = -0.905 + 0.15 = -0.755 m
박스 dimension: 30 cm × 30 cm × 30 cm (W × D × H, 박스 v11 standard)
```

손 도달 target:
```
hand_R target at t=2.0: (+0.306, -0.755, +0.15)  [박스 우측면]
hand_L target at t=2.0: (+0.306, -0.755, -0.15)  [박스 좌측면]
```

---

## 5. NIOSH RWL 계산 (참고)

NIOSH RWL = 23 × HM × VM × DM × AM × FM × CM
- HM (horizontal multiplier) = 25/H (H=35 cm) = 0.714
- VM = 1 - 0.003 × |V - 75| (V=15 cm 박스 mid-height) → 1 - 0.003 × 60 = 0.82
- DM = 0.82 + 4.5/D (D = 75 cm hand travel) = 0.82 + 0.06 = 0.88
- AM = 1 (symmetric)
- FM ≈ 1 (single lift)
- CM = 1 (good coupling)

RWL ≈ 23 × 0.714 × 0.82 × 0.88 × 1 × 1 × 1 ≈ **11.85 kg**

→ Lifting Index (LI) = 15 / 11.85 = **1.27** (>1, 위험 약간 초과 — suit가 ES 부담 줄이는 효과 검증 가치 있음)

15 kg + 35 cm horizontal은 NIOSH RWL 약간 초과. caregiving worker realistic loading 시나리오로 적절.

---

## 6. 위험 / Open Issue

1. **TLFB v2.0 hip_flexion default 범위 미실측** (Day 3 opensim-agent 작업): 110° 가능 여부 확인 필요. 불가 시 Akhavanfar 모델 swap
2. **deep squat (knee 110°+) IK 안정성**: 박스 v11에서 medium squat까지만 검증. deep squat은 새로 검증 필요
3. **발 고정 protocol**: 박스 v11에서 검증된 calcn_r x = -0.044 고정 + pelvis_tx 보상 → squat은 pelvis_tx 변화 작음 (knee forward dominant) but ankle dorsiflex 20°가 핵심
4. **여성 65세 그룹 hip mobility 제한** (P8): hip flexion 가용범위 ↓ → 동일 박스 위치에서 lumbar flexion 강제 ↑ → Phase 2에서 별도 그룹
5. **suit 효과 squat에서 stoop보다 작음** (P3 핵심): 본 시나리오 결과 ES reduction 28% (stoop)보다 낮을 가능성 — 정직하게 보고

---

## 7. Sanity Check (literature 대비)

| 항목 | 우리 spec | Literature 평균 | 일치? |
|------|----------|-----------------|-------|
| 박스 weight | 15 kg | 6-20 kg (P1-P7) | ✅ 중간값 |
| Hip flexion peak | 110° | 85-135° (P3, P6) | ✅ 범위 내 |
| Knee flexion peak | 115° | 110-135° deep (P3) | ✅ deep squat 범주 |
| Trunk inclination | 35° | 30-56° (P3) | ✅ 하한 |
| Lift duration | 4 s | 1.3-6 s (P3 exercise / occupational) | ✅ occupational 표준 |
| Foot stance | parallel | parallel (P3, P6, P7) | ✅ symmetric standard |

Sanity check 통과. 다음 Day 3 작업: opensim-agent hip/knee ROM 실측 후 spec 미세조정.
