"""
Phase 1a Reproduction — L20 Single Condition (Week 3, Step 2).

Uses the new base infrastructure (build_model_processor, SuitConfig) to
reproduce the Phase 1a MocoInverse solve with the L20 (24 N·m) suit condition.

Expected results (from existing Phase 1a memory):
    IL_R10_r Standing    : ~8.1 %
    IL_R10_r Eccentric   : ~53.3 %
    IL_R10_r Hold        : ~87.7 % (baseline, F=0) / reduced with suit
    IL_R10_r Concentric  : ~82.8 % (baseline)
    IL_R10_r Recovery    : ~27.6 %
    ES reduction @24 Nm  : ~28 %
    Reserve pelvis_ty    : < 100 N

The script uses MocoInverse (same as original Phase 1a) but builds the
ModelProcessor via base.build_model_processor() for consistency.

Usage:
    /home/sysop/miniconda3/envs/opensim/bin/python run_phase1a_reproduction_l20.py

Output:
    /data/opensim_results/phase1a_reproduction/B_suit200/solution.sto
    /data/opensim_results/phase1a_reproduction/B_noload/solution.sto
"""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
sys.path.insert(0, '/data/wearable-assist/opensim_analysis/thoracolumbar_fb')

import numpy as np
import opensim as osim

# ---------------------------------------------------------------------------
# Paths — match original Phase 1a exactly
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

# Phase 1a 5-phase definitions (verified)
PHASES = [
    ('Standing',   0.0, 0.5),
    ('Eccentric',  0.5, 1.5),
    ('Hold',       1.5, 2.5),
    ('Concentric', 2.5, 4.0),
    ('Recovery',   4.0, 5.0),
]

# Suit sweep columns
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
    """Suit activation profile matching gen_stoop_v5 schedule."""
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
    """Strip model to Phase 1a 114-muscle subset (identical to original)."""
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
    return out_path


def prepare_reference(out_path):
    """Convert motion to radians for MocoInverse kinematics input."""
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
        f"stoop_v5_p1a_repro\nversion=1\nnRows={n}\n"
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


