"""Step A.2 — pelvis_tilt 175 Nm root cause analysis script.

Implements Phase 3 verification:
  - Creates a modified stoop motion with shoulder_elv=0 (arm hanging)
  - Runs Phase 1a smoke solve with no_coupler model + shoulder_elv=0 kinematics
  - Compares pelvis_tilt reserve vs baseline no_coupler (arm elevated by coupler artifact)
  - Verifies: if shoulder_elv=0 → pelvis_tilt reserve drops to normal

Usage:
  /home/sysop/miniconda3/envs/opensim/bin/python analyze_pelvis_tilt_root_cause.py

Output:
  /data/opensim_results/variation_matrix_phase1a/V3_armhang/solution.sto
"""
import os, sys, time, shutil
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim

MOT         = '/data/stoop_motion/stoop_synthetic_v5.mot'
GRF_XML     = '/data/stoop_motion/stoop_grf_v5.xml'
GRF_STO     = '/data/stoop_motion/stoop_grf_v5.sto'
PHASE1A_LIST = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/phase1a_muscle_list.txt'
SRC_NO_COUPLER = (
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
    'MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler.osim'
)
OUT_DIR = Path('/data/opensim_results/variation_matrix_phase1a/V3_armhang')
RESERVE_OPTF = 10.0
T_START, T_END = 1.0, 3.0
MESH = 25


def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def create_arm_hang_motion(out_path):
    """Create modified stoop motion with shoulder_elv=elv_angle=0 throughout.

    This represents arms hanging by sides (no coupler-driven elevation).
    Appropriate for no_coupler model in stoop lift.
    """
    tbl = osim.TimeSeriesTable(MOT)
    labels = list(tbl.getColumnLabels())
    times = np.array(list(tbl.getIndependentColumn()))
    n = len(times)

    # Columns to zero out (arm elevation from coupler artifact)
    zero_cols = {'shoulder_elv_r', 'shoulder_elv_l', 'elv_angle_r', 'elv_angle_l'}

    header = (
        f"stoop_v5_armhang_no_coupler\nversion=1\nnRows={n}\n"
        f"nColumns={1+len(labels)}\ninDegrees=yes\n\n"
        "Units are S.I. units (angles in degrees).\n\nendheader\n"
        "time\t" + "\t".join(labels) + "\n"
    )

    with open(out_path, 'w') as f:
        f.write(header)
        for i in range(n):
            row = tbl.getRowAtIndex(i)
            vals = [f"{times[i]:.6f}"]
            for j, lab in enumerate(labels):
                v = float(row[j])
                if lab in zero_cols:
                    v = 0.0  # arm hanging
                vals.append(f"{v:.6f}")
            f.write("\t".join(vals) + "\n")

    log(f'  Arm-hang motion created: {out_path} ({n} frames)')
    log(f'  shoulder_elv_r/l and elv_angle_r/l set to 0 throughout')
    return out_path


def prepare_model(out_path, out_dir):
    keep = set()
    with open(PHASE1A_LIST) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            keep.add(s)

    import xml.etree.ElementTree as ET
    tree = ET.parse(SRC_NO_COUPLER)
    root = tree.getroot()
    removed = kept_mus = kept_other = 0
    MUSCLE_TYPES = {
        'Millard2012EquilibriumMuscle', 'Thelen2003Muscle',
        'DeGrooteFregly2016Muscle', 'ActivationFiberLengthMuscle',
        'Muscle', 'SimpleMuscle', 'RigidTendonMuscle'
    }
    for forceset in root.iter('ForceSet'):
        obj = forceset.find('objects')
        if obj is None:
            continue
        for child in list(obj):
            name = child.get('name')
            if name is None:
                continue
            if child.tag in MUSCLE_TYPES or 'Muscle' in child.tag:
                if name in keep:
                    kept_mus += 1
                else:
                    obj.remove(child)
                    removed += 1
            else:
                kept_other += 1
    tree.write(str(out_path), encoding='utf-8', xml_declaration=True)
    log(f'  Model: kept {kept_mus} muscles + {kept_other} forces, removed {removed}')
    shutil.copy(GRF_STO, Path(out_dir) / 'stoop_grf_v5.sto')
    grf_xml_dst = Path(out_dir) / 'stoop_grf_v5.xml'
    shutil.copy(GRF_XML, grf_xml_dst)
    return str(out_path), str(grf_xml_dst)


