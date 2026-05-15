"""
Phase 3: Box MocoTrack 5-Conditions Sweep.

Runs 5 conditions (B_suit0 through B_suit200) using MocoTrack + contact.
Must be run AFTER B_suit0 pilot PASS (run_box_mocotrack_pilot.py).

Conditions:
    B_suit0   :   0 N  ->  0.0 N·m   (baseline)
    B_suit50  :  50 N  ->  6.0 N·m
    B_suit100 : 100 N  -> 12.0 N·m
    B_suit150 : 150 N  -> 18.0 N·m
    B_suit200 : 200 N  -> 24.0 N·m   (Phase 1a L20 same torque)

Suit torque is applied via external torque pair (thoracic + pelvis) in
the ExternalLoads XML, identical to Phase 1a approach.

Infrastructure (same as pilot):
    MocoTrack + Hunt-Crossley contact + Hand ExternalForce (no stoop GRF STO)

Fail-fast: if any condition fails IPOPT convergence, sweep STOPS immediately
and user must decide (no automatic retry).

Parallel execution (recommended):
    for n in 50 100 150 200; do
        nohup python run_box_mocotrack_sweep.py --condition B_suit$n \
            > /data/opensim_results/box_mocotrack_v1/B_suit${n}/run.log 2>&1 &
    done

Sequential (this script default):
    python run_box_mocotrack_sweep.py                    # all 5
    python run_box_mocotrack_sweep.py --condition B_suit50  # single

Monitor:
    tail -f /data/opensim_results/box_mocotrack_v1/B_suit*/run.log

Output:
    /data/opensim_results/box_mocotrack_v1/B_suit{N}/solution.sto  (x5)
    /data/opensim_results/box_mocotrack_v1/sweep_summary.json

References:
    Phase 1a suit sweep: F=[0,50,100,150,200]N -> [0,6,12,18,24] Nm, slope=1.164 %/Nm
    Hu 2026 EMG-based range: 14.9-28.6% ES reduction at 20 kg box lift
    Hicks 2015: pelvis_ty <36.8 N, pelvis_tilt <12.9 Nm (MODEL ARTIFACT for tilt)
"""
from __future__ import annotations

import os
import sys
import json
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
    SuitConfig, make_suit_sweep,
    setup_for_box_task,
    add_foot_contact_model,
    generate_box_force_sto,
    add_hand_external_force_xml,
    HICKS_TRANS_THRESHOLD_N,
    HICKS_ROT_THRESHOLD_NM,
    PHASE1A_MOMENT_ARM,
)

# ── Constants ──────────────────────────────────────────────────────────────────

MODEL_PATH  = get_default_model_path()
MOTION_FILE = '/data/stoop_motion/box_motion_v11b.mot'
OUT_ROOT    = Path('/data/opensim_results/box_mocotrack_v1')
SHARED_DIR  = OUT_ROOT / 'shared'

T_START, T_END = 1.0, 4.0
BOX_MASS_KG    = 20.0
GRASP_TIME     = 2.0
GRIP_POINT     = (0.40, 0.75, 0.0)

# Suit ramp profile time constants (same as Phase 1a and v5)
RAMP_T0, RAMP_T1 = 1.0, 2.5   # ramp-up window
HOLD_T0, HOLD_T1 = 2.5, 3.0   # hold window
DOWN_T0, DOWN_T1 = 3.0, 4.0   # ramp-down window

# All 5 conditions (SuitConfig with unit safety)
ALL_CONDITIONS = make_suit_sweep([0, 50, 100, 150, 200])

# Phase boundaries for box motion
PHASES = {
    'Standing':   (1.0, 1.5),
    'Eccentric':  (1.5, 2.0),
    'Grasp':      (2.0, 2.5),
    'Concentric': (2.5, 3.5),
    'Carry':      (3.5, 4.0),
}


def log(msg: str) -> None:
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def suit_alpha(t: float) -> float:
    """
    Suit torque ramp profile for box lifting.

    Profile:
        t < 1.0           : 0 (pre-motion)
        1.0 <= t <= 2.5   : ramp up (cosine, 0 to 1)
        2.5 < t <= 3.0    : hold at 1.0
        3.0 < t <= 4.0    : ramp down (cosine, 1 to 0)
        t > 4.0           : 0
    """
    if t < RAMP_T0:
        return 0.0
    elif t <= RAMP_T1:
        return (1.0 - np.cos(np.pi * (t - RAMP_T0) / (RAMP_T1 - RAMP_T0))) / 2.0
    elif t <= HOLD_T1:
        return 1.0
    elif t <= DOWN_T1:
        return (1.0 + np.cos(np.pi * (t - HOLD_T1) / (DOWN_T1 - HOLD_T1))) / 2.0
    return 0.0


