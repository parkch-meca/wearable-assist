"""Phase 2.C.4 v2 — Box motion v11b, 4 conditions, Muscle set v2 (158 muscles).

Upgrade from v1 (114 muscles):
  + 44 lower limb muscles (glut_max, glut_med, hamstrings, quadriceps,
    iliopsoas, hip assist, hip deep rotators, adductors, calf, tibialis)
  = 158 total muscles

Motivation: v1 had excessive reserves:
  pelvis_tilt:  221 N·m  (Phase 1a: 19.4 N·m)
  hip_flexion:  179 N·m  (should be muscle-generated)
  pelvis_ty:   3570 N    (vertical support)
Adding lower limb muscles should absorb hip/knee/ankle moments → reserve reduction.

Conditions:
  B_noload  : suit OFF (0 N·m)
  B_suit50  : 50 N·m
  B_suit100 : 100 N·m
  B_suit200 : 200 N·m

Model  : MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim
Motion : box_motion_v11b.mot (t=0–5 s, 601 frames)
Solve window: t=1.0–4.0 s (lift focus, same as v1)
Mesh: 50 intervals

Phase 1a regression confirmed PASS (max ΔES 0.10 %p with muscle set v2).
"""
import os, sys, time, shutil
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim

# ── Add muscle_set_v2 to path ───────────────────────────────────────────────
SCRIPT_DIR = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts')
sys.path.insert(0, str(SCRIPT_DIR))
from muscle_set_v2 import MUSCLE_SET_V2

# ── Paths ──────────────────────────────────────────────────────────────────
SRC_MODEL = (
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
    'MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim'
)
MOT          = '/data/stoop_motion/box_motion_v11b.mot'
GRF_STO_BASE = '/data/stoop_motion/stoop_grf_v5.sto'
GRF_XML_BASE = '/data/stoop_motion/stoop_grf_v5.xml'
OUT_ROOT     = Path('/data/opensim_results/phase2c4_box_v11b_v2')

# ── Timing (identical to v1) ────────────────────────────────────────────────
T_START, T_END = 1.0, 4.0
MESH           = 50
RESERVE_OPTF   = 10.0

# ── Conditions ─────────────────────────────────────────────────────────────
CONDITIONS = [
    ('B_noload',  0.0),
    ('B_suit50',  50.0),
    ('B_suit100', 100.0),
    ('B_suit200', 200.0),
]

# ── Column definitions ──────────────────────────────────────────────────────
SUIT_COLS = [
    'thor_F_vx','thor_F_vy','thor_F_vz','thor_T_x','thor_T_y','thor_T_z',
    'thor_P_px','thor_P_py','thor_P_pz',
    'pel_F_vx','pel_F_vy','pel_F_vz','pel_T_x','pel_T_y','pel_T_z',
    'pel_P_px','pel_P_py','pel_P_pz',
]
GRF_COLS = [
    'ground_force_R_vx','ground_force_R_vy','ground_force_R_vz',
    'ground_force_R_px','ground_force_R_py','ground_force_R_pz',
    'ground_torque_R_x','ground_torque_R_y','ground_torque_R_z',
    'ground_force_L_vx','ground_force_L_vy','ground_force_L_vz',
    'ground_force_L_px','ground_force_L_py','ground_force_L_pz',
    'ground_torque_L_x','ground_torque_L_y','ground_torque_L_z',
]


def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def alpha_box(t):
    """Suit assist ramp profile (same as v1)."""
    if t < 0.5:   return 0.0
    if t <= 2.0:  return (1.0 - np.cos(np.pi * (t - 0.5) / 1.5)) / 2.0
    if t <= 2.5:  return 1.0
    if t <= 4.0:  return (1.0 + np.cos(np.pi * (t - 2.5) / 1.5)) / 2.0
    return 0.0


