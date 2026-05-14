"""
Phase 1a Reproduction — 5-Condition Suit Sweep (Week 3, Step 2).

Runs MocoInverse for all 5 suit conditions:
    B_suit0   : F=0 N   -> T=0 N·m
    B_suit50  : F=50 N  -> T=6 N·m
    B_suit100 : F=100 N -> T=12 N·m
    B_suit150 : F=150 N -> T=18 N·m
    B_suit200 : F=200 N -> T=24 N·m

Uses base.make_suit_sweep() + base.build_model_processor().
B_noload (F=0) is used as the baseline for dose-response computation.

Expected results (from existing Phase 1a sweep memory):
    ES_mean Hold slope    : 1.164 %/N·m  (R²=1.0000)
    ES_mean Con slope     : 1.186 %/N·m
    Reduction @ 24 N·m   : ~28 %
    Hu 2026 range         : 14.9-28.6 % (matched at 24 N·m)

Usage:
    /home/sysop/miniconda3/envs/opensim/bin/python run_phase1a_reproduction_sweep.py

Output:
    /data/opensim_results/phase1a_reproduction/B_suit{0,50,100,150,200}/solution.sto
    /data/opensim_results/phase1a_reproduction/sweep_report.md
"""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
sys.path.insert(0, '/data/wearable-assist/opensim_analysis/thoracolumbar_fb')

import numpy as np
import opensim as osim
from base import make_suit_sweep, build_model_processor, SuitConfig

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SRC_MODEL = (
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
    'MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim'
)
MOT = '/data/stoop_motion/stoop_synthetic_v5.mot'
GRF_STO = '/data/stoop_motion/stoop_grf_v5.sto'
PHASE1A_LIST = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/phase1a_muscle_list.txt'
OUT_ROOT = Path('/data/opensim_results/phase1a_reproduction')

T_START, T_END = 0.0, 5.0
MESH = 50
RESERVE_OPTF = 10.0
MOMENT_ARM = 0.12

# 5-phase definitions (verified)
PHASES = [
    ('Standing',   0.0, 0.5),
    ('Eccentric',  0.5, 1.5),
    ('Hold',       1.5, 2.5),
    ('Concentric', 2.5, 4.0),
    ('Recovery',   4.0, 5.0),
]

