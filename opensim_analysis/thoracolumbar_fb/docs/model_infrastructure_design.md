# Model Infrastructure Design (2026-04-29)

**목적**: 박스/Squat/Walk 등 다양한 작업에 동일하게 적용되는 검증된 OpenSim Moco 인프라 설계.  
**원칙**: 시도 X, 설계만. Step 2 (구현) 전 CHEOL HOON님 검토 필수.  
**근거**: 박스 motion v3-v7 5회 반복 실패 분석 + Phase 1a 검증 완료 방법론 계승.

---

## 1. Foot Contact Model

### 1.1 현재 방식 (ExternalLoads GRF STO) — 문제점 명시

현재 Phase 1a 및 Phase 2 박스 motion 모두 `stoop_grf_v5.sto`에 의존한다.  
이 파일은 stoop_synthetic_v5 kinematics 기반 정적 GRF(368 N/foot, 상수)로 생성되었다.

문제:
- Semi-squat 박스 motion에서 pelvis_ty가 -0.089 m 하강 → 수직 가속도 발생 → 정적 GRF와 동역학 불일치.
- Phase 2 B_noload에서 pelvis_ty reserve 3570 N 발생 (Hicks 2015 기준 37 N 이하 필요).
- 새 동작(Squat, Walk)마다 별도 GRF 파일 수작업 생성 필요 → 확장성 없음.

### 1.2 Hunt-Crossley Sphere 방식 — 목표 아키텍처

**참조 구현**: Falisse et al. 2019 (PLOS One), OpenSim 예제 `example2DWalking.py`, Dembia 2020

Hunt-Crossley 접촉 구는 발과 바닥 사이의 비선형 접촉력을 실시간 계산한다.  
Motion이 주어지면 GRF는 solver가 자동 계산 — 외부 STO 파일 불필요.

#### 1.2.1 OpenSim 내 구현 클래스: `SmoothSphereHalfSpaceForce`

Falisse 2019 / OpenSim 4.x에서 사용되는 smooth(연속 미분 가능) 버전. IPOPT 최적화 시 필수.  
(고전 `HuntCrossleyForce`는 불연속 미분 → Moco에 부적합. Walker 예제 등 forward simulation에만 사용.)

#### 1.2.2 구 파라미터 (2D gait 예제 실측, OpenSim 번들)

| 구 이름 | 부착 body | radius (m) | 위치 (body frame) |
|---------|-----------|-----------|------------------|
| heel_r / heel_l | calcn_r/l | **0.035** | (0.031, 0.010, 0) |
| front_r / front_l | calcn_r/l (앞) | **0.015** | (0.177, -0.016, ±0.005) |

Force 파라미터 (2D gait 예제):
```xml
<stiffness>3067776</stiffness>       <!-- N/m^2, 접촉 강성 -->
<dissipation>2.0</dissipation>        <!-- s/m -->
<static_friction>0.8</static_friction>
<dynamic_friction>0.8</dynamic_friction>
<viscous_friction>0.5</viscous_friction>
```

#### 1.2.3 ThoracolumbarFB 적용 시 조정 필요 사항

ThoracolumbarFB calcn body는 2D gait와 다른 스케일/좌표계.  
현재 모델 실측값:
- `calcn_r` 기준점: ground frame x = -0.0442 m (직립 시)
- `toes_r` 기준점: ground frame x = +0.1342 m
- ground y = -0.905 m

조정 방향:
- heel sphere: calcn_r body frame에서 heel bone 위치에 배치 (약 후방 -0.05 m, y 0)
- ball sphere: toes_r 또는 metatarsal 위치에 배치 (약 전방 +0.06 m)
- radius: 0.035 m (heel), 0.015~0.020 m (ball) — 75 kg 남성 체중 지지 기준

**구현 전 필수 확인 사항**:
- calcn_r body의 geometry mesh에서 heel/ball 좌표 실측 (FK로 확인)
- ContactHalfSpace floor 정의 (y = -0.905 m, 우리 모델 ground plane)
- 양발 대칭 확인 (calcn_l/toes_l 반대 z)

### 1.3 Contact Sphere vs ExternalLoads 비교

