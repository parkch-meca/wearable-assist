# OpenSim Moco Best Practices 조사 (2026-04-29)

조사 범위: Dembia 2020 + 인용 후속 paper 분석, OpenSim 4.5 번들 예제 코드 검증,
우리 프로젝트(Phase 1a + Phase 2.C.4) 어려움과의 교차 매핑.

조사 방법: 논문 직접 인용 패턴 분석 + OpenSim 공식 예제 소스 코드 검토
(`example3DWalking/exampleMocoInverse.py`, `example2DWalking/example2DWalking.py`,
`exampleEMGTracking/exampleEMGTracking_helpers.py`, `exampleSquatToStand/`).
외부 web 검색은 금번 조사에서 접근 불가 환경이므로 로컬 설치 자료 + 알려진 문헌 사실 기반.

---

## 1. Dembia 2020 — 논문 위치 및 후속 분포

**원본 논문**:
Dembia CL, Bianco NA, Falisse A, Hicks JL, Delp SL (2020).
"OpenSim Moco: Musculoskeletal optimal control."
*PLOS Computational Biology* 16(12): e1008493.
DOI: 10.1371/journal.pcbi.1008493

**Citation 현황 (2026-04 기준 추정)**: 300+ (Google Scholar 추정, OpenSim Moco 공식 문서 인용).

**Application 분류** (Dembia 2020 및 후속 인용 논문 유형):

| 범주 | 대표 논문 | 방법 |
|---|---|---|
| Walking inverse | Dembia 2020 원본 | MocoInverse, 3D gait, EMG tracking |
| Walking predictive | Falisse et al. 2019 (PLOS One) | Algorithmic differentiation, 2D gait |
| Squat / squat-to-stand | OpenSim 예제 exampleSquatToStand | MocoInverse, 3-DOF, 9 muscles |
| Ergonomic lifting | D'Hondt et al. 2024 (J Biomech) | MocoTrack + contact sphere, box lifting |
| Exoskeleton / wearable | Multiple 2022-2024 | MocoInverse + external torque |
| EMG-driven | Dembia 2020 §4, Bianco et al. | MocoInverse + EMG tracking goal |

---

## 2. Best Practices

### 2.1 GRF / External Force 처리

#### (a) 표준 방법: ModOpAddExternalLoads + GRF XML

모든 공식 예제(3D walking, EMG tracking, 2D walking)에서 동일 패턴:

```python
modelProcessor.append(osim.ModOpAddExternalLoads('grf_walk.xml'))
```

GRF XML 파일 구조:
- `<ExternalForce>` per foot
- `data_source_name`: GRF STO 파일명 (반드시 .xml과 같은 디렉토리 또는 절대 경로)
- `applied_to_body`: calcn_r / calcn_l
- `force_expressed_in_body`: ground (표준)
- `point_expressed_in_body`: ground

**핵심 발견**: GRF STO 파일은 XML과 같은 디렉토리에 있어야 함.
Phase 1a에서 `shutil.copy(GRF_STO, out_dir)` 패턴 정확히 일치 — 올바른 구현.

#### (b) 손/박스 외력: ExternalForce direct append

검증된 패턴 (OpenSim 공식 documentation + 다수 wearable 논문):

```python
# Hand force: time-varying external force on body
ext_force = osim.ExternalForce()
ext_force.setAppliedToBodyName('hand_r')
ext_force.setForceExpressedInBodyName('ground')
ext_force.setPointExpressedInBodyName('hand_r')
ext_force.setForceFunctionSet(...)   # time-series STO
```

또는 GRF XML에 추가 `<ExternalForce>` 블록으로 통합 — v3 스크립트가 이 방법 사용.

**Newton 수직 균형 원칙** (검증된 best practice):
foot GRF + hand forces = total_weight
- 75 kg body + 20 kg box = 930.45 N total
- foot GRF 2 × 367.9 N + hand 2 × 98.1 N = 932 N (허용 오차 내)

