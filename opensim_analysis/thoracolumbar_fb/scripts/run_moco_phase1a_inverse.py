"""Phase 1a smoke v2 — MocoInverse on stoop_v5 (t=1.0–3.0 s) with 114 muscles.

Rationale (see docs/smoke_test_v1_diagnosis.md):
  MocoTrack smoke v1 oscillated because its Pareto front had no interior
  point — tracking demanded a moment that muscles cannot produce (saturate),
  and reserves (w=100) were too expensive to absorb the rest. MocoInverse
  eliminates this trade-off by PRESCRIBING the kinematics; only muscle +
  reserve controls remain free. Reserves optF = 10 Nm (SO R10 equivalent)
  makes them structurally expensive so muscles are preferred.

Config:
  - model          : MaleFullBodyModel_v2.0_OS4_moco_stoop.osim
  - muscles        : 114 Phase 1a subset (other 506 removed via XML)
  - reference mot  : stoop_synthetic_v5.mot trimmed to 1.0-3.0 s (rad)
  - mesh intervals : 25
  - reserves       : 10 Nm optimalForce (non-pelvis rotational)
  - effort cost    : default MocoControlGoal (weight 1)
  - max iter       : 500
"""
import os, sys, time
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim

SRC_MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_moco_stoop.osim'
MOT = '/data/stoop_motion/stoop_synthetic_v5.mot'
PHASE1A_LIST = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/phase1a_muscle_list.txt'
OUT_ROOT = Path('/data/wearable-assist/results/phase1a_inverse'); OUT_ROOT.mkdir(parents=True, exist_ok=True)

T_START, T_END = 1.0, 3.0
MESH_INTERVALS = 25
MAX_ITER = 500
RESERVE_OPTF = 10.0   # SO R10 equivalent


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
    """XML-edit: remove muscles not in Phase 1a from forceset."""
    keep = load_phase1a_set()
    import xml.etree.ElementTree as ET
    tree = ET.parse(SRC_MODEL)
    root = tree.getroot()
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
                if name in keep:
                    kept_mus += 1
                else:
                    obj.remove(child); removed += 1
            else:
                kept_other += 1
    tree.write(str(out_path), encoding='utf-8', xml_declaration=True)
    m2 = osim.Model(str(out_path)); m2.initSystem()
    log(f'Model: kept {kept_mus} muscles + {kept_other} forces, removed {removed}.')
    log(f'  Reload: muscles={m2.getMuscles().getSize()}, forces={m2.getForceSet().getSize()}')
    return out_path


