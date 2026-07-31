"""
ThoracolumbarFB Reach Envelope Analysis
작업 1.1~1.4: 팔 도달 범위 + Arm architecture + Pelvis backward shift 진단
"""

import opensim as osim
import numpy as np
import math
import sys

MODEL_PATH = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim'

# ── helpers ──────────────────────────────────────────────────────────────────
def set_coord(cs, name, deg, s, model):
    c = cs.get(name)
    c.setValue(s, math.radians(deg), False)

def get_pos(model, s, body_name):
    body = model.getBodySet().get(body_name)
    p = body.getPositionInGround(s)
    return np.array([p.get(0), p.get(1), p.get(2)])

def bisect_pelvis_tx(model, s, cs, target_x=-0.0442, lo=-1.5, hi=0.5, n=60):
    c = cs.get('pelvis_tx')
    for _ in range(n):
        mid = (lo + hi) / 2
        c.setValue(s, mid, False)
        model.realizePosition(s)
        cx = model.getBodySet().get('calcn_r').getPositionInGround(s).get(0)
        if cx < target_x:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def bisect_pelvis_ty(model, s, cs, target_y=-0.905, lo=-1.0, hi=0.5, n=60):
    c = cs.get('pelvis_ty')
    for _ in range(n):
        mid = (lo + hi) / 2
        c.setValue(s, mid, False)
        model.realizePosition(s)
        cy = model.getBodySet().get('calcn_r').getPositionInGround(s).get(1)
        if cy < target_y:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def set_all_zero(cs, s, model):
    for i in range(cs.getSize()):
        c = cs.get(i)
        if not c.isConstrained(s):
            c.setValue(s, 0.0, False)
    model.realizePosition(s)

# ── 1.3 Arm architecture ─────────────────────────────────────────────────────
def measure_arm_architecture(model, s, cs):
    print("\n" + "="*60)
    print("1.3 ARM ARCHITECTURE")
    print("="*60)

    set_all_zero(cs, s, model)
    model.realizePosition(s)

    # Marker positions in ground frame (standing)
    pelvis_pos   = get_pos(model, s, 'pelvis')
    scapula_pos  = get_pos(model, s, 'scapula_R')
    humerus_pos  = get_pos(model, s, 'humerus_R')
    ulna_pos     = get_pos(model, s, 'ulna_R')
    radius_pos   = get_pos(model, s, 'radius_R')
    hand_pos     = get_pos(model, s, 'hand_R')
    calcn_pos    = get_pos(model, s, 'calcn_r')
    clavicle_pos = get_pos(model, s, 'clavicle_R')

    print(f"  calcn_r  ground: x={calcn_pos[0]:.4f}  y={calcn_pos[1]:.4f}  z={calcn_pos[2]:.4f}")
    print(f"  pelvis   ground: x={pelvis_pos[0]:.4f}  y={pelvis_pos[1]:.4f}  z={pelvis_pos[2]:.4f}")
    print(f"  clavicle ground: x={clavicle_pos[0]:.4f}  y={clavicle_pos[1]:.4f}  z={clavicle_pos[2]:.4f}")
    print(f"  scapula  ground: x={scapula_pos[0]:.4f}  y={scapula_pos[1]:.4f}  z={scapula_pos[2]:.4f}")
    print(f"  humerus  ground: x={humerus_pos[0]:.4f}  y={humerus_pos[1]:.4f}  z={humerus_pos[2]:.4f}")
    print(f"  ulna     ground: x={ulna_pos[0]:.4f}  y={ulna_pos[1]:.4f}  z={ulna_pos[2]:.4f}")
    print(f"  radius   ground: x={radius_pos[0]:.4f}  y={radius_pos[1]:.4f}  z={radius_pos[2]:.4f}")
    print(f"  hand_R   ground: x={hand_pos[0]:.4f}  y={hand_pos[1]:.4f}  z={hand_pos[2]:.4f}")

    # Segment lengths (joint center to joint center)
    upper_arm  = np.linalg.norm(humerus_pos - scapula_pos)
    forearm    = np.linalg.norm(ulna_pos - humerus_pos)
    hand_seg   = np.linalg.norm(hand_pos - ulna_pos)
    total_arm  = np.linalg.norm(hand_pos - scapula_pos)
    shoulder_h = scapula_pos[1]  # shoulder height above ground

    print(f"\n  Segment lengths (scapula origin = shoulder approx):")
    print(f"    Upper arm  (scapula→humerus): {upper_arm*100:.1f} cm")
    print(f"    Forearm    (humerus→ulna):    {forearm*100:.1f} cm")
    print(f"    Hand       (ulna→hand_R):     {hand_seg*100:.1f} cm")
    print(f"    Total arm  (scapula→hand_R):  {total_arm*100:.1f} cm")
    print(f"    Shoulder height above ground: {shoulder_h:.4f} m ({shoulder_h*100:.1f} cm)")
    print(f"    Shoulder x (forward):         {scapula_pos[0]:.4f} m")

    print(f"\n  Anthropometric reference (adult male):")
    print(f"    Upper arm: ~33 cm  → model: {upper_arm*100:.1f} cm  ({(upper_arm*100-33)/33*100:+.1f}%)")
    print(f"    Forearm:   ~28 cm  → model: {forearm*100:.1f} cm  ({(forearm*100-28)/28*100:+.1f}%)")
    print(f"    Hand:      ~19 cm  → model: {hand_seg*100:.1f} cm  ({(hand_seg*100-19)/19*100:+.1f}%)")
    print(f"    Total:     ~80 cm  → model: {total_arm*100:.1f} cm  ({(total_arm*100-80)/80*100:+.1f}%)")

    return {
        'shoulder_pos': scapula_pos,
        'hand_default': hand_pos,
        'upper_arm': upper_arm,
        'forearm': forearm,
        'hand_seg': hand_seg,
        'total_arm': total_arm,
        'shoulder_height': shoulder_h,
    }

