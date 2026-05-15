"""Step A.2 — Variation Matrix: 4 model variants, Phase 1a Stoop smoke solve.

Variants:
  V1: original with_coupler, no_forearm  (result EXISTS: phase1a_full/solution.sto)
  V2: with_coupler + forearm_v1          (NEW solve needed)
  V3: no_coupler, no_forearm             (result EXISTS: phase1a_smoke_no_coupler/)
  V4: no_coupler + forearm_v1 (current)  (result EXISTS: phase1a_smoke_forearm_v1/)

Purpose: isolate contribution of coupler removal vs forearm_v1 to
  pelvis_tilt reserve 175.57 Nm anomaly.

Usage:
  /home/sysop/miniconda3/envs/opensim/bin/python run_variation_matrix_phase1a.py
  # runs only V2 (V1, V3, V4 already have results)

Output:
  /data/opensim_results/variation_matrix_phase1a/V2/solution.sto
  /data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/step_a2/variation_matrix_results.md
"""
import os, sys, time, shutil
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim

# ── paths ──────────────────────────────────────────────────────────────────
MOT         = '/data/stoop_motion/stoop_synthetic_v5.mot'
GRF_XML     = '/data/stoop_motion/stoop_grf_v5.xml'
GRF_STO     = '/data/stoop_motion/stoop_grf_v5.sto'
PHASE1A_LIST = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/phase1a_muscle_list.txt'

# V2: with_coupler (moco_stoop) + forearm_v1
# moco_stoop model = WeldJoint variant of modified (used for Phase 1a)
# forearm_v1 applied on top of no_coupler; we need a with_coupler + forearm_v1 variant
SRC_WITH_COUPLER_MOCO = (
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
    'MaleFullBodyModel_v2.0_OS4_moco_stoop.osim'
)
SRC_FOREARM_V1_NO_COUPLER = (
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
    'MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim'
)

OUT_V2_MODEL = (
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
    'MaleFullBodyModel_v2.0_OS4_moco_stoop_forearm_v1.osim'
)
OUT_V2_RESULTS = '/data/opensim_results/variation_matrix_phase1a/V2'

RESERVE_OPTF = 10.0
T_START, T_END = 1.0, 3.0
MESH = 25  # smoke: 2 s window / 25 intervals


def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


