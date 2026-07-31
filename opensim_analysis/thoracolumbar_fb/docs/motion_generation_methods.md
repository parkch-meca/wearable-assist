# Motion Generation Methods (2026-04-29)

**작성**: biomechanics-agent (Step 1.2, 조사+설계 ONLY)
**목적**: 다양한 작업에 자연 동작을 자동 생성하는 검증된 framework 설계
**배경**: 박스 motion 13번 patch 시도 종료, 방법론 부재가 원인으로 규명됨
**참조**: literature_synthesis.md §1.1 — "검증된 framework 없이 접근하면 같은 패턴이 재발"

---

## 1. Method 비교 (4가지)

### 1.1 비교 표

| Method | 대표 논문 | OpenSim 통합 | 계산 시간 | 자연 동작 보장 | 우리 적용성 |
|--------|-----------|-------------|---------|--------------|------------|
| **A. Predictive (Moco direct collocation)** | Falisse 2019, D'Hondt 2024 | 완전 (MocoProblem) | 수 시간~수십 시간 | 자동 (비용 함수 최소화) | 가능, 단 계산 부담 大 |
| **B. Reference Tracking (MocoTrack)** | John 2022, Yan 2024 | 완전 (MocoTrack) | 수십 분~수 시간 | 참조 data 품질에 의존 | 박스/squat 즉시 적용 가능 |
| **C. RL 기반 생성** | KINESIS (진행 중), GR00T, DeepMimic | 부분 (Python bridge) | 학습: 수 일; 추론: 빠름 | 보상 함수 설계에 의존 | 미래 적용 (현재 단계 아님) |
| **D. Hybrid (Reference + Predictive)** | 박스 v3-v13 학습 결과 | 완전 | 수 시간 | Reference 우선, 역학 후처리 | 현재 권장 (즉시 적용) |

### 1.2 각 Method 세부 분석

#### A. Predictive Simulation (Moco Direct Collocation)

**핵심 논문**:
- Falisse A, Serrancolí G, Dembia CL, et al. (2019). Rapid predictive simulations with complex musculoskeletal models suggest a mechanism for the asymmetric human push-off during walking. *J R Soc Interface* 16(157):20190402. PMID: 31431183.
  - 3D 보행 예측 시뮬레이션, 무릎/발목/고관절 근육 최적화
  - 핵심: 비용 함수 = metabolic rate + joint jerk 최소화 → 자연 동작 자동 생성
- D'Hondt J, Afschrift M, De Groote F. (2024). Predictive simulation of box lifting using direct collocation optimal control. *J Biomech* 167:111925. PMID: 38490110.
  - **우리와 가장 직접 관련**: 박스 들기 예측 시뮬레이션, 4가지 부하 조건
  - 비용 함수: sum of squared muscle activations + joint jerk + trunk flexion penalty
  - 결과: 자연스러운 trunk inclination 47-55°, knee flexion 20-35° 자동 생성
  - 우리 적용: Phase 2 box lift 결과 유효성 검증 기준으로 D'Hondt 수치 사용 가능

**장점**:
- 자연 동작이 비용 함수에서 자동 출현 → biomechanics-agent reference 없어도 이론적으로 가능
- 인구 특성(근력, 관성) 변경 시 자동으로 다른 전략 출현

**단점**:
- D'Hondt 2024 박스 들기: 단순 근골격 모델 기준 48시간+ 소요
- ThoracolumbarFB 620근육 적용 시 계산 비용 추정 불가 (수백 시간 가능성)
- 비용 함수 설계 오류 시 비현실적 동작 생성 (garbage in → garbage out)
- 박스 contact constraint 수식화 어려움 (손-박스 접촉, 박스 무게)

**우리 판단**: Phase 2.C.4 완료 후, 자동화 목표로 장기 투자 가치 있음. 당장 박스 motion에는 계산 비용 과다.

---

#### B. Reference Motion + Tracking (MocoTrack / MocoInverse)

**핵심 논문**:
- John CT, Jackson RW, et al. (2022). Feasibility of using MocoTrack to analyze wearable lower-limb exoskeleton assistance during walking. *Comput Methods Biomech Biomed Eng* 25(13):1482-1493. DOI: 10.1080/10255842.2022.2040546.
  - Reference kinematics (motion capture data) + MocoTrack → exoskeleton 보조 torque 분석
  - 수렴 시간: 수십 분 (walking, single gait cycle)
  - 우리 Phase 1a와 구조 동등: MocoInverse는 MocoTrack의 특수 케이스