def hand_alpha(t: float) -> float:
    """Hand force ramp: 0 before GRASP_TIME, ramp over 0.5s, hold after."""
    if t < GRASP_TIME:
        return 0.0
    elif t < GRASP_TIME + 0.5:
        return (1.0 - np.cos(np.pi * (t - GRASP_TIME) / 0.5)) / 2.0
    return 1.0


def build_combined_ext_loads(cond_dir: Path, suit_config: SuitConfig) -> tuple[str, str]:
    """
    Build combined ExternalLoads STO + XML for one condition.

    Contains:
        - Hand forces (upward, ramp at grasp time)
        - Suit torque pair (thoracic extension + pelvis flexion)
        - NO foot GRF STO (handled by Hunt-Crossley contact)

    Returns (sto_path, xml_path).
    """
    suit_nm = suit_config.torque_Nm
    force_per_hand = BOX_MASS_KG * 9.81 / 2.0

    # Read time vector from motion
    tbl = osim.TimeSeriesTable(MOTION_FILE)
    times_all = np.array(list(tbl.getIndependentColumn()))
    # Trim to motion window (with small margin)
    mask = (times_all >= T_START - 0.1) & (times_all <= T_END + 0.1)
    times = times_all[mask]
    n = len(times)

    # Columns:
    #   hand forces (6: vx/vy/vz + px/py/pz for each hand)
    #   suit torque pair (thoracic Tz + pelvis Tz)
    # Hand force columns
    hand_cols = [
        'hand_r_force_vx', 'hand_r_force_vy', 'hand_r_force_vz',
        'hand_r_point_px', 'hand_r_point_py', 'hand_r_point_pz',
        'hand_l_force_vx', 'hand_l_force_vy', 'hand_l_force_vz',
        'hand_l_point_px', 'hand_l_point_py', 'hand_l_point_pz',
    ]
    # Suit torque columns (thoracic extension + pelvis counter-torque)
    suit_cols = [
        'thor_T_x', 'thor_T_y', 'thor_T_z',
        'thor_F_vx', 'thor_F_vy', 'thor_F_vz',
        'thor_P_px', 'thor_P_py', 'thor_P_pz',
        'pel_T_x',  'pel_T_y',  'pel_T_z',
        'pel_F_vx',  'pel_F_vy',  'pel_F_vz',
        'pel_P_px',  'pel_P_py',  'pel_P_pz',
    ]
    all_cols = hand_cols + suit_cols
    n_cols = len(all_cols)

    data = np.zeros((n, n_cols))
    gx, gy, gz = GRIP_POINT

    for i, t in enumerate(times):
        f = force_per_hand * hand_alpha(float(t))
        alpha = suit_alpha(float(t))
        Tz = suit_nm * alpha

        # hand_r upward force at grip point (right side, z = -0.13 m)
        data[i, hand_cols.index('hand_r_force_vy')] = f
        data[i, hand_cols.index('hand_r_point_px')] = gx
        data[i, hand_cols.index('hand_r_point_py')] = gy
        data[i, hand_cols.index('hand_r_point_pz')] = -0.13

        # hand_l upward force at grip point (left side, z = +0.13 m)
        data[i, hand_cols.index('hand_l_force_vy')] = f
        data[i, hand_cols.index('hand_l_point_px')] = gx
        data[i, hand_cols.index('hand_l_point_py')] = gy
        data[i, hand_cols.index('hand_l_point_pz')] = +0.13

        # Suit torque: thoracic extension (+Tz) + pelvis flexion (-Tz)
        base = len(hand_cols)
        data[i, base + suit_cols.index('thor_T_z')] = +Tz
        data[i, base + suit_cols.index('pel_T_z')]  = -Tz

    # Write STO
    sto_name = f'ext_loads_{suit_config.name}.sto'
    sto_path = cond_dir / sto_name
    header = (
        f'box_mocotrack_ext_loads  suit={suit_nm:.1f}Nm  hand={force_per_hand:.1f}N\n'
        f'version=1\nnRows={n}\nnColumns={1 + n_cols}\n'
        'inDegrees=no\n\n'
        'Units are S.I. (seconds, metres, Newtons, Newton-metres)\n\nendheader\n'
        'time\t' + '\t'.join(all_cols) + '\n'
    )
    with open(sto_path, 'w') as fh:
        fh.write(header)
        for i in range(n):
            row = [f'{times[i]:.6f}'] + [f'{v:.6f}' for v in data[i]]
            fh.write('\t'.join(row) + '\n')

    # Write XML
    xml_name = f'ext_loads_{suit_config.name}.xml'
    xml_path = cond_dir / xml_name
    xml_content = f"""\
<?xml version="1.0" encoding="UTF-8" ?>
<!-- Box MocoTrack ExternalLoads: {suit_config.name}
     suit={suit_nm:.1f} N·m  hand={force_per_hand:.1f} N  no GRF STO (contact handles it) -->
<OpenSimDocument Version="40000">
  <ExternalLoads name="box_mocotrack_{suit_config.name}">
    <objects>

      <!-- Hand forces: upward reaction to box weight (20 kg) -->
      <!-- ThoracolumbarFB v2.0 uses hand_R / hand_L (capital R/L) -->
      <ExternalForce name="hand_r_box_force">
        <isDisabled>false</isDisabled>
        <applied_to_body>hand_R</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>hand_r_force_v</force_identifier>
        <point_identifier>hand_r_point_p</point_identifier>
        <data_source_name>{sto_name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="hand_l_box_force">
        <isDisabled>false</isDisabled>
        <applied_to_body>hand_L</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>hand_l_force_v</force_identifier>
        <point_identifier>hand_l_point_p</point_identifier>
        <data_source_name>{sto_name}</data_source_name>
      </ExternalForce>

      <!-- Suit torque pair (thoracic extension + pelvis counter-torque) -->
      <!-- torque={suit_nm:.1f} N·m = {suit_config.force_N:.0f} N x {PHASE1A_MOMENT_ARM} m -->
      <ExternalForce name="suit_thoracic">
        <isDisabled>false</isDisabled>
        <applied_to_body>thoracic1</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>thor_F_v</force_identifier>
        <point_identifier>thor_P_p</point_identifier>
        <torque_identifier>thor_T_</torque_identifier>
        <data_source_name>{sto_name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="suit_pelvis">
        <isDisabled>false</isDisabled>
        <applied_to_body>pelvis</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>pel_F_v</force_identifier>
        <point_identifier>pel_P_p</point_identifier>
        <torque_identifier>pel_T_</torque_identifier>
        <data_source_name>{sto_name}</data_source_name>
      </ExternalForce>

    </objects>
    <groups />
    <datafile>{sto_name}</datafile>
  </ExternalLoads>
</OpenSimDocument>
"""
    xml_path.write_text(xml_content)

    # Sanity log
    t_mid_idx = np.argmin(np.abs(times - 2.5))
    hand_vy_r = data[t_mid_idx, hand_cols.index('hand_r_force_vy')]
    hand_vy_l = data[t_mid_idx, hand_cols.index('hand_l_force_vy')]
    suit_tz_th = data[t_mid_idx, len(hand_cols) + suit_cols.index('thor_T_z')]
    log(f'  ExtLoads @t=2.5s: hand_r={hand_vy_r:.1f}N  hand_l={hand_vy_l:.1f}N  '
        f'thor_Tz={suit_tz_th:.1f}Nm (suit={suit_nm:.1f}Nm)')

    return str(sto_path), str(xml_path)