# ── Step 1: Create V2 model (with_coupler + forearm_v1) ───────────────────
def create_v2_model():
    """Apply forearm_v1 modification to with_coupler moco_stoop model.

    The forearm_v1 mod: radius_hand_r/l joint parent-frame Y offset
    changed from -0.242 m to -0.434 m (adds 19.2 cm hand segment).
    We read both models in XML and transplant the modified joint offsets.
    """
    import xml.etree.ElementTree as ET

    log('Creating V2 model: with_coupler + forearm_v1')

    if os.path.exists(OUT_V2_MODEL):
        log(f'  V2 model already exists: {OUT_V2_MODEL}')
        return OUT_V2_MODEL

    # Parse both models
    tree_base = ET.parse(SRC_WITH_COUPLER_MOCO)
    root_base = tree_base.getroot()
    tree_fa   = ET.parse(SRC_FOREARM_V1_NO_COUPLER)
    root_fa   = tree_fa.getroot()

    # Find radius_hand_r and radius_hand_l parent frame transforms
    # in forearm_v1 model
    def find_joint_parent_frame(root, joint_name):
        """Return the PhysicalOffsetFrame element that is the parent frame of joint."""
        for jt in root.iter('CustomJoint'):
            if jt.get('name') == joint_name:
                pf = jt.find('.//frames/PhysicalOffsetFrame')
                if pf is not None:
                    return pf
        return None

    def find_joint_in_jointset(root, joint_name):
        """Find joint element by name in JointSet."""
        for jset in root.iter('JointSet'):
            obj = jset.find('objects')
            if obj is None:
                continue
            for child in obj:
                if child.get('name') == joint_name:
                    return child
        return None

    joints_to_copy = ['radius_hand_r', 'radius_hand_l']

    for jname in joints_to_copy:
        src_joint = find_joint_in_jointset(root_fa, jname)
        dst_joint = find_joint_in_jointset(root_base, jname)
        if src_joint is None or dst_joint is None:
            log(f'  WARNING: could not find joint {jname} in one of the models')
            continue

        # Extract parent frame translation from source (forearm_v1)
        # and copy to destination (with_coupler)
        src_frames = src_joint.find('.//frames')
        dst_frames = dst_joint.find('.//frames')

        if src_frames is None or dst_frames is None:
            log(f'  WARNING: frames not found for {jname}')
            continue

        # Get all PhysicalOffsetFrame elements
        src_pofs = src_frames.findall('PhysicalOffsetFrame')
        dst_pofs = dst_frames.findall('PhysicalOffsetFrame')

        # Match by name (parent frame has parent body name)
        src_pof_map = {pof.get('name'): pof for pof in src_pofs}
        dst_pof_map = {pof.get('name'): pof for pof in dst_pofs}

        copied = 0
        for name, src_pof in src_pof_map.items():
            if name in dst_pof_map:
                dst_pof = dst_pof_map[name]
                # Copy translation
                src_trans = src_pof.find('.//translation')
                dst_trans = dst_pof.find('.//translation')
                if src_trans is not None and dst_trans is not None:
                    old_val = dst_trans.text
                    dst_trans.text = src_trans.text
                    log(f'    {jname} frame {name}: translation {old_val} -> {src_trans.text}')
                    copied += 1

        if copied == 0:
            log(f'  WARNING: no translations copied for {jname}')
        else:
            log(f'  {jname}: copied {copied} frame translation(s)')

    tree_base.write(OUT_V2_MODEL, encoding='utf-8', xml_declaration=True)
    log(f'  Saved V2 model: {OUT_V2_MODEL}')

    # Quick validation: load and initSystem
    m = osim.Model(OUT_V2_MODEL)
    state = m.initSystem()
    cs = m.getConstraintSet()
    log(f'  initSystem OK — constraints: {cs.getSize()} (expect 4 for with_coupler)')

    # Check coupler still present
    coupler_names = [cs.get(i).getName() for i in range(cs.getSize())]
    log(f'  Constraints: {coupler_names}')

    # Check hand_R position at standing
    m.realizePosition(state)
    hand_r = m.getBodySet().get('hand_R').getPositionInGround(state)
    hand_l = m.getBodySet().get('hand_L').getPositionInGround(state)
    log(f'  hand_R standing: ({hand_r[0]:.3f}, {hand_r[1]:.3f}, {hand_r[2]:.3f})')
    log(f'  hand_L standing: ({hand_l[0]:.3f}, {hand_l[1]:.3f}, {hand_l[2]:.3f})')

    return OUT_V2_MODEL


# ── Step 2: Prepare reduced model (114 muscles) ───────────────────────────
def prepare_model(src_model, out_path, out_dir):
    keep = set()
    with open(PHASE1A_LIST) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            keep.add(s)

    import xml.etree.ElementTree as ET
    tree = ET.parse(src_model)
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


# ── Step 3: Prepare kinematics reference ──────────────────────────────────
def prepare_reference(src_model, out_path, t_start, t_end):
    tbl = osim.TimeSeriesTable(MOT)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    m = osim.Model(src_model)
    m.initSystem()
    cs = m.getCoordinateSet()
    is_rot = [cs.contains(L) and cs.get(L).getMotionType() == 1 for L in labels]
    mask = (times >= t_start - 1e-9) & (times <= t_end + 1e-9)
    keep = np.where(mask)[0]
    n = len(keep)
    header = (
        f"stoop_v5_phase1a_v2_with_coupler_forearm_v1\nversion=1\nnRows={n}\n"
        f"nColumns={1+len(labels)}\ninDegrees=no\n\n"
        "Units are S.I. units.\n\nendheader\n"
        "time\t" + "\t".join(labels) + "\n"
    )
    with open(out_path, 'w') as f:
        f.write(header)
        for i in keep:
            row = tbl.getRowAtIndex(int(i))
            vals = [f"{times[i]:.6f}"]
            for j, lab in enumerate(labels):
                v = row[j]
                if is_rot[j]:
                    v = np.radians(v)
                vals.append(f"{v:.6f}")
            f.write("\t".join(vals) + "\n")
    log(f'  Reference: {n} frames  t=[{times[keep[0]]:.3f},{times[keep[-1]]:.3f}]')
    return out_path


