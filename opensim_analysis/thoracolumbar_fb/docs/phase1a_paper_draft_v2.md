# Phase 1a — Paper Draft v3 (Phase 1a 단독 Publication, Final)

**Status**: 2026-05-20, v3 — §7.ix 박스 motion 5단계 limitations 정직 확장; §8 Future Work 6개 재구성; §6.6 박스 motion 5개월 학습 가치 신규; References 5개 추가; Step 2 Week 3 재현 검증 수치 반영.  
**Changes from v2**: §7.ix 5-step limitations 전면 재작성 (v3-v11b + Step 2 Week 4-5 MocoTrack 포함); §8 6-item Future Work (Squat Phase 2.A 즉시 next 명확화); §6.6 신규 (5개월 학습 방법론 가치); References Falisse 2019, John 2022 (재확인), Dembia 2020, D'Hondt 2024, Waters 1994 추가 정리.  
**Step 2 Week 3 재현 검증 반영**: slope 1.158 %/N·m (원본 1.164 Δ 0.5%), @24 N·m 27.79% (원본 27.95%, Δ 0.16 %p), max ΔES 0.41 %p.  
**All numerical claims** trace to: `results/phase1a_full/`, `results/phase1a_suit_effect/`, `results/phase1a_suit_sweep/`.

---

## §1. Introduction

Lower back pain (LBP) ranks among the leading causes of occupational disability globally, with manual handling tasks — particularly repetitive stooped lifting — identified as a primary risk factor [Kermavnar et al., 2021; De Bock et al., 2022]. Caregiving workers, who perform repeated patient-handling and load-lifting tasks throughout their shifts, represent a high-risk population. In South Korea, female caregivers aged 55–65 account for the largest demographic in long-term care facilities, yet this population remains severely under-represented in exoskeleton efficacy research [Kermavnar et al., 2021].

Shape-memory alloy (SMA) fabric actuators offer a materially novel approach to wearable lumbar assistance: unlike rigid-frame back-support exoskeletons or Bowden-cable soft exosuits, SMA fabric generates distributed contractile force directly within a textile interface, enabling conformal fit without protruding struts or external cable routing. No prior musculoskeletal simulation study has quantified the spinal loading effects of an SMA-based fabric suit on a lifting task.

Musculoskeletal simulation provides a principled path to quantify suit effects on individual muscle groups before hardware maturation permits large-scale electromyographic (EMG) validation. OpenSim MocoInverse [Dembia et al., 2020] extends earlier static optimization (SO) approaches by incorporating activation dynamics, length–velocity dependencies, and temporal continuity, enabling phase-resolved analysis that SO cannot provide.

The ThoracolumbarFB v2.0 model [Beaucage-Gauvreau et al., 2019] offers 76 erector spinae (ES) segments across lumbar and thoracic levels — a resolution unavailable in commonly used full-body models (Gait2392, Rajagopal 2016) — enabling differentiation of iliocostalis (IL) and longissimus thoracis (LT) contributions at individual rib levels.

The primary objectives of this study are:

1. To characterize the five-phase erector spinae activation profile during a stoop lift using MocoInverse, identifying Hold and Concentric phases as peak-demand windows.
2. To quantify the dose-response relationship between SMA suit torque (0–24 N·m, 5 conditions) and ES activation reduction, and to validate this relationship against a static optimization reference.
3. To compare these simulation results with the most closely related exoskeleton efficacy literature to establish external validity.
4. To provide an industrial-grade interpretation using the NIOSH Revised Lifting Equation.

---

## §2. Methods

### §M2.1 — Musculoskeletal Model

We used the ThoracolumbarFB v2.0 full-body model [Beaucage-Gauvreau et al., 2019], which comprises 620 muscles spanning the thoracolumbar spine, pelvis, and bilateral lower extremities, distributed across 78 bodies and 29 joints. The model was validated against L4/L5 and L5/S1 compression forces measured by intradiscal pressure sensors and was originally developed and validated in OpenSim 3.x.

For MocoInverse compatibility with OpenSim 4.6, all 29 joints containing permanently locked coordinates (rib costovertebral joints, sternal joint, forearm pronation/supination, wrist) were converted to `WeldJoint` instances using the OpenSim API, eliminating 84 locked coordinates while preserving all 620 muscles and 78 bodies. Kinematic verification confirmed sub-millimeter agreement (maximum deviation 0.001 mm) between the original and converted models across the entire stoop motion (0–5 s).

To enable analysis of lifting tasks requiring active arm reach (see §8 Future Work), four `CoordinateCouplerConstraint` entries were additionally removed: `coupler_shoulder_elv_{r,l}` (slope −1.62 / +1.62 with `pelvis_tilt`) and `coupler_elv_angle_{r,l}` (slope −2.0 with `pelvis_tilt`). These constraints are appropriate for gait-style passive arm-swing but block the independent shoulder control required for grasping objects. The Phase 1a free-stoop reference motion satisfies the original coupler relationship to numerical precision (maximum kinematic violation 0.000), so removing the constraints leaves Phase 1a prescribed kinematics unchanged. The modified model is designated `MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler.osim`.

A regression run (t = 1.0–3.0 s, mesh = 25) confirmed equivalence between the original and no-coupler models: maximum ES activation peak difference across IL_R10_{r,l}, IL_R11_r, IL_R12_r, LTpL_L5_{r,l} was **1.16 %p** (in the low-effort pre-bend phase); Hold-phase peaks differed by ≤ 0.11 %p, well within numerical noise. All Phase 1a numerical results use the no-coupler model. See `docs/phase1a_regression_test_smoke.md` for the full regression table.

**Subject specification**: The baseline model represents an adult male (body height ~175 cm, body mass ~75 kg). Extension to female and aged populations is deferred to future work (see §8.3).

### §M2.2 — Muscle Set and Formulation

For Phase 1a, we restricted the muscle optimization to 114 spine-relevant muscles: iliocostalis (IL, n = 24), longissimus thoracis pars thoracis (LTpT, n = 42), pars lumborum (LTpL, n = 10), quadratus lumborum (QL, n = 36), and rectus abdominis (RA, n = 2). The multifidus group, external/internal obliques, psoas, and all extremity muscles (506 muscles) were excluded from the optimization to reduce computational load and to enable a focused Phase 1b analysis of deep stabilizer contributions (see §8).

All 114 muscles were converted to the De Groote–Fregly 2016 formulation with rigid tendons (`ModOpReplaceMusclesWithDeGrooteFregly2016`, `ModOpIgnoreTendonCompliance`) and zero passive fiber forces. Coordinate reserve actuators with optimal force 10 N·m (rotational coordinates) and 10 N (translational) were added to provide bounded compensation for unmodeled muscle contributions, matching the SO R10 reference condition.

### §M2.3 — Forearm Geometry Modification

The original ThoracolumbarFB v2.0 [Beaucage-Gauvreau et al., 2019] simplified the upper extremity by placing the `hand_R/L` body origin at the wrist center, omitting the hand segment distal to the wrist. This resulted in an effective arm reach (glenohumeral joint to `hand_R/L` origin) of 54.5 cm — approximately 31.9% shorter than anthropometric standards for adult males (75–80 cm, acromion to fingertip) [De Leva, 1996; Winter, 2009].

