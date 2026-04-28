"""Phase 1a — Suit effect analysis.

Runs MocoInverse with a 200 N (24 N·m peak) suit torque coupler added to
the existing GRF, on the same Phase 1a configuration that converged in
2 minutes. Output is the suit-condition solution. Compare against the
baseline solution (results/phase1a_full/solution.sto).

Suit specification (matches existing SO v5 pipeline):
  - Action-reaction torque pair around z-axis (sagittal extension):
      thoracic1 :  +T * alpha(t)  N·m
      pelvis    :  -T * alpha(t)  N·m
  - T = 200 N × 0.12 m moment arm = 24 N·m peak
  - alpha(t) profile (matches gen_stoop_v5):
      t < 0.5         → 0
      0.5 ≤ t ≤ 2.5   → cosine ramp 0 → 1
      2.5 ≤ t ≤ 3.0   → 1 (hold during stoop plateau)
      3.0 ≤ t ≤ 5.0   → cosine ramp 1 → 0
"""
import os, sys, time, shutil
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim

SRC_MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_moco_stoop.osim'
MOT = '/data/stoop_motion/stoop_synthetic_v5.mot'
GRF_STO = '/data/stoop_motion/stoop_grf_v5.sto'
PHASE1A_LIST = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/phase1a_muscle_list.txt'
OUT_ROOT_DEFAULT = Path('/data/wearable-assist/results/phase1a_suit_effect')

T_START, T_END = 0.0, 5.0
MESH = 50
RESERVE_OPTF = 10.0
MOMENT_ARM = 0.12
# Default; override via env var SUIT_FORCE_N
SUIT_FORCE_N = float(os.environ.get('SUIT_FORCE_N', '200'))
SUIT_TORQUE_PEAK = SUIT_FORCE_N * MOMENT_ARM
OUT_ROOT = Path(os.environ.get('OUT_ROOT', str(OUT_ROOT_DEFAULT)))
OUT_ROOT.mkdir(parents=True, exist_ok=True)


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


def log(msg): print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def alpha_v5(t):
    if t < 0.5:  return 0.0
    if t <= 2.5: return (1.0 - np.cos(np.pi * (t - 0.5) / 2.0)) / 2.0
    if t <= 3.0: return 1.0
    if t <= 5.0: return (1.0 + np.cos(np.pi * (t - 3.0) / 2.0)) / 2.0
    return 0.0