# ── Step 4: MocoInverse solve ─────────────────────────────────────────────
def run_inverse(model_path, grf_xml, ref_path, t_start, t_end,
                mesh_intervals, solution_path):
    log('--- MocoInverse setup (V2: with_coupler + forearm_v1) ---')
    inverse = osim.MocoInverse()
    inverse.setName('phase1a_v2_with_coupler_forearm_v1')

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
    inverse.set_mesh_interval((t_end - t_start) / mesh_intervals)
    inverse.set_kinematics_allow_extra_columns(True)

    log(f'  Solving: t=[{t_start},{t_end}], mesh={mesh_intervals}, optF={RESERVE_OPTF}')
    t0 = time.time()
    sol = inverse.solve()
    t_elapsed = time.time() - t0
    moco_sol = sol.getMocoSolution()
    success = moco_sol.success()
    log(f'  Solve done in {t_elapsed:.1f}s  success={success}  status={moco_sol.getStatus()}')

    try:
        moco_sol.unseal()
    except Exception:
        pass
    moco_sol.write(str(solution_path))
    log(f'  Solution written: {solution_path}')
    return moco_sol, t_elapsed


# ── Step 5: Extract reserves from solution ────────────────────────────────
def extract_reserves(sto_path, label, t_ref=2.5):
    """Return dict of key reserve metrics."""
    if not os.path.exists(sto_path):
        return {'label': label, 'error': 'file not found'}

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
    t_idx = int(np.argmin(np.abs(times - t_ref))) if times[-1] >= t_ref else len(times) - 1
    spine_fe_sum = 0.0
    for c in spine_fe_cols:
        idx = labels.index(c)
        spine_fe_sum += abs(tbl.getRowAtIndex(t_idx)[idx]) * RESERVE_OPTF

    il_col = '/forceset/IL_R10_r/activation'
    il_max = None
    if il_col in labels:
        idx = labels.index(il_col)
        vals = np.array([tbl.getRowAtIndex(i)[idx] for i in range(tbl.getNumRows())])
        il_max = float(np.max(vals))

    return {
        'label': label,
        'pelvis_tilt_nm': pt,
        'pelvis_ty_n': ty,
        'spine_fe_nm': spine_fe_sum,
        'il_r10_r': il_max,
    }


# ── Step 6: Print variation matrix table ─────────────────────────────────
def print_table(results):
    print()
    print('=' * 90)
    print('VARIATION MATRIX — pelvis_tilt 175 Nm Root Cause Analysis')
    print('=' * 90)
    print(f'{"Variant":<35} {"Coupler":>8} {"Forearm":>8} {"PT reserve(Nm)":>16}'
          f' {"PY reserve(N)":>14} {"SpineFE(Nm)":>12} {"IL_R10_r":>10}')
    print('-' * 90)

    HICKS_PT = 12.9   # Nm
    HICKS_TY = 36.8   # N

    variant_specs = [
        ('V1 original',      True,  False),
        ('V2 forearm_only',  True,  True),
        ('V3 no_coupler',    False, False),
        ('V4 current',       False, True),
    ]

    for r in results:
        spec = next((s for s in variant_specs if s[0].split()[0] == r['label'].split()[0]), None)
        coupler = 'yes' if spec and spec[1] else 'no'
        forearm = 'yes' if spec and spec[2] else 'no'
        pt  = r.get('pelvis_tilt_nm')
        ty  = r.get('pelvis_ty_n')
        sfe = r.get('spine_fe_nm')
        il  = r.get('il_r10_r')

        pt_str  = f'{pt:.2f}' if pt is not None else 'n/a'
        ty_str  = f'{ty:.2f}' if ty is not None else 'n/a'
        sfe_str = f'{sfe:.2f}' if sfe is not None else 'n/a'
        il_str  = f'{il*100:.1f}%' if il is not None else 'n/a'

        pt_flag  = '*** FAIL' if pt  is not None and pt  > HICKS_PT else ''
        ty_flag  = ' FAIL' if ty is not None and ty > HICKS_TY else ''

        print(f'{r["label"]:<35} {coupler:>8} {forearm:>8} {pt_str:>14}{pt_flag}'
              f'  {ty_str:>10}{ty_flag}  {sfe_str:>10}  {il_str:>8}')

    print('-' * 90)
    print(f'Hicks 2015 thresholds: PT < {HICKS_PT} Nm  |  PY < {HICKS_TY} N')
    print('=' * 90)
    print()

    # Root cause analysis
    v_map = {r['label'].split()[0]: r for r in results}
    v1 = v_map.get('V1')
    v2 = v_map.get('V2')
    v3 = v_map.get('V3')
    v4 = v_map.get('V4')

    if all(v is not None for v in [v1, v2, v3, v4]):
        pt1 = v1['pelvis_tilt_nm'] or 0
        pt2 = v2['pelvis_tilt_nm'] or 0
        pt3 = v3['pelvis_tilt_nm'] or 0
        pt4 = v4['pelvis_tilt_nm'] or 0
        print('ROOT CAUSE ANALYSIS:')
        print(f'  D_forearm = V2 - V1 = {pt2-pt1:.2f} Nm  (forearm_v1 alone, with coupler)')
        print(f'  D_nocoupler = V3 - V1 = {pt3-pt1:.2f} Nm  (no_coupler alone, no forearm)')
        print(f'  D_interaction = V4 - V3 - V2 + V1 = {pt4-pt3-pt2+pt1:.2f} Nm')
        print(f'  Total delta V4-V1 = {pt4-pt1:.2f} Nm')
        nocoupler_frac = (pt3 - pt1) / (pt4 - pt1) * 100 if (pt4 - pt1) > 0 else 0
        forearm_frac   = (pt2 - pt1) / (pt4 - pt1) * 100 if (pt4 - pt1) > 0 else 0
        print(f'  no_coupler fraction: {nocoupler_frac:.1f}%')
        print(f'  forearm_v1 fraction: {forearm_frac:.1f}%')

        dominant = 'no_coupler' if nocoupler_frac > 50 else 'forearm_v1'
        print(f'  --> Dominant cause: {dominant}')
    print()


