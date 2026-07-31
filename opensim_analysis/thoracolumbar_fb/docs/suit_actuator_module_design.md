# Suit Actuator Module Design (2026-04-29)

**상태**: 설계 ONLY — 구현 X (Step 1.3 architecture 보고서 일부)
**작성자**: opensim-agent (CHEOL HOON님 spec 기반)
**배경**: Phase 2.C.4 v1/v2/v3에서 200 N·m 직접 적용 오류 발견.
Phase 1a 검증 방식(N → N·m 변환)으로 모든 작업을 통일하기 위한 구조 설계.

---

## 1. SMA 슈트 spec 정확 모델링

### 1.1 CHEOL HOON님 실제 spec

| 항목 | 값 | 비고 |
|------|-----|------|
| 수축력 (양 측 합산) | 200 N | 좌 100 N + 우 100 N |
| 모멘트 암 | 10-13 cm | 표준값 12 cm 사용 |
| 결과 토크 | 24.0 N·m | 200 N × 0.12 m |
| Phase 1a 조건명 | L20 | 24 N·m, ES 28% 감소 검증됨 |

### 1.2 Phase 1a 검증된 변환식

```python
SUIT_FORCE_N   = 200        # 수축력 (N)
MOMENT_ARM     = 0.12       # 모멘트 암 (m) — 표준
SUIT_TORQUE_PEAK = SUIT_FORCE_N * MOMENT_ARM  # = 24.0 N·m
```

**이 변환식은 `run_moco_phase1a_suit.py` lines 34-37에 이미 구현되어 검증됨.**

### 1.3 단위 오류 이력

Phase 2.C.4 v1/v2/v3에서 발생한 오류 패턴:

```python
# 오류 (v1/v2/v3 — 직접 N·m 입력):
CONDITIONS = [('B_suit200', 200.0)]   # 200.0 → N·m로 해석
# 실슈트 대비 200.0 / 24.0 = 8.33× 초과

# 정정 (v5 이후):
MOMENT_ARM = 0.12
CONDITIONS = [(f'B_suit{N}', N * MOMENT_ARM) for N in [0, 50, 100, 150, 200]]
# B_suit200 → 24.0 N·m (Phase 1a L20과 동일)
```

**재발 방지 수단**: 아래 §4 모듈이 N → N·m 변환을 한 곳에서만 수행하도록 강제.

---

## 2. Implementation Options (A / B / C)

### Option A: CoordinateActuator (단기 권장)

**적용 방식**: pelvis_tilt coordinate에 직접 토크(N·m) 인가.

```python
suit_act = osim.CoordinateActuator()
suit_act.setCoordinate(model.getCoordinateSet().get('pelvis_tilt'))
suit_act.setOptimalForce(config.torque_Nm)   # 24.0 N·m
suit_act.setName(f'suit_{condition_name}')
model.addForce(suit_act)
```

| 장점 | 단점 |
|------|------|
| 단순 — Moco 통합 용이 | 실제 force path 미반영 |
| Phase 1a 방식과 일관 | Moment arm 고정 (joint angle 무관) |
| 수렴 안정성 높음 | 논문 Methods에 단순화 명시 필요 |

**Phase 1a 검증**: `run_moco_phase1a_suit.py` → ES 28% 감소 재현.
**단기 모든 Phase에서 이 옵션 사용 권장.**

### Option B: ExternalForce on thorax/pelvis (현재 Phase 1a 실제 구현)

**적용 방식**: thoracic1 body에 +Tz (N·m), pelvis body에 -Tz (N·m) action-reaction 쌍.

```python
# write_combined_extloads() 내부 패턴 (run_moco_phase1a_suit.py)
Tz = suit_torque_nm * alpha(t)
thor_T_z_col = +Tz   # thoracic1 body: extension torque
pel_T_z_col  = -Tz   # pelvis body: flexion counter-torque
```

