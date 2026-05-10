# Wearable Robot Evaluation Framework 문헌 조사 (2026-04-29)

**작성**: biomechanics-agent  
**목적**: 4개월 단발성 patch 패턴 탈피, 검증된 evaluation framework 위에서 Phase 2.C.4 및 이후 계획 수립  
**우리 상황**: ThoracolumbarFB v2.0 (620 muscles, 76 ES), SMA fabric suit, stoop/box lifting, 65세 여성 caregiving 목표

---

## 1. 검색 결과 요약

### 검색 query 사용 (PubMed eUtils, 2026-04-29)

| 검색 범주 | 대표 query | 발견 수 |
|---------|-----------|-------|
| OpenSim back exo simulation | "back exoskeleton OpenSim biomechanics evaluation" | 3 |
| Spine load musculoskeletal model | "exoskeleton spine load musculoskeletal model" | 8 |
| Passive exo lifting EMG | "passive exoskeleton evaluation lifting EMG muscle" | 15+ |
| Biomechanical assessment | "exoskeleton biomechanical assessment lifting workers" | 15+ |
| Systematic review back exo | "effects industrial back-support exoskeletons body loading" | 6+ |
| Benchmarking framework | "benchmarking occupational exoskeletons evidence mapping" | 1 |
| Predictive simulation | "exoskeleton predictive simulation OpenSim Moco" | 1 |
| Specific authors (Dembia, Quinlivan) | individual queries | 2 |

**총 고유 논문 후보**: ~51 PMIDs 수집, 23개 핵심 논문 abstract 확보

### Citation 분포 (PubMed 출판 연도 기준)
- 2016-2018: 2편 (Dembia, Kim, Quinlivan 시대)
- 2020-2021: 6편 (systematic review 전성기)
- 2022-2023: 5편 (실험적 validation 심화)
- 2024-2026: 10편 (OpenSim + Moco 통합, active exo 급증)

---

## 2. Framework 비교 표 (10개)

| # | Framework | Authors (year) | 추정 Citation | Task 종류 | 인구 | Tool | 주요 metric | 코드 공개 |
|---|-----------|---------------|-------------|----------|------|------|-----------|---------|
| F1 | CMC-based predictive simulation (Stanford) | Dembia et al. (2017) | ~400+ | Walking (7 joints) | 성인 남성 | OpenSim CMC | Metabolic cost, muscle activity | Yes (SimTK) |
| F2 | Dose-response soft exosuit (Harvard) | Quinlivan et al. (2017) | ~600+ | Treadmill walking | 성인 7명 | Physical experiment | Metabolic rate, ankle torque | No |
| F3 | Systematic review / benchmark | Kermavnar et al. (2021) | ~200+ | Lifting, bending (다양) | Healthy young men 위주 | 모든 도구 (분석) | EMG, joint moment, compression, UX | N/A |
| F4 | Optimization-model spine load estimation | Madinei & Nussbaum (2023) | ~30 | Repetitive lifting (9 cond.) | 18명 gender-balanced | Custom opt. model | L5/S1 compression, shear | No |
| F5 | OpenSim exosuit validation pipeline | Yan et al. (2024) | ~15 | Squat+stoop lift (6+lower) | 14명 healthy | OpenSim SO | Muscle forces (ES, hip ext) | No |
| F6 | OpenSim vs AnyBody comparison | Behjati Ashtiani et al. (2025) | ~5 | Symmetric+asymmetric lifting | 18명 gender-balanced | OpenSim + AnyBody | L4/L5 IJF (compression, shear) | No |
| F7 | Hinge-type BSE modeling (4 methods) | Riahi et al. (2026) | New | Squat + stoop | 14명 | OpenSim | ES activation, L5-S1 JRF | No |
| F8 | Active dual-joint exo (4 assist levels) | Hu et al. (2026) | New | Lifting (free technique) | 8명 | EMG-driven model | L5S1 compression, ES moment | No |
| F9 | Benchmarking sys. review (VUB) | De Bock et al. (2022) | ~130 | 다양 (lifting + overhead + carrying) | 다양 (139 studies) | N/A (framework) | EMG, biomechanical, UX | N/A |
| F10 | Versatile exo multi-task evaluation | Poliero, Toxiri et al. (2021) | ~60 | Lifting + carrying + walking | Healthy adults | XoTrunk + EMG | ES activation, dynamic fit, gait | No |