# ── main ──────────────────────────────────────────────────────────────────
def main():
    log('=== Step A.2: Variation Matrix ===')
    log('V1, V3, V4 use existing results. V2 requires new solve.')

    # ── V2 solve ──────────────────────────────────────────────────────────
    out_dir = Path(OUT_V2_RESULTS)
    out_dir.mkdir(parents=True, exist_ok=True)

    v2_model_full = create_v2_model()
    v2_model_reduced = out_dir / 'phase1a_model.osim'
    v2_ref   = out_dir / 'states_reference.sto'
    v2_sol   = out_dir / 'solution.sto'

    log('\n--- V2: Preparing reduced model ---')
    _, grf_xml = prepare_model(v2_model_full, v2_model_reduced, out_dir)

    log('--- V2: Preparing kinematics reference ---')
    prepare_reference(str(v2_model_reduced), str(v2_ref), T_START, T_END)

    log('--- V2: Running MocoInverse ---')
    moco_sol, t_el = run_inverse(
        str(v2_model_reduced), grf_xml, str(v2_ref),
        T_START, T_END, MESH, str(v2_sol)
    )
    log(f'V2 solve: {t_el:.1f}s  success={moco_sol.success()}')

    # ── Collect all results ───────────────────────────────────────────────
    log('\n--- Collecting reserves from all variants ---')
    results = []

    # V1: original Phase 1a full (t_ref = 2.5 within range)
    r1 = extract_reserves('/data/wearable-assist/results/phase1a_full/solution.sto',
                          'V1 original (full)')
    results.append(r1)

    # V2: just solved
    r2 = extract_reserves(str(v2_sol), 'V2 forearm_only (smoke)')
    results.append(r2)

    # V3: existing smoke (t_ref adjusted to 2.5 but range is 1-3, so will use t=2.48)
    r3 = extract_reserves('/data/wearable-assist/results/phase1a_smoke_no_coupler/solution.sto',
                          'V3 no_coupler (smoke)')
    results.append(r3)

    # V4: existing forearm_v1 smoke
    r4 = extract_reserves('/data/wearable-assist/results/phase1a_smoke_forearm_v1/solution.sto',
                          'V4 current (smoke)')
    results.append(r4)

    print_table(results)

    # Print for each
    for r in results:
        log(f"{r['label']}: PT={r.get('pelvis_tilt_nm','n/a'):.3f} Nm  "
            f"PY={r.get('pelvis_ty_n','n/a'):.3f} N  "
            f"SpineFE={r.get('spine_fe_nm','n/a'):.3f} Nm  "
            f"IL_R10_r={r.get('il_r10_r','n/a')}")

    log('\n=== Step A.2 Variation Matrix DONE ===')
    log(f'V2 results: {OUT_V2_RESULTS}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f'FATAL: {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)
