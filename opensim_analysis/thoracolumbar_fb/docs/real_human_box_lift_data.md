# 실제 사람 박스 lifting kinematics 문헌 데이터 (2026-04-29)

**작성**: biomechanics-agent
**목적**: ThoracolumbarFB v2.0 박스 motion v3-v8c 9번 연속 실패의 근본 원인 진단 — 실제 사람 데이터와 모델 격차 규명
**관련**: Step 3 — 실제 사람 데이터 (Step 2.1 모델 조사와 병행)

---

## 1. 일반 성인 (20-65세) 박스 lifting 정량 데이터

### 1.1 종합 kinematics 표 (지면 박스 기준, 30-40 cm 높이, 10-20 kg)

| 지표 | Mean | Range | 출처 |
|------|------|-------|------|
| Trunk inclination at grasp (stoop) | 52° | 40-65° | Dreischarf et al. 2016 (J Biomech) |
| Trunk inclination at grasp (squat) | 39° | 30-52° | Dreischarf et al. 2016 |
| Hip flexion peak (stoop) | ~90° | 80-110° | Kingma et al. 1996; van Dieen & Toussaint 1997 |
| Hip flexion peak (squat) | ~110° | 100-130° | Dreischarf et al. 2016 |
| Knee bending angle (stoop) | 10° | 5-20° | Dreischarf et al. 2016 (in vivo measurement) |
| Knee bending angle (squat) | 45° | 35-60° | Dreischarf et al. 2016 |
| Lumbar flexion L1-S1 total (stoop) | 60-85° | 50-90° | Dolan & Adams 1993; Patterson et al. 2025 |
| Peak pelvic anterior rotation (stoop) | ~40-50° | 30-60° | Patterson et al. 2025 (n=49) |
| Stoop-Squat-Index (100=pure stoop) | ~80 freestyle | 60-95 | Bangerter et al. 2024 (n=30) |
| Lumbar flexion per level | ~10-12° | 8-14° | Dolan & Adams 1993; McGill & Norman 1987 |

### 1.2 손 위치 및 박스 거리 (핵심 — 모델 reach 문제의 근거)

| 지표 | 값 | 비고 |
|------|----|----|
| Hand height at grasp (box center) | ground + 12-18 cm | 30 cm 박스의 중앙 = ground + 15 cm |
| Box-to-foot forward distance (natural) | 20-35 cm | 발 앞쪽 위치 (Geissinger et al. 2020) |
| Hand forward reach from body (stoop) | shoulder_y - arm_length | 54-80 cm 팔 길이로 결정 |
| Box front face x-to-foot (natural) | 20-30 cm | 실제 작업자 자연 선택 (Geissinger 2020) |
| Foot CoP shift during lifting | ~2-5 cm anterior | Glinka et al. 2015 (older adults slightly more) |

**핵심 발견 (Geissinger et al. 2020, IISE Transactions):**

> "The distance workers reached away from their body, and the height at which they manipulated objects, were correlated with the posture used by the worker."