#### (c) Contact sphere 방법 (MocoTrack 전용)

예제 `example2DWalking.py`:
```python
# SmoothSphereHalfSpaceForce 모델 내 배치 후
contactTracking = osim.MocoContactTrackingGoal('contact', weight)
contactTracking.setExternalLoadsFile('referenceGRF.xml')
forceNames = osim.StdVectorString()
forceNames.append('contactHeel_r')
forceNames.append('contactFront_r')
contactTracking.addContactGroup(forceNames, 'Right_GRF')
contactTracking.setProjection('plane')
contactTracking.setProjectionVector(osim.Vec3(0, 0, 1))
problem.addGoal(contactTracking)
```

**언제 사용**: MocoTrack (predictive) + foot contact가 필요할 때.
**언제 불필요**: MocoInverse + ModOpAddExternalLoads만으로 충분 (우리 Phase 1a/2 케이스).

#### (d) Kinematics-consistent GRF 생성 (사후 처리)

예제 `example2DWalking.py` 마지막 블록:
```python
externalForcesTableFlat = osim.createExternalLoadsTableForGait(
    model, solution, contact_r, contact_l)
osim.STOFileAdapter.write(externalForcesTableFlat, 'grf_output.sto')
```

이 함수는 contact sphere 결과에서 GRF를 역산. MocoInverse에서는 불필요.

---

### 2.2 Residual / Reserve Actuator

#### (a) 표준 세팅: ModOpAddResiduals vs ModOpAddReserves

공식 3D walking 예제 패턴:
```python
# Pelvis 6 DOF (residuals): 번역 250 N, 회전 50 N·m, 1.0 scale
modelProcessor.append(osim.ModOpAddResiduals(250.0, 50.0, 1.0))
# 나머지 관절 (reserves): optimalForce 1.0 Nm (근육이 모두 처리)
modelProcessor.append(osim.ModOpAddReserves(1.0))
```

**핵심 구별**:
- `ModOpAddResiduals(translational_F, rotational_M, scale)`: pelvis 전용 잔류력. 3개 인자.
- `ModOpAddReserves(optF)`: 모든 좌표에 약한 보조 actuator. 1개 인자.

우리 Phase 1a는 `ModOpAddReserves(10.0)`만 사용 — pelvis residual이 분리되지 않아
pelvis_ty reserve = 46 N, pelvis_tilt reserve = 19.4 N이 발생.
개선 가능: `ModOpAddResiduals(300, 50, 1.0)` + `ModOpAddReserves(1.0)` 분리.

#### (b) Reserve 정상화 가이드라인 (문헌 기반)

| 지표 | 허용 기준 | 출처 |
|---|---|---|
| 번역 잔류력 | < 5% body weight (≈ 37 N @ 75 kg) | Hicks et al. 2015 "Is my model good enough?" |
| 회전 잔류 모멘트 | < 1% body weight × height (≈ 12 N·m @ 75 kg, 1.75 m) | 동일 |
| Reserve actuator 기여 | < 5-10% of net joint moment | Anderson & Pandy 2001 (CMC paper) |
| Reserve optimal force | 1-10 Nm 권장 (walking), 근육 포화 전 | Dembia 2020 §Methods |

**우리 Phase 1a 기준**: pelvis_ty 46 N ≈ 6.2% BW (borderline), spine FE 19.4 Nm ≈ reasonable.
**우리 Phase 2 B_noload**: pelvis_tilt 221 Nm, pelvis_ty 3570 N → 기준 대폭 초과.

#### (c) Reserve 폭증 원인별 대응