def build_moco_study_for_condition(
    suit_config: SuitConfig,
    ext_loads_xml: str,
    cond_dir: Path,
) -> osim.MocoStudy:
    """
    Build MocoStudy for one sweep condition.

    Pipeline (correct order — contact added before ModelProcessor wrapping):
        1. Load osim.Model directly
        2. add_foot_contact_model (Hunt-Crossley, Falisse 2019)
        3. model.finalizeConnections()
        4. Wrap in ModelProcessor(model)
        5. ModOpAddExternalLoads (hand + suit torque XML)
        6. ModOpAddResiduals (rot=50, trans=300, box task)
        7. ModOpAddReserves (1.0)
        8. Muscle operators (DGF, rigid tendon, no passive)
        9. MocoTrack

    ThoracolumbarFB v2.0 body names: hand_R / hand_L (capital R/L).
    """
    # Step 1-3: Load model + contact
    model = osim.Model(MODEL_PATH)
    model = add_foot_contact_model(model)
    model.finalizeConnections()

    # Step 4-8: ModelProcessor with standard box Moco operators
    mp = osim.ModelProcessor(model)
    mp.append(osim.ModOpAddExternalLoads(ext_loads_xml))
    mp.append(osim.ModOpAddResiduals(50.0, 300.0, 1.0))   # box task
    mp.append(osim.ModOpAddReserves(1.0))                   # Dembia 2020 weak
    mp.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    mp.append(osim.ModOpIgnoreTendonCompliance())
    mp.append(osim.ModOpIgnorePassiveFiberForcesDGF())

    # Step 9: MocoTrack
    track = osim.MocoTrack()
    track.setName(f'box_mocotrack_{suit_config.name}')
    track.setModel(mp)

    ref = osim.TableProcessor(MOTION_FILE)
    ref.append(osim.TabOpConvertDegreesToRadians())
    ref.append(osim.TabOpUseAbsoluteStateNames())
    track.setStatesReference(ref)
    track.set_allow_unused_references(True)
    track.set_initial_time(T_START)
    track.set_final_time(T_END)
    track.set_mesh_interval(0.02)
    track.set_states_global_tracking_weight(1.0)
    track.set_control_effort_weight(1.0)

    study = track.initialize()

    problem = study.updProblem()
    try:
        effort_goal = osim.MocoControlGoal.safeDownCast(
            problem.updGoal('control_effort')
        )
        if effort_goal is not None:
            effort_goal.setWeight(0.001)
    except Exception:
        pass

    solver = osim.MocoCasADiSolver.safeDownCast(study.updSolver())
    solver.set_optim_convergence_tolerance(1e-3)
    solver.set_optim_constraint_tolerance(1e-3)
    solver.set_optim_max_iterations(3000)

    return study