# 6-muscle ES subset for mean
ES6 = ['IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'IL_R11_l', 'LTpL_L5_r', 'LTpL_L5_l']

GRF_COLS = [
    'ground_force_R_vx','ground_force_R_vy','ground_force_R_vz',
    'ground_force_R_px','ground_force_R_py','ground_force_R_pz',
    'ground_torque_R_x','ground_torque_R_y','ground_torque_R_z',
    'ground_force_L_vx','ground_force_L_vy','ground_force_L_vz',
    'ground_force_L_px','ground_force_L_py','ground_force_L_pz',
    'ground_torque_L_x','ground_torque_L_y','ground_torque_L_z',
]
SUIT_COLS = [
    'thor_F_vx','thor_F_vy','thor_F_vz','thor_T_x','thor_T_y','thor_T_z',
    'thor_P_px','thor_P_py','thor_P_pz',
    'pel_F_vx','pel_F_vy','pel_F_vz','pel_T_x','pel_T_y','pel_T_z',
    'pel_P_px','pel_P_py','pel_P_pz',
]


def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def alpha_v5(t):
    if t < 0.5:     return 0.0
    if t <= 2.5:    return (1.0 - np.cos(np.pi * (t - 0.5) / 2.0)) / 2.0
    if t <= 3.0:    return 1.0
    if t <= 5.0:    return (1.0 + np.cos(np.pi * (t - 3.0) / 2.0)) / 2.0
    return 0.0


def load_phase1a_set():
    names = set()
    with open(PHASE1A_LIST) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            names.add(s)
    return names


def prepare_model(out_path, keep):
    import xml.etree.ElementTree as ET
    tree = ET.parse(SRC_MODEL)
    root = tree.getroot()
    MUSCLE_TYPES = {
        'Millard2012EquilibriumMuscle', 'Thelen2003Muscle',
        'DeGrooteFregly2016Muscle', 'ActivationFiberLengthMuscle',
        'Muscle', 'SimpleMuscle', 'RigidTendonMuscle',
    }
    for fs in root.iter('ForceSet'):
        obj = fs.find('objects')
        if obj is None:
            continue
        for child in list(obj):
            name = child.get('name')
            if name is None:
                continue
            if child.tag in MUSCLE_TYPES or 'Muscle' in child.tag:
                if name not in keep:
                    obj.remove(child)
    tree.write(str(out_path), encoding='utf-8', xml_declaration=True)


def prepare_reference(out_path):
    tbl = osim.TimeSeriesTable(MOT)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    m = osim.Model(SRC_MODEL)
    m.initSystem()
    cs = m.getCoordinateSet()
    is_rot = [cs.contains(L) and cs.get(L).getMotionType() == 1 for L in labels]
    mask = (times >= T_START - 1e-9) & (times <= T_END + 1e-9)
    keep_idx = np.where(mask)[0]
    n = len(keep_idx)
    header = (
        f"stoop_v5_p1a_sweep\nversion=1\nnRows={n}\n"
        f"nColumns={1+len(labels)}\ninDegrees=no\n\n"
        "Units are S.I. units.\n\nendheader\n"
        "time\t" + "\t".join(labels) + "\n"
    )
    with open(out_path, 'w') as f:
        f.write(header)
        for i in keep_idx:
            row = tbl.getRowAtIndex(int(i))
            vals = [f"{times[i]:.6f}"]
            for j, lab in enumerate(labels):
                v = row[j]
                if is_rot[j]:
                    v = np.radians(v)
                vals.append(f"{v:.6f}")
            f.write("\t".join(vals) + "\n")


def write_extloads(cond_dir, torque_nm):
    out_mot = cond_dir / 'ext_grf_suit.mot'
    out_xml = cond_dir / 'ext_grf_suit.xml'
    tbl = osim.TimeSeriesTable(GRF_STO)
    times = np.array(list(tbl.getIndependentColumn()))
    col_labels = list(tbl.getColumnLabels())
    n = tbl.getNumRows()

    grf = np.zeros((n, len(GRF_COLS)))
    for i in range(n):
        r = tbl.getRowAtIndex(i)
        for j, c in enumerate(GRF_COLS):
            grf[i, j] = r[col_labels.index(c)]

    suit = np.zeros((n, len(SUIT_COLS)))
    if torque_nm > 0:
        i_thor = SUIT_COLS.index('thor_T_z')
        i_pel = SUIT_COLS.index('pel_T_z')
        for i, t in enumerate(times):
            Tz = torque_nm * alpha_v5(float(t))
            suit[i, i_thor] = +Tz
            suit[i, i_pel] = -Tz

    all_cols = GRF_COLS + SUIT_COLS
    data = np.hstack([grf, suit])
    header = (
        f"phase1a_sweep_grf  T={torque_nm}Nm\nversion=1\nnRows={n}\n"
        f"nColumns={1+len(all_cols)}\ninDegrees=no\n\n"
        "Units are S.I. units (second, meters, Newtons, ...)\n\nendheader\n"
        "time\t" + "\t".join(all_cols) + "\n"
    )
    with open(out_mot, 'w') as f:
        f.write(header)
        for i, t in enumerate(times):
            f.write("\t".join([f"{t:.6f}"] + [f"{v:.6f}" for v in data[i]]) + "\n")

    xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
  <ExternalLoads name="phase1a_sweep_grf_suit">
    <objects>
      <ExternalForce name="grf_R">
        <isDisabled>false</isDisabled>
        <applied_to_body>calcn_r</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>ground_force_R_v</force_identifier>
        <point_identifier>ground_force_R_p</point_identifier>
        <torque_identifier>ground_torque_R_</torque_identifier>
        <data_source_name>{out_mot.name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="grf_L">
        <isDisabled>false</isDisabled>
        <applied_to_body>calcn_l</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>ground_force_L_v</force_identifier>
        <point_identifier>ground_force_L_p</point_identifier>
        <torque_identifier>ground_torque_L_</torque_identifier>
        <data_source_name>{out_mot.name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="suit_thoracic">
        <isDisabled>false</isDisabled>
        <applied_to_body>thoracic1</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>thor_F_v</force_identifier>
        <point_identifier>thor_P_p</point_identifier>
        <torque_identifier>thor_T_</torque_identifier>
        <data_source_name>{out_mot.name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="suit_pelvis">
        <isDisabled>false</isDisabled>
        <applied_to_body>pelvis</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>pel_F_v</force_identifier>
        <point_identifier>pel_P_p</point_identifier>
        <torque_identifier>pel_T_</torque_identifier>
        <data_source_name>{out_mot.name}</data_source_name>
      </ExternalForce>
    </objects>
    <groups />
    <datafile>{out_mot.name}</datafile>
  </ExternalLoads>
</OpenSimDocument>
"""
    out_xml.write_text(xml)
    return str(out_mot), str(out_xml)


def solve_condition(suit_cfg, shared_model, shared_ref):
    """Solve one sweep condition via MocoInverse + base ModelProcessor."""
    cond_name = suit_cfg.name
    torque_nm = suit_cfg.torque_Nm
    cond_dir = OUT_ROOT / cond_name
    cond_dir.mkdir(parents=True, exist_ok=True)
    sol_path = cond_dir / 'solution.sto'

    if sol_path.exists():
        log(f'[{cond_name}] solution.sto exists, skipping')
        return str(sol_path), True, 0.0

    _, ext_xml = write_extloads(cond_dir, torque_nm)
    log(f'[{cond_name}] ext_loads written (T={torque_nm:.1f} N·m)')

    # base.build_model_processor (Architecture §2.3 stoop: rot=20, trans=50)
    mp = build_model_processor(
        model_path=str(shared_model),
        task_type='stoop',
        external_loads_xml=ext_xml,
    )
    mp.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    mp.append(osim.ModOpIgnoreTendonCompliance())
    mp.append(osim.ModOpIgnorePassiveFiberForcesDGF())

    inverse = osim.MocoInverse()
    inverse.setName(f'repro_{cond_name}')
    inverse.setModel(mp)
    inverse.setKinematics(osim.TableProcessor(str(shared_ref)))
    inverse.set_initial_time(T_START)
    inverse.set_final_time(T_END)
    inverse.set_mesh_interval((T_END - T_START) / MESH)
    inverse.set_kinematics_allow_extra_columns(True)

    t0 = time.time()
    log(f'[{cond_name}] Solving...')
    sol = inverse.solve()
    elapsed = time.time() - t0
    moco_sol = sol.getMocoSolution()
    success = moco_sol.success()
    log(f'[{cond_name}] Solve: success={success}  time={elapsed:.1f}s')

    try:
        moco_sol.unseal()
    except Exception:
        pass
    moco_sol.write(str(sol_path))
    log(f'[{cond_name}] Saved {sol_path}')
    return str(sol_path), success, elapsed


def load_act(tbl, name):
    labels = list(tbl.getColumnLabels())
    for i, L in enumerate(labels):
        if L.endswith(f'/{name}/activation'):
            n = tbl.getNumRows()
            return np.array([tbl.getRowAtIndex(k)[i] for k in range(n)]) * 100
    return None


def load_phase_means(sol_path):
    """Load ES6 activation means per phase."""
    tbl = osim.TimeSeriesTable(sol_path)
    times = np.array(list(tbl.getIndependentColumn()))
    acts = {n: load_act(tbl, n) for n in ES6}
    acts = {k: v for k, v in acts.items() if v is not None}

    if not acts:
        return None

    arr = np.stack(list(acts.values()), axis=1)
    es_mean = arr.mean(axis=1)

    result = {'times': times}
    for pname, ts, te in PHASES:
        mask = (times >= ts) & (times <= te)
        if mask.sum() > 0:
            result[f'{pname}_mean'] = float(es_mean[mask].mean())
            result[f'{pname}_peak'] = float(es_mean[mask].max())

    # IL_R10_r individual
    if 'IL_R10_r' in acts:
        il = acts['IL_R10_r']
        result['IL_R10_r_peak'] = float(il.max())
        for pname, ts, te in PHASES:
            mask = (times >= ts) & (times <= te)
            if mask.sum() > 0:
                result[f'IL_R10_r_{pname}_mean'] = float(il[mask].mean())
                result[f'IL_R10_r_{pname}_peak'] = float(il[mask].max())

    result['n_muscles'] = len(acts)
    return result


def fit_line(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 1.0
    return float(slope), float(intercept), float(r2)


def main():
    log('=== Phase 1a Reproduction Sweep — 5 conditions via base infrastructure ===')

    # Validate make_suit_sweep() (base Week 1.2)
    sweep = make_suit_sweep([0, 50, 100, 150, 200])
    log(f'make_suit_sweep() returned {len(sweep)} conditions:')
    for sc in sweep:
        log(f'  {sc.name}: force={sc.force_N} N, torque={sc.torque_Nm} N·m')

    # Shared model + reference
    shared_model = OUT_ROOT / 'phase1a_model.osim'
    shared_ref = OUT_ROOT / 'states_reference.sto'
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    if not shared_model.exists():
        log('Preparing Phase 1a model...')
        keep = load_phase1a_set()
        prepare_model(shared_model, keep)
    if not shared_ref.exists():
        log('Preparing reference kinematics...')
        prepare_reference(shared_ref)

    # Solve all 5 conditions sequentially
    results = {}
    timings = {}
    successes = {}
    for sc in sweep:
        sol_path, ok, elapsed = solve_condition(sc, shared_model, shared_ref)
        timings[sc.name] = elapsed
        successes[sc.name] = ok
        if ok or Path(sol_path).exists():
            data = load_phase_means(sol_path)
            results[sc.name] = data
            results[sc.name]['torque_nm'] = sc.torque_Nm
            results[sc.name]['force_n'] = sc.force_N
        else:
            log(f'[{sc.name}] FAILED — no solution data')

    # Compute dose-response
    log('Computing dose-response...')
    forces = [0, 50, 100, 150, 200]
    torques = np.array([f * MOMENT_ARM for f in forces])
    cond_names = [f'B_suit{f}' for f in forces]

    hold_means = np.array([results[c]['Hold_mean'] for c in cond_names if c in results and 'Hold_mean' in results[c]])
    con_means  = np.array([results[c]['Concentric_mean'] for c in cond_names if c in results and 'Concentric_mean' in results[c]])

    base_hold = results.get('B_suit0', {}).get('Hold_mean', None)
    base_con  = results.get('B_suit0', {}).get('Concentric_mean', None)

    if base_hold is not None:
        red_hold = np.array([100 * (base_hold - results[c].get('Hold_mean', base_hold)) / base_hold for c in cond_names if c in results])
        red_con  = np.array([100 * (base_con  - results[c].get('Concentric_mean', base_con))  / base_con  for c in cond_names if c in results])
        s_hold, i_hold, r2_hold = fit_line(torques[:len(red_hold)], red_hold)
        s_con, i_con, r2_con    = fit_line(torques[:len(red_con)],  red_con)

        print()
        print('=' * 70)
        print('Sweep Dose-Response Results (S1-S6)')
        print('=' * 70)
        print(f'{"S1":<4} All conditions converged: {all(successes.values())}')
        print(f'{"S2":<4} ES_mean Hold slope:  {s_hold:.3f} %/N·m  (expected 1.164 ±0.1)')
        print(f'{"S3":<4} R² Hold:             {r2_hold:.4f}  (expected 1.0000 ±0.05)')
        print(f'{"S4":<4} Reduction @ 24 N·m:  {red_hold[-1]:.2f} %  (expected 28 ±5%)')
        print(f'{"S5":<4} Hu 2026 14.9-28.6%:  {14.9 <= red_hold[-1] <= 28.6}')
        print(f'{"S6":<4} ES_mean Con slope:   {s_con:.3f} %/N·m (expected ~1.186)')
        print('=' * 70)

        # Write report
        report_path = OUT_ROOT / 'sweep_report.md'
        with open(report_path, 'w') as f:
            f.write('# Phase 1a Reproduction Sweep Report\n\n')
            f.write('## Infrastructure\n')
            f.write('- base.build_model_processor(task_type=stoop, rot=20, trans=50)\n')
            f.write('- base.make_suit_sweep([0,50,100,150,200])\n')
            f.write('- base.SuitConfig (unit safety assertion)\n\n')
            f.write('## Dose-Response Results\n\n')
            f.write('| Metric | Slope (%/Nm) | R^2 | Reduction @ 24 Nm |\n|---|---:|---:|---:|\n')
            f.write(f'| ES_mean Hold (new) | {s_hold:.3f} | {r2_hold:.4f} | {red_hold[-1]:.2f}% |\n')
            f.write(f'| ES_mean Con  (new) | {s_con:.3f}  | {r2_con:.4f}  | {red_con[-1]:.2f}%  |\n')
            f.write(f'| ES_mean Hold (orig)| 1.164 | 1.0000 | 27.95% |\n')
            f.write(f'| SO S1.6 reference  | 1.206 | 1.000  | 28.97% |\n\n')
            f.write('## S1-S6 Verification\n\n')
            f.write(f'- S1 All convergent: {all(successes.values())}\n')
            f.write(f'- S2 Hold slope deviation from 1.164: {abs(s_hold - 1.164):.3f} %/Nm\n')
            f.write(f'- S3 R^2: {r2_hold:.4f}\n')
            f.write(f'- S4 Reduction @ 24 Nm: {red_hold[-1]:.2f}%\n')
            f.write(f'- S5 Hu 2026 range match: {14.9 <= red_hold[-1] <= 28.6}\n')
        log(f'Report: {report_path}')

    log('=== Sweep Complete ===')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        log(f'FATAL: {e}')
        traceback.print_exc()
        sys.exit(1)