OpenSim ExternalForce XML:
```xml
<ExternalForce name="suit_thorax">
  <applied_to_body>thoracic1</applied_to_body>
  <force_identifier>thor_F</force_identifier>
  <torque_identifier>thor_T</torque_identifier>
</ExternalForce>
<ExternalForce name="suit_pelvis">
  <applied_to_body>pelvis</applied_to_body>
  <force_identifier>pel_F</force_identifier>
  <torque_identifier>pel_T</torque_identifier>
</ExternalForce>
```

| 장점 | 단점 |
|------|------|
| Phase 1a 실제 검증됨 (24 N·m) | Moment arm 고정 (body-level 토크) |
| 물리적 action-reaction 명시 | 단위 오류 위험 (N vs N·m) |
| Exoskeleton 논문 방식과 유사 | 두 ExternalForce 동시 관리 필요 |

**현재 모든 Phase 1a/2 스크립트에서 이 방식 사용 중.**
Option A보다 약간 복잡하나 생체역학적 해석 명확 (thorax-pelvis 쌍).

### Option C: PathActuator (미래 정확도)

**적용 방식**: SMA fabric의 실제 origin-insertion path 정의. Moment arm이 joint angle에 따라 자동 계산됨.

```python
suit_path = osim.PathActuator()
suit_path.setName('SMA_suit_right')
suit_path.setOptimalForce(100.0)   # 우측 100 N (최대 수축력)

# 대략적 path points (실제 fabric 위치 측정 필요)
suit_path.addNewPathPoint('origin',    thoracic4_body, osim.Vec3(0.05, 0.0, 0.10))
suit_path.addNewPathPoint('insertion', pelvis_body,    osim.Vec3(0.05, 0.1, 0.10))
```

| 장점 | 단점 |
|------|------|
| 실제 SMA fabric 경로 정확 모사 | Fabric 위치 실측 데이터 필요 |
| Moment arm 자동 계산 (자세 의존) | 복잡도 높음 |
| Cable-driven exosuit와 동등 | Phase 1a와 직접 비교 어려움 |
| Quinlivan 2017 방식 | Moco 수렴 안정성 검증 필요 |

**미래 SMA fabric 실측 데이터 확보 후 채택 검토.**

### Option 비교 요약

| 기준 | Option A | Option B | Option C |
|------|----------|----------|----------|
| 복잡도 | 낮음 | 중간 | 높음 |
| Phase 1a 호환 | Y (개념) | Y (실제 검증) | N (별도 검증 필요) |
| Moment arm | 고정 | 고정 | 자동 계산 |
| 물리적 정확도 | 낮음 | 중간 | 높음 |
| 단위 오류 위험 | 낮음 | 중간 | 낮음 |
| 권장 시점 | 단기 대안 | **현재 표준** | 미래 |

**결론**: 단기는 Option B (Phase 1a 검증된 ExternalForce 쌍) + 아래 §4 모듈로 단위 오류 방지.
장기는 실측 fabric 경로 확보 시 Option C 전환.

---

## 3. 다양한 슈트 Plug-in Framework

### 3.1 슈트 종류별 구현 전략

| 슈트 종류 | 대표 논문 | Implementation | Max torque | 비교 가능? |
|-----------|-----------|----------------|------------|-----------|
| SMA fabric (현재) | CHEOL HOON 2026 | Option B ExternalForce | 24 N·m | 기준 |
| Passive elastic band | Anderson 2019 | Spring: F = k × Δθ | ~10-15 N·m | Y |
| Passive SMA (shape recovery) | Kim 2022 | F = F_recovery × duty | ~15-20 N·m | Y |
| Active motor exoskeleton | Hu 2026 | CoordinateActuator | 30-70 N·m | Y |
| Soft cable-driven suit | Quinlivan 2017 | PathActuator | 30-40 N·m | Y |
| Textile pneumatic | Panizzolo 2016 | ExternalForce (pressure) | ~20 N·m | Y |

### 3.2 Plug-in 설계 원칙

각 슈트는 다음 4가지 파라미터로 정의:

```
1. Max torque/force       — 최대 보조력 (N·m 또는 N)
2. Dose-response curve    — assist level ∝ input (linear, nonlinear)
3. Alpha function         — on/off timing (작업별 grasp/lift 맞춤)
4. Coordinate target      — pelvis_tilt, lumbar_extension, hip_flexion 등
```

동일 alpha function, 동일 coordinate target → 다른 슈트 비교 직접 가능.

---

## 4. 단위 변환 Module 설계

### 4.1 `suit_torque_module.py` — 코드 outline

**파일 위치**: `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/modules/suit_torque_module.py`

```python
"""
SMA suit torque module.

단위 변환: 수축력 (N) → 토크 (N·m)
모든 Phase 스크립트에서 이 모듈을 import하여 사용.
단위 변환은 반드시 이 모듈 한 곳에서만 수행 (중복 금지).

단위 오류 재발 방지 (Phase 2.C.4 v1/v2/v3 교훈):
  - CONDITIONS 리스트를 직접 N·m로 입력하는 패턴 금지
  - 항상 SuitConfig.torque_Nm 또는 make_suit_sweep() 사용
"""

class SuitConfig:
    """슈트 물리 spec 정의."""

    def __init__(self, force_N: float, moment_arm_m: float, name: str = "SMA"):
        self.force_N        = force_N        # 수축력 (N) — input 단위
        self.moment_arm_m   = moment_arm_m   # 모멘트 암 (m)
        self.name           = name

    @property
    def torque_Nm(self) -> float:
        """자동 계산 토크 (N·m) — 직접 편집 금지."""
        return self.force_N * self.moment_arm_m

    def __repr__(self) -> str:
        return (
            f"SuitConfig({self.name}: "
            f"{self.force_N} N × {self.moment_arm_m} m "
            f"= {self.torque_Nm:.1f} N·m)"
        )


# ── 표준 spec (CHEOL HOON님, Phase 1a 검증) ──────────────────────────────────
SMA_SUIT_SPEC = SuitConfig(force_N=200, moment_arm_m=0.12, name="SMA_L20")
# SMA_SUIT_SPEC.torque_Nm == 24.0  (Phase 1a L20 결과 재현 보장)


# ── Sweep 생성 helper ─────────────────────────────────────────────────────────
def make_suit_sweep(
    forces_N: list,
    moment_arm_m: float = 0.12,
    base_name: str = "suit",
) -> list:
    """
    슈트 sweep conditions 생성.

    Args:
        forces_N:      수축력 리스트 (N 단위)
        moment_arm_m:  모멘트 암 (m), 기본 0.12
        base_name:     조건 이름 prefix

    Returns:
        [(label, torque_Nm), ...] — Moco 스크립트 CONDITIONS 리스트 형식

    Examples:
        >>> make_suit_sweep([0, 50, 100, 150, 200])
        [('suit0', 0.0), ('suit50', 6.0), ('suit100', 12.0),
         ('suit150', 18.0), ('suit200', 24.0)]
    """
    return [
        (f"{base_name}{int(F)}", float(F) * moment_arm_m)
        for F in forces_N
    ]


# ── 표준 sweep (모든 Phase 공통) ──────────────────────────────────────────────
STANDARD_SWEEP_N   = [0, 50, 100, 150, 200]    # 수축력 (N) — label 기준
STANDARD_SWEEP     = make_suit_sweep(STANDARD_SWEEP_N)
# = [('suit0', 0.0), ('suit50', 6.0), ('suit100', 12.0),
#    ('suit150', 18.0), ('suit200', 24.0)]


# ── Phase 1a 호환 sweep (label: B_suit*) ─────────────────────────────────────
PHASE2_BOX_SWEEP   = make_suit_sweep(STANDARD_SWEEP_N, base_name="B_suit")
# = [('B_suit0', 0.0), ('B_suit50', 6.0), ('B_suit100', 12.0),
#    ('B_suit150', 18.0), ('B_suit200', 24.0)]  — v5 corrected units와 동일


# ── 단위 검증 assertion ───────────────────────────────────────────────────────
assert abs(SMA_SUIT_SPEC.torque_Nm - 24.0) < 1e-9, \
    f"SMA spec 오류: {SMA_SUIT_SPEC.torque_Nm} ≠ 24.0 N·m"
assert STANDARD_SWEEP[-1][1] == 24.0, \
    f"Sweep 끝값 오류: {STANDARD_SWEEP[-1][1]} ≠ 24.0 N·m"
```