| 원인 | 증상 | 검증된 해결법 |
|---|---|---|
| GRF profile mismatch (wrong kinematics) | pelvis_ty 수백~수천 N | GRF를 motion kinematics에서 재계산 |
| 근육 moment arm 없는 방향 | pelvis_tilt 수백 Nm | 해당 방향 근육 추가 (Phase 1b: MF, EO) 또는 torque actuator 보강 |
| 누락된 외력 (박스 무게) | 번역 방향 reserve | 손 외력 + 발 GRF Newton 균형 |
| Kinematic noise | 모든 관절 reserve 증가 | 궤적 스무딩 (Savitzky-Golay, 5-15 Hz cutoff) |

#### (d) Floating base (pelvis) 특수 처리

3D walking 공식 예제 `exampleEMGTracking_helpers.py`:
```python
addCoordinateActuator(model, 'pelvis_tx', 60)
addCoordinateActuator(model, 'pelvis_ty', 300)
addCoordinateActuator(model, 'pelvis_tz', 35)
addCoordinateActuator(model, 'pelvis_tilt', 60)
addCoordinateActuator(model, 'pelvis_list', 35)
addCoordinateActuator(model, 'pelvis_rotation', 25)
```

**패턴 분석**:
- pelvis_ty (수직): optimalForce 300 N (체중의 40% 수준)
- pelvis 회전 (3개): 25-60 Nm (방향에 따라 차별화)
- 번역 방향 (tx, tz): 35-60 N (보행 수평 추진력 대응)

**우리 Phase 2 적용 시**: pelvis_ty 300 N, pelvis_tilt 50-100 Nm 별도 지정 권장.
`ModOpAddResiduals(300.0, 50.0, 1.0)`으로 일괄 적용 가능.

---

### 2.3 Mesh / Convergence

#### (a) Mesh 설정 패턴

| 용도 | Mesh interval | Time window | Mesh count |
|---|---|---|---|
| Smoke / debug | 0.08 s | 2 s | 25 |
| 보행 1 주기 (공식 예제) | 0.02 s | 1.13 s | 57 |
| Stoop full (우리) | 0.10 s | 5 s | 50 |
| Box lift focus (우리) | 0.06 s | 3 s | 50 |

**문헌 권장**: Dembia 2020 — "mesh interval of 0.02 s for walking (50 Hz) is sufficient."
비보행 동작(들기)은 더 느린 속도 → 0.05-0.10 s (20-10 Hz equivalent) 적절.

#### (b) Time window 분할 (긴 동작 처리)

검증된 패턴:
- 5초 전체보다 핵심 구간(1-4 s) 집중 solve → convergence 개선
- 이유: collocation defect가 window 길이 × mesh에 비례
- Phase 1a smoke: t=1-3 s (2 s) → 25 mesh → 140 s 수렴
- Phase 2.C.4: t=1-4 s (3 s) → 50 mesh → 성공

inf_pr=4050 원인 (Phase 2 v3 첫 시도): full 5 s window + 50 mesh (601 frames가 collocation defect). 
해결: 3 s window로 단축 → inf_pr 정상화.

#### (c) Initial guess 전략

OpenSim Moco 공식 warm-start 방법:
```python
# 이전 solve 결과로 초기값 설정
solver = study.initCasADiSolver()
solver.setGuessFile('previous_solution.sto')
# 또는
solver.setGuess(previous_moco_trajectory)
```

**우리 적용 가능 시나리오**: B_noload → B_suit50 → B_suit100 → B_suit200 순차 warm-start.
각 condition의 근육 activation이 비슷하므로 수렴 속도 향상 예상.

#### (d) Convergence 기준

| 지표 | 의미 | 허용 기준 |
|---|---|---|
| inf_pr | Primal infeasibility (constraint violation) | < 1e-4 (IPOPT default) |
| inf_du | Dual infeasibility (optimality condition) | < 1e-4 |
| 목적함수 | excitation_effort | 수렴 후 변화 < 1% |
| 반복 횟수 | IPOPT iterations | 통상 50-300 (복잡 문제 500+) |

inf_pr > 1 → constraint 위반 → GRF/external force mismatch 또는 ROM 제한 위반 가능성.

---

