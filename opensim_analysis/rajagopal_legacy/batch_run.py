#!/usr/bin/env python3
"""
Batch musculoskeletal analysis: 270 conditions × 10 motions = 2,700 simulations.
Uses multiprocessing for parallel execution on 24 cores.
"""

import os, sys, glob, json, time, traceback
import numpy as np
import pandas as pd
from multiprocessing import Pool, cpu_count
from itertools import product

# ─── Configuration ────────────────────────────────────────────────────────────

BVH_DIR = "/data/bones-seed/soma_uniform/bvh"
MODEL_BASE = "/data/opensim_models/Rajagopal_with_erector.osim"
OUT_ROOT = "/data/opensim_results"
ANALYSIS_DIR = "/data/opensim_analysis"

N_WORKERS = 24
MOMENT_ARM = 0.115  # meters
HAND_DISTANCE = 0.443  # mean hand-pelvis horizontal distance (m), from FK analysis
G = 9.81

# Experimental factors
SEXES = {
    'male':   {'heights': {'slim': 165, 'avg': 170, 'heavy': 175},
               'masses':  {'slim': 60,  'avg': 70,  'heavy': 80}},
    'female': {'heights': {'slim': 155, 'avg': 160, 'heavy': 165},
               'masses':  {'slim': 50,  'avg': 58,  'heavy': 65}},
}
AGES = {'young': 1.0, 'middle': 0.85, 'senior': 0.70}
BODY_TYPES = ['slim', 'avg', 'heavy']
LOADS_KG = [10, 20, 30]
SUIT_FORCES_N = [0, 50, 100, 150, 200]


# ─── BVH Parser (minimal, same as tested) ────────────────────────────────────

def parse_bvh(fp):
    with open(fp) as f:
        lines = [l.strip() for l in f if l.strip()]
    idx = 0
    assert lines[idx] == "HIERARCHY"; idx += 1
    J = {}; stk = []; cc = 0; root = None
    while idx < len(lines) and lines[idx] != "MOTION":
        p = lines[idx].split()
        if p[0] in ("ROOT", "JOINT"):
            nm = p[1]
            if p[0] == "ROOT": root = nm
            idx += 1; idx += 1
            off = [float(x) for x in lines[idx].split()[1:4]]
            idx += 1; cp = lines[idx].split()
            nc = int(cp[1]); chs = cp[2:2+nc]
            J[nm] = {'ch': chs, 'ci': list(range(cc, cc+nc)), 'off': off}
            cc += nc; stk.append(nm)
        elif p[0] == "}":
            if stk: stk.pop()
        idx += 1
    assert lines[idx] == "MOTION"; idx += 1
    nf = int(lines[idx].split()[1]); idx += 1
    dt = float(lines[idx].split()[2]); idx += 1
    D = np.zeros((nf, cc))
    for f in range(nf):
        vs = lines[idx+f].split()
        D[f, :len(vs)] = [float(v) for v in vs[:cc]]
    return J, root, D, dt, nf


def gch(J, nm, ch, D, f):
    if nm not in J: return 0.0
    j = J[nm]
    for i, c in enumerate(j['ch']):
        if c == ch: return D[f, j['ci'][i]]
    return 0.0