| 항목 | ExternalLoads GRF STO (현재) | SmoothSphereHalfSpaceForce (목표) |
|------|-----------------------------|------------------------------------|
| GRF 계산 | 사전 생성 필요 (동작마다 별도 파일) | 자동 (solver가 contact 계산) |
| GRF 일관성 | kinematics와 불일치 가능 → reserve 폭발 | kinematics와 완전 일관 |
| 적용 방법 | MocoInverse + ModOpAddExternalLoads | MocoTrack (또는 MocoStudy) |
| Solver 요건 | 모든 Moco tool | MocoTrack / MocoStudy 권장 |
| 구현 난이도 | 낮음 (이미 검증됨) | 중간 (모델 수정 + 파라미터 튜닝 필요) |
| Reserve 위험 | 높음 (GRF mismatch 시) | 낮음 |
| 확장성 | 낮음 (동작마다 GRF 재생성) | 높음 (모션만 변경) |

**결론**: 인프라 목표는 Contact Sphere 방식. 그러나 Phase 1a 호환성 유지를 위해 병행 지원 설계.

### 1.4 박스 / Squat / Walk 적용 계획

| 작업 | 발 접촉 방식 | 비고 |
|------|------------|------|
| stoop lift (Phase 1a) | ExternalLoads (현행) | 이미 검증 완료, 변경 불필요 |
| semi-squat box lift | SmoothSphereHalfSpaceForce | 목표: pelvis_ty reserve < 37 N |
| squat | SmoothSphereHalfSpaceForce | box와 동일 모델 재사용 |
| walking | SmoothSphereHalfSpaceForce | Falisse 2019 패턴 직접 재사용 |

---

## 2. ExternalForce 정확 적용 (박스, 슈트 등)

### 2.1 Hand External Force — 박스 무게

#### 2.1.1 문제 진단 (기존 방식)

Phase 2 현행: 박스 무게를 ExternalForce로 적용하지 않고 reserve로 처리.  
결과: pelvis_tilt reserve 221 N·m 발생 (Hicks 2015 기준 13 N·m 이하 필요).

Newton 균형:  
- 75 kg 몸 + 20 kg 박스 = 930.45 N 전체 수직 하중
- 발 GRF만 있을 경우: 각 발 465.2 N 필요 (vs Phase 1a의 368 N)
- 또는 발 GRF = 368 N/foot + 손 하중 = 981 N 총 균형 요건 충족

#### 2.1.2 정확한 방법: ExternalForce time-series

```python
# 박스 ExternalForce — hand_r body에 박스 절반 무게 (각 손 98.1 N 하향)
# 적용 시점: grasp 시작 후만 (alpha 함수로 시간 변화)
BOX_MASS = 20.0   # kg
G = 9.81
HAND_FORCE_Y = -BOX_MASS * G / 2   # -98.1 N (각 손에)

# alpha: grasp 전 0, grasp 중 1
# → 발 GRF는 상수 (368 N/foot) 유지
# → 손 하중 = 98.1 N × alpha(t)
# → 전체 수직 균형: 2×368 + 2×98.1×alpha ≈ 930 N (grasp 시 완전 균형)
```

적용 방식:
```python
ext_force_r = osim.ExternalForce()
ext_force_r.setName('hand_box_force_r')
ext_force_r.setAppliedToBodyName('hand_r')           # hand_r body에 직접
ext_force_r.setForceExpressedInBodyName('ground')    # ground frame 기준 수직력
ext_force_r.setPointExpressedInBodyName('hand_r')    # 적용 점: hand_r origin
```

참조: `opensim_moco_best_practices.md` §2.1(b) — Newton 균형 균형 원칙 (930 N).

#### 2.1.3 Grasp 시점 자동 Detection

biomechanics-agent 문서(`ground_box_lift_side_grip.md`) §1 기준:
- t = 2.0 s: grasp peak
- alpha 함수로 자동 time-varying:

```python
def alpha_grasp(t):
    """박스 grasp 시점 alpha 함수 (t=1.5-2.0 s 선형 증가)"""
    if t < 1.5:  return 0.0
    if t <= 2.0: return (t - 1.5) / 0.5   # 선형 증가 (또는 cosine)
    if t <= 4.0: return 1.0                # 들고 있는 중
    if t <= 4.5: return (4.5 - t) / 0.5   # 내려놓기
    return 0.0
```

#### 2.1.4 박스 Trajectory 자동 Update