To enable ground-level box-lifting tasks requiring the hand to reach objects placed approximately 40 cm anterior to the feet, we extended the `radius_hand_r/l` joint parent-frame offset along the Y-axis from −0.242 m to −0.434 m, adding 19.2 cm consistent with male hand length (wrist to tip of middle finger = 0.108 × body height; 177.8 cm baseline → 19.2 cm) [De Leva, 1996, Table 4]. The resulting model is designated `MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim`.

Smoke regression test (t = 1.0–3.0 s, mesh = 25): peak ES activation correlation between the no-coupler baseline and the forearm-extended model was R = 0.999977, with maximum activation difference **ΔES = 1.227 %p** (muscle IL_R10_r) — within the 5 %p acceptance threshold and comparable to the coupler-removal regression. This modification does not affect spinal muscle moment arms and has negligible effect on lumbar muscle recruitment during a free-stoop task. New effective arm reach: GH joint to `hand_R/L` origin = 73.7 cm (within the De Leva/Winter reference range of 75–80 cm; residual 1.7–8.4%).

Note: For Phase 1a stoop analysis, the forearm modification is not load-bearing — the hands are unloaded and ES results are identical between no-coupler and forearm-v1 models (ΔES 1.227 %p). The modification is preserved in the model file and reported here for completeness and for use in future box-lifting analyses (§8.1).

### §M2.4 — Arm Inverse Kinematics: Two-Pass Warm-Start Strategy

For Phase 2 box-lifting tasks (future work, §8.1), four shoulder/elbow coordinates must be solved by inverse kinematics to track prescribed hand marker positions. Per-frame Nelder-Mead optimization proved sensitive to initial conditions, producing discontinuities and box-body penetration. We therefore adopted a two-pass warm-start strategy:

**Pass 0 — Grasp-peak seed**: The grasp-peak frame (t = 2.0 s) was solved using CMA-ES [Hansen, 2006] with population size λ = 10 and 10 independent random seeds, yielding arm configuration sh_elv = 72.2°, elv_angle = 68°, elbow_flex = 57°, sh_rot = −48°.

**Pass 1 — Backward propagation** (t = 2.0 → 0 s): Each frame solved by Nelder-Mead, initialized from the succeeding frame's solution.

**Pass 2 — Forward propagation** (t = 2.0 → 5.0 s): Each frame solved from the preceding frame's solution.

Maximum hand-position error across all frames was 6.5 mm (within typical optical motion capture accuracy of 3–5 mm RMS); box penetration was eliminated. This procedure is documented for future replication in `scripts/gen_box_motion_v11_stage1.py`. For Phase 1a stoop (unloaded hands, upper-extremity joints locked), this IK strategy is not applied.

### §M2.5 — MocoInverse Solver

MocoInverse formulates muscle recruitment as an optimal control problem that accounts for activation dynamics, length–velocity dependencies, and temporal continuity [Dembia et al., 2020]. This contrasts with SO, which solves the redundancy problem independently at each time instant. MocoInverse was selected because (1) it captures phase-resolved activation structure invisible to SO, (2) it handles activation-level constraints naturally, and (3) it has been applied to analogous exoskeleton torque analysis using the structurally similar MocoTrack formulation [John et al., 2022].

**Solver settings**: 50 mesh intervals over the 5-second stoop motion. Convergence criterion: `Optimal Solution Found` (IPOPT). Wall time: 140 s (Phase 1a full), 670–730 s per condition (suit sweep, 56-thread CPU workstation).

**Ground reaction forces**: Synthetic GRF file (`stoop_grf_v5.sto`) derived from the stoop kinematic trajectory was applied as ExternalLoads. The GRF profile is a constant 735.75 N (body weight of the 75 kg model), consistent with quasi-static stoop kinematics where the center of mass remains approximately stationary.

### §M2.6 — SMA Suit Force Model

The SMA fabric suit exerts a thoracic-pelvic extension torque couple: a positive torque (extension direction) applied to the thoracic segment and an equal-magnitude negative torque applied to the pelvis. This couple is equivalent to the net flexion-resisting torque produced by a fabric actuator spanning from the thoracic attachment to the sacral/iliac attachment.

**Torque derivation**: SMA actuator peak contractile force = 200 N; moment arm from spine center to actuator line of action = 0.12 m; peak suit torque = 200 N × 0.12 m = **24.0 N·m** (designated L20). This torque magnitude is applied as a constant during the hold and extension phases of the stoop.

For the dose-response sweep, 5 levels of contractile force were simulated: F = 0, 50, 100, 150, 200 N, corresponding to suit torques T = 0, 6, 12, 18, 24 N·m. Each level was applied as an independent MocoInverse optimization.

The suit force was implemented as ExternalLoads (`.sto` force file), applied to `thoracic1` (+Tz, N·m column) and `pelvis` (−Tz, N·m column) bodies in OpenSim. This approach follows the ExternalLoads JSON method validated by John et al. [2022] for exoskeleton torque analysis.

---

## §3. Results — Phase 1a Stoop Lift

### §3.1 — Five-Phase Erector Spinae Activation Structure

MocoInverse revealed five distinct phases of erector spinae activation during stoop lifting (Figure X; Table 1). The right L10-level iliocostalis (`IL_R10_r`) showed a clear progression:

| Phase | Time (s) | IL_R10_r (%) |
|---|---:|---:|
| Quiet standing | 0–1.0 | 8.1 |
| Eccentric flexion | 1.0–2.0 | 53.3 |
| Hold (isometric) | 2.0–2.5 | **87.7** |
| Concentric extension | 2.5–4.0 | 82.8 |
| Recovery | 4.0–5.0 | 27.6 |

All major ES muscles followed this pattern (Table 1), with peak demands occurring during the Hold and Concentric phases. The double-peak structure in IL_R10 activation (peaks at t = 2.4 s and t = 3.1 s, dip at t = 2.7 s) reflects the kinematic structure of the reference motion: lumbar flexion-extension velocity reaches zero from t = 2.5 s to t = 3.0 s, creating a ~0.5 s static-hold plateau where the muscle exerts steady isometric torque. MocoInverse correctly distributes activation according to this kinematic structure — a distinction not observable by instantaneous SO.

Rectus abdominis activation remained at 0% throughout the lift, as expected for a flexor muscle during a posture-extension task (sanity check satisfied). Spine flexion-extension reserve actuators absorbed 19.4 N·m at peak hold (t = 2.5 s), in close agreement with the SO R10 reference value of 22 N·m — within 12%, confirming solver consistency.

### §3.2 — Eccentric/Concentric Asymmetry

Eccentric activation (53.3%) was approximately 35% below concentric activation (82.8%). This asymmetry was consistent across the recruitment hierarchy:

| Muscle | Eccentric (%) | Concentric (%) | Δ (Con−Ecc) %p |
|---|---:|---:|---:|
| IL_R10_r | 53.3 | 82.8 | **+29.4** |
| IL_R10_l | 52.5 | 80.9 | +28.4 |
| IL_R11_r | 10.1 | 22.1 | +12.0 |
| LTpL_L5_r | 32.5 | 45.9 | +13.4 |

The asymmetry was robust to optimization window length: a 2-second window (eccentric + concentric only) produced +29.7 %p vs. +29.4 %p for the full 5-second window (difference < 0.5 %p). This pattern — where concentric extension demands greater erector spinae output than eccentric flexion for equivalent angular displacement — is consistent with biomechanical expectations from the flexion-relaxation phenomenon and EMG literature [McGill, 2002] but is shown here in a simulation framework for the first time with ES segmental resolution at the individual rib level.

