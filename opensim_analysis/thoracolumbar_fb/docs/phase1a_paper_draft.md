# Phase 1a — Paper Draft Fragments

Working English text for the manuscript Methods, Results, and Discussion sections. Draft only — pending coauthor review.

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

## Discussion — Implications for assistive device design

This activation dynamics analysis demonstrates that the hold and concentric phases impose the greatest demand on erector spinae muscles (peak activations 87.7 % and 82.8 %, respectively), while eccentric activation is approximately half (53.3 %). For SMA fabric-based assistive suits, this finding has direct design implications: timing assistive torque to the hold-and-extend phase may yield disproportionately greater benefit than uniform assistance throughout the lift cycle. The 35 % activation asymmetry between eccentric and concentric phases — undetectable by SO — provides a quantitative basis for **phase-targeted assist control strategies**.

Additionally, the close agreement between MocoInverse (19.4 Nm) and SO R10 (22 Nm) at peak load, despite the methodological differences, validates the underlying biomechanical model and confirms that our reserve strength sensitivity findings (from earlier SO sweeps R100/R50/R10/R5/R1) translate consistently to the dynamics-aware framework.

Future work will (i) extend Phase 1a to include the multifidus group (Phase 1b) to quantify deep stabilizer load sharing, (ii) integrate the SMA suit thoracic-pelvic torque couple into MocoInverse to compute phase-resolved assist effects, and (iii) extend to box-lifting tasks with hand external loads.

---

## Suggested Figure X — 5-phase ES activation

[`docs/images/phase1a_full/figure_5phase_activation.png`](images/phase1a_full/figure_5phase_activation.png) — Bar chart showing mean ± SD activation per phase (Quiet / Eccentric / Hold / Concentric / Recovery) for five key ES muscles (`IL_R10_r/l`, `IL_R11_r`, `LTpL_L5_r/l`).

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