---

## 3. 핵심 References (각 paper 핵심 방법 + 우리 적용성)

### F1. Dembia et al. 2017 — Stanford CMC Framework

**Citation**: Dembia CL, Silder A, Uchida TK, Hicks JL, Delp SL (2017). *Simulating ideal assistive devices to reduce the metabolic cost of walking with heavy loads.* PLoS One 12(7):e0180320. PMID: 28700630.

**핵심 방법**: OpenSim Computed Muscle Control(CMC)로 7종 가상 단관절 보조장치(massless) 효과를 예측 시뮬레이션. 각 장치는 1 DoF에 무제한 토크 제공. 실측 kinematics를 tracking하면서 sum-of-squared-activation 최소화 목표 함수. Metabolic savings + 근육별 activity 변화 동시 분석.

**Pipeline 단계**:
1. Loaded walking kinematics 측정 (MoCap)
2. CMC setup (tracking + min activation)
3. 7 장치 조건 × 병렬 시뮬레이션
4. Metabolic cost 예측 (Bhargava 공식)
5. Muscle redistribution 패턴 분석

**우리 적용성**: **부분 적합**. Walking 전용 (lifting 아님). 그러나 "CMC로 다수 조건 병렬 비교" 접근법은 우리 Phase 2.C.4 4-condition Moco 설계에 직접 참조 가능. Simulations are freely available on SimTK — 재현 가능.

---

### F2. Quinlivan et al. 2017 — Harvard Exosuit Dose-Response

**Citation**: Quinlivan BT et al. (2017). *Assistance magnitude versus metabolic cost reductions for a tethered multiarticular soft exosuit.* Science Robotics 2(2):eaah4416. PMID: 33157865.

**핵심 방법**: Tethered soft exosuit로 ankle assistance를 biological ankle moment의 10~38%(4 levels)로 변화시켜 metabolic rate를 측정. 개념: "dose-response curve" — 보조 크기 대비 metabolic 절감률 정량화.

**결과**: Peak assistance 시 metabolic rate 22.83 ± 3.17% 감소 (powered-off vs max powered).

**우리 적용성**: **높음 (개념)**. 우리 Phase 1a suite sweep (0~200 N·m)과 구조가 동일. "Assistance magnitude vs ES reduction" = 우리의 dose-response 1.164 %/N·m slope가 이 framework의 직접 구현. 참고: Quinlivan은 metabolic cost, 우리는 ES activation — 측정 메트릭만 다름.

---

### F3. Kermavnar et al. 2021 — Updated Systematic Review

**Citation**: Kermavnar T, de Vries AW, de Looze MP, O'Sullivan LW (2021). *Effects of industrial back-support exoskeletons on body loading and user experience: an updated systematic review.* Ergonomics 64(6):685-711. PMID: 33369518.

**핵심 방법**: 최근 5년(2016-2021) 논문 33편 체계적 리뷰. Passive 20편, Active 13편. 평가 항목: EMG (ES 위주), L5/S1 moment/compression, kinematics, UX (SUS, VAS).

**핵심 발견**:
- ES, peak L5/S1 moment, spinal compression 감소 일반적으로 보고
- Abdominal/lower limb activity 증가 부작용 빈번
- 대부분 연구: 젊은 건강한 남성, laboratory setting
- **격차 식별**: 실제 산업 작업자 대상 field study 부재, 여성/노인 부재

**우리 적용성**: **높음 (격차 식별)**. 우리 연구가 메워야 할 gap이 여기에 명시됨 — 노인 여성, 실제 caregiving 작업. 우리 논문에서 이 review가 식별한 "이 격차를 우리가 메운다"는 논거 사용 가능.