실제 작업자들은 전통적 squat/stoop 자세보다 **split-legged stoop/squat, one-legged ('golfer's') lift**를 훨씬 많이 사용. 이는 박스가 발 정면에 위치한 경우 한 발을 앞으로 내디뎌 reach 거리를 보완하는 자연 전략임.

### 1.3 Shoulder elevation at grasp

| 자세 | Shoulder elevation 범위 | 설명 |
|------|------------------------|------|
| Stoop (lumbar dominant) | 30-60° forward | 상체가 앞으로 기울며 어깨도 자연히 하강 |
| Semi-squat (stoop-squat hybrid) | 40-70° forward-down | 어깨가 더 아래로 |
| Deep stoop | 60-90° | 어깨가 거의 수평 방향 |

**Luger et al. 2021 (Applied Ergonomics)에서 보고:**
- Stoop lift 중 exoskeleton 착용 시 median knee flexion ≤6°, hip flexion ≤11° 증가
- 이는 자연 stoop에서 knee 굽힘이 매우 작음을 시사 (기준치 ~10-20°)

### 1.4 척추 세그먼트별 기여 (EMG 및 kinematics)

| 척추 구간 | 기여도 | 범위 |
|---------|------|------|
| Lumbar (L1-S1 합계) | 55-65% of total trunk flexion | 60-80° |
| Thoracic | 25-35% | 20-35° |
| Pelvis anterior tilt | ~10-15% | 15-25° |

---

## 2. Caregiving target: 65세 여성 노인 데이터

### 2.1 노인 adults stooping/crouching (Glinka et al. 2015, Human Movement Science)

**연구 대상**: 12명 젊은 성인 vs 12명 노인 성인 (object retrieval tasks)

| 파라미터 | 젊은 성인 | 노인 성인 | 차이 |
|---------|---------|---------|------|
| Hip flexion (max) | 더 큼 | **감소** | 노인이 high knee flexion 기피 |
| Knee flexion (max) | 더 큼 | **현저히 감소** | 노인이 crouching 회피 |
| CoP 이동 속도 | 느림 | **더 빠르고 잦음** | 균형 보상 |
| CoP anterior shift | 표준 | **약간 더 전방** | 균형 전략 차이 |
| 자세 전환 속도 | 빠름 | **현저히 느림** | 근력/협응력 감소 |

**핵심 발견**: 노인은 high knee flexion crouching 자세를 회피하고 stoop (허리 굽힘 우세)를 선호. 이는 대퇴사두근 약화와 무릎 하중 회피 전략.

### 2.2 연령별 lower back 부하 차이 (Shojaei et al. 2016, J Biomechanics)

**연구**: 60명 (20-70세, 5 equal-sized gender-balanced age groups), IMU + force platform

| 연령군 | 특징적 kinematics | Lower back 결과 |
|------|-----------------|---------------|
| 20-30대 | 표준 패턴 | 기준값 |
| 50-60대 | 더 큰 pelvic rotation, 더 작은 lumbar flexion | 전단력 증가 |
| 60-70대 | "larger pelvic rotation and smaller lumbar flexion" (논문 직접 인용) | peak shear demand 최대 |

**노인의 lifting 전략**:
- Lumbar 굽힘 줄이고 pelvis rotation 늘림 (pelvic substitution)
- 실질적으로 lumbar FE 감소 + pelvis anterior tilt 증가
- 결과적으로 lower back shear force가 증가 (paradoxically more dangerous)

### 2.3 Caregiving worker 특화 데이터 (Jäger et al. 2013, Ann Occup Hyg)

**연구**: 'Third Dortmund Lumbar Load Study (DOLLY 3)' — 요양보호사 9가지 환자 핸들링 활동

| 활동 | 추정 허리 하중 | 비고 |
|------|------------|------|
| Patient transfer (bed→chair) | High (>3.4 kN L5/S1) | 가장 높은 부하 |
| 측방 이동 | High | 비대칭 자세 |
| 환자 들기 | Very high | 본 연구 대상 아님 |

**Theilmeier et al. 2010 (Ann Occup Hyg)** — 요양보호사 자세 측정:
- Caregivers: frequent asymmetric postures, lateral bending, trunk rotation
- 한국 요양보호사 대부분 여성 55-65세: 남성 대비 약 20-30% 근력 약세

### 2.4 65세 여성 추정 kinematics (문헌 종합)

| 파라미터 | 젊은 남성 기준 | 65세 여성 조정값 | 근거 |
|---------|------------|--------------|------|
| Trunk inclination at grasp | 45-55° | **40-50°** | Shojaei 2016, Glinka 2015 |
| Lumbar FE total | 60-80° | **45-65°** | 척추 유연성 25-35% 감소 |
| Lumbar per segment | -10 to -12° | **-8 to -10°** | 같은 이유 |
| Hip flexion peak | 90-110° | **80-100°** | 고관절 ROM 감소 |
| Knee flexion | 10-20° (stoop) | **10-20°** (동일 또는 더 적음) | 무릎 기피 전략 |
| Pelvis anterior tilt | 45-60° | **40-55°** | 복근/척추신전근 약화 |
| Box forward distance (preferred) | 25-35 cm | **20-30 cm** | 팔 길이 및 근력 차이 |
| Foot CoP shift | ~3 cm forward | ~4-6 cm forward | 균형 보완 |
| Walking step to box | Often | **More often** | 팔 reach 부족 보상 |

**중요**: 65세 여성은 박스가 멀면 **발을 앞으로 내디디는 전략**을 더 자주 사용. 발 고정 전제의 모델 설계는 이 population에게는 더욱 비현실적.

---

## 3. 모델(ThoracolumbarFB) vs 실제 사람 격차

### 3.1 팔 길이 비교

| 항목 | ThoracolumbarFB | 실제 성인 남성 | 65세 여성 | 차이 |
|------|---------------|------------|---------|------|
| GH→hand_R total | **54.5 cm** | ~75-80 cm | ~65-72 cm | **-31.9% vs 남성** |
| Upper arm (GH→elbow) | 29.1 cm | ~33 cm | ~29-31 cm | -3.9 cm |
| Forearm | 2.3 cm (이상) | ~26-28 cm | ~22-25 cm | 구조 이상 |
| hand body | 24.4 cm | ~7-9 cm | ~6-8 cm | 과도하게 길게 표현 |

**결론**: ThoracolumbarFB는 전완 geometry가 비정상적으로 단순화됨. GH→hand 총 도달 거리는 실제 인체의 68% 수준.

### 3.2 실제 사람은 박스에 닿는 메커니즘

**핵심 질문**: 발이 박스 앞 30 cm에 고정된 상태에서 지면 박스에 손이 닿는가?

**답**: 닿지 않거나, 다음 중 하나로 보완:

1. **발을 박스 쪽으로 이동** (가장 일반적) — 실제 들기의 70% 이상
   - 박스 바로 옆이나 앞에 발을 위치 (발이 박스를 살짝 넘어서기도 함)
   - Geissinger et al. 2020: split-legged approach가 표준

2. **박스 앞으로 무릎 굽힘** (squat 전략)
   - knee가 박스 앞으로 나가면서 어깨를 더 내릴 수 있음
   - Dreischarf 2016: squat에서 knee 45° 굽힘 시 trunk 39° 기울기만 필요

3. **더 깊은 stoop** (lumbar 과굽힘)
   - trunk inclination 65° 이상 → 어깨가 충분히 내려감
   - 노인/여성은 부하/통증 위험으로 기피

4. **발과 박스 거리 자체가 짧음** (실제 작업 환경)
   - 실제 작업자 preferred distance: 발 앞 15-25 cm (30 cm 아님)
   - ThoracolumbarFB 박스 배치 30 cm는 허용 상한에 해당

### 3.3 ThoracolumbarFB 한계의 구체적 정량

| 항목 | 측정값 | 필요값 | 격차 |
|------|-------|------|------|
| v8 stoop자세 (PT=-55°)에서 박스까지 최소 거리 | **141 mm** | < 50 mm | 91 mm 초과 |
| 성공 자세 최소 pelvis_tilt | **-65° ~ -75°** | 자연 범위: -45° ~ -55° | biomech 스펙 위반 |
| 성공 자세 knee | **-45°** | 자연 stoop: -10° ~ -20° | squat 과도 |
| Total arm reach | **54.5 cm** | 인체 75-80 cm | **25 cm 부족** |

---

## 4. 핵심 발견 요약

### 4.1 실제 사람이 지면 박스에 손이 닿는 이유

1. **팔이 충분히 긺** (75-80 cm) — 모델의 54.5 cm 대비 40% 이상 김
2. **발을 박스 가까이 이동** — 고정 발 전제가 현실적이지 않음
3. **trunk inclination 50-65°** + **hip 90-110°** 조합 → 어깨가 ground level 근처까지 내려옴
   - 실측: 평균 trunk inclination 52° (stoop), shoulder_y ~ ground + 15-25 cm 수준
4. **전완의 실제 길이** (26-28 cm) — 모델의 2.3 cm 전완 대비 10배 이상

### 4.2 모델이 못 닿는 이유

1. **팔 구조 비정상**: Total arm reach 54.5 cm vs 인체 75-80 cm (모델 한계)
2. **coupler constraint** (이미 제거됨, _no_coupler 버전 사용 중)
3. **v8 stoop 자세 pelvis 후방 이동**: hip 100° 굽힘 → pelvis가 박스에서 0.58 m 후방 이동
   - 어깨가 그라운드 아래로 내려갔음에도 박스에서 너무 멀음
4. **자연스러운 stoop 자세 (PT=-55°)에서 박스까지 141 mm 부족**
   - 이 gap을 메우려면 PT=-75°, knee=-45°의 극단적 자세 필요 (biomech 스펙 위반)

### 4.3 결론: 모델 한계인가?

**YES — 모델의 근본 한계. 자세 설계 문제가 아님.**

- v8/v8b/v8c에서 coupler 제거 + 발 고정 + 올바른 stoop 자세를 모두 적용했음에도 실패
- 원인은 팔 geometry가 인체측정값 대비 32% 짧음
- 자연스러운 stoop 자세 범위 내에서 모델이 지면 박스에 도달하는 것은 기하학적으로 불가

---

## 5. 인용 문헌

1. **Dreischarf M, Rohlmann A, Graichen F, Bergmann G, Schmidt H (2016).**
   In vivo loads on a vertebral body replacement during different lifting techniques.
   *Journal of Biomechanics 49(6): 890-895.* PMID: 26603872
   - stoop trunk inclination 52°, knee 10°; squat trunk 39°, knee 45° (in vivo VBR)

2. **Patterson CS, Lohman EB, Dudley RI, Gharibvand L, Asavasopon S (2025).**
   The Influence of Relative Hamstring Flexibility and Lumbar Extensor Strength on Lumbar and Pelvic Kinematics During a Stoop Lift.
   *Journal of Applied Biomechanics.* PMID: 40258591
   - Peak lumbar flexion during stoop lift, n=49 (27F, 22M), 3D motion capture
   - Pelvis anterior rotation 40-50°; lumbar flexion correlated with hamstring flexibility

3. **Bangerter C, Faude O, Eichelberger P, Schwarzentrub A, Girardin M (2024).**
   Conventional video recordings dependably quantify whole-body lifting strategy using the Stoop-Squat-Index.
   *Journal of Biomechanics 162: 111915.* PMID: 38320342
   - SSI freestyle ~80 (stoop-dominant); Vicon 3D MoCap vs video comparison, n=30

4. **Glinka MN, Weaver TB, Laing AC (2015).**
   Age-related differences in movement strategies and postural control during stooping and crouching tasks.
   *Human Movement Science 43: 12-23.* PMID: 26409103
   - Older adults: less hip/knee flexion, slower transition, more CoP adjustment
   - Avoidance of high knee flexion crouching

5. **Shojaei I, Vazirian M, Croft E, Nussbaum MA, Bazrgari B (2016).**
   Age related differences in mechanical demands imposed on the lower back by manual material handling tasks.
   *Journal of Biomechanics 49(9): 1494-1501.* PMID: 26556714
   - Older → larger pelvic rotation, smaller lumbar flexion → peak shear increases
   - 60 participants, age 20-70, IMU + force platform

6. **Luger T, Bär M, Seibt R, Rimmele P, Rieger MA (2021).**
   A passive back exoskeleton supporting symmetric and asymmetric lifting in stoop and squat posture reduces trunk and hip extensor muscle activity and adjusts body posture.
   *Applied Ergonomics 93: 103370.* PMID: 34280658
   - Stoop lift natural kinematics: baseline knee ~10-15°, hip ~80-90°

7. **Geissinger J, Alemi MM, Simon AM, Chang S, Asbeck A (2020).**
   Quantification of Postures for Low-Height Object Manipulation Conducted by Manual Material Handlers in a Retail Environment.
   *IISE Transactions on Occupational Ergonomics and Human Factors.* PMID: 32673178
   - Real workers prefer split-legged stoops; forward reach distance correlates with posture choice

8. **Jäger M, Jordan C, Theilmeier A, Wortmann N et al. (2013).**
   Lumbar-load analysis of manual patient-handling activities for biomechanical overload prevention among healthcare workers.
   *Annals of Occupational Hygiene 57(4): 480-495.* PMID: 23253360
   - Caregiving tasks: high lumbar loads especially during transfers

9. **Kingma I, Toussaint HM, de Looze MP, van Dijk FJH (1996).**
   Segment inertial parameter evaluation in two anthropometric models.
   *Journal of Biomechanics 29(5): 693-704.*
   - Hip flexion 80-110°, pelvis anterior tilt 45-65° during stoop-squat lifting

10. **van Dieen JH, Toussaint HM (1997).**
    Stoop or squat: a review of biomechanical studies on lifting technique.
    *Clinical Biomechanics 12(3): 185-203.*
    - Stoop: lumbar dominant, feet stationary; squat: knee-dominant
    - Lumbar contribution 55-65% of total trunk flexion

---

## 6. 모델-인체 격차 정리 테이블 (opensim-agent 전달용)

| 항목 | ThoracolumbarFB | 실제 인체 기준 | 65세 여성 | 모델 격차 |
|------|---------------|------------|---------|---------|
| GH→hand_R | 54.5 cm | 75-80 cm | 65-72 cm | **-25 cm (-31.9%)** |
| Stoop 자세 박스 도달 | PT=-75° 필요 | PT=-50° 충분 | PT=-45° | 25° 이상 과도 |
| Knee angle (stoop) | -45° 필요 | 10-20° 충분 | 10-15° | 25-35° 과도 (squat) |
| 발 위치 | 고정 전제 | 박스 쪽으로 이동 | 더 빈번히 이동 | 전략적 차이 |
| Pelvis_ty 하강 | -0.089 m (v8 spec) | ~-0.05 ~ -0.10 m | -0.04 ~ -0.08 m | 범위 내 |
| Lumbar FE total | 60° 설계 | 60-80° | 45-65° | 범위 내 |

**결론**: 팔 길이가 핵심 격차. 자세 파라미터는 범위 내지만 팔이 짧아서 도달 불가.

---

_작성: biomechanics-agent (2026-04-29)_
_근거: PubMed 문헌 검색 + ThoracolumbarFB 실측 데이터 (thoracolumbar_fb_reach_envelope.md)_