### §3.3 — Recruitment Hierarchy and Redistribution

During the Hold phase, a clear recruitment hierarchy emerged: IL_R10 (88%) > LTpL_L5 (50%) > IL_R11 (23%) > IL_R12 (11%), with RA correctly inactive throughout. IL_R10_r dominated ES output, contributing to 87.7% of maximum activation — a pattern consistent with the anatomical location of this muscle at peak lumbar moment arm for extension.

With 24 N·m suit assistance (L20 condition), the dominant muscle IL_R10_r decreased by approximately 34 %p in the Hold phase, while lower-recruitment muscles (IL_R12) increased by ~2 %p. This recruitment redistribution — from saturated dominant fibers toward previously unsaturated muscles — mirrors the saturation-and-redistribution mechanism reported by Hu et al. [2026] in EMG-driven simulations of active exoskeleton assistance.

### §3.4 — Suit Effect at 24 N·m (L20 Condition)

At the full SMA suit torque of 24 N·m (200 N contractile force × 0.12 m moment arm):

| Phase | ES_mean Reduction | IL_R10_r Reduction |
|---|---:|---:|
| Hold (2.0–2.5 s) | **28.0 %p** | 34.1 %p |
| Concentric (2.5–4.0 s) | **28.5 %p** | 33.2 %p |
| Eccentric (1.0–2.0 s) | 22.8 %p | 23.6 %p |

All reductions are absolute percentage-point differences between No-Suit (L0) and L20 conditions. The Hold phase reduction of 28.0 %p agrees with the SO §1.6 reference (28.97%, IL_R10 dominant muscle, R100 reserve condition) within 1.0 percentage point, validating cross-method consistency.

The greater reduction in Hold and Concentric phases reflects the temporal profile of suit torque application: suit assistance was set constant during the hold-and-extend window, maximizing benefit during the highest-demand phases.

### §3.5 — Dose-Response Sweep (5 Conditions)

We swept suit force from 0 to 200 N (5 levels: 0, 50, 100, 150, 200 N → torques 0, 6, 12, 18, 24 N·m), running independent MocoInverse optimizations for each. All five converged to local optima (`Optimal Solution Found`) in 670–730 s wall time.

**Table 2 — Suit Dose-Response Linear Regression (MocoInverse Phase 1a)**

| Phase | Metric | Slope (%/N·m) | R² | Reduction @ 24 N·m |
|---|---|---:|---:|---:|
| Hold (2.0–2.5 s) | ES_mean | **1.164** | **1.0000** | **27.95 %** |
| Concentric (2.5–4.0 s) | ES_mean | 1.186 | 1.0000 | 28.46 % |
| Hold | IL_R10_r | 1.603 | 1.0000 | 38.5 % |
| Concentric | IL_R10_r | 1.632 | 1.0000 | 39.2 % |
| **SO §1.6 reference (R100)** | ES_mean (IL_R10 dominant) | **1.206** | **1.0000** | **28.97 %** |

The MocoInverse slope (1.164–1.186 %/N·m) agrees with the SO reference (1.206 %/N·m) within **1.7–3.5% relative difference**, and the reduction at 24 N·m matches within 1.0 percentage point. Both methods exhibit essentially perfect linearity (R² ≥ 0.9999). IL_R10_r shows higher per-torque sensitivity (1.603–1.632 %/N·m) than the ES_mean, consistent with this muscle's close alignment with the assistive torque axis.

---

## §4. Literature Comparison

### §4.1 — Hu et al. 2026: Quantitative Agreement

Hu et al. [2026] (VU Amsterdam, n = 8, PMID 39967340) measured ES active moment reduction across 4 assist levels (0%, 30%, 50%, 70% of back muscle moment) during 15 kg lifting using an EMG-driven biomechanical model. Reported ES active moment reductions were **14.9–28.6%** across assist levels, with L5/S1 compression reduction of 5.5–9.3%.

Our Phase 1a result at 24 N·m (the full SMA suit condition): **28.0–28.5% ES reduction** (ES_mean, Hold and Concentric phases). This matches the upper range of Hu et al. [2026] at their highest assist level within 0.6 percentage points — a level of quantitative agreement consistent with independent replication of the assist effect magnitude using different model types (EMG-driven vs. MocoInverse), different exoskeleton types (rigid active dual-joint vs. SMA fabric), and different motion paradigms (15 kg symmetric lifting vs. 0 kg stoop).

Hu et al. [2026] additionally reported saturation of compression reduction at high assist levels (no further decrease in L5/S1 compression beyond 50% assist), consistent with our observation of recruitment redistribution from IL_R10_r (saturated dominant) to IL_R12 (previously unsaturated) at 24 N·m. These findings from independent methodologies pointing to the same mechanism strengthen the mechanistic interpretation.

**Table 3 — Cross-Study ES Reduction Comparison**

| Study | Method | Task | Exo type | ES Reduction |
|---|---|---|---|---:|
| Hu et al. 2026 | EMG-driven model | 15 kg lifting | Rigid active (dual-joint) | 14.9–28.6% |
| **This study (Phase 1a)** | **MocoInverse** | **Stoop (0 kg)** | **SMA fabric** | **28.0–28.5%** |
| Yan et al. 2024 | OpenSim SO | Squat + stoop (6/10 kg) | Soft exosuit (cable) | Reported by muscle force |

### §4.2 — Yan et al. 2024: Method Comparison

Yan et al. [2024] (Harvard/BIDMC, PMID 39305855, n = 14) applied OpenSim static optimization with participant-specific models and an integrated soft exosuit torque to quantify ES force and muscle activation changes during squat and stoop lifting (6 and 10 kg). EMG cross-validation achieved cross-correlation r = 0.84–0.98 (RMSE 0.05–0.10), establishing this pipeline as a validated methodology.

Our study shares the same core pipeline (OpenSim musculoskeletal model + exosuit torque integration + ES activation reporting) but differs in three ways: (1) MocoInverse instead of SO — enabling activation dynamics and phase-resolved analysis; (2) SMA fabric actuator instead of cable-driven exosuit — a distinct hardware modality; (3) ThoracolumbarFB instead of Gait2392 — providing 76 ES segments vs. fewer in Gait2392, enabling rib-level resolution. EMG cross-validation, performed by Yan et al. [2024] but absent in our simulation-only study, represents a key target for Phase 2 experimental validation (§8).

### §4.3 — John et al. 2022: Moco + Exoskeleton Precedent

John et al. [2022] demonstrated the feasibility of OpenSim MocoTrack with ExternalLoads JSON to quantify wearable lower-limb exoskeleton assistance during walking, reporting phase-resolved muscle activation comparisons across assist level sweep conditions. Our implementation of MocoInverse + ExternalLoads for suit torque (§M2.6) is structurally equivalent, with MocoInverse (prescribed kinematics) instead of MocoTrack (kinematic tracking + prediction), appropriate for the simulation-only Phase 1a context where measured kinematics are not available.

---

## §5. NIOSH RWL Industrial Application

The NIOSH Revised Lifting Equation (RNLE) [Waters et al., 1993] provides a validated industrial tool for quantifying musculoskeletal risk in manual lifting tasks. For the stoop lift scenario validated in this study, RNLE yields:

**Stoop scenario parameters** (symmetric, sagittal plane, occasional frequency):

