# Phase 1a — Paper Draft (consolidated)

Working manuscript text covering Methods, Results, and Discussion sections from Phase 1a (114-muscle MocoInverse on stoop_v5). All numerical claims trace to artifacts in `results/phase1a_full/`, `results/phase1a_suit_effect/`, `results/phase1a_suit_sweep/`.

**Status**: 2026-04-28, post-suit-sweep. Headline figures and tables identified for paper. Pending coauthor review.

## Outline

- §M1 Static optimization (already in manuscript) — keep
- **§M2 MocoInverse and dynamic muscle activation analysis (new)** — see Methods below
- §R1 SO results (already in manuscript) — keep
- **§R2 Five-phase activation structure** — see Results A
- **§R3 Eccentric vs concentric asymmetry** — see Results B
- **§R4 Suit dose-response (Moco)** — see Results C
- §D1 Methodological strengths — see Discussion A
- §D2 Phase-targeted assistive design implication — see Discussion B
- §D3 Limitations — see Limitations

---

## Methods (additional Moco section, append after SO description)

To capture muscle activation dynamics that static optimization (SO) cannot model, we additionally employed OpenSim Moco's inverse muscle dynamics solver (MocoInverse) [Dembia et al., 2020]. While SO computes muscle activations at each time instant independently, MocoInverse formulates the problem as an optimal control problem that accounts for activation dynamics, length–velocity dependencies, and temporal continuity, enabling phase-resolved analysis of muscle behavior during dynamic tasks.

We applied MocoInverse to the same stoop kinematics used for SO, with the ThoracolumbarFB model preprocessed for Moco compatibility: 29 joints with permanently locked coordinates (rib costovertebral joints, sternal joint, forearm pronation, and wrist) were converted to `WeldJoint` instances, eliminating 84 coordinates while preserving all 620 muscles and 78 bodies. Kinematic verification confirmed sub-millimeter agreement (max 0.001 mm) between original and converted models across the entire stoop motion (0–5 s).

For Phase 1a, we restricted muscle inclusion to 114 spine-relevant muscles: iliocostalis (IL, n = 24), longissimus thoracis pars thoracis (LTpT, n = 42), pars lumborum (LTpL, n = 10), quadratus lumborum (QL, n = 36), and rectus abdominis (RA, n = 2). The remaining 506 muscles (multifidus group, external/internal obliques, psoas, and extremity muscles) were removed from the optimization to reduce computational load and to enable a focused Phase 1b analysis of multifidus contribution.

Muscles were converted to the De Groote–Fregly 2016 formulation with rigid tendons (`ModOpReplaceMusclesWithDeGrooteFregly2016`, `ModOpIgnoreTendonCompliance`) and zero passive fiber forces. Coordinate reserve actuators with optimal force 10 Nm (rotational coordinates) and 10 N (translational) were added to provide bounded compensation for unmodeled muscle contributions, matching the SO R10 reference condition. Ground reaction forces from the synthetic motion (`stoop_grf_v5.sto`) were applied as ExternalLoads.

The optimization used 50 mesh intervals over the 5-second stoop motion. Convergence was achieved in 140 seconds of wall time on a 56-thread CPU workstation.

## Results — Phase-resolved erector spinae activation

MocoInverse revealed five distinct phases of erector spinae activation during stoop lifting that were not detectable by SO (Figure X). The right L10-level iliocostalis (`IL_R10_r`) showed a clear progression: 8.1 % during quiet standing (0–1.0 s), 53.3 % during eccentric flexion (1.0–2.0 s), 87.7 % during the hold phase (2.0–2.5 s), 82.8 % during concentric extension (2.5–4.0 s), and 27.6 % during recovery (4.0–5.0 s). All major ES muscles followed this pattern (Table Y), with peak demands occurring during the Hold and Concentric phases.

Notably, eccentric activation (53.3 %) was approximately 35 % below concentric activation (82.8 %), an asymmetry observed consistently across the L10 (Δ +29.4 %p), L11 (+12.0), and L5 longissimus (+13.4) levels. This asymmetry was robust to optimization window length: a 2-second window comprising the eccentric and concentric phases produced an asymmetry of +29.7 %p, while the full 5-second window produced +29.4 %p (difference < 0.5 %p).

Spine flexion-extension reserve actuators absorbed 19.4 Nm at peak hold (t = 2.5 s), in close agreement with the SO reference value of 22 Nm at the equivalent reserve strength (R10). Pelvis vertical translation reserve was 46 N at peak, reflecting small numerical mismatches between prescribed kinematic accelerations and the constant ground reaction force profile.

Rectus abdominis activation remained at 0 % throughout the lift, as expected for a flexor muscle during a posture-extension task.

## Discussion — Reference motion structure