# ── 1.1 Standing reach envelope ───────────────────────────────────────────────
def standing_reach_envelope(model, s, cs, arm_info):
    print("\n" + "="*60)
    print("1.1 STANDING REACH ENVELOPE")
    print("="*60)

    TARGET = np.array([+0.256, -0.755, +0.150])

    set_all_zero(cs, s, model)
    model.realizePosition(s)

    results = []
    min_dist = 1e9
    best_conf = None

    # Sweep arm joints (coarse grid)
    shoulder_elv_vals = np.arange(0, 160, 15)   # 0..155 deg
    elv_angle_vals    = np.arange(-90, 156, 20)  # -90..155 deg
    shoulder_rot_vals = np.arange(-90, 50, 30)   # -90..45 deg
    elbow_vals        = np.arange(0, 156, 15)    # 0..155 deg

    n_total = len(shoulder_elv_vals)*len(elv_angle_vals)*len(shoulder_rot_vals)*len(elbow_vals)
    print(f"  Sweeping {n_total:,} combinations...")

    for se in shoulder_elv_vals:
        set_coord(cs, 'shoulder_elv_r', se, s, model)
        for ea in elv_angle_vals:
            set_coord(cs, 'elv_angle_r', ea, s, model)
            for sr in shoulder_rot_vals:
                set_coord(cs, 'shoulder_rot_r', sr, s, model)
                for ef in elbow_vals:
                    set_coord(cs, 'elbow_flexion_r', ef, s, model)
                    model.realizePosition(s)
                    hp = get_pos(model, s, 'hand_R')
                    dist = np.linalg.norm(hp - TARGET)
                    results.append(hp.copy())
                    if dist < min_dist:
                        min_dist = dist
                        best_conf = (se, ea, sr, ef, hp.copy())

    results = np.array(results)
    print(f"\n  Box target: ({TARGET[0]:.3f}, {TARGET[1]:.3f}, {TARGET[2]:.3f})")
    print(f"  hand_R x range: [{results[:,0].min():.3f}, {results[:,0].max():.3f}]")
    print(f"  hand_R y range: [{results[:,1].min():.3f}, {results[:,1].max():.3f}]")
    print(f"  hand_R z range: [{results[:,2].min():.3f}, {results[:,2].max():.3f}]")

    print(f"\n  Closest config to target ({TARGET}):")
    print(f"    shoulder_elv={best_conf[0]:.0f}, elv_angle={best_conf[1]:.0f}, "
          f"shoulder_rot={best_conf[2]:.0f}, elbow_flex={best_conf[3]:.0f}")
    print(f"    hand_R = ({best_conf[4][0]:.3f}, {best_conf[4][1]:.3f}, {best_conf[4][2]:.3f})")
    print(f"    dist to target = {min_dist*1000:.1f} mm")
    print(f"    Reachable: {'YES' if min_dist < 0.05 else 'NO (>50mm)'}")

    # Target plane slices
    # x-y slice near z=+0.15
    z_mask = np.abs(results[:,2] - 0.15) < 0.05
    if z_mask.sum() > 0:
        r_z = results[z_mask]
        print(f"\n  Slice z=0.15±0.05: {z_mask.sum()} points")
        print(f"    x: [{r_z[:,0].min():.3f}, {r_z[:,0].max():.3f}]")
        print(f"    y: [{r_z[:,1].min():.3f}, {r_z[:,1].max():.3f}]")
        can_reach_x = TARGET[0] <= r_z[:,0].max() and TARGET[0] >= r_z[:,0].min()
        can_reach_y = TARGET[1] <= r_z[:,1].max() and TARGET[1] >= r_z[:,1].min()
        print(f"    Target x={TARGET[0]:.3f} in range: {'YES' if can_reach_x else 'NO'}")
        print(f"    Target y={TARGET[1]:.3f} in range: {'YES' if can_reach_y else 'NO'}")

    # Reset
    set_all_zero(cs, s, model)
    model.realizePosition(s)
    return results, min_dist, best_conf