손 위치를 추적해 박스 중심을 계산:
```python
# 렌더러 + Moco 결과 분석 모두에서 사용
# grasp 전: 박스 정적 위치 (box_x_ground, box_bottom_y, 0)
# grasp 후: hand_R y - BOX_HEIGHT/2 (손 위치 추적)
box_center_y = hand_center_y(t) - BOX_HEIGHT/2  # grasp 시
```

### 2.2 슈트 External Force — Phase 1a 검증 방식 계승

Phase 1a 검증된 패턴 (`suit_unit_diagnosis.md`):

```python
SUIT_FORCE_N  = 200           # SMA 수축력 (N) — 이 값을 입력
MOMENT_ARM    = 0.12          # 모멘트 암 (m) — 0.10~0.13 m 범위
SUIT_TORQUE   = SUIT_FORCE_N * MOMENT_ARM  # = 24.0 N·m (OpenSim에 적용되는 값)
```

이 변환식을 독립 모듈로 분리 (Section 4 참조).

적용 body: thoracic1 (+Tz), pelvis (-Tz) — Phase 1a와 동일.

### 2.3 외력 계층 구조

```
외력 종류          | 적용 body     | 단위  | 시간 변화 | 참조
-------------------|--------------|-------|----------|--------
발 GRF (contact)  | calcn_r/l    | N     | 자동      | contact sphere
또는 발 GRF (STO) | calcn_r/l    | N     | 상수/파일 | GRF XML
박스 손 하중 R     | hand_r       | N     | alpha(t)  | 섹션 2.1
박스 손 하중 L     | hand_l       | N     | alpha(t)  | 섹션 2.1
슈트 토크 상부     | thoracic1    | N·m   | alpha(t)  | Phase 1a
슈트 토크 하부     | pelvis       | N·m   | alpha(t)  | Phase 1a (반대 부호)
```

---

## 3. Reserve 자동 정상화 (RRA-like)

### 3.1 현재 문제점

Phase 1a: `ModOpAddReserves(10.0)` 일괄 적용 → pelvis_ty = 46 N (borderline).  
Phase 2 박스: 동일 방식 → pelvis_ty = 3570 N, pelvis_tilt = 221 N·m (기준 대폭 초과).

원인: GRF가 kinematics와 불일치 (stoop_grf_v5를 semi-squat에 적용).

### 3.2 Hicks 2015 허용 기준

| 지표 | 허용 기준 | 75 kg / 1.75 m 기준값 |
|------|---------|----------------------|
| 번역 잔류력 | < 5% body weight | < 36.8 N |
| 회전 잔류 모멘트 | < 1% BW × height | < 12.9 N·m |
| Reserve 기여 | < 5-10% net joint moment | 관절별 확인 |

### 3.3 ModOpAddResiduals + ModOpAddReserves 분리 전략

OpenSim 공식 3D walking 예제 검증 패턴:

```python
# 올바른 순서 (공식 exampleMocoInverse.py 기준)
model_proc.append(osim.ModOpAddResiduals(250.0, 50.0, 1.0))
#  인자: translational_F (N), rotational_M (N·m), scale_factor
#  → pelvis 6 DOF에만 residual actuator 부여 (번역 250 N, 회전 50 N·m)

model_proc.append(osim.ModOpAddReserves(1.0))
#  인자: optimalForce (N·m)
#  → 나머지 모든 좌표에 약한 보조 actuator (1 N·m)
```

우리 작업별 권장값:

| 작업 | translational_F | rotational_M | 이유 |
|------|----------------|-------------|------|
| stoop lift (Phase 1a) | 50 N | 20 N·m | 정적 동작, 작은 가속도 |
| semi-squat box lift | **300 N** | **50 N·m** | semi-squat 수직 가속도 |
| squat | 300 N | 50 N·m | box와 동일 수준 |
| walking | 250 N | 50 N·m | 공식 예제 값 |

300 N 값의 근거: walking 공식 예제 pelvis_ty = 300 N → 체중의 40% 수준. semi-squat 가속도는 보행 수준 이하이므로 300 N이면 충분.

### 3.4 Reserve 상태 자동 모니터링 코드

