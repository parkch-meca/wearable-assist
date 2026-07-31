# ThoracolumbarFB v2.0 — Joint ROM analysis (Step 1.1)

Model: `/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim`

Purpose: identify which coords have ROM tighter than typical adult literature, flagging candidates for ROM extension before re-attempting ground-box motion design.

Convention: rotational coords in degrees; ankle plantarflex/dorsiflex sign per OpenSim model.

Flexion-side limit: for FE coords (negative = flex in FB), `range_min` is the flex-side bound. For `*_flexion_*` coords (positive = flex), `range_max` is the flex-side bound.

## Full ROM table

| coord | unit | model min | model max | range | default | locked | clamped | lit min | lit max |
|---|---|---:|---:|---:|---:|---|---|---:|---:|
| `L5_S1_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -15 | 5 |
| `L4_L5_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -12 | 5 |
| `L3_L4_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -10 | 5 |
| `L2_L3_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -10 | 5 |
| `L1_L2_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -10 | 5 |
| `T12_L1_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -8 | 3 |
| `T11_T12_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -5 | 3 |
| `T10_T11_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -5 | 3 |
| `T9_T10_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -4 | 3 |
| `T8_T9_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -4 | 3 |
| `T7_T8_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -4 | 3 |
| `T6_T7_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -4 | 3 |
| `T5_T6_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -4 | 3 |
| `T4_T5_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -3 | 2 |
| `T3_T4_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -3 | 2 |
| `T2_T3_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -3 | 2 |
| `T1_T2_FE` | deg | -89.95 | +89.95 | 179.91 | +0.000 | N | N | -3 | 2 |
| `hip_flexion_r` | deg | -120.00 | +120.00 | 240.00 | +0.000 | N | N | -30 | 130 |
| `hip_flexion_l` | deg | -120.00 | +120.00 | 240.00 | +0.000 | N | N | -30 | 130 |
| `hip_adduction_r` | deg | -120.00 | +120.00 | 240.00 | +0.000 | N | N | — | — |
| `hip_adduction_l` | deg | -120.00 | +120.00 | 240.00 | +0.000 | N | N | — | — |
| `hip_rotation_r` | deg | -120.00 | +120.00 | 240.00 | +0.000 | N | N | — | — |
| `hip_rotation_l` | deg | -120.00 | +120.00 | 240.00 | +0.000 | N | N | — | — |
| `knee_angle_r` | deg | -120.00 | +10.00 | 130.00 | +0.000 | N | N | -140 | 5 |
| `knee_angle_l` | deg | -120.00 | +10.00 | 130.00 | +0.000 | N | N | -140 | 5 |
| `ankle_angle_r` | deg | -90.00 | +90.00 | 180.00 | +0.000 | N | N | -50 | 30 |
| `ankle_angle_l` | deg | -60.00 | +60.00 | 120.00 | +0.000 | N | N | -50 | 30 |
| `pelvis_tilt` | deg | -90.00 | +90.00 | 180.00 | +0.000 | N | N | -30 | 90 |
| `pelvis_list` | deg | -90.00 | +90.00 | 180.00 | +0.000 | N | N | — | — |
| `pelvis_rotation` | deg | -180.00 | +180.00 | 360.00 | +0.000 | N | N | — | — |
| `pelvis_tx` | m | -5.00 | +5.00 | 10.00 | +0.000 | N | N | — | — |
| `pelvis_ty` | m | -1.00 | +2.00 | 3.00 | +0.000 | N | N | — | — |
| `pelvis_tz` | m | -3.00 | +3.00 | 6.00 | +0.000 | N | N | — | — |
| `shoulder_elv_r` | deg | +0.00 | +154.70 | 154.70 | +0.000 | N | Y | 0 | 180 |
| `shoulder_elv_l` | deg | -154.70 | +0.00 | 154.70 | +0.000 | N | Y | -180 | 0 |
| `elv_angle_r` | deg | -90.00 | +155.16 | 245.16 | +0.000 | N | Y | -90 | 130 |
| `elv_angle_l` | deg | -90.00 | +155.16 | 245.16 | +0.000 | N | Y | -130 | 90 |
| `shoulder_rot_r` | deg | -90.44 | +44.69 | 135.13 | +0.000 | N | Y | -90 | 90 |
| `shoulder_rot_l` | deg | -45.00 | +90.84 | 135.84 | +0.000 | N | Y | -90 | 90 |
| `elbow_flexion_r` | deg | +0.00 | +155.27 | 155.27 | +0.000 | N | Y | 0 | 145 |
| `elbow_flexion_l` | deg | +0.00 | +155.27 | 155.27 | +0.000 | N | Y | 0 | 145 |
| `pro_sup_r` | deg | -90.00 | +90.00 | 180.00 | +0.000 | Y | Y | — | — |
| `pro_sup_l` | deg | -90.00 | +90.00 | 180.00 | +0.000 | Y | Y | — | — |

## Flagged ROM bottlenecks (model tighter than literature)

| coord | side | model | literature | gap |
|---|---|---:|---:|---:|
| `hip_flexion_r` | flex limit | +120.00 | +130.00 | +10.00 |
| `hip_flexion_l` | flex limit | +120.00 | +130.00 | +10.00 |
| `shoulder_elv_r` | elv max | +154.70 | +180.00 | +25.30 |

## Summary by region

**Lumbar FE (L5/S1 → T12/L1)**: L5_S1_FE -90.0°, L4_L5_FE -90.0°, L3_L4_FE -90.0°, L2_L3_FE -90.0°, L1_L2_FE -90.0°, T12_L1_FE -90.0° — **total flex capacity: 539.7°**

**Thoracic FE (T11/T12 → T1/T2)**: T11_T12_FE -90.0°, T10_T11_FE -90.0°, T9_T10_FE -90.0°, T8_T9_FE -90.0°, T7_T8_FE -90.0°, T6_T7_FE -90.0°, T5_T6_FE -90.0°, T4_T5_FE -90.0°, T3_T4_FE -90.0°, T2_T3_FE -90.0°, T1_T2_FE -90.0° — **total flex capacity: 989.5°**

**Hip flexion R/L**: hip_flexion_r +120.0°, hip_flexion_l +120.0°

**Knee R/L**: knee_angle_r [-120.0,+10.0]°, knee_angle_l [-120.0,+10.0]°

**Ankle R/L**: ankle_angle_r [-90.0,+90.0]°, ankle_angle_l [-60.0,+60.0]°

**Shoulder elv R/L**: shoulder_elv_r [+0.0,+154.7]°, shoulder_elv_l [-154.7,+0.0]°

**Elbow R/L**: elbow_flexion_r +155.3°, elbow_flexion_l +155.3°

**Pelvis tilt**: pelvis_tilt [-90.0,+90.0]°

