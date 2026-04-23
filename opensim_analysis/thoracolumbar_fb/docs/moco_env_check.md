# OpenSim Moco Environment Check

**Date**: 2026-04-23
**Host**: parkch@Precision-7960-Tower

## [3.1] Python OpenSim Moco import

```python
>>> import opensim
>>> opensim.__version__
'4.5.2'
>>> opensim.MocoStudy()       # OK
>>> opensim.MocoTrack()        # OK
>>> opensim.MocoInverse()      # OK
```

✅ Moco classes available. Built-in CasADi backend is present (no separate `casadi` pip package required; OpenSim links it internally).

## [3.2] Moco examples

Location: `/home/sysop/miniconda3/envs/opensim/share/doc/OpenSim/Code/Python/Moco/`

Available:
- `exampleSlidingMass.py` — simplest one-body demo
- `exampleHangingMuscle.py` — single-muscle quick test
- `exampleOptimizeMass.py`
- `examplePredictAndTrack.py`
- `exampleKinematicConstraints.py`
- `exampleSquatToStand/` — 3-DOF, 9-muscle squat
- `example3DWalking/` — MocoInverse + MocoTrack end-to-end
- `exampleEMGTracking/`
- `example2DWalking/`

✅ Smoke-test candidate: `exampleSlidingMass.py` (< 1 min expected).

## [3.3] ThoracolumbarFB compatibility with Moco

```python
m = osim.Model('MaleFullBodyModel_v2.0_OS4_modified.osim')
m.initSystem()
# Muscles: 620, Coordinates: 165, Forces: 648

study = osim.MocoStudy()
problem = study.updProblem()
problem.setModelAsCopy(m)           # OK
solver = study.initCasADiSolver()    # ❌ FAIL
```

❌ **Failure**:
```
Coordinate '/jointset/T12_r12R_CVjnt/T12_r12R_Y' is locked, but Moco does not support
locked coordinates. Consider replacing the joint for this coordinate with a WeldJoint
instead.
```

The ThoracolumbarFB model has numerous locked rib / costovertebral joints (`_r*_CVjnt`) encoded as locked coordinates. Moco requires them to be replaced with `WeldJoint` instances.

### Fix plan (to run before Moco pipeline work begins)

Write `prepare_model_for_moco.py`:
```
for every Joint J in model:
    if every Coord c of J is locked (default value = min = max):
        replace J with WeldJoint preserving parent/child frames
```

Expected scope: ~40–60 rib/costovertebral joints need welding. Alternative: iterate through `CoordinateSet` and for each locked coordinate, walk up to its parent Joint and swap.

Effort estimate: ~1 hour to script + validate (tree walk, preserve kinematic chain).

## [3.4] Hardware

| Resource | Value |
|---|---|
| CPU threads (`nproc`) | **56** |
| RAM | **125 GiB** total (10 used, 115 free) |
| Swap | 15 GiB |
| `/data` disk | 1.9 T / 68 G used / **1.8 T free** |

Moco CasADi solver is CPU-bound and can utilize parallel derivatives. 56 threads ample for mesh refinement sweeps. Disk/RAM headroom fine for extended optimization runs.

## [3.5] CasADi dependency

```python
>>> import casadi
ModuleNotFoundError: No module named 'casadi'
```

⚠ Standalone CasADi Python package not installed. **Not required** — OpenSim 4.5.2 links its own CasADi version internally and `MocoCasADiSolver` works without the pip package. Confirmed by successful `initCasADiSolver()` on a trivial problem (fails only on ThoracolumbarFB for the locked-coordinate reason above, not a CasADi missing error).

## Summary

| Check | Status | Action |
|---|:---:|---|
| [3.1] Moco Python import | ✅ | none |
| [3.2] Examples available | ✅ | pick `exampleSlidingMass.py` for first run |
| [3.3] TL model direct load | ⚠ | must replace ~40–60 locked joints with WeldJoints |
| [3.4] Hardware | ✅ | 56 CPU / 125 GiB RAM / 1.8 T disk |
| [3.5] Dependencies (CasADi) | ✅ | internal OK, standalone not needed |

**Moco 착수 준비도**: model-preprocessing 1개 작업 완료 시 진행 가능. 경로:

1. `prepare_model_for_moco.py` 작성·실행 (~1 h)
2. `exampleSlidingMass` smoke test (< 1 min)
3. MocoInverse로 v2 motion의 박스 들기 재계산 파이프라인 설계 (activation dynamics, reserve penalty)
4. 다른 동작 확장 시 동일 파이프라인 재사용

Moco 파이프라인 설계 논의는 위 1·2 완료 후 사용자와 진행.