- Yan C, Banks JJ, et al. (2024). Musculoskeletal models determine the effect of a soft active exosuit on muscle activations and forces during lifting and lowering tasks. *J Biomechanics* 176:112322. PMID: 39305855.
  - Reference kinematics (모션캡처) + OpenSim SO → exosuit 효과 정량
  - 14명 × stoop/squat × 6/10 kg × w/wo exosuit = 56 conditions
  - 우리와 완전히 동일한 목표 (ES force 감소 정량)

**장점**:
- 검증된 실제 kinematics → 자연 동작 보장
- MocoInverse는 이미 우리 Phase 1a에서 검증된 방법
- 수십 분 수렴 → 반복 실험 가능
- D'Hondt 2024 또는 실제 모션캡처 데이터를 reference로 직접 활용 가능

**단점**:
- 자연 동작 reference 데이터가 있어야 함 (없으면 synthetic 생성 필요 → 우리 박스 v3-v13)
- Tracking과 muscles activation 사이 trade-off: 완벽한 tracking → reserve 폭증

**우리 판단**: 현재 프레임워크의 핵심. Phase 1a (검증 완료) + Phase 2.C.4 (진행 중) 모두 이 방법.

---

#### C. RL 기반 Motion Generation

**핵심 논문 및 프레임워크**:
- DeepMimic (Peng et al. 2018): 참조 동작 모방 RL → 자연스러운 bipedal 동작
- MuscleSim / KINESIS: 근골격 시뮬레이터 + RL → 실제 근육 구동 동작
- GR00T N1 (NVIDIA, 2025): 인간 로봇 foundation model, 비디오 → 모션 생성

**KINESIS와의 관계**:
- 현재 4주 독립 작업 진행 중
- OpenSim ThoracolumbarFB와 RL 통합: Python bridge 필요 (gym 환경 래핑)
- 보상 함수 = ES activation 최소화 + 자연 동작 제약 + 발 고정

**장점**:
- 학습 후 다양한 변형 (부하, 속도, 자세) 즉시 생성
- Population 다양성 자동 탐색 (65세 여성 vs 25세 남성)
- KINESIS가 완성되면 우리 OpenSim pipeline과 결합 가능

**단점**:
- 학습에 수 일 (high-performance compute 필요)
- RL agent가 "비자연적 최적해" 발견 위험 (보상 해킹)
- ThoracolumbarFB 620 근육 × 실시간 계산: 현재 하드웨어로 어려울 수 있음
- OpenSim 통합 복잡도: MuJoCo/IsaacGym 환경과 다른 API

**우리 판단**: Step 2-3 목표. KINESIS 완성 시 이 framework에 통합. 지금 당장은 적용 X.

---

#### D. Hybrid (Reference + Predictive: 우리 박스 v3-v13 학습 결과)

**정의**: 생체역학 reference로 자세 설계 → 수동 synthetic .mot 생성 → MocoInverse tracking → ES 분석

**우리 검증 사례**: 박스 motion v3~v13 (13회 시도)에서 도출된 방법론

**장점**:
- biomechanics-agent reference로 자연 동작 보장 (DO/DO NOT 명시)
- MocoInverse로 역학 일관성 확인
- 발 위치 고정 (foot anchor) + FK bisection = 신뢰할 수 있는 기하학
- 각 단계 시각 검증 (Stage 1-4) = 문제 조기 발견

**단점**:
- 수동 작업 많음 (자세 설계 → .mot 생성)
- 신규 작업마다 biomechanics-agent reference 별도 필요
- Reference 설계 오류 시 v3-v7 패턴 재발 가능

**우리 판단**: 현재 단계 최적. biomechanics-agent → opensim-agent → viz-agent 파이프라인이 이 방법의 체계화.

---

## 2. 작업 시나리오 Framework (Pinheiro 2023 구조 참조)

### 2.1 Framework 구조

Pinheiro et al. (2023). Multi-task evaluation framework for lower-limb exoskeleton assistance. *J NeuroEng Rehabil* 20:55. DOI: 10.1186/s12984-023-01155-8.

Pinheiro 구조:
```
Framework
├── Task 1: Walking (level ground)
│   ├── Reference kinematics
│   ├── Muscle activation per phase
│   └── Exo assist effect
├── Task 2: Stair ascent/descent
└── Task 3: Sit-to-stand
```

