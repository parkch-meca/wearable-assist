# 대체 Fullbody 모델 후보 (2026-04-29)

**작성**: biomechanics-agent
**목적**: Step 2.1 — 박스 lifting 적합 대체 모델 web 조사 + 로컬 모델 비교
**배경**: ThoracolumbarFB arm reach 54.5 cm (인체 대비 -31.9%) → 박스 lifting 9번 연속 실패

---

## 1. 시스템 내 모델 + 공개 모델 후보 목록

### 1.1 현재 시스템 내 모델 (로컬)

| 모델 | 경로 | 척추 분절 | Muscle 수 | Arm reach | 박스 lifting |
|------|------|---------|---------|---------|------------|
| ThoracolumbarFB v2.0 (no_coupler) | `/data/opensim_models/ThoracolumbarFB/...` | 22 (T1~S1) | **620** | **54.5 cm** | **NO** (-141 mm) |
| LFB v1.0 | `/data/opensim_models/LFB/LFB_model.osim` | 5 (L1~L5) | 238 | ~53 cm | **NO** |
| Rajagopal 2016 | `/data/opensim_models/Rajagopal2016.osim` | 1 (lumbar) | 80 | ~53 cm | 구조 제한 |
| RajagopalLaiUhlrich 2023 | `/data/opensim_models/RajagopalLaiUhlrich2023.osim` | 1 (lumbar) | 80 | ~53 cm | 구조 제한 |

### 1.2 공개/학술 모델 후보 (web 조사)

---

## 2. 각 모델 상세 평가

### 2.1 ThoracolumbarFB v2.0 (현재 모델)

**출처**: Ignasiak et al. 2016 + 다수 업데이트, SimTK.org 공개  
**논문**: Phase 1a에서 이미 활용 중, ES 분석 골든 스탠다드

| 항목 | 값 | 평가 |
|------|----|----|
| 척추 분절 | 22개 (T1~S1, 각 관절 독립) | ES 분석 최적 |
| ES muscle 수 | 76개 (erector spinae 분절별) | 목적에 최적 |
| Total muscles | 620 | 최다 |
| Arm reach (GH→hand_R) | 54.5 cm | **인체 대비 -31.9%** |
| shoulder_elv ROM | 0~155° (no_coupler 버전) | 적절 |
| 박스 lifting 적합성 | NO | 자연스러운 자세에서 141 mm 부족 |
| Phase 1a 호환 | **완전 호환** | |
| 학술 인용 | 높음 | |

**판정**: ES 분석 목적에는 최선. 박스 lifting 표현에는 arm geometry 한계.

---

### 2.2 GenericLiftingFullBody (LFB) v1.0

**출처**: Beaucage-Gauvreau et al. 2019, PLoS ONE; SimTK.org 공개  
**경로**: `/data/opensim_models/LFB/LFB_model.osim`

| 항목 | 값 | 평가 |
|------|----|----|
| 척추 분절 | 5 (L1~L5) + torso (상위는 단일 rigid) | ES 분석 제한 |
| ES muscle 수 | 0 (ES 없음) | **ES 분석 불가** |
| Total muscles | 238 | 중간 |
| Lumbar ROM | L5_S1 only: **-11.2° ~ +3.6°** | **극히 제한** |
| Arm ROM | arm_flex -90°~180° | 넓음 |
| Arm reach | ~53 cm (ThoracolumbarFB와 유사) | 부족 |
| 박스 lifting 자세 | lumbar -11° 이상 불가 | **근본적으로 부적합** |
| Phase 1a 호환 | **불가** (척추 구조 완전 다름) | |

**판정**: 박스 lifting 설계 목적으로도 lumbar ROM이 너무 제한적이며, ES 분석 불가.

---

### 2.3 Rajagopal Full Body Model 2016

**출처**: Rajagopal A, Dembia CL, DeMers MS, Delp DD, Hicks JL, Delp SL (2016).
Full-Body Musculoskeletal Model for Muscle-Driven Simulation of Human Gait.
*IEEE Trans Biomed Eng 63(10): 2068-2079.* PMID: 27392337