def prepare_reference_from_mot(mot_path, model_path, out_ref, t_start, t_end):
    """Convert motion (degrees) to radians reference for MocoInverse."""
    tbl = osim.TimeSeriesTable(mot_path)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    m = osim.Model(model_path)
    m.initSystem()
    cs = m.getCoordinateSet()
    is_rot = [cs.contains(L) and cs.get(L).getMotionType() == 1 for L in labels]

    # Check if inDegrees
    try:
        in_deg_str = tbl.getTableMetaDataAsString('inDegrees')
        in_degrees = (in_deg_str.lower() == 'yes')
    except Exception:
        in_degrees = True  # assume degrees if no key

    mask = (times >= t_start - 1e-9) & (times <= t_end + 1e-9)
    keep_idx = np.where(mask)[0]
    n = len(keep_idx)
    header = (
        f"stoop_v5_armhang_nc_ref\nversion=1\nnRows={n}\n"
        f"nColumns={1+len(labels)}\ninDegrees=no\n\n"
        "Units are S.I. units.\n\nendheader\n"
        "time\t" + "\t".join(labels) + "\n"
    )
    with open(out_ref, 'w') as f:
        f.write(header)
        for i in keep_idx:
            row = tbl.getRowAtIndex(int(i))
            vals = [f"{times[i]:.6f}"]
            for j, lab in enumerate(labels):
                v = float(row[j])
                if is_rot[j] and in_degrees:
                    v = np.radians(v)
                vals.append(f"{v:.6f}")
            f.write("\t".join(vals) + "\n")
    log(f'  Reference: {n} frames  t=[{times[keep_idx[0]]:.3f},{times[keep_idx[-1]]:.3f}]')
    return out_ref


def run_inverse(model_path, grf_xml, ref_path, t_start, t_end, mesh, sol_path):
    log('--- MocoInverse (V3_armhang: no_coupler + shoulder_elv=0) ---')
    inverse = osim.MocoInverse()
    inverse.setName('phase1a_v3_armhang')

    model_proc = osim.ModelProcessor(model_path)
    model_proc.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    model_proc.append(osim.ModOpIgnoreTendonCompliance())
    model_proc.append(osim.ModOpIgnorePassiveFiberForcesDGF())
    model_proc.append(osim.ModOpAddExternalLoads(grf_xml))
    model_proc.append(osim.ModOpAddReserves(RESERVE_OPTF))
    inverse.setModel(model_proc)

    inverse.setKinematics(osim.TableProcessor(str(ref_path)))
    inverse.set_initial_time(t_start)
    inverse.set_final_time(t_end)
    inverse.set_mesh_interval((t_end - t_start) / mesh)
    inverse.set_kinematics_allow_extra_columns(True)

    log(f'  Solving: t=[{t_start},{t_end}], mesh={mesh}, optF={RESERVE_OPTF}')
    t0 = time.time()
    sol = inverse.solve()
    t_elapsed = time.time() - t0
    moco_sol = sol.getMocoSolution()
    success = moco_sol.success()
    log(f'  Done: {t_elapsed:.1f}s  success={success}  status={moco_sol.getStatus()}')

    try:
        moco_sol.unseal()
    except Exception:
        pass
    moco_sol.write(str(sol_path))
    log(f'  Solution: {sol_path}')
    return moco_sol, t_elapsed


