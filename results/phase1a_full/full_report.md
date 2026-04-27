# Phase 1a Full — MocoInverse with GRF (Report)

- IPOPT: **Optimal Solution Found** ✅
- Wall time: **140 s** (2 min 20 s)
- Objective (excitation_effort): 434.1
- Mesh intervals: 50, motion t=0–5 s, 114 muscles, GRF integrated

## Phase × muscle mean activation (%)

| Muscle | Quiet | Eccentric | Hold | Concentric | Recovery | Δ(Con-Ecc) |
|---|---|---|---|---|---|---|
| IL_R10_r | 8.1 | 53.3 | 87.7 | 82.8 | 27.6 | +29.4 |
| IL_R11_r | 0.0 | 10.1 | 23.1 | 22.1 | 3.8 | +12.0 |
| IL_R12_r | 0.0 | 2.3 | 10.7 | 10.1 | 0.3 | +7.7 |
| IL_R10_l | 8.0 | 52.5 | 85.6 | 80.9 | 27.2 | +28.4 |
| IL_R11_l | 0.0 | 9.6 | 21.3 | 20.5 | 3.6 | +10.9 |
| IL_R12_l | 0.0 | 2.2 | 10.3 | 9.7 | 0.3 | +7.4 |
| LTpL_L5_r | 8.8 | 32.5 | 48.6 | 45.9 | 17.7 | +13.4 |
| LTpL_L5_l | 8.9 | 32.8 | 49.9 | 47.0 | 17.9 | +14.2 |
| LTpT_T11_r | 0.0 | 2.7 | 7.6 | 7.1 | 0.9 | +4.4 |
| LTpT_T12_r | 0.0 | 0.9 | 4.0 | 3.6 | 0.2 | +2.7 |
| QL_post_I_2-L4_r | 0.2 | 1.3 | 2.4 | 2.3 | 0.7 | +1.0 |
| QL_post_I_3-L1_r | 0.1 | 0.7 | 2.7 | 2.5 | 0.2 | +1.8 |
| rect_abd_r | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | -0.0 |
| rect_abd_l | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | -0.0 |

## Reserve breakdown @ t=2.5 s (peak hold)

| Category | count | gen (Nm or N) |
|---|---:|---:|
| spine_FE | 19 | 19.4 |
| spine_LB | 19 | 2.6 |
| spine_AR | 19 | 5.8 |
| pelvis | 6 | 52.3 |
| hip | 6 | 31.1 |
| knee | 2 | 157.6 |
| ankle | 2 | 36.6 |
| other | 0 | 0.0 |
| **TOTAL** | 73 | **305.5** |

- pelvis_ty: **46.1 N** (smoke without GRF: 799 N → with GRF: 63 N → Full: 46.1 N)

## Comparison: Smoke (no GRF) vs Smoke+GRF vs Full

| Metric | Smoke (no GRF) | Smoke+GRF | Full+GRF |
|---|---:|---:|---:|
| Convergence | ✅ | ✅ | ✅ |
| Wall time | 65 s | 68 s | 140 s |
| Spine FE reserve sum | 20.3 Nm | 20.2 Nm | 19.4 Nm |
| pelvis_ty reserve | 799 N | 63 N | 46.1 N |
| IL_R10_r peak (overall) | (smoke peak) | — | 92.4% |
| IL_R11_r peak (overall) | (smoke peak) | — | 25.4% |
| LTpL_L5_r peak (overall) | (smoke peak) | — | 50.1% |

## S1–S6 judgment

- **S1 IPOPT converged**: ✅
- **S2 ES peak 40–100%**: ✅ (4 muscles)
- **S3 Spine FE reserve < 30 Nm @ peak**: ✅ (19.4 Nm)
- **S4 Ecc ≠ Con asymmetry**: ✅
- **S5 pelvis_ty < 30 N (GRF working)**: ❌ (46.1 N)
- **S6 Quiet < Eccentric ≤ Concentric pattern**: ✅