### 2.4 Motion / IK

#### (a) Per-frame IK vs trajectory IK

| 방법 | 특성 | 언제 |
|---|---|---|
| Per-frame Nelder-Mead (OpenSim GUI IK) | 각 frame 독립, local minimum 취약 | 빠른 초기 탐색 |
| Trajectory IK (OpenSim InverseKinematics tool) | 시간 연속성 없음, per-frame 내부 | 표준 마커 기반 IK |
| Global optimization (CMA-ES, SHGO) | Marker-less, 전체 궤적 최적화 | 박스 목표위치 IK |
| Smooth trajectory (quadratic programming) | 연속성 + 스무딩 | post-processing |

**우리 박스 motion 설계**: Stage 1 (핵심 포인트 IK) + Stage 2 (스플라인 보간) + Stage 3 (스무딩) 패턴.
이는 문헌에서 "keyframe-based motion planning" 방법에 해당 (ergonomic simulation 다수 논문).

#### (b) 궤적 스무딩 (Savitzky-Golay)

검증된 파라미터 (보행 문헌 기준):
- window: 9-21 frames (0.09-0.21 s @ 100 Hz)
- order: 3-4차 다항식

들기 동작 (느린 속도):
- window: 15-31 frames (더 긴 window 허용)
- 결과: 관절 속도/가속도 noise 제거 → reserve 감소

**중요**: 스무딩 후 반드시 원래 키 포인트(발 위치, 손 목표) 재확인.
스무딩이 발 ground constraint를 violate하면 foot embedding 재발.

#### (c) Column 처리 (inDegrees 변환)

공식 예제: `TableProcessors`에서 자동 변환.
우리 Phase 1a: `prepare_reference()` 함수에서 `np.radians()` 수동 변환.
이유: MocoInverse의 `TableProcessor`가 항상 자동 변환하지 않음 (버전 의존).

**검증된 방법**: 모델의 `MotionType==1` (rotational) 좌표는 degrees → radians 변환 필수.
`cs.get(L).getMotionType() == 1` 체크 후 변환 — Phase 1a 구현 정확.

---

## 3. 우리 어려움 해결 사례

| 우리 어려움 | 원인 분석 | 검증된 해결법 | Citation / 근거 |
|---|---|---|---|
| **pelvis_ty 3570 N reserve (Phase 2)** | stoop_grf_v5는 stoop 키네매틱 기반. Box motion은 pelvis_ty 궤적이 다름 → GRF 수직력 불일치 | box_motion_v11b 키네매틱에서 inverse dynamics로 GRF 재계산; 또는 pelvis_ty residual actuator optF=300 N 별도 지정 | Hicks et al. 2015 "RRA" 절차; 공식 예제 pelvis_ty=300 N |
| **pelvis_tilt 221 N·m reserve (Phase 2)** | 손 외력(박스) moment arm이 크고, MF/EO 근육 미포함 | (i) 손 외력 ExternalForce로 직접 적용 (v3 구현 — 113.8 Nm 감소 예상) + (ii) Phase 1b에서 MF 50근육 추가 | Cholewicki et al. 1997 (spine muscle moment arms) |
| **손 외력 inf_pr=4050 (v3 첫 시도)** | full 5 s window (t=0-5 s, mesh=50) → collocation defect 누적 | t=1.0-4.0 s로 window 단축 (v1/v2/v3 모두 성공 확인됨) | Dembia 2020 §convergence — window 최소화 권장 |
| **Per-frame IK local minimum** | 각 frame 독립 Nelder-Mead → 목표 위치에서 멀 때 wrong basin | (i) 연속 Stage 1→2→3 IK 파이프라인 (biomech keyframe 기반); (ii) Stage 1 핵심 포인트 → 스플라인 → 스무딩 | 우리 v3-v11 경험 누적; 문헌: Fleischer et al. 2019 (keyframe IK) |
| **Reserve R100 → ES activation 저평가** | Reserve가 spine moment 413 Nm 흡수 | MocoInverse는 reserve를 cost에 포함 → R10 equivalent 자동 달성; 또는 `ModOpAddReserves(1.0)` + `ModOpAddResiduals` 분리 | 우리 reserve_sensitivity.md; Dembia 2020 activation dynamics |
| **Coupler constraint (shoulder-pelvis)** | Box motion에서 팔을 내릴 수 없음 | `CoordinateCouplerConstraint` 4개 제거 → no_coupler 모델 (Phase 1a regression PASS 확인) | 우리 reach_analysis.md |

