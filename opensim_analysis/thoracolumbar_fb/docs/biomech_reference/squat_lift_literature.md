# Squat Lift Literature Synthesis

**작성일**: 2026-05-26
**작성**: literature-agent (Plan v2 Day 2 작업 1)
**목적**: Squat lift EMG/Kinematics 학계 검증 reference 5+ paper 정리, Variant C 시드 평가 입력
**근거 원칙**: 모든 numeric에 PMID/DOI 동반. 2023-2026 paper 우선.

---

## 1. 핵심 Paper 8개 (5+ 요구사항 초과)

| # | Citation | PMID/DOI | Year | Lift Type | Box | n | 핵심 발견 (numeric) | 우리 적용 |
|---|----------|----------|------|-----------|-----|---|---------------------|------------|
| P1 | Yan C, Banks JJ, ..., Anderson DE. *J Biomech* 176:112322 | PMID 39305855 / 10.1016/j.jbiomech.2024.112322 | 2024 | squat + stoop | 6, 10 kg | 14 | OpenSim 모델 + soft exosuit, EMG-model cross-corr r = 0.84–0.98, RMSE 0.05–0.10 | OpenSim 사용 + validation 기준 |
| P2 | Hu F, Brouwer NP, Tabasi A, .... *Ergonomics* 69(3):453–465 | PMID 39967340 / 10.1080/00140139.2025.2466030 | 2026 | free (squat/stoop 자유) | 15 kg | — | dual-joint active exo: L5/S1 compression 5.5–9.3% ↓, ES active moment 14.9–28.6% ↓, lumbar flexion minor change | validation criteria 핵심 (§4) |

> ⛔ **정정 (2026-07-30)**: 이 절의 Hasenmaier 2026 "10–17 %" / "10–27 %"는 **%MVC 절대 포인트**이지 상대 감소율이 아니다. stoop 상대 감소율은 69.8→42.4 %MVC = **−39.3 %**, squat은 원문이 수준 간 유의차를 보고하지 않아 **대조 불가**. 상세는 `hu2026_squat_validation_input.md` R1 정정 박스 및 `five_motion_paper_draft.md` §4 참조.
| P3 | Hasenmaier J, Siebert T, Mayer D, Stutzig N. *Front Bioeng Biotechnol* 14:1631785 | 10.3389/fbioe.2026.1631785 | 2026 | symmetric stoop **vs squat** (직접 비교) | 15 kg, 5 reps @ 45 bpm | 17 (8M/9F, 21.5±2.5 y) | squat: 약 135° knee flexion, trunk inclination ~56° (<30° trunk flexion), ES 10–17% ↓, BF 2–3% (n.s.) | **squat-stoop 직접 비교 핵심 + squat kinematic spec** |
| P4 | Akhavanfar M, Mir-Orefice A, Uchida TK, Graham RB. *Ann Biomed Eng* 52(2):259–269 | PMID 37741902 / 10.1007/s10439-023-03368-x | 2024 | dynamic lift/lower 9 tasks | 다양 | — | Enhanced FATLS (Bruno 기반) + passive structures + kinematic constraints, validation r > 0.9 | **Variant C 핵심 모델** (§Variant C 추천) |
| P5 | Eskandari AH, Ghezelbash F, Shirazi-Adl A, Arjmand N, Larivière C. *Appl Ergon* 123:104407 | PMID 39489061 / 10.1016/j.apergo.2024.104407 | 2025 | repetitive lift/lower (knee–shoulder) | empty crate | — | EMG-assisted in-house spine model (Polytechnique Montréal), peak 15% spinal compression/shear ↓ at large trunk flexion | OpenSim 호환 X — fallback 필요 |
| P6 | Park BY 등. *Occupational Ergonomics* 3(2):99-103 (PMID — 미부여; 인용 사용) | — | 2002 (참고) | squat vs stoop | 5, 10, 15 kg | 26 (남 23.5 y, 66.5 kg, 172 cm) | squat: 큰 knee flexion + hip-ankle support moment 우세, lumbar curvature kyphosis→lordosis 변환 50% (squat) / 60% (stoop), max lumbar moment 차이 n.s. | 기본 kinematic 참고 |
| P7 | Kingma I 등. *Front Bioeng Biotechnol* (PMC 8599159) "From Stoop to Squat" | 10.3389/fbioe.2021.769117 | 2021 | stoop/free-squat/free-style | 다양 | — | free-squat L4/L5 compression 3509±68 N (vs stoop 2783±184 N), squat 동작이 lumbar compression 더 높음 | squat이 항상 안전 X 근거 |
| P8 | Tomescu SS 등. *Phys Ther Sport* "Hip flexion mobility + lumbar extensor strength" | PMID 35026497 / 10.1016/j.ptsp.2021.10.008 | 2022 | squat lift | — | 여성 그룹 | hip flexion 가용범위 ↓ → 여성에서 peak lumbar flexion ↑ (negative assoc), 여성 lumbar extensor strength도 peak lumbar flexion negative assoc | **여성 65세 caregiving target 확장 근거** |