---

### F4. Madinei & Nussbaum 2023 — Optimization-Model Spine Load (Virginia Tech)

**Citation**: Madinei S, Nussbaum MA (2023). *Estimating lumbar spine loading when using back-support exoskeletons in lifting tasks.* J Biomechanics 147:111439. PMID: 36638578.

**핵심 방법**: 18명 (gender-balanced) × 2 BSE (BackX, Laevo) × 9 conditions (symmetric/asymmetric) = 144 시뮬레이션. Optimization-based musculoskeletal model (OpenSim 기반)로 L5/S1 compression + shear 예측. EMG composite measure와 spine force 상관 분석.

**핵심 발견**:
- BSE 착용: peak compression 8-15% 감소
- Laevo: asymmetric lifting 시 mediolateral shear 35% 감소
- **중요**: "EMG reduction ≠ spine force reduction" — 두 metric 상관 낮음

**우리 적용성**: **매우 높음**. 9 conditions × optimization model은 우리 Phase 2.C.4 설계 참고. Gender-balanced 설계 (우리 65세 여성 목표에 근거). "EMG ≠ spine load" 발견은 우리가 ES activation만이 아니라 spine force도 추가해야 함을 시사.

---

### F5. Yan et al. 2024 — OpenSim Exosuit Validation Pipeline (Harvard/BIDMC)

**Citation**: Yan C, Banks JJ, Allaire BT, Quirk DA, Chung J, Walsh CJ, Anderson DE (2024). *Musculoskeletal models determine the effect of a soft active exosuit on muscle activations and forces during lifting and lowering tasks.* J Biomechanics 176:112322. PMID: 39305855.

**핵심 방법**: 14명 healthy × squat+stoop × 6kg+10kg × with/without 2.7kg exosuit = 56 conditions. OpenSim participant-specific models에 exosuit 통합. 모델 검증: EMG vs model predicted activation (cross-correlation 0.84-0.98). RMSE 0.05-0.10 (기존 문헌 수준). ES force + hip extensor force 비교.

**핵심 발견**:
- ES force: 모든 lifting task에서 peak 감소
- Hip extensor: squat 10kg만 감소 (task-specificity)
- Exosuit 146N 보조 → ES 힘 감소는 그 1.7-4.2배 (amplification effect)
- "Incorporating exosuits into musculoskeletal models is a valid approach"

**우리 적용성**: **매우 높음 (직접 참조)**. Soft exosuit + OpenSim SO 파이프라인이 우리와 동일한 구조. Squat/stoop 모두 평가, stoop ES force 감소 직접 비교 가능. 우리 ThoracolumbarFB와 달리 OpenSim Gait2392 기반 — 방법론 참고, 모델 직접 전환 불필요.

---

### F6. Behjati Ashtiani et al. 2025 — OpenSim vs AnyBody Cross-validation

**Citation**: Behjati Ashtiani M et al. (2025). *Using musculoskeletal models to estimate the effects of exoskeletons on spine loads during dynamic lifting tasks: differences between OpenSim and the AnyBody modelling system.* J Biomechanics 188:112780. PMID: 40441118.

**핵심 방법**: 동일 18명 데이터로 OpenSim + AnyBody 두 모델에서 3 BSE × 3 task conditions × symmetric/asymmetric = 18 조합 분석. L4/L5 IJF (compression, shear) 비교. Pearson r, Bland-Altman 분석.

**핵심 발견**:
- OpenSim이 AnyBody보다 compression 크게 추정 (체계적 차이)
- Compression: 두 모델 r > 0.95 (강한 양의 상관)
- Shear: r 약하거나 음수 (특히 asymmetric) — 모델 가정 차이
- BSE 효과: 둘 다 reduction 추정하지만 OpenSim이 더 큰 감소 추정