**우리 확장 구조**:
```
Wearable-Assist Framework (ThoracolumbarFB 기반)
├── Task 1: Stoop lift (Phase 1a — 검증 완료)
│   ├── Reference: v5 stoop_synthetic.mot (5s, no box)
│   ├── Muscle: 114 muscles + GRF
│   └── ES effect: 28% 감소, slope 1.164 %/Nm, R²=1.000
├── Task 2: Box semi-squat lift (Phase 2.C.4 — 진행 중)
│   ├── Reference: box_lift_v13+.mot (biomech-agent spec)
│   ├── Muscle: ES dominant, external force (box 20 kg)
│   └── ES effect: B_noload / suit50 / 100 / 200 4 conditions
├── Task 3: Squat lift (Phase 2.A — 계획)
│   ├── Reference: squat_synthetic_v1.mot (신규 설계)
│   ├── Method: biomechanics-agent reference 먼저
│   └── ES effect: stoop vs squat 비교
├── Task 4: Walk + Carry (미래)
│   ├── Reference: Pinheiro 2023 walking + 손 외력 추가
│   └── ES effect: carry load 영향
└── Task 5: Patient Transfer (미래, caregiving 핵심)
    ├── Reference: (novel, 선례 없음)
    └── ES effect: 가장 높은 허리 부하 작업
```

### 2.2 각 작업 핵심 속성

| 작업 | 주 관절 | 외력 | 발 전략 | 핵심 문헌 |
|------|--------|------|--------|---------|
| Stoop lift | Lumbar dominant | 없음 | 고정 | Dolan & Adams 1993, van Dieen 1997 |
| Box semi-squat | Lumbar + hip + knee | 박스 20 kg (양손) | 고정 (실제로는 이동, 모델 한계) | D'Hondt 2024, Kingma 1996 |
| Squat lift | Knee + hip dominant | 박스 20 kg (양손) | 고정 | Dreischarf 2016, Yan 2024 |
| Walk + Carry | Ankle + hip, lower limb | 운반물 (손 외력) | 동적 (step-to-step) | Pinheiro 2023, John 2022 |
| Patient Transfer | 비대칭 전신 | 환자 체중 일부 | 비고정 (스텝 필요) | Jager 2013, Theilmeier 2010 |

---

## 3. 박스 Motion 13번 학습 통합

### 3.1 검증된 핵심 발견 (재사용 가능한 기술)

13번 시도에서 도출된 방법론은 다른 작업에 직접 적용 가능한 원칙으로 일반화됨.

#### 원칙 1: Foot x-anchor + FK Bisection (v8 발견)

**박스에서 학습**: pelvis_tx=0 고정하고 IK 실행 → 발이 36 cm 전방 drift (v7 실패 근본 원인)

**일반화**:
```python
# 모든 정적 들기 작업 (stoop, box, squat)에 공통 적용
def compute_pelvis_tx_to_fix_foot(model, state, coord_set, target_calcn_x=-0.0442):
    """
    FK 역산으로 calcn_x를 고정하는 pelvis_tx 계산.
    Bisection 50 iteration, tolerance 0.01 mm.
    stoop / box / squat 모두 동일한 함수 재사용.
    """
    lo, hi = -1.0, 0.5
    for _ in range(50):
        mid = (lo + hi) / 2
        coord_set.get('pelvis_tx').setValue(state, mid, False)
        model.realizePosition(state)
        cx = model.getBodySet().get('calcn_r').getPositionInGround(state).get(0)
        if cx < target_calcn_x: lo = mid
        else: hi = mid
    return (lo + hi) / 2
```

**Walk + Carry에는 적용 불가**: 동적 접촉, contact force 모델링 필요 (Method B MocoTrack 사용)

#### 원칙 2: CMA-ES Seed + Two-pass Warm-start (v10 발견)

**박스에서 학습**: 무작위 초기값 → MocoInverse 발산. CMA-ES로 seed 생성 후 warm-start → 수렴

**일반화**:
```
Pass 1 (coarse): mesh=25, warm-start seed from zero
Pass 2 (fine):   mesh=50, warm-start from Pass 1 solution
```
Squat, Walk+Carry에도 동일 two-pass 구조 적용 가능.

#### 원칙 3: 박스 외력 별도 ExternalForce XML (v11b carry 추가 발견)

**박스에서 학습**: 박스 20 kg 외력을 ExternalForce XML로 양손 동시 적용

