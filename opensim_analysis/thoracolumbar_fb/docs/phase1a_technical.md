# Phase 1a Full — Technical Notes

For collaborators / future maintainers reproducing or extending the pipeline.

## 1. Software stack

| Component | Version |
|---|---|
| Python | 3.10 (conda env `opensim`) |
| OpenSim | 4.5.2 (`/home/sysop/miniconda3/envs/opensim/`) |
| CasADi | bundled with OpenSim Moco |
| IPOPT | bundled (linear solver `ma27`) |
| Hardware | 56 CPU threads, 125 GiB RAM, 1.8 T disk |

## 2. Model preparation

ThoracolumbarFB v2.0 has 57 locked coordinates in 29 joints which Moco's CasADi solver cannot handle. We replaced them with `WeldJoint` instances.

```bash
python opensim_analysis/thoracolumbar_fb/scripts/prepare_model_for_moco.py
```

→ produces `/data/opensim_models/.../MaleFullBodyModel_v2.0_OS4_moco_stoop.osim`. Verification: kinematic max error 0.000 mm vs original at default pose and across stoop_v5 motion (see [`docs/kinematic_error_table.md`](kinematic_error_table.md)).

29 joints removed — 84 coordinates total (57 locked + 27 free-but-dormant rib X-rotations and sternum rotations that have no role in any planned analysis). Result: 81 free coords down from 165, all muscles and bodies preserved.

## 3. Phase 1a muscle subset

114 muscles selected from 620 (option D per user 2026-04-24):

| Group | Prefix | Count |
|---|---|---:|
| Iliocostalis | `IL_` | 24 |
| Longissimus thoracis pars thoracis | `LTpT_` | 42 |
| Longissimus thoracis pars lumborum | `LTpL_` | 10 |
| Quadratus lumborum | `QL_` | 36 |
| Rectus abdominis | `rect_abd_{r,l}` | 2 |

Implementation: XML-edit removes the other 506 muscles from the ForceSet directly (bypasses an OpenSim segfault when `ForceSet.remove()` is called on muscles via Python). See `prepare_model()` in `run_moco_phase1a_full.py`.

Excluded for Phase 1b (deferred): MF (50), multifidus (46), deep/sup-mult (14), EO (92), IO (12), psoas (22).

## 4. Reference kinematics

`stoop_synthetic_v5.mot` is in degrees with `inDegrees=yes` header. Pre-conversion to radians via `prepare_reference()` because direct feed to `TableProcessor` does not auto-convert reliably across all Moco versions. Trimmed to t=0–5 s and saved as `states_reference.sto`.

## 5. GRF integration

`stoop_grf_v5.{sto,xml}` provides constant 50/50 vertical GRF (368 N each foot, total 736 N ≈ 75 kg body weight). Applied via `ModOpAddExternalLoads(grf_xml)` in the model processor. The `.sto` file must reside next to the `.xml` (we copy both into the run directory).

Effect on solver: pelvis_ty reserve dropped from **799 N (no GRF) → 46 N (with GRF)**; spine FE reserves unchanged (~20 Nm). The 46 N residual reflects small numerical mismatches between the prescribed kinematic acceleration and the GRF profile.

## 6. MocoInverse configuration

```python
inverse = osim.MocoInverse()
inverse.setName('phase1a_full')

model_proc = osim.ModelProcessor(model_path)
model_proc.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
model_proc.append(osim.ModOpIgnoreTendonCompliance())          # rigid tendon, no fiber_length state
model_proc.append(osim.ModOpIgnorePassiveFiberForcesDGF())      # standard for inverse problems
model_proc.append(osim.ModOpAddExternalLoads(grf_xml))
model_proc.append(osim.ModOpAddReserves(10.0))                 # 10 Nm/N optF, applied to ALL coords
inverse.setModel(model_proc)

inverse.setKinematics(osim.TableProcessor(ref_path))
inverse.set_initial_time(0.0)
inverse.set_final_time(5.0)
inverse.set_mesh_interval(0.1)                                 # = (5-0)/50 → 50 intervals
inverse.set_kinematics_allow_extra_columns(True)

solution = inverse.solve()
```

### Why MocoInverse, not MocoTrack

We attempted MocoTrack first (smoke v1, see [`docs/smoke_test_v1_diagnosis.md`](smoke_test_v1_diagnosis.md)). The cost function was Pareto-empty:
- Tracking demanded 200–400 Nm spine extension moment.
- Muscles saturate short of that (per SO R10).
- Reserves had to absorb the rest, but `w_reserve=100` made any reserve use very expensive.
- Solver oscillated between feasible-expensive and cheap-infeasible. After 1 h 54 m and 267 IPOPT iterations, halted.