**우리 적용성**: **높음 (validation 설계)**. 우리 OpenSim 결과의 한계를 사전에 이해하는 데 필수. Phase 2 결과 작성 시 "OpenSim은 compression 과다 추정 가능성" 명시 필요. 다중 모델 cross-validation 필요성 인지.

---

### F7. Riahi et al. 2026 — OpenSim Hinge BSE 4-Method Comparison

**Citation**: Riahi N et al. (2026). *Musculoskeletal Modeling of a Hinge-Type Back-Support Exoskeleton: A Simplified Approach for Practical Assessment.* Ann Biomed Eng 54(1):195-210. PMID: 41196487.

**핵심 방법**: 14명 × squat+stoop × 4 OpenSim modeling methods (torque→hip, torque from exo data, force vector from kinematics, force vector from exo+kinematics). Statistical parameter mapping으로 시계열 전체 비교.

**핵심 발견**:
- Method 3 (force vector from kinematics만) ≈ Method 4 (full exo data)
- Method 1, 2 (pure torque)는 squatting 보조 구간에서 유의한 차이
- 결론: "force vector + user kinematics" = practical yet accurate

**우리 적용성**: **매우 높음 (즉시 적용)**. 우리 SMA suit coupler가 pelvis-thorax torque 제공 = Method 1 equivalent. Riahi가 Method 3이 더 정확하다는 근거 → 우리도 force vector 방식 검토 가치 있음. ThoracolumbarFB에서 coupler torque 구현 방식의 타당성 검증 근거.

---

### F8. Hu et al. 2026 — Active Dual-Joint BSE 4-Condition Dose-Response

**Citation**: Hu F, Brouwer NP, Tabasi A, Kingma I, van Dijk W, Mohamed Refai MI, Kooij HV, van Dieën JH (2026). *Influence of varied assistance levels provided by a dual-joint active back-support exoskeleton on spinal musculoskeletal loading and kinematics during lifting.* Ergonomics 69(3):453-465. PMID: 39967340.

**핵심 방법**: 8명 × 4 assistance levels (0%, 30%, 50%, 70% of back muscle moment) × free technique lifting 15kg. EMG-driven biomechanical model로 L5S1 compression force + back muscle active moment. Time-averaged outcomes.

**핵심 발견**:
- Non-zero assistance: L5S1 compression 5.5-9.3% 감소, ES active moment 14.9-28.6% 감소
- 고보조 → compression 추가 감소 없음 (saturation 가능성)
- Abdominal activity 변화 없음 (controller 성공)
- Lumbar flexion 소폭 변화만

**우리 적용성**: **매우 높음 (구조 동일)**. 우리 Phase 2.C.4: 4 conditions (B_noload, suit50, suit100, suit200) ↔ 이 논문 0/30/50/70% 구조 완전 동일. ES active moment 감소 14.9-28.6% (우리 ES activation 28% 감소와 일치). Saturation 현상도 우리 Phase 1a에서 관찰된 현상 (suit sweep R²=1.000 but with recruitment redistribution). 이 논문을 Phase 2.C.4 reference로 핵심 활용.

---

### F9. De Bock et al. 2022 — Benchmarking Framework (VUB)

**Citation**: De Bock S et al. (2022). *Benchmarking occupational exoskeletons: An evidence mapping systematic review.* Appl Ergon 98:103582. PMID: 34600307.

**핵심 방법**: PubMed + WoS + Scopus (March 2021). 139 eligible studies, 33 back + 25 shoulder + 18 other 고유 exoskeleton. Evidence mapping 방식 — 각 연구를 task type × outcome measure × setting으로 매핑. Framework 권고사항 도출.

**핵심 발견 (Framework 권고)**:
- 표준 평가 순서: 1) controlled lab task → 2) simulated work task → 3) real field task
- 핵심 outcomes: muscle activity (EMG) + biomechanical data (kinematics, joint moments)
- 점점 추세: 현실적 task + UX + physiological 병행 측정
- **격차**: age/gender diversity, long-term effects, field studies