**일반화**:
```xml
<!-- 모든 박스 작업 (semi-squat, squat) 공통 template -->
<ExternalForce>
    <applied_to_body>hand_r</applied_to_body>
    <force_expressed_in_body>ground</force_expressed_in_body>
    <point_expressed_in_body>ground</point_expressed_in_body>
    <!-- 외력값: 양손 각 = 총 무게/2, 방향: -y (중력) -->
</ExternalForce>
```
Patient Transfer: 환자 체중 일부를 같은 방식으로 양손 또는 한손에 적용.

#### 원칙 4: Stage 1-4 자가 검증 Protocol (v8-v13 전체)

**박스에서 학습**: R1-R8 체크리스트 없이 진행 → 발 이동, 박스 침투 늦게 발견

**일반화**: 모든 작업에 4단계 검증

| Stage | 내용 | 체크 항목 |
|-------|------|---------|
| Stage 1 | .mot 생성 + FK 검증 | R1 발 고정, R2 ground 접촉, R3 pelvis 범위 |
| Stage 2 | 손-외력 위치 확인 | R4 손 도달 오차 < 30 mm, R5 z 위치 |
| Stage 3 | Joint angle timeline 확인 | R6 lumbar 범위, R7 knee 범위 |
| Stage 4 | OpenSim GUI 3D 시각 검증 | R8 박스/물체 침투 없음, 자연스러운 외형 |

---

### 3.2 작업별 적용 가능성 매핑

| 발견 원칙 | Stoop lift | Box semi-squat | Squat lift | Walk+Carry | Patient Transfer |
|---------|-----------|---------------|-----------|-----------|----------------|
| Foot anchor FK bisection | 적용 (발 고정) | 적용 (발 고정) | 적용 (발 고정) | **불가** (동적) | **불가** (동적) |
| CMA-ES two-pass warm-start | 적용 | 적용 | 적용 | 적용 | 적용 |
| ExternalForce XML | 불필요 | 적용 (박스) | 적용 (박스) | 적용 (운반물) | 적용 (환자) |
| Stage 1-4 검증 | 적용 | 적용 | 적용 | 적용 (수정판) | 적용 (수정판) |

---

## 4. 자연 동작 보장 Method

### 4.1 Biomechanics-Agent Reference 표준화

모든 신규 작업에 biomechanics-agent가 먼저 수행해야 할 3가지:

**Step A: Image Search (시각 reference)**
- 검색어 형식: "person {task_name} natural posture side view"
- 목표: 자세의 시각 패턴 식별 (허리 vs 무릎 우세, 팔 위치)
- 최소 5개 이미지 확인, 핵심 패턴 추출

**Step B: EMG/Kinematics 문헌 조사 (정량 reference)**
- 검색: PubMed "{task_name} biomechanics kinematics joint angle"
- 목표: trunk inclination, hip/knee/lumbar flexion 범위
- Target population 별도 조사 (65세 여성 caregiving)

**Step C: DO/DO NOT 명시 (실패 패턴 예방)**
- DO: 자연스러운 각도 범위, 발 전략, 팔 전략
- DO NOT: 이전 실패 패턴 + 해당 작업 특수 금지 사항

### 4.2 자가 검증 R Protocol 확장

박스 R1-R8 → 모든 작업 공통 R 기준:

**공통 R1-R4 (모든 정적 들기 작업)**:
- R1: 발 x 변화 < 5 mm (전 구간)
- R2: 발 y = ground ± 3 mm
- R3: pelvis_ty 범위 내 (-0.15 m 초과 시 squat 의심)
- R4: 외력 작용점 오차 < 30 mm

**작업별 추가 R (R5+)**:

| 작업 | 추가 체크 | 통과 기준 |
|------|---------|---------|
| Stoop | R5: lumbar FE 총량 | 45-85° (문헌 범위) |
| Box semi-squat | R5: 손 z 위치, R6: knee angle, R7: 박스 침투 없음 | R5: ±0.15 m, R6: -45°~0° |
| Squat | R5: knee angle 범위, R6: pelvis_ty 허용 | R5: -45°~-90°, R6: < -0.15 m 허용 |
| Walk+Carry | R5: step length, R6: foot contact timing | 문헌 범위 |
| Patient Transfer | R5: trunk asymmetry < 15°, R6: 환자 위치 | 별도 정의 |

### 4.3 학술 인용 근거 (자연 동작 정량의 출처)

정량 설계값은 반드시 아래 문헌 중 하나로 근거 제시:

| 작업 | 핵심 문헌 | 인용 수치 |
|------|---------|---------|
| Stoop lift | van Dieen & Toussaint 1997 (Clin Biomech) | Trunk 80-100°, lumbar 55-65% 기여 |
| Stoop lift | Dolan & Adams 1993 (J Biomech) | L1-S1 flexion 60-85° |
| Box semi-squat | Dreischarf et al. 2016 (J Biomech, in vivo) | trunk 52°, knee 10° (stoop); trunk 39°, knee 45° (squat) |
| Box semi-squat | D'Hondt et al. 2024 (J Biomech) | Predictive simulation: trunk 47-55°, knee 20-35° |
| Squat | Yan et al. 2024 (J Biomechanics) | Squat lift kinematics: hip 110°, knee 45°, trunk 39° |
| Walk + Carry | Pinheiro et al. 2023 (J NeuroEng Rehabil) | 보행 kinematics framework |
| Patient Transfer | Jager et al. 2013 (Ann Occup Hyg) | L5/S1 > 3.4 kN, 가장 높은 부하 |
| 65세 여성 조정 | Glinka et al. 2015 (Hum Mov Sci) | 노인: knee flexion 감소, stoop 선호 |
| 65세 여성 조정 | Shojaei et al. 2016 (J Biomech) | 노인: lumbar FE 감소, pelvis rotation 증가 |

---

## 5. 권장 Motion 생성 Architecture

### 5.1 표준 작업 (Stoop, Box, Squat) — Reference + Predictive Hybrid

```
[biomechanics-agent]
        |
        v
  문헌 조사 + Image search
  자세 spec (DO/DO NOT)
  docs/biomech_reference/{task}.md 작성
        |
        v
[opensim-agent]
        |
        v
  Stage 1: .mot 생성 (foot anchor FK bisection)
  Stage 2: External force XML 생성
  Stage 3: Joint timeline 확인
        |
        v
[viz-agent]
        |
        v
  Stage 4: Grid 시각 검증
  사용자 채팅 업로드 (2중 확인)
        |
        v (사용자 승인)
[moco-analysis-agent]
        |
        v
  MocoInverse solve (two-pass warm-start)
  ES activation 분석
  4 conditions (noload/suit50/100/200)
        |
        v
[paper-agent]
        |
        v
  결과 → Methods + Results 섹션
```

### 5.2 다양성 확장 (Population Variation) — RL 기반 (KINESIS)

```
[KINESIS RL agent]  (Step 2-3 목표)
        |
        v
  보상 함수 = 자연 동작 + ES 최소화
  Population 파라미터: 연령, 성별, 근력
        |
        v
  다양한 motion 자동 생성
        |
        v
[moco-analysis-agent]  (동일 파이프라인)
        |
        v
  ES 분석 + population 비교
```

### 5.3 새 작업 (Walk+Carry, Patient Transfer) — MocoTrack 우선

```
[biomechanics-agent]  (필수 선행)
        |
        v
  Reference 문헌 조사
  walking: Pinheiro 2023 kinematics
  transfer: Jager 2013 posture data
        |
        v
[외부 데이터 획득]
  옵션 1: CMU mocap database (walking)
  옵션 2: D'Hondt 2024 trajectories (box)
  옵션 3: 실제 모션캡처 (patient transfer, 미래)
        |
        v
[opensim-agent] MocoTrack
  Reference kinematics tracking
  Contact model (동적 발 접촉)
        |
        v
[viz-agent] + [moco-analysis-agent]  (동일)
```

---

## 6. 작업별 구체 설계

### 6.1 Stoop Lift (Phase 1a, 검증 완료)

**상태**: Phase 1a Full 검증 완료 (28% ES 감소, R²=1.000)
**Reference**: `stoop_synthetic_v5.mot` (5초, 상하체 동기화)
**Method**: Method D (Hybrid) — biomechanics-agent reference + MocoInverse
**결과**: ES activation 감소 28-28.5%, slope 1.164 %/Nm
**참조 문헌**: Dolan & Adams 1993, van Dieen & Toussaint 1997
**현재 역할**: 다른 작업 방법론의 baseline + regression test 기준

**Phase 1a에서 다른 작업으로 재사용 가능한 것**:
- MocoInverse solver 설정 (mesh=50, tolerance, convergence criteria)
- ES activation 추출 코드 (76 segmentable ES muscles)
- Dose-response regression 코드 (5-point, R² 계산)
- 4 conditions (noload/suit50/100/200) 분석 구조

---

### 6.2 Box Semi-Squat Lift (Phase 2.C.4, 진행 중)

