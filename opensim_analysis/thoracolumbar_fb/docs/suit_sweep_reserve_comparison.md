# Suit Sweep Slope — R100 vs R50 Robustness Check

**Date**: 2026-04-23
**Motion**: stoop_synthetic (3 s, no box), sampled at t = 2.33 s
**Conditions**: F = 0, 50, 100, 150, 200 N → T = 0, 6, 12, 18, 24 N·m

## Data @ t=2.33 s

| F (N) | T (N·m) | ES peak R100 | ES peak R50 | ES mean R100 | ES mean R50 | Reserve R100 | Reserve R50 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.0 | 27.64 % | **51.61 %** | 7.87 % | 14.72 % | 178 Nm | 115 Nm |
| 50 | 6.0 | 25.70 % | 48.86 % | 7.34 % | 13.93 % | 164 Nm | 107 Nm |
| 100 | 12.0 | 23.76 % | 46.12 % | 6.81 % | 13.15 % | 149 Nm | 100 Nm |
| 150 | 18.0 | 21.81 % | 43.38 % | 6.28 % | 12.36 % | 134 Nm | 93 Nm |
| 200 | 24.0 | 19.86 % | **40.64 %** | 5.76 % | 11.58 % | 119 Nm | 86 Nm |

All 10 runs converged (`ok=True`). R² of the linear fit = 1.0000 for all four slopes.

## Linear fit: ES reduction (%) vs torque (N·m)

| Fit | Slope | Intercept | R² | Δ @ 24 N·m | Baseline @ F=0 |
|---|---:|---:|---:|---:|---:|
| **§1.6 historical** (R100 mean, full 0–3 s time-peak) | **+1.206 %/Nm** | — | **1.0000** | **+28.97 %** | — |
| R100 peak @ t=2.33 | +1.172 %/Nm | −0.009 | 1.0000 | +28.12 % | 27.64 % |
| R100 mean @ t=2.33 | +1.120 %/Nm | +0.009 | 1.0000 | +26.88 % | 7.87 % |
| **R50 peak @ t=2.33** | **+0.885 %/Nm** | +0.007 | 1.0000 | **+21.25 %** | 51.61 % |
| **R50 mean @ t=2.33** | **+0.889 %/Nm** | −0.000 | 1.0000 | **+21.33 %** | 14.72 % |

## Robustness verdict (user threshold: |Δslope|/R100 < 10 % relative)

| Metric | \|Δ\| relative | Verdict |
|---|---:|---|
| peak slope | **24.4 %** | ⚠ sensitive |
| mean slope | **20.7 %** | ⚠ sensitive |
| \|Δ(red@24Nm)\| (peak) | 6.87 %p | ⚠ > 5 %p |
| \|Δ(red@24Nm)\| (mean) | 5.55 %p | ⚠ > 5 %p |

Both slope and reduction magnitude shift more than the 10 % / 5 %p thresholds set by the user. **Branch B** (sensitive) per the user's decision tree.

## Interpretation

The suit-only (no box) motion has a small baseline spine moment (no external load). Reserves absorb most of it at R100 (178 Nm reserve vs ES peak 27.6 %). Tightening reserves at R50 pushes the absolute activation up substantially (51.6 %), but the suit torque (constant 24 N·m max) does not scale with the baseline. Thus:

- **Absolute reduction @ 24 N·m**: R100 gives 7.78 %p (27.64 → 19.86), R50 gives 10.97 %p (51.61 → 40.64). Suit does MORE absolute work at R50.
- **Relative reduction @ 24 N·m**: R100 gives 28.12 %, R50 gives 21.25 %. Smaller relative share at R50 because baseline is larger.

Direction and linearity are preserved. The suit still reduces ES activation monotonically with torque, R² = 1.000 in both reserve regimes.

## Contrast with box + semi-squat condition

In the box + semi-squat condition (see [reserve_sensitivity.md](reserve_sensitivity.md)):
- Baseline ES peak 67 % (R100) → 87 % (R50)
- Suit Δ% 10.34 → 10.60 (|Δ| = 0.27 %p, **robust**)

The box condition loads the spine much more heavily. Muscles are already the dominant force source even at R100, so reserve tightening rescales baseline and suit effect proportionally → relative % preserved.

## Implications for past results

| Item | Status |
|---|---|
| §1.6 slope 1.206 %/Nm → R50 0.89 %/Nm | ~26 % lower magnitude |
| §1.6 Δ=28.97 % → R50 ~21 % | Headline number shifts |
| R² = 1 preserved | ✅ |
| Monotonic decrease preserved | ✅ |
| Fig 7 per-muscle reductions | Re-run at R50 recommended before paper submission |
| Fig 8 infographic (46 %, 37 %) | Same |

**§1.6 slope is reserve-sensitive** but conclusions (suit reduces ES, linear dose-response) are robust. Re-running at R50 will bring numbers closer to the EMG-literature baseline while preserving the story.

## Scripts

- `scripts/run_suit_sweep_R50.py` — 5-condition suit sweep @ R50
- Outputs at `/data/stoop_results/suit_sweep_R50/F{0,50,100,150,200}/`
- Baseline at `/data/stoop_results/suit_sweep_v2/F*/` (R100)
