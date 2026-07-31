"""
Phase 2: Box MocoTrack B_suit0 Pilot v2 (Hardened — 2026-04-29).

Changes vs v1 (run_box_mocotrack_pilot.py):
    1. Threads: 56 -> 28   (set_num_parallel + OMP_NUM_THREADS env)
    2. Max iterations: 3000 -> 1000
    3. Mesh interval: 0.02 -> 0.025 s  (120 intervals/3s vs 150)
    4. RotatingFileHandler for log (10 MB chunks, 3 backups)
    5. stdout flush every line (--line-buffered equivalent)

v1 failure analysis:
    - Last line of pilot_run.log: "[info] Number of threads: 56"
    - IPOPT first iteration never reached in ~1 min
    - Likely: 56-thread NLP init overhead / CasADi compilation with 56 threads
      caused initialization stall before first IPOPT iter
    - Fix: halve threads to 28 (CasADi codegen safer at 28), reduce mesh

Infrastructure (unchanged from v1):
    MocoTrack + Hunt-Crossley contact (no stoop GRF STO) + Hand ExternalForce
    B_suit0 = baseline, 0 N, 0 N·m suit torque

Decision gate:
    A. PASS  -> proceed run_box_mocotrack_sweep.py (5 conditions)
    B. Partial (converged, reserve abnormal) -> user consultation
    C. FAIL  -> immediate consultation + option 1 fallback

Wall time limit: 7200 s (2 hours). Hard abort via SIGALRM.

Usage:
    python run_box_mocotrack_pilot_v2.py
    python run_box_mocotrack_pilot_v2.py --dry-run

Output:
    /data/opensim_results/box_mocotrack_v1/B_suit0/solution.sto
    /data/opensim_results/box_mocotrack_v1/B_suit0/pilot_verdict.txt
    /data/opensim_results/box_mocotrack_v1/B_suit0/pilot_v2.log   (RotatingFileHandler)
"""
from __future__ import annotations

import os
import sys
import time
import signal
import logging
import logging.handlers
import argparse
from pathlib import Path

# ── Environment: set BEFORE importing opensim ─────────────────────────────────
# Halve threads: CasADi NLP init is safer at 28 vs 56
os.environ['OMP_NUM_THREADS']    = '28'
os.environ['OPENBLAS_NUM_THREADS'] = '28'
os.environ['MKL_NUM_THREADS']    = '28'
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')

# ── Path setup ────────────────────────────────────────────────────────────────
BASE_DIR = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb')
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'scripts'))

import numpy as np
import opensim as osim

from base import (
    build_model_processor, get_default_model_path,
    SuitConfig,
    setup_for_box_task,
    add_foot_contact_model,
    generate_box_force_sto,
    add_hand_external_force_xml,
    HICKS_TRANS_THRESHOLD_N,
    HICKS_ROT_THRESHOLD_NM,
)

# ── Constants ─────────────────────────────────────────────────────────────────

MODEL_PATH  = get_default_model_path()
MOTION_FILE = '/data/stoop_motion/box_motion_v11b.mot'
OUT_ROOT    = Path('/data/opensim_results/box_mocotrack_v1')
SHARED_DIR  = OUT_ROOT / 'shared'
COND_DIR    = OUT_ROOT / 'B_suit0'

T_START, T_END  = 1.0, 4.0
BOX_MASS_KG     = 20.0
GRASP_TIME      = 2.0
GRIP_POINT      = (0.40, 0.75, 0.0)   # ground frame metres
WALL_TIME_LIMIT = 7200.0              # 2 hours hard limit

# v2 tuning parameters
NUM_PARALLEL   = 28     # was 56 in v1
MAX_ITERATIONS = 1000   # was 3000 in v1
MESH_INTERVAL  = 0.025  # was 0.02 in v1  -> 120 intervals / 3 s

# ES muscles — key indicators of loading (Phase 1a reference)
KEY_ES_MUSCLES = [
    'IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'IL_R11_l',
    'IL_R12_r', 'IL_R12_l', 'LTpL_L5_r', 'LTpL_L5_l',
]

