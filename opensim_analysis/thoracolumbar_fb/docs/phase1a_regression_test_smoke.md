# Phase 1a regression test — smoke (PASS)

Date: 2026-04-28

Baseline:  `/data/wearable-assist/results/phase1a_smoke_grf/solution.sto` (with coupler, original Phase 1a result)
Modified:  `/data/wearable-assist/results/phase1a_smoke_no_coupler/solution.sto` (4 couplers removed)

**Verdict: PASS** (max |Δ| = 1.16 %p; big changes >5 %p: 0; medium 2-5 %p: 0)

PASS criteria: all ES peaks within ±5 %p of baseline.

## ES activation peaks per phase

| muscle | phase | baseline (%) | modified (%) | Δ (%p) | rel (%) |
|---|---|---:|---:|---:|---:|
| `IL_R10_r` | Pre-bend (0.5-1.0) | 27.43 | 28.59 | +1.16 | +4.2 |
| `IL_R10_r` | Concentric (1.0-2.0) | 79.58 | 79.75 | +0.18 | +0.2 |
| `IL_R10_r` | Hold (2.0-2.4) | 90.94 | 91.02 | +0.09 | +0.1 |
| `IL_R10_r` | Eccentric (2.5-4.0) | 83.63 | 83.71 | +0.08 | +0.1 |
| `IL_R10_l` | Pre-bend (0.5-1.0) | 27.19 | 28.35 | +1.16 | +4.3 |
| `IL_R10_l` | Concentric (1.0-2.0) | 77.80 | 77.99 | +0.19 | +0.2 |
| `IL_R10_l` | Hold (2.0-2.4) | 88.65 | 88.76 | +0.11 | +0.1 |
| `IL_R10_l` | Eccentric (2.5-4.0) | 81.50 | 81.61 | +0.11 | +0.1 |
| `IL_R11_r` | Pre-bend (0.5-1.0) | 0.03 | 0.01 | -0.01 | +0.0 |
| `IL_R11_r` | Concentric (1.0-2.0) | 19.89 | 19.95 | +0.06 | +0.3 |
| `IL_R11_r` | Hold (2.0-2.4) | 24.81 | 24.85 | +0.04 | +0.2 |
| `IL_R11_r` | Eccentric (2.5-4.0) | 27.48 | 27.64 | +0.16 | +0.6 |
| `IL_R12_r` | Pre-bend (0.5-1.0) | 0.01 | 0.00 | -0.01 | +0.0 |
| `IL_R12_r` | Concentric (1.0-2.0) | 7.98 | 8.20 | +0.22 | +2.7 |
| `IL_R12_r` | Hold (2.0-2.4) | 12.39 | 12.61 | +0.22 | +1.8 |
| `IL_R12_r` | Eccentric (2.5-4.0) | 13.20 | 13.58 | +0.38 | +2.9 |
| `LTpL_L5_r` | Pre-bend (0.5-1.0) | 18.54 | 18.48 | -0.06 | -0.3 |
| `LTpL_L5_r` | Concentric (1.0-2.0) | 45.83 | 45.75 | -0.09 | -0.2 |
| `LTpL_L5_r` | Hold (2.0-2.4) | 49.68 | 49.65 | -0.03 | -0.1 |
| `LTpL_L5_r` | Eccentric (2.5-4.0) | 45.86 | 45.85 | -0.01 | -0.0 |
| `LTpL_L5_l` | Pre-bend (0.5-1.0) | 18.72 | 18.67 | -0.05 | -0.3 |
| `LTpL_L5_l` | Concentric (1.0-2.0) | 46.71 | 46.64 | -0.07 | -0.1 |
| `LTpL_L5_l` | Hold (2.0-2.4) | 51.06 | 51.05 | -0.02 | -0.0 |
| `LTpL_L5_l` | Eccentric (2.5-4.0) | 47.20 | 47.20 | -0.01 | -0.0 |

## Verdict: PASS

Coupler removal does not alter ES activation patterns. The modified model is suitable for box motion v6 design and Phase 2 analyses.

Time-series plot: `images/phase1a_regression_smoke.png`
