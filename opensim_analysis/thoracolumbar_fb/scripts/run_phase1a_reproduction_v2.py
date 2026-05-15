"""
Phase 1a Reproduction v2 — 5-Condition Suit Sweep (Week 3 REDO).

Critical fix vs v1:
    - Uses ModOpAddReserves(10.0) matching original Phase 1a (not base.build_model_processor
      which adds residuals(20,50)+reserves(1.0) that caused inf_pr stuck at 156).
    - Model: no_coupler_forearm_v1 (same as reproduction_l20/sweep)
    - All other parameters identical to original Phase 1a.

Usage:
    /home/sysop/miniconda3/envs/opensim/bin/python run_phase1a_reproduction_v2.py --force-n 0
    /home/sysop/miniconda3/envs/opensim/bin/python run_phase1a_reproduction_v2.py --force-n 200

Output:
    /data/opensim_results/phase1a_reproduction_v2/B_suit{N}/solution.sto
    /data/opensim_results/phase1a_reproduction_v2/B_suit{N}/run.log
"""
import argparse
import os
import sys
import time
from pathlib import Path

os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
sys.path.insert(0, '/data/wearable-assist/opensim_analysis/thoracolumbar_fb')

import numpy as np
import opensim as osim

# ---------------------------------------------------------------------------
# Paths — identical to original Phase 1a
# ---------------------------------------------------------------------------
SRC_MODEL = (
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
    'MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim'
)
MOT = '/data/stoop_motion/stoop_synthetic_v5.mot'
GRF_STO = '/data/stoop_motion/stoop_grf_v5.sto'
PHASE1A_LIST = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/phase1a_muscle_list.txt'
OUT_ROOT = Path('/data/opensim_results/phase1a_reproduction_v2')
SHARED_MODEL = OUT_ROOT / 'phase1a_model_v2.osim'
SHARED_REF = OUT_ROOT / 'states_reference_v2.sto'

T_START, T_END = 0.0, 5.0
MESH = 50
# CRITICAL: match original Phase 1a reserve setup
RESERVE_OPTF = 10.0   # original used ModOpAddReserves(10.0) for ALL joints
MOMENT_ARM = 0.12

PHASES = [
    ('Standing',   0.0, 0.5),
    ('Eccentric',  0.5, 1.5),
    ('Hold',       1.5, 2.5),
    ('Concentric', 2.5, 4.0),
    ('Recovery',   4.0, 5.0),
]

# 6-muscle ES subset
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


def log(msg, logfile=None):
    s = f'[{time.strftime("%H:%M:%S")}] {msg}'
    print(s, flush=True)
    if logfile:
        with open(logfile, 'a') as f:
            f.write(s + '\n')


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


def prepare_shared_model():
    """Strip model to Phase 1a 114-muscle subset."""
    if SHARED_MODEL.exists():
        return
    import xml.etree.ElementTree as ET
    keep = load_phase1a_set()
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
    tree.write(str(SHARED_MODEL), encoding='utf-8', xml_declaration=True)
    print(f'[prep] Phase1a model written: {SHARED_MODEL}')


def prepare_shared_reference():
    """Convert motion to radians for MocoInverse."""
    if SHARED_REF.exists():
        return
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
        f"stoop_v5_p1a_repro_v2\nversion=1\nnRows={n}\n"
        f"nColumns={1+len(labels)}\ninDegrees=no\n\n"
        "Units are S.I. units.\n\nendheader\n"
        "time\t" + "\t".join(labels) + "\n"
    )
    with open(SHARED_REF, 'w') as f:
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
    print(f'[prep] Reference kinematics written: {SHARED_REF}')


def write_extloads(cond_dir, torque_nm):
    """Write combined GRF + suit torque external loads."""
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
        f"phase1a_repro_v2_grf  T={torque_nm:.1f}Nm\nversion=1\nnRows={n}\n"
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
  <ExternalLoads name="phase1a_repro_v2_grf_suit">
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