**경로**: `/data/opensim_models/Rajagopal2016.osim`

| 항목 | 값 | 평가 |
|------|----|----|
| 척추 분절 | **1개** (lumbar_extension 단일 DOF) | ES 분석 불가 |
| ES muscle 수 | 0 (ES 없음) | **불가** |
| Total muscles | 80 (하지 중심) | 적음 |
| Lumbar ROM | -90° ~ +90° (단일 joint) | 범위는 넓지만 단순 |
| Hip ROM | -30° ~ +120° | 적절 |
| Arm ROM | arm_flex -90°~+90°, arm_add -120°~+90° | 적절 |
| Arm reach | ~53 cm | 부족 (ThoracolumbarFB와 유사) |
| 박스 lifting (이론) | 단일 lumbar joint = 비현실적 자세 | 부적합 |
| Phase 1a 호환 | **불가** | |
| 주요 용도 | Gait (보행) 시뮬레이션 | 도메인 불일치 |

**판정**: Gait 전용 모델. ES 없음. 박스 lifting에 부적합.

---

### 2.4 RajagopalLaiUhlrich Full Body 2023

**출처**: Lai AK, Uhlrich SD, Delp SL (2023) — Rajagopal 2016의 업데이트 버전
**경로**: `/data/opensim_models/RajagopalLaiUhlrich2023.osim`

| 항목 | 값 | 평가 |
|------|----|----|
| 척추 분절 | 1 (lumbar_extension) | ES 분석 불가 |
| Total muscles | 80 | Rajagopal과 동일 |
| Wrist DoF 추가 | wrist_flex, wrist_dev 추가됨 | lifting과 무관 |
| 박스 lifting | 구조적 제한 동일 | 부적합 |
| Phase 1a 호환 | **불가** | |

**판정**: Rajagopal 2016과 동일한 한계. 추가 wrist DoF는 lifting과 무관.

---

### 2.5 AnyBody PGBM (Generic Lumbar Spine, de Zee et al. 2007)

**출처**: de Zee M, Hansen L, Wong C, Rasmussen J, Simonsen EB (2007).
A generic detailed rigid-body lumbar spine model.
*Journal of Biomechanics 40(6): 1219-1227.* PMID: 16901492

| 항목 | 값 | 평가 |
|------|----|----|
| 척추 분절 | 7 (L1~S1, 18 DOF) | 상세 lumbar |
| Muscles | 154 (lumbar 전용) | 상체만 |
| 용도 | AnyBody Modelling System | OpenSim 비호환 |
| Validation | L4-5 intradiscal pressure | 검증 충분 |
| 박스 lifting | 시뮬레이션 가능 (AnyBody 내) | OpenSim 이전 불가 |
| 공개 여부 | AnyBody 상용 소프트웨어 | 접근 제한 |

**판정**: AnyBody 전용. OpenSim 프로젝트와 직접 호환 불가.

---

### 2.6 Holzbaur Upper Extremity Model 2005

**출처**: Holzbaur KRS, Murray WM, Delp SL (2005).
A model of the upper extremity for simulating musculoskeletal surgery and analyzing neuromuscular control.
*Annals of Biomedical Engineering 33(6): 829-840.* PMID: 16078622

| 항목 | 값 | 평가 |
|------|----|----|
| 척추 분절 | 없음 (상지 전용 모델) | |
| Upper extremity DoF | 15 (shoulder~wrist~finger) | 상세 |
| Muscles | 50 compartments | 어깨+팔 근육 상세 |
| Arm reach | 정상 인체 기준 | **충분** |
| 용도 | 어깨 수술 시뮬레이션, 신경근 제어 | |
| OpenSim 호환 | 예 (OpenSim 원조 모델) | |
| ThoracolumbarFB와 결합 가능? | 이론적 가능 | 높은 복잡도 |

**판정**: ThoracolumbarFB 척추 + Holzbaur 어깨/팔 hybrid의 가능성. 복잡도 높음.

---

### 2.7 Hamner Full Body 2010 (92 musculotendon actuators)