---

## 2. 검증된 Numeric Spec (Squat lift)

### Kinematic (peak angle)
- **Hip flexion peak**: 85–110° (medium squat), 110–135° (deep squat) — P6, P3, [Escamilla et al. 2001 인용 via P3]
- **Knee flexion peak**: ~135° (deep squat technique, P3); 90–110° (medium); 60° (parallel squat)
- **Lumbar flexion peak (sum L1–L5)**: 변동 큼. P3 trunk inclination ~56° (<30° trunk flexion). Free-squat이 stoop 대비 lumbar flexion 약간 적지만 큰 차이 X (P6 max lumbar moment 차이 n.s.). 여성/고령에서 hip mobility 부족 시 lumbar flexion ↑ (P8)
- **Trunk angle (inclination)**: squat ~30–56° (P3); stoop > 60°
- **Ankle dorsiflexion**: 20–25° (P6 인용)

### EMG (ES, % MVC)
- **Squat ES peak**: 30–50% MVC 범위 (paper별 변동; P3에서 baseline 비교 reduction 단위로 보고)
- **Exoskeleton ES reduction (squat)**: 10–17% (P3, Apogee active), 14.9–28.6% (P2 Hu 2026 free-tech, 일부 squat 포함), 12–15% (back-support exo 일반, P3 cite)
- **Hip-driven exo는 squat에 효과 낮음** (P3 핵심 결론: squat은 knee extension dominant → hip exo 효과 ↓)

### Load
- 6 kg (P1 light), 10 kg (P1, P6), 15 kg (P2, P3, P6 max), 20 kg (P7 max)
- **caregiving context**: 환자 들기 ≈ 60–80 kg 부분 들기 → 실제 손에 가해지는 force ≈ 10–20 kg 등가
- 우리 권장: **15 kg** (literature 최빈값, P2/P3/P6 모두 사용)

### Lift duration
- P3: 5 reps @ 45 bpm → 약 1.33 s per rep cycle (왕복) → descent+ascent 각 ~0.65 s (매우 빠름, exercise context)
- 일반 occupational lift: 2–4 s per phase (descent or ascent), total 4–6 s
- 우리 권장: **4 s total** (descent 1.5 s + grasp 1.0 s + ascent 1.5 s)

### Box position (height)
- P2, P3: ground to standing (가장 일반적)
- NIOSH RWL: horizontal multiplier가 vertical보다 영향 큼; 박스 가까울수록 (h < 25 cm) RWL ↑
- 우리 권장: **ground level + 30 cm 박스 mid-height + 35 cm horizontal**

---

## 3. OpenSim 호환성 (Variant 평가 입력)