def bvh_to_mot(bvh_path, mot_path):
    """Convert SOMA BVH to OpenSim .mot, return duration."""
    J, root, D, dt, nf = parse_bvh(bvh_path)
    step = 4  # 120→30fps
    frames = list(range(0, nf, step))

    coord_names = [
        'pelvis_tx','pelvis_ty','pelvis_tz',
        'pelvis_tilt','pelvis_list','pelvis_rotation',
        'lumbar_extension','lumbar_bending','lumbar_rotation',
        'hip_flexion_r','hip_adduction_r','hip_rotation_r','knee_angle_r',
        'ankle_angle_r','subtalar_angle_r',
        'hip_flexion_l','hip_adduction_l','hip_rotation_l','knee_angle_l',
        'ankle_angle_l','subtalar_angle_l',
        'arm_flex_r','arm_add_r','arm_rot_r','elbow_flex_r',
        'arm_flex_l','arm_add_l','arm_rot_l','elbow_flex_l',
    ]

    def get_coord(fi):
        v = {}
        v['pelvis_tx'] = gch(J,'Hips','Zposition',D,fi) * 0.01
        v['pelvis_ty'] = gch(J,'Hips','Yposition',D,fi) * 0.01
        v['pelvis_tz'] = gch(J,'Hips','Xposition',D,fi) * 0.01
        v['pelvis_tilt'] = -(gch(J,'Hips','Xrotation',D,fi) - 90.0)
        v['pelvis_list'] = -gch(J,'Hips','Yrotation',D,fi)
        v['pelvis_rotation'] = gch(J,'Hips','Zrotation',D,fi) - 90.0
        v['lumbar_extension'] = -(gch(J,'Spine1','Zrotation',D,fi) + gch(J,'Spine2','Zrotation',D,fi))
        v['lumbar_bending'] = gch(J,'Spine1','Xrotation',D,fi) + gch(J,'Spine2','Xrotation',D,fi)
        v['lumbar_rotation'] = gch(J,'Spine1','Yrotation',D,fi) + gch(J,'Spine2','Yrotation',D,fi)
        v['hip_flexion_r'] = -gch(J,'RightLeg','Zrotation',D,fi)
        v['hip_adduction_r'] = gch(J,'RightLeg','Xrotation',D,fi)
        v['hip_rotation_r'] = -gch(J,'RightLeg','Yrotation',D,fi)
        v['knee_angle_r'] = -gch(J,'RightShin','Zrotation',D,fi)
        v['ankle_angle_r'] = -gch(J,'RightFoot','Zrotation',D,fi)
        v['subtalar_angle_r'] = gch(J,'RightFoot','Xrotation',D,fi)
        v['hip_flexion_l'] = -gch(J,'LeftLeg','Zrotation',D,fi)
        v['hip_adduction_l'] = -gch(J,'LeftLeg','Xrotation',D,fi)
        v['hip_rotation_l'] = gch(J,'LeftLeg','Yrotation',D,fi)
        v['knee_angle_l'] = -gch(J,'LeftShin','Zrotation',D,fi)
        v['ankle_angle_l'] = -gch(J,'LeftFoot','Zrotation',D,fi)
        v['subtalar_angle_l'] = -gch(J,'LeftFoot','Xrotation',D,fi)
        v['arm_flex_r'] = -gch(J,'RightArm','Zrotation',D,fi)
        v['arm_add_r'] = gch(J,'RightArm','Xrotation',D,fi)
        v['arm_rot_r'] = gch(J,'RightArm','Yrotation',D,fi)
        v['elbow_flex_r'] = gch(J,'RightForeArm','Zrotation',D,fi)
        v['arm_flex_l'] = -gch(J,'LeftArm','Zrotation',D,fi)
        v['arm_add_l'] = -gch(J,'LeftArm','Xrotation',D,fi)
        v['arm_rot_l'] = -gch(J,'LeftArm','Yrotation',D,fi)
        v['elbow_flex_l'] = gch(J,'LeftForeArm','Zrotation',D,fi)
        return v

    n_out = len(frames)
    with open(mot_path, 'w') as f:
        f.write(f"motion\nversion=1\nnRows={n_out}\nnColumns={len(coord_names)+1}\n")
        f.write("inDegrees=yes\nendheader\n")
        f.write("time\t" + "\t".join(coord_names) + "\n")
        for fi in frames:
            t = fi * dt
            vals = get_coord(fi)
            f.write(f"{t:.6f}\t" + "\t".join(f"{vals[c]:.6f}" for c in coord_names) + "\n")

    return n_out * dt * step


# ─── Model Scaling ────────────────────────────────────────────────────────────