**출처**: Hamner SR, Seth A, Delp SL (2010).
Muscle contributions to propulsion and support during running.
*Journal of Biomechanics 43(14): 2709-2716.* PMID: 20691972

| 항목 | 값 | 평가 |
|------|----|----|
| 척추 분절 | 1 (torso rigid body) | ES 분석 불가 |
| Total muscles | 92 (하지 + 팔 torque 포함) | |
| 팔 DoF | 있음 (arm swing 포함) | |
| 용도 | Running gait simulation | 도메인 불일치 |
| Phase 1a 호환 | **불가** | |

**판정**: Running 전용. ES 없음.

---

### 2.8 MoBo (Model Bodenreaction) 계열 / exoskeleton lifting 논문 모델들

**최근 논문 (2024-2026) 에서 box lifting에 사용된 모델:**

| 연구 | 모델 | 척추 | ES 가능? |
|------|------|-----|---------|
| Favennec et al. 2026 (CMBBE) | "validated musculoskeletal model" + CORFOR exo | "15 participants lifted a box" | 불명 |
| Hu et al. 2026 (Ergonomics) | "subject-specific" EMG-driven model | L5S1 | ES: 부분 |
| Eskandari et al. 2025 (Applied Ergonomics) | Comprehensive back muscles model | L1-S1 | 가능 |

**Eskandari et al. 2025 주목**: "comprehensive set of outcomes... trunk muscle activation, muscle group forces, spinal loads" → 박스 lifting + ES 분석 모두 수행. 사용 모델이 OpenSim 기반이라면 참고 가치 큼.

---

## 3. 박스 lifting 적합성 평가 종합표

| 모델 | 척추 분절 | ES 분석 | Arm reach | 박스 lifting | Phase 1a | 공개 |
|------|---------|--------|---------|------------|---------|------|
| **ThoracolumbarFB v2.0** | **22** | **76개** | 54.5 cm | NO (-31.9%) | **YES** | YES |
| LFB v1.0 | 5 | 없음 | ~53 cm | NO (lumbar ROM) | NO | YES |
| Rajagopal 2016 | 1 | 없음 | ~53 cm | NO (구조) | NO | YES |
| RajagopalLai 2023 | 1 | 없음 | ~53 cm | NO (구조) | NO | YES |
| AnyBody PGBM | 7 | 부분 | - | AnyBody만 | NO | AnyBody |
| Holzbaur UE | 없음 | 없음 | **~75-80 cm** | 어깨만 | NO (hybrid) | YES |
| Hamner 2010 | 1 | 없음 | ~53 cm | NO | NO | YES |

---

## 4. ThoracolumbarFB vs 후보 모델 핵심 비교

### 4.1 ES 분석 관점 (본 연구의 주 목적)

```
ThoracolumbarFB: 척추 22분절, 76 ES muscles → 유일하게 이 연구 목적 충족
LFB:             5 lumbar 분절, ES 없음   → 불가
Rajagopal:       1 lumbar 단일 → 완전 불가
AnyBody PGBM:    7 lumbar, OpenSim 비호환 → 이전 불가
```

**결론**: ES 분석 관점에서 ThoracolumbarFB 대체 불가. 시스템 내 어떤 모델도 76 ES 분석을 제공하지 못함.

### 4.2 Arm reach 관점

```
모든 현재 모델: GH→hand ~53-55 cm (유사하게 짧음)
실제 인체:      GH→hand ~75-80 cm
Holzbaur UE:   ~75-80 cm (어깨 전용 모델, 척추 없음)
```

**결론**: OpenSim 표준 arm geometry는 전반적으로 인체측정 기준 대비 짧음. 이는 단일 모델의 문제가 아닌 OpenSim 커뮤니티 공통 특성.

---

## 5. 권장 후보 (있다면)

### 5.1 즉시 활용 가능한 대안: 없음

시스템 내 어떤 모델도 다음 두 조건을 동시 충족하지 못함:
- 조건 A: 76 ES muscles (segment-wise ES analysis 가능)
- 조건 B: 박스 lifting (natural stoop 자세에서 팔 reach 가능)