```python
def check_reserves(solution_path, bw_n=736.0, bw_nm=12.9):
    """
    Hicks 2015 기준으로 reserve 상태 자동 점검.
    bw_n: 75kg × 9.81 = 736 N (번역 기준 5%)
    bw_nm: 736 × 1.75 × 0.01 = 12.87 N·m (회전 기준 1%)
    """
    import pandas as pd
    sol = pd.read_csv(solution_path, skiprows=..., sep='\t')  # STO 파서
    reserve_cols = [c for c in sol.columns if 'reserve' in c.lower()]
    
    results = {}
    for col in reserve_cols:
        peak = sol[col].abs().max()
        if 'pelvis_t' in col:          # 번역 (N)
            status = 'PASS' if peak < bw_n * 0.05 else 'FAIL'
        else:                           # 회전 (N·m)
            status = 'PASS' if peak < bw_nm else 'FAIL'
        results[col] = {'peak': peak, 'status': status}
    return results
```

### 3.5 GRF Kinematics-Consistent 재계산 (경로 2, 권장)

`opensim_moco_best_practices.md` §6 "경로 2" 설계:

1. 박스 motion kinematics(.mot)에서 pelvis 수직 가속도 계산 (수치 미분, SG 필터 후)
2. 전체 시스템 질량 (75 + 20 kg) × 수직 가속도 → 필요 수직력 시계열
3. 왼/오른발 50:50 분배 → `box_grf_new.sto` 생성
4. `stoop_grf_v5.sto` 대체

이것이 Hicks 2015 RRA 절차의 핵심. Contact Sphere 도입 전 단기 해결책으로도 유효.

---

## 4. 슈트 단위 변환 일관성

### 4.1 오류 역사

Phase 1a (검증됨): `SUIT_FORCE_N (200 N) × MOMENT_ARM (0.12 m) = 24.0 N·m` 적용.  
Phase 2.C.4 (오류): `CONDITIONS = [('B_suit200', 200.0)]` → 200 N·m 직접 적용 = 실제의 8.33배.

`suit_unit_diagnosis.md` §4 참조.

### 4.2 suit_torque_module.py 설계

```python
"""
suit_torque_module.py
---------------------
SMA wearable suit 단위 변환 전용 모듈.
모든 Moco 스크립트가 import하여 사용 — 직접 값 기입 금지.

CHEOL HOON 님 슈트 스펙:
  SMA 수축력: 200 N (좌/우 각 100 N)
  모멘트 암: 0.10~0.13 m (중앙값 0.12 m)
  결과 토크: 200 N × 0.12 m = 24.0 N·m
"""

# 검증된 값 (Phase 1a 기준)
SUIT_FORCE_N_NOMINAL = 200.0   # N, SMA 정격 수축력
MOMENT_ARM_M         = 0.12    # m, 모멘트 암 (중앙값)
SUIT_TORQUE_NM       = SUIT_FORCE_N_NOMINAL * MOMENT_ARM_M  # = 24.0 N·m

def force_n_to_torque_nm(force_n: float, moment_arm_m: float = MOMENT_ARM_M) -> float:
    """SMA 수축력 (N) → 토크 (N·m) 변환.
    
    Args:
        force_n: SMA 수축력 (N). 예: 200.0
        moment_arm_m: 모멘트 암 (m). 기본값 0.12.
    Returns:
        torque_nm: OpenSim ExternalForce에 적용할 토크 (N·m).
    """
    return force_n * moment_arm_m

def sweep_conditions(forces_n: list, moment_arm_m: float = MOMENT_ARM_M) -> list:
    """Sweep 조건 생성. 반환: [(label, torque_nm), ...]
    
    Args:
        forces_n: [0, 50, 100, 150, 200] — N 단위 리스트
    Returns:
        [('F0_T0.0', 0.0), ('F50_T6.0', 6.0), ...] — label + N·m 값
    """
    return [(f'F{int(f)}_T{f*moment_arm_m:.1f}', f * moment_arm_m)
            for f in forces_n]
```

### 4.3 사용 예시

```python
# 모든 Moco 스크립트에서:
from suit_torque_module import force_n_to_torque_nm, sweep_conditions

# Phase 1a 동등 단건:
SUIT_TORQUE_PEAK = force_n_to_torque_nm(200)  # = 24.0 N·m

# Phase 2 sweep:
CONDITIONS = sweep_conditions([0, 50, 100, 150, 200])
# → [('F0_T0.0', 0.0), ('F50_T6.0', 6.0), ('F100_T12.0', 12.0), ...]
```