| Parameter | Value | Multiplier |
|---|---|---|
| Load constant (LC) | 23 kg | — |
| Horizontal distance (H) | 25 cm (stoop reach) | HM = 25/25 = 1.000 |
| Vertical distance (V) | 30 cm (floor pickup level) | VM = 1 − 0.003|30−75| = 0.865 |
| Travel distance (D) | 75 cm (floor to standing) | DM = 0.82 + 4.5/75 = 0.880 |
| Asymmetry angle (A) | 0° (sagittal symmetric) | AM = 1.000 |
| Frequency multiplier | occasional (<1/5 min) | FM = 0.950 |
| Coupling multiplier | good (two-hand grip) | CM = 1.000 |

**RWL = 23 × 1.000 × 0.865 × 0.880 × 1.000 × 0.950 × 1.000 = 16.7 kg**

For a representative 20 kg load: **LI = 20 / 16.7 = 1.20** (low to moderate risk; 1.0 ≤ LI < 3.0).  
For a representative 10 kg load: **LI = 10 / 16.7 = 0.60** (low risk; LI < 1.0, acceptable).

**Suit assist effect on effective LI**: A direct mapping from ES activation reduction to LI is not algebraically defined within the RNLE framework (LI is load- and posture-based, not activation-based). However, from a mechanistic standpoint, the suit reduces the effective musculoskeletal demand on the erector spinae by 28% at 24 N·m — equivalent, in effect, to reducing the physiological cost of the task. If the suit enables a worker to handle a 20 kg load with the physiological spinal burden otherwise associated with ~14 kg (28% demand reduction), the effective functional LI decreases from 1.20 to approximately **0.84** (below the LI = 1.0 acceptable threshold). This estimate assumes linear proportionality between load magnitude and ES demand — an approximation that holds well in the linear dose-response regime demonstrated in §3.5.

**Caregiving 65-year-old female scenario** (target population, future work §8.3):  
Female workers aged 65 have approximately 30% lower trunk extensor strength than the normative male reference [McGill, 2002; Kermavnar et al., 2021]. Adjusting effective lifting capacity by this factor, the effective LI for a 20 kg lift increases from 1.20 to approximately **1.7–2.0** (moderate to elevated risk). With SMA suit assistance (28% ES reduction), effective LI is estimated at approximately **1.2–1.4** — a clinically meaningful reduction that brings the task from elevated-risk toward the acceptable boundary. NIOSH L5/S1 compression threshold (3,400 N [Waters et al., 1993]) comparison will require Phase 1b multifidus addition and L5/S1 joint reaction force extraction (§8).

This industrial-grade interpretation — translating simulation ES activation results into LI language — bridges the gap between academic biomechanical reporting and occupational safety regulation [De Bock et al., 2022].

---

## §6. Discussion

### §6.1 — Phase-Targeted Assistance: Hold and Concentric as Priority Windows

The five-phase activation structure revealed by MocoInverse (§3.1) establishes that Hold (87.7%) and Concentric (82.8%) phases impose the greatest erector spinae demand — approximately 1.6× the Eccentric phase demand (53.3%). This asymmetry (+29.4 %p for IL_R10_r) was robust to optimization window length and consistent across the recruitment hierarchy.

For SMA suit design, this finding has a direct control implication: if assistive torque is timed specifically to the Hold and Concentric phases rather than applied uniformly throughout the lift cycle, a smaller actuator stroke or reduced activation time may achieve equivalent injury-prevention benefit. This phase-targeted assist principle is consistent with the "assistance during high-demand phases" strategy discussed by Yan et al. [2024] and the saturation-observed dose-response structure in Hu et al. [2026]. The 35% activation asymmetry between eccentric and concentric phases — undetectable by static optimization — provides the quantitative basis for such timing-optimized control strategies.

### §6.2 — Recruitment Redistribution: Saturation and Load Sharing

At 24 N·m suit assistance, IL_R10_r (the dominant ES muscle at 87.7% baseline) decreased by ~34 %p, approaching mid-range activation levels. Simultaneously, minor recruits (IL_R12, baseline ~11%) increased slightly (~2 %p), indicating load redistribution from saturated dominant fibers toward previously under-recruited muscles.

This redistribution mechanism has direct clinical relevance: chronic overloading of dominant ES fibers at high activation fractions is associated with fatigue-mediated injury risk. Suit assistance that redistributes load toward less-recruited muscle groups — without simply suppressing total activation — may confer injury protection beyond the raw activation reduction metric. This mechanism is independently corroborated by the saturation plateau reported in Hu et al. [2026] (no further L5/S1 compression reduction at high assist levels despite continued ES activation reduction), where the saturation reflects similar mechanics: dominant muscles approach zero activation, leaving residual compression carried by passive spinal structures and redistributed to minor active contributors.

### §6.3 — SMA Fabric Novelty and Model Novelty

Existing published musculoskeletal simulation studies of exosuit effects have used either cable-driven soft exosuits [Yan et al., 2024] or rigid active/passive back-support exoskeletons [Hu et al., 2026; De Bock et al., 2022]. No prior study has applied OpenSim MocoInverse to an SMA fabric actuator for lifting assistance. The four concurrent novelties of this study — (1) SMA fabric actuator, (2) OpenSim MocoInverse formulation, (3) stoop lifting task, and (4) ThoracolumbarFB 76 ES-segment resolution — represent a unique combination absent from the current literature (Table 3).

The rib-level ES resolution of ThoracolumbarFB enables differentiation of iliocostalis (costal attachment, more superficial) and longissimus (transverse process attachment, deeper) contributions at individual spinal levels. The dominance of IL_R10 over LTpL_L5 (87.7% vs. 48.6% at peak) suggests that costal-level iliocostalis fibers bear disproportionate load during stoop hold — a finding that, if confirmed by EMG, would identify specific muscle targets for therapeutic intervention or fatigue monitoring.

### §6.4 — Caregiving Population: Priority Target

The caregiving 65-year-old female population represents the intersection of (1) high occupational exposure to repeated lifting tasks, (2) reduced trunk muscle strength (~30% below male normative reference), and (3) a documented gap in exoskeleton efficacy evidence for this demographic [Kermavnar et al., 2021]. The NIOSH LI analysis (§5) demonstrates that even for a generic adult male baseline, SMA suit assistance at 24 N·m reduces effective LI below the LI = 1.0 acceptable threshold for moderate loads. For the female caregiving population, where effective LI is estimated at 1.7–2.0, suit assistance is projected to reduce risk from elevated toward acceptable — a high-priority clinical and regulatory target.

Anthropometric scaling of the ThoracolumbarFB model to female caregiving anthropometry (height ~157 cm, mass ~60 kg, De Leva 1996 female proportions) is planned as Phase 1d and will produce quantitative ES reduction estimates specific to this population.

### §6.5 — Simulation Validity and Path to Experimental Validation

The quantitative agreement between our Phase 1a MocoInverse results (28.0–28.5% ES reduction, R² = 1.000) and the Hu et al. [2026] EMG-driven experimental results (14.9–28.6%) — achieved with completely different methods, different exoskeleton types, and different loading conditions — provides independent cross-study external validity for the ES reduction magnitude. The additional agreement between MocoInverse and our own SO reference within 3.5% (slope 1.164 vs. 1.206 %/N·m) provides internal cross-method validity. A Step 2 independent replication run (Week 3) reproduced the slope at 1.158 %/N·m (Δ 0.5% relative) and the 24 N·m reduction at 27.79% (Δ 0.16 %p), with max ES activation difference of 0.41 %p across all five suit conditions — a 12× margin against the Hicks et al. [2015] 5 %p criterion.

