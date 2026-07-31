# TLFB+forearm_v1 Squat ROM 실측 (Gap 3)

**모델**: `MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim`  
**경로**: `/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/`  
**측정일**: 2026-05-26  
**방법**: OpenSim Python API (`model.getCoordinateSet()` iterate, `initSystem()` 후 실측)

---

## 1. 실측 표 (Squat 관련 coord)

### 1.1 하지 + Pelvis

| Coordinate | Min (deg/m) | Max (deg/m) | Range | Squat 요구 | 충족 여부 |
|------------|------------|------------|-------|-----------|---------|
| `hip_flexion_r` | -120.0 | **+120.0** | 240.0 | 100-130 deg (positive = flexion) | **부분 PASS** |
| `hip_flexion_l` | -120.0 | **+120.0** | 240.0 | 100-130 deg | **부분 PASS** |
| `hip_adduction_r` | -120.0 | +120.0 | 240.0 | -15~+15 (발 벌림) | PASS |
| `hip_adduction_l` | -120.0 | +120.0 | 240.0 | | PASS |
| `hip_rotation_r` | -120.0 | +120.0 | 240.0 | -30~+30 | PASS |
| `hip_rotation_l` | -120.0 | +120.0 | 240.0 | | PASS |
| `knee_angle_r` | **-120.0** | +10.0 | 130.0 | -100~-130 (음수=굴곡) | **부분 PASS** |
| `knee_angle_l` | **-120.0** | +10.0 | 130.0 | -100~-130 | **부분 PASS** |
| `ankle_angle_r` | -90.0 | +90.0 | 180.0 | +20~+30 dorsiflexion | PASS |
| `ankle_angle_l` | -60.0 | **+60.0** | 120.0 | +20~+30 | PASS |
| `pelvis_tilt` | -90.0 | +90.0 | 180.0 | +10~+30 anterior | PASS |
| `pelvis_ty` | -1.00 m | +2.00 m | 3.00 m | ~0.65-0.93 m (IK free) | PASS |

### 1.2 Lumbar FE (5 분절)

| Coordinate | Min (deg) | Max (deg) | Range | Squat 단독 요구 |
|------------|----------|----------|-------|--------------|
| `L1_L2_FE` | -89.95 | +89.95 | 179.9 | — (각 분절 제한 없음) |
| `L2_L3_FE` | -89.95 | +89.95 | 179.9 | |
| `L3_L4_FE` | -89.95 | +89.95 | 179.9 | |
| `L4_L5_FE` | -89.95 | +89.95 | 179.9 | |
| `L5_S1_FE` | -89.95 | +89.95 | 179.9 | |
| **합계 최대** | | | **~450 deg** | Squat 20-40 deg 요구 → PASS |

### 1.3 Thoracic FE (대표)

모든 thoracic 분절 (T1_T2~T12_L1_FE): **±89.95 deg** 균일  
Squat 흉추 요구 (~ ±5 deg per segment) 대비 대폭 여유 → PASS

---

## 2. Bottleneck Coord 식별

### 주요 Bottleneck: hip_flexion + knee_angle (경미한 제약)

**hip_flexion_r/l = ±120 deg**  
- Squat deep flexion 요구: **100-130 deg** (긴 문헌 범위)
- 모델 최대: 120 deg
- 결론: 100-120 deg 범위는 커버됨. 120-130 deg 구간은 **10 deg 부족**
- 실제 squat에서 hip flexion이 정확히 130 deg를 요구하는 경우는 일반 성인 기준 드물며, 중간 squat (moderately deep) 기준 100-115 deg이면 충분 (Escamilla 2001, J Biomech)

**knee_angle_r/l = [-120, +10] deg (음수 = 굴곡)**  
- Squat deep knee flexion 요구: -100 ~ -130 deg
- 모델 최대 굴곡: -120 deg
- 결론: 100-120 deg 커버됨. 130 deg deep squat은 **10 deg 부족**
- 단, 박스 들기 squat (반 squat, semi-squat)은 knee flexion 90-110 deg가 전형적 (Straker 2003, Ergonomics) → 실제 작업 시나리오에서 충분

### 2차 주의: ankle_angle 비대칭

**ankle_angle_r: [-90, +90] deg vs ankle_angle_l: [-60, +60] deg**  
- L/R 비대칭: 오른발 ±90 deg, 왼발 ±60 deg
- Squat dorsiflexion 요구 (~20-30 deg)는 양측 모두 충족
- 비대칭의 원인: XML에서 ankle_l joint 정의가 의도적으로 ±60 deg (1.047 rad)로 설정됨 — Coupler 제거 전 원본 TLFB v2.0에서도 동일
- 기능적 영향: Squat dorsiflexion 범위(최대 30 deg) 내에서는 문제없음

### PASS 항목 (병목 아님)

- Lumbar FE: 각 분절 ±90 deg → squat 20-40 deg 요구 대비 무제한에 가까움
- Pelvis_tilt: ±90 deg → squat anterior tilt (10-30 deg) 여유
- Pelvis_ty: [-1.00, +2.00] m → IK free; 중립 서기 ~0.93 m, deep squat ~0.65 m 충분히 허용
- Hip adduction/rotation: ±120 deg → 발 벌림 (15 deg abd) 여유

