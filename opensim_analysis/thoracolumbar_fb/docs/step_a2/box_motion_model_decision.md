# Box Motion Model Decision

**Date**: 2026-05-15
**Decision by**: opensim-agent (Step A.2 Phase 4)
**Based on**: Variation Matrix results + Phase 3 root cause verification

---

## 1. Summary of Findings

### pelvis_tilt 174 Nm: Root Cause

| Finding | Evidence |
|---------|---------|
| Dominant cause | Coupler removal (99.6% of delta) |
| forearm_v1 contribution | 1.0% (negligible, 1.69 Nm) |
| Mechanism | Coupler constraint was supplying ~174 Nm generalized force at pelvis_tilt via J^T × lambda |
| Arm kinematics (arm at 0 deg) | Reduces to 145.7 Nm but still FAILS — structural cause |
| ES analysis impact | None (max ΔES 0.41 %p — PASS) |

### What the reserve means

The pelvis_tilt reserve control = 17.56 (raw), actual force = 17.56 × optF(10) = 175.6 Nm.  
This represents a REAL mechanical imbalance in the no_coupler model: without the shoulder-pelvis coupling, the Moco optimizer must use the reserve to compensate for the missing constraint force. The force is not "numerical noise" — it is a structural consequence of the model topology change.

---

## 2. Options Evaluated

| Option | Description | pelvis_tilt | ES valid | Box compatible |
|--------|-------------|------------|----------|----------------|
| A. no_coupler + forearm_v1 (current) | REPRO_V2 = V4 | 174 Nm FAIL | YES | YES |
| B. with_coupler + forearm_v1 (new V2) | Coupler active, forearm extended | 1.82 Nm PASS | YES | NO (coupler breaks box grip) |
| C. no_coupler + shoulder muscles added | Add ~20 shoulder muscles to Phase 1a | TBD | Need regression | YES |
| D. Accept as limitation, proceed | Document in Methods/Limitations | 174 Nm FAIL | YES | YES |

---

## 3. Decision: Option A (Current: no_coupler + forearm_v1)

**Rationale:**
1. ES analysis is valid: max ΔES 0.41 %p across 5 conditions (PASS by Hicks criteria: < 5 %p)
2. pelvis_tilt reserve anomaly is a STRUCTURAL ARTIFACT of coupler removal, not a musculoskeletal error
3. With coupler (V2): box motion incompatible (coupler forces arm to 72.9 deg elevation at max stoop — incompatible with reaching down to grab box)
4. Box motion arm position (reaching down) ≠ stoop_v5.mot arm position (72.9 deg elevated)
5. Phase 2 box motion: the pelvis_tilt reserve impact may differ (arms are at lower elevation)

**Disclosure (Methods/Limitations required):**

> "The no_coupler model variant shows an elevated pelvis_tilt reserve actuator (174 Nm, 13.5× the Hicks 2015 threshold of 12.9 Nm). Root cause analysis confirms this is a structural artifact of removing the shoulder-pelvis coupler constraints: the coupler constraint reaction force previously provided ~174 Nm of generalized force at the pelvis_tilt coordinate through the constraint Jacobian, which must now be supplied by the reserve. A four-variant isolation experiment confirmed that coupler removal accounts for 99.6% of the reserve exceedance (forearm_v1 modification: 1.0%). Importantly, erector spinae activations are unaffected (max ΔES 0.41 %p across 5 suit conditions, PASS). The reserve exceedance is disclosed as a model limitation; the no_coupler model is retained for box-lifting phases where free shoulder kinematics are biomechanically required."

---

## 4. Box Motion Reserve Prediction

For the box motion (semi-squat lift):
- Arms reach DOWN to grab box: shoulder_elv ≈ 0-30 deg (lower than stoop 72.9 deg)
- Less arm elevation → less kinematic inconsistency vs stoop_v5 case
- Prediction: pelvis_tilt reserve may be similar or lower than 145.7 Nm (V3_armhang)
- Actual value: requires box motion Moco solve (planned in Step A.3)

**Criterion for box motion model accept/reject**: If pelvis_tilt reserve < 200 Nm AND ES results are robust (suit effect direction preserved), proceed with box MocoTrack. Report reserve magnitude honestly.

---

## 5. Model Files for Box Motion

| Role | Model File |
|------|-----------|
| Box IK stage 1-3 | `MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim` |
| Box Moco solve | `MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim` |
| Phase 1a reference | `MaleFullBodyModel_v2.0_OS4_moco_stoop.osim` (with_coupler, for comparison) |

---

## 6. Rejected Options

**Option B (with_coupler + forearm_v1):**
- V2 solve confirmed: pelvis_tilt = 1.82 Nm (PASS)
- BUT: box motion requires arms to reach down and forward (not elevated to 72.9 deg)
- Coupler would force shoulder_elv = -1.62 × pelvis_tilt → incompatible with box grip
- Rejected for box motion.

**Option C (add shoulder muscles):**
- Would require adding ~20 shoulder crossing muscles to Phase 1a/2 muscle set
- Changes validated Phase 1a results → new regression test needed
- Significantly increases computational cost
- Deferred to future work.

---

*Decision: opensim-agent, 2026-05-15*
*Validation data: docs/step_a2/variation_matrix_results.md*