def quick_reserve_check(sol_path: str) -> dict:
    """Extract key reserve values from solution STO."""
    if not os.path.isfile(sol_path):
        return {}
    try:
        tbl = osim.TimeSeriesTable(sol_path)
        labels = list(tbl.getColumnLabels())
        n_rows = tbl.getNumRows()
        data = np.zeros((n_rows, len(labels)))
        for i in range(n_rows):
            row = tbl.getRowAtIndex(i)
            for j in range(len(labels)):
                data[i, j] = row[j]

        res = {}
        key_reserves = ['pelvis_ty', 'pelvis_tilt', 'pelvis_tx',
                         'hip_flexion_r', 'hip_flexion_l']
        for nm in key_reserves:
            for j, lab in enumerate(labels):
                if nm in lab and ('reserve' in lab.lower() or 'residual' in lab.lower()):
                    res[nm] = round(float(np.abs(data[:, j]).max()), 2)
                    break
        return res
    except Exception as exc:
        return {'error': str(exc)}


def run_condition(suit_config: SuitConfig) -> dict:
    """Run one sweep condition and return result dict."""
    label = suit_config.name
    cond_dir = OUT_ROOT / label
    cond_dir.mkdir(parents=True, exist_ok=True)

    log(f'')
    log(f'--- Condition: {label}  '
        f'suit={suit_config.force_N:.0f} N -> {suit_config.torque_Nm:.1f} N·m ---')

    # Build external loads
    sto_path, xml_path = build_combined_ext_loads(cond_dir, suit_config)

    # Build study
    log(f'Building MocoStudy...')
    study = build_moco_study_for_condition(suit_config, xml_path, cond_dir)

    # Solve
    sol_path = cond_dir / 'solution.sto'
    log(f'Solving... mesh=0.02s, t=[{T_START},{T_END}], suit={suit_config.torque_Nm:.1f}Nm')
    t0 = time.time()

    success, status, wall_time = False, 'not_run', 0.0
    try:
        solution = study.solve()
        wall_time = time.time() - t0
        success = solution.success()
        status = solution.getStatus()
        log(f'Solve done: {wall_time:.1f}s  success={success}  status={status}')

        try:
            solution.unseal()
        except Exception:
            pass
        solution.write(str(sol_path))
        log(f'Saved: {sol_path}')

    except Exception as exc:
        wall_time = time.time() - t0
        log(f'Solve EXCEPTION after {wall_time:.1f}s: {exc}')
        success = False
        status = f'EXCEPTION: {exc}'

    # Quick reserve check
    reserves = quick_reserve_check(str(sol_path))
    if reserves and 'error' not in reserves:
        log(f'  pelvis_ty={reserves.get("pelvis_ty","?")} N  '
            f'pelvis_tilt={reserves.get("pelvis_tilt","?")} Nm')
        ty = reserves.get('pelvis_ty', None)
        if ty is not None:
            hicks_pass = ty <= HICKS_TRANS_THRESHOLD_N
            log(f'  Hicks pelvis_ty: {"PASS" if hicks_pass else "FAIL"} '
                f'(threshold={HICKS_TRANS_THRESHOLD_N} N)')

    return {
        'label':        label,
        'force_N':      suit_config.force_N,
        'torque_Nm':    suit_config.torque_Nm,
        'success':      success,
        'status':       status,
        'wall_time_s':  round(wall_time, 1),
        'sol_path':     str(sol_path),
        'reserves':     reserves,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Box MocoTrack 5-Conditions Sweep (Phase 3)',
    )
    parser.add_argument(
        '--condition', type=str, default=None,
        help='Run single condition (e.g. B_suit0, B_suit50). Default: all 5.',
    )
    args = parser.parse_args()

    # Select conditions
    if args.condition:
        conds = [c for c in ALL_CONDITIONS if c.name == args.condition]
        if not conds:
            valid = [c.name for c in ALL_CONDITIONS]
            log(f'Unknown condition: {args.condition}. Valid: {valid}')
            return 2
    else:
        conds = ALL_CONDITIONS

    log('=== Box MocoTrack 5-Conditions Sweep ===')
    log(f'Model: {Path(MODEL_PATH).name}')
    log(f'Motion: {Path(MOTION_FILE).name}')
    log(f'Infrastructure: MocoTrack + Hunt-Crossley contact (no stoop GRF STO)')
    log(f'Time window: [{T_START}, {T_END}] s | BOX_MASS={BOX_MASS_KG} kg')
    log(f'Conditions ({len(conds)}):')
    for c in conds:
        log(f'  {c.name}: {c.force_N:.0f} N -> {c.torque_Nm:.1f} N·m')
    log('')

    results = []
    t_total = time.time()

    for suit_config in conds:
        try:
            r = run_condition(suit_config)
            results.append(r)
        except Exception as exc:
            log(f'FATAL in {suit_config.name}: {exc}')
            import traceback
            traceback.print_exc()
            results.append({
                'label': suit_config.name,
                'force_N': suit_config.force_N,
                'torque_Nm': suit_config.torque_Nm,
                'success': False,
                'status': f'EXCEPTION: {exc}',
                'wall_time_s': 0,
                'sol_path': 'FAILED',
                'reserves': {},
            })

        # Fail-fast: stop if condition failed
        if results and not results[-1]['success']:
            log(f'')
            log(f'==> STOPPED: {results[-1]["label"]} FAILED.')
            log(f'    Status: {results[-1]["status"]}')
            log(f'    Action: consult CHEOL HOON before proceeding.')
            log(f'    Sited protocol: no automatic retry, option 1 fallback if needed.')
            break

    total_time = time.time() - t_total

    # Summary
    log('')
    log('=' * 65)
    log('SWEEP SUMMARY')
    log('=' * 65)
    log(f'{"Condition":<12} {"Force(N)":<10} {"Torque(Nm)":<12} '
        f'{"Success":<10} {"Wall(s)":<10} {"Status"}')
    for r in results:
        log(f'{r["label"]:<12} {r["force_N"]:<10.0f} {r["torque_Nm"]:<12.1f} '
            f'{str(r["success"]):<10} {r["wall_time_s"]:<10.1f} {r["status"]}')

    log(f'')
    log(f'Total wall time: {total_time:.1f}s ({total_time/60:.1f} min)')

    # Pilot compatibility check (compare B_suit0 reserve to pilot)
    suit0 = next((r for r in results if r['label'] == 'B_suit0'), None)
    if suit0 and suit0['success']:
        ty = suit0.get('reserves', {}).get('pelvis_ty', None)
        if ty is not None:
            log(f'')
            log(f'[Pilot compatibility check]')
            log(f'  B_suit0 pelvis_ty = {ty} N (Hicks threshold = {HICKS_TRANS_THRESHOLD_N} N)')
            if ty <= HICKS_TRANS_THRESHOLD_N:
                log(f'  -> PASS: contact model working correctly')
            elif ty < 100:
                log(f'  -> PARTIAL: improved over stoop GRF STO approach (3570 N)')
            else:
                log(f'  -> REVIEW: pelvis_ty still elevated, consult')

    # Save summary JSON
    summary_path = OUT_ROOT / 'sweep_summary.json'
    with open(summary_path, 'w') as fh:
        json.dump(results, fh, indent=2)
    log(f'Summary saved: {summary_path}')

    # Return code
    all_success = all(r['success'] for r in results)
    return 0 if all_success else 1


if __name__ == '__main__':
    sys.exit(main())