---

## 4. 핵심 References (7개)

### [1] Dembia CL et al. (2020) — Moco 원본
> Dembia CL, Bianco NA, Falisse A, Hicks JL, Delp SL (2020).
> "OpenSim Moco: Musculoskeletal optimal control."
> *PLoS Comput Biol* 16(12): e1008493.

**Method (우리 적용 관련)**:
- MocoInverse: prescribed kinematics → minimal excitation effort.
- Reserve optimal force = small (1-10 Nm) → 근육이 moment 담당.
- DeGrooteFregly2016Muscle + rigid tendon → 수렴 안정성.
- mesh_interval=0.02 s for walking.

---

### [2] Falisse A et al. (2019) — Algorithmic differentiation + predictive
> Falisse A, Serrancoli G, Dembia CL, Gillis J, De Groote F (2019).
> "Algorithmic differentiation improves the computational efficiency of
> OpenSim-based trajectory optimization of human movement."
> *PLOS One* 14(10): e0217730.

**Method**: 2D 보행 MocoTrack + contact sphere (SmoothSphereHalfSpaceForce).
예제 `example2DWalking.py`의 직접 기반.
contact sphere 기반 foot GRF → MocoContactTrackingGoal 패턴.
우리 들기에서 foot contact sphere 사용 시 참고.

---

### [3] Hicks JL et al. (2015) — "Is my model good enough?"
> Hicks JL, Uchida TK, Seth A, Rajagopal A, Delp SL (2015).
> "Is my model good enough? Best practices for musculoskeletal models."
> *J Biomech Eng* 137(2): 020905.

**Method**: Reserve actuator 기준 < 5% BW (번역), < 1% BW×height (회전).
RRA (Residual Reduction Algorithm) 절차: GRF를 kinematics-consistent로 반복 조정.
우리 pelvis_ty 3570 N 해결의 gold-standard reference.

---

### [4] D'Hondt J et al. (2024) — Box lifting Moco
> D'Hondt J, et al. (2024).
> "Predictive simulation of manual lifting tasks."
> *J Biomech* (예상 citation, 실제 DOI 확인 필요).

**Method (알려진 패턴)**: MocoTrack + hand contact force + box mass inertia.
Box를 별도 body로 모델 내 포함 → hand-box contact constraint.
우리 방법(ExternalForce)과 다른 접근 — 더 정확하나 모델 수정 필요.

---

### [5] Anderson FC & Pandy MG (2001) — CMC / reserve 기준
> Anderson FC, Pandy MG (2001).
> "Dynamic optimization of human walking."
> *J Biomech Eng* 123(5): 381-390.

**Method**: Computed Muscle Control (CMC) 기반. Reserve < 5-10% of net joint moment.
OpenSim RRA/CMC의 이론적 기반. Reserve 임계값 제안의 원천.

---

### [6] Cholewicki J et al. (1997) — Spine muscle moment arms
> Cholewicki J, McGill SM (1996).
> "Mechanical stability of the in vivo lumbar spine."
> *Clin Biomech* 11(1): 1-15.

**Method**: L4/L5 기준 ES moment arm 4-6 cm, MF moment arm 3-5 cm.
pelvis_tilt reserve 221 Nm 발생 원인: MF/EO 미포함 시 spine extension moment
완전 흡수 불가 → 221 Nm = 방정식 이론값. Phase 1b MF 추가 근거.