변수명 규칙: `_N` suffix = Newton (힘), `_NM` suffix = Newton·meter (토크).

---

## 5. 다양한 작업 Framework

### 5.1 설계 원칙: Base + Task Module

```
infrastructure/
├── base/
│   ├── model_setup.py         # 모델 로드, 근육 subset, ModOp 파이프라인
│   ├── suit_torque_module.py  # 슈트 단위 변환 (Section 4)
│   ├── reserve_monitor.py     # Hicks 2015 기준 reserve 점검 (Section 3.4)
│   └── ik_validation.py       # Stage 1 IK 자가 검증 체크리스트
│
├── tasks/
│   ├── stoop_lift/
│   │   ├── motion.py          # stoop_synthetic_v5.mot 참조
│   │   ├── grf.py             # stoop_grf_v5 (ExternalLoads, 검증 완료)
│   │   └── conditions.py      # B_noload, B_suit24 등
│   │
│   ├── box_lift/
│   │   ├── motion.py          # box_motion_v*.mot (FK 역산, 발 고정)
│   │   ├── grf.py             # Contact sphere 또는 GRF 재계산
│   │   ├── hand_force.py      # 박스 손 하중 ExternalForce (Section 2.1)
│   │   └── conditions.py      # B_noload, B_suit24 등
│   │
│   ├── squat/
│   │   ├── motion.py          # 새 설계 (box_lift 패턴 재사용)
│   │   ├── grf.py             # Contact sphere (box_lift와 동일)
│   │   └── conditions.py
│   │
│   └── walk/
│       ├── motion.py
│       ├── grf.py             # Falisse 2019 contact sphere 재사용
│       └── conditions.py
│
└── analysis/
    ├── es_activation.py       # ES 근활성 추출, suit effect 계산
    ├── reserve_report.py      # reserve 진단 리포트
    └── suit_effect_sweep.py   # linear regression, R² 계산
```

### 5.2 Base model_setup.py 설계

```python
def build_model_processor(
    model_path: str,
    grf_xml: str | None,
    muscle_list: list[str],
    residuals: tuple = (300.0, 50.0, 1.0),   # (trans_N, rot_Nm, scale)
    reserves_optf: float = 1.0,
    fiber_width_scale: float = 1.5,
) -> osim.ModelProcessor:
    """
    표준 Moco 모델 파이프라인 빌더.
    Phase 1a ~ Phase 2 모두 이 함수 통과.
    
    최소 변경으로 작업 전환: grf_xml + muscle_list 교체만으로 충분.
    """
    proc = osim.ModelProcessor(model_path)
    
    # 1. GRF (있을 경우)
    if grf_xml:
        proc.append(osim.ModOpAddExternalLoads(grf_xml))
    
    # 2. 근육 변환 (표준 순서 — 공식 예제 동일)
    proc.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    proc.append(osim.ModOpIgnoreTendonCompliance())
    proc.append(osim.ModOpIgnorePassiveFiberForcesDGF())
    proc.append(osim.ModOpScaleActiveFiberForceCurveWidthDGF(fiber_width_scale))
    
    # 3. Residuals (pelvis 전용) + Reserves (나머지)
    proc.append(osim.ModOpAddResiduals(*residuals))
    proc.append(osim.ModOpAddReserves(reserves_optf))
    
    return proc
```

### 5.3 작업 전환 예시

```python
# stoop_lift 작업:
from tasks.stoop_lift.motion import STOOP_MOT, STOOP_GRF_XML
from tasks.stoop_lift.conditions import STOOP_CONDITIONS
proc = build_model_processor(MODEL_PATH, STOOP_GRF_XML, PHASE1A_MUSCLES,
                              residuals=(50.0, 20.0, 1.0))

# box_lift 작업 (모델 setup은 동일, 외력만 변경):
from tasks.box_lift.motion import BOX_MOT, BOX_GRF_XML
from tasks.box_lift.conditions import BOX_CONDITIONS
proc = build_model_processor(MODEL_PATH, BOX_GRF_XML, PHASE1A_MUSCLES,
                              residuals=(300.0, 50.0, 1.0))

# walk 작업:
from tasks.walk.motion import WALK_MOT, WALK_GRF_XML
proc = build_model_processor(MODEL_PATH, WALK_GRF_XML, WALK_MUSCLES,
                              residuals=(250.0, 50.0, 1.0))
```