def prepare_model(out_path):
    """Trim model to MUSCLE_SET_V2 (158 muscles)."""
    keep = set(MUSCLE_SET_V2)
    import xml.etree.ElementTree as ET
    tree = ET.parse(SRC_MODEL)
    root = tree.getroot()
    removed = kept_mus = kept_other = 0
    MUSCLE_TYPES = {
        'Millard2012EquilibriumMuscle', 'Thelen2003Muscle',
        'DeGrooteFregly2016Muscle', 'ActivationFiberLengthMuscle',
        'Muscle', 'SimpleMuscle', 'RigidTendonMuscle',
    }
    for fs in root.iter('ForceSet'):
        obj = fs.find('objects')
        if obj is None: continue
        for child in list(obj):
            name = child.get('name')
            if name is None: continue
            if child.tag in MUSCLE_TYPES or 'Muscle' in child.tag:
                if name in keep:
                    kept_mus += 1
                else:
                    obj.remove(child)
                    removed += 1
            else:
                kept_other += 1
    tree.write(str(out_path), encoding='utf-8', xml_declaration=True)
    log(f'Model v2: kept {kept_mus} muscles + {kept_other} forces, removed {removed}')
    log(f'  Muscle set v2: {len(MUSCLE_SET_V2)} requested, {kept_mus} found in model')
    return out_path


def prepare_reference(out_path):
    """Convert motion to radians + Savitzky-Golay smoothing on arm coords (same as v1)."""
    from scipy.signal import savgol_filter
    tbl = osim.TimeSeriesTable(MOT)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())

    m = osim.Model(SRC_MODEL)
    m.initSystem()
    cs = m.getCoordinateSet()

    is_rot = []
    for L in labels:
        if cs.contains(L):
            is_rot.append(cs.get(L).getMotionType() == 1)
        else:
            is_rot.append(False)

    mask = (times >= T_START - 1e-9) & (times <= T_END + 1e-9)
    keep = np.where(mask)[0]
    n = len(keep)

    data = np.zeros((len(times), len(labels)))
    for i in range(len(times)):
        row = tbl.getRowAtIndex(i)
        for j in range(len(labels)):
            v = row[j]
            if is_rot[j]:
                v = np.radians(v)
            data[i, j] = v

    # Smooth arm coords to eliminate velocity discontinuities
    ARM_COORDS = ['elbow_flexion_r', 'elbow_flexion_l',
                  'shoulder_elv_r', 'shoulder_elv_l',
                  'elv_angle_r', 'elv_angle_l',
                  'shoulder_rot_r', 'shoulder_rot_l']
    SMOOTH_WIN = 51
    SMOOTH_ORD = 3
    dt = times[1] - times[0]
    for lab in ARM_COORDS:
        if lab in labels:
            idx = labels.index(lab)
            orig = data[:, idx]
            sm = savgol_filter(orig, window_length=SMOOTH_WIN, polyorder=SMOOTH_ORD)
            vel_before = np.abs(np.diff(orig)).max() / dt
            vel_after  = np.abs(np.diff(sm)).max() / dt
            data[:, idx] = sm
            log(f'  Smoothed {lab}: vel {vel_before:.1f} → {vel_after:.1f} rad/s')

    header = (
        f'box_v11b_moco_ref_smooth_v2\nversion=1\nnRows={n}\n'
        f'nColumns={1 + len(labels)}\ninDegrees=no\n\n'
        'Units are S.I. units.\n\nendheader\n'
        'time\t' + '\t'.join(labels) + '\n'
    )
    with open(out_path, 'w') as f:
        f.write(header)
        for i in keep:
            vals = [f'{times[i]:.6f}'] + [f'{data[i, j]:.6f}' for j in range(len(labels))]
            f.write('\t'.join(vals) + '\n')
    log(f'Reference: {n} frames  t=[{times[keep[0]]:.3f},{times[keep[-1]]:.3f}]')
    return out_path