def create_scaled_model(sex, body_type, age, model_base, output_path):
    """Scale Rajagopal model by height/mass/age using OpenSim API."""
    import opensim as osim

    height_cm = SEXES[sex]['heights'][body_type]
    mass_kg = SEXES[sex]['masses'][body_type]
    strength = AGES[age]

    # Reference: Rajagopal default is ~170cm, 75.16kg male
    ref_height = 170.0
    ref_mass = 75.16

    height_scale = height_cm / ref_height
    mass_scale = mass_kg / ref_mass

    model = osim.Model(model_base)

    # Scale body masses
    bodies = model.getBodySet()
    for i in range(bodies.getSize()):
        b = bodies.get(i)
        b.setMass(b.getMass() * mass_scale)

    # Scale muscle forces by age factor
    muscles = model.getMuscles()
    for i in range(muscles.getSize()):
        m = muscles.get(i)
        m.setMaxIsometricForce(m.getMaxIsometricForce() * strength)

    model.initSystem()
    model.printToXML(output_path)
    return output_path


# ─── Single Condition Runner ──────────────────────────────────────────────────

def run_single(args):
    """Run ID for one condition × one motion. Return metrics dict."""
    cond_id, mot_path, model_path, suit_force_n, load_kg, sex, age, body_type, motion_name = args

    import opensim as osim

    try:
        model = osim.Model(model_path)

        # Add suit actuator if force > 0
        suit_torque = suit_force_n * MOMENT_ARM
        if suit_force_n > 0:
            suit_act = osim.CoordinateActuator()
            suit_act.setName('suit_lumbar')
            suit_act.set_coordinate('lumbar_extension')
            suit_act.setOptimalForce(suit_torque)
            suit_act.setMinControl(1.0)
            suit_act.setMaxControl(1.0)
            model.addForce(suit_act)

        model.initSystem()

        # Run ID
        sto = osim.Storage(mot_path)
        t0, t1 = sto.getFirstTime(), sto.getLastTime()

        id_tool = osim.InverseDynamicsTool()
        id_tool.setModel(model)
        id_tool.setCoordinatesFileName(mot_path)
        id_tool.setLowpassCutoffFrequency(6.0)
        id_tool.setStartTime(t0 + 0.1)
        id_tool.setEndTime(t1 - 0.1)

        # Unique output per condition
        raw_dir = os.path.join(OUT_ROOT, "raw")
        os.makedirs(raw_dir, exist_ok=True)
        id_out = os.path.join(raw_dir, f"id_{cond_id}.sto")
        id_tool.setOutputGenForceFileName(id_out)
        id_tool.setResultsDir(raw_dir)
        id_tool.run()

        # Extract metrics from ID results
        id_sto = osim.Storage(id_out)
        nf = id_sto.getSize()

        metrics = {
            'cond_id': cond_id, 'sex': sex, 'age': age, 'body_type': body_type,
            'load_kg': load_kg, 'suit_force_n': suit_force_n,
            'suit_torque_nm': suit_torque, 'motion': motion_name,
        }

        # Extract key joint torques
        for col_name, key in [
            ('lumbar_extension_moment', 'lumbar'),
            ('hip_flexion_r_moment', 'hip_r'),
            ('hip_flexion_l_moment', 'hip_l'),
            ('knee_angle_r_moment', 'knee_r'),
            ('arm_flex_r_moment', 'shoulder_r'),
            ('arm_flex_l_moment', 'shoulder_l'),
            ('elbow_flex_r_moment', 'elbow_r'),
            ('elbow_flex_l_moment', 'elbow_l'),
        ]:
            try:
                d = osim.ArrayDouble()
                id_sto.getDataColumn(col_name, d)
                vals = np.array([d.getitem(i) for i in range(nf)])
                metrics[f'{key}_peak'] = float(np.max(np.abs(vals)))
                metrics[f'{key}_mean'] = float(np.mean(np.abs(vals)))
                # Extension-only for lumbar (positive values)
                if key == 'lumbar':
                    ext = vals[vals > 0]
                    metrics['lumbar_ext_peak'] = float(ext.max()) if len(ext) > 0 else 0.0
                    metrics['lumbar_ext_mean'] = float(ext.mean()) if len(ext) > 0 else 0.0
                    # Add analytical load effect: Δτ = load_kg × g × hand_distance
                    load_torque = load_kg * G * HAND_DISTANCE
                    vals_loaded = vals + load_torque  # load increases extension demand
                    ext_loaded = vals_loaded[vals_loaded > 0]
                    metrics['lumbar_ext_loaded_peak'] = float(ext_loaded.max()) if len(ext_loaded) > 0 else 0.0
                    metrics['lumbar_ext_loaded_mean'] = float(ext_loaded.mean()) if len(ext_loaded) > 0 else 0.0
                    # Biological torque after suit assist (on loaded torque)
                    bio = np.where(vals_loaded > 0, np.maximum(0, vals_loaded - suit_torque), vals_loaded)
                    bio_ext = bio[bio > 0]
                    metrics['lumbar_bio_ext_peak'] = float(bio_ext.max()) if len(bio_ext) > 0 else 0.0
                    metrics['lumbar_bio_ext_mean'] = float(bio_ext.mean()) if len(bio_ext) > 0 else 0.0
            except:
                metrics[f'{key}_peak'] = np.nan
                metrics[f'{key}_mean'] = np.nan

        # Clean up raw .sto to save disk
        try:
            os.remove(id_out)
        except:
            pass

        return metrics

    except Exception as e:
        return {
            'cond_id': cond_id, 'sex': sex, 'age': age, 'body_type': body_type,
            'load_kg': load_kg, 'suit_force_n': suit_force_n,
            'motion': motion_name, 'error': str(e)[:200],
        }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    os.makedirs(os.path.join(OUT_ROOT, "raw"), exist_ok=True)

    # Step 1: Select 10 motions
    print("Step 1: Selecting motions...")
    stoop_files = sorted(glob.glob(f"{BVH_DIR}/*/neutral_stoop_down_R_*__A*.bvh"))
    stoop_files = [f for f in stoop_files if '_M.' not in f]

    seen = set()
    selected_bvh = []
    for f in stoop_files:
        perf = os.path.basename(f).split('__')[1].replace('.bvh', '')
        if perf not in seen and len(selected_bvh) < 10:
            selected_bvh.append(f)
            seen.add(perf)
    print(f"  Selected {len(selected_bvh)} motions")

    # Step 2: Convert BVH → .mot
    print("Step 2: Converting BVH → .mot...")
    mot_dir = os.path.join(OUT_ROOT, "motions")
    os.makedirs(mot_dir, exist_ok=True)

    mot_files = {}
    for bvh_path in selected_bvh:
        bn = os.path.splitext(os.path.basename(bvh_path))[0]
        mot_path = os.path.join(mot_dir, f"{bn}.mot")
        if not os.path.exists(mot_path):
            bvh_to_mot(bvh_path, mot_path)
        mot_files[bn] = mot_path
    print(f"  Converted {len(mot_files)} motions")

    # Step 3: Create scaled models (18 variants)
    print("Step 3: Creating scaled models...")
    model_dir = os.path.join(OUT_ROOT, "models")
    os.makedirs(model_dir, exist_ok=True)

    model_paths = {}
    for sex in SEXES:
        for body_type in BODY_TYPES:
            for age in AGES:
                key = f"{sex}_{body_type}_{age}"
                path = os.path.join(model_dir, f"model_{key}.osim")
                if not os.path.exists(path):
                    create_scaled_model(sex, body_type, age, MODEL_BASE, path)
                model_paths[key] = path
    print(f"  Created {len(model_paths)} model variants")

    # Step 4: Build task list (270 conditions × 10 motions)
    print("Step 4: Building task list...")
    tasks = []
    cond_id = 0
    for sex in SEXES:
        for age in AGES:
            for body_type in BODY_TYPES:
                model_key = f"{sex}_{body_type}_{age}"
                model_path = model_paths[model_key]
                for load_kg in LOADS_KG:
                    for suit_n in SUIT_FORCES_N:
                        for motion_name, mot_path in mot_files.items():
                            tasks.append((
                                cond_id, mot_path, model_path, suit_n, load_kg,
                                sex, age, body_type, motion_name
                            ))
                            cond_id += 1

    print(f"  Total tasks: {len(tasks)} ({len(tasks)//10} conditions × 10 motions)")

    # Step 5: Parallel execution
    print(f"Step 5: Running {len(tasks)} simulations on {N_WORKERS} workers...")
    t_start = time.time()

    with Pool(N_WORKERS) as pool:
        results = pool.map(run_single, tasks)

    elapsed = time.time() - t_start
    print(f"  Completed in {elapsed:.0f}s ({elapsed/60:.1f} min)")

    # Step 6: Aggregate results
    print("Step 6: Aggregating results...")
    df = pd.DataFrame(results)

    # Count errors
    n_err = df['error'].notna().sum() if 'error' in df.columns else 0
    print(f"  Errors: {n_err}/{len(df)}")

    # Save raw results
    df.to_csv(os.path.join(OUT_ROOT, "all_results.csv"), index=False)

    # Compute condition-level summaries (average over 10 motions)
    group_cols = ['sex', 'age', 'body_type', 'load_kg', 'suit_force_n']
    metric_cols = [c for c in df.columns if c.endswith('_peak') or c.endswith('_mean')]
    summary = df.groupby(group_cols)[metric_cols].agg(['mean', 'std']).reset_index()
    summary.columns = ['_'.join(c).strip('_') for c in summary.columns]
    summary.to_csv(os.path.join(OUT_ROOT, "summary.csv"), index=False)

    print(f"  Saved: {OUT_ROOT}/all_results.csv ({len(df)} rows)")
    print(f"  Saved: {OUT_ROOT}/summary.csv ({len(summary)} rows)")

    # Quick stats
    print(f"\n{'='*70}")
    print(f"  BATCH RESULTS OVERVIEW")
    print(f"{'='*70}")

    if 'lumbar_bio_ext_peak' in df.columns:
        baseline = df[df['suit_force_n'] == 0]
        suited_200 = df[df['suit_force_n'] == 200]

        bl_peak = baseline['lumbar_bio_ext_peak'].mean()
        s200_peak = suited_200['lumbar_bio_ext_peak'].mean()
        if bl_peak > 0:
            reduction = (1 - s200_peak / bl_peak) * 100
            print(f"  Lumbar ext peak (all conditions avg):")
            print(f"    Baseline:  {bl_peak:.1f} Nm")
            print(f"    200N suit: {s200_peak:.1f} Nm")
            print(f"    Reduction: {reduction:.1f}%")

        # By sex
        for sex in ['male', 'female']:
            bl_s = baseline[baseline['sex'] == sex]['lumbar_bio_ext_peak'].mean()
            s2_s = suited_200[suited_200['sex'] == sex]['lumbar_bio_ext_peak'].mean()
            if bl_s > 0:
                red = (1 - s2_s / bl_s) * 100
                print(f"    {sex}: {bl_s:.1f} → {s2_s:.1f} Nm ({red:.1f}%)")

        # By age
        for age in AGES:
            bl_a = baseline[baseline['age'] == age]['lumbar_bio_ext_peak'].mean()
            s2_a = suited_200[suited_200['age'] == age]['lumbar_bio_ext_peak'].mean()
            if bl_a > 0:
                red = (1 - s2_a / bl_a) * 100
                print(f"    {age}: {bl_a:.1f} → {s2_a:.1f} Nm ({red:.1f}%)")

    print(f"{'='*70}")
    print("DONE.")


if __name__ == "__main__":
    main()