# ── 1.2 Stoop reach envelope ──────────────────────────────────────────────────
def stoop_reach_envelope(model, s, cs):
    print("\n" + "="*60)
    print("1.2 STOOP REACH ENVELOPE (foot anchor)")
    print("="*60)

    TARGET = np.array([+0.256, -0.755, +0.150])
    TARGET_CALCN_X = -0.0442
    TARGET_CALCN_Y = -0.905

    # Posture grid
    pelvis_tilts  = [-30, -45, -55, -65, -75]
    hip_flexions  = [60, 80, 100, 110]
    knee_angles   = [0, -15, -30, -45]
    lumbar_totals = [-30, -50, -60, -75]  # per-segment = total / 6

    foot_anchor_tests = [-0.0442, +0.0058, +0.0558, +0.1058]  # +0, +0.05, +0.10, +0.15

    print("\n  [A] Fixed foot anchor = -0.0442 (default)")
    results_table = []

    for pt in pelvis_tilts:
        for hf in hip_flexions:
            for ka in knee_angles:
                for lt in lumbar_totals:
                    # Set posture
                    set_all_zero(cs, s, model)
                    per_seg = lt / 6.0  # distribute across 5 lumbar + T12_L1
                    set_coord(cs, 'pelvis_tilt', pt, s, model)
                    set_coord(cs, 'L5_S1_FE',   per_seg, s, model)
                    set_coord(cs, 'L4_L5_FE',   per_seg, s, model)
                    set_coord(cs, 'L3_L4_FE',   per_seg, s, model)
                    set_coord(cs, 'L2_L3_FE',   per_seg, s, model)
                    set_coord(cs, 'L1_L2_FE',   per_seg, s, model)
                    set_coord(cs, 'T12_L1_FE',  per_seg * 0.6, s, model)
                    set_coord(cs, 'hip_flexion_r', hf, s, model)
                    set_coord(cs, 'hip_flexion_l', hf, s, model)
                    set_coord(cs, 'knee_angle_r', ka, s, model)
                    set_coord(cs, 'knee_angle_l', ka, s, model)

                    # Ankle auto
                    set_coord(cs, 'ankle_angle_r', -9, s, model)
                    set_coord(cs, 'ankle_angle_l', -9, s, model)

                    # Bisect pelvis_tx for foot anchor
                    tx = bisect_pelvis_tx(model, s, cs, target_x=TARGET_CALCN_X)
                    cs.get('pelvis_tx').setValue(s, tx, False)

                    # Bisect pelvis_ty for ground
                    ty = bisect_pelvis_ty(model, s, cs, target_y=TARGET_CALCN_Y)
                    cs.get('pelvis_ty').setValue(s, ty, False)

                    model.realizePosition(s)

                    # Measure pelvis pos
                    pelvis_pos = get_pos(model, s, 'pelvis')
                    calcn_pos  = get_pos(model, s, 'calcn_r')
                    scapula_pos = get_pos(model, s, 'scapula_R')

                    # Best arm reach (coarse sweep)
                    min_dist = 1e9
                    best_hand = None
                    for se in np.arange(0, 160, 20):
                        set_coord(cs, 'shoulder_elv_r', se, s, model)
                        for ea in np.arange(-90, 156, 25):
                            set_coord(cs, 'elv_angle_r', ea, s, model)
                            for ef in np.arange(0, 156, 20):
                                set_coord(cs, 'elbow_flexion_r', ef, s, model)
                                model.realizePosition(s)
                                hp = get_pos(model, s, 'hand_R')
                                dist = np.linalg.norm(hp - TARGET)
                                if dist < min_dist:
                                    min_dist = dist
                                    best_hand = hp.copy()

                    # Reset arm
                    set_coord(cs, 'shoulder_elv_r', 0, s, model)
                    set_coord(cs, 'elv_angle_r', 0, s, model)
                    set_coord(cs, 'elbow_flexion_r', 0, s, model)

                    pelvis_box_dist = abs(pelvis_pos[0] - TARGET[0])
                    arm_reach_avail = np.linalg.norm(scapula_pos - TARGET)
                    reachable = (min_dist < 0.050)

                    results_table.append({
                        'pelvis_tilt': pt, 'hip': hf, 'knee': ka, 'lumbar': lt,
                        'pelvis_tx': tx, 'pelvis_ty': ty,
                        'pelvis_x': pelvis_pos[0], 'pelvis_y': pelvis_pos[1],
                        'shoulder_x': scapula_pos[0], 'shoulder_y': scapula_pos[1],
                        'pelvis_box_dist': pelvis_box_dist,
                        'min_dist_mm': min_dist * 1000,
                        'reachable': reachable,
                        'calcn_x_actual': calcn_pos[0],
                        'calcn_err_mm': abs(calcn_pos[0] - TARGET_CALCN_X) * 1000,
                    })

    # Print summary table
    print(f"\n  {'PT':>5} {'HF':>5} {'KA':>5} {'LT':>5} "
          f"{'pelvis_tx':>10} {'pelvis_x':>10} {'shoulder_y':>11} "
          f"{'box_dist':>9} {'min_mm':>8} {'OK?':>5}")
    print("  " + "-"*90)

    # Show notable results
    sorted_results = sorted(results_table, key=lambda r: r['min_dist_mm'])
    # Top 20 closest
    for r in sorted_results[:20]:
        print(f"  {r['pelvis_tilt']:>5.0f} {r['hip']:>5.0f} {r['knee']:>5.0f} {r['lumbar']:>5.0f} "
              f"  {r['pelvis_tx']:>8.3f}   {r['pelvis_x']:>8.3f}   {r['shoulder_y']:>9.3f} "
              f"  {r['pelvis_box_dist']:>7.3f}  {r['min_dist_mm']:>7.1f}  {'YES' if r['reachable'] else 'no'}")

    n_reachable = sum(1 for r in results_table if r['reachable'])
    print(f"\n  Total configurations tested: {len(results_table)}")
    print(f"  Reachable (dist < 50 mm): {n_reachable}")
    print(f"  Best distance: {sorted_results[0]['min_dist_mm']:.1f} mm")
    print(f"  Best config: pelvis_tilt={sorted_results[0]['pelvis_tilt']}, "
          f"hip={sorted_results[0]['hip']}, knee={sorted_results[0]['knee']}, "
          f"lumbar={sorted_results[0]['lumbar']}")

    # [B] Foot anchor variation test (single representative posture)
    print("\n\n  [B] Foot anchor variation (pelvis_tilt=-55, hip=100, knee=-30, lumbar=-60)")
    print(f"\n  {'calcn_target':>13} {'pelvis_tx':>10} {'pelvis_x':>10} "
          f"{'shoulder_y':>11} {'box_dist':>9} {'min_mm':>8} {'OK?':>5}")
    print("  " + "-"*70)

    for fa in foot_anchor_tests:
        set_all_zero(cs, s, model)
        set_coord(cs, 'pelvis_tilt', -55, s, model)
        set_coord(cs, 'L5_S1_FE',  -10, s, model)
        set_coord(cs, 'L4_L5_FE',  -10, s, model)
        set_coord(cs, 'L3_L4_FE',  -10, s, model)
        set_coord(cs, 'L2_L3_FE',  -10, s, model)
        set_coord(cs, 'L1_L2_FE',  -10, s, model)
        set_coord(cs, 'T12_L1_FE',  -6, s, model)
        set_coord(cs, 'hip_flexion_r', 100, s, model)
        set_coord(cs, 'hip_flexion_l', 100, s, model)
        set_coord(cs, 'knee_angle_r', -30, s, model)
        set_coord(cs, 'knee_angle_l', -30, s, model)
        set_coord(cs, 'ankle_angle_r', -9, s, model)
        set_coord(cs, 'ankle_angle_l', -9, s, model)

        tx = bisect_pelvis_tx(model, s, cs, target_x=fa)
        cs.get('pelvis_tx').setValue(s, tx, False)
        ty = bisect_pelvis_ty(model, s, cs, target_y=TARGET_CALCN_Y)
        cs.get('pelvis_ty').setValue(s, ty, False)
        model.realizePosition(s)

        pelvis_pos  = get_pos(model, s, 'pelvis')
        scapula_pos = get_pos(model, s, 'scapula_R')

        min_dist = 1e9
        for se in np.arange(0, 160, 20):
            set_coord(cs, 'shoulder_elv_r', se, s, model)
            for ea in np.arange(-90, 156, 25):
                set_coord(cs, 'elv_angle_r', ea, s, model)
                for ef in np.arange(0, 156, 20):
                    set_coord(cs, 'elbow_flexion_r', ef, s, model)
                    model.realizePosition(s)
                    hp = get_pos(model, s, 'hand_R')
                    dist = np.linalg.norm(hp - TARGET)
                    if dist < min_dist:
                        min_dist = dist

        set_coord(cs, 'shoulder_elv_r', 0, s, model)
        set_coord(cs, 'elv_angle_r', 0, s, model)
        set_coord(cs, 'elbow_flexion_r', 0, s, model)

        pbd = abs(pelvis_pos[0] - TARGET[0])
        print(f"  {fa:>13.4f}   {tx:>8.3f}   {pelvis_pos[0]:>8.3f}   {scapula_pos[1]:>9.3f}"
              f"  {pbd:>7.3f}  {min_dist*1000:>7.1f}  {'YES' if min_dist<0.05 else 'no'}")

    return results_table