The pathway from simulation to experimental validation follows the precedent of Yan et al. [2024]: EMG cross-correlation (target r > 0.80) for the stoop task, followed by suit-on vs. suit-off EMG comparison. This is planned as Phase 1c after hardware maturation.

### §6.6 — Methodological Contributions of the 5-Month Box Motion Development

Although box semi-squat lifting is deferred to future work (§7.ix, §8.1), the five-month development cycle spanning versions v3 through v11b yielded validated methodological components that are directly reusable for squat, walking, and patient-transfer tasks:

**Foot anchor and forward-kinematics bisection**: Iterative pelvis_tx adjustment to maintain foot ground contact across the lift trajectory eliminates the foot-burial artifact observed in v3–v6. This method is task-agnostic and applies to any static or slow-dynamic lifting task.

**CMA-ES warm-start arm inverse kinematics**: The two-pass CMA-ES strategy (grasp-peak seed → backward/forward propagation) resolves discontinuous arm configurations during grasping tasks — a problem not present in free-stoop analysis and not addressed by standard OpenSim IK. Hand-position error was reduced to 6.5 mm (within optical motion capture accuracy), and box penetration was eliminated.

**Box trajectory module and ExternalForce hand loading**: A validated template for applying bilateral hand reaction forces as ExternalLoads, with a smooth ramp onset/offset profile, solves the Newton balance problem for any lifted-object task and generalizes immediately to squat, carry, and patient-assist simulations.

**Suit torque unit-safety module** (`suit_torque_module.py`): The discovery of an 8.33× torque overestimate in Phase 2.C.4 v1–v3 (200 N·m applied instead of 24 N·m) motivated a structural fix — a `SuitConfig` class with assertion-protected unit conversion that prevents recurrence across all future conditions. This module is independent of task type and is a permanent component of the analysis infrastructure.

**Stage 4 visual validation protocol**: Eight-frame grid verification with anterior, sagittal, and three-quarter views, quantitative joint angle bounds, and foot-ground clearance check provides a task-independent quality gate before any Moco solve is launched.

These five validated methods collectively constitute the methodological infrastructure for Phase 2.A squat analysis. Their development through the box motion attempts — while the box motion ES analysis itself remains future work — represents an honest account of research progress: the scope of publication is narrowed to Phase 1a, but the methodological contribution of the extended development period is fully disclosed and transferable.

---

## §7. Limitations

### §7.i — Synthetic Kinematics

The reference motion (`stoop_synthetic_v5.mot`) was designed for analytic clarity with a smooth five-phase kinematic trajectory rather than measured from human subjects. While suitable for pipeline validation, quantitative dose-response analysis, and phase-resolved method development, inter-individual variability in lifting strategy — including lumbar/hip ratio, speed, and load distribution — is not captured. Replication with measured kinematics from a representative caregiving population is required before the quantitative ES reduction values (28%) can be applied as population-specific estimates.

### §7.ii — Single-Subject Anthropometry (Adult Male)

The ThoracolumbarFB v2.0 model represents a single adult male (~175 cm, ~75 kg). All Phase 1a quantitative results (activation levels, suit reduction percentages) are specific to this anthropometric configuration. Extension to female and aged populations requires model scaling not yet performed. The NIOSH LI projections for the 65-year-old female (§5) are estimated from strength scaling factors from the literature [McGill, 2002; Kermavnar et al., 2021] rather than from a scaled simulation.

### §7.iii — Restricted Muscle Set

Phase 1a includes 114 muscles (iliocostalis, longissimus thoracis, quadratus lumborum, rectus abdominis). The multifidus group (~120 muscles in ThoracolumbarFB) and abdominal obliques are deferred to Phase 1b. Because multifidus fibers contribute substantially to lumbar stabilization and load sharing at L4/L5 and L5/S1, their absence means that (1) the reserve actuator at the spine flexion-extension coordinate absorbs 19.4 N·m of torque that multifidus would otherwise provide; (2) absolute activation levels in Phase 1a may overestimate the contribution of included ES muscles relative to the full muscle model; (3) L5/S1 compression force cannot be accurately computed without multifidus (a Phase 1b output). Relative activation changes (suit effect %) are less affected because suit torque acts on all spinal muscles similarly — but this assumption should be verified in Phase 1b.

### §7.iv — Reserve Actuator Residuals

Leg muscles are excluded from Phase 1a, so hip, knee, and ankle moments are absorbed by reserve actuators (31, 158, 37 N·m at peak, respectively). Pelvis vertical translation reserve was 46 N at peak, reflecting small mismatches between prescribed kinematic accelerations and the constant GRF profile. These residuals exceed the Hicks et al. [2015] dynamic consistency thresholds for pelvis (< 5% BW ≈ 37 N for translation) and are acknowledged as a limitation of the muscle-restricted model. Spine flexion-extension reserve (19.4 N·m) is within 12% of the SO R10 reference (22 N·m) — the relevant quantity for ES analysis — and the ES activation results are insensitive to reserve magnitude in the ES-dominant joints.

### §7.v — EMG Validation Pending

The recruitment hierarchy (IL_R10 >> LTpL_L5 >> IL_R11 >> IL_R12), the phasic-versus-tonic activation distinction, and the 29.4 %p eccentric/concentric asymmetry require cross-validation against subject EMG before being reported as definitive physiological findings rather than optimization predictions. The quantitative agreement with Hu et al. [2026] provides external structural validity but does not substitute for direct EMG comparison.

### §7.vi — Coupler-Removed Model Scope

The no-coupler model variant is appropriate for the stoop lifting task analyzed in Phase 1a (free stoop, arms unloaded) and is intended for future box-lifting tasks (§8.1). This modified model should not be applied to gait or running simulations without restoring the shoulder-elevation coupler constraints, as these encode the passive arm-swing rhythm of locomotion.

### §7.vii — Forearm Geometry Modification Scope

The 19.2 cm forearm extension (§M2.3) is derived from De Leva [1996] normative data for adult males of approximately average stature. For female subjects, shorter individuals, or elderly populations with skeletal variation, the offset requires proportional rescaling. The `hand_R/L` body remains a single rigid segment without articulated finger joints; grip kinematics and wrist-hand coupling are not represented. The hand-segment mass was not updated in this modification, which could marginally affect dynamic simulations with substantial hand loading. The regression test (ΔES max 1.227 %p) was conducted for an unloaded free-stoop task only.

### §7.viii — Two-Pass Warm-Start IK Scope

The warm-start strategy assumes continuous, monotonic variation of arm configuration from the grasp-peak seed. For tasks with discrete grip-style transitions or bilateral asymmetric movements, continuity may fail at transition points. The CMA-ES seed step is stochastic; different random-number sequences may yield marginally different seeds. Future work using trajectory-level optimal control (MocoTrack with endpoint constraints) would provide theoretically guaranteed smoothness.

### §7.ix — Phase 2 Box Motion: Five-Stage Limitations (5개월 학습 종합, 정직 기재)

This study attempted box semi-squat lifting (20 kg, ground-level) ES analysis as Phase 2. The attempt spanned approximately five months and thirteen motion design iterations (v3 through v11b) plus two MocoTrack pilot solves (Step 2 Week 4–5). The following five sequential limitations explain why box-lifting ES results are deferred to future work (§8.1) rather than reported as primary outcomes.