### 5.4 Pinheiro 2023 Multi-task Framework 비교

Pinheiro et al. 2023 (보행 + 계단 + 앉았다일어서기 동일 모델 적용)의 핵심 원칙:
1. Base model 공유 (근육, inertia, geometry — 불변)
2. Task module만 교체 (kinematics, external force, constraints)
3. 결과 비교 가능 (동일 근육 subset, 동일 reserve 기준)

우리 설계도 동일 철학. 차이점: 우리는 MocoInverse 고정 (prescribed kinematics) vs Pinheiro는 MocoTrack/MocoStudy 혼합. 들기 작업은 motion 품질이 충분할 경우 MocoInverse가 수렴 안정적.

---

## 6. 통합 아키텍처 다이어그램

```
[User / CHEOL HOON]
      |
      | 작업 지정 (stoop / box_lift / squat / walk)
      v
[Task Module]
  motion.py     → .mot 파일 (FK 역산, 발 고정)
  grf.py        → GRF XML+STO  또는  Contact Sphere
  hand_force.py → ExternalForce STO (박스 작업 시)
  conditions.py → suit torque N→N·m 변환 후 조건 리스트
      |
      v
[base/model_setup.py]
  build_model_processor()
    ├─ ModOpAddExternalLoads (GRF)
    ├─ ModOpReplaceMusclesWithDeGrooteFregly2016
    ├─ ModOpIgnoreTendonCompliance
    ├─ ModOpIgnorePassiveFiberForcesDGF
    ├─ ModOpScaleActiveFiberForceCurveWidthDGF(1.5)
    ├─ ModOpAddResiduals(trans, rot, scale)    ← 작업별 튜닝
    └─ ModOpAddReserves(1.0)
      |
      v
[Moco Solver]
  MocoInverse (prescribed kinematics)
  또는 MocoTrack (contact sphere 사용 시)
      |
      v
[analysis/]
  es_activation.py   → ES peak/mean, suit Δ%
  reserve_report.py  → Hicks 2015 PASS/FAIL
  suit_effect_sweep.py → slope, R²
      |
      v
[paper-agent / viz-agent]
  논문 섹션, 그림, 영상
```

**GRF 선택 분기**:
```
ExternalLoads (STO)       Contact Sphere
      ↑                         ↑
MocoInverse              MocoTrack / MocoStudy
(정적/준정적 동작)        (동적 동작, GRF 재현 필요)
stoop_lift [Phase 1a]    box_lift, squat, walk
(이미 검증)              (인프라 구축 대상)
```

---

## 7. Phase 1a 호환성

### 7.1 기존 결과 재현 가능 여부

새 인프라의 `base/model_setup.py`가 기존 Phase 1a 조건을 재현하려면:

```python
# Phase 1a 동등 호출 (기존 run_moco_phase1a_full.py와 동일 효과)
proc = build_model_processor(
    model_path = MOCO_STOOP_MODEL,
    grf_xml    = STOOP_GRF_XML,
    muscle_list= PHASE1A_114_MUSCLES,
    residuals  = (50.0, 20.0, 1.0),    # ← 현행 ModOpAddReserves(10.0)와 다름!
    reserves_optf = 1.0,
)
```

주의: 현행 Phase 1a는 `ModOpAddReserves(10.0)` 단일 적용 (pelvis residual 분리 안 됨).  
새 인프라로 전환 시 `ModOpAddResiduals + ModOpAddReserves(1.0)` 분리 → ES activation 소폭 변화 예상.

**Phase 1a 회귀 시험 필요**:
- 새 reserve 구조로 Phase 1a smoke test 재실행
- max ΔES < 5 %p → PASS, 기존 주요 결과(28% suit effect) 유지 여부 확인

### 7.2 24 N·m → 28% suit effect 재현

`suit_torque_module.py` 사용 시:
```python
SUIT_TORQUE_PEAK = force_n_to_torque_nm(200)  # = 24.0 N·m
# Phase 1a와 동일 → 28% suit effect 재현 기대
```

단, reserve 구조 변경(10.0 → residuals + 1.0)으로 baseline ES activation 변화 가능성.  
만약 28% → 25-31% 범위 내이면 해석적으로 동등 (Phase 1a의 "허용 오차" 범위).

---

## 8. 검증 시나리오

### 8.1 인프라 검증 1 — Phase 1a 재현 (최우선)