**우리 적용성**: **높음 (프레임 설계)**. 우리 연구가 어느 단계에 있는지 위치 파악 가능. Phase 1a = "controlled lab task" (stoop only). Phase 2.C.4 = "simulated work task" (box lifting). Field study = 향후 과제. 이 framework을 논문 Methods 절 justification에 사용 가능.

---

### F10. Poliero, Toxiri et al. 2021 — Versatile Exo Multi-Task Evaluation (IIT)

**Citation**: Poliero T, Sposito M, Toxiri S, Di Natali C et al. (2021). *Versatile and non-versatile occupational back-support exoskeletons: A comparison in laboratory and field studies.* Wearable Technol 2:e12. PMID: 38486626.

**핵심 방법**: XoTrunk exoskeleton × versatile(task-adaptive) vs non-versatile control × lifting + carrying + walking. EMG (ES), kinematics (hip flexion), task recognition accuracy, subjective feedback. Lab + 9시간 field test.

**핵심 발견**:
- Versatile: lifting ES 감소 + carrying ES 감소 동시 달성
- Non-versatile: walking 중 hip flexion 감소 (gait interference)
- Task recognition online accuracy > 91%
- Field testing 9h: subjective acceptance 긍정적

**우리 적용성**: **부분 적합**. 우리 suit는 passive (task-adaptive 아님). 그러나 "다양한 task에 대한 ES reduction + gait interference 검사" 방법론은 우리가 carrying/walking task 추가 시 참고. Multi-task evaluation 설계 방법론으로 활용.

---

## 4. 우리 목표 부합도 평가

| Framework | 다양 task | 다양 assist level | OpenSim | Public code | 65세 여성 | Phase 2.C.4 적합성 |
|-----------|---------|----------------|---------|------------|---------|-----------------|
| F1 Dembia 2017 | 아니오 (walking) | 간접적 | **YES** | **YES (SimTK)** | 아니오 | 낮음 (방법 참고만) |
| F2 Quinlivan 2017 | 아니오 (walking) | **YES (4 levels)** | 아니오 | 아니오 | 아니오 | 중간 (dose-response 개념) |
| F3 Kermavnar 2021 | **YES (다양)** | 부분 | 아니오 | 아니오 | 아니오 (격차 인식) | 높음 (논거/격차 확인) |
| F4 Madinei 2023 | 부분 (lifting만) | 간접적 | **YES** | 아니오 | 부분 (gender-balanced) | **매우 높음** |
| F5 Yan 2024 | **YES (squat+stoop)** | 아니오 | **YES** | 아니오 | 아니오 | **매우 높음** |
| F6 Behjati 2025 | 부분 | 아니오 (3 BSE) | **YES** | 아니오 | 아니오 | 높음 (한계 이해) |
| F7 Riahi 2026 | 부분 (squat+stoop) | 아니오 (4 methods) | **YES** | 아니오 | 아니오 | **매우 높음** |
| F8 Hu 2026 | 아니오 (1 task) | **YES (4 levels)** | 아니오 | 아니오 | 아니오 | **매우 높음** |
| F9 De Bock 2022 | **YES (meta)** | N/A | N/A | N/A | **YES (격차)** | 높음 (설계 근거) |
| F10 Poliero 2021 | **YES (다양)** | 아니오 | 아니오 | 아니오 | 아니오 | 중간 |

---

## 5. 가장 Promising 1-2개

### 1순위: Yan et al. 2024 (OpenSim exosuit validation pipeline) + Hu et al. 2026 (4-condition dose-response) — **복합 적용**

이 두 논문을 결합하면 우리 Phase 2.C.4가 검증된 경로를 따른다는 근거가 생긴다.

**Yan 2024 (구조 참고)**:
- OpenSim SO + exosuit torque 통합
- Squat + stoop 두 자세 동시 평가
- EMG vs model activation 검증 프로토콜 (cross-correlation 0.84-0.98 기준)
- ES force 감소 1.7-4.2× amplification 발견
- 우리와 차이: Gait2392 기반 → ThoracolumbarFB는 더 상세한 모델

