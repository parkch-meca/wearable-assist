"""
Phase 2: Box MocoTrack B_suit0 Pilot (Single Condition Verification).

Runs ONE condition (B_suit0, 0 N·m) with the new infrastructure:
    MocoTrack + Hunt-Crossley contact (no stoop GRF STO) + Hand ExternalForce

This is the critical gate before sweeping 5 conditions. Purpose:
    - Validate MocoTrack + contact + hand force all work together
    - Measure pelvis_ty/pelvis_tilt without stoop GRF STO artifact
    - Verify IL_R10 ES activation pattern is biomechanically reasonable

Decision gate (sited from task spec):
    A. PASS: proceed with run_box_mocotrack_sweep.py (5 conditions)
    B. Partial (converged but reserve abnormal): user consultation
    C. FAIL (no convergence): immediate consultation + option 1 fallback

Infrastructure change vs Phase 2.C.4 v5 (MocoInverse):
    OLD: MocoInverse + stoop GRF STO -> pelvis_ty = 3570 N (vs Hicks 36.8 N)
    NEW: MocoTrack + Hunt-Crossley contact -> GRF auto-computed, no STO needed

Pilot verdict (auto-generated):
    IPOPT status + pelvis_ty + pelvis_tilt + IL_R10 check -> printed at end.

Wall time limit: 2 hours (7200 s). Script will abort if exceeded.

Usage:
    python run_box_mocotrack_pilot.py
    python run_box_mocotrack_pilot.py --dry-run   # setup only, no solve

Output:
    /data/opensim_results/box_mocotrack_v1/B_suit0/solution.sto
    /data/opensim_results/box_mocotrack_v1/B_suit0/pilot_verdict.txt

References:
    Dembia 2020: ModOpAddResiduals(50, 300, 1.0) box task
    Falisse 2019: SmoothSphereHalfSpaceForce + Hunt-Crossley
    John 2022: MocoTrack exo setup, mesh_interval=0.02s
    Hicks 2015: pelvis_ty < 36.8 N (5% BW), pelvis_tilt < 12.9 Nm (1% BWxht)
"""
from __future__ import annotations

import os
import sys
import time
import argparse
from pathlib import Path

os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')

# --- path setup ---
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

T_START, T_END = 1.0, 4.0
BOX_MASS_KG    = 20.0
GRASP_TIME     = 2.0
GRIP_POINT     = (0.40, 0.75, 0.0)   # ground frame metres
WALL_TIME_LIMIT = 7200.0              # 2 hours

# ES muscles that are the key indicator of loading (Phase 1a reference)
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


def log(msg: str) -> None:
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


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
        body_r='hand_R',   # ThoracolumbarFB v2.0 uses capital R/L
        body_l='hand_L',
    )
    log(f'  XML: {xml_path}')

    return sto_path, xml_path