목적: 새 인프라(`build_model_processor`)가 기존 결과를 재현하는지 확인.

```
검증 조건:
  model: MaleFullBodyModel_v2.0_OS4_moco_stoop.osim
  motion: stoop_synthetic_v5.mot
  grf: stoop_grf_v5.xml/sto
  muscles: 114 (Phase 1a list)
  
기준 결과 (Phase 1a Full):
  ES peak activation (B_noload): ~91%
  Suit effect (24 N·m): ~28%
  Suit sweep slope: 1.164 %/Nm, R²=1.000

Pass 기준:
  - max ΔES peak < 5 %p (절대값)
  - suit effect 23~33% 범위 내 (±5 %p)
  - slope 방향성 유지 (음수)
  - R² > 0.95
```

### 8.2 인프라 검증 2 — 박스 motion (reserve 정상화)

목적: GRF 재계산 + residuals 분리로 reserve를 Hicks 2015 기준 이내로 낮추는지 확인.

```
검증 조건:
  model: MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim
  motion: 새 box motion (v8 이후)
  grf: box_grf_kinematics_consistent.sto (재계산 GRF)
  residuals: ModOpAddResiduals(300, 50, 1.0)

Pass 기준:
  - pelvis_ty reserve peak < 37 N (Hicks 기준 5% BW)
  - pelvis_tilt reserve peak < 13 N·m (Hicks 기준 1% BW×ht)
  - inf_pr < 1e-3 (수렴)
  - 수렴 시간 < 3600 s (1시간)
```

### 8.3 인프라 검증 3 — Squat 자연 확장

목적: 새 Task Module 추가가 Base Module 수정 없이 가능한지 확인.

```
설계:
  tasks/squat/motion.py — 박스 없는 pure squat (pelvis_tilt=-60, knee=-90°)
  tasks/squat/grf.py    — box_lift와 동일 contact sphere 재사용
  tasks/squat/conditions.py — suit torque 동일

Pass 기준 (설계 단계):
  - base/model_setup.py 수정 없이 squat 실행 가능
  - reserve Hicks 기준 충족
  - ES 활성도 패턴 생리학적 타당성 (hip extensor 주도 예상)
```

---

## 9. 예상 구현 시간

### Phase 별 작업 분해

| Phase | 작업 | 담당 에이전트 | 예상 시간 |
|-------|------|------------|---------|
| Step 2.1 | suit_torque_module.py 구현 + 단위 테스트 | opensim-agent | 0.5일 |
| Step 2.2 | GRF kinematics-consistent 재계산 스크립트 | opensim-agent | 1일 |
| Step 2.3 | base/model_setup.py + reserve_monitor.py | opensim-agent | 1일 |
| Step 2.4 | Phase 1a 재현 검증 (smoke 재실행) | moco-analysis-agent | 0.5일 |
| Step 2.5 | 박스 motion GRF 교체 + reserve 정상화 검증 | moco-analysis-agent | 1일 |
| Step 2.6 | Contact sphere 파라미터 튜닝 (ThoracolumbarFB) | opensim-agent | 2일 |
| Step 2.7 | Task module 구조 구축 (stoop, box, squat 포함) | opensim-agent | 1일 |
| **소계** | **기본 인프라** | | **7일** |

| Phase | 작업 | 예상 시간 |
|-------|------|---------|
| Step 3.1 | 박스 motion v8 + 인프라 통합 검증 | 2일 |
| Step 3.2 | Phase 2.C.4 box conditions (올바른 24 N·m) 재실행 | 1일 |
| Step 3.3 | Squat task module 추가 | 1일 |
| **소계** | **박스 + Squat 검증** | **4일** |

**전체 인프라 구축**: 약 2주 (11일).  
**참고**: 박스 motion 4개월 patch 패턴 방지를 위한 1회 투자.

### 단기 Hotfix (인프라 완성 전 박스 분석 필요 시)

Step 1 (즉시, 1시간):
```python
# run_moco_phase2c4_box_sweep.py 수정
# 200 N·m → 24 N·m (suit_unit_diagnosis.md 옵션 1)
CONDITIONS = [
    ('B_noload',  0.0),
    ('B_suit6',   6.0),   # 50 N × 0.12
    ('B_suit12', 12.0),   # 100 N × 0.12
    ('B_suit18', 18.0),   # 150 N × 0.12
    ('B_suit24', 24.0),   # 200 N × 0.12
]
```