def write_combined_extloads(out_mot, out_xml, suit_torque_nm):
    """Combine GRF + suit torque into single ext_loads .mot + .xml."""
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
    if suit_torque_nm > 0:
        i_thor = SUIT_COLS.index('thor_T_z')
        i_pel = SUIT_COLS.index('pel_T_z')
        for i, t in enumerate(times):
            Tz = suit_torque_nm * alpha_v5(float(t))
            suit[i, i_thor] = +Tz
            suit[i, i_pel] = -Tz

    all_cols = GRF_COLS + SUIT_COLS
    data = np.hstack([grf, suit])
    header = (
        f"phase1a_repro_grf  T={suit_torque_nm}Nm\nversion=1\nnRows={n}\n"
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


def solve_condition(cond_name, torque_nm, shared_model, shared_ref):
    """Run MocoInverse for one condition using new base infrastructure."""
    from base import build_model_processor, SuitConfig, PHASE1A_FORCE_N, PHASE1A_MOMENT_ARM

    cond_dir = OUT_ROOT / cond_name
    cond_dir.mkdir(parents=True, exist_ok=True)

    ext_mot = cond_dir / 'ext_grf_suit.mot'
    ext_xml = cond_dir / 'ext_grf_suit.xml'
    sol_path = cond_dir / 'solution.sto'

    if sol_path.exists():
        log(f'[{cond_name}] solution.sto already exists, skipping solve')
        return str(sol_path)

    log(f'[{cond_name}] Writing ext loads (torque={torque_nm} N·m)')
    write_combined_extloads(str(ext_mot), str(ext_xml), torque_nm)

    # --- base infrastructure: build_model_processor ---
    # stoop task: residuals_rot=20 N·m, residuals_trans=50 N (Architecture §2.3)
    # ExternalLoads applied via ModelProcessor (GRF + suit torque in same file)
    log(f'[{cond_name}] Building ModelProcessor via base.build_model_processor()')
    mp = build_model_processor(
        model_path=str(shared_model),
        task_type='stoop',
        external_loads_xml=str(ext_xml),
    )
    # Muscle operators (MocoInverse requires these)
    mp.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    mp.append(osim.ModOpIgnoreTendonCompliance())
    mp.append(osim.ModOpIgnorePassiveFiberForcesDGF())

    # --- MocoInverse (same solver as original Phase 1a) ---
    inverse = osim.MocoInverse()
    inverse.setName(f'phase1a_repro_{cond_name}')
    inverse.setModel(mp)
    inverse.setKinematics(osim.TableProcessor(str(shared_ref)))
    inverse.set_initial_time(T_START)
    inverse.set_final_time(T_END)
    inverse.set_mesh_interval((T_END - T_START) / MESH)
    inverse.set_kinematics_allow_extra_columns(True)

    # SuitConfig validation (unit safety — base Week 1.2)
    if torque_nm > 0:
        force_equiv = torque_nm / PHASE1A_MOMENT_ARM
        sc = SuitConfig(cond_name, force_N=force_equiv, moment_arm_m=PHASE1A_MOMENT_ARM)
        log(f'[{cond_name}] SuitConfig: force={sc.force_N} N, arm={sc.moment_arm_m} m, '
            f'torque={sc.torque_Nm} N·m  (assertion PASS)')

    log(f'[{cond_name}] Solving (mesh={MESH}, T={torque_nm} N·m)...')
    t0 = time.time()
    sol = inverse.solve()
    elapsed = time.time() - t0
    moco_sol = sol.getMocoSolution()
    success = moco_sol.success()
    log(f'[{cond_name}] Solve done: success={success}  elapsed={elapsed:.1f}s')

    try:
        moco_sol.unseal()
    except Exception:
        pass
    moco_sol.write(str(sol_path))
    log(f'[{cond_name}] Saved {sol_path}')
    return str(sol_path)


def extract_phase_values(sol_path):
    """Extract IL_R10_r activation per phase + reserve stats."""
    tbl = osim.TimeSeriesTable(sol_path)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())

    # Find IL_R10_r activation column
    il_r10_r = None
    for i, L in enumerate(labels):
        if L.endswith('/IL_R10_r/activation'):
            il_r10_r = np.array([tbl.getRowAtIndex(j)[i] for j in range(tbl.getNumRows())]) * 100
            break

    # Find pelvis_ty reserve
    pelvis_ty_max = None
    for i, L in enumerate(labels):
        if 'pelvis_ty' in L and 'reserve' in L:
            col = np.array([tbl.getRowAtIndex(j)[i] for j in range(tbl.getNumRows())])
            pelvis_ty_max = float(np.abs(col).max() * RESERVE_OPTF)
            break

    phase_vals = {}
    if il_r10_r is not None:
        for pname, ts, te in PHASES:
            mask = (times >= ts) & (times <= te)
            if mask.sum() > 0:
                phase_vals[pname] = {
                    'mean': float(il_r10_r[mask].mean()),
                    'peak': float(il_r10_r[mask].max()),
                }
    return phase_vals, pelvis_ty_max


