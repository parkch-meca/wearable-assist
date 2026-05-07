"""Phase 1a regression with Muscle Set v2 (114 + 44 lower limb = 158 muscles).

Validates that adding lower limb muscles:
  1. Does NOT significantly change ES (erector spinae) activation (max delta < 5 %p)
  2. REDUCES reserve pelvis_tilt, hip_flexion, knee_angle, ankle from baseline

Baseline: forearm_v1 smoke (pelvis_tilt reserve max=17.5 N·m, knee max=7.9 N·m)
Target (Phase 2.C.4 box): pelvis_tilt was 221 N·m → must be reduced

Usage:
  python run_moco_phase1a_v2_lower_limb.py smoke   # t=1.0-3.0, mesh=25 (~8-15 min)
  python run_moco_phase1a_v2_lower_limb.py full    # t=0.0-5.0, mesh=50 (~2-3 hr)
"""
import os, sys, time, shutil
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim
import sys
sys.path.insert(0, str(Path(__file__).parent))
from muscle_set_v2 import MUSCLE_SET_V2

SRC_MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim'
MOT       = '/data/stoop_motion/stoop_synthetic_v5.mot'
GRF_XML   = '/data/stoop_motion/stoop_grf_v5.xml'
GRF_STO   = '/data/stoop_motion/stoop_grf_v5.sto'

RESERVE_OPTF = 10.0


def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def prepare_model(out_path, keep_set):
    """Remove all muscles NOT in keep_set from source model XML."""
    import xml.etree.ElementTree as ET
    tree = ET.parse(SRC_MODEL)
    root = tree.getroot()
    MUSCLE_TYPES = {
        'Millard2012EquilibriumMuscle', 'Thelen2003Muscle',
        'DeGrooteFregly2016Muscle', 'ActivationFiberLengthMuscle',
        'Muscle', 'SimpleMuscle', 'RigidTendonMuscle'
    }
    removed = kept_mus = kept_other = 0
    for forceset in root.iter('ForceSet'):
        obj = forceset.find('objects')
        if obj is None:
            continue
        for child in list(obj):
            name = child.get('name')
            if name is None:
                continue
            if child.tag in MUSCLE_TYPES or 'Muscle' in child.tag:
                if name in keep_set:
                    kept_mus += 1
                else:
                    obj.remove(child)
                    removed += 1
            else:
                kept_other += 1

    tree.write(str(out_path), encoding='utf-8', xml_declaration=True)
    log(f'Model: kept {kept_mus} muscles + {kept_other} forces, removed {removed}')

    out_dir = Path(out_path).parent
    shutil.copy(GRF_STO, out_dir / 'stoop_grf_v5.sto')
    grf_xml_dst = out_dir / 'stoop_grf_v5.xml'
    shutil.copy(GRF_XML, grf_xml_dst)
    return str(out_path), str(grf_xml_dst)


def prepare_reference(out_path, t_start, t_end):
    """Convert .mot to radians STO for MocoInverse kinematics reference."""
    tbl = osim.TimeSeriesTable(MOT)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    m = osim.Model(SRC_MODEL)
    m.initSystem()
    cs = m.getCoordinateSet()
    is_rot = [cs.contains(L) and cs.get(L).getMotionType() == 1 for L in labels]
    mask = (times >= t_start - 1e-9) & (times <= t_end + 1e-9)
    keep = np.where(mask)[0]
    n = len(keep)
    header = (
        f"stoop_v5_phase1a_v2_lower_limb\nversion=1\nnRows={n}\n"
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
    log(f'Reference: {n} frames  t=[{times[keep[0]]:.3f},{times[keep[-1]]:.3f}]')
    return str(out_path)


def run_inverse(model_path, grf_xml, ref_path, t_start, t_end,
                mesh_intervals, solution_path):
    log('--- MocoInverse setup (v2 lower limb + GRF) ---')
    inverse = osim.MocoInverse()
    inverse.setName('phase1a_v2_lower_limb')

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

    log(f'Solving: t=[{t_start},{t_end}], mesh={mesh_intervals}, reserve_optF={RESERVE_OPTF}')
    t0 = time.time()
    sol = inverse.solve()
    t_elapsed = time.time() - t0
    moco_sol = sol.getMocoSolution()
    success = moco_sol.success()
    log(f'Solve done in {t_elapsed:.1f}s  success={success}  status={moco_sol.getStatus()}')

    try:
        moco_sol.unseal()
    except Exception:
        pass
    moco_sol.write(str(solution_path))
    log(f'Solution written: {solution_path}')
    return moco_sol, t_elapsed


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'smoke'
    if mode == 'smoke':
        t_start, t_end = 1.0, 3.0
        mesh = 25
        out_root = Path('/data/opensim_results/phase1a_v2_lower_limb/smoke')
    elif mode == 'full':
        t_start, t_end = 0.0, 5.0
        mesh = 50
        out_root = Path('/data/opensim_results/phase1a_v2_lower_limb/full')
    else:
        log(f'Unknown mode: {mode}  (use smoke or full)')
        sys.exit(2)

    out_root.mkdir(parents=True, exist_ok=True)
    keep_set = set(MUSCLE_SET_V2)
    log(f'=== Phase 1a v2 lower_limb  mode={mode}  muscles={len(keep_set)} ===')

    model_path = out_root / 'phase1a_v2_model.osim'
    ref_path   = out_root / 'states_reference.sto'
    sol_path   = out_root / 'solution.sto'

    log('Step 1: prepare model')
    model_path_str, grf_xml = prepare_model(model_path, keep_set)

    log('Step 2: prepare reference kinematics')
    prepare_reference(ref_path, t_start, t_end)

    log('Step 3: MocoInverse solve')
    sol, t_el = run_inverse(model_path_str, grf_xml, str(ref_path),
                            t_start, t_end, mesh, str(sol_path))

    log(f'=== DONE  t_elapsed={t_el:.1f}s  success={sol.success()} ===')
    log(f'Output: {out_root}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f'FATAL: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