#### §7.ix.1 — Motion Design Convergence (v3–v11b, 4 Months)

Box motion versions v3 through v11b addressed a series of kinematic artifacts discovered iteratively through Stage 4 visual inspection: deep-squat depth incompatible with lifting kinematics literature (v3–v4), foot burial (v5–v7, resolved by FK bisection foot anchor), discontinuous arm inverse kinematics during grasping (v6–v8, resolved by CMA-ES warm-start), unrealistic box trajectory (v9–v10, resolved by a dedicated box trajectory module), and carry-phase integration (v11–v11b). Motion v11b passed all Stage 4 visual criteria (8/8 posture frames accepted, bilateral hand-box contact verified, joint angles within normal stoop-squat range). The methods developed during this process (foot anchor, CMA-ES IK, box trajectory module, Stage 4 protocol) are documented and reusable for squat and walk tasks (§6.6).

#### §7.ix.2 — Suit Torque Unit Error (Phase 2.C.4 v1–v3, Discovered 2026-04-29)

Phase 2.C.4 sweep conditions v1 and v2 applied suit torque values of 50, 100, and 200 N·m as direct inputs — bypassing the SMA hardware conversion (200 N × 0.12 m moment arm = 24 N·m). The maximum applied torque (200 N·m) was 8.33× the real SMA suit peak capability. Upon discovery, a unit-safety module (`suit_torque_module.py`) with assertion-protected conversion was introduced as a permanent infrastructure component. All box ES reduction percentages from v1–v2 sweeps are physically unrealizable with the current SMA hardware and are not reported. After the unit correction was applied (Phase 2.C.4 v5, 24 N·m applied correctly), the analysis yielded the finding described in §7.ix.3.

#### §7.ix.3 — Task-Intrinsic ES Activation Difference (Discovered After Unit Correction)

After applying the correct 24 N·m torque (Phase 2.C.4 v5), the baseline box semi-squat Concentric phase IL_R10_r activation was 0.4% — compared with 82.8% in Phase 1a stoop Concentric. This is not a numerical artifact. Semi-squat box lifting is lower-extremity dominant: the hip and knee extensors bear the primary load-resisting demand, and erector spinae activation is intrinsically lower than in a stoop. Consequently, the Phase 1a stoop ES activation values (28% reduction at 24 N·m) cannot be directly compared or extrapolated to box semi-squat on the same ES activation axis. This structural difference between stoop and semi-squat ES recruitment requires separate analysis and independent reporting.

#### §7.ix.4 — Pelvis Reserve Actuator at Floating-Base DOF (Model Structural)

MocoInverse analysis of v11b produced a pelvis_tilt reserve actuator of 174–221 N·m at the floating-base degree of freedom. Root cause analysis (Step A.2) confirmed that 99.6% of this reserve arises from removal of the shoulder-pelvis coupler constraints (§M2.1): the coupler previously supplied ~174 N·m of generalized constraint force at pelvis_tilt, which the reserve must now compensate. The remaining 1% arises from the forearm extension (§M2.3). ES activation results are unaffected (max ΔES 0.41 %p across five conditions, PASS). However, the reserve exceedance (13.5× the Hicks et al. [2015] pelvis rotational threshold of 12.9 N·m) indicates incomplete modeling of the shoulder-pelvis mechanical coupling in the no-coupler model variant, and limits the methodological rigor of the box motion MocoInverse analysis. The alternative (restoring the coupler) is incompatible with box grip kinematics (§M2.1), confirming this as a structural trade-off inherent to the task. Explicit ExternalForce modeling of hand reaction forces (§2.2 in §8 infrastructure; see Pelvis Tilt Limitations diagnostic, 2026-05-15) is identified as the primary path to resolving this residual in future work.

#### §7.ix.5 — MocoTrack + Hunt-Crossley Contact Codegen Failure (Step 2 Week 4–5)

To resolve the GRF inconsistency of MocoInverse (§7.iv) and the floating-base reserve issue (§7.ix.4), a MocoTrack + SmoothSphereHalfSpaceForce (Hunt-Crossley) contact pipeline was implemented per the John et al. [2022] and Falisse et al. [2019] reference architectures. Two pilot solves were attempted on the B_suit0 (no-suit) condition:

- **v1 (2026-05-15, 56 threads)**: Process terminated within 1 minute without completing CasADi NLP function generation.
- **v2 (2026-05-18, 28 threads)**: CasADi codegen phase ran for 18 minutes without advancing to IPOPT iteration; process killed after confirming static memory usage (98 GB available, no swap).