### 5.2 가능한 접근 방향

**방향 1: ThoracolumbarFB 팔 geometry 보강 (humerus scale-up)**
- ThoracolumbarFB humerus_R/L 길이를 29 cm → 33 cm로 scale (+13.8%)
- forearm geometry 재구성 (현재 ulna 2.3 cm → 26-28 cm)
- 예상 reach 보강: +20-25 cm → total ~75-80 cm
- Phase 1a 영향: 예상 ΔES < 1 %p (팔 세그먼트와 ES는 직접 연결 없음)
- 학술 정당성: 필요 (Methods에 인체측정 근거 제시)

**방향 2: 박스 시나리오 자체를 변경**
- 지면 박스(y=-0.755) → 작업대 박스(y=-0.30 ~ -0.50)로 높이 조정
- 현재 모델로 reach 가능한 박스 높이: Low pallet (mid y=-0.60) 이상
- 단점: 연구 시나리오(지면 박스 들기)와 불일치

**방향 3: 발 위치 제약 완화 (발이 박스 쪽으로 이동)**
- 실제 인체에서 가장 자연스러운 전략
- 발 고정 전제 제거 → IK에서 calcn_r x를 자유화하되 박스에 근접 이동
- 현실적 lifting 시나리오에 부합
- Phase 1a (제자리 stoop)에는 영향 없음

---

## 6. 인용 문헌

1. **Rajagopal A, Dembia CL, DeMers MS, Delp DD, Hicks JL, Delp SL (2016).**
   Full-Body Musculoskeletal Model for Muscle-Driven Simulation of Human Gait.
   *IEEE Transactions on Biomedical Engineering 63(10): 2068-2079.* PMID: 27392337
   - Lower extremity focused, 80 muscles, single lumbar joint

2. **de Zee M, Hansen L, Wong C, Rasmussen J, Simonsen EB (2007).**
   A generic detailed rigid-body lumbar spine model.
   *Journal of Biomechanics 40(6): 1219-1227.* PMID: 16901492
   - AnyBody-based; 7 lumbar segments, 154 muscles; validated against intradiscal pressure

3. **Holzbaur KRS, Murray WM, Delp SL (2005).**
   A model of the upper extremity for simulating musculoskeletal surgery and analyzing neuromuscular control.
   *Annals of Biomedical Engineering 33(6): 829-840.* PMID: 16078622
   - 15 DoF, 50 muscle compartments; accurate arm geometry

4. **Hamner SR, Seth A, Delp SL (2010).**
   Muscle contributions to propulsion and support during running.
   *Journal of Biomechanics 43(14): 2709-2716.* PMID: 20691972
   - Full body 92 actuators; running-optimized, single torso body

5. **Eskandari AH, Ghezelbash F, Shirazi-Adl A, Arjmand N (2025).**
   Effect of a back-support exoskeleton on internal forces and lumbar spine stability during low load lifting task.
   *Applied Ergonomics 125: 104189.* PMID: 39489061
   - Comprehensive spine model + exoskeleton; box lifting with ES analysis

6. **Hu F, Brouwer N, Tabasi A, Kingma I, van Dijk W (2026).**
   Influence of varied assistance levels provided by a dual-joint active back-support exoskeleton on spinal musculoskeletal loading and kinematics during lifting.
   *Ergonomics.* PMID: 39967340
   - EMG-driven subject-specific model; 15 kg box lifting; L5S1 compression + back muscle moment

7. **Beaucage-Gauvreau E, Robertson WSP, Brandon SCE et al. (2019).**
   Validation of an open-source and toolbox-neutral musculoskeletal model of the lower limb and lumbar spine.
   *Royal Society Open Science 6: 181650.* [LFB model paper]
   - LFB model: 238 muscles, lumbar L1-L5 + lower extremity; validated for load-handling

---

_작성: biomechanics-agent (2026-04-29)_
_로컬 모델 분석 참조: `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/alternative_models_local.md`_
_Reach 진단 참조: `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/thoracolumbar_fb_reach_envelope.md`_