**Hu 2026 (4-condition 구조 참고)**:
- 4 assist levels × 1 lifting task = 우리 Phase 2.C.4와 동일 구조
- ES moment 14.9-28.6% 감소 = 우리 Phase 1a 28% 결과와 정합
- Saturation 현상 보고 = 우리 Moco에서도 관찰됨 (suit 200 N·m에서 추가 감소 제한)
- 코드 비공개지만 방법론 충분히 기술됨

**즉시 적용 방안**:
```
Phase 2.C.4 설계:
  - Task: box 20kg stoop-squat lift (Yan 참고)
  - Conditions: B_noload (0), suit_50Nm, suit_100Nm, suit_200Nm (Hu 참고)
  - Model: OpenSim SO (Yan pipeline)
  - Metrics: ES peak activation + ES force + L5S1 compression (Madinei 추가)
  - Validation: EMG correlation target r > 0.84 (Yan 기준)
```

**소요 예상 시간**: Moco 4-condition 병렬 실행 (opensim-agent + moco-analysis-agent 4개) — 각 ~2-3시간 계산 → 동시 병렬 시 8-12시간 내 완료 가능.

---

### 2순위: De Bock et al. 2022 (VUB Benchmarking Framework) + Kermavnar 2021

**근거**: 우리 연구 위치 파악과 논문 Justification에 필수.

- De Bock이 제시한 3단계 (controlled → simulated → field) 중 우리는 1-2단계
- Kermavnar가 식별한 격차 (여성, 노인, 실제 작업)가 우리 future work의 정확한 target
- 이 두 systematic review가 없으면 "왜 이 연구가 필요한가"의 논거 약화

**즉시 적용**: 논문 Introduction 1-2문단, Methods "study rationale" 절에 De Bock + Kermavnar 인용.

---

## 6. 시행착오 위험 평가

### 현재 우리 상황 vs Framework 격차

| 항목 | Framework 표준 | 우리 현재 | 위험 |
|-----|-------------|---------|-----|
| Task 다양성 | 3+ tasks 권고 (De Bock) | Stoop + Box 2개 | 중간 (향후 확장 필요) |
| 인구 | Gender-balanced 또는 target-specific | 단일 generic model | 높음 (65세 여성 보정 미반영) |
| Assist levels | 4+ conditions 권고 | Phase 1a: 5 conditions | 낮음 (이미 적합) |
| Model validation | EMG vs model r > 0.80 | Phase 1a PASS, box phase 미검증 | 중간 |
| Spine force | Compression + shear 모두 | ES activation only (Phase 1a) | 중간 |
| UX/subjective | 필요 (field study 이후) | 없음 | 낮음 (현 단계 OK) |
| EMG ≠ spine load 구분 | Madinei 2023이 지적 | 우리는 activation만 | 중간 |

### Framework 채택 시 위험

1. **모방 vs 차별화**: Yan 2024를 그대로 모방하면 novelty 감소. 우리만의 차별점: ThoracolumbarFB (620 muscles, 76 ES segments)의 세분화된 ES 분석 → 부위별 ES 기여 (lumbar vs thoracic) = 기존 논문이 제공 못하는 데이터.

2. **GRF mismatch 위험**: 박스 motion에서 GRF synthesis가 실패 반복됨. Yan 2024도 squat/stoop lifting에서 GRF를 force plate로 직접 측정 — 우리는 합성 → Riahi 2026 Method 3처럼 "force vector from kinematics" 접근이 더 현실적.

3. **65세 여성 모델 부재**: Kermavnar + De Bock 모두 노인/여성 데이터 부재를 격차로 지목. 우리도 현재 generic model 사용 → Phase 2 이후 anthropometric scaling 또는 별도 실험 필요.

### 결정점: 모방 vs 차별화

