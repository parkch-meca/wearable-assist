# Phase 1a Smoke Test v1 — Diagnosis (Halted)

**Date**: 2026-04-24
**Configuration**: MocoTrack, 114 muscles, stoop_v5 t=1.0–3.0 s, mesh=25,
w_track=1, w_effort=0.1/muscle, w_reserve=100/reserve, reserve optF=100 Nm, max_iter=500.
**Outcome**: Halted by user at 284 iter / 1 h 54 m / RSS 6.3 GB. **Not converged**.

---

## Iteration-by-iteration (every ~50)

| iter | obj | inf_pr | inf_du | phase |
|---:|---:|---:|---:|---|
| 0 | 5.70 | 2.90e+04 | 3.30e-03 | initial guess |
| 50 | 120.2 | 7.90e+02 | 1.95e+03 | early descent (obj rose from iter 73's 45.7) |
| **73** | **45.7** | 6.33e+03 | 6.54e+07 | best obj reached, still infeasible |
| 97 | 449 | 1.41e+05 | **1.53e+14** | **first dual blow-up (restoration)** |
| 118 | 113 | 5.55e+03 | 8.45e+12 | restoration ongoing |
| 168 | 72 | 2.22e+03 | 7.16e+10 | slowly recovering |
| 225 | ~80 | ~4e+03 | ~1e+07 | oscillating |
| 256 | 1076 | **9.0** | 6.47e+08 | **near-feasible (inf_pr=9) but obj high** |
| 284 | 68.7 | 6.05e+03 | 2.19e+05 | final (halt) |

**Oscillation signature** (last 50 iters):
- obj mean = 587.5, std = 513.6, CV = 0.87 (87% relative variation) — not converging
- inf_pr: 9 to 10,000 range (jumping between feasible and far-infeasible)
- inf_du: 10^5 to 10^9 (still 5-9 orders above typical convergence threshold 1e-6)

## Observed phase structure

1. **iter 0–73**: Smooth initial descent. Obj 5.7 → 45.7 monotonically; inf_pr 29 K → 6 K. Normal behaviour.
2. **iter 74–96**: First restoration phase. Dual infeasibility grows from 10^7 to **10^14** (catastrophic). IPOPT enters its regularization mode (`lg(rg)` column shows ±11 at iter 97, meaning 10^11 regularization factor). This is a classic "large Lagrangian Hessian spike" — usually caused by a degenerate constraint Jacobian (ill-posed problem).
3. **iter 97–256**: Alternating feasibility–cost trade-offs. Every 10–30 iter, obj spikes up to 500–1000 when it gains feasibility (inf_pr ↓), then drops back to 70–150 when it tolerates infeasibility (inf_pr ↑). Net: no convergence direction.
4. **iter 256**: momentarily achieved inf_pr=9 (near-feasible) with obj=1076. This tells us **the feasible obj is around 1000 units**, and the "desired" cheap obj (~45) is **structurally unreachable** under the current cost function.

## Cost-term pathology

The feasible obj at iter 256 is ≈ 1076. Assuming reserves contribute most of it:

- 26 mesh points × ~40 active rotational reserves each = ~1040 active control-squared terms
- Average reserve control per active point ≈ sqrt(1076 / (100 × 1040)) ≈ **0.10**
- With reserve optF = 100 Nm, this means **~10 Nm average reserve force per active coord**
- Sum across spine FE reserves (8 coords): ~80 Nm — far below the 200–400 Nm that the motion actually requires for ES support

**Interpretation**: the kinematics prescribe ~200–400 Nm of spine extension moment at peak bend. Muscles alone cannot produce this (SO results show IL_R11_r saturates even at R=10). So reserves MUST carry a large fraction. With w_reserve = 100 and optF = 100 Nm, **any reserve use is very expensive** → solver keeps flipping between "use reserves, feasible, obj 1000+" and "don't use reserves, infeasible by kinematics, obj 45–70". **No middle ground exists under this cost structure** → oscillation.

## Why v1 could not converge in principle

The cost function has a **mutually exclusive pair** of penalties:
- Tracking (w=1) demands matching kinematics which require large spine moments
- Reserve penalty (w=100) makes reserves expensive
- Muscle effort (w=0.1) is the cheapest path — but muscles saturate

So the Pareto front has no interior point. Either feasible (expensive) or cheap (infeasible).

---

## Three proposed corrections (pick one)

### (A) Cost rebalancing — MocoTrack continued

```
w_track   : 1  → 10      (strongly prioritize kinematics)
w_effort  : 0.1            (unchanged)
w_reserve : 100 → 10       (allow reserves more freely)
```

**Rationale**: Remove the oscillation trigger. With w_reserve=10, reserves are 10× cheaper, solver won't flip between "use reserves" and "don't". Tracking weight bumped to 10 prevents solver from letting kinematics drift.

**Expected outcome**: Converge in 200–400 iter. Reserves: 100–200 Nm spine (similar to SO R100's 413 Nm but significantly reduced vs. that). Absolute ES peak: similar to SO R50 (~87 % on IL_R11_r). Relative suit effect: robust per yesterday's analysis.

**Runtime**: ~1 h (similar pace to v1, fewer oscillations).
**Risk**: Reserves may still be larger than desired for paper headline numbers.

### (B) Mesh refinement — MocoTrack continued

```
mesh_intervals : 25 → 50   (0.04 s interval)
all other settings kept
```

**Rationale**: Finer mesh → smoother dynamic discretization → fewer sudden feasibility jumps at collocation points.

**Expected outcome**: Possibly converges, but the **structural cost mismatch (from v1 diagnosis) persists**. Mesh refinement alone may not fix the Pareto-front-empty issue.

**Runtime**: 2–3 h.
**Risk**: Core problem unchanged — could just produce the same oscillation more slowly.

### (C) Switch to MocoInverse — **strongly recommended**

```
Problem   : MocoTrack → MocoInverse
Kinematics: prescribed (kinematic constraint, no tracking slack)
Cost      : only muscle effort + reserve (no tracking term)
Other     : mesh=25, 114 muscles, reserves optF=10 Nm, w_reserve=100
```

**Rationale**:
- MocoTrack's value is kinematic deviation allowed. In our smoke test, kinematics is fully prescribed by `stoop_v5.mot` — no reason to let it drift.
- MocoInverse forces exact kinematic adherence via equality constraints, only optimizes muscle/reserve controls.
- Problem becomes dramatically simpler: no tracking trade-off → no Pareto oscillation.
- **This is the exact analog of SO with activation dynamics** — the user's stated purpose ("eccentric/concentric asymmetry").
- Reserve optF lowered to 10 Nm so reserves are structurally expensive (match SO R10 analysis), making muscle effort the preferred path.

**Expected outcome**: Smooth convergence in 50–150 iter. Analogous to SO R10 pattern but with activation dynamics continuity. ES peaks 70–100 % (as in SO R10).

**Runtime**: 15–45 min.
**Risk**: Some muscles may saturate (as in SO R10) — acceptable because it matches physiological ceiling.

---

## Recommendation: Option C

Option C directly addresses the diagnosed root cause (cost-function Pareto-empty) by removing the tracking degree of freedom. It also aligns with the project's stated scientific goal (activation dynamics, not motion generation). Expected to complete well within the 1-hour "smoke test normal" budget.

If the user prefers to stay on MocoTrack (for future motion generation use cases), Option A is the better compromise vs. B.

Option B is not recommended alone — it addresses a symptom (mesh) rather than cause (cost).

---

## Artifacts preserved (do not delete)

- `/data/wearable-assist/results/phase1a_smoke/run.log` — full IPOPT log
- `/data/wearable-assist/results/phase1a_smoke/iter_summary.json` — parsed iter data
- `/data/wearable-assist/results/phase1a_smoke/phase1a_model.osim` — 114-muscle model (reusable)
- `/data/wearable-assist/results/phase1a_smoke/states_reference.sto` — trimmed reference (reusable)

These artifacts remain valid inputs for any v2 retry with modified cost or solver.
