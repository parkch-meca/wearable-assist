# Locked Coordinate Inventory — MaleFullBodyModel_v2.0_OS4_modified.osim

**Date**: 2026-04-24
**Source**: `/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim`
**Total locked coordinates**: 57
**Unique joints**: 29
**Purpose**: Plan for replacing locked coords with WeldJoints so Moco CasADiSolver can initialize.

---

## Classification proposal (awaiting user approval)

| Category | Count | Rationale |
|---|---:|---|
| **WELD** | **51** | Safe to weld — no meaningful role in stoop / box-lift / reach / overhead |
| **REVIEW** | **6** | User decision — could matter for future reach/grasp tasks |
| **KEEP (locked, not welded)** | **0** | No locked coord belongs to the stoop/lift DOF set |

User-specified KEEP set (lumbar FE, hip_flexion, knee_angle, ankle_dorsiflexion, shoulder, elbow) is all free already — they do not appear here.

---

## Group A — Costovertebral joints (WELD, 48 coords)

Rib attachment Y + Z rotations at each thoracic level, bilateral. All default 0, purely structural in this model — ribs do not move relative to their thoracic vertebrae during stoop/lift. Welding has zero kinematic effect but removes 48 locked variables from the optimization.

| Joint | Coord(s) | Type | Parent → Child |
|---|---|---|---|
| T1_r1R_CVjnt | T1_r1R_Y, T1_r1R_Z | CustomJoint | thoracic1 → rib1_R |
| T2_r2R_CVjnt | T2_r2R_Y, T2_r2R_Z | CustomJoint | thoracic2 → rib2_R |
| T3_r3R_CVjnt | T3_r3R_Y, T3_r3R_Z | CustomJoint | thoracic3 → rib3_R |
| T4_r4R_CVjnt | T4_r4R_Y, T4_r4R_Z | CustomJoint | thoracic4 → rib4_R |
| T5_r5R_CVjnt | T5_r5R_Y, T5_r5R_Z | CustomJoint | thoracic5 → rib5_R |
| T6_r6R_CVjnt | T6_r6R_Y, T6_r6R_Z | CustomJoint | thoracic6 → rib6_R |
| T7_r7R_CVjnt | T7_r7R_Y, T7_r7R_Z | CustomJoint | thoracic7 → rib7_R |
| T8_r8R_CVjnt | T8_r8R_Y, T8_r8R_Z | CustomJoint | thoracic8 → rib8_R |
| T9_r9R_CVjnt | T9_r9R_Y, T9_r9R_Z | CustomJoint | thoracic9 → rib9_R |
| T10_r10R_CVjnt | T10_r10R_Y, T10_r10R_Z | CustomJoint | thoracic10 → rib10_R |
| T11_r11R_CVjnt | T11_r11R_Y, T11_r11R_Z | CustomJoint | thoracic11 → rib11_R |
| T12_r12R_CVjnt | T12_r12R_Y, T12_r12R_Z | CustomJoint | thoracic12 → rib12_R |
| T1_r1L_CVjnt … T12_r12L_CVjnt | (same pattern, left side) | CustomJoint | thoracic{N} → rib{N}_L |

**Recommendation: WELD all 24 joints (48 coords)** — zero expected kinematic impact.

---

## Group B — Sternum (WELD, 1 joint / 3 coords)

Rigid positioning of the sternum relative to rib1_R. Already locked at default (0, 0, 0). No meaningful role in any lift task.

| Joint | Coords | Type | Parent → Child |
|---|---|---|---|
| r1R_sterR_jnt | SternumX, SternumY, SternumZ | CustomJoint (translational) | rib1_R → sternum |

**Recommendation: WELD**.

---

## Group C — Forearm pronation/supination (REVIEW, 2 coords)

Currently locked at `pro_sup = 0` (neutral — palms face each other / forward depending on shoulder orientation). For the current stoop + box-lift motions, arms hang passively so pro/sup is not exercised. For future **overhead / reach / carry asymmetric grasp** motions, pro_sup might matter.

| Joint | Coord | Type | Parent → Child | Current use |
|---|---|---|---|---|
| radioulnar | pro_sup_r | CustomJoint | ulna_R → radius_R | locked @ 0 |
| radioulnar_l | pro_sup_l | CustomJoint | ulna_L → radius_L | locked @ 0 |

**Recommendation: REVIEW**. Default proposal = **WELD** (current scope is bilateral symmetric box lift; pro/sup at 0 is physiologically plausible). If user plans reach/overhead work within 6 months, unlock first then weld is wrong — keep free instead.

---

## Group D — Wrist (REVIEW, 4 coords, coupled motion)

Currently locked. `coupled` motion type means the DOF is constrained by another coord (usually wrist radial/ulnar deviation is coupled to flexion). For box lift with grip closed, wrist is approximately fixed. For grasp/release / finer manipulation, wrist DOFs matter.

| Joint | Coord | Type | Parent → Child | Motion type | Note |
|---|---|---|---|---|---|
| radius_hand_r | wrist_dev_r | CustomJoint | radius_R → hand_R | coupled | locked |
| radius_hand_r | wrist_flex_r | CustomJoint | radius_R → hand_R | coupled | locked |
| radius_hand_l | wrist_dev_l | CustomJoint | radius_L → hand_L | coupled | locked |
| radius_hand_l | wrist_flex_l | CustomJoint | radius_L → hand_L | coupled | locked |

**Recommendation: REVIEW**. Default proposal = **WELD** (current box lift does not involve wrist motion; locked-at-0 kinematics preserved by weld). ⚠ Caveat: `coupled` motion type means welding must preserve the couplers between these coords. If replacing the radius_hand_r joint with WeldJoint also removes all 2 coords simultaneously (dev + flex), that's fine. If only one is welded and the other retained, the coupler breaks.

→ **If REVIEW decision is WELD**, script must replace the full `radius_hand_{r,l}` joint atomically (both dev and flex together) via WeldJoint. Same for `radioulnar{,_l}`.

---

## Summary decision matrix for user approval

| Group | Joints | Coords | Proposal |
|---|---:|---:|---|
| A — Costovertebral | 24 | 48 | **WELD all** ✅ (no kinematic effect) |
| B — Sternum | 1 | 3 | **WELD** ✅ (structural) |
| C — pro_sup (forearm) | 2 | 2 | REVIEW — default WELD |
| D — Wrist | 2 | 4 | REVIEW — default WELD (atomic joint replace) |

**Total if all approved: WELD 29 joints / 57 coords** → all locked coords eliminated. Model becomes Moco-ready.

**Conservative alternative**: WELD only Groups A + B (25 joints / 51 coords) and leave groups C+D locked → but then Moco CasADiSolver still fails because it can't handle the remaining 6 locked coords. **Not viable** unless OpenSim allows disabling specific locks programmatically (unlikely for these coupled/locked-by-design coords).

→ Realistic path: **approve WELD for all 29 joints**. Future reach/overhead work would require unlocking/replacing these joints anyway, regardless of whether we weld now.

---

## Raw inventory data

57 records exported at `/tmp/locked_inventory.json`. Probe script: `/tmp/locked_inventory.py`.