def solve_condition(force_n, logfile=None):
    """Solve one suit condition. Returns (sol_path, success, elapsed)."""
    torque_nm = force_n * MOMENT_ARM
    cond_name = f'B_suit{int(force_n)}'
    cond_dir = OUT_ROOT / cond_name
    cond_dir.mkdir(parents=True, exist_ok=True)
    sol_path = cond_dir / 'solution.sto'

    if sol_path.exists() and sol_path.stat().st_size > 0:
        log(f'[{cond_name}] solution.sto exists (size={sol_path.stat().st_size}), skipping', logfile)
        return str(sol_path), True, 0.0

    # Write ext loads
    _, ext_xml = write_extloads(cond_dir, torque_nm)
    log(f'[{cond_name}] ext_loads written (T={torque_nm:.1f} Nm)', logfile)

    # CRITICAL: use same reserve setup as original Phase 1a
    # Original: ModOpAddReserves(10.0) for ALL joints (no ModOpAddResiduals)
    mp = osim.ModelProcessor(str(SHARED_MODEL))
    mp.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    mp.append(osim.ModOpIgnoreTendonCompliance())
    mp.append(osim.ModOpIgnorePassiveFiberForcesDGF())
    mp.append(osim.ModOpAddExternalLoads(ext_xml))
    mp.append(osim.ModOpAddReserves(RESERVE_OPTF))  # 10.0 N/Nm for ALL joints

    inverse = osim.MocoInverse()
    inverse.setName(f'repro_v2_{cond_name}')
    inverse.setModel(mp)
    inverse.setKinematics(osim.TableProcessor(str(SHARED_REF)))
    inverse.set_initial_time(T_START)
    inverse.set_final_time(T_END)
    inverse.set_mesh_interval((T_END - T_START) / MESH)
    inverse.set_kinematics_allow_extra_columns(True)

    log(f'[{cond_name}] Solving (mesh={MESH}, T={torque_nm:.1f} Nm, optF={RESERVE_OPTF})...', logfile)
    t0 = time.time()
    sol = inverse.solve()
    elapsed = time.time() - t0

    moco_sol = sol.getMocoSolution()
    success = moco_sol.success()
    status = moco_sol.getStatus()
    log(f'[{cond_name}] Solve: success={success}  status={status}  time={elapsed:.1f}s', logfile)

    try:
        moco_sol.unseal()
    except Exception:
        pass
    moco_sol.write(str(sol_path))
    log(f'[{cond_name}] Saved {sol_path}  size={sol_path.stat().st_size}', logfile)
    return str(sol_path), success, elapsed


def load_act(tbl, name):
    labels = list(tbl.getColumnLabels())
    n = tbl.getNumRows()
    for i, L in enumerate(labels):
        if L.endswith(f'/{name}/activation'):
            return np.array([tbl.getRowAtIndex(k)[i] for k in range(n)]) * 100
    return None


def analyze_solution(sol_path):
    """Extract ES metrics and reserve values."""
    tbl = osim.TimeSeriesTable(sol_path)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())

    # ES6 activations
    acts = {n: load_act(tbl, n) for n in ES6}
    acts = {k: v for k, v in acts.items() if v is not None}
    if not acts:
        return None

    arr = np.stack(list(acts.values()), axis=1)
    es_mean = arr.mean(axis=1)
    il_r10 = load_act(tbl, 'IL_R10_r')

    # Reserve pelvis_ty
    pelvis_ty_max_n = None
    for i, L in enumerate(labels):
        if 'pelvis_ty' in L and 'reserve' in L:
            data = np.array([tbl.getRowAtIndex(k)[i] for k in range(tbl.getNumRows())])
            pelvis_ty_max_n = float(np.abs(data).max() * RESERVE_OPTF)
            break

    result = {'n_muscles': len(acts), 'pelvis_ty_max_n': pelvis_ty_max_n}

    for pname, ts, te in PHASES:
        mask = (times >= ts) & (times <= te)
        if mask.sum() > 0:
            result[f'ES_mean_{pname}_mean'] = float(es_mean[mask].mean())
            result[f'ES_mean_{pname}_peak'] = float(es_mean[mask].max())
            if il_r10 is not None:
                result[f'IL_R10_{pname}_mean'] = float(il_r10[mask].mean())
                result[f'IL_R10_{pname}_peak'] = float(il_r10[mask].max())

    # Hold using sweep_report window t>=2.0, t<2.5 for comparability
    mask_hold_orig = (times >= 2.0) & (times < 2.5)
    mask_con_orig  = (times >= 2.5) & (times < 4.0)
    result['ES_mean_Hold_orig'] = float(es_mean[mask_hold_orig].mean())
    result['ES_mean_Conc_orig'] = float(es_mean[mask_con_orig].mean())

    return result