def prepare_reference(out_path):
    tbl = osim.TimeSeriesTable(MOT)
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    m = osim.Model(SRC_MODEL); m.initSystem()
    cs = m.getCoordinateSet()
    is_rot = []
    for lab in labels:
        is_rot.append(cs.contains(lab) and cs.get(lab).getMotionType() == 1)

    mask = (times >= T_START - 1e-9) & (times <= T_END + 1e-9)
    keep = np.where(mask)[0]
    n = len(keep)
    header = (f"stoop_v5_phase1a_inv\nversion=1\nnRows={n}\n"
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


def run_inverse(model_path, ref_path, solution_path):
    log('--- MocoInverse setup ---')
    inverse = osim.MocoInverse()
    inverse.setName('phase1a_inverse')

    # ModelProcessor: DeGrooteFregly2016 muscles + rigid tendon +
    # ignore passive fibers + reserves at 10 Nm.
    model_proc = osim.ModelProcessor(model_path)
    model_proc.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    model_proc.append(osim.ModOpIgnoreTendonCompliance())
    model_proc.append(osim.ModOpIgnorePassiveFiberForcesDGF())
    model_proc.append(osim.ModOpAddReserves(RESERVE_OPTF))
    inverse.setModel(model_proc)

    # Kinematics (will be prescribed — treated as equality constraint)
    table_proc = osim.TableProcessor(str(ref_path))
    inverse.setKinematics(table_proc)

    inverse.set_initial_time(T_START)
    inverse.set_final_time(T_END)
    inverse.set_mesh_interval((T_END - T_START) / MESH_INTERVALS)
    inverse.set_kinematics_allow_extra_columns(True)

    log('Solving (MocoInverse, mesh_interval=%.4f, reserves optF=%.1f Nm)...'
        % ((T_END-T_START)/MESH_INTERVALS, RESERVE_OPTF))
    t0 = time.time()
    sol = inverse.solve()
    t_elapsed = time.time() - t0

    moco_sol = sol.getMocoSolution()
    success = moco_sol.success()
    status = moco_sol.getStatus()
    log(f'Solve done in {t_elapsed:.1f}s  success={success}  status={status}')

    try:
        moco_sol.unseal()
    except Exception:
        pass
    moco_sol.write(str(solution_path))
    return moco_sol, t_elapsed


def analyze(solution_path, report_path, t_elapsed, moco_sol):
    """Extract ES peaks, reserve usage, eccentric/concentric asymmetry."""
    log('--- Analyzing solution ---')
    tbl = osim.TimeSeriesTable(str(solution_path))
    times = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())
    n = tbl.getNumRows(); m = tbl.getNumColumns()
    data = np.zeros((n, m))
    for i in range(n):
        r = tbl.getRowAtIndex(i)
        for j in range(m):
            data[i, j] = r[j]

    # Helper: find activation column for muscle name
    def col_for(muscle_name):
        targets = [f'/forceset/{muscle_name}/activation',
                   f'/forceset/{muscle_name}']
        for t in targets:
            for i, L in enumerate(labels):
                if L.endswith(t) or L == t or L == muscle_name:
                    return data[:, i], L
        return None, None

    # Key muscles (align with SO report convention)
    key = ['IL_R10_r','IL_R11_r','IL_R12_r','IL_R10_l','IL_R11_l','IL_R12_l',
           'LTpT_T11_r','LTpT_T12_r','LTpT_R11_r','LTpT_R12_r',
           'LTpL_L5_r','LTpL_L4_r',
           'QL_post_I_2-L4_r','QL_post_I_2-L3_r',
           'rect_abd_r','rect_abd_l']
    peaks = {}
    t233_vals = {}
    ecc_vals = {}  # mean over t in [1.0, 2.0]
    con_vals = {}  # mean over t in [2.0, 3.0]
    idx_233 = int(np.argmin(np.abs(times - 2.333)))
    mask_ecc = (times >= 1.0) & (times <= 2.0)
    mask_con = (times >= 2.0) & (times <= 3.0)
    for name in key:
        c, lab = col_for(name)
        if c is None:
            continue
        peaks[name] = float(np.max(c)) * 100
        t233_vals[name] = float(c[idx_233]) * 100
        if mask_ecc.sum() > 0: ecc_vals[name] = float(c[mask_ecc].mean()) * 100
        if mask_con.sum() > 0: con_vals[name] = float(c[mask_con].mean()) * 100

    # Reserves
    reserve_cols = [(i, L) for i, L in enumerate(labels) if 'reserve_' in L]
    spine_reserve_prefixes = ('reserve_L','reserve_T','reserve_Abs')
    spine_at_233 = 0.0
    reserve_sums_over_time = []
    for i, L in reserve_cols:
        pass
    # Reserve generated Nm = control × optF (optF = 10 Nm for non-pelvis rot)
    total_at_233 = 0.0
    spine_at_233_only = 0.0
    for i, L in reserve_cols:
        gen = abs(data[idx_233, i]) * RESERVE_OPTF
        total_at_233 += gen
        # Extract coord name from reserve path (e.g. /forceset/reserve_L5_S1_FE)
        name = L.split('/')[-1] if '/' in L else L
        # Strip trailing /activation if state path
        if name.startswith('reserve_'):
            coord = name.replace('reserve_', '')
            if any(coord.startswith(p) for p in ['L5_','L4_','L3_','L2_','L1_','T12_','T11_','T10_']):
                if 'FE' in coord:
                    spine_at_233_only += gen

    # Report
    lines = [
        f'# Phase 1a smoke v2 (MocoInverse) — Report', '',
        f'- Wall time: **{t_elapsed:.1f} s** ({t_elapsed/60:.1f} min)',
        f'- IPOPT status: **{moco_sol.getStatus()}**',
        f'- Success: **{moco_sol.success()}**',
        f'- Solution cols: {m}   time pts: {n}',
        '',
        '## Config',
        f'- MocoInverse, mesh_intervals={MESH_INTERVALS}',
        f'- Reserves optF={RESERVE_OPTF} Nm (non-pelvis rotational)',
        f'- Muscles: 114 (Phase 1a subset, DeGrooteFregly2016 + rigid tendon)',
        '',
        '## Key muscle activations',
        '',
        '| Muscle | peak (%) | @ t=2.333 s (%) | ecc mean (%) | con mean (%) |',
        '|---|---:|---:|---:|---:|',
    ]
    for name in key:
        if name in peaks:
            lines.append(f'| {name} | {peaks[name]:.1f} | {t233_vals.get(name,float("nan")):.1f} | '
                         f'{ecc_vals.get(name,float("nan")):.1f} | {con_vals.get(name,float("nan")):.1f} |')

    lines += [
        '',
        '## Reserve usage (at t=2.33 s)',
        f'- Reserve columns detected: {len(reserve_cols)}',
        f'- **Spine FE reserve sum**: {spine_at_233_only:.1f} Nm',
        f'- Total all reserves: {total_at_233:.1f} Nm',
        f'- Compare SO: R100=413, R50=209, R10=22 Nm (spine FE)',
        '',
        '## Eccentric (t=1-2 s) vs concentric (t=2-3 s) asymmetry',
    ]
    for name in key:
        if name in ecc_vals and name in con_vals:
            asym = (con_vals[name] - ecc_vals[name])
            sign = '↑' if asym > 0 else ('↓' if asym < 0 else '=')
            lines.append(f'- {name}: ecc {ecc_vals[name]:.1f}% / con {con_vals[name]:.1f}% {sign}{abs(asym):.1f}%p')

    # S1-S5 judgment
    max_peak_il_r11 = peaks.get('IL_R11_r', 0)
    n_in_band = sum(1 for v in peaks.values() if 40 <= v <= 100)
    has_asym = any(abs(con_vals.get(k,0) - ecc_vals.get(k,0)) > 2 for k in peaks.keys())

    lines += ['',
              '## S1–S5 smoke-test pass/fail',
              '',
              f'- **S1 IPOPT converged**: {"✅" if moco_sol.success() else "❌"}',
              f'- **S2 ES peak 40–100% (any muscle)**: {"✅" if n_in_band > 0 else "❌"}  ({n_in_band} muscles in band)',
              f'- **S3 Spine FE reserve < 50 Nm @ t=2.33**: {"✅" if spine_at_233_only < 50 else "❌"}  ({spine_at_233_only:.1f} Nm)',
              f'- **S4 Ecc ≠ Con asymmetry observed**: {"✅" if has_asym else "❌"}',
              f'- **S5 IL_R11_r peak range 80–100%**: {"✅" if 80 <= max_peak_il_r11 <= 100 else "❌"}  ({max_peak_il_r11:.1f}%)',
              ]
    Path(report_path).write_text('\n'.join(lines))
    log(f'Report written to {report_path}')
    return {
        'success': moco_sol.success(),
        'status': moco_sol.getStatus(),
        't_elapsed': t_elapsed,
        'il_r11_r_peak': max_peak_il_r11,
        'spine_reserve_at_233': spine_at_233_only,
        'has_asymmetry': has_asym,
    }


def main():
    t0 = time.time()
    model_path = OUT_ROOT / 'phase1a_model.osim'
    ref_path   = OUT_ROOT / 'states_reference.sto'
    sol_path   = OUT_ROOT / 'solution.sto'
    report_path = OUT_ROOT / 'run_report.md'

    log('=== Step 1: prepare model ===')
    prepare_model(model_path)
    log('=== Step 2: prepare reference ===')
    prepare_reference(ref_path)
    log('=== Step 3: MocoInverse solve ===')
    moco_sol, t_elapsed = run_inverse(str(model_path), str(ref_path), str(sol_path))
    log('=== Step 4: analyze ===')
    try:
        summary = analyze(str(sol_path), str(report_path), t_elapsed, moco_sol)
        log(f'Summary: {summary}')
    except Exception as e:
        log(f'Analysis failed: {e}')
        import traceback; traceback.print_exc()
    log(f'TOTAL WALL: {time.time()-t0:.1f}s')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f'FATAL: {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)