MocoInverse prescribes kinematics as equality constraints — no tracking trade-off — and matches our scientific goal (activation dynamics at given motion). Converged in 140 s on the same hardware.

## 7. Outputs and validation

- `solution.sto`: 101 time points × 495 columns (114 muscle activations + 73 reserve controls + 81 coordinates × 2 + auxiliary). 813 KB.
- IPOPT: `Optimal Solution Found.` Objective `excitation_effort = 434.1`.
- Spine FE reserve sum at peak (t=2.5 s): **19.4 Nm** — matches SO R10 reference (22 Nm) within 12 %.
- Eccentric→concentric activation asymmetry: smoke 2-s window +29.7 %p vs full 5-s +29.4 %p (variance 0.3 %p). Result is robust to motion window length and mesh density.

## 7b. Verifications (post-hoc)

### Bilateral symmetry sanity (Phase 1a Full)

| Pair | Right | Left | Difference |
|---|---:|---:|---:|
| IL_R10 Hold mean | 87.7 % | 85.6 % | 2.1 %p |
| IL_R11 Hold mean | 23.1 % | 21.3 % | 1.8 %p |
| LTpL_L5 Hold mean | 48.6 % | 49.9 % | −1.3 %p |
| LTpL_L5 Δ(con−ecc) | +13.4 %p | +14.2 %p | 0.8 %p |

→ Left-right activation differences ≤ 2.1 %p. Model symmetry confirmed; provides clean baseline for asymmetric tasks (one-arm reach, lateral bend) in future analyses.

### Reference motion plateau check (Case A)

Aggregate lumbar flexion-extension velocity from `stoop_synthetic_v5.mot`:

| Phase | Time | max |velocity| (deg/s) |
|---|---|---:|
| Eccentric | 1.0–2.0 | 22.0 |
| Hold (script-defined) | 2.0–2.5 | 15.6 |
| **True plateau** | **2.5–3.0** | **0.07** |
| Concentric | 2.5–4.0 | 22.0 |

Reference motion has a clear ~0.5 s near-static plateau at peak flexion (vel < 0.5 % of eccentric peak). The IL_R10 dip at t≈2.7 s during this plateau is a faithful response to the kinematic structure (Case A). Note that the user-defined "Hold" phase (2.0–2.5) overlaps the eccentric ramp end; the actual plateau falls in the early "Concentric" window. Phase boundary semantics may be revised in subsequent reports for precision.

### Quiet & Recovery phase observations (minor)

- t≈0.4 s: brief activation excursion (~5 %) in IL_R10 — coincides with motion onset (small acceleration impulse). Not a sustained phase.
- t≈4.0–4.3 s: short re-activation spike (~28 %) in IL_R10 during the deceleration phase of the concentric extension as the trunk approaches upright. Mirror of the t≈2.4 s deceleration peak, scaled to the lower late-cycle moment demand.

These are kinematic-driven (acceleration/deceleration of the trunk), not independent recruitment events.

## 8. Known issues / limitations

| Issue | Status / mitigation |
|---|---|
| 27 free-but-dormant coords welded along with locked ones | Acceptable: rib-X and sternum rotations have no role in any planned analysis |
| Knee/hip/ankle reserves up to 158 Nm at peak | Expected: Phase 1a excludes leg muscles by design. Reserves do the work. Phase 1b/2 will include legs as needed. |
| pelvis_ty residual 46 N | Small. Could be eliminated by re-fitting GRF acceleration profile to kinematic accelerations (~0.05 m/s² noise → 30 N difference). Not blocking. |
| Muscle peaks differ slightly between SO and MocoInverse | Expected: SO is instantaneous, MocoInverse smooths via activation dynamics. Both are physiologically valid; MocoInverse is closer to EMG-observable behavior. |

## 9. Reproduction recipe

```bash
# 1. Prepare model (one-time, output reused everywhere)
python opensim_analysis/thoracolumbar_fb/scripts/prepare_model_for_moco.py

# 2. Smoke test with GRF (verify in 2 min)
python opensim_analysis/thoracolumbar_fb/scripts/run_moco_phase1a_full.py smoke

# 3. Full run
python opensim_analysis/thoracolumbar_fb/scripts/run_moco_phase1a_full.py full

# 4. Analyze + plots
python opensim_analysis/thoracolumbar_fb/scripts/analyze_phase1a_full.py

# 5. Polished figures (paper-quality)
python opensim_analysis/thoracolumbar_fb/scripts/polish_phase1a_figures.py
```

Total runtime: **~5 minutes** end-to-end on this hardware (model prep 10 s + smoke 70 s + full 140 s + analysis 5 s + figures 10 s).