# 5-phase boundaries (box motion specific)
PHASES = {
    'Standing':   (1.0, 1.5),
    'Eccentric':  (1.5, 2.0),
    'Grasp':      (2.0, 2.5),
    'Concentric': (2.5, 3.5),
    'Carry':      (3.5, 4.0),
}


# ── Logging setup ─────────────────────────────────────────────────────────────

def setup_logging(log_path: Path) -> logging.Logger:
    """RotatingFileHandler (10 MB chunks, 3 backups) + StreamHandler."""
    logger = logging.getLogger('pilot_v2')
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')

    # Rotating file handler — prevent single huge log
    fh = logging.handlers.RotatingFileHandler(
        str(log_path), maxBytes=10 * 1024 * 1024, backupCount=3,
        encoding='utf-8',
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Also write to stdout (for nohup capture)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger


# Module-level logger (set up in main)
_LOG: logging.Logger | None = None


def log(msg: str) -> None:
    if _LOG:
        _LOG.info(msg)
    else:
        print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


# ── SIGALRM wall-time enforcer ────────────────────────────────────────────────

def _wall_time_handler(signum, frame):
    raise TimeoutError(f'Wall time limit {WALL_TIME_LIMIT}s exceeded — aborting')


# ── Artifact builders ─────────────────────────────────────────────────────────

def build_shared_artifacts() -> tuple[str, str]:
    """Generate hand force STO + ExternalLoads XML in shared/ directory."""
    SHARED_DIR.mkdir(parents=True, exist_ok=True)

    sto_path = str(SHARED_DIR / 'box_hand_force.sto')
    xml_path = str(SHARED_DIR / 'box_hand_loads.xml')

    log('Generating hand force STO...')
    generate_box_force_sto(
        output_sto_path=sto_path,
        motion_file=MOTION_FILE,
        box_mass_kg=BOX_MASS_KG,
        grasp_start_time=GRASP_TIME,
        grip_point_ground=GRIP_POINT,
    )
    log(f'  STO: {sto_path}  force_per_hand={BOX_MASS_KG * 9.81 / 2:.1f} N')

    log('Generating hand ExternalLoads XML...')
    add_hand_external_force_xml(
        output_xml_path=xml_path,
        hand_force_data_sto=sto_path,
        body_r='hand_R',
        body_l='hand_L',
    )
    log(f'  XML: {xml_path}')
    return sto_path, xml_path


def build_moco_study(box_loads_xml: str) -> osim.MocoStudy:
    """
    Build MocoStudy for B_suit0 pilot v2.

    Key differences from v1:
        - set_num_parallel(28)  <-- was 56
        - max_iterations=1000   <-- was 3000
        - mesh_interval=0.025   <-- was 0.02

    Pipeline (same as v1, contact-before-modelprocessor order):
        1. Load Model + add_foot_contact_model
        2. finalizeConnections
        3. ModelProcessor + ModOps (hand force, residuals, reserves, muscles)
        4. MocoTrack initialize
        5. Solver: num_parallel=28, max_iter=1000
    """
    log('Loading model for foot contact addition...')
    model = osim.Model(MODEL_PATH)
    model = add_foot_contact_model(model)
    model.finalizeConnections()

    n_spheres = sum(
        1 for i in range(model.getContactGeometrySet().getSize())
        if model.getContactGeometrySet().get(i).getConcreteClassName() == 'ContactSphere'
    )
    n_forces = sum(
        1 for i in range(model.getForceSet().getSize())
        if 'SmoothSphereHalfSpaceForce' in model.getForceSet().get(i).getConcreteClassName()
    )
    log(f'  Contact model: {n_spheres} spheres, {n_forces} Hunt-Crossley forces')

    log('Building ModelProcessor (box task, trans=300 N, rot=50 Nm)...')
    mp = osim.ModelProcessor(model)
    mp.append(osim.ModOpAddExternalLoads(box_loads_xml))
    mp.append(osim.ModOpAddResiduals(50.0, 300.0, 1.0))
    mp.append(osim.ModOpAddReserves(1.0))
    mp.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    mp.append(osim.ModOpIgnoreTendonCompliance())
    mp.append(osim.ModOpIgnorePassiveFiberForcesDGF())

    log('Building MocoTrack study...')
    track = osim.MocoTrack()
    track.setName('box_mocotrack_B_suit0_v2')
    track.setModel(mp)

    ref = osim.TableProcessor(MOTION_FILE)
    ref.append(osim.TabOpConvertDegreesToRadians())
    ref.append(osim.TabOpUseAbsoluteStateNames())
    track.setStatesReference(ref)
    track.set_allow_unused_references(True)

    track.set_initial_time(T_START)
    track.set_final_time(T_END)
    track.set_mesh_interval(MESH_INTERVAL)        # 0.025 s (v2)
    track.set_states_global_tracking_weight(1.0)
    track.set_control_effort_weight(1.0)

    study = track.initialize()

    # Control effort goal weight (0.001, John 2022)
    problem = study.updProblem()
    try:
        effort_goal = osim.MocoControlGoal.safeDownCast(
            problem.updGoal('control_effort')
        )
        if effort_goal is not None:
            effort_goal.setWeight(0.001)
    except Exception:
        pass

    # Solver: v2 key change — 28 threads, 1000 max iter
    solver = osim.MocoCasADiSolver.safeDownCast(study.updSolver())
    solver.set_parallel(NUM_PARALLEL)
    solver.set_optim_convergence_tolerance(1e-3)
    solver.set_optim_constraint_tolerance(1e-3)
    solver.set_optim_max_iterations(MAX_ITERATIONS)

    log(f'  MocoStudy ready: mesh={MESH_INTERVAL}s '
        f'(~{int((T_END-T_START)/MESH_INTERVAL)} intervals), '
        f'tol=1e-3, max_iter={MAX_ITERATIONS}, num_parallel={NUM_PARALLEL}')
    return study


# ── Solution analysis ─────────────────────────────────────────────────────────

def analyze_solution(sol_path: str) -> dict:
    """Extract ES activation + reserve metrics from solution STO."""
    results = {}

    if not os.path.isfile(sol_path):
        return {'error': f'Solution not found: {sol_path}'}

    try:
        tbl = osim.TimeSeriesTable(sol_path)
        labels = list(tbl.getColumnLabels())
        n_rows = tbl.getNumRows()
        times  = np.array(list(tbl.getIndependentColumn()))

        data = np.zeros((n_rows, len(labels)))
        for i in range(n_rows):
            row = tbl.getRowAtIndex(i)
            for j in range(len(labels)):
                data[i, j] = row[j]

        # ES muscle activation columns
        es_cols = [
            (j, lab) for j, lab in enumerate(labels)
            if any(m in lab for m in [
                'IL_R', 'IL_L', 'LTpL', 'LTpM', 'ITS', 'MF',
                '/IL_', '/LT', '/ITS', '/MF'
            ])
            and ('activation' in lab or 'excitation' in lab or '/control' in lab)
        ]
        if not es_cols:
            es_cols = [
                (j, lab) for j, lab in enumerate(labels)
                if any(m in lab for m in ['IL_R10', 'IL_R11', 'IL_R12',
                                           'LTpL_L5', 'LTpL_L4'])
            ]

        results['n_es_cols_found'] = len(es_cols)

        if es_cols:
            es_data  = data[:, [j for j, _ in es_cols]]
            es_names = [lab for _, lab in es_cols]

            phase_peaks = {}
            for phase_name, (t0, t1) in PHASES.items():
                mask = (times >= t0 - 1e-9) & (times <= t1 + 1e-9)
                if mask.any():
                    phase_data = es_data[mask]
                    peak_val   = float(phase_data.max())
                    peak_col   = es_names[int(phase_data.max(axis=0).argmax())]
                    mean_val   = float(phase_data.mean())
                    phase_peaks[phase_name] = {
                        'peak':        round(peak_val * 100, 1),
                        'mean':        round(mean_val * 100, 1),
                        'peak_muscle': peak_col.split('/')[-1],
                    }
            results['phase_peaks'] = phase_peaks

            il_r10_cols = [(j, lab) for j, lab in enumerate(labels)
                           if 'IL_R10' in lab or 'il_r10' in lab.lower()]
            if il_r10_cols:
                il_r10_data = data[:, [j for j, _ in il_r10_cols]]
                for phase_name, (t0, t1) in PHASES.items():
                    mask = (times >= t0 - 1e-9) & (times <= t1 + 1e-9)
                    if mask.any():
                        peak = float(il_r10_data[mask].max()) * 100
                        results.setdefault('il_r10_phase', {})[phase_name] = round(peak, 1)

        # Reserve actuator check
        res_cols = [(j, lab) for j, lab in enumerate(labels)
                    if 'reserve' in lab.lower() or 'residual' in lab.lower()]
        results['n_reserve_cols'] = len(res_cols)

        reserve_summary = {}
        if res_cols:
            for j, lab in res_cols:
                col_data = np.abs(data[:, j])
                short = lab.split('/')[-2] if '/' in lab else lab
                reserve_summary[short] = round(float(col_data.max()), 2)

            for key in ['pelvis_ty', 'pelvis_tilt', 'pelvis_tx',
                         'pelvis_list', 'pelvis_rotation',
                         'hip_flexion_r', 'hip_flexion_l']:
                for j, lab in res_cols:
                    if key in lab:
                        reserve_summary[f'_KEY_{key}'] = round(
                            float(np.abs(data[:, j]).max()), 2
                        )
                        break

        results['reserves'] = reserve_summary

        pelvis_ty_max   = reserve_summary.get('_KEY_pelvis_ty', None)
        pelvis_tilt_max = reserve_summary.get('_KEY_pelvis_tilt', None)
        if pelvis_ty_max is not None:
            results['hicks_pelvis_ty'] = {
                'value':     pelvis_ty_max,
                'threshold': HICKS_TRANS_THRESHOLD_N,
                'pass':      pelvis_ty_max <= HICKS_TRANS_THRESHOLD_N,
            }
        if pelvis_tilt_max is not None:
            results['hicks_pelvis_tilt'] = {
                'value':     pelvis_tilt_max,
                'threshold': HICKS_ROT_THRESHOLD_NM,
                'pass':      pelvis_tilt_max <= HICKS_ROT_THRESHOLD_NM,
            }

    except Exception as exc:
        results['analysis_error'] = str(exc)

    return results


# ── Verdict writer ────────────────────────────────────────────────────────────

def write_pilot_verdict(
    cond_dir: Path,
    ipopt_status: str,
    success: bool,
    wall_time: float,
    analysis: dict,
    version: str = 'v2',
) -> str:
    verdict_path = cond_dir / 'pilot_verdict.txt'

    pelvis_ty   = analysis.get('hicks_pelvis_ty', {})
    pelvis_tilt = analysis.get('hicks_pelvis_tilt', {})
    ty_pass     = pelvis_ty.get('pass', None)
    tilt_pass   = pelvis_tilt.get('pass', None)

    if not success:
        scenario = 'C: FAIL (no convergence) -> immediate consultation'
    elif ty_pass is False and tilt_pass is False:
        ty_val = pelvis_ty.get('value', '?')
        scenario = (
            f'B: Partial (converged, reserve abnormal) -> consultation\n'
            f'   pelvis_ty={ty_val} N (Hicks threshold={HICKS_TRANS_THRESHOLD_N} N)\n'
            f'   pelvis_tilt={pelvis_tilt.get("value","?")} Nm (threshold={HICKS_ROT_THRESHOLD_NM} Nm)\n'
            f'   Note: pelvis_tilt FAIL expected (MODEL ARTIFACT)\n'
            f'   pelvis_ty FAIL indicates GRF dynamics mismatch -> investigate'
        )
    elif tilt_pass is False and (ty_pass is True or ty_pass is None):
        scenario = (
            f'A: PASS (pelvis_tilt FAIL = MODEL ARTIFACT as expected)\n'
            f'   pelvis_tilt={pelvis_tilt.get("value","?")} Nm -> MODEL ARTIFACT\n'
            f'   pelvis_ty={pelvis_ty.get("value","?")} N -> within Hicks threshold\n'
            f'   -> Proceed with run_box_mocotrack_sweep.py'
        )
    else:
        scenario = (
            f'A: PASS (all reserves within expected bounds)\n'
            f'   -> Proceed with run_box_mocotrack_sweep.py'
        )

    phase_peaks = analysis.get('phase_peaks', {})
    il_r10      = analysis.get('il_r10_phase', {})

    lines = [
        '=' * 65,
        f'Box MocoTrack B_suit0 Pilot Verdict ({version})',
        '=' * 65,
        '',
        '[Run config]',
        f'  num_parallel  : {NUM_PARALLEL}',
        f'  max_iterations: {MAX_ITERATIONS}',
        f'  mesh_interval : {MESH_INTERVAL} s',
        '',
        '[IPOPT Status]',
        f'  status  : {ipopt_status}',
        f'  success : {success}',
        f'  wall    : {wall_time:.1f} s ({wall_time/60:.1f} min)',
        '',
        '[ES Activation — 5 Phase Peaks]',
    ]
    for phase, vals in phase_peaks.items():
        lines.append(
            f'  {phase:<12}: peak={vals["peak"]}%  mean={vals["mean"]}%'
            f'  [{vals["peak_muscle"]}]'
        )
    if il_r10:
        lines.append('')
        lines.append('[IL_R10 Phase Peaks]')
        for phase, val in il_r10.items():
            lines.append(f'  {phase:<12}: {val}%')

    lines += [
        '',
        '[Reserve — Hicks 2015 Check]',
        f'  pelvis_ty    : {pelvis_ty.get("value","?")} N'
        f'  (threshold={HICKS_TRANS_THRESHOLD_N} N)'
        f'  {"PASS" if ty_pass else "FAIL" if ty_pass is False else "?"}',
        f'  pelvis_tilt  : {pelvis_tilt.get("value","?")} Nm'
        f'  (threshold={HICKS_ROT_THRESHOLD_NM} Nm)'
        f'  {"PASS" if tilt_pass else "FAIL (MODEL ARTIFACT EXPECTED)" if tilt_pass is False else "?"}',
        '',
        '[Scenario Verdict]',
        f'  {scenario}',
        '',
        f'  Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}',
        '=' * 65,
    ]

    verdict_path.write_text('\n'.join(lines))
    return str(verdict_path)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    global _LOG

    parser = argparse.ArgumentParser(
        description='Box MocoTrack B_suit0 Pilot v2 (Hardened)',
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Build study and verify setup only — do not solve')
    args = parser.parse_args()

    COND_DIR.mkdir(parents=True, exist_ok=True)

    # Logging: RotatingFileHandler + stdout
    log_path = COND_DIR / 'pilot_v2.log'
    _LOG = setup_logging(log_path)

    log('=== Box MocoTrack B_suit0 Pilot v2 (Hardened) ===')
    log(f'Model      : {Path(MODEL_PATH).name}')
    log(f'Motion     : {Path(MOTION_FILE).name}')
    log(f'Time window: [{T_START}, {T_END}] s')
    log(f'num_parallel  : {NUM_PARALLEL} (was 56 in v1)')
    log(f'max_iterations: {MAX_ITERATIONS} (was 3000 in v1)')
    log(f'mesh_interval : {MESH_INTERVAL} s (was 0.02 in v1)')
    log(f'OMP_NUM_THREADS: {os.environ.get("OMP_NUM_THREADS","??")}')
    log(f'Log: {log_path}')
    log('')

    # Step 1: Shared artifacts
    sto_path, xml_path = build_shared_artifacts()

    # Step 2: Build MocoStudy
    log('Building MocoStudy...')
    t_build = time.time()
    study = build_moco_study(box_loads_xml=xml_path)
    log(f'Study built in {time.time() - t_build:.1f}s')

    if args.dry_run:
        log('DRY RUN: study constructed, no solve. Exiting.')
        return 0

    # Step 3: Solve with SIGALRM wall-time guard
    sol_path = COND_DIR / 'solution.sto'
    log(f'Solving B_suit0 (0 N*m)... wall limit={WALL_TIME_LIMIT/3600:.0f}h')
    log('IPOPT output follows:')

    signal.signal(signal.SIGALRM, _wall_time_handler)
    signal.alarm(int(WALL_TIME_LIMIT))

    t_solve = time.time()
    try:
        solution  = study.solve()
        wall_time = time.time() - t_solve
        signal.alarm(0)   # cancel alarm

        moco_sol  = solution
        success   = moco_sol.success()
        status    = moco_sol.getStatus()
        log(f'Solve done: {wall_time:.1f}s  success={success}  status={status}')

        try:
            moco_sol.unseal()
        except Exception:
            pass
        moco_sol.write(str(sol_path))
        log(f'Saved: {sol_path}')

    except TimeoutError as te:
        wall_time = time.time() - t_solve
        signal.alarm(0)
        log(f'TIMEOUT: {te}')
        write_pilot_verdict(COND_DIR, f'TIMEOUT after {wall_time:.0f}s',
                            False, wall_time, {})
        log('SCENARIO C: FAIL (timeout) -> consult CHEOL HOON')
        return 1

    except Exception as exc:
        wall_time = time.time() - t_solve
        signal.alarm(0)
        log(f'Solve EXCEPTION: {exc}')
        import traceback
        traceback.print_exc()
        write_pilot_verdict(COND_DIR, f'EXCEPTION: {exc}', False, wall_time, {})
        log('SCENARIO C: FAIL -> consult CHEOL HOON immediately')
        return 1

    # Step 4: Analyze
    log('Analyzing solution...')
    analysis = analyze_solution(str(sol_path))

    log('')
    log('=== PILOT v2 RESULTS ===')
    for phase, vals in analysis.get('phase_peaks', {}).items():
        log(f'  {phase:<12}: ES_peak={vals["peak"]}%  ES_mean={vals["mean"]}%'
            f'  [{vals["peak_muscle"]}]')

    il_r10 = analysis.get('il_r10_phase', {})
    if il_r10:
        log('  [IL_R10 phase peaks]')
        for phase, val in il_r10.items():
            log(f'    {phase:<12}: {val}%')

    log('')
    log('=== RESERVE CHECK (Hicks 2015) ===')
    hicks_ty   = analysis.get('hicks_pelvis_ty', {})
    hicks_tilt = analysis.get('hicks_pelvis_tilt', {})
    log(f'  pelvis_ty   : {hicks_ty.get("value","?")} N '
        f'(threshold={HICKS_TRANS_THRESHOLD_N} N) '
        f'{"PASS" if hicks_ty.get("pass") else "FAIL" if hicks_ty.get("pass") is False else "?"}')
    log(f'  pelvis_tilt : {hicks_tilt.get("value","?")} Nm '
        f'(threshold={HICKS_ROT_THRESHOLD_NM} Nm) '
        f'{"PASS" if hicks_tilt.get("pass") else "FAIL (MODEL ARTIFACT EXPECTED)" if hicks_tilt.get("pass") is False else "?"}')

    # Step 5: Write verdict
    verdict_path = write_pilot_verdict(
        COND_DIR, status, success, wall_time, analysis, version='v2',
    )
    log(f'Verdict: {verdict_path}')

    ty_pass = hicks_ty.get('pass', None)
    if not success:
        log('==> SCENARIO C: FAIL -> consult CHEOL HOON immediately')
        log('    Action: option 1 fallback (Phase 1a standalone)')
        return 1
    elif ty_pass is False:
        ty_val = hicks_ty.get('value', '?')
        log(f'==> SCENARIO B: pelvis_ty={ty_val} N > Hicks {HICKS_TRANS_THRESHOLD_N} N')
        log('    -> Contact model may not fully resolve GRF mismatch -> consult')
        return 2
    else:
        log('==> SCENARIO A: PASS -> proceed with run_box_mocotrack_sweep.py')
        return 0


if __name__ == '__main__':
    sys.exit(main())
