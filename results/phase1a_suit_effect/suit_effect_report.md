# Phase 1a Suit Effect — Report

- Baseline solution: `results/phase1a_full/solution.sto`
- Suit (+24 N·m) solution: `results/phase1a_suit_effect/solution_suit.sto`
- Suit profile: cosine ramp 0.5–2.5 s up, hold 2.5–3.0 s, ramp 3.0–5.0 s down (matches v5 SO suit_sweep)
- Both runs converged (Optimal Solution Found)

## Phase × muscle ΔES (suit − baseline)

| Muscle | Phase | Baseline (%) | Suit (%) | Δ (%p) | Δ (%) |
|---|---|---:|---:|---:|---:|
| IL_R10_r | Quiet | 8.1 | 7.7 | -0.3 | -4.1 |
| IL_R10_r | Eccentric | 53.3 | 36.8 | -16.6 | -31.1 |
| IL_R10_r | Hold | 87.7 | 54.0 | -33.8 | -38.5 |
| IL_R10_r | Concentric | 82.8 | 50.3 | -32.4 | -39.2 |
| IL_R10_r | Recovery | 27.6 | 20.9 | -6.6 | -24.1 |
| IL_R10_l | Quiet | 8.0 | 7.7 | -0.3 | -4.1 |
| IL_R10_l | Eccentric | 52.5 | 35.9 | -16.6 | -31.6 |
| IL_R10_l | Hold | 85.6 | 51.8 | -33.8 | -39.5 |
| IL_R10_l | Concentric | 80.9 | 48.5 | -32.4 | -40.1 |
| IL_R10_l | Recovery | 27.2 | 20.6 | -6.6 | -24.4 |
| IL_R11_r | Quiet | 0.0 | 0.0 | -0.0 | +0.0 |
| IL_R11_r | Eccentric | 10.1 | 8.6 | -1.6 | -15.5 |
| IL_R11_r | Hold | 23.1 | 19.0 | -4.1 | -17.9 |
| IL_R11_r | Concentric | 22.1 | 18.0 | -4.1 | -18.7 |
| IL_R11_r | Recovery | 3.8 | 3.2 | -0.5 | -14.2 |
| IL_R12_r | Quiet | 0.0 | 0.0 | -0.0 | +0.0 |
| IL_R12_r | Eccentric | 2.3 | 3.2 | +0.8 | +35.8 |
| IL_R12_r | Hold | 10.7 | 12.7 | +2.0 | +18.7 |
| IL_R12_r | Concentric | 10.1 | 12.0 | +2.0 | +19.4 |
| IL_R12_r | Recovery | 0.3 | 0.5 | +0.2 | +0.0 |
| IL_R11_l | Quiet | 0.0 | 0.0 | -0.0 | +0.0 |
| IL_R11_l | Eccentric | 9.6 | 8.0 | -1.6 | -16.4 |
| IL_R11_l | Hold | 21.3 | 17.1 | -4.2 | -19.6 |
| IL_R11_l | Concentric | 20.5 | 16.4 | -4.2 | -20.2 |
| IL_R11_l | Recovery | 3.6 | 3.1 | -0.5 | -14.8 |
| IL_R12_l | Quiet | 0.0 | 0.0 | -0.0 | +0.0 |
| IL_R12_l | Eccentric | 2.2 | 3.1 | +0.8 | +35.7 |
| IL_R12_l | Hold | 10.3 | 12.1 | +1.8 | +17.4 |
| IL_R12_l | Concentric | 9.7 | 11.5 | +1.8 | +18.3 |
| IL_R12_l | Recovery | 0.3 | 0.5 | +0.2 | +0.0 |
| LTpL_L5_r | Quiet | 8.8 | 8.6 | -0.2 | -2.4 |
| LTpL_L5_r | Eccentric | 32.5 | 28.9 | -3.6 | -10.9 |
| LTpL_L5_r | Hold | 48.6 | 42.4 | -6.2 | -12.8 |
| LTpL_L5_r | Concentric | 45.9 | 39.9 | -6.0 | -13.0 |
| LTpL_L5_r | Recovery | 17.7 | 16.3 | -1.5 | -8.3 |
| LTpL_L5_l | Quiet | 8.9 | 8.7 | -0.2 | -2.4 |
| LTpL_L5_l | Eccentric | 32.8 | 29.3 | -3.6 | -10.9 |
| LTpL_L5_l | Hold | 49.9 | 43.6 | -6.3 | -12.6 |
| LTpL_L5_l | Concentric | 47.0 | 41.0 | -6.0 | -12.8 |
| LTpL_L5_l | Recovery | 17.9 | 16.4 | -1.5 | -8.2 |
| LTpL_L4_r | Quiet | 0.0 | 0.0 | -0.0 | +0.0 |
| LTpL_L4_r | Eccentric | 5.2 | 5.2 | -0.0 | -0.6 |
| LTpL_L4_r | Hold | 7.7 | 6.8 | -0.9 | -12.1 |
| LTpL_L4_r | Concentric | 7.6 | 6.7 | -0.9 | -11.9 |
| LTpL_L4_r | Recovery | 2.9 | 2.9 | -0.0 | -0.8 |
| LTpT_T11_r | Quiet | 0.0 | 0.0 | -0.0 | +0.0 |
| LTpT_T11_r | Eccentric | 2.7 | 2.5 | -0.2 | -8.3 |
| LTpT_T11_r | Hold | 7.6 | 7.1 | -0.5 | -6.9 |
| LTpT_T11_r | Concentric | 7.1 | 6.6 | -0.6 | -7.8 |
| LTpT_T11_r | Recovery | 0.9 | 0.8 | -0.1 | +0.0 |
| LTpT_T12_r | Quiet | 0.0 | 0.0 | -0.0 | +0.0 |
| LTpT_T12_r | Eccentric | 0.9 | 1.0 | +0.1 | +0.0 |
| LTpT_T12_r | Hold | 4.0 | 4.6 | +0.7 | +16.8 |
| LTpT_T12_r | Concentric | 3.6 | 4.2 | +0.6 | +16.3 |
| LTpT_T12_r | Recovery | 0.2 | 0.2 | -0.0 | +0.0 |
| QL_post_I_2-L4_r | Quiet | 0.2 | 0.1 | -0.2 | +0.0 |
| QL_post_I_2-L4_r | Eccentric | 1.3 | 0.9 | -0.4 | -28.7 |
| QL_post_I_2-L4_r | Hold | 2.4 | 2.1 | -0.4 | -14.6 |
| QL_post_I_2-L4_r | Concentric | 2.3 | 1.9 | -0.4 | -15.8 |
| QL_post_I_2-L4_r | Recovery | 0.7 | 0.4 | -0.3 | +0.0 |
| QL_post_I_3-L1_r | Quiet | 0.1 | 0.0 | -0.0 | +0.0 |
| QL_post_I_3-L1_r | Eccentric | 0.7 | 0.6 | -0.1 | +0.0 |
| QL_post_I_3-L1_r | Hold | 2.7 | 3.1 | +0.3 | +11.8 |
| QL_post_I_3-L1_r | Concentric | 2.5 | 2.7 | +0.2 | +10.1 |
| QL_post_I_3-L1_r | Recovery | 0.2 | 0.1 | -0.1 | +0.0 |
| rect_abd_r | Quiet | 0.0 | 0.0 | -0.0 | +0.0 |
| rect_abd_r | Eccentric | 0.0 | 0.0 | -0.0 | +0.0 |
| rect_abd_r | Hold | 0.0 | 0.0 | -0.0 | +0.0 |
| rect_abd_r | Concentric | 0.0 | 0.0 | -0.0 | +0.0 |
| rect_abd_r | Recovery | 0.0 | 0.0 | -0.0 | +0.0 |

## ES summary (mean of 6 dominant ES muscles)

| Phase | Baseline (%) | Suit (%) | Δ (%p) | Δ (%) |
|---|---:|---:|---:|---:|
| Quiet | 5.6 | 5.5 | -0.2 | -3.2 |
| Eccentric | 31.8 | 24.6 | -7.2 | -22.8 |
| Hold | 52.7 | 38.0 | -14.7 | -28.0 |
| Concentric | 49.9 | 35.7 | -14.2 | -28.5 |
| Recovery | 16.3 | 13.4 | -2.9 | -17.7 |

## SO §1.6 comparison

| Metric | SO R100 | SO R50 (re-est.) | Moco IL_R10 Hold | Moco IL_R10 Conc |
|---|---:|---:|---:|---:|
| Reduction at 24 N·m | 28.97 % | 21.25 % | +38.5 % | +39.2 % |