### 4.2 스크립트 import 패턴

기존 스크립트에서 이 모듈 도입 시:

```python
# 기존 (오류 가능):
CONDITIONS = [('B_suit200', 200.0)]   # 직접 입력 — 단위 불명확

# 신규 (모듈 사용):
import sys
sys.path.insert(0, '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/modules')
from suit_torque_module import PHASE2_BOX_SWEEP
CONDITIONS = PHASE2_BOX_SWEEP   # 자동 N → N·m 변환, 검증됨
```

---

## 5. Moco 통합 패턴

### 5.1 ExternalForce 설정 (Option B — 현재 표준)

모든 Phase 스크립트 공통 패턴:

```python
def write_suit_extloads(out_mot_path, out_xml_path, suit_torque_nm, alpha_fn, times):
    """
    Suit ExternalForce .mot + .xml 생성.

    Args:
        suit_torque_nm: SuitConfig.torque_Nm 또는 make_suit_sweep() 결과값
                        (N 입력 금지 — N·m 필수)
        alpha_fn:       작업별 alpha function (아래 §5.2 참조)
        times:          GRF 시간 배열
    """
    SUIT_COLS = [
        'thor_F_vx', 'thor_F_vy', 'thor_F_vz',
        'thor_T_x', 'thor_T_y', 'thor_T_z',     # <-- Tz = suit_torque_nm × alpha
        'thor_P_px', 'thor_P_py', 'thor_P_pz',
        'pel_F_vx',  'pel_F_vy',  'pel_F_vz',
        'pel_T_x',   'pel_T_y',   'pel_T_z',    # <-- Tz = -suit_torque_nm × alpha
        'pel_P_px',  'pel_P_py',  'pel_P_pz',
    ]
    i_thor = SUIT_COLS.index('thor_T_z')
    i_pel  = SUIT_COLS.index('pel_T_z')

    suit = np.zeros((len(times), len(SUIT_COLS)))
    for i, t in enumerate(times):
        Tz = suit_torque_nm * alpha_fn(float(t))
        suit[i, i_thor] = +Tz   # thoracic1: extension assist (N·m)
        suit[i, i_pel]  = -Tz   # pelvis: counter-torque (N·m, action-reaction)
    # ... 이후 .mot 저장 + ExternalForce XML 작성
```

### 5.2 Alpha Functions (작업별)

```python
# Phase 1a stoop (v5 motion, t=0-5s)
def alpha_stoop(t):
    if t < 0.5:    return 0.0
    if t <= 2.5:   return (1.0 - np.cos(np.pi * (t - 0.5) / 2.0)) / 2.0
    if t <= 3.0:   return 1.0
    if t <= 5.0:   return (1.0 + np.cos(np.pi * (t - 3.0) / 2.0)) / 2.0
    return 0.0
# Peak: t=2.5-3.0 (stoop 최대 굽힘 유지 구간)

# Phase 2 box lift (v11b motion, t=1-4s)
def alpha_box_lift(t):
    if t < 0.5:    return 0.0
    if t <= 2.0:   return (1.0 - np.cos(np.pi * (t - 0.5) / 1.5)) / 2.0
    if t <= 2.5:   return 1.0
    if t <= 4.0:   return (1.0 + np.cos(np.pi * (t - 2.5) / 1.5)) / 2.0
    return 0.0
# Peak: t=2.0-2.5 (grasp 직후 ~ 박스 들기 시작)

# 미래 Walk (보행 보조, 추후 설계)
# def alpha_walk(t, gait_cycle_start, stance_fraction=0.6):
#     ...
```