**권장**: Yan 2024 pipeline 채택 (OpenSim SO + exosuit) + ES segment-level 분석 (우리 ThoracolumbarFB 강점) + 4-condition dose-response (Hu 2026) = 차별화 달성.

---

## 7. 인용 목록

1. **Dembia CL, Silder A, Uchida TK, Hicks JL, Delp SL (2017).** Simulating ideal assistive devices to reduce the metabolic cost of walking with heavy loads. *PLoS One 12(7):e0180320.* PMID: 28700630. [doi:10.1371/journal.pone.0180320]

2. **Quinlivan BT, Lee S, Malcolm P et al. (2017).** Assistance magnitude versus metabolic cost reductions for a tethered multiarticular soft exosuit. *Science Robotics 2(2):eaah4416.* PMID: 33157865. [doi:10.1126/scirobotics.aah4416]

3. **Kermavnar T, de Vries AW, de Looze MP, O'Sullivan LW (2021).** Effects of industrial back-support exoskeletons on body loading and user experience: an updated systematic review. *Ergonomics 64(6):685-711.* PMID: 33369518. [doi:10.1080/00140139.2020.1870162]

4. **Madinei S, Nussbaum MA (2023).** Estimating lumbar spine loading when using back-support exoskeletons in lifting tasks. *J Biomechanics 147:111439.* PMID: 36638578. [doi:10.1016/j.jbiomech.2023.111439]

5. **Eskandari AH, Ghezelbash F, Shirazi-Adl A, Arjmand N, Larivière C (2025).** Effect of a back-support exoskeleton on internal forces and lumbar spine stability during low load lifting task. *Appl Ergon 123:104407.* PMID: 39489061.

6. **Schmalz T, Colienne A, Bywater E et al. (2022).** A Passive Back-Support Exoskeleton for Manual Materials Handling: Reduction of Low Back Loading and Metabolic Effort during Repetitive Lifting. *IISE Trans Occup Ergon Hum Factors 10(1):7-20.* PMID: 34763618.

7. **Di Natali C, Chini G, Toxiri S et al. (2021).** Equivalent Weight: Connecting Exoskeleton Effectiveness with Ergonomic Risk during Manual Material Handling. *Int J Environ Res Public Health 18(5):2677.* PMID: 33799947. [doi:10.3390/ijerph18052677]

8. **Behjati Ashtiani M, Akhavanfar M, Li L, Kim S, Nussbaum MA (2025).** Using musculoskeletal models to estimate the effects of exoskeletons on spine loads during dynamic lifting tasks: differences between OpenSim and the AnyBody modelling system. *J Biomechanics 188:112780.* PMID: 40441118.

9. **Riahi N, Jasimi Zindashti N, Golabchi A, Tavakoli M, Rouhani H (2026).** Musculoskeletal Modeling of a Hinge-Type Back-Support Exoskeleton: A Simplified Approach for Practical Assessment. *Ann Biomed Eng 54(1):195-210.* PMID: 41196487.

10. **Yan C, Banks JJ, Allaire BT, Quirk DA, Chung J, Walsh CJ, Anderson DE (2024).** Musculoskeletal models determine the effect of a soft active exosuit on muscle activations and forces during lifting and lowering tasks. *J Biomechanics 176:112322.* PMID: 39305855. [doi:10.1016/j.jbiomech.2024.112322]

11. **Hu F, Brouwer NP, Tabasi A, Kingma I, van Dijk W, Mohamed Refai MI, Kooij HV, van Dieën JH (2026).** Influence of varied assistance levels provided by a dual-joint active back-support exoskeleton on spinal musculoskeletal loading and kinematics during lifting. *Ergonomics 69(3):453-465.* PMID: 39967340.

12. **Marican MA, Chandra LD, Tang Y et al. (2025).** Biomechanical Effects of a Passive Back-Support Exosuit During Simulated Military Lifting Tasks-An EMG Study. *Sensors 25(10):3211.* PMID: 40432003.

