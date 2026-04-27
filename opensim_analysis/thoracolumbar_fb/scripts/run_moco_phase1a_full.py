"""Phase 1a Full — MocoInverse with GRF on stoop_v5 t=0..5 s, mesh=50.

Adds external GRF loads (stoop_grf_v5.xml/sto) to remove pelvis_ty reserve
artefact (smoke had ~800 N pelvis_ty reserve substituting floor reaction).

Two modes:
  python run_moco_phase1a_full.py smoke   # t=1.0-3.0, mesh=25 (re-verifies GRF)
  python run_moco_phase1a_full.py full    # t=0.0-5.0, mesh=50 (production)
"""
import os, sys, time, shutil
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim

SRC_MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_moco_stoop.osim'
MOT = '/data/stoop_motion/stoop_synthetic_v5.mot'
GRF_XML = '/data/stoop_motion/stoop_grf_v5.xml'
GRF_STO = '/data/stoop_motion/stoop_grf_v5.sto'
PHASE1A_LIST = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/phase1a_muscle_list.txt'

RESERVE_OPTF = 10.0


def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def load_phase1a_set():
    names = set()
    with open(PHASE1A_LIST) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith('#'): continue
            names.add(s)
    return names


def prepare_model(out_path):
    """XML strip 506 muscles outside Phase 1a; copy GRF files next to model."""
    keep = load_phase1a_set()
    import xml.etree.ElementTree as ET
    tree = ET.parse(SRC_MODEL); root = tree.getroot()
    removed = kept_mus = kept_other = 0
    MUSCLE_TYPES = {'Millard2012EquilibriumMuscle','Thelen2003Muscle',
                    'DeGrooteFregly2016Muscle','ActivationFiberLengthMuscle',
                    'Muscle','SimpleMuscle','RigidTendonMuscle'}
    for forceset in root.iter('ForceSet'):
        obj = forceset.find('objects')
        if obj is None: continue
        for child in list(obj):
            name = child.get('name')
            if name is None: continue
            if child.tag in MUSCLE_TYPES or 'Muscle' in child.tag:
                if name in keep: kept_mus += 1
                else: obj.remove(child); removed += 1
            else:
                kept_other += 1
    tree.write(str(out_path), encoding='utf-8', xml_declaration=True)
    log(f'Model: kept {kept_mus} muscles + {kept_other} forces, removed {removed}')

    # Copy GRF files into the model directory so ExternalLoads finds them
    out_dir = Path(out_path).parent
    shutil.copy(GRF_STO, out_dir / 'stoop_grf_v5.sto')
    grf_xml_dst = out_dir / 'stoop_grf_v5.xml'
    shutil.copy(GRF_XML, grf_xml_dst)
    return out_path, str(grf_xml_dst)


def prepare_reference(out_path, t_start, t_end):
    tbl = osim.TimeSeriesTable(MOT)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    m = osim.Model(SRC_MODEL); m.initSystem()
    cs = m.getCoordinateSet()
    is_rot = [cs.contains(L) and cs.get(L).getMotionType() == 1 for L in labels]
    mask = (times >= t_start - 1e-9) & (times <= t_end + 1e-9)
    keep = np.where(mask)[0]
    n = len(keep)
    header = (f"stoop_v5_phase1a\nversion=1\nnRows={n}\n"
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
    log(f'Reference: {n} frames  t=[{times[keep[0]]:.3f},{times[keep[-1]]:.3f}]')
    return out_path


def run_inverse(model_path, grf_xml, ref_path, t_start, t_end,
                mesh_intervals, solution_path):
    log('--- MocoInverse setup with GRF ---')
    inverse = osim.MocoInverse()
    inverse.setName('phase1a_full')

    model_proc = osim.ModelProcessor(model_path)
    model_proc.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    model_proc.append(osim.ModOpIgnoreTendonCompliance())
    model_proc.append(osim.ModOpIgnorePassiveFiberForcesDGF())
    # ADD GRF before adding reserves
    model_proc.append(osim.ModOpAddExternalLoads(grf_xml))
    model_proc.append(osim.ModOpAddReserves(RESERVE_OPTF))
    inverse.setModel(model_proc)

    inverse.setKinematics(osim.TableProcessor(str(ref_path)))
    inverse.set_initial_time(t_start); inverse.set_final_time(t_end)
    inverse.set_mesh_interval((t_end - t_start) / mesh_intervals)
    inverse.set_kinematics_allow_extra_columns(True)

    log(f'Solving: t=[{t_start},{t_end}], mesh={mesh_intervals}, optF={RESERVE_OPTF}')
    t0 = time.time()
    sol = inverse.solve()
    t_elapsed = time.time() - t0
    moco_sol = sol.getMocoSolution()
    success = moco_sol.success()
    log(f'Solve done in {t_elapsed:.1f}s  success={success}  status={moco_sol.getStatus()}')

    try: moco_sol.unseal()
    except Exception: pass
    moco_sol.write(str(solution_path))
    return moco_sol, t_elapsed


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'smoke'
    if mode == 'smoke':
        t_start, t_end = 1.0, 3.0
        mesh = 25
        out_root = Path('/data/wearable-assist/results/phase1a_smoke_grf')
    elif mode == 'full':
        t_start, t_end = 0.0, 5.0
        mesh = 50
        out_root = Path('/data/wearable-assist/results/phase1a_full')
    else:
        log(f'Unknown mode: {mode}'); sys.exit(2)
    out_root.mkdir(parents=True, exist_ok=True)

    model_path = out_root / 'phase1a_model.osim'
    ref_path   = out_root / 'states_reference.sto'
    sol_path   = out_root / 'solution.sto'

    log(f'=== mode={mode}  t=[{t_start},{t_end}]  mesh={mesh} ===')
    log('Step 1: prepare model + GRF')
    _, grf_xml = prepare_model(model_path)
    log('Step 2: prepare reference')
    prepare_reference(ref_path, t_start, t_end)
    log('Step 3: solve')
    sol, t_el = run_inverse(str(model_path), grf_xml, str(ref_path),
                            t_start, t_end, mesh, str(sol_path))
    log(f'TOTAL: {t_el:.1f}s  success={sol.success()}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f'FATAL: {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)
