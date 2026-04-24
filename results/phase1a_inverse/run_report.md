# Phase 1a smoke v2 (MocoInverse) — Report

- IPOPT: **Optimal Solution Found** ✅
- Solve wall time: **65.3 s**
- Objective (excitation_effort): 11752.3
- Mesh intervals: 25, reserve optF = 10 Nm (rotational)
- Model: 114 muscles (Phase 1a subset, DeGrooteFregly2016 + rigid tendon)

## Muscle activations (key)

| Muscle | peak % | t_peak (s) | @ t=2.33 (%) | ecc mean (%) | con mean (%) | Δ (con−ecc) %p |
|---|---:|---:|---:|---:|---:|---:|
| IL_R10_r | 92.0 | 2.440 | 90.4 | 54.9 | 84.6 | +29.7 |
| IL_R11_r | 27.5 | 3.000 | 24.3 | 10.7 | 23.1 | +12.4 |
| IL_R12_r | 13.5 | 3.000 | 12.0 | 2.8 | 11.3 | +8.6 |
| IL_R10_l | 89.7 | 2.440 | 88.1 | 54.0 | 82.5 | +28.5 |
| IL_R11_l | 26.2 | 3.000 | 22.4 | 10.2 | 21.3 | +11.2 |
| IL_R12_l | 12.9 | 3.000 | 11.6 | 2.7 | 10.9 | +8.3 |
| LTpT_T11_r | 8.6 | 3.000 | 8.1 | 2.8 | 7.7 | +4.9 |
| LTpT_T12_r | 4.6 | 2.480 | 4.3 | 0.9 | 4.0 | +3.2 |
| LTpT_R11_r | 8.6 | 3.000 | 4.6 | 2.9 | 4.5 | +1.6 |
| LTpT_R12_r | 0.7 | 3.000 | 0.1 | 0.2 | 0.2 | +0.0 |
| LTpL_L5_r | 50.1 | 2.440 | 49.4 | 33.1 | 46.7 | +13.6 |
| LTpL_L4_r | 8.1 | 1.960 | 7.6 | 5.5 | 7.3 | +1.8 |
| LTpL_L5_l | 51.5 | 2.440 | 50.8 | 33.5 | 48.0 | +14.5 |
| QL_post_I_2-L4_r | 2.5 | 2.480 | 2.4 | 1.0 | 2.3 | +1.2 |
| QL_post_I_2-L3_r | 0.9 | 3.000 | 0.6 | 0.4 | 0.6 | +0.3 |
| QL_post_I_3-L1_r | 3.1 | 2.480 | 2.9 | 0.5 | 2.7 | +2.2 |
| rect_abd_r | 0.0 | 1.000 | 0.0 | 0.0 | 0.0 | -0.0 |
| rect_abd_l | 0.0 | 1.000 | 0.0 | 0.0 | 0.0 | -0.0 |

## Reserve usage @ t=2.33 s

| Category | count | generated Nm |
|---|---:|---:|
| spine_FE | 19 | 20.3 |
| spine_LB | 19 | 2.5 |
| spine_AR | 19 | 5.7 |
| pelvis | 6 | 812.7 |
| hip | 6 | 35.4 |
| knee | 2 | 7.1 |
| ankle | 2 | 1.3 |
| other | 0 | 0.0 |
| **TOTAL** | 73 | **885.0** |

### Top 10 individual reserves (by |gen Nm| at t=2.33)

| Reserve path | ctrl | optF Nm | gen Nm |
|---|---:|---:|---:|
| `jointset_ground_pelvis_pelvis_ty` | +79.897 | 10 | +799.0 |
| `jointset_hip_r_hip_flexion_r` | +1.760 | 10 | +17.6 |
| `jointset_hip_l_hip_flexion_l` | +1.760 | 10 | +17.6 |
| `jointset_ground_pelvis_pelvis_tx` | -1.255 | 10 | +12.5 |
| `jointset_T1_head_neck_T1_head_neck_FE` | +0.695 | 10 | +7.0 |
| `jointset_T10_T11_IVDjnt_T10_T11_FE` | +0.571 | 10 | +5.7 |
| `jointset_knee_r_knee_angle_r` | -0.355 | 10 | +3.5 |
| `jointset_knee_l_knee_angle_l` | -0.355 | 10 | +3.5 |
| `jointset_L5_S1_IVDjnt_L5_S1_FE` | +0.218 | 10 | +2.2 |
| `jointset_L4_L5_IVDjnt_L4_L5_FE` | -0.191 | 10 | +1.9 |

### Reference (SO studies at t=2.33)
- SO R100 (baseline): 413 Nm spine FE
- SO R50:  209 Nm spine FE
- SO R10:   22 Nm spine FE

## S1–S5 smoke-test judgment

- **S1 IPOPT converged**: ✅
- **S2 ES peak 40–100 % (≥1 muscle)**: ✅  (4 muscles in band)
- **S3 Spine FE reserve < 50 Nm @ t=2.33**: ✅  (20.3 Nm)
- **S4 Ecc ≠ Con asymmetry observed**: ✅
- **S5 IL_R10/R11_r peak 40–100 %**: IL_R10_r=92.0%  IL_R11_r=27.5%