def write_grf_suit_extloads(out_mot, out_xml, cond_dir, suit_torque_nm):
    """GRF (body + box weight after grasp) + suit torque pair.

    Box weight (20 kg × 9.81/2 = 98.1 N/foot) ramps onto feet at t=2.0 s (grasp)
    over 0.5 s. This satisfies vertical Newton's law without needing hand ExternalForce.
    Identical to v1 strategy.
    """
    tbl = osim.TimeSeriesTable(GRF_STO_BASE)
    times   = np.array(list(tbl.getIndependentColumn()))
    grf_lab = list(tbl.getColumnLabels())
    n       = tbl.getNumRows()

    BOX_MASS   = 20.0
    GRAVITY    = 9.81
    GRASP_T    = 2.0
    RAMP_DUR   = 0.5

    grf = np.zeros((n, len(GRF_COLS)))
    for i in range(n):
        row = tbl.getRowAtIndex(i)
        for j, c in enumerate(GRF_COLS):
            grf[i, j] = row[grf_lab.index(c)]

    vy_R_idx = GRF_COLS.index('ground_force_R_vy')
    vy_L_idx = GRF_COLS.index('ground_force_L_vy')
    box_force_per_foot = BOX_MASS * GRAVITY / 2.0

    for i, t in enumerate(times):
        t = float(t)
        if t < GRASP_T:
            alpha = 0.0
        elif t < GRASP_T + RAMP_DUR:
            alpha = (t - GRASP_T) / RAMP_DUR
        else:
            alpha = 1.0
        add_vy = box_force_per_foot * alpha
        grf[i, vy_R_idx] += add_vy
        grf[i, vy_L_idx] += add_vy

    suit = np.zeros((n, len(SUIT_COLS)))
    i_thor = SUIT_COLS.index('thor_T_z')
    i_pel  = SUIT_COLS.index('pel_T_z')
    for i, t in enumerate(times):
        Tz = suit_torque_nm * alpha_box(float(t))
        suit[i, i_thor] = +Tz
        suit[i, i_pel]  = -Tz

    all_cols = GRF_COLS + SUIT_COLS
    data = np.hstack([grf, suit])
    mot_name = Path(out_mot).name
    header = (
        f'phase2c4_box_v11b_v2_extloads  suit={suit_torque_nm}Nm\n'
        f'version=1\nnRows={n}\nnColumns={1 + len(all_cols)}\n'
        'inDegrees=no\n\n'
        'Units are S.I. units (second, meters, Newtons, ...)\n\nendheader\n'
        'time\t' + '\t'.join(all_cols) + '\n'
    )
    with open(out_mot, 'w') as f:
        f.write(header)
        for i, t in enumerate(times):
            f.write('\t'.join([f'{t:.6f}'] + [f'{v:.6f}' for v in data[i]]) + '\n')

    xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
  <ExternalLoads name="phase2c4_box_v11b_v2">
    <objects>
      <ExternalForce name="grf_R">
        <isDisabled>false</isDisabled>
        <applied_to_body>calcn_r</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>ground_force_R_v</force_identifier>
        <point_identifier>ground_force_R_p</point_identifier>
        <torque_identifier>ground_torque_R_</torque_identifier>
        <data_source_name>{mot_name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="grf_L">
        <isDisabled>false</isDisabled>
        <applied_to_body>calcn_l</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>ground_force_L_v</force_identifier>
        <point_identifier>ground_force_L_p</point_identifier>
        <torque_identifier>ground_torque_L_</torque_identifier>
        <data_source_name>{mot_name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="suit_thoracic">
        <isDisabled>false</isDisabled>
        <applied_to_body>thoracic1</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>thor_F_v</force_identifier>
        <point_identifier>thor_P_p</point_identifier>
        <torque_identifier>thor_T_</torque_identifier>
        <data_source_name>{mot_name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="suit_pelvis">
        <isDisabled>false</isDisabled>
        <applied_to_body>pelvis</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>pel_F_v</force_identifier>
        <point_identifier>pel_P_p</point_identifier>
        <torque_identifier>pel_T_</torque_identifier>
        <data_source_name>{mot_name}</data_source_name>
      </ExternalForce>
    </objects>
    <groups />
    <datafile>{mot_name}</datafile>
  </ExternalLoads>
</OpenSimDocument>
"""
    Path(out_xml).write_text(xml)
    log(f'External loads written: {Path(out_mot).name}')
    return out_mot, out_xml


def run_condition(label, suit_torque_nm, model_path, ref_path):
    cond_dir = OUT_ROOT / label
    cond_dir.mkdir(parents=True, exist_ok=True)

    ext_mot  = cond_dir / 'ext_loads.mot'
    ext_xml  = cond_dir / 'ext_loads.xml'
    sol_path = cond_dir / 'solution.sto'

    log(f'--- Condition: {label}  suit={suit_torque_nm} N·m ---')
    write_grf_suit_extloads(str(ext_mot), str(ext_xml), cond_dir, suit_torque_nm)

    log('Setting up MocoInverse...')
    inverse = osim.MocoInverse()
    inverse.setName(f'phase2c4_v2_{label}')

    model_proc = osim.ModelProcessor(str(model_path))
    model_proc.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    model_proc.append(osim.ModOpIgnoreTendonCompliance())
    model_proc.append(osim.ModOpIgnorePassiveFiberForcesDGF())
    model_proc.append(osim.ModOpAddExternalLoads(str(ext_xml)))
    model_proc.append(osim.ModOpAddReserves(RESERVE_OPTF))
    inverse.setModel(model_proc)

    inverse.setKinematics(osim.TableProcessor(str(ref_path)))
    inverse.set_initial_time(T_START)
    inverse.set_final_time(T_END)
    inverse.set_mesh_interval((T_END - T_START) / MESH)
    inverse.set_kinematics_allow_extra_columns(True)

    log(f'Solving... (mesh={MESH}, t=[{T_START},{T_END}], suit={suit_torque_nm} N·m, muscles=158)')
    t0 = time.time()
    sol = inverse.solve()
    t_el = time.time() - t0
    moco_sol = sol.getMocoSolution()
    success = moco_sol.success()
    status  = moco_sol.getStatus()
    log(f'Solve done: {t_el:.1f}s  success={success}  status={status}')

    try:
        moco_sol.unseal()
    except Exception:
        pass
    moco_sol.write(str(sol_path))
    log(f'Saved: {sol_path}')

    # Quick reserve check immediately after solve
    log('Quick reserve check...')
    tbl = osim.TimeSeriesTable(str(sol_path))
    labels = list(tbl.getColumnLabels())
    res_cols = [(i, L) for i, L in enumerate(labels) if 'reserve' in L.lower()]
    if res_cols:
        n = tbl.getNumRows()
        res_data = np.zeros((n, len(res_cols)))
        for i in range(n):
            row = tbl.getRowAtIndex(i)
            for j, (idx, _) in enumerate(res_cols):
                res_data[i, j] = row[idx] * RESERVE_OPTF
        max_abs = np.abs(res_data).max(axis=0)
        top5 = np.argsort(-max_abs)[:5]
        for j in top5:
            short = res_cols[j][1].split('/')[-1]
            log(f'  Reserve {short}: max={max_abs[j]:.1f}')

    return {
        'label': label,
        'suit_nm': suit_torque_nm,
        'success': success,
        'status': status,
        'wall_time_s': t_el,
        'sol_path': str(sol_path),
    }


def main():
    if len(sys.argv) > 1:
        requested = set(sys.argv[1:])
        conds = [(lbl, nm) for lbl, nm in CONDITIONS if lbl in requested]
        if not conds:
            log(f'Unknown condition(s): {sys.argv[1:]}')
            log(f'Valid: {[c[0] for c in CONDITIONS]}')
            sys.exit(2)
    else:
        conds = CONDITIONS

    log('=== Phase 2.C.4 v2 — Box v11b, Muscle Set v2 (158 muscles) ===')
    log(f'Model : {Path(SRC_MODEL).name}')
    log(f'Motion: {Path(MOT).name}')
    log(f'Muscle set v2: {len(MUSCLE_SET_V2)} muscles')
    log(f'Conditions: {[c[0] for c in conds]}')
    log(f'Mesh={MESH}, t=[{T_START},{T_END}], reserveOptF={RESERVE_OPTF}')
    log('Key question: does adding 44 lower-limb muscles reduce pelvis_tilt reserve (v1: 221 N·m)?')

    shared_dir = OUT_ROOT / 'shared'
    shared_dir.mkdir(parents=True, exist_ok=True)
    model_path = shared_dir / 'phase2c4_v2_model.osim'
    ref_path   = shared_dir / 'states_reference.sto'

    log(f'Preparing shared model v2 ({len(MUSCLE_SET_V2)} muscles)...')
    prepare_model(model_path)

    log('Preparing motion reference (degrees → radians + smoothing)...')
    prepare_reference(ref_path)

    results = []
    t_total = time.time()
    for label, suit_nm in conds:
        try:
            r = run_condition(label, suit_nm, model_path, ref_path)
            results.append(r)
        except Exception as e:
            log(f'FATAL in {label}: {e}')
            import traceback; traceback.print_exc()
            results.append({
                'label': label, 'suit_nm': suit_nm,
                'success': False, 'status': str(e),
                'wall_time_s': 0, 'sol_path': 'FAILED',
            })

    log('')
    log('=== SUMMARY ===')
    log(f'{"Condition":<12} {"Suit(Nm)":<10} {"Success":<10} {"Time(s)":<10} Status')
    for r in results:
        log(f'{r["label"]:<12} {r["suit_nm"]:<10.0f} {str(r["success"]):<10} '
            f'{r["wall_time_s"]:<10.1f} {r["status"]}')
    log(f'Total wall time: {time.time() - t_total:.1f}s')

    import json
    summary_path = OUT_ROOT / 'solve_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    log(f'Summary saved: {summary_path}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f'FATAL: {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)