def print_verification_table(phase_vals_noload, phase_vals_suit, pelvis_ty_noload, pelvis_ty_suit):
    """Print T1-T8 verification table."""
    # Reference values from memory
    ref = {
        'Standing':   8.1,
        'Eccentric':  53.3,
        'Hold':       87.7,
        'Concentric': 82.8,
        'Recovery':   27.6,
    }

    print()
    print('=' * 70)
    print('L20 Single Condition — T1-T8 Verification')
    print('=' * 70)
    print(f'{"Test":<8} {"Description":<35} {"Expected":>10} {"Actual":>10} {"Result":>8}')
    print('-' * 70)
    print(f'{"T1":<8} {"IPOPT Solve success":<35} {"OK":>10} {"?":<10} check log')
    print(f'{"T2":<8} {"Wall time reasonable":<35} {"~140s":>10} {"?":<10} check log')

    tol = 15.0  # ±15 %p tolerance for reproduction
    for test_id, phase, desc in [
        ('T3', 'Standing', 'IL_R10 Standing'),
        ('T4', 'Eccentric', 'IL_R10 Eccentric peak'),
        ('T5', 'Hold', 'IL_R10 Hold peak'),
        ('T6', 'Concentric', 'IL_R10 Concentric peak'),
        ('T7', 'Recovery', 'IL_R10 Recovery'),
    ]:
        expected = ref[phase]
        if phase in phase_vals_noload:
            actual = phase_vals_noload[phase]['peak']
            delta = abs(actual - expected)
            status = 'PASS' if delta < tol else 'WARN'
            print(f'{test_id:<8} {desc:<35} {expected:>10.1f}% {actual:>10.1f}% {status:>8}')
        else:
            print(f'{test_id:<8} {desc:<35} {expected:>10.1f}% {"N/A":>10} {"SKIP":>8}')

    # T8 Reserve pelvis_ty
    if pelvis_ty_noload is not None:
        status = 'PASS' if pelvis_ty_noload < 100 else 'WARN'
        print(f'{"T8":<8} {"Reserve pelvis_ty < 100 N":<35} {"<100 N":>10} {pelvis_ty_noload:>10.1f}N {status:>8}')
    else:
        print(f'{"T8":<8} {"Reserve pelvis_ty < 100 N":<35} {"<100 N":>10} {"N/A":>10} {"SKIP":>8}')
    print('=' * 70)

    # Suit effect vs noload
    if phase_vals_noload and phase_vals_suit:
        print()
        print('L20 Suit Effect (B_suit200 vs B_noload):')
        for phase in ['Hold', 'Concentric', 'Eccentric']:
            if phase in phase_vals_noload and phase in phase_vals_suit:
                base = phase_vals_noload[phase]['peak']
                suit = phase_vals_suit[phase]['peak']
                red = 100 * (base - suit) / base
                print(f'  {phase:<12}: noload={base:.1f}%  suit={suit:.1f}%  reduction={red:.1f}%')


def main():
    log('=== Phase 1a Reproduction — L20 Single Condition (new base infrastructure) ===')

    # Step 1: Shared model (114 muscles)
    log('Step 1: Preparing Phase 1a model (114 muscles)')
    shared_model = OUT_ROOT / 'phase1a_model.osim'
    if not shared_model.exists():
        keep = load_phase1a_set()
        OUT_ROOT.mkdir(parents=True, exist_ok=True)
        prepare_model(shared_model, keep)
        log(f'  Model prepared: {shared_model}')
    else:
        log(f'  Model already exists: {shared_model}')

    # Step 2: Reference kinematics
    log('Step 2: Preparing reference kinematics')
    shared_ref = OUT_ROOT / 'states_reference.sto'
    if not shared_ref.exists():
        prepare_reference(shared_ref)
        log(f'  Reference prepared: {shared_ref}')
    else:
        log(f'  Reference already exists: {shared_ref}')

    # Step 3: Solve B_noload (F=0, T=0)
    log('Step 3: Solving B_noload (baseline, F=0, T=0)')
    noload_path = solve_condition('B_noload', torque_nm=0.0,
                                  shared_model=shared_model,
                                  shared_ref=shared_ref)

    # Step 4: Solve B_suit200 (L20, F=200N, T=24 N·m)
    log('Step 4: Solving B_suit200 (L20, F=200N, T=24 N·m)')
    suit_path = solve_condition('B_suit200', torque_nm=24.0,
                                shared_model=shared_model,
                                shared_ref=shared_ref)

    # Step 5: Verification
    log('Step 5: Verification T1-T8')
    phase_vals_noload, pelvis_ty_noload = extract_phase_values(noload_path)
    phase_vals_suit, pelvis_ty_suit = extract_phase_values(suit_path)

    print_verification_table(phase_vals_noload, phase_vals_suit,
                              pelvis_ty_noload, pelvis_ty_suit)

    log('=== L20 Reproduction Complete ===')
    log(f'B_noload: {noload_path}')
    log(f'B_suit200: {suit_path}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        log(f'FATAL: {e}')
        traceback.print_exc()
        sys.exit(1)