Step 2 (1일): ModOpAddResiduals(300, 50, 1.0) 교체 → pelvis_ty reserve 감소.  
Step 3 (1일): GRF 재계산 → 완전 정상화.

---

## 10. 인용

| 번호 | 문헌 | 우리 설계에서의 역할 |
|------|------|------------------|
| [1] | Dembia CL et al. (2020). OpenSim Moco. *PLoS Comput Biol* 16(12):e1008493. | MocoInverse 기본, reserve 가이드라인, ModOpAddResiduals |
| [2] | Falisse A et al. (2019). Algorithmic differentiation. *PLOS One* 14(10):e0217730. | SmoothSphereHalfSpaceForce 원천, 2D walking contact sphere 파라미터 |
| [3] | Hicks JL et al. (2015). Is my model good enough? *J Biomech Eng* 137(2):020905. | Reserve 허용 기준 (< 5% BW 번역, < 1% BW×ht 회전), RRA 절차 |
| [4] | John CT et al. (2022). Exoskeleton assistance symmetry. *Science Robotics* 7:eabf4699. | Wearable torque ExternalForce 적용, MocoInverse + ExternalLoads 패턴 |
| [5] | D'Hondt J et al. (2024). Predictive simulation of manual lifting. *J Biomech* (추정). | Box lifting MocoTrack + contact, hand force 적용 사례 |
| [6] | Anderson FC & Pandy MG (2001). Dynamic optimization of human walking. *J Biomech Eng* 123:381. | Reserve < 5-10% net joint moment 기준 |
| [7] | Pinheiro CF et al. (2023). Multi-task musculoskeletal simulation. (학술지 미확인) | Task module 패턴, 동일 base model 다중 작업 |
| [8] | De Leva P (1996). Adjustments to Zatsiorsky-Seluyanov's segment inertia. *J Biomech* 29(9):1223. | Forearm_v1 modification 근거 (손 19.2 cm) |
| [9] | van Dieen JH & Toussaint HM (1997). Stoop or squat. *Clin Biomech* 12(3):185. | 박스 motion biomech reference (발 고정, trunk angle) |
| [10] | OpenSim 4.5.2 번들 예제 (2023). exampleMocoInverse.py, example2DWalking.py. | ModOpAddResiduals/Reserves 분리 패턴, contact sphere 파라미터 실측 |

---

## 11. 현재 자산 목록 (인프라 구축 시작점)

### 모델 파일
```
/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/
  MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim  ← 박스 용 (최신)
  MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler.osim              ← Phase 1a 호환
  MaleFullBodyModel_v2.0_OS4_moco_stoop.osim                         ← Phase 1a 원본
```

### 검증된 스크립트 (재사용 가능 코드)
```
scripts/run_moco_phase1a_full.py        — prepare_model(), prepare_reference(), MocoInverse 설정
scripts/run_moco_phase1a_suit.py        — suit ExternalForce 패턴 (24 N·m 검증)
scripts/run_moco_phase2c4_box_sweep.py  — alpha_box() 함수, GRF+suit 합산 STO 패턴
scripts/remove_couplers.py              — 모델 수정 패턴
scripts/modify_forearm_geometry.py      — radius_hand_r offset 수정 패턴
```

### 검증된 수치 (변경 불가 기준값)
```
SUIT_FORCE_N = 200        → SUIT_TORQUE_NM = 24.0      [Phase 1a 검증]
MOMENT_ARM = 0.12 m                                      [Phase 1a 검증]
RESERVE_OPTF_PHASE1A = 10.0 Nm (현행, 분리 전)          [Phase 1a 기준]
Phase 1a suit effect: 28.0% @ 24 N·m                    [논문 수치]
Phase 1a slope: 1.164 %/Nm, R² = 1.000                 [논문 수치]
max ΔES (coupler 제거): 1.16 %p                          [regression PASS]
max ΔES (forearm v1):   1.23 %p                          [regression PASS]
```

---

_작성: opensim-agent (2026-04-29)_  
_검토 대상: CHEOL HOON님 architecture 검토 후 Step 2 (구현) 진행_  
_다음 단계: CHEOL HOON님 승인 → Step 2.1 suit_torque_module.py 구현부터_
