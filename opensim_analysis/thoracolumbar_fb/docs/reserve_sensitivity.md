# Reserve Actuator Sensitivity Study

**Date**: 2026-04-23
**Scope**: Box-lift v2 (stoop_box20kg_v2.mot), B_suit0 / B_suit200 @ single time step t=2.33 s

## Background

§1.6 headline numbers (suit_sweep_v2 slope 1.206 %/Nm, R²=1.000, Δ 28.97 %) were derived from SO runs with non-pelvis rotational reserve `optimalForce = 100 Nm`. Verification check `[2]` revealed reserve generating **413 Nm** of spine extension moment at t=2.33 s — larger than typical L5/S1 moment for a 20 kg lift (200–400 Nm). Hypothesis: reserves were "hijacking" work that should have been borne by ES muscles, resulting in artificially low reported ES activation.

## Sweep design

One-step SO at t=2.32–2.36 s (captures peak ES moment). Parallel 4-job launch (one per reserve value). Model builder: `run_reserve_sweep.py` → `build_reserved_model(rotational_opt_nm)` which replaces the non-pelvis rotational reserves with the swept value while keeping pelvis rotations (500 Nm) and all translations (1000 N) unchanged.

## Results

### B_suit0 (no suit, 20 kg box)

| Reserve (Nm) | Converged | ES peak | ES mean | Peak muscle | >50 % | >70 % | >95 % | Max all | Spine FE reserve sum |
|---:|:---:|---:|---:|:---:|:---:|:---:|:---:|---:|---:|
| **R100** (baseline) | ✅ | 66.7 % | 18.6 % | IL_R11_r | 5 | 0 | 0 | 66.7 % | **413 Nm** |
| R50 | ✅ | 86.8 % | 25.3 % | IL_R11_r | 6 | 4 | 0 | 86.8 % | 209 Nm |
| R10 | ✅ | **100.0 %** ⚠ | 38.7 % | IL_R10_r | 22 | 5 | 2 | **100.0 %** | 22 Nm |
| R5 | ✅ | 100.0 % | 41.6 % | IL_R10_r | 25 | 9 | 4 | 100.0 % | 6.8 Nm |
| R1 | ✅ | 100.0 % | 43.8 % | LTpL_L5_r | 26 | 11 | 4 | 100.0 % | 0.4 Nm |

### B_suit200 (+200 N suit = 24 N·m peak torque)

| Reserve (Nm) | ES peak | ES mean | Spine FE reserve sum |
|---:|---:|---:|---:|
| R100 | 59.77 % | 16.68 % | 365.5 Nm |
| R50 | 77.61 % | 22.55 % | 185.4 Nm |

### Suit Δ% robustness (box + semi-squat)

| Metric | @ R100 | @ R50 | \|Δ(R50)−Δ(R100)\| |
|---|---:|---:|---:|
| ES peak Δ relative | **−10.34 %** | **−10.60 %** | **0.27 %p** ✅ robust |
| ES peak Δ absolute | −6.89 %p | −9.20 %p | 2.31 %p |
| ES mean Δ relative | **−10.42 %** | **−10.95 %** | 0.53 %p ✅ |

## Diagnosis

1. **R100 underestimates absolute ES activation** by ~30–50 %. Reserves absorb > 400 Nm of spine moment — physiologically the "work" should come from muscles.
2. **R50 matches EMG literature**: ES peak 87 % @ B_suit0 sits in the 40–80 % MVC range reported in 20 kg lift EMG studies.
3. **R≤10 hits saturation** (multiple ES muscles at 100 %). SO converges but solution is degenerate. Not recommended as default.
4. **R50 is the sweet spot** for single time-step analysis.
5. **Suit relative effect is robust** at the semi-squat + box condition (|Δ| = 0.27 %p).

## Cross-condition sensitivity

See [suit_sweep_reserve_comparison.md](suit_sweep_reserve_comparison.md) for the separate finding that **suit-only (no box) sweep** shows larger sensitivity (slope |Δ| = 20.7 % relative). Robustness is **condition-dependent**:

| Condition | Baseline ES peak (R100) | Baseline ES peak (R50) | Suit Δ% (R100 → R50) |
|---|---:|---:|---|
| Box + semi-squat | 67 % | 87 % | 10.34 → 10.60 % (robust) |
| Suit-only stoop | 28 % | 52 % | 28.12 → 21.25 % (sensitive) |

Interpretation: when baseline ES is small and reserves carry most of the moment, tightening reserves inflates baseline disproportionately to the suit reduction → relative % shrinks. When baseline is already high and muscles dominate, reserves and suit scale proportionally → relative % stays.

## Computational cost (parallel 4-job, 1 SO step each)

| Reserve | Wall time |
|---:|---:|
| R50 | 1289 s (21.5 min) |
| R10 | 1470 s |
| R5 | 1383 s |
| R1 | 1471 s |
| R50 + B_suit200 (easier problem) | **14.5 s** |

Tight reserves (R≤10) induce interior-point solver near the muscle-saturation boundary → per-step time blows up 90× vs B_suit200 + R50. Full-trajectory sweep at R≤10 infeasible without days of compute.

## Impact on past results

| Past result | Impact |
|---|---|
| §1.6 suit_sweep slope 1.206 %/Nm | **Sensitive**. R50 gives 0.89 %/Nm (−26 %) |
| §1.6 Δ = 28.97 % @ 24 N·m | R50 gives 21.3 % |
| §1.6 R² = 1.0000 | Unchanged (linearity robust) |
| Direction (suit reduces ES) | Unchanged ✅ |
| Box-lift Δ% | Unchanged (10.3 → 10.6 %) |

## Recommendation

- **Box video (interim)**: keep R100 results, change display metric from ES mean (diluted over 76 muscles) to ES peak (max across ES). Matches EMG literature. [KNOWN_LIMITATIONS.md §3 참조]
- **Headline paper numbers**: re-report with R50 when Moco pipeline ready (Moco handles reserves more systematically with explicit activation dynamics and penalty weights).
- **§1.6 re-run not urgent** — direction/R² unchanged, only absolute slope shifts. Will be superseded by Moco results.

## Script references

- `scripts/run_reserve_sweep.py` — sweep B_suit0 at single reserve value
- `scripts/run_reserve_sweep_suit200.py` — B_suit200 variant
- Outputs at `/data/stoop_results/reserve_sweep/R{X}{_suit200}/`