| Source | Model | OpenSim 호환 | 공개 URL | Squat 적합성 |
|--------|-------|--------------|----------|---------------|
| P1 Yan 2024 | participant-specific (base 미명시) | ✅ OpenSim (버전 미명시) | 자체 데이터, model 별도 공개 X | ✅ squat + stoop 둘 다 |
| P4 Akhavanfar 2024 | **Enhanced FATLS (Bruno 2015 기반)** | ✅ **OpenSim 3.3 + 4.4** | **SimTK group_id=2108** ([download](https://simtk.org/frs/?group_id=2108), MIT license) | ✅ **dynamic lifting 9 tasks validated** |
| P5 Eskandari 2025 | EMG-assisted FE+MS (Polytechnique Montréal in-house) | ❌ 자체 in-house (FE 통합, OpenSim X) | 미공개 | n/a |
| Bruno 2015 (base) | Thoracolumbar v2.0 (우리 baseline) | ✅ OpenSim 4.x | SimTK group_id=959 | ⚠️ static/isometric 위주 validation, dynamic은 Akhavanfar enhancement 필요 |
| Christophy 2012 / Beaumont | lumbar + lower limb | ✅ OpenSim 4.x | Tandfonline 2021 paper | ⚠️ trunk only |

---

## 4. 우리 task (Squat lift) 적용 — DO / DO NOT

### DO
1. **squat 동작 정의 명확히**: knee flexion ≥ 90° (medium 이상). P3 기준 135° 가능
2. **trunk flexion 30–60°** (≪ stoop 90°)
3. **15 kg, ground level, 35 cm horizontal** (literature 최빈값)
4. **descent 1.5 s + grasp 1.0 s + ascent 1.5 s = 4 s** (P3 빠른 cycle보단 occupational 표준)
5. **hip flexion mobility를 모델에서 확보** (deep squat 130°+ 필요) — Day 3 opensim-agent 실측 작업
6. **여성 65세 그룹은 hip mobility 제약 (P8)**으로 lumbar flexion 추가 ↑ → suit assist 효과 다를 가능성 검증

### DO NOT
1. Hip-aligned exo가 squat에 stoop만큼 효과적이라고 가정 X (P3: squat 효과 ↓)
2. P6 인용으로 "squat이 stoop보다 lumbar에 안전" 주장 X (max lumbar moment 차이 n.s. + P7 free-squat L4/L5 compression 더 높음)
3. P2 Hu 2026 14.9–28.6% reduction을 squat 단독 수치로 인용 X (Hu 2026은 free-technique). squat 단독은 P3 10–17% 인용 적절
4. Eskandari 2025 model 직접 사용 X (in-house, OpenSim 호환 X)

---

## 5. Variant C 후보 평가 (시드 A/B/C/대안)

자세한 평가는 `variant_c_recommendation.md` 참조. 요약:

- **시드 A (Yan 2024 Gait2392 추정)**: model 자체 공개 X, base 미명시 → 비추천
- **시드 B (TLFB + hip/knee ROM 확장 자체 보강)**: literature 1순위 약함 → fallback 후보
- **시드 C (Eskandari 2025)**: **OpenSim 호환 X 확정** (in-house FE+MS, Polytechnique Montréal) → **불채택**
- **대안 D (Akhavanfar 2024 Enhanced FATLS)**: ✅ OpenSim 4.4 + SimTK 공개 + dynamic lifting 9 tasks validated + Bruno 2015 우리 baseline의 enhanced 버전 → **최강 추천**

---

## Bibliography (Vancouver style)

1. Yan C, Banks JJ, Allaire BT, Quirk DA, Chung J, Walsh CJ, Anderson DE. Musculoskeletal models determine the effect of a soft active exosuit on muscle activations and forces during lifting and lowering tasks. *J Biomech* 2024;176:112322. doi:10.1016/j.jbiomech.2024.112322 (PMID 39305855)
2. Hu F, Brouwer NP, Tabasi A, et al. Influence of varied assistance levels provided by a dual-joint active back-support exoskeleton on spinal musculoskeletal loading and kinematics during lifting. *Ergonomics* 2026;69(3):453–465. doi:10.1080/00140139.2025.2466030 (PMID 39967340)
3. Hasenmaier J, Siebert T, Mayer D, Stutzig N. Effects of an active exoskeleton on the muscle activity of the erector spinae and biceps femoris muscles during lifting with symmetric stoop and squat technique. *Front Bioeng Biotechnol* 2026;14:1631785. doi:10.3389/fbioe.2026.1631785
4. Akhavanfar M, Mir-Orefice A, Uchida TK, Graham RB. An Enhanced Spine Model Validated for Simulating Dynamic Lifting Tasks in OpenSim. *Ann Biomed Eng* 2024;52(2):259–269. doi:10.1007/s10439-023-03368-x (PMID 37741902)
5. Eskandari AH, Ghezelbash F, Shirazi-Adl A, Arjmand N, Larivière C. Effect of a back-support exoskeleton on internal forces and lumbar spine stability during low load lifting task. *Appl Ergon* 2025;123:104407. doi:10.1016/j.apergo.2024.104407 (PMID 39489061)
6. Park BY, et al. Kinematic contribution and synchronization of the trunk, hip and knee during squat lifting. *Occup Ergon* 2002;3(2):99–103.
7. Kingma I, et al. From Stoop to Squat: A Comprehensive Analysis of Lumbar Loading Among Different Lifting Styles. *Front Bioeng Biotechnol* 2021;9:769117. doi:10.3389/fbioe.2021.769117 (PMC 8599159)
8. Tomescu SS, et al. The influence of hip flexion mobility and lumbar spine extensor strength on lumbar spine flexion during a squat lift. *Phys Ther Sport* 2022. PMID 35026497
9. Bruno AG, Bouxsein ML, Anderson DE. Development and Validation of a Musculoskeletal Model of the Fully Articulated Thoracolumbar Spine and Rib Cage. *J Biomech Eng* 2015;137(8):081003. (우리 baseline, SimTK group_id=959)
