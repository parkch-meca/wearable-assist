# Suit Unit 진단 (2026-04-29)

## 1. CHEOL HOON님 SMA 슈트 실제 spec

- 수축력 200 N (좌/우 각 100 N)
- 모멘트 암 10-13 cm (중앙값 12 cm = 0.12 m)
- 결과 토크 200 N × 0.12 m = **24 N·m**
- Phase 1a 검증 조건 명칭: "L20" = 24 N·m

---

## 2. Phase 1a 코드 분석

**파일**: `run_moco_phase1a_suit.py`

- **Actuator 종류**: ExternalForce 쌍 (thoracic1 +Tz, pelvis -Tz)
- **계산 방식**:
  ```python
  MOMENT_ARM = 0.12           # line 34
  SUIT_FORCE_N = float(os.environ.get('SUIT_FORCE_N', '200'))   # line 36
  SUIT_TORQUE_PEAK = SUIT_FORCE_N * MOMENT_ARM                  # line 37
  # → SUIT_TORQUE_PEAK = 200 × 0.12 = 24.0 N·m
  ```
- **적용 컬럼**: `thor_T_z` (+Tz) / `pel_T_z` (-Tz) — 단위 N·m (OpenSim SI)
- **단위**: **N·m** (토크 직접 적용)
- **L20 실제 값**: SUIT_FORCE_N=200 N → SUIT_TORQUE_PEAK = **24.0 N·m**
- **docstring 명시**: `"T = 200 N × 0.12 m moment arm = 24 N·m peak"` (line 12)

**Phase 1a suit sweep** (`analyze_phase1a_suit_sweep.py`):
- 5 conditions: F = 0 / 50 / 100 / 150 / 200 N
- 각각 MOMENT_ARM=0.12 곱하여 T = 0 / 6 / 12 / 18 / 24 N·m 변환 후 적용
- Line 78: `torques = np.array([F * MOMENT_ARM for F in forces])`
- x축 레이블: "Suit torque (N·m)" — Phase 1a sweep의 50/100/150/200은 **N** 단위

---

## 3. Phase 2.C.4 코드 분석

### v1 sweep (`run_moco_phase2c4_box_sweep.py`)

```python
CONDITIONS = [
    ('B_noload',  0.0),
    ('B_suit50',  50.0),
    ('B_suit100', 100.0),
    ('B_suit200', 200.0),
]   # lines 74-79
```

- **B_suit200 = 200.0** 이 값이 `write_grf_suit_extloads()` 함수에 `suit_torque_nm` 인자로 전달됨
- 함수 내부: `Tz = suit_torque_nm * alpha_box(float(t))` (line 276)
- `thor_T_z`에 직접 `Tz` 기록 → OpenSim 해석 단위: **N·m**
- 변환 없음 — **200.0이 200 N·m로 직접 적용됨**
- 확인 로그: `f'--- Condition: {label}  suit={suit_torque_nm} N·m ---'` (line 360)

### v2 sweep (`run_moco_phase2c4_box_v2_sweep.py`)

```python
CONDITIONS = [
    ('B_noload',  0.0),
    ('B_suit50',  50.0),
    ('B_suit100', 100.0),
    ('B_suit200', 200.0),
]   # lines 54-59
```

- 동일 구조: `suit_torque_nm` → `thor_T_z` 직접 기록 (line 230)
- `f'phase2c4_box_v11b_v2_extloads  suit={suit_torque_nm}Nm\n'` (line 239)
- **B_suit200 = 200.0 N·m 직접 적용** (변환 없음)

### 분석 스크립트 레이블 (`analyze_phase2c4_box_v2.py`)

```python
COND_LABELS = {
    'B_noload':  'No suit (baseline)',
    'B_suit50':  'Suit 50 N·m',
    'B_suit100': 'Suit 100 N·m',
    'B_suit200': 'Suit 200 N·m',
}   # lines 63-68
```

- **"Suit 200 N·m"** — 레이블 자체도 N·m 단위로 표기
- 이 레이블이 코드 값 200.0 N·m를 정확하게 반영

### 렌더 스크립트 (`render_box_v11b_suit_comparison.py`)

- docstring: `"B_suit200 (Suit ON 200 N*m)"` (line 4)
- 타이틀 텍스트: `'SUIT ON  |  B_suit200  (200 N·m)'` (line 260)
- B_suit200 solution 경로: `/data/opensim_results/phase2c4_box_v11b/B_suit200/solution.sto`
  → v1 sweep 결과 사용

---

## 4. 단위 변환 추적

| 단계 | Phase 1a (검증됨) | Phase 2.C.4 |
|------|-----------------|-------------|
| 원자료 | 200 N 수축력 | 200 N·m (직접 입력값) |
| MOMENT_ARM 적용 | 200 N × 0.12 m = 24 N·m | 없음 |
| 코드 변수 | `SUIT_TORQUE_PEAK = 24.0` | `suit_torque_nm = 200.0` |
| OpenSim 적용값 | **24.0 N·m** | **200.0 N·m** |
| 실제 슈트 대비 배율 | 1× (정확) | 8.33× (과대) |