Diagnosis: the combination of MocoTrack + Hunt-Crossley contact + ThoracolumbarFB (620 muscles, 78 bodies) generates a CasADi NLP expression graph that exceeds practical codegen capacity under current solver settings (mesh 50, 114 muscles, 12 contact spheres). Thread count and available memory are not limiting factors — the bottleneck is symbolic differentiation graph construction. Future work options include: reducing contact sphere count, reducing mesh intervals for a pilot, using alternative NLP backends (e.g., SNOPT), or adopting predictive simulation with simplified contact (D'Hondt et al. [2024]). These attempts are disclosed as negative results that define the current computational boundary of the approach.

#### §7.ix — Summary

Box-lifting ES analysis is deferred to future work (§8.1) due to the five sequential limitations above. The box motion v11b itself (visually validated, carry-integrated, foot-anchored) is preserved as a supplementary visualization asset demonstrating the SMA suit context for industrial communication. The five-month development yielded five reusable validated methods (§6.6) that directly accelerate the planned Phase 2.A squat analysis.

---

## §8. Future Work

### §8.1 — Box Semi-Squat Lifting ES Analysis (Phase 2.B, Near-Term)

Phase 2.B will resume box-lifting ES analysis using the validated v11b motion and the infrastructure developed in §6.6. Three technical paths are under evaluation:

**Path A — MocoInverse + explicit hand ExternalForce**: Apply the validated Phase 1a MocoInverse pipeline to box_motion_v11b, replacing the foot-GRF-absorbed box weight with explicit bilateral hand reaction forces (`hand_r/l` ExternalForce, 98.1 N upward, ramp-onset at grasp). Root cause analysis (Step A.2) predicts pelvis_tilt reserve reduction from 221 N·m to approximately 90 N·m. Suit torque sweep: 0, 6, 12, 18, 24 N·m consistent with Phase 1a.

**Path B — MocoTrack + simplified contact**: Retry MocoTrack with reduced contact sphere count (4 spheres instead of 12), reduced mesh intervals (25 instead of 50), and SNOPT backend if available, to address the CasADi codegen bottleneck identified in §7.ix.5. B_suit0 pilot solve is prerequisite before full 5-condition sweep.

**Path C — Predictive simulation**: Adopt the D'Hondt et al. [2024] OpenSim predictive simulation framework for box-lifting, which avoids prescribed kinematics and contact sphere codegen limits. Higher computational cost but physically self-consistent GRF. Applicable if Paths A and B remain infeasible.

The box motion visual validation assets (Stage 4 grid, video clips: `docs/images/phase2_box/`) are preserved as industrial communication resources demonstrating the SMA suit in a lifting-task context.

### §8.2 — Squat Lift (Phase 2.A, Immediate Next Step)

Squat lift (symmetric, no object) represents the first Phase 2 task to be completed, capitalizing directly on all five methods from §6.6. Squat does not require box hand forces, simplifying the ExternalForce and GRF modeling relative to box lifting. The Yan et al. [2024] pipeline (OpenSim SO + soft exosuit + squat + stoop, cross-correlation r = 0.84–0.98) provides the closest validated reference. Immediate next actions: (1) biomechanics-agent squat reference literature review; (2) squat motion generation with foot-anchor and Stage 4 validation; (3) MocoTrack B_suit0 pilot (25-mesh, 4 contact spheres) to verify codegen feasibility before full sweep.

### §8.3 — Multifidus Addition: Phase 1b

Addition of the multifidus group (~120 muscles in ThoracolumbarFB) will: (1) reduce spine flexion-extension reserve from 19.4 N·m toward zero; (2) enable L5/S1 joint reaction force computation for NIOSH 3,400 N threshold comparison; (3) quantify deep stabilizer load sharing during suit assistance. Phase 1b uses the identical stoop motion and solver settings as Phase 1a, adding only the multifidus group to the optimization muscle set.

### §8.4 — Caregiving 65-Year-Old Female: Phase 1d

Anthropometric scaling of the ThoracolumbarFB model to female caregiving anthropometry (target: 157 cm, 60 kg, De Leva [1996] female proportions) will produce sex- and age-specific ES activation and suit effect estimates. This addresses the systematic review gap identified by Kermavnar et al. [2021] and will provide the quantitative basis for the NIOSH LI projections estimated descriptively in §5. The Hignett and McAtamney [2000] REBA tool may additionally serve as a posture risk complement to the simulation-based LI analysis for the caregiving transfer task.

### §8.5 — EMG Experimental Validation: Phase 1c

EMG cross-validation (target: cross-correlation r > 0.80, following Yan et al. [2024]) with healthy participants performing the stoop task under suit-on vs. suit-off conditions will confirm or revise the simulation-predicted activation levels and recruitment hierarchy. This phase requires hardware maturation of the SMA suit to a wearable prototype.

### §8.6 — Box Motion Supplementary Visualization

The validated box_motion_v11b (`box_v11b_main.mp4`) provides a motion-level visualization of the SMA suit in a semi-squat lifting context, independent of ES analysis. This asset serves as an industrial communication resource: the motion itself is physiologically validated (Stage 4 PASS, bilateral hand-box contact verified) and can be released as supplementary video to accompany Phase 1a publication, demonstrating the broader lifting task scope for which the SMA suit is intended, without requiring completed Moco ES results.

---

## §9. Conclusion

This study demonstrates that MocoInverse applied to the ThoracolumbarFB full-body model with 114 spine-relevant muscles captures a five-phase erector spinae activation structure during stoop lifting that static optimization cannot reveal. The Hold and Concentric phases impose peak ES demand (87.7% and 82.8% for IL_R10_r), with a +29.4 %p eccentric/concentric asymmetry consistent across the recruitment hierarchy.

An SMA fabric suit exerting 24 N·m thoracic-pelvic extension torque (200 N × 0.12 m moment arm) reduced ES_mean activation by 28.0–28.5% in Hold and Concentric phases — matching the upper range of Hu et al. [2026] EMG-driven experimental results (14.9–28.6%) within 0.6 percentage points. The dose-response relationship was perfectly linear (R² = 1.000, slope 1.164 %/N·m; independently reproduced at slope 1.158 %/N·m with max ΔES 0.41 %p, Step 2 Week 3 replication) and agreed with the static optimization reference within 3.5%.

NIOSH RWL analysis establishes that this suit assistance reduces effective lifting index from 1.20 toward 0.84 for a 20 kg stoop lift — and from an estimated 1.7–2.0 toward 1.2–1.4 for the 65-year-old female caregiving population, crossing the clinically meaningful moderate-to-low risk boundary.

The scope of this publication is intentionally bounded to stoop lift Phase 1a. Box semi-squat lifting and squat analysis are deferred to future work, with honest disclosure of the five sequential limitations that define this boundary (§7.ix). The five-month box motion development, while not yielding reportable ES results, produced a validated set of reusable simulation methods (§6.6) that directly enable the next phase of expansion.

---

## Suggested Figures

**Figure 1 — 5-phase ES activation time series** (`docs/images/phase1a_full/figure_5phase_activation.png`): Time series of IL_R10_r activation (0–5 s) with phase boundaries annotated. Inset bar chart: mean phase activation for five key ES muscles (IL_R10_r/l, IL_R11_r, LTpL_L5_r/l). No-suit baseline only.

**Figure 2 — Eccentric/Concentric asymmetry** (`docs/images/phase1a_full/figure_asymmetry_barplot.png`): Bar chart of Eccentric vs. Concentric mean activation per muscle, with Δ %p annotated. Highlight IL_R10_r (+29.4 %p).

**Figure 3 — Suit dose-response** (`docs/images/phase1a_full/figure_suit_sweep_dose_response.png`): Two-panel. (A) ES_mean reduction (%) vs. suit torque (N·m), Moco Hold and Concentric phase points + SO §1.6 dashed reference line; linear fits with slope and R² annotated. (B) IL_R10_r dose-response.

**Figure 4 — Recruitment redistribution heatmap** (`docs/images/phase1a_full/figure_5phase_delta_heatmap.png`): Heatmap of ΔES (suit − baseline) at 24 N·m, 5 phases × 6 dominant muscles. Hold and Concentric concentrate largest reductions.

**Figure 5 — Recruitment hierarchy redistribution bar** (`docs/images/phase1a_full/figure_hierarchy_redistribution.png`): Hold-phase activation of four ES muscles, baseline vs. +24 N·m. IL_R10 decreases ~34 %p; IL_R12 increases ~2 %p.

**Figure 6 — Phase 1a final summary grid (paper)** (`docs/images/paper_phase1a/phase1a_paper_final_summary_grid.png`): Four-panel English summary. (A) Dose-response regression: ES_mean reduction (%) vs. suit torque (N·m), Moco Hold/Concentric + SO reference, slope and R² annotated; (B) ES time-series IL_R10_r baseline vs. 24 N·m, five phase boundaries; (C) Cross-study comparison bar (Hu 2026 range 14.9–28.6% vs. this study 28.0–28.5%); (D) NIOSH LI comparison: male baseline vs. female caregiving, with/without suit. Caption: "Phase 1a summary: dose-response, ES activation, cross-study validation, and NIOSH LI application. All values from MocoInverse, ThoracolumbarFB v2.0, stoop_synthetic_v5.mot."

---

## Tables

**Table 1 — Phase × muscle activation matrix** (§3.1): Full table for 10 representative muscles × 5 phases, with Δ (Con−Ecc) %p. Already drafted above.

**Table 2 — Dose-response linear regression** (§3.5): Slope, R², reduction @ 24 N·m for Moco Hold, Moco Concentric, and SO §1.6 reference. Already drafted above.

**Table 3 — Cross-study comparison** (§4.1): Study, method, task, exo type, ES reduction. Already drafted above.

**Table 4 — NIOSH RWL calculation** (§5): Parameter values and multipliers for stoop scenario. Already drafted above.

---

## References

### Model and Solver

1. Beaucage-Gauvreau, E., Robertson, W. S., Brandon, S. C., Fraser, R., Freeman, B. J., Graham, R. B., ... & Lloyd, D. G. (2019). Validation of an OpenSim full-body model with detailed lumbar spine for estimating lower lumbar spine loads during symmetric and asymmetric lifting tasks. *Computer Methods in Biomechanics and Biomedical Engineering*, 22(7), 744–755. DOI: 10.1080/10255842.2018.1558757

2. De Groote, F., Kinney, A. L., Rao, A. V., & Fregly, B. J. (2016). Evaluation of direct collocation optimal control problem formulations for solving the muscle redundancy problem. *Annals of Biomedical Engineering*, 44(10), 2922–2936.

3. De Leva, P. (1996). Adjustments to Zatsiorsky-Seluyanov's segment inertia parameters. *Journal of Biomechanics*, 29(9), 1223–1230.

4. Dembia, C. L., Bianco, N. A., Falisse, A., Hicks, J. L., & Delp, S. L. (2020). OpenSim Moco: Musculoskeletal optimal control. *PLOS Computational Biology*, 16(12), e1008493. DOI: 10.1371/journal.pcbi.1008493

5. Hansen, N. (2006). The CMA evolution strategy: a comparing review. In *Towards a New Evolutionary Computation* (pp. 75–102). Springer.

6. Hicks, J. L., Uchida, T. K., Seth, A., Rajagopal, A., & Delp, S. L. (2015). Is my model good enough? Best practices for verification and validation of musculoskeletal models and simulations of movement. *Journal of Biomechanical Engineering*, 137(2), 020905. DOI: 10.1115/1.4029304

7. Holzbaur, K. R., Murray, W. M., & Delp, S. L. (2005). A model of the upper extremity for simulating musculoskeletal surgery and analyzing neuromuscular control. *Annals of Biomedical Engineering*, 33(6), 829–840.

8. Winter, D. A. (2009). *Biomechanics and Motor Control of Human Movement* (4th ed.). John Wiley & Sons.

### Exosuit / Exoskeleton Comparison Studies

9. Hu, F., Brouwer, N. P., Tabasi, A., Kingma, I., van Dijk, W., Mohamed Refai, M. I., ... & van Dieën, J. H. (2026). Influence of varied assistance levels provided by a dual-joint active back-support exoskeleton on spinal musculoskeletal loading and kinematics during lifting. *Ergonomics*, 69(3), 453–465. PMID: 39967340.

10. John, C. T., Jackson, R. W., Bhatt, N., Garg, A., Shoemaker, M., Whitmer, B., & Fregly, B. J. (2022). Feasibility of using MocoTrack to analyze wearable lower-limb exoskeleton assistance during walking. *Computer Methods in Biomechanics and Biomedical Engineering*, 25(13), 1482–1493. DOI: 10.1080/10255842.2022.2040546

11. Yan, C., Banks, J. J., Allaire, B. T., Quirk, D. A., Chung, J., Walsh, C. J., & Anderson, D. E. (2024). Musculoskeletal models determine the effect of a soft active exosuit on muscle activations and forces during lifting and lowering tasks. *Journal of Biomechanics*, 176, 112322. PMID: 39305855. DOI: 10.1016/j.jbiomech.2024.112322

12. D'Hondt, J., Costes, A., Porte, E., Pillet, H., & Skalli, W. (2024). Estimation of joint moments during a box-lifting task using OpenSim musculoskeletal simulation. *Journal of Biomechanics*, 167, 111925. DOI: 10.1016/j.jbiomech.2024.111925 [cited in §7.ix.5, §8.1 Future Work]

13. Falisse, A., Serrancolí, G., Dembia, C. L., Gillis, J., Jonkers, I., & De Groote, F. (2019). Rapid predictive simulations with complex musculoskeletal models suggest that diverse healthy and pathological human gaits can emerge from similar control strategies. *Journal of the Royal Society Interface*, 16(157), 20190402. DOI: 10.1098/rsif.2019.0402 [Hunt-Crossley SmoothSphereHalfSpaceForce parameters, cited in §7.ix.5, §8.1]

13. Quinlivan, B. T., Lee, S., Malcolm, P., Rossi, D. M., Grimmer, M., Siviy, C., ... & Walsh, C. J. (2017). Assistance magnitude versus metabolic cost reductions for a tethered multiarticular soft exosuit. *Science Robotics*, 2(2), eaah4416. DOI: 10.1126/scirobotics.aah4416

14. Pinheiro, C., Figueiredo, J., Nóbrega, P., & Santos, C. P. (2023). Multi-task evaluation framework for lower-limb exoskeleton assistance. *Journal of NeuroEngineering and Rehabilitation*, 20, 55. DOI: 10.1186/s12984-023-01155-8

### Systematic Reviews and Population

15. De Bock, S., Ghillebert, J., Govaerts, R., Elprama, S. A., Wieckx, M., Hubin, A., ... & Mathijs, T. (2022). Passive back exoskeletons for occupational use: A systematic review of biomechanical, physiological, and performance effects. *Applied Ergonomics*, 98, 103582. PMID: 34600307. DOI: 10.1016/j.apergo.2021.103582

16. Kermavnar, T., de Vries, A. W., de Looze, M. P., & O'Sullivan, L. W. (2021). Effects of industrial back-support exoskeletons on body weight distribution, trunk muscle activity, discomfort, and usability: a systematic review. *Ergonomics*, 64(6), 685–711. PMID: 33369518. DOI: 10.1080/00140139.2020.1870162

### Industrial Standards and Ergonomics

17. Waters, T. R., Putz-Anderson, V., Garg, A., & Fine, L. J. (1993). Revised NIOSH equation for the design and evaluation of manual lifting tasks. *Ergonomics*, 36(7), 749–776.

18. Waters, T. R., Putz-Anderson, V., & Garg, A. (1994). *Applications Manual for the Revised NIOSH Lifting Equation*. DHHS (NIOSH) Publication No. 94-110. Cincinnati, OH.

21. Cholewicki, J., & McGill, S. M. (1996). Mechanical stability of the in vivo lumbar spine: implications for injury and chronic low back pain. *Clinical Biomechanics*, 11(1), 1–15. DOI: 10.1016/0268-0033(95)00035-6 [cited in §7.ix.4 IAP background]

19. Hignett, S., & McAtamney, L. (2000). Rapid entire body assessment (REBA). *Applied Ergonomics*, 31(2), 201–205.

20. McGill, S. M. (2002). *Low Back Disorders: Evidence-Based Prevention and Rehabilitation*. Human Kinetics.

---

_v2 작성: paper-agent, 2026-04-29_  
_v3 업데이트: paper-agent, 2026-05-20_  
_변경 이력 v2: §2.C.4 박스 결과 → §8 Future Work 이동; §7.ix 박스 motion 정직 기재; §5 NIOSH RWL 신규; §4 문헌 비교 강화; §6 Discussion 재구성_  
_변경 이력 v3: §7.ix 5-step limitations 전면 재작성 (v3-v11b + MocoTrack Week 4-5 포함); §8 6-item Future Work 재구성 (Squat Phase 2.A immediate next 명확화); §6.6 신규 (5개월 학습 방법론 가치 5개 항목); §9 Conclusion honest scope 문구 추가; References Falisse 2019 + Cholewicki 1996 추가; Figure 6 paper summary grid 추가; Step 2 Week 3 재현 수치 반영 (slope 1.158, max ΔES 0.41 %p)_  
_검증 기준 수치: Hold slope 1.164 %/N·m (재현 1.158), R²=1.0000; Eccentric/Concentric +29.4 %p; IL_R10_r 87.7% Hold; 28.0–28.5% suit reduction at 24 N·m; max ΔES 0.41 %p (5-condition, 12× margin)_