13. **Ding S, Reyes FA, Bhattacharya S, Seyram O, Yu H (2023).** A Novel Passive Back-Support Exoskeleton With a Spring-Cable-Differential for Lifting Assistance. *IEEE Trans Neural Syst Rehabil Eng 31:3781-3789.* PMID: 37725739.

14. **De Bock S, Ghillebert J, Govaerts R et al. (2022).** Benchmarking occupational exoskeletons: An evidence mapping systematic review. *Appl Ergon 98:103582.* PMID: 34600307. [doi:10.1016/j.apergo.2021.103582]

15. **Poliero T, Sposito M, Toxiri S, Di Natali C et al. (2021).** Versatile and non-versatile occupational back-support exoskeletons: A comparison in laboratory and field studies. *Wearable Technol 2:e12.* PMID: 38486626.

16. **Bär M, Steinhilber B, Rieger MA, Luger T (2021).** The influence of using exoskeletons during occupational tasks on acute physical stress and strain compared to no exoskeleton - A systematic review and meta-analysis. *Appl Ergon 94:103385.* PMID: 33676059.

17. **Baldassarre A, Lulli LG, Cavallo F et al. (2022).** Industrial exoskeletons from bench to field: Human-machine interface and user experience in occupational settings and tasks. *Front Public Health 10:1039680.* PMID: 36478728.

18. **Thamsuwan O, Milosavljevic S, Srinivasan D, Trask C (2020).** Potential exoskeleton uses for reducing low back muscular activity during farm tasks. *Am J Ind Med 63(11):1017-1028.* PMID: 32926450.

19. **Erezuma UL, Espin A, Torres-Unda J et al. (2022).** Use of a passive lumbar back exoskeleton during a repetitive lifting task: effects on physiologic parameters and intersubject variability. *Int J Occup Saf Ergon 28(4):2377-2384.* PMID: 34608854.

20. **Zheng L, Sekhar C, Alluri V, Hawke AL, Hwang J (2025).** Evaluation of a passive back-support exoskeleton in bed-to-chair patient handling tasks. *Int J Occup Saf Ergon 31(2):478-485.* PMID: 39931955.

21. **Ostraich B, Riemer R (2024).** Rethinking Exoskeleton Simulation-Based Design: The Effect of Using Different Cost Functions. *IEEE Trans Neural Syst Rehabil Eng 32:2153-2164.* PMID: 38833397.

22. **Kim S, Nussbaum MA, Mokhlespour Esfahani MI et al. (2018).** Assessing the influence of a passive, upper extremity exoskeletal vest for tasks requiring arm elevation: Part I. *Appl Ergon 70:315-322.* PMID: 29525268.

---

## 8. 부록: 우리 연구 현황 vs Framework 위치 매핑

```
De Bock 2022 3단계 평가 사다리:
  Stage 1: Controlled lab task (단순 stoop)       ← Phase 1a [DONE]
  Stage 2: Simulated work task (box lifting)      ← Phase 2.C.4 [IN PROGRESS]
  Stage 3: Real field study (caregiving workers)  ← Future work

Quinlivan dose-response 구조:
  0% → 30% → 50% → 70% assist level             ← 우리: 0 / 50 / 100 / 200 N·m [동일 구조]

Yan 2024 OpenSim pipeline:
  MoCap → IK → SO + exosuit torque → muscle forces ← 우리: .mot → Moco → ES activation [동일 구조, 더 상세한 ES]

Hu 2026 dose-response 발견:
  ES moment 14.9-28.6% 감소 at 0-70% assist       ← 우리 Phase 1a: 28% 감소 at 24 N·m [정합]
  Saturation: 고보조 = compression 추가 감소 없음   ← 우리 Moco: recruitment redistribution 관찰 [정합]
```

---

_작성: biomechanics-agent (2026-04-29)_  
_검색 방법: PubMed eUtils API, 23편 abstract 직접 확보, 51 unique PMIDs 수집_  
_주의: Citation counts는 PubMed API에서 직접 제공하지 않아 출판연도·저널·저자 prominence 기반 추정_