# ── 1.4 Pelvis backward shift mechanism ──────────────────────────────────────
def pelvis_backward_shift_diagnosis(model, s, cs):
    print("\n" + "="*60)
    print("1.4 PELVIS BACKWARD SHIFT MECHANISM")
    print("="*60)

    TARGET_CALCN_X = -0.0442
    TARGET_CALCN_Y = -0.905
    TARGET_BOX_X   = +0.256

    # Compare pelvis_tilt -55 vs -45 (v8 반직관 거동)
    configs = [
        {'pelvis_tilt': -45, 'hip': 100, 'knee': -30, 'lumbar_seg': -10, 'ankle': -9},
        {'pelvis_tilt': -55, 'hip': 100, 'knee': -30, 'lumbar_seg': -10, 'ankle': -9},
        {'pelvis_tilt': -65, 'hip': 100, 'knee': -30, 'lumbar_seg': -10, 'ankle': -9},
        {'pelvis_tilt': -55, 'hip': 80,  'knee': -30, 'lumbar_seg': -10, 'ankle': -9},
        {'pelvis_tilt': -55, 'hip': 100, 'knee':   0, 'lumbar_seg': -10, 'ankle': -9},
        {'pelvis_tilt': -55, 'hip': 100, 'knee': -30, 'lumbar_seg':   0, 'ankle': -9},
        {'pelvis_tilt': -55, 'hip': 100, 'knee': -30, 'lumbar_seg': -14, 'ankle': -9},
    ]

    print(f"\n  {'Config':50s} {'pelvis_tx':>10} {'pelvis_x':>10} "
          f"{'pelvis→box':>11} {'calcn_err':>10}")
    print("  " + "-"*100)

    diag_results = []
    for cfg in configs:
        set_all_zero(cs, s, model)
        set_coord(cs, 'pelvis_tilt', cfg['pelvis_tilt'], s, model)
        ls = cfg['lumbar_seg']
        set_coord(cs, 'L5_S1_FE',  ls,       s, model)
        set_coord(cs, 'L4_L5_FE',  ls,       s, model)
        set_coord(cs, 'L3_L4_FE',  ls,       s, model)
        set_coord(cs, 'L2_L3_FE',  ls,       s, model)
        set_coord(cs, 'L1_L2_FE',  ls,       s, model)
        set_coord(cs, 'T12_L1_FE', ls * 0.6, s, model)
        set_coord(cs, 'hip_flexion_r', cfg['hip'], s, model)
        set_coord(cs, 'hip_flexion_l', cfg['hip'], s, model)
        set_coord(cs, 'knee_angle_r',  cfg['knee'], s, model)
        set_coord(cs, 'knee_angle_l',  cfg['knee'], s, model)
        set_coord(cs, 'ankle_angle_r', cfg['ankle'], s, model)
        set_coord(cs, 'ankle_angle_l', cfg['ankle'], s, model)

        tx = bisect_pelvis_tx(model, s, cs, target_x=TARGET_CALCN_X)
        cs.get('pelvis_tx').setValue(s, tx, False)
        ty = bisect_pelvis_ty(model, s, cs, target_y=TARGET_CALCN_Y)
        cs.get('pelvis_ty').setValue(s, ty, False)
        model.realizePosition(s)

        pelvis_pos = get_pos(model, s, 'pelvis')
        calcn_pos  = get_pos(model, s, 'calcn_r')
        pelvis_box = abs(pelvis_pos[0] - TARGET_BOX_X)
        calcn_err  = abs(calcn_pos[0] - TARGET_CALCN_X) * 1000

        label = f"PT={cfg['pelvis_tilt']:>4}, hip={cfg['hip']:>4}, kn={cfg['knee']:>4}, L={cfg['lumbar_seg']:>5}"
        print(f"  {label:50s}  {tx:>8.3f}   {pelvis_pos[0]:>8.3f}   {pelvis_box:>9.3f}   {calcn_err:>8.1f} mm")
        diag_results.append({'config': label, 'tx': tx, 'pelvis_x': pelvis_pos[0], 'pbd': pelvis_box})

    # Individual joint contribution (pelvis_tilt effect alone)
    print("\n  --- Joint-by-joint contribution (pelvis_tilt=-55 baseline) ---")
    print(f"  {'Joint changed':35s} {'pelvis_tx':>10} {'pelvis→box':>12}")
    print("  " + "-"*60)

    joints_to_zero = [
        ('pelvis_tilt only (-55, rest=0)', {'pelvis_tilt': -55}),
        ('+ hip=100',   {'pelvis_tilt': -55, 'hip': 100}),
        ('+ knee=-30',  {'pelvis_tilt': -55, 'hip': 100, 'knee': -30}),
        ('+ lumbar=-10 each', {'pelvis_tilt': -55, 'hip': 100, 'knee': -30, 'lumbar_seg': -10}),
        ('+ ankle=-9',  {'pelvis_tilt': -55, 'hip': 100, 'knee': -30, 'lumbar_seg': -10, 'ankle': -9}),
    ]

    for label, cfg in joints_to_zero:
        set_all_zero(cs, s, model)
        if 'pelvis_tilt' in cfg:
            set_coord(cs, 'pelvis_tilt', cfg['pelvis_tilt'], s, model)
        if 'hip' in cfg:
            set_coord(cs, 'hip_flexion_r', cfg['hip'], s, model)
            set_coord(cs, 'hip_flexion_l', cfg['hip'], s, model)
        if 'knee' in cfg:
            set_coord(cs, 'knee_angle_r', cfg['knee'], s, model)
            set_coord(cs, 'knee_angle_l', cfg['knee'], s, model)
        if 'lumbar_seg' in cfg:
            ls = cfg['lumbar_seg']
            for ln in ['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L2_L3_FE', 'L1_L2_FE']:
                set_coord(cs, ln, ls, s, model)
            set_coord(cs, 'T12_L1_FE', ls * 0.6, s, model)
        if 'ankle' in cfg:
            set_coord(cs, 'ankle_angle_r', cfg['ankle'], s, model)
            set_coord(cs, 'ankle_angle_l', cfg['ankle'], s, model)

        tx = bisect_pelvis_tx(model, s, cs, target_x=TARGET_CALCN_X)
        cs.get('pelvis_tx').setValue(s, tx, False)
        ty = bisect_pelvis_ty(model, s, cs, target_y=TARGET_CALCN_Y)
        cs.get('pelvis_ty').setValue(s, ty, False)
        model.realizePosition(s)

        pelvis_pos = get_pos(model, s, 'pelvis')
        pbd = abs(pelvis_pos[0] - TARGET_BOX_X)
        print(f"  {label:35s}  {tx:>8.3f}   {pbd:>10.3f}")

    return diag_results

# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    print("Loading model...")
    model = osim.Model(MODEL_PATH)
    s = model.initSystem()
    cs = model.getCoordinateSet()
    print(f"Model loaded: {model.getName()}")
    print(f"  Bodies: {model.getBodySet().getSize()}")
    print(f"  Coordinates: {cs.getSize()}")
    print(f"  Muscles: {model.getMuscles().getSize()}")

    # shoulder_elv ROM check
    c_se = cs.get('shoulder_elv_r')
    print(f"\n  shoulder_elv_r range: [{math.degrees(c_se.getRangeMin()):.1f}, {math.degrees(c_se.getRangeMax()):.1f}] deg")
    c_ea = cs.get('elv_angle_r')
    print(f"  elv_angle_r range:    [{math.degrees(c_ea.getRangeMin()):.1f}, {math.degrees(c_ea.getRangeMax()):.1f}] deg")

    # 1.3 Arm architecture
    arm_info = measure_arm_architecture(model, s, cs)

    # 1.1 Standing reach
    reach_results, min_dist, best_conf = standing_reach_envelope(model, s, cs, arm_info)

    # 1.2 Stoop reach
    stoop_results = stoop_reach_envelope(model, s, cs)

    # 1.4 Pelvis backward shift
    diag_results = pelvis_backward_shift_diagnosis(model, s, cs)

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
