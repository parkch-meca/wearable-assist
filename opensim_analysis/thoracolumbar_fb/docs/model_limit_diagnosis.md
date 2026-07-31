# ThoracolumbarFB v2.0 — Step 1.3 진단 보고

**Date**: 2026-04-28
**Diagnostic outputs**: [thoracolumbar_fb_rom_analysis.md](thoracolumbar_fb_rom_analysis.md), [reach_analysis.md](reach_analysis.md)

## 핵심 발견

**Joint ROM은 병목이 아닙니다. CoordinateCouplerConstraint가 진짜 병목입니다.**

### 진단 1 (반증): Lumbar/Thoracic flexion ROM 부족 — **❌ 가설 기각**

| 영역 | 모델 ROM | 문헌 (정상 성인) | 평가 |
|---|---|---|---|
| Lumbar L1/2 ~ L5/S1 (각 segment) | ±90° | ~10-15° flex/level | 모델이 9배 더 큼 |
| Thoracic T1/2 ~ T11/12 (각 segment) | ±90° | ~3-5° flex/level | 모델이 20배 더 큼 |
| **총 lumbar flex 능력** | **540°** | ~50-60° | 9배 |
| **총 thoracic flex 능력** | **990°** | ~30-40° | 25배 |

→ Spine ROM은 비현실적으로 큼. 굴곡 제한이 모션 설계의 병목일 수 없음.

### 진단 2 (반증): Hip flexion ROM 부족 — **❌ 가설 기각** (사실상)

- 모델: ±120° (hip flex 최대 +120°)
- 문헌: 정상 성인 130° flex
- Gap: 10° — 무시 가능 (들기 작업에 충분)

### 진단 3 (반증): Arm DoF 부족 — **❌ 가설 기각**

- shoulder_elv: 0~155°
- elv_angle: -90~155°
- elbow: 0~155°
- 팔 길이 549 mm 측정 (humerus 291 mm + 전완+손목 258 mm)

→ 팔 좌표계 자유도 충분.

### 진단 4 (입증): **CoordinateCouplerConstraint가 어깨를 강제 elevation** — **✅ 진짜 병목**

모델에 4개의 coupler constraint:

```
coupler_shoulder_elv_r:  shoulder_elv_r = -1.62 × pelvis_tilt
coupler_shoulder_elv_l:  shoulder_elv_l = +1.62 × pelvis_tilt
coupler_elv_angle_r:     elv_angle_r    = -2.0  × pelvis_tilt
coupler_elv_angle_l:     elv_angle_l    = -2.0  × pelvis_tilt
```

**Pelvis tilt가 음수 (stoop)일수록 어깨가 강제로 forward elevation됨:**

| pelvis_tilt | 강제 sh_elv (° forward) | 강제 elv_angle (°) |
|---:|---:|---:|
| 0° (직립) | 0° | 0° |
| −20° | +32.4° | +40° |
| −35° | +56.7° | +70° |
| −40° | +64.8° | +80° |
| −50° | +81.0° | +100° |

→ Stoop posture에서 팔이 옆구리에 수직으로 떨어질 수 없음. Coupler가 어깨를 앞으로 들어올림.

## Reach test 결과 비교

| Posture | shoulder_y | sh_elv (couple-imposed) | hand_y (with coupler) | hand_y geometric max (no coupler) | gap |
|---|---:|---:|---:|---:|---:|
| P1 shallow (v5) | +0.195 | +56.7° | **−0.331** | −0.354 | 23 mm |
| P2 stoop_squat (v3) | −0.037 | +81.0° | **−0.563** | −0.586 | 23 mm |
| P3 deep lumbar | −0.199 | +64.8° | **−0.735** | −0.748 | 13 mm |
| P4 deep+thoracic | −0.209 | +72.9° | **−0.603** | −0.758 | **155 mm** |

**관찰:**

1. P3 (pelvis_tilt=-40°, hip 110°, knee -45°, lumbar -10°/level): hand_y=-0.735 — **그라운드 박스 (mid -0.74)에 거의 도달**
2. P4 (P3에 thoracic flex 추가): pelvis_tilt이 더 크기 때문에 (-45°) coupler가 더 강하게 어깨를 들어올림 → hand_y -0.603 (P3보다 더 위로 감)
3. **deeper stoop이 무조건 reach를 늘리는 것이 아님**: pelvis_tilt 깊을수록 coupler가 어깨 elevation 강제 → 팔이 위로 들리는 역효과

**가장 중요한 reach 가능 박스 위치:**

| 박스 위치 | P1 shallow | P2 stoop_squat | P3 deep lumbar | P4 deep+thoracic |
|---|---|---|---|---|
| Ground (mid −0.74) | ❌ +409 mm | ❌ +177 mm | **✅ −5 mm** | ❌ +137 mm |
| Low pallet (mid −0.60) | ❌ +269 mm | ❌ +37 mm | ✅ −135 mm | ✅ −3 mm |
| Low workbench (mid −0.30) | ❌ +31 mm | ✅ −263 mm | ✅ −435 mm | ✅ −303 mm |
| Std workbench (mid 0.0) | ✅ −331 mm | ✅ −563 mm | ✅ −735 mm | ✅ −603 mm |

→ **현재 모델로 그라운드 박스 reach 가능한 유일한 자세**: P3 (deep lumbar dominant, pelvis_tilt=-40°). 단 5mm 여유.

## 권고

### 옵션 A — 모델 수정 없이 P3 자세로 진행 (가장 빠름)

- 박스 motion v6 = P3 자세 (pelvis_tilt=-40°, hip 110°, knee -45°, lumbar -10°/level)
- 그라운드 박스 + 측면 잡기 가능
- 시각적으로 v3보다 lumbar dominant (자연스러운 deadlift-like 자세)
- 단점: pelvis_tilt 깊어 어깨 forward 강제 (coupler 효과). 양손이 박스 옆구리 잡는 자세에서 어깨가 앞으로 살짝 elevated → 어색할 수 있음

### 옵션 B — Coupler 제거 (근본 수정)

- 4개 constraint 제거 → 어깨 좌표 완전 자유
- 모든 박스 위치 도달 가능
- Phase 1a 재현 검증 필요 (regression test)
- Stage 4 재시각 검증 필요
- **Step 1.4 feasibility report 참조**

### 옵션 C — Coupler를 motion file에 ' baked in'

- Constraint는 제거하되, 모션 설계에서 coupler 관계를 데이터로 적용
- Phase 1a stoop motion: 동일 coupler 관계 유지 → 결과 동일
- Box motion: coupler 관계 무시 가능
- 가장 hybrid한 접근

### 옵션 D — 현 모델 유지 + 기존 motion v4 활용

- v4 (옵션 A: box adapted to hand) 결과 활용
- 추가 모션 설계 포기
- 논문은 v4 박스 결과로 작성

## 진단 결론

**모델 ROM 확장은 불필요.** 진짜 문제는 4개의 어깨 coupler constraint이며, 이는 다음 중 하나로 해결 가능:

1. **자세 조정 (P3)** — 코드 수정만으로 해결 (1시간)
2. **Coupler 제거** — 모델 XML 4줄 수정 + Phase 1a 재현 검증 (3-4시간)
3. **Coupler를 motion에 hardcoding** — apply_state에서 coupler 관계 명시 (2시간)

다음 Step 1.4에서 옵션 B (coupler 제거)의 비용과 회귀 검증 절차 정리.
