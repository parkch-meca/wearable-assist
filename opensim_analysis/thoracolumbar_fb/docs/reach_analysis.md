# Reach analysis — 4 postures × coupler ON/OFF (Step 1.2)

Model: `/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim`

Arm length (humerus + forearm + wrist): **549.0 mm**

## Postures

| ID | pelvis_tilt | hip_flex | knee | lumbar/level | thoracic/level | ankle |
|---|---:|---:|---:|---:|---:|---:|
| `P1_shallow_v5` | -35° | +60° | -30° | -7° | — | +5° |
| `P2_stoop_squat_v3` | -50° | +95° | -55° | -8° | — | +8° |
| `P3_deep_lumbar_dom` | -40° | +110° | -45° | -10° | — | +10° |
| `P4_deep_lumbar_thoracic` | -45° | +110° | -45° | -10° | -3° | +10° |

## With coupler (current model)

Shoulder elevation is forced to `-1.62 × pelvis_tilt`. When pelvis_tilt is negative (stoop), shoulder is FORCED to elevate forward — arm cannot hang straight.

| Posture | pelvis_ty | shoulder (x,y) | sh_elv (couple-imposed) | elv_angle (couple-imposed) | hand y at "hang" | hand_y geometric max reach |
|---|---:|---:|---:|---:|---:|---:|
| `P1_shallow_v5` | -0.031 | (+0.412, +0.195) | +56.7° | +70.0° | -0.331 | -0.354 |
| `P2_stoop_squat_v3` | -0.118 | (+0.455, -0.037) | +81.0° | +100.0° | -0.563 | -0.586 |
| `P3_deep_lumbar_dom` | -0.294 | (+0.433, -0.199) | +64.8° | +80.0° | -0.735 | -0.748 |
| `P4_deep_lumbar_thoracic` | -0.244 | (+0.404, -0.209) | +72.9° | +90.0° | -0.603 | -0.758 |

## Without coupler (constraint removed)

Shoulder coordinates free to be set by user/IK.

| Posture | pelvis_ty | shoulder (x,y) | sh_elv (free at 0) | hand y at "hang" | hand_y geometric max reach |
|---|---:|---:|---:|---:|---:|
| `P1_shallow_v5` | -0.031 | (+0.412, +0.195) | +0.0° | +0.049 | -0.354 |
| `P2_stoop_squat_v3` | -0.118 | (+0.455, -0.037) | +0.0° | +0.014 | -0.586 |
| `P3_deep_lumbar_dom` | -0.294 | (+0.433, -0.199) | +0.0° | -0.128 | -0.748 |
| `P4_deep_lumbar_thoracic` | -0.244 | (+0.404, -0.209) | +0.0° | +0.179 | -0.758 |

## Box reachability

Reach criterion: box mid y ≥ shoulder_y - arm_length (geometric max). Coupler-imposed shoulder elevation does NOT change this max — it just prevents reaching it.

### With coupler — actual hand reach blocked by sh_elv forcing

| Posture | shoulder_y | hand reach (coupler-blocked) | ground (mid y=-0.74) | low pallet (mid y=-0.60) | low workbench (mid y=-0.30) | std workbench (mid y=0.00) |
|---|---:|---:|---|---|---|---|
| `P1_shallow_v5` | +0.195 | -0.331 | ❌ (-409 mm) | ❌ (-269 mm) | ✅ (+31 mm) | ✅ (+331 mm) |
| `P2_stoop_squat_v3` | -0.037 | -0.563 | ❌ (-177 mm) | ❌ (-37 mm) | ✅ (+263 mm) | ✅ (+563 mm) |
| `P3_deep_lumbar_dom` | -0.199 | -0.735 | ❌ (-5 mm) | ✅ (+135 mm) | ✅ (+435 mm) | ✅ (+735 mm) |
| `P4_deep_lumbar_thoracic` | -0.209 | -0.603 | ❌ (-137 mm) | ✅ (+3 mm) | ✅ (+303 mm) | ✅ (+603 mm) |

### Without coupler — geometric max reach (arm hanging straight down)

| Posture | shoulder_y | max reach | ground (mid y=-0.74) | low pallet (mid y=-0.60) | low workbench (mid y=-0.30) | std workbench (mid y=0.00) |
|---|---:|---:|---|---|---|---|
| `P1_shallow_v5` | +0.195 | -0.354 | ❌ (-386 mm) | ❌ (-246 mm) | ✅ (+54 mm) | ✅ (+354 mm) |
| `P2_stoop_squat_v3` | -0.037 | -0.586 | ❌ (-154 mm) | ❌ (-14 mm) | ✅ (+286 mm) | ✅ (+586 mm) |
| `P3_deep_lumbar_dom` | -0.199 | -0.748 | ✅ (+8 mm) | ✅ (+148 mm) | ✅ (+448 mm) | ✅ (+748 mm) |
| `P4_deep_lumbar_thoracic` | -0.209 | -0.758 | ✅ (+18 mm) | ✅ (+158 mm) | ✅ (+458 mm) | ✅ (+758 mm) |

## Diagnosis summary

| Posture | with-coupler hand_y | no-coupler hand_y_max | Δ (mm) lower with coupler removed |
|---|---:|---:|---:|
| `P1_shallow_v5` | -0.331 | -0.354 | **+23 mm** |
| `P2_stoop_squat_v3` | -0.563 | -0.586 | **+24 mm** |
| `P3_deep_lumbar_dom` | -0.735 | -0.748 | **+13 mm** |
| `P4_deep_lumbar_thoracic` | -0.603 | -0.758 | **+155 mm** |

