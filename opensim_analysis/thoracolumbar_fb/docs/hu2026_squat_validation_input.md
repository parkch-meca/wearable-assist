# Hu 2026 Squat Validation Input

**작성일**: 2026-05-26
**작성**: literature-agent (Day 2 작업 4)
**목적**: Hu 2026 (PMID 39967340)의 squat 단독 결과 정밀 추출 + 부족 시 대안 squat-specific paper로 validation criteria 보강
**산출**: validation_protocol_v2.md §3 (Day 4 작성) 입력 자료

---

## 1. Hu 2026 정밀 재검토

### Citation
Hu F, Brouwer NP, Tabasi A, et al. **Influence of varied assistance levels provided by a dual-joint active back-support exoskeleton on spinal musculoskeletal loading and kinematics during lifting**. *Ergonomics* 2026;69(3):453–465. doi:10.1080/00140139.2025.2466030 (PMID 39967340)

### Lifting style
- **"Free technique"** — 참여자가 squat/stoop 자유 선택
- ⚠️ **Squat 단독 결과 명시 없음** — pooled (free-technique) 데이터만 보고
- abstract 기준 분리 불가, full text 확보 시 subgroup 가능성 있음 (Day 3 후속 작업 가능)

### 정량 결과 (pooled, free-technique)
| Outcome | Without exo | With exo (assistance level 30–70%) | Reduction |
|---------|-------------|-----------------------------------|-----------|
| L5/S1 compressive force | baseline | – | **5.5–9.3% ↓** |
| Back muscle active moment | baseline | – | **14.9–28.6% ↓** |
| Lumbar flexion | baseline | – | minor change (정량값 abstract 미명시) |
| 70% vs 30-50% assistance | – | – | L5/S1 추가 감소 없음, ES moment만 추가 감소 |

### Box / participants
- Box: **15 kg**
- Lifting style: free
- 모델: **EMG-driven biomechanical model** (OpenSim 명시 X — Day 3 full text 확인 후속 필요)

### 결론
- Hu 2026 squat **단독 수치 추출 불가** (free-technique pooled only)
- ES moment 14.9–28.6% reduction은 squat+stoop 혼합 수치 → 우리 squat 시나리오 비교에 **상한선**으로만 사용
- L5/S1 compression 5.5–9.3% reduction은 squat 시나리오 validation 비교 기준에 적합 (free-tech 중 squat이 lumbar compression 더 높다는 P7 Kingma 근거 고려 시 우리 squat 결과는 ↑ 가능)

---

## 2. 대안 Squat-Specific Validation Reference (보강)

### Reference R1: Hasenmaier et al. 2026 (P3, 직접 squat 측정)

> ## ⛔ 정정 (2026-07-30) — 아래 원본 기재는 단위를 오독한 것이며 인용 금지
>
> 원문 초록을 verbatim 재확인한 결과, **"10–27 % MVC"는 %MVC 절대 포인트 감소이지
> 상대 감소율이 아니다.** 아래 항목은 이를 상대 감소율 목표치로 잘못 기록하였다.
>
> **원문 확인값** (stoop):
> | 조건 | ES 활성도 |
> |---|---:|
> | 1) 외골격 미착용 | 69.8 %MVC |
> | 2) 착용 0/0 % | 59.2 %MVC |
> | 3) 착용 50/20 % | 50.7 %MVC |
> | 4) 착용 100/60 % | **42.4 %MVC** |
>
> → **stoop 상대 감소율 = (69.8 − 42.4) / 69.8 = −39.3 %**
> → 원문 요약: "a reduction of MES activity of about 10 %–27 % MVC ... across both
>   lifting techniques" — 두 기법 전체에 대한 **절대 %MVC 포인트** 범위
> → **squat**: 원문이 "there were no significant results between the individual
>   levels"로 보고 → **상대 감소율 인용 불가**
>
> **영향**: 이 오독을 근거로 한 "우리 squat이 문헌 범위를 초과" 류의 서술은 모두 무효.
> 정정된 대조는 `five_motion_paper_draft.md` §4를 참조.
> 오독이 파급된 위치 목록은 `five_motion_completion_record.md`의 "문헌 오독 정정 이력" 참조.

- DOI: 10.3389/fbioe.2026.1631785
- ~~**Squat 단독 ES reduction**: **10–17% MVC ↓** (Apogee active exo, 50% support → 100% support)~~ ← **오독, 사용 금지**
- Squat technique knee flexion ~135°
- BF (biceps femoris) reduction: 2–3% (n.s.)
- ~~핵심: **squat은 stoop보다 exo 효과 작음** (squat 10–17% vs stoop 10–27%)~~ ← **오독, 사용 금지**
- ~~**우리 시나리오 직접 비교 가능 reference** (squat 단독)~~ ← squat은 유의차 미보고로 **대조 불가**

