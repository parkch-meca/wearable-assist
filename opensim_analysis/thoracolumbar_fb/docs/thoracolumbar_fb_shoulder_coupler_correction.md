# ThoracolumbarFB shoulder rhythm coupler — L/R asymmetry correction

**Date discovered**: 2026-04-28 during box motion v3 design (Stage 1).
**Affected model**: `MaleFullBodyModel_v2.0_OS4_modified.osim` (and the welded
variant `MaleFullBodyModel_v2.0_OS4_moco_stoop.osim`).
**Affected pose**: deep forward bend (pelvis_tilt ≈ −55°, hip_flexion ≈ 95°).
**Recommended fix**: post-assembly correction `elv_angle_l += α × 7.15°`.

---

## Problem

When constructing a stoop / bend pose by setting only spine and lower-extremity
target angles symmetrically and letting `model.assemble(state)` resolve coupler
constraints, the resulting hand positions are **L/R asymmetric** in the
sagittal-vertical (y) coordinate. At α = 1 (peak bend) on the v3 design, the
two-handed reach was off by ~2.6 cm:

| Side | hand y (m) |
|---|---:|
| hand_R | −0.7549 |
| hand_L | −0.7813 |
| **Difference** | **−0.0264 m (2.6 cm)** |

Lateral (z) and forward (x) coordinates were already mirror-symmetric.

## Diagnosis

The model's auto-assembled arm coords are mirror-symmetric on paper:

| Coord | R value | L value | Convention |
|---|---:|---:|---|
| shoulder_elv | +89.10° | −89.10° | mirror (sign flip) ✓ |
| elv_angle | +110.00° | +110.00° | same value — **convention issue** |
| shoulder_rot | 0.00° | 0.00° | neutral |
| elbow_flexion | 0.00° | 0.00° | neutral |

Coordinate ranges in the model:
- `shoulder_elv_r ∈ [0, +154.7]`, `shoulder_elv_l ∈ [−154.7, 0]` ← mirror by sign
- `elv_angle_r ∈ [−90, +155]`, `elv_angle_l ∈ [−90, +155]` ← same range, no built-in mirror

The `elv_angle` coordinate represents the elevation plane in each side's local
frame, not a model-global angle. With an asymmetric body pose (deep trunk bend),
the shoulder rhythm coupler drives `elv_angle_l = elv_angle_r` instead of an
appropriately mirrored value, causing the left arm's elevation plane to differ
from the right's. The result is hand_L y ~2.6 cm below hand_R y.

## Sensitivity test (at peak bend, α = 1)

| L-side coord | Δ for 0 cm hand-y diff | Sensitivity |
|---|---|---:|
| `elv_angle_l` | **+7.15°** | ~0.4 cm / deg |
| `shoulder_rot_l` | (no zero crossing within ±30°) | ±-shape, low effect |
| `elbow_flexion_l` | +7.0° | ~0.2 cm / deg |
| `hip_flexion_l` | (no effect — controls foot, not arm) | 0 |

`elv_angle_l += 7.15°` is the cleanest single-coord correction.

## Fix

In motion-generation scripts that target a deep-bend pose:

```python
# After model.assemble(state):
if alpha > 1e-9 and 'elv_angle_l' in names_idx:
    c_elv_l = cs.get(names_idx['elv_angle_l'])
    v = c_elv_l.getValue(state) + alpha * np.radians(7.15)
    c_elv_l.setValue(state, v, False)
model.realizePosition(state)   # do NOT re-assemble — would undo the fix
```

The correction scales with `alpha` (the bend amplitude) so that at standing
(`alpha = 0`) the arms remain at default, and at peak bend (`alpha = 1`) the
full 7.15° offset is applied.

After fix:

| Side | hand y (m) |
|---|---:|
| hand_R | −0.7549 |
| hand_L | −0.7554 |
| **Difference** | **−0.0005 m (0.5 mm)** |

## Reuse policy

The +7.15° offset value was tuned empirically for the box v3 deep-bend
configuration. For other deep-bend poses with different spine/leg targets, the
correction value may differ. Recommended workflow when designing a new pose:

1. Set spine + leg targets, run `model.assemble(state)`.
2. Read hand_R y and hand_L y. If `|hand_R y − hand_L y| < 1 cm`, no correction
   needed.
3. Otherwise, run a brief sensitivity sweep on `elv_angle_l` (steps of 1° in the
   range ±15°) and locate the zero crossing of `(hand_L y − hand_R y)`.
4. Apply that offset scaled by the alpha schedule of the motion.

Reusable script: `scripts/calibrate_shoulder_coupler.py` (TODO if used in
future phases).

## Why not regenerate the model?

The shoulder rhythm coupler is a published feature of the ThoracolumbarFB
model and modifying it would invalidate prior validation. The post-assembly
correction is conservative (only adjusts `elv_angle_l`, leaves all other
coords intact) and can be removed if a future ThoracolumbarFB release
provides symmetric coupler resolution.

## Validation

Verified at three time points along v3 motion (Stage 1):

| t (s) | α | hand_R y | hand_L y | diff |
|---|---:|---:|---:|---:|
| 0.5 | 0.00 | −0.042 | −0.042 | 0 (no correction) |
| 1.0 | 0.20 | −0.084 | −0.084 | 0.0 (within noise) |
| 2.0 | 1.00 | −0.7549 | −0.7554 | 0.0005 m |

Symmetry preserved across the alpha range.