def write_combined_extloads(out_mot, out_xml, suit_torque_nm):
    """Combine GRF + suit torque pair into one ext_loads .mot + xml."""
    tbl = osim.TimeSeriesTable(GRF_STO)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    n = tbl.getNumRows()
    grf = np.zeros((n, len(GRF_COLS)))
    for i in range(n):
        r = tbl.getRowAtIndex(i)
        for j, c in enumerate(GRF_COLS):
            grf[i, j] = r[labels.index(c)]
    suit = np.zeros((n, len(SUIT_COLS)))
    i_thor = SUIT_COLS.index('thor_T_z')
    i_pel  = SUIT_COLS.index('pel_T_z')
    for i, t in enumerate(times):
        Tz = suit_torque_nm * alpha_v5(float(t))
        suit[i, i_thor] = +Tz
        suit[i, i_pel]  = -Tz

    all_cols = GRF_COLS + SUIT_COLS
    data = np.hstack([grf, suit])
    header = (
        f"phase1a_suit_grf  T={suit_torque_nm}Nm\nversion=1\nnRows={n}\n"
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
  <ExternalLoads name="phase1a_grf_suit">
    <objects>
      <ExternalForce name="grf_R">
        <isDisabled>false</isDisabled>
        <applied_to_body>calcn_r</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>ground_force_R_v</force_identifier>
        <point_identifier>ground_force_R_p</point_identifier>
        <torque_identifier>ground_torque_R_</torque_identifier>
        <data_source_name>{Path(out_mot).name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="grf_L">
        <isDisabled>false</isDisabled>
        <applied_to_body>calcn_l</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>ground_force_L_v</force_identifier>
        <point_identifier>ground_force_L_p</point_identifier>
        <torque_identifier>ground_torque_L_</torque_identifier>
        <data_source_name>{Path(out_mot).name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="suit_thoracic">
        <isDisabled>false</isDisabled>
        <applied_to_body>thoracic1</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>thor_F_v</force_identifier>
        <point_identifier>thor_P_p</point_identifier>
        <torque_identifier>thor_T_</torque_identifier>
        <data_source_name>{Path(out_mot).name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="suit_pelvis">
        <isDisabled>false</isDisabled>
        <applied_to_body>pelvis</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>pel_F_v</force_identifier>
        <point_identifier>pel_P_p</point_identifier>
        <torque_identifier>pel_T_</torque_identifier>
        <data_source_name>{Path(out_mot).name}</data_source_name>
      </ExternalForce>
    </objects>
    <groups />
    <datafile>{Path(out_mot).name}</datafile>
  </ExternalLoads>
</OpenSimDocument>
"""
    Path(out_xml).write_text(xml)


def load_phase1a_set():
    names = set()
    with open(PHASE1A_LIST) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith('#'): continue
            names.add(s)
    return names


def prepare_model(out_path):
    """Same XML strip as phase1a_full."""
    keep = load_phase1a_set()
    import xml.etree.ElementTree as ET
    tree = ET.parse(SRC_MODEL); root = tree.getroot()
    MUSCLE_TYPES = {'Millard2012EquilibriumMuscle','Thelen2003Muscle',
                    'DeGrooteFregly2016Muscle','ActivationFiberLengthMuscle',
                    'Muscle','SimpleMuscle','RigidTendonMuscle'}
    for fs in root.iter('ForceSet'):
        obj = fs.find('objects')
        if obj is None: continue
        for child in list(obj):
            name = child.get('name')
            if name is None: continue
            if child.tag in MUSCLE_TYPES or 'Muscle' in child.tag:
                if name not in keep:
                    obj.remove(child)
    tree.write(str(out_path), encoding='utf-8', xml_declaration=True)
    return out_path


def prepare_reference(out_path):
    tbl = osim.TimeSeriesTable(MOT)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    m = osim.Model(SRC_MODEL); m.initSystem()
    cs = m.getCoordinateSet()
    is_rot = [cs.contains(L) and cs.get(L).getMotionType() == 1 for L in labels]
    mask = (times >= T_START - 1e-9) & (times <= T_END + 1e-9)
    keep = np.where(mask)[0]
    n = len(keep)
    header = (f"stoop_v5_p1a_suit\nversion=1\nnRows={n}\n"
              f"nColumns={1+len(labels)}\ninDegrees=no\n\n"
              "Units are S.I. units.\n\nendheader\n"
              "time\t" + "\t".join(labels) + "\n")
    with open(out_path, 'w') as f:
        f.write(header)
        for i in keep:
            row = tbl.getRowAtIndex(int(i))
            vals = [f"{times[i]:.6f}"]
            for j, lab in enumerate(labels):
                v = row[j]
                if is_rot[j]: v = np.radians(v)
                vals.append(f"{v:.6f}")
            f.write("\t".join(vals) + "\n")


def main():
    log('=== Phase 1a Suit effect — MocoInverse with 24 N·m suit torque ===')
    model_path = OUT_ROOT / 'phase1a_model.osim'
    ref_path   = OUT_ROOT / 'states_reference.sto'
    ext_mot    = OUT_ROOT / 'ext_grf_suit.mot'
    ext_xml    = OUT_ROOT / 'ext_grf_suit.xml'
    sol_path   = OUT_ROOT / 'solution_suit.sto'

    log('Step 1: prepare model (114 muscles)')
    prepare_model(model_path)

    log('Step 2: prepare reference')
    prepare_reference(ref_path)

    log('Step 3: build combined GRF + suit torque ext_loads')
    write_combined_extloads(ext_mot, ext_xml, SUIT_TORQUE_PEAK)

    log('Step 4: MocoInverse setup + solve')
    inverse = osim.MocoInverse()
    inverse.setName('phase1a_suit')

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

    log(f'Solving (mesh={MESH}, suit T={SUIT_TORQUE_PEAK} Nm)...')
    t0 = time.time()
    sol = inverse.solve()
    t_el = time.time() - t0
    moco_sol = sol.getMocoSolution()
    log(f'Solve done in {t_el:.1f}s  success={moco_sol.success()}')

    try: moco_sol.unseal()
    except Exception: pass
    moco_sol.write(str(sol_path))
    log(f'Saved {sol_path}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f'FATAL: {e}'); import traceback; traceback.print_exc(); sys.exit(1)