**핵심 차이**: Phase 1a는 `SUIT_FORCE_N × MOMENT_ARM` 변환을 거쳐 24 N·m 적용.
Phase 2.C.4는 숫자 50/100/200을 이미 N·m 값으로 직접 사용. 변환 없음.

---

## 5. 시나리오 판정

### **시나리오 A 확정 (200 N·m 직접 적용, 실제 슈트의 8.33배)**

코드 근거 (정량):

1. `CONDITIONS = [('B_suit200', 200.0)]` → 200.0이 `suit_torque_nm` (N·m 단위)로 전달
2. `Tz = suit_torque_nm * alpha_box(float(t))` → 200.0 × alpha = 최대 200.0 N·m 적용
3. Phase 1a 동일 경로: `SUIT_TORQUE_PEAK = SUIT_FORCE_N * MOMENT_ARM = 200 × 0.12 = 24.0 N·m`
4. Phase 2.C.4에서 `MOMENT_ARM` 변환 코드 없음 — 200이 N이 아니라 N·m 값

**영상 라벨 "200 N·m"**: 라벨이 정확. 실제로 200 N·m이 적용된 것이 맞음.
그러나 실제 SMA 슈트 spec(24 N·m)의 **8.33배** 과대 적용.

---

## 6. 핵심 코드 인용

### Phase 1a (정확, 24 N·m)
```python
# run_moco_phase1a_suit.py, lines 34-37
MOMENT_ARM = 0.12
SUIT_FORCE_N = float(os.environ.get('SUIT_FORCE_N', '200'))
SUIT_TORQUE_PEAK = SUIT_FORCE_N * MOMENT_ARM
# SUIT_TORQUE_PEAK = 24.0 N·m
```

### Phase 2.C.4 v1 (과대, 200 N·m)
```python
# run_moco_phase2c4_box_sweep.py, lines 74-79
CONDITIONS = [
    ('B_noload',  0.0),
    ('B_suit50',  50.0),    # 50.0 N·m (실슈트의 2.08배)
    ('B_suit100', 100.0),   # 100.0 N·m (실슈트의 4.17배)
    ('B_suit200', 200.0),   # 200.0 N·m (실슈트의 8.33배)
]
```

### Phase 2.C.4 v2 (과대, 동일 구조)
```python
# run_moco_phase2c4_box_v2_sweep.py, lines 54-59
CONDITIONS = [
    ('B_noload',  0.0),
    ('B_suit50',  50.0),
    ('B_suit100', 100.0),
    ('B_suit200', 200.0),
]
```

### torque 적용 공통 패턴 (v1/v2 모두)
```python
# write_grf_suit_extloads() 내부
Tz = suit_torque_nm * alpha_box(float(t))
suit[i, i_thor] = +Tz   # → thor_T_z에 N·m 단위로 기록
suit[i, i_pel]  = -Tz   # → pel_T_z에 N·m 단위로 기록
```

---

## 7. Phase 1a vs Phase 2.C.4 비교

| 항목 | Phase 1a (검증됨) | Phase 2.C.4 |
|------|-----------------|-------------|
| Actuator 종류 | ExternalForce 쌍 | ExternalForce 쌍 (동일) |
| 적용 body | thoracic1/pelvis | thoracic1/pelvis (동일) |
| 컬럼 | thor_T_z / pel_T_z | thor_T_z / pel_T_z (동일) |
| L20/B_suit200 값 | **24.0 N·m** | **200.0 N·m** |
| 같은 구조? | Y (동일 ExternalForce 방식) | |
| 같은 단위? | N·m (동일) | N·m (동일) |
| 같은 값? | **NO — 8.33배 차이** | |

구조와 단위 체계는 동일하나, 적용된 수치가 8.33배 다름.

---

## 8. 다음 단계 (사용자 협의용)

**시나리오 A 확정 — 재실행 필요**

Phase 2.C.4 B_suit50/100/200 결과는 실제 SMA 슈트의 2.1/4.2/8.3배 토크가 적용된 결과.
현재 B_suit200 결과에서 "ES 0% 또는 극단적 감소"가 나타났다면, 이는 실제 슈트로는
재현 불가능한 값임.

**옵션 1: Phase 1a와 일관된 조건으로 재실행 (권장)**
```
B_noload  : 0 N·m    (변경 없음)
B_suit24  : 24 N·m   (= L20, 200 N × 0.12 m — Phase 1a와 동일)
```
또는 sweep을 유지할 경우:
```
B_suit6   : 6 N·m    (= F50)
B_suit12  : 12 N·m   (= F100)
B_suit18  : 18 N·m   (= F150)
B_suit24  : 24 N·m   (= F200 = L20)
```

**옵션 2: 현재 결과를 "가상 고출력 슈트 시나리오"로 유지**
- 논문 Methods에 "50/100/200 N·m is hypothetical scenario exceeding SMA spec"으로 명시
- Phase 1a(24 N·m) 결과와 비교 그래프에 extrapolation으로 표현
- Limitations에 명시 필수

**옵션 1 권장 이유**: Phase 1a와의 일관성 유지 + 실제 슈트 spec 준수 + 논문 방어 가능성.