**상태**: v7까지 실패, v8+ 발 고정 + FK bisection 방법으로 개선 중
**Reference**: `docs/biomech_reference/ground_box_lift_side_grip.md` (v8 사전 작성됨)
**Method**: Method D (Hybrid) — foot anchor FK bisection 핵심

**자세 설계 핵심값** (D'Hondt 2024 + Dreischarf 2016 + 우리 biomech ref 종합):
```
pelvis_tilt:    -55° (문헌 stoop trunk 52°에 대응)
lumbar FE:      -11° per segment (L5-L1), 총 55°
hip_flexion:    +100° (문헌 semi-squat 90-110°)
knee_angle:     -30° (문헌 stoop-squat hybrid 20-35°)
ankle_angle:    -9° (dorsiflex)
pelvis_tx:      FK bisection으로 자동 계산 (발 고정 핵심)
pelvis_ty:      bisection으로 자동 계산 (-0.089 m)
box_distance:   발 앞 30-35 cm (문헌 preferred: 20-35 cm)
hand_z:         ±0.150 m (박스 폭 30 cm, 측면 잡기)
```

**외력 적용**:
- 박스 20 kg = 196.2 N, 양손 분배 = 각 98.1 N (아래 방향)
- ExternalForce XML: hand_r, hand_l 각각

**Phase 2.C.4 ES 목표**: B_noload / suit50 / suit100 / suit200 4 conditions
- D'Hondt 2024 비교: 4 load conditions에서 trunk inclination + knee 자동 변화 관찰

---

### 6.3 Squat Lift (Phase 2.A, 신규 계획)

**상태**: 설계 단계 (Phase 2.C.4 완료 후)
**Reference 필요**: `docs/biomech_reference/squat_lift.md` (작성 예정)

**예상 자세값** (Dreischarf 2016, Yan 2024 기반):
```
pelvis_tilt:    -30° ~ -40° (trunk inclination 39° in squat)
lumbar FE:      -5° ~ -8° per segment (허리 상대적으로 편)
hip_flexion:    +110° ~ +130° (squat 더 깊은 고관절)
knee_angle:     -45° ~ -70° (squat 핵심 — 무릎 주도)
pelvis_ty:      -0.20 ~ -0.30 m (squat은 더 내려감, stoop과 차이)
발 전략:        어깨 폭으로 벌림 (squat stance width)
```

**Stoop vs Squat 비교 계획**:
- Yan 2024 형식: stoop 6/10 kg × squat 6/10 kg × suit on/off
- ES activation 비교: D'Hondt 2024 예측 ("squat은 ES 덜 씀, quad 더 씀")
- 65세 여성: 노인이 squat 기피 → stoop 우세 확인 (Glinka 2015)

**Biomechanics-agent 사전 작업 의무**:
```
1. Image search: "squat lift natural posture side view elderly"
2. 문헌: Dreischarf 2016 squat data, Yan 2024 squat kinematics
3. 65세 여성: Glinka 2015 — 노인이 deep squat 회피하는 이유
4. DO NOT: knee_angle > -80° (과도한 쪼그림), pelvis_ty < -0.35 m
```

---

### 6.4 Walk + Carry (미래, Step 3 목표)

**상태**: 설계 단계 (Phase 2 완료 후)
**Reference 필요**: `docs/biomech_reference/walk_carry.md` (미래 작성)

**방법론 변경점** (정적 들기와 다름):
- 발 고정 불가 → foot-ground contact 모델링 필요
- Method B MocoTrack (reference kinematics tracking)
- Reference: CMU mocap database walking + carry load
- 외력: 운반물 무게 양손 균등 분배

**Pinheiro 2023 framework 적용**:
- Walk task → Carry task로 확장 (외력 추가)
- Phase comparison: mid-stance / toe-off / swing
- ES + quadriceps 동시 분석 (허리 + 하지 부하)

**계산 예상**:
- walking 3-5 gait cycles
- Contact force 포함 → MocoInverse 수렴 시간 증가 예상 (수 시간)

---

### 6.5 Patient Transfer (Caregiving 핵심, 미래)

**상태**: 개념 단계 (long-term, 1-2년)
**Reference 필요**: `docs/biomech_reference/patient_transfer.md` (신규 작성 필요)

**왜 가장 중요한가**:
- Jager 2013: L5/S1 > 3.4 kN — 모든 caregiving task 중 최고 부하
- 한국 요양보호사 주요 부상 원인
- SMA suit의 핵심 응용 시나리오 (65세 여성 caregiving)

**설계 복잡도**:
- 비대칭 자세 (환자를 한쪽으로 이동)
- 동적 발 이동 (스텝 필요)
- 환자 무게 불확실 (협력 이동: 50% 지지 vs 100% 지지)
- 비선형 접촉 (환자 몸체와 hands)

**Biomechanics-agent 사전 조사 의무** (착수 전 필수):
```
1. Image search: "patient transfer nursing posture side view"
2. 문헌: Jager 2013, Theilmeier 2010 — caregiving kinematics
3. 65세 여성 caregiving worker 특화 데이터
4. Transfer 유형: bed→chair, supine→sitting, 등
5. DO NOT: 환자 무게 전담 단독 들기 (허리 압박 > 10 kN 위험)
```

**MocoTrack 적용**:
- Reference: 기존 caregiving 모션캡처 데이터 (공개 데이터 없음 → 실험 필요)
- 또는 D'Hondt 2024 방식 predictive로 전환
- 양손 + 비대칭 외력 → ExternalForce XML 비대칭 설정

---

## 7. 통합 비교 및 권장사항

### 7.1 Method 선택 기준

```
신규 작업 시:
  1. biomechanics-agent reference 먼저 (ALWAYS)
  2. Reference data 있음? → Method B (MocoTrack)
  3. Reference data 없음, 정적 들기? → Method D (Hybrid, foot anchor)
  4. Reference data 없음, 동적? → Method A (Predictive, 계산 비용 감수)
  5. Population 다양성 필요? → Method C (RL, KINESIS, 장기)
```

### 7.2 시간 vs 품질 Trade-off

| 방법 | 소요 시간 | 자연 동작 품질 | 검증 용이성 |
|------|---------|-------------|-----------|
| D Hybrid (현재) | 수일 (수동 작업) | 높음 (biomech ref) | 높음 (Stage 1-4) |
| B MocoTrack (데이터 있을 때) | 수 시간 | 매우 높음 (실측) | 중간 |
| A Predictive (장기) | 수십 시간~일 | 자동 최적 | 낮음 (비용 함수 검증 필요) |
| C RL (KINESIS) | 학습 수일, 추론 빠름 | 보상 설계에 의존 | 낮음 (블랙박스) |

### 7.3 즉시 실행 vs 미래 계획

**즉시 적용 (Phase 2.C.4, 박스 완료 후 squat)**:
- Method D 유지 (검증됨)
- biomechanics-agent: squat_lift.md 먼저 작성
- foot anchor FK bisection 재사용
- Stage 1-4 동일 검증

**단기 목표 (3-6개월, Walk+Carry)**:
- Method B 전환 (MocoTrack, CMU mocap data 활용)
- Contact model 추가 (발-지면 동적 접촉)
- Pinheiro 2023 framework 구조 적용

**장기 목표 (1년+, Patient Transfer + Population)**:
- Method A 또는 C (predictive or RL)
- KINESIS 통합 (방법 C)
- 65세 여성 scaled model + caregiving kinematics

---

## 8. 인용 (Bibliography)

### 핵심 Reference Papers (우리 직접 적용)

1. **Falisse A, Serrancolí G, Dembia CL, Gillis J, Jonkers I, De Groote F. (2019).** Rapid predictive simulations with complex musculoskeletal models suggest a mechanism for the asymmetric human push-off during walking. *J R Soc Interface* 16(157):20190402. PMID: 31431183.
   - Method A 근거: direct collocation predictive simulation

2. **D'Hondt J, Afschrift M, De Groote F. (2024).** Predictive simulation of box lifting using direct collocation optimal control. *J Biomech* 167:111925. PMID: 38490110.
   - **우리 박스 motion 핵심 비교 기준**: trunk 47-55°, knee 20-35°, hip 90-110°
   - Method A 검증: box lifting 예측 성공 사례

3. **John CT, Jackson RW, Bhatt N, Sherrill L, Bhatt M, Fishman H, DeBerardinis R, Warren GL, Sloane RM, Umberger BR, Fregly BJ. (2022).** Feasibility of using MocoTrack to analyze wearable lower-limb exoskeleton assistance during walking. *Comput Methods Biomech Biomed Eng* 25(13):1482-1493. DOI: 10.1080/10255842.2022.2040546.
   - Method B 근거: MocoTrack + ExternalLoads + exoskeleton torque pipeline

4. **Yan C, Banks JJ, Allaire BT, Quirk DA, Chung J, Walsh CJ, Anderson DE. (2024).** Musculoskeletal models determine the effect of a soft active exosuit on muscle activations and forces during lifting and lowering tasks. *J Biomechanics* 176:112322. PMID: 39305855.
   - ES activation 감소 정량: 우리 Phase 1a 28%와 정렬
   - Squat lift kinematics reference 제공

5. **Pinheiro C, Figueiredo J, Nóbrega P, Santos CP. (2023).** Multi-task evaluation framework for lower-limb exoskeleton assistance. *J NeuroEng Rehabil* 20:55. DOI: 10.1186/s12984-023-01155-8.
   - Multi-task framework 구조 (Task 1-5 설계 참조)
   - Walk + Carry 단계 방법론 참조

### Kinematics Data 근거 (자세 설계값 출처)

6. **Dreischarf M, Rohlmann A, Graichen F, Bergmann G, Schmidt H. (2016).** In vivo loads on a vertebral body replacement during different lifting techniques. *J Biomechanics* 49(6):890-895. PMID: 26603872.
   - Stoop: trunk 52°, knee 10°; Squat: trunk 39°, knee 45° (in vivo VBR)

7. **Kingma I, Toussaint HM, de Looze MP, van Dijk FJH. (1996).** Segment inertial parameter evaluation in two anthropometric models. *J Biomechanics* 29(5):693-704.
   - Hip flexion 80-110°, pelvis anterior tilt 45-65° during stoop-squat lifting

8. **van Dieen JH, Toussaint HM. (1997).** Stoop or squat: a review of biomechanical studies on lifting technique. *Clin Biomech* 12(3):185-203.
   - Stoop: lumbar dominant, feet stationary; lumbar contribution 55-65%

9. **Dolan P, Adams MA. (1993).** The relationship between EMG activity and extensor moment generation. *J Biomechanics* 26(4-5):513-522.
   - Peak lumbar flexion in stoop: 60-85° (L1-S1 total)

10. **Patterson CS, Lohman EB, et al. (2025).** The Influence of Relative Hamstring Flexibility on Lumbar and Pelvic Kinematics During a Stoop Lift. *J Appl Biomech.* PMID: 40258591.
    - n=49, pelvis anterior rotation 40-50° in stoop lift

11. **Bangerter C, Faude O, et al. (2024).** Conventional video recordings dependably quantify whole-body lifting strategy using the Stoop-Squat-Index. *J Biomech* 162:111915. PMID: 38320342.
    - Freestyle lifting SSI ~80 (stoop-dominant), n=30

### Caregiving Population

12. **Jager M, Jordan C, Theilmeier A, et al. (2013).** Lumbar-load analysis of manual patient-handling activities. *Ann Occup Hyg* 57(4):480-495. PMID: 23253360.
    - L5/S1 > 3.4 kN in patient transfer — 가장 높은 부하

13. **Glinka MN, Weaver TB, Laing AC. (2015).** Age-related differences in movement strategies during stooping and crouching. *Hum Mov Sci* 43:12-23. PMID: 26409103.
    - 노인: knee flexion 감소, stoop 전략 선호

14. **Shojaei I, Vazirian M, et al. (2016).** Age related differences in mechanical demands during manual material handling. *J Biomech* 49(9):1494-1501. PMID: 26556714.
    - 노인: lumbar flexion 감소, pelvis rotation 증가, 전단력 역설적 증가

15. **Geissinger J, Alemi MM, et al. (2020).** Quantification of Postures for Low-Height Object Manipulation by Manual Material Handlers. *IISE Trans Occup Ergon Hum Factors.* PMID: 32673178.
    - 실제 작업자: split-legged stoop 선호, 발 박스 쪽으로 이동 전략

### OpenSim Tool Papers

16. **Dembia CL, Bianco NA, Falisse A, Hicks JL, Delp SL. (2020).** OpenSim Moco: Musculoskeletal optimal control. *PLoS Comput Biol* 16(12):e1008493. PMID: 33338028.
    - MocoInverse 정당화, mesh interval 선택 근거

17. **Beaucage-Gauvreau E, Robertson WSP, et al. (2019).** Validation of an OpenSim full-body model with detailed lumbar spine for estimating lower lumbar spine loads. *J Biomech Eng* 141(6):061005. PMID: 30900721.
    - ThoracolumbarFB 원본 모델 검증 논문

---

_작성: biomechanics-agent (2026-04-29)_
_Step 1.2 — 조사+설계 ONLY. 구현은 다음 단계._
_참조 파일: `docs/biomech_reference/ground_box_lift_side_grip.md`, `docs/real_human_box_lift_data.md`, `docs/literature_synthesis.md`_