### Reference R2: Kingma et al. 2021 (P7, squat lumbar loading)
- DOI: 10.3389/fbioe.2021.769117
- Free-squat L4/L5 compression: **3509 ± 68 N**
- Stoop L4/L5 compression: **2783 ± 184 N**
- 핵심: **free-squat이 stoop보다 lumbar compression 더 높음** (popular belief과 반대)
- 우리 baseline (no suit) squat 결과 lumbar compression 검증 reference

### Reference R3: Yan et al. 2024 (P1, squat + stoop OpenSim)
- DOI: 10.1016/j.jbiomech.2024.112322
- EMG-model cross-correlation: r = **0.84–0.98** (back + hip extensors)
- RMSE: 0.05–0.10
- 핵심: **OpenSim EMG validation 정량 기준** — 우리 시나리오에 동일 적용
- Soft active exosuit (2.7 kg) 효과 정량 비교

### Reference R4: Park et al. 2002 (P6, squat vs stoop ROM)
- Squat knee flexion: 큰 hip-ankle support moment
- 인용 가치: kinematic baseline (한국인 cohort 평균 hip 100°, knee 30° at peak — 우리 모델 default 비교)

---

## 3. Validation Criteria 통합 (Day 4 입력)

### Criterion 1: Kinematic accuracy
- Hip flexion peak: target 110° (±10°) (P3, P6)
- Knee flexion peak: target 115° (±15°) (P3 deep squat)
- Lumbar sum flexion: target 25° (±10°)
- Trunk inclination: target 35° (±15°) (P3 30–56° 범위)
- **Source**: P3 Hasenmaier 2026 + P6 Park 2002

### Criterion 2: EMG-model agreement (no suit)
- Cross-correlation r > **0.80** (P1 Yan 2024 lower bound 0.84의 보수적 적용)
- RMSE < **0.15** (P1 0.05–0.10 + 안전 margin)
- ES 8개 fascicle (L1–L5 양측) 비교

### Criterion 3: Suit effect (squat)
- ES reduction: target **10–17%** (P3 squat 단독 직접 비교)
- L5/S1 compression reduction: target **5–10%** (P2 Hu 2026 pooled 5.5–9.3% adapted to squat)
- **상한선**: 28% (P2 max, free-tech) — 우리 squat이 이를 초과하면 의심
- **하한선**: 5% (P3 min)

### Criterion 4: Baseline (no suit) lumbar loading
- L5/S1 compression: 약 3000–4000 N (P7 free-squat 3509 N + load 15 kg 적용)
- 단순 stoop 비교 시 squat이 더 높을 가능성 (P7 핵심) — limitation으로 언급

### Criterion 5: Phase 1a regression (squat 확장 시)
- Stoop static SO (Phase 1a) 결과 28% reduction → 직접 squat 비교 X
- Squat dynamic Moco 결과는 별도 baseline
- **Variant C (Akhavanfar) 채택 시 추가 regression** (Day 3)

---

## 4. 위험 / Open Issue

1. **Hu 2026 squat 단독 결과 미명시** → P3 Hasenmaier 2026이 우리 핵심 validation reference (squat 단독)
2. **Hu 2026 모델 OpenSim 여부 불명** → Day 3 full text 확보 후 결정 (Ergonomics journal 접근 필요)
3. **P3 sample은 young adults (21.5±2.5 y)** → 우리 caregiving target 65세 여성 그룹은 별도 reference 필요 (P8 Tomescu 2022 hip mobility 제한 근거만 있음)
4. **Squat에서 suit 효과 작을 가능성 (P3 결론)** → Phase 1a stoop 28% reduction과 squat이 다를 것 정직 보고

---

## 5. Day 4 paper-agent 작성 위치

- `validation_protocol_v2.md §3 Validation Criteria` → §3.1 Kinematic / §3.2 EMG / §3.3 Suit effect / §3.4 Lumbar loading
- 본 docs를 paper-agent에 input으로 전달
- 본 docs의 R1–R4 Bibliography는 `squat_lift_literature.md` Bibliography와 통합

---

## Bibliography (본 docs 인용)

1. Hu F, Brouwer NP, Tabasi A, et al. *Ergonomics* 2026;69(3):453–465. doi:10.1080/00140139.2025.2466030 (PMID 39967340)
2. Hasenmaier J, Siebert T, Mayer D, Stutzig N. *Front Bioeng Biotechnol* 2026;14:1631785. doi:10.3389/fbioe.2026.1631785
3. Kingma I, et al. *Front Bioeng Biotechnol* 2021;9:769117. doi:10.3389/fbioe.2021.769117 (PMC 8599159)
4. Yan C, Banks JJ, ..., Anderson DE. *J Biomech* 2024;176:112322. doi:10.1016/j.jbiomech.2024.112322 (PMID 39305855)
5. Park BY, et al. *Occup Ergon* 2002;3(2):99–103
6. Tomescu SS, et al. *Phys Ther Sport* 2022. PMID 35026497