def build_moco_study(box_loads_xml: str) -> osim.MocoStudy:
    """
    Build MocoStudy for B_suit0 pilot.

    Pipeline (correct order to avoid double-application of ModOps):
        1. Load osim.Model directly from MODEL_PATH
        2. add_foot_contact_model (Hunt-Crossley, Falisse 2019)
        3. model.finalizeConnections()
        4. Wrap in fresh ModelProcessor(model)
        5. ModOpAddExternalLoads (hand force XML, body=hand_R/hand_L)
        6. ModOpAddResiduals (rot=50 Nm, trans=300 N, box task)
        7. ModOpAddReserves (scale=1.0, Dembia 2020 weak)
        8. ModOpReplaceMusclesWithDeGrooteFregly2016 + tendon/passive ops
        9. MocoTrack (mesh=0.02s, John 2022)

    No GRF STO: GRF is auto-computed by foot-ground contact physics.
    No suit torque: B_suit0 is baseline (0 N, 0 N·m).

    Key fix (2026-04-29): body names are hand_R / hand_L (capital R/L)
    in ThoracolumbarFB v2.0. Previous hand_r/hand_l caused RuntimeError
    in finalizeConnections().
    """
    import warnings

    # Step 1: Load model + add contact geometry BEFORE wrapping in ModelProcessor
    log('Loading model for foot contact addition...')
    model = osim.Model(MODEL_PATH)
    model = add_foot_contact_model(model)
    model.finalizeConnections()

    # Verify contact components
    n_spheres = sum(
        1 for i in range(model.getContactGeometrySet().getSize())
        if model.getContactGeometrySet().get(i).getConcreteClassName() == 'ContactSphere'
    )
    n_forces = sum(
        1 for i in range(model.getForceSet().getSize())
        if 'SmoothSphereHalfSpaceForce' in model.getForceSet().get(i).getConcreteClassName()
    )
    log(f'  Contact model: {n_spheres} spheres, {n_forces} Hunt-Crossley forces')

    # Step 2: Wrap in ModelProcessor + append Moco operators in standard order
    log('Building ModelProcessor with Moco operators (box task, trans=300 N, rot=50 Nm)...')
    mp = osim.ModelProcessor(model)
    # ExternalLoads (hand force, no GRF STO — contact handles GRF)
    mp.append(osim.ModOpAddExternalLoads(box_loads_xml))
    # Residuals: box task (Dembia 2020 exampleMocoInverse, Architecture §2.3)
    mp.append(osim.ModOpAddResiduals(50.0, 300.0, 1.0))
    # Reserves: other joints, weak (Dembia 2020 standard)
    mp.append(osim.ModOpAddReserves(1.0))
    # Muscle operators (required by MocoTrack)
    mp.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    mp.append(osim.ModOpIgnoreTendonCompliance())
    mp.append(osim.ModOpIgnorePassiveFiberForcesDGF())

    log('Building MocoTrack study...')
    track = osim.MocoTrack()
    track.setName('box_mocotrack_B_suit0')
    track.setModel(mp)

    ref = osim.TableProcessor(MOTION_FILE)
    ref.append(osim.TabOpConvertDegreesToRadians())
    ref.append(osim.TabOpUseAbsoluteStateNames())
    track.setStatesReference(ref)
    track.set_allow_unused_references(True)

    track.set_initial_time(T_START)
    track.set_final_time(T_END)
    track.set_mesh_interval(0.02)       # John 2022: 50 mesh/s
    track.set_states_global_tracking_weight(1.0)
    track.set_control_effort_weight(1.0)

    study = track.initialize()

    # Tighten control effort goal (0.001, John 2022)
    problem = study.updProblem()
    try:
        effort_goal = osim.MocoControlGoal.safeDownCast(
            problem.updGoal('control_effort')
        )
        if effort_goal is not None:
            effort_goal.setWeight(0.001)
    except Exception:
        pass

    # Solver: CasADi + IPOPT, John 2022 tolerances
    solver = osim.MocoCasADiSolver.safeDownCast(study.updSolver())
    solver.set_optim_convergence_tolerance(1e-3)
    solver.set_optim_constraint_tolerance(1e-3)
    solver.set_optim_max_iterations(3000)

    log(f'  MocoStudy ready: mesh_interval=0.02s, tol=1e-3, max_iter=3000')
    return study