def extract_reserves(sto_path, label):
    if not os.path.exists(sto_path):
        return None
    tbl = osim.TimeSeriesTable(sto_path)
    labels = list(tbl.getColumnLabels())
    times = np.array(list(tbl.getIndependentColumn()))

    def get_max_abs(col):
        if col not in labels:
            return None
        idx = labels.index(col)
        vals = np.array([tbl.getRowAtIndex(i)[idx] for i in range(tbl.getNumRows())])
        return float(np.max(np.abs(vals))) * RESERVE_OPTF

    pt = get_max_abs('/forceset/reserve_jointset_ground_pelvis_pelvis_tilt')
    ty = get_max_abs('/forceset/reserve_jointset_ground_pelvis_pelvis_ty')

    spine_fe_cols = [l for l in labels
                     if '_FE' in l and 'reserve' in l.lower()
                     and 'ground_pelvis' not in l and 'Abs' not in l]
    t_idx = int(np.argmin(np.abs(times - 2.5))) if times[-1] >= 2.5 else len(times) - 1
    spine_fe_sum = sum(
        abs(tbl.getRowAtIndex(t_idx)[labels.index(c)]) * RESERVE_OPTF
        for c in spine_fe_cols
    )

    il_col = '/forceset/IL_R10_r/activation'
    il_max = None
    if il_col in labels:
        idx = labels.index(il_col)
        vals = np.array([tbl.getRowAtIndex(i)[idx] for i in range(tbl.getNumRows())])
        il_max = float(np.max(vals))

    print(f'\n[{label}]')
    print(f'  pelvis_tilt reserve: {pt:.2f} Nm (Hicks threshold: 12.9 Nm)')
    print(f'  pelvis_ty reserve:   {ty:.2f} N  (Hicks threshold: 36.8 N)')
    print(f'  Spine FE sum @ t~2.5s: {spine_fe_sum:.2f} Nm')
    print(f'  IL_R10_r peak: {il_max*100:.1f}%' if il_max else '  IL_R10_r: not found')
    pt_flag = 'PASS' if pt <= 12.9 else f'FAIL ({pt/12.9:.1f}x threshold)'
    print(f'  pelvis_tilt Hicks: {pt_flag}')
    return {'pelvis_tilt': pt, 'pelvis_ty': ty, 'spine_fe': spine_fe_sum, 'il_r10': il_max}


def main():
    log('=== Phase 3: pelvis_tilt root cause verification ===')
    log('Test: V3_armhang = no_coupler model + shoulder_elv=0 kinematics')

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    arm_hang_mot = OUT_DIR / 'stoop_v5_armhang.mot'
    model_path   = OUT_DIR / 'phase1a_model.osim'
    ref_path     = OUT_DIR / 'states_reference.sto'
    sol_path     = OUT_DIR / 'solution.sto'

    log('\nStep 1: Create arm-hang motion')
    create_arm_hang_motion(str(arm_hang_mot))

    log('\nStep 2: Prepare reduced no_coupler model')
    _, grf_xml = prepare_model(model_path, OUT_DIR)

    log('\nStep 3: Prepare kinematics reference')
    prepare_reference_from_mot(str(arm_hang_mot), str(model_path),
                                str(ref_path), T_START, T_END)

    log('\nStep 4: Run MocoInverse')
    moco_sol, t_el = run_inverse(
        str(model_path), grf_xml, str(ref_path),
        T_START, T_END, MESH, str(sol_path)
    )

    log('\n=== RESULTS COMPARISON ===')
    print('\nVariant                          | Shoulder_elv | pelvis_tilt reserve')
    print('                                 |              | (actual Nm)')
    print('-' * 75)

    # V3 original (with coupler-generated arm trajectory)
    r3 = extract_reserves(
        '/data/wearable-assist/results/phase1a_smoke_no_coupler/solution.sto',
        'V3 no_coupler + coupler-generated arm (72.9 deg)'
    )

    # V3_armhang (arm at 0 deg)
    r3h = extract_reserves(str(sol_path), 'V3_armhang + shoulder_elv=0 (arm hanging)')

    if r3 and r3h:
        delta = r3h['pelvis_tilt'] - r3['pelvis_tilt']
        print(f'\nDelta pelvis_tilt (armhang - orig): {delta:.2f} Nm')
        if r3h['pelvis_tilt'] <= 12.9:
            print('FINDING: Setting shoulder_elv=0 resolves pelvis_tilt anomaly')
            print('  Mechanism CONFIRMED: coupler-generated arm kinematics are the proximate cause')
            print('  Root cause: stoop_v5.mot was generated with couplers active')
        else:
            print(f'FINDING: shoulder_elv=0 does NOT fully resolve issue ({r3h["pelvis_tilt"]:.1f} Nm)')

    log('\n=== Phase 3 verification complete ===')
    log(f'Results: {OUT_DIR}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f'FATAL: {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)