def print_regression_table(results_by_force):
    """Print dose-response regression vs original baseline."""
    forces = [0, 50, 100, 150, 200]
    torques = np.array([f * MOMENT_ARM for f in forces])

    # Original baseline values (from actual solution files, sweep_report window)
    orig_hold_es = np.array([52.71, 49.02, 45.36, 41.66, 37.97])
    orig_conc_es = np.array([49.87, 46.32, 42.79, 39.23, 35.68])
    orig_hold_il = np.array([87.73, 79.30, 70.88, 62.44, 53.96])  # from sweep_report IL_R10_r Hold mean

    # New values (sweep_report window)
    new_hold_es = np.array([results_by_force[f].get('ES_mean_Hold_orig', np.nan) for f in forces])
    new_conc_es = np.array([results_by_force[f].get('ES_mean_Conc_orig', np.nan) for f in forces])

    # Delta
    delta_hold = new_hold_es - orig_hold_es
    delta_conc = new_conc_es - orig_conc_es

    from scipy.stats import linregress

    print()
    print('=' * 80)
    print('Phase 5: Regression Test — New Infrastructure vs Original Phase 1a')
    print('=' * 80)

    print(f'\n{"F(N)":>6} {"T(Nm)":>6} {"Orig_Hold_ES%":>14} {"New_Hold_ES%":>13} {"Delta":>7} {"Orig_Conc_ES%":>14} {"New_Conc_ES%":>13} {"Delta":>7}')
    for i, f in enumerate(forces):
        print(f'{f:>6} {torques[i]:>6.1f} {orig_hold_es[i]:>14.2f} {new_hold_es[i]:>13.2f} {delta_hold[i]:>+7.2f} {orig_conc_es[i]:>14.2f} {new_conc_es[i]:>13.2f} {delta_conc[i]:>+7.2f}')

    print(f'\nMax |ΔES_mean Hold| = {np.abs(delta_hold).max():.2f} %p  (threshold: 5.0 %p)')
    print(f'Max |ΔES_mean Conc| = {np.abs(delta_conc).max():.2f} %p  (threshold: 5.0 %p)')

    # New dose-response
    base_h = new_hold_es[0]; base_c = new_conc_es[0]
    red_h = 100 * (base_h - new_hold_es) / base_h
    red_c = 100 * (base_c - new_conc_es) / base_c
    orig_red_h = 100 * (orig_hold_es[0] - orig_hold_es) / orig_hold_es[0]

    if not np.any(np.isnan(red_h)) and len(red_h) > 1:
        s_h, i_h, r_h, _, _ = linregress(torques, red_h)
        s_c, i_c, r_c, _, _ = linregress(torques, red_c)
        print(f'\nDose-Response (new):')
        print(f'  ES_mean Hold slope:  {s_h:.3f} %/Nm  R²={r_h**2:.4f}  @24Nm={red_h[-1]:.2f}%')
        print(f'  ES_mean Conc slope:  {s_c:.3f} %/Nm  R²={r_c**2:.4f}  @24Nm={red_c[-1]:.2f}%')
        print(f'Dose-Response (orig):')
        print(f'  ES_mean Hold slope:  1.164 %/Nm  R²=1.0000  @24Nm=27.95%')
        print(f'  ES_mean Conc slope:  1.186 %/Nm  R²=1.0000  @24Nm=28.46%')
        print(f'Diff slope Hold: {abs(s_h - 1.164):.3f} %/Nm  (threshold: 0.1)')
        print(f'Diff R²:         {abs(r_h**2 - 1.0):.4f}       (threshold: 0.05)')

    print()
    print('=' * 80)

    # Scenario determination
    all_delta = np.concatenate([np.abs(delta_hold), np.abs(delta_conc)])
    max_delta = np.nanmax(all_delta)
    if max_delta < 5.0:
        print('SCENARIO: A — PASS (all |ΔES| < 5 %p)')
    elif max_delta < 10.0:
        print(f'SCENARIO: B — PARTIAL PASS (max |ΔES|={max_delta:.2f} %p, some > 5 %p)')
    else:
        print(f'SCENARIO: C — FAIL (max |ΔES|={max_delta:.2f} %p > 10 %p)')
    print('=' * 80)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--force-n', type=float, required=True,
                        help='Suit force in N (0,50,100,150,200)')
    args = parser.parse_args()
    force_n = float(args.force_n)

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    cond_name = f'B_suit{int(force_n)}'
    cond_dir = OUT_ROOT / cond_name
    logfile = cond_dir / 'run.log'
    cond_dir.mkdir(parents=True, exist_ok=True)

    log(f'=== Phase 1a Reproduction v2 — {cond_name} (F={force_n}N, T={force_n*MOMENT_ARM:.1f}Nm) ===', logfile)
    log(f'Reserve setup: ModOpAddReserves({RESERVE_OPTF}) — matches original Phase 1a', logfile)
    log(f'Model: {SRC_MODEL}', logfile)

    # Prepare shared files (idempotent)
    log('Preparing shared model...', logfile)
    prepare_shared_model()
    log('Preparing shared reference...', logfile)
    prepare_shared_reference()

    # Solve
    sol_path, success, elapsed = solve_condition(force_n, logfile)

    if success and Path(sol_path).exists():
        log('Analyzing solution...', logfile)
        metrics = analyze_solution(sol_path)
        if metrics:
            log(f'n_muscles: {metrics["n_muscles"]}', logfile)
            log(f'pelvis_ty reserve max: {metrics.get("pelvis_ty_max_n", "N/A"):.2f} N', logfile)
            for pname, _, _ in PHASES:
                key_mean = f'ES_mean_{pname}_mean'
                key_il = f'IL_R10_{pname}_peak'
                if key_mean in metrics:
                    log(f'  {pname}: ES_mean={metrics[key_mean]:.2f}%  IL_R10_peak={metrics.get(key_il, float("nan")):.2f}%', logfile)
    else:
        log(f'SOLVE FAILED or solution not written. success={success}', logfile)

    log('=== Done ===', logfile)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        print(f'FATAL: {e}')
        traceback.print_exc()
        sys.exit(1)