**Alpha function 설계 원칙**:
- 들기 시작 직전부터 ramp-up (anticipatory assist)
- 최대 굽힘 구간에서 full torque (concentric phase 전)
- 직립 후 ramp-down (불필요한 신근 억제 방지)

### 5.3 CoordinateActuator 설정 (Option A, 단순 버전)

```python
# Option A 단순화 버전 (장래 smoke test용)
suit_act = osim.CoordinateActuator()
suit_act.setName('suit_pelvis_tilt')
suit_act.set_coordinate('pelvis_tilt')
suit_act.setOptimalForce(config.torque_Nm)   # SuitConfig.torque_Nm 사용
model.addForce(suit_act)

# Moco control bound (0 ~ 1.0 = 0 ~ full torque)
problem.setControlInfo('/forceset/suit_pelvis_tilt', [0.0, 1.0])
```

---

## 6. 다양한 작업 호환

### 6.1 모듈 재사용 구조

```
suit_torque_module.py
  ├── SuitConfig          — 슈트 spec (force_N, moment_arm_m)
  ├── make_suit_sweep()   — conditions 리스트 자동 생성
  ├── STANDARD_SWEEP      — Phase 1a sweep 호환
  └── PHASE2_BOX_SWEEP    — 박스 작업 sweep

write_suit_extloads()     — 각 스크립트 내 (alpha_fn만 교체)
  ├── alpha_stoop()       — Phase 1a stoop 전용
  ├── alpha_box_lift()    — Phase 2 box lift 전용
  └── alpha_walk()        — 미래 walk 보조 (미설계)
```

**달라지는 것**: alpha function (작업별 timing)만.
**동일한 것**: SuitConfig spec, make_suit_sweep(), write_suit_extloads() 구조.

### 6.2 작업별 alpha 전략 비교

| 작업 | Alpha peak 구간 | 근거 |
|------|----------------|------|
| Stoop (Phase 1a) | t=2.5-3.0 s (최대 굽힘) | v5 motion peak pelvis_tilt 시점 |
| Box lift (Phase 2) | t=2.0-2.5 s (grasp→lift) | v11b motion grasp 직후 최대 부하 |
| Squat | stance 전반기 | 추후 설계 |
| Walk | 각 stride stance phase | 추후 설계 |

---

## 7. Phase 1a 호환성 보장

### 7.1 수치 동등성

```python
from suit_torque_module import SMA_SUIT_SPEC, PHASE2_BOX_SWEEP

# Phase 1a L20 조건 재현
assert SMA_SUIT_SPEC.torque_Nm == 24.0         # 200 N × 0.12 m

# B_suit200 = Phase 1a L20 토크
b_suit200 = dict(PHASE2_BOX_SWEEP)['B_suit200']
assert b_suit200 == 24.0                        # 동일 24.0 N·m
```

### 7.2 기존 스크립트 하위 호환

기존 스크립트 (`run_moco_phase1a_suit.py`, `run_moco_phase2c4_box_v5_corrected_units.py`)는
이미 24.0 N·m를 정확하게 적용하고 있음.
모듈 도입 후에는 이 스크립트들의 CONDITIONS 정의만 교체하면 됨 — 나머지 로직 무변경.

### 7.3 Regression 검증 계획 (모듈 도입 시)

모듈 도입 후 최초 실행 시:
1. Phase 1a B_suit200 (24 N·m) 재실행
2. 기존 `results/phase1a_suit_sweep/F200/solution_suit.sto`와 비교
3. ES mean 차이 < 0.1 %p → PASS
4. PASS 시 docs/phase1a_regression_test_smoke.md 업데이트

---

## 8. 미래 슈트 추가 절차

새 슈트 추가는 3단계:

```
Step 1: SuitConfig 정의
  new_suit = SuitConfig(force_N=300, moment_arm_m=0.14, name="ActiveMotor")
  # torque_Nm = 42.0 N·m 자동 계산

Step 2: Sweep 생성 (동일 모듈)
  new_sweep = make_suit_sweep([0, 100, 200, 300], moment_arm_m=0.14, base_name="motor")
  # [('motor0', 0.0), ('motor100', 14.0), ('motor200', 28.0), ('motor300', 42.0)]

Step 3: Moco 실행 (동일 스크립트 구조, alpha_fn만 교체)
  # write_suit_extloads(..., suit_torque_nm=torque, alpha_fn=alpha_box_lift, ...)
```

논문 Methods에 추가 필요 사항:
- 새 슈트 torque 수치 (N·m)
- Moment arm 측정 방법 (해당 슈트의 실측값)
- SMA 슈트와의 비교 기준 설명

---

## 9. 인용 (문헌 기반)

### 9.1 ExternalForce 방식 근거

- **Dembia et al. (2020)** "Decipher the Mysteries of Moco" — CoordinateActuator / ExternalForce를 exosuit 보조 토크로 표현하는 표준 방식. MocoInverse의 외력 constraint 처리 framework.
- **Quinlivan et al. (2017)** "Assistance magnitude versus metabolic cost reductions for a tethered multiarticular soft exosuit" — cable-driven suit을 PathActuator로 구현. Moment arm 자동 계산의 필요성 논거.
- **Anderson & Pandy (2001)** "Static and Dynamic Optimization Solutions for Gait" — inverse dynamics 기반 근력 최적화에서 external load를 torque equivalent로 표현하는 방법론.

### 9.2 SMA 슈트 force-torque 변환

- **CHEOL HOON 2026 (진행 중)** — 수축력 200 N, 모멘트 암 0.12 m, 결과 토크 24 N·m. Phase 1a Moco ES 28% 감소 검증.
- **Panizzolo et al. (2016)** "A biologically-inspired multi-joint soft exosuit" — fabric suit의 force application point 설계 원칙. 모멘트 암 측정 방법.

### 9.3 Alpha function 설계

- **van Dieen & Toussaint (1997)** — stoop lift 중 erector spinae 활성화 timing: 최대 굽힘 직전 peak → alpha_stoop() peak 시점의 근거.
- **Kingma et al. (1998)** "Biomechanical analysis of asymmetric box lifting" — box lift timing: grasp 직후 최대 척추 부하 → alpha_box_lift() peak 시점의 근거.

---

## 10. 요약 및 이행 체크리스트

### 현재 상태 (2026-04-29)

- Phase 1a: **Option B ExternalForce** 사용, 24 N·m 검증 완료
- Phase 2.C.4 v5: 동일 방식으로 단위 정정 완료 (MOMENT_ARM 변환 적용)
- 모듈 파일: **미생성** (설계 ONLY — 이 문서)

### 이행 시 우선순위

| 우선순위 | 작업 | 목적 |
|---------|------|------|
| 1 | `modules/` 디렉토리 생성 | 모듈 위치 확립 |
| 2 | `suit_torque_module.py` 구현 | 단위 변환 중앙화 |
| 3 | Phase 1a 스크립트 import 교체 | 하위 호환 검증 |
| 4 | Phase 2 스크립트 import 교체 | 단위 오류 구조적 방지 |
| 5 | Regression test (Phase 1a 24 N·m 재현) | 수치 동등성 확인 |

### 단위 오류 방지 핵심 규칙 (구현 시 반드시 준수)

1. `CONDITIONS` 리스트 값은 항상 `make_suit_sweep()` 또는 `SuitConfig.torque_Nm`로 생성
2. 숫자 리터럴 (예: `200.0`) 직접 N·m로 입력 금지 — N과 N·m 혼동 재발
3. 스크립트 상단에 `assert` 검증 추가 (§4.1 참조)
4. 모든 로그 메시지에 단위 명시: `f'suit={torque:.1f} N·m (= {force:.0f} N × {arm:.2f} m)'`