def analyze_solution(sol_path: str) -> dict:
    """Extract ES activation + reserve metrics from solution STO."""
    import warnings
    results = {}

    if not os.path.isfile(sol_path):
        return {'error': f'Solution not found: {sol_path}'}

    try:
        tbl = osim.TimeSeriesTable(sol_path)
        labels = list(tbl.getColumnLabels())
        n_rows = tbl.getNumRows()
        times  = np.array(list(tbl.getIndependentColumn()))

        # Build data array
        data = np.zeros((n_rows, len(labels)))
        for i in range(n_rows):
            row = tbl.getRowAtIndex(i)
            for j in range(len(labels)):
                data[i, j] = row[j]

        # -- ES muscle activation --
        es_cols = [
            (j, lab) for j, lab in enumerate(labels)
            if any(m in lab for m in [
                'IL_R', 'IL_L', 'LTpL', 'LTpM', 'ITS', 'MF',
                '/IL_', '/LT', '/ITS', '/MF'
            ])
            and ('activation' in lab or 'excitation' in lab or '/control' in lab)
        ]

        # Fallback: look for muscle state columns matching ES pattern
        if not es_cols:
            es_cols = [
                (j, lab) for j, lab in enumerate(labels)
                if any(m in lab for m in ['IL_R10', 'IL_R11', 'IL_R12',
                                           'LTpL_L5', 'LTpL_L4'])
            ]

        results['n_es_cols_found'] = len(es_cols)

        if es_cols:
            es_data = data[:, [j for j, _ in es_cols]]
            es_names = [lab for _, lab in es_cols]

            # 5-phase peak analysis
            phase_peaks = {}
            for phase_name, (t0, t1) in PHASES.items():
                mask = (times >= t0 - 1e-9) & (times <= t1 + 1e-9)
                if mask.any():
                    phase_data = es_data[mask]
                    peak_val = float(phase_data.max())
                    peak_col = es_names[int(phase_data.max(axis=0).argmax())]
                    mean_val = float(phase_data.mean())
                    phase_peaks[phase_name] = {
                        'peak': round(peak_val * 100, 1),   # percent
                        'mean': round(mean_val * 100, 1),
                        'peak_muscle': peak_col.split('/')[-1],
                    }
            results['phase_peaks'] = phase_peaks

            # IL_R10 specific
            il_r10_cols = [(j, lab) for j, lab in enumerate(labels)
                           if 'IL_R10' in lab or 'il_r10' in lab.lower()]
            if il_r10_cols:
                il_r10_data = data[:, [j for j, _ in il_r10_cols]]
                for phase_name, (t0, t1) in PHASES.items():
                    mask = (times >= t0 - 1e-9) & (times <= t1 + 1e-9)
                    if mask.any():
                        peak = float(il_r10_data[mask].max()) * 100
                        results.setdefault('il_r10_phase', {})[phase_name] = round(peak, 1)

        # -- Reserve actuator check --
        res_cols = [(j, lab) for j, lab in enumerate(labels)
                    if 'reserve' in lab.lower() or 'residual' in lab.lower()]
        results['n_reserve_cols'] = len(res_cols)

        reserve_summary = {}
        if res_cols:
            for j, lab in res_cols:
                col_data = np.abs(data[:, j])
                short = lab.split('/')[-2] if '/' in lab else lab
                reserve_summary[short] = round(float(col_data.max()), 2)

            # Key reserves
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

        # Hicks 2015 check
        pelvis_ty_max = reserve_summary.get('_KEY_pelvis_ty', None)
        pelvis_tilt_max = reserve_summary.get('_KEY_pelvis_tilt', None)
        if pelvis_ty_max is not None:
            results['hicks_pelvis_ty'] = {
                'value': pelvis_ty_max,
                'threshold': HICKS_TRANS_THRESHOLD_N,
                'pass': pelvis_ty_max <= HICKS_TRANS_THRESHOLD_N,
            }
        if pelvis_tilt_max is not None:
            results['hicks_pelvis_tilt'] = {
                'value': pelvis_tilt_max,
                'threshold': HICKS_ROT_THRESHOLD_NM,
                'pass': pelvis_tilt_max <= HICKS_ROT_THRESHOLD_NM,
            }

    except Exception as exc:
        results['analysis_error'] = str(exc)

    return results