---

## 3. Baseline (Variant A) Squat 가능 여부 판정

### 판정: **부분 PASS**

| 조건 | 결과 | 근거 |
|------|------|------|
| Hip flexion 100 deg | PASS | 모델 최대 120 deg ≥ 100 deg |
| Hip flexion 120 deg | PASS | 모델 최대 = 120 deg (경계) |
| Hip flexion 130 deg | FAIL | 모델 최대 120 deg < 130 deg (10 deg 부족) |
| Knee flexion 100 deg | PASS | 모델 최대 120 deg ≥ 100 deg |
| Knee flexion 120 deg | PASS | 모델 최대 = 120 deg (경계) |
| Knee flexion 130 deg | FAIL | 모델 최대 120 deg < 130 deg (10 deg 부족) |
| Ankle dorsiflexion 30 deg | PASS | 양측 60-90 deg 가용 |
| Lumbar flexion 20-40 deg total | PASS | 각 분절 ±90 deg |
| Pelvis_ty squat 하강 | PASS | [-1.0, +2.0] m |

**결론**: Semi-squat (박스 들기 전형, knee/hip 90-115 deg) → **PASS**.  
Deep squat (130 deg 요구) → **10 deg FAIL**. 단, 박스 들기 시나리오는 deep squat이 아닌 semi-squat이므로 실제 작업 분석 목적에서는 **기능적 PASS**.

### 중요 맥락

- Straker 2003 (Ergonomics) 박스 들기 semi-squat: knee peak ~105 deg, hip peak ~110 deg → 모델 120 deg 이내
- Escamilla 2001 (J Biomech): competitive squat 130 deg는 powerlifting 기준, 직업 들기 작업은 90-110 deg
- 즉, TLFB+forearm_v1을 **박스 squat lift 분석에 ROM 확장 없이 사용 가능** — Variant B 확장은 선택사항

---

## 4. 한계 시 확장 방안 (Variant B spec)

ROM이 bottleneck이 될 경우 (deep squat 시나리오 채택 시) 적용 가능한 최소 변경:

### 옵션 A: Hip flexion + Knee flexion 10 deg 확장 (XML 2줄)

```xml
<!-- hip_flexion_r/l: 현재 [-120, 120] → [-120, 135] -->
<!-- knee_angle_r/l:  현재 [-120, 10]  → [-135, 10] -->

<!-- hip_flexion_r -->
<range>-2.0943950999999998 2.3561945</range>  <!-- 135 deg = 2.3562 rad -->

<!-- knee_angle_r -->
<range>-2.3561945 0.1745329</range>  <!-- -135 deg = -2.3562 rad -->
```

적용 위치: XML 내 `<Coordinate name="hip_flexion_r">`, `<Coordinate name="hip_flexion_l">`,  
`<Coordinate name="knee_angle_r">`, `<Coordinate name="knee_angle_l">` 각 `<range>` 태그

### Phase 1a Regression 영향 예상

| 항목 | 예상 영향 |
|------|---------|
| Phase 1a stoop 동작 | 최소 — stoop은 hip 60-80 deg, knee <30 deg → 범위 확장과 무관 |
| ES activation | 변화 없음 (IK solution 동일) |
| max ΔES | ~0 %p (ROM constraint가 stoop 범위 밖에서 확장되므로) |
| 판정 | PASS 예상 (regression test 권장) |

### 옵션 B: 현행 유지 (권장)

Semi-squat 시나리오 (박스 들기 = 실제 작업)는 현 ROM으로 충분.  
XML 수정 불필요 → Phase 1a regression risk 0.

---

## 5. Variant B Spec (parallel-explorer-agent 전달용)

Variant B = TLFB+forearm_v1 현행 모델 (no_coupler) + **ROM 확장 없이 적용**

- 모델 파일: `MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim`
- Squat 시나리오: Semi-squat (knee peak 90-115 deg, hip peak 95-115 deg)
- ROM 상한: hip 120 deg, knee 120 deg — 박스 들기 semi-squat 내 충분
- ROM 확장 Variant B': hip/knee 10 deg 확장 (deep squat 130 deg 시나리오용, 사용자 승인 필요)
- Phase 1a 영향: 확장 시에도 stoop 범위 밖 → ΔES ~0 예상, regression test 권장

### parallel-explorer-agent 권장 메시지

Variant A (forearm_v1 no_coupler) baseline을 Squat lift에 적용 시:
- ROM 관점 기능적 PASS (semi-squat 기준)
- 추가 모델 수정 불필요
- IK target: knee peak -105 to -115 deg, hip peak 105-115 deg 설정 권장
- Deep squat 요구 시 Variant B' (hip/knee 각 10 deg 확장) 검토

---

## 6. 측정 방법 노트

- Python API: `/home/sysop/miniconda3/envs/opensim/bin/python` + opensim 4.x
- `model.initSystem()` 후 `getCoordinateSet()` 전체 iterate
- 회전형: `getRangeMin/Max()` radians → degrees 변환
- 병진형: `getRangeMin/Max()` meters 직독
- Locked 확인: `coord.getLocked(state)` — 57개 rib/sternum/forearm coords 잠금 (squat에 무관)

---

*Gap 3 실측 완료 (2026-05-26). opensim-agent 산출.*