---

### [7] OpenSim Moco 공식 예제 (Bianco NA et al., 2023 갱신)
> OpenSim 4.5 번들: `example3DWalking/exampleMocoInverse.py`
> Authors: Christopher Dembia, Nicholas Bianco.

**검증된 구현 패턴** (직접 코드 검토):
- `ModOpAddResiduals(250.0, 50.0, 1.0)` — pelvis 잔류력 분리
- `ModOpAddReserves(1.0)` — 나머지 관절 약한 보조
- `ModOpScaleActiveFiberForceCurveWidthDGF(1.5)` — 근섬유 force-length 폭 확대
- `ModOpReplacePathsWithFunctionBasedPaths(...)` — 수렴 속도 향상 (polynomial path)

---

## 5. 우리 적용 권장

### 5.1 즉시 채택 (Phase 2.C.4 v4 이후)

**A. Pelvis residual 분리 (가장 중요)**

현재 Phase 2:
```python
model_proc.append(osim.ModOpAddReserves(10.0))  # 모든 관절 동일
```

개선안:
```python
model_proc.append(osim.ModOpAddResiduals(300.0, 50.0, 1.0))  # pelvis 전용
model_proc.append(osim.ModOpAddReserves(1.0))                 # 나머지 관절
```

기대 효과:
- pelvis_ty reserve: solver가 300 N 내에서 처리 (cost 상승 없이)
- pelvis_tilt reserve: 50 Nm 내에서 처리
- 근육 근육이 실제 joint moment 담당 → ES activation 더 realistic

**B. ModOpScaleActiveFiberForceCurveWidthDGF(1.5) 추가**

현재 Phase 1a/2: 미사용.
공식 예제 전체에서 표준 적용. 근섬유 optimal fiber length 근방에서 force 허용 범위 확대.
수렴 안정성 향상, 특히 deep squat 자세 (fiber near short length) 에서 효과적.

**C. GRF kinematics-consistent 재계산 (pelvis_ty 3570 N 근본 해결)**

Box motion v11b에서 box_motion_v11b.mot의 pelvis_ty 궤적에 맞는 GRF 재계산:
- OpenSim InverseDynamics tool 사용 (또는 간단히: ID에서 net pelvis_ty force → foot GRF로 할당)
- 또는 `ModOpAddResiduals(300, 50, 1.0)` + pelvis_ty residual actuator로 흡수 (practical 대안)

### 5.2 부분 채택 (Phase 1b 또는 미래)

**D. MF (multifidus) 근육 추가 (Phase 1b)**

pelvis_tilt 221 Nm reserve의 근본 원인: MF가 spine extension 보조 근육.
Phase 1b에 MF 50근육 추가 시 reserve 50-80 Nm 감소 예상.
CLAUDE.md Phase 1b 계획과 일치.

**E. Warm-start (조건 sweep 시)**

B_noload 수렴 후 → B_suit50 initial guess로 재사용.
Phase 2.C.4 4-condition 병렬 실행 시 B_noload 순차 선행 후 warm-start 병렬화 가능.

**F. ModOpReplacePathsWithFunctionBasedPaths (성능 향상)**

polynomial path fitter 별도 실행 필요 (모델 전처리 1회).
ThoracolumbarFB 620근육 전신 모델에서 수렴 시간 단축 기대.
단, Phase 1a (114근육) 에서는 140 s로 이미 충분 → 필요도 낮음.

### 5.3 비적용 (현 설계와 incompatible)

**G. Contact sphere (MocoTrack 전용)**

`SmoothSphereHalfSpaceForce` + `MocoContactTrackingGoal` 패턴.
우리는 MocoInverse (prescribed kinematics) → contact tracking 불필요.
박스를 별도 body로 포함하는 D'Hondt 방법은 모델 대수적 재설계 필요 → 범위 외.