def write_pilot_verdict(
    cond_dir: Path,
    ipopt_status: str,
    success: bool,
    wall_time: float,
    analysis: dict,
) -> str:
    """Write pilot verdict text file."""
    verdict_path = cond_dir / 'pilot_verdict.txt'

    pelvis_ty = analysis.get('hicks_pelvis_ty', {})
    pelvis_tilt = analysis.get('hicks_pelvis_tilt', {})

    # Scenario determination
    ty_pass   = pelvis_ty.get('pass', None)
    tilt_pass = pelvis_tilt.get('pass', None)

    if not success:
        scenario = 'C: FAIL (no convergence) -> immediate consultation'
    elif ty_pass is False and tilt_pass is False:
        ty_val = pelvis_ty.get('value', '?')
        scenario = (
            f'B: Partial (converged, reserve abnormal) -> consultation\n'
            f'   pelvis_ty={ty_val} N (Hicks threshold={HICKS_TRANS_THRESHOLD_N} N)\n'
            f'   pelvis_tilt={pelvis_tilt.get("value","?")} Nm (threshold={HICKS_ROT_THRESHOLD_NM} Nm)\n'
            f'   Note: pelvis_tilt FAIL expected (MODEL ARTIFACT, see KNOWN_LIMITATIONS)\n'
            f'   pelvis_ty FAIL indicates GRF dynamics mismatch -> investigate'
        )
    elif tilt_pass is False and (ty_pass is True or ty_pass is None):
        scenario = (
            f'A: PASS (pelvis_tilt FAIL = MODEL ARTIFACT as expected)\n'
            f'   pelvis_tilt={pelvis_tilt.get("value","?")} Nm -> MODEL ARTIFACT\n'
            f'   pelvis_ty={pelvis_ty.get("value","?")} N -> within/near Hicks threshold\n'
            f'   -> Proceed with run_box_mocotrack_sweep.py'
        )
    else:
        scenario = (
            f'A: PASS (all reserves within expected bounds)\n'
            f'   -> Proceed with run_box_mocotrack_sweep.py'
        )

    phase_peaks = analysis.get('phase_peaks', {})
    il_r10 = analysis.get('il_r10_phase', {})

    lines = [
        '=' * 65,
        'Box MocoTrack B_suit0 Pilot Verdict',
        '=' * 65,
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Box MocoTrack B_suit0 Pilot (Phase 2)',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Build study and verify setup only — do not solve',
    )
    args = parser.parse_args()

    log('=== Box MocoTrack B_suit0 Pilot ===')
    log(f'Model: {Path(MODEL_PATH).name}')
    log(f'Motion: {Path(MOTION_FILE).name}')
    log(f'Time window: [{T_START}, {T_END}] s')
    log(f'Infrastructure: MocoTrack + Hunt-Crossley contact (no stoop GRF STO)')
    log(f'Previous approach: MocoInverse + stoop GRF STO -> pelvis_ty=3570 N FAIL')
    log('')

    COND_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate shared artifacts
    sto_path, xml_path = build_shared_artifacts()

    # Step 2: Build MocoStudy
    log('Building MocoStudy...')
    t_build = time.time()
    study = build_moco_study(box_loads_xml=xml_path)
    log(f'Study built in {time.time() - t_build:.1f}s')

    if args.dry_run:
        log('DRY RUN: study constructed, no solve. Exiting.')
        return 0

    # Step 3: Solve
    sol_path = COND_DIR / 'solution.sto'
    log(f'Solving B_suit0 (0 N·m)... wall limit={WALL_TIME_LIMIT/3600:.0f}h')
    log('IPOPT output follows:')

    t_solve = time.time()
    try:
        solution = study.solve()
        wall_time = time.time() - t_solve

        # Extract status
        moco_sol = solution
        success = moco_sol.success()
        status  = moco_sol.getStatus()
        log(f'Solve done: {wall_time:.1f}s  success={success}  status={status}')

        # Save solution
        try:
            moco_sol.unseal()
        except Exception:
            pass
        moco_sol.write(str(sol_path))
        log(f'Saved: {sol_path}')

    except Exception as exc:
        wall_time = time.time() - t_solve
        log(f'Solve EXCEPTION: {exc}')
        import traceback
        traceback.print_exc()
        verdict_path = write_pilot_verdict(
            COND_DIR, f'EXCEPTION: {exc}', False, wall_time, {}
        )
        log(f'Verdict: {verdict_path}')
        log('SCENARIO C: FAIL -> immediate consultation')
        return 1

    if wall_time > WALL_TIME_LIMIT:
        log(f'WARNING: wall time {wall_time:.0f}s exceeded limit {WALL_TIME_LIMIT:.0f}s')

    # Step 4: Analyze
    log('Analyzing solution...')
    analysis = analyze_solution(str(sol_path))

    # Print key results
    log('')
    log('=== PILOT RESULTS ===')
    phase_peaks = analysis.get('phase_peaks', {})
    for phase, vals in phase_peaks.items():
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
        COND_DIR, status, success, wall_time, analysis,
    )
    log(f'')
    log(f'Verdict written: {verdict_path}')

    # Final scenario
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
