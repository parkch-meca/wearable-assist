# Variation Matrix Results: pelvis_tilt Reserve Root Cause

**Date**: 2026-05-15
**Analysis**: opensim-agent (Step A.2 Phase 2)
**Motion**: stoop_synthetic_v5.mot, t=[1.0,3.0]s, mesh=25 (smoke)
**Reserve optimalForce**: 10.0 Nm (all joints)

---

## 1. Variation Matrix

| Variant | Coupler | Forearm v1 | pelvis_tilt (Nm) | pelvis_ty (N) | SpineFE (Nm) | IL_R10_r |
|---------|---------|------------|-----------------|--------------|-------------|----------|
| **V1 original** | yes | no | **0.13** (PASS) | 64.65 (FAIL) | 19.40 | 92.4% |
| **V2 forearm_only** | yes | yes | **1.82** (PASS) | 65.89 (FAIL) | 21.09 | 93.1% |
| **V3 no_coupler** | no | no | **174.08** (FAIL) | 65.83 (FAIL) | 20.93 | 92.0% |
| **V4 current** | no | yes | **174.79** (FAIL) | 65.88 (FAIL) | 21.04 | 93.2% |
| V3_armhang | no | no | **145.73** (FAIL) | 62.30 (FAIL) | 17.54 | 48.8% |

Hicks 2015 thresholds: pelvis_tilt < 12.9 Nm, pelvis_ty < 36.8 N.

---

## 2. Root Cause Decomposition

| Effect | Delta pelvis_tilt | Fraction |
|--------|------------------|---------|
| D_forearm = V2 - V1 | +1.69 Nm | 1.0% |
| D_nocoupler = V3 - V1 | +173.95 Nm | **99.6%** |
| D_interaction = V4 - V3 - V2 + V1 | -0.98 Nm | -0.6% |
| **Total (V4 - V1)** | **+174.66 Nm** | 100% |

**Primary cause: no_coupler removal (99.6%)**
**forearm_v1 contribution: negligible (1.0%)**

---

## 3. Mechanism

The shoulder-pelvis coupler constraints (4 couplers) provide ~174 Nm of generalized force at the pelvis_tilt coordinate through the constraint Jacobian (J^T × lambda). This force represents the mechanical coupling of arm inertia/gravity to pelvis rotation.

**stoop_v5.mot shoulder kinematics**: The motion file was generated with couplers active. At peak stoop (pelvis_tilt = -45 deg), shoulder_elv_r = 72.9 deg (exactly -1.62 × (-45°)). When prescribed to the no_coupler model, this elevated arm position contributes additional reserve.

**V3_armhang test (shoulder_elv=0)**: Even with arms hanging (0 deg), the no_coupler model requires 145.7 Nm pelvis_tilt reserve. This confirms that the root cause is structural (coupler removal changes mechanical topology) rather than purely kinematic (arm trajectory prescription).

---

## 4. Solve Statistics

| Variant | Model | t range | Status | Wall time |
|---------|-------|---------|--------|-----------|
| V1 | moco_stoop (with_coupler) | 0.0-5.0 (full) | Succeeded | 140 s (ref) |
| V2 | moco_stoop_forearm_v1 (NEW) | 1.0-3.0 (smoke) | Succeeded | 68 s |
| V3 | moco_stoop_no_coupler | 1.0-3.0 (smoke) | Succeeded | ~60 s (ref) |
| V4 | moco_stoop_no_coupler_forearm_v1 | 1.0-3.0 (smoke) | Succeeded | 50 s (ref) |
| V3_armhang | moco_stoop_no_coupler + arm-hang motion | 1.0-3.0 (smoke) | Succeeded | 53 s |

---

## 5. ES Muscle Analysis

| Variant | IL_R10_r peak | Change vs V1 |
|---------|-------------|-------------|
| V1 | 92.4% | — (baseline) |
| V2 | 93.1% | +0.7 %p |
| V3 | 92.0% | -0.4 %p |
| V4 | 93.2% | +0.8 %p |

ES muscle activations are effectively unchanged across all variants (max ΔES < 1 %p). This confirms the previous regression test finding (max ΔES 0.41 %p for REPRO_V2 5-condition sweep). The pelvis_tilt reserve anomaly does NOT affect ES analysis validity.

---

## 6. Files

| File | Path |
|------|------|
| V1 solution | `/data/wearable-assist/results/phase1a_full/solution.sto` |
| V2 model | `/data/opensim_models/.../MaleFullBodyModel_v2.0_OS4_moco_stoop_forearm_v1.osim` |
| V2 solution | `/data/opensim_results/variation_matrix_phase1a/V2/solution.sto` |
| V3 solution | `/data/wearable-assist/results/phase1a_smoke_no_coupler/solution.sto` |
| V4 solution | `/data/wearable-assist/results/phase1a_smoke_forearm_v1/solution.sto` |
| V3_armhang motion | `/data/opensim_results/variation_matrix_phase1a/V3_armhang/stoop_v5_armhang.mot` |
| V3_armhang solution | `/data/opensim_results/variation_matrix_phase1a/V3_armhang/solution.sto` |

---

*Analysis: opensim-agent, Step A.2 Phase 2*