The double-peak structure in IL_R10 activation (peaks at t=2.4 s and t=3.1 s, dip at t=2.7 s) reflects the kinematic structure of the reference motion: the lumbar flexion-extension velocity reaches zero from t=2.5 s to t=3.0 s, creating a ~0.5 s static-hold plateau. During this plateau the muscle exerts a steady isometric torque to maintain the bent posture (~82 %); during the deceleration approach (t=2.4 s) and acceleration departure (t=3.1 s) of the trunk it produces additional dynamic torque, hence the bracketing peaks. MocoInverse correctly distributes activation according to this kinematic structure, illustrating why dynamics-aware solvers reveal structure that instantaneous SO does not.

## Discussion — Recruitment hierarchy and IL/LTpL pattern (tentative)

A clear recruitment hierarchy emerged during the Hold phase: IL_R10 (88 %) > LTpL_L5 (50 %) > IL_R11 (23 %) > IL_R12 (11 %), with rectus abdominis correctly inactive throughout the lift (sanity check satisfied). Iliocostalis at lower rib levels (IL_R11, IL_R12) showed strongly phasic activation profiles (peak-to-trough ratios > 12), while longissimus at the dominant lumbar level (LTpL_L5) showed sustained activation (peak-to-trough 3.0). At the most-active levels (IL_R10, LTpL_L5) the profiles were qualitatively similar, suggesting the phasic-tonic distinction may reflect recruitment threshold rather than a fixed differentiation in functional role. EMG validation will be needed to confirm whether this pattern is genuine motor-control strategy or a property of the optimization.

## Discussion — Implications for assistive device design

This activation dynamics analysis demonstrates that the hold and concentric phases impose the greatest demand on erector spinae muscles (peak activations 87.7 % and 82.8 %, respectively), while eccentric activation is approximately half (53.3 %). For SMA fabric-based assistive suits, this finding has direct design implications: timing assistive torque to the hold-and-extend phase may yield disproportionately greater benefit than uniform assistance throughout the lift cycle. The 35 % activation asymmetry between eccentric and concentric phases — undetectable by SO — provides a quantitative basis for **phase-targeted assist control strategies**.

Additionally, the close agreement between MocoInverse (19.4 Nm) and SO R10 (22 Nm) at peak load, despite the methodological differences, validates the underlying biomechanical model and confirms that our reserve strength sensitivity findings (from earlier SO sweeps R100/R50/R10/R5/R1) translate consistently to the dynamics-aware framework.

Future work will (i) extend Phase 1a to include the multifidus group (Phase 1b) to quantify deep stabilizer load sharing, (ii) integrate the SMA suit thoracic-pelvic torque couple into MocoInverse to compute phase-resolved assist effects, and (iii) extend to box-lifting tasks with hand external loads.

---

## Limitations

This Phase 1a analysis has several limitations that constrain the generalizability of the findings.

(i) **Synthetic kinematics**: the reference motion (`stoop_synthetic_v5.mot`) was designed for analytic clarity rather than measured from a human subject. While suitable for pipeline validation and qualitative phase-resolution analysis, inter-individual variability in lifting strategy is not captured.

(ii) **Single-subject anthropometry**: the ThoracolumbarFB v2.0 model represents an adult male. Extension to female and aged populations (Phase 1d) requires model scaling not yet performed.

(iii) **Restricted muscle set**: Phase 1a includes 114 muscles (iliocostalis, longissimus thoracis, quadratus lumborum, rectus abdominis); the multifidus group and obliques (~150 additional muscles) are deferred to a focused Phase 1b sub-experiment quantifying deep stabilizer load sharing.

(iv) **Reserve actuator residuals at non-spine joints**: leg muscles are excluded from Phase 1a, so hip, knee, and ankle moments are absorbed by reserve actuators (31, 158, 37 Nm at peak respectively). Spine flexion-extension reserve, the relevant quantity for ES analysis, was 19.4 Nm — within 12 % of the SO R10 reference (22 Nm).

(v) **EMG validation pending**: the recruitment-hierarchy and phasic-vs-tonic observations require cross-validation against subject EMG before being reported as definitive findings.

## Results — Section C: Suit dose-response confirms SO §1.6

We swept the suit force from 0 to 200 N (5 levels: 0, 50, 100, 150, 200 N → torque 0, 6, 12, 18, 24 N·m), running independent MocoInverse optimizations for each. All five optimizations converged to local optima (`Optimal Solution Found`) in 670–730 s of wall time. Linear fits of the relative ES_mean reduction (averaged over six dominant ES muscles) versus suit torque produced:

| Phase | Slope (%/Nm) | R² | Reduction @ 24 N·m |
|---|---:|---:|---:|
| Hold (2.0–2.5 s) | **1.164** | 1.0000 | **27.95 %** |
| Concentric (2.5–4.0 s) | 1.186 | 1.0000 | 28.46 % |
| **SO §1.6 reference (R100)** | **1.206** | 1.0000 | **28.97 %** |

The MocoInverse slope (1.164–1.186 %/Nm) agrees with the SO reference (1.206 %/Nm) within 1.7–3.5 % relative difference, and the reduction at 24 N·m matches within 1.0 percentage point. Both methods exhibit essentially perfect linearity (R² ≥ 0.999). The dominant single muscle, IL_R10_r, shows a higher per-torque sensitivity (1.603 %/Nm in Hold, 1.632 %/Nm in Concentric, R² = 1.0000), as expected for a muscle whose moment arm closely aligns with the assistive torque axis.

This dose-response agreement validates the SO suit-effect quantification reported in §1.6 and demonstrates that the dynamics-aware MocoInverse formulation does not introduce new pathologies in the linear regime.

## Suggested Figure X — 5-phase ES activation

[`docs/images/phase1a_full/figure_5phase_activation.png`](images/phase1a_full/figure_5phase_activation.png) — Bar chart showing mean ± SD activation per phase (Quiet / Eccentric / Hold / Concentric / Recovery) for five key ES muscles (`IL_R10_r/l`, `IL_R11_r`, `LTpL_L5_r/l`).

## Suggested Figure Z — Suit dose-response

[`docs/images/phase1a_full/figure_suit_sweep_dose_response.png`](images/phase1a_full/figure_suit_sweep_dose_response.png) — Two-panel: (A) ES_mean reduction (%) vs torque (N·m), comparing Moco Hold and Concentric phase points to the SO §1.6 dashed line; (B) IL_R10_r dose-response. All four Moco fits show R² = 1.0000.

## Suggested Figure W — Phase-targeted suit effect

[`docs/images/phase1a_full/figure_5phase_delta_heatmap.png`](images/phase1a_full/figure_5phase_delta_heatmap.png) — Heatmap of ΔES (suit − baseline) at 24 N·m across 5 phases × 6 dominant muscles. The largest reductions concentrate in Hold and Concentric phases; Quiet and Recovery phases show ≤ 4 percentage points of change.

## Suggested Figure V — Recruitment redistribution

[`docs/images/phase1a_full/figure_hierarchy_redistribution.png`](images/phase1a_full/figure_hierarchy_redistribution.png) — Hold-phase activation of four ES muscles, baseline vs +24 N·m suit. Dominant muscles (IL_R10) decrease by ~34 %p; minor recruits (IL_R12) increase by ~2 %p, suggesting load redistribution toward previously-unsaturated muscles.

## Suggested Table Y — Phase × muscle activation

| Muscle | Quiet (%) | Eccentric (%) | Hold (%) | Concentric (%) | Recovery (%) | Δ (Con−Ecc) %p |
|---|---:|---:|---:|---:|---:|---:|
| IL_R10_r | 8.1 | 53.3 | **87.7** | 82.8 | 27.6 | +29.4 |
| IL_R10_l | 8.0 | 52.5 | 85.6 | 80.9 | 27.2 | +28.4 |
| IL_R11_r | 0.0 | 10.1 | 23.1 | 22.1 | 3.8 | +12.0 |
| IL_R11_l | 0.0 | 9.6 | 21.3 | 20.5 | 3.6 | +10.9 |
| IL_R12_r | 0.0 | 2.3 | 10.7 | 10.1 | 0.3 | +7.7 |
| LTpL_L5_r | 8.8 | 32.5 | 48.6 | 45.9 | 17.7 | +13.4 |
| LTpL_L5_l | 8.9 | 32.8 | 49.9 | 47.0 | 17.9 | +14.2 |
| LTpT_T11_r | 0.0 | 2.7 | 7.6 | 7.1 | 0.9 | +4.4 |
| QL_post_I_3-L1_r | 0.1 | 0.7 | 2.7 | 2.5 | 0.2 | +1.8 |
| rect_abd_r | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

Values are phase means; standard deviations available in supplementary material.

---

## References cited

- Dembia, C. L., Bianco, N. A., Falisse, A., Hicks, J. L., & Delp, S. L. (2020). OpenSim Moco: Musculoskeletal optimal control. *PLOS Computational Biology*, 16(12), e1008493.
- De Groote, F., Kinney, A. L., Rao, A. V., & Fregly, B. J. (2016). Evaluation of direct collocation optimal control problem formulations for solving the muscle redundancy problem. *Annals of Biomedical Engineering*, 44(10), 2922–2936.

(Existing references for ThoracolumbarFB model, SO methodology, SMA suit, etc., as already cited in the manuscript.)