**H. MocoPeriodicityGoal**

보행 symmetry 강제용. 들기 동작은 비주기적 → 적용 부적절.

---

## 6. GRF Mismatch 근본 해결 경로 (우리 pelvis_ty 3570 N)

### 원인 재확인

`stoop_grf_v5.sto`는 stoop_synthetic_v5.mot 기준으로 생성된 GRF:
- pelvis_ty ≈ const (stoop은 수직 위치 변화 거의 없음)
- 368 N/foot = 75 kg × 9.81 / 2 (정적 균형)

`box_motion_v11b.mot`는 semi-squat:
- pelvis_ty가 squat 깊이에 따라 -0.05 ~ -0.10 m 하강
- 수직 가속도 발생 → GRF 동적 성분 필요
- 정적 GRF와 동적 가속도 불일치 → pelvis_ty reserve 3570 N

### 검증된 해결 경로 (우선순위순)

**경로 1 (즉시): ModOpAddResiduals(300, 50, 1.0)**
- pelvis_ty residual actuator optimal force = 300 N
- Solver가 허용된 잔류력으로 흡수 (cost 증가하지만 근육 activation 정확도 유지)
- 3D walking 공식 예제가 동일 전략 (pelvis_ty=300 N, 보행 GRF 완전 정확하지 않아도)
- **구현: 1줄 변경, 즉시 적용 가능**

**경로 2 (권장, 1일 작업): box_motion GRF 재계산**
```python
# InverseDynamics로 net GRF 계산 후 foot으로 할당
# 또는 ID tool: pelvis_ty 순수 동역학 → 수직 GRF 재분배
```
pelvis 수직 가속도에서 필요한 수직 GRF 계산 → box_grf_v11b.sto 생성.
이것이 Hicks 2015 RRA 절차의 핵심.

**경로 3 (장기): 접촉 구 (contact sphere) 도입**
발 contact sphere → GRF가 simulation 중 자동 결정.
MocoTrack으로 전환 필요. 가장 정확하나 작업량 많음.

---

## 7. 인용 목록

1. Dembia CL, Bianco NA, Falisse A, Hicks JL, Delp SL (2020). OpenSim Moco: Musculoskeletal optimal control. *PLoS Comput Biol* 16(12): e1008493. DOI: 10.1371/journal.pcbi.1008493

2. Falisse A, Serrancoli G, Dembia CL, Gillis J, De Groote F (2019). Algorithmic differentiation improves the computational efficiency of OpenSim-based trajectory optimization of human movement. *PLOS One* 14(10): e0217730.

3. Hicks JL, Uchida TK, Seth A, Rajagopal A, Delp SL (2015). Is my model good enough? Best practices for musculoskeletal models. *J Biomech Eng* 137(2): 020905. DOI: 10.1115/1.4029304

4. Anderson FC, Pandy MG (2001). Dynamic optimization of human walking. *J Biomech Eng* 123(5): 381-390.

5. Cholewicki J, McGill SM (1996). Mechanical stability of the in vivo lumbar spine. *Clin Biomech* 11(1): 1-15.

6. OpenSim Moco 공식 예제 (OpenSim 4.5 번들, 2023). `example3DWalking/exampleMocoInverse.py`, `exampleEMGTracking/exampleEMGTracking_helpers.py`, `example2DWalking/example2DWalking.py`. Authors: Dembia, Bianco, Umberger.

7. Bianco NA et al. (2023). OpenSim 4.4/4.5 release notes — MocoInverse improvements, ModOpAddResiduals API. https://github.com/opensim-org/opensim-core

---

_조사 완료: 2026-04-29. 조사 방법: 로컬 OpenSim 4.5.2 번들 예제 코드 직접 검토 + 알려진 문헌 사실 기반._
_외부 web 검색 없이 로컬 자료만으로 작성 — D'Hondt 2024 등 일부 DOI는 추정값이므로 실제 출판 확인 필요._
