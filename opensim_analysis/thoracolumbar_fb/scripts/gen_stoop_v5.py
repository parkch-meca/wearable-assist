"""Stoop v5 — same flat-foot solve as v4, but SLOWER bend (2 s, matches
straighten). Goal: reduce the angular-deceleration peak at bend-end so that
the L5/S1 moment pattern is gravity-dominated (bend < straighten).

Timing (5 s total; motion window 4.5 s):
  0.0 - 0.5 s : upright
  0.5 - 2.5 s : bend (2 s, was 1 s in v4)
  2.5 - 3.0 s : hold
  3.0 - 5.0 s : straighten (2 s)"""
import opensim as osim
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim'
MOT_OUT = Path('/data/stoop_motion/stoop_synthetic_v5.mot')
GRF_OUT = Path('/data/stoop_motion/stoop_grf_v5.sto')
GRF_XML_OUT = Path('/data/stoop_motion/stoop_grf_v5.xml')
PNG_OUT = Path('/data/opensim_results/stoop_v5_motion_check.png')

FPS = 120
T_TOTAL = 5.0
N_FRAMES = int(T_TOTAL * FPS) + 1
BODY_MASS_KG = 75.0
G = 9.81
F_PER_FOOT = BODY_MASS_KG * G / 2.0

SPINE_TARGETS = {
    'pelvis_tilt':  -45.0,
    'hip_flexion_r': 80.0, 'hip_flexion_l': 80.0,
    'knee_angle_r': -60.0, 'knee_angle_l': -60.0,
    'L5_S1_FE': -5.0, 'L4_L5_FE': -5.0, 'L3_L4_FE': -5.0,
    'L2_L3_FE': -5.0, 'L1_L2_FE': -5.0, 'T12_L1_FE': -3.0,
}
T_BEND_START, T_BEND_END = 0.5, 2.5
T_HOLD_END, T_STRAIGHTEN_END = 3.0, 5.0


def alpha(t):
    """Smooth S-curves, now SYMMETRIC 2 s bend / 2 s straighten so inertia
    effects are minimized and gravity dominates the L5/S1 moment profile."""
    if t < T_BEND_START: return 0.0
    if t <= T_BEND_END:
        p = (t - T_BEND_START) / (T_BEND_END - T_BEND_START)
        return float((1.0 - np.cos(np.pi * p)) / 2.0)
    if t <= T_HOLD_END: return 1.0
    if t <= T_STRAIGHTEN_END:
        p = (t - T_HOLD_END) / (T_STRAIGHTEN_END - T_HOLD_END)
        return float((1.0 + np.cos(np.pi * p)) / 2.0)
    return 0.0


def foot_angle(bs, state, side='r'):
    c = bs.get(f'calcn_{side}').getPositionInGround(state)
    t = bs.get(f'toes_{side}').getPositionInGround(state)
    dx, dy = t.get(0) - c.get(0), t.get(1) - c.get(1)
    return float(np.degrees(np.arctan2(dy, dx)))


def solve_pose(model, cs, bs, state, defaults, names, is_rot, t, target_heel_Y):
    # (1) Apply spine/hip/knee targets + provisional pelvis_ty=0, ankle=0
    for i in range(len(names)):
        cs.get(i).setValue(state, defaults[i], False)
    a = alpha(t)
    for coord, deg in SPINE_TARGETS.items():
        j = names.index(coord)
        val = (np.radians(deg) if is_rot[j] else deg) * a
        cs.get(j).setValue(state, val, False)
    cs.get('pelvis_ty').setValue(state, 0.0, False)
    cs.get('ankle_angle_r').setValue(state, 0.0, False)
    cs.get('ankle_angle_l').setValue(state, 0.0, False)
    model.assemble(state); model.realizePosition(state)
    # (2) Measure foot tilt and correct ankle (slope ~ 1:1 deg)
    fa_r = foot_angle(bs, state, 'r')
    fa_l = foot_angle(bs, state, 'l')
    cs.get('ankle_angle_r').setValue(state, np.radians(-fa_r), False)
    cs.get('ankle_angle_l').setValue(state, np.radians(-fa_l), False)
    model.assemble(state); model.realizePosition(state)
    # Second-pass polish — linearity isn't exact, residual may remain
    fa_r2 = foot_angle(bs, state, 'r')
    fa_l2 = foot_angle(bs, state, 'l')
    cur_r = cs.get('ankle_angle_r').getValue(state)
    cur_l = cs.get('ankle_angle_l').getValue(state)
    cs.get('ankle_angle_r').setValue(state, cur_r - np.radians(fa_r2), False)
    cs.get('ankle_angle_l').setValue(state, cur_l - np.radians(fa_l2), False)
    model.assemble(state); model.realizePosition(state)
    # (3) Correct pelvis_ty so calcn.Y == target_heel_Y
    y = bs.get('calcn_r').getPositionInGround(state).get(1)
    cs.get('pelvis_ty').setValue(state, target_heel_Y - y, False)
    model.assemble(state); model.realizePosition(state)


def main():
    MOT_OUT.parent.mkdir(parents=True, exist_ok=True)
    PNG_OUT.parent.mkdir(parents=True, exist_ok=True)
    model = osim.Model(MODEL); state = model.initSystem()
    cs = model.getCoordinateSet(); bs = model.getBodySet()
    n = cs.getSize()
    names = [cs.get(i).getName() for i in range(n)]
    defaults = [cs.get(i).getDefaultValue() for i in range(n)]
    is_rot = [cs.get(i).getMotionType() == 1 for i in range(n)]

    # Target heel Y at upright default
    for i in range(n): cs.get(i).setValue(state, defaults[i], False)
    model.assemble(state); model.realizePosition(state)
    target_Y = bs.get('calcn_r').getPositionInGround(state).get(1)
    print(f'[target] heel Y (upright) = {target_Y:.4f} m')

    # Motion data
    times = np.linspace(0.0, T_TOTAL, N_FRAMES)
    data = np.tile(np.array(defaults), (N_FRAMES, 1))
    for i, t in enumerate(times):
        solve_pose(model, cs, bs, state, defaults, names, is_rot, float(t), target_Y)
        for j in range(n):
            data[i, j] = cs.get(j).getValue(state)
    data_out = data.copy()
    for j in range(n):
        if is_rot[j]:
            data_out[:, j] = np.degrees(data[:, j])

    header = (
        "stoop_synthetic_v4\nversion=1\n"
        f"nRows={N_FRAMES}\nnColumns={1+n}\ninDegrees=yes\n\n"
        "Units are S.I. units (second, meters, Newtons, ...)\n\nendheader\n"
        "time\t" + "\t".join(names) + "\n"
    )
    with open(MOT_OUT, 'w') as f:
        f.write(header)
        for i, t in enumerate(times):
            f.write("\t".join([f"{t:.6f}"] + [f"{v:.6f}" for v in data_out[i]]) + "\n")
    print(f'[mot] {MOT_OUT}  ({N_FRAMES} frames)')

    # GRF file
    cols = [
        'ground_force_R_vx','ground_force_R_vy','ground_force_R_vz',
        'ground_force_R_px','ground_force_R_py','ground_force_R_pz',
        'ground_torque_R_x','ground_torque_R_y','ground_torque_R_z',
        'ground_force_L_vx','ground_force_L_vy','ground_force_L_vz',
        'ground_force_L_px','ground_force_L_py','ground_force_L_pz',
        'ground_torque_L_x','ground_torque_L_y','ground_torque_L_z',
    ]
    grf = np.zeros((N_FRAMES, len(cols)))
    for i, t in enumerate(times):
        solve_pose(model, cs, bs, state, defaults, names, is_rot, float(t), target_Y)
        fR = bs.get('calcn_r').getPositionInGround(state)
        fL = bs.get('calcn_l').getPositionInGround(state)
        grf[i, cols.index('ground_force_R_vy')] = F_PER_FOOT
        grf[i, cols.index('ground_force_L_vy')] = F_PER_FOOT
        grf[i, cols.index('ground_force_R_px')] = fR.get(0)
        grf[i, cols.index('ground_force_R_py')] = fR.get(1)
        grf[i, cols.index('ground_force_R_pz')] = fR.get(2)
        grf[i, cols.index('ground_force_L_px')] = fL.get(0)
        grf[i, cols.index('ground_force_L_py')] = fL.get(1)
        grf[i, cols.index('ground_force_L_pz')] = fL.get(2)
    ghdr = (
        f"stoop_grf_v4  body_mass={BODY_MASS_KG}kg  F_per_foot={F_PER_FOOT:.1f}N\n"
        f"version=1\nnRows={N_FRAMES}\nnColumns={1+len(cols)}\ninDegrees=no\n\n"
        "Units are S.I. units (second, meters, Newtons, ...)\n\nendheader\n"
        "time\t" + "\t".join(cols) + "\n"
    )
    with open(GRF_OUT, 'w') as f:
        f.write(ghdr)
        for i, t in enumerate(times):
            f.write("\t".join([f"{t:.6f}"] + [f"{v:.6f}" for v in grf[i]]) + "\n")
    print(f'[grf] {GRF_OUT}')
    GRF_XML_OUT.write_text(f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
  <ExternalLoads name="stoop_grf">
    <objects>
      <ExternalForce name="grf_R">
        <isDisabled>false</isDisabled>
        <applied_to_body>calcn_r</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>ground_force_R_v</force_identifier>
        <point_identifier>ground_force_R_p</point_identifier>
        <torque_identifier>ground_torque_R_</torque_identifier>
        <data_source_name>{GRF_OUT.name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="grf_L">
        <isDisabled>false</isDisabled>
        <applied_to_body>calcn_l</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>ground_force_L_v</force_identifier>
        <point_identifier>ground_force_L_p</point_identifier>
        <torque_identifier>ground_torque_L_</torque_identifier>
        <data_source_name>{GRF_OUT.name}</data_source_name>
      </ExternalForce>
    </objects>
    <groups />
    <datafile>{GRF_OUT.name}</datafile>
  </ExternalLoads>
</OpenSimDocument>
""")
    print(f'[grf xml] {GRF_XML_OUT}')

    # --- snapshot ---
    body_names = [bs.get(i).getName() for i in range(bs.getSize())]
    chains = [
        ('spine', ['pelvis','sacrum','lumbar5','lumbar4','lumbar3','lumbar2','lumbar1',
                   'thoracic12','thoracic10','thoracic8','thoracic6','thoracic4',
                   'thoracic2','thoracic1','head_neck'], 'k'),
        ('R leg', ['pelvis','femur_r','tibia_r','talus_r','calcn_r','toes_r'], 'tab:blue'),
        ('L leg', ['pelvis','femur_l','tibia_l','talus_l','calcn_l','toes_l'], 'tab:cyan'),
        ('R arm', ['thoracic1','clavicle_R','scapula_R','humerus_R','ulna_R','radius_R','hand_R'], 'tab:red'),
        ('L arm', ['thoracic1','clavicle_L','scapula_L','humerus_L','ulna_L','radius_L','hand_L'], 'tab:orange'),
    ]
    snaps = [(0.0, 'upright'), (1.5, 'mid-bend'), (2.75, 'max bend'),
             (4.0, 'mid-straight'), (5.0, 'upright')]
    fig, axes = plt.subplots(1, 5, figsize=(20, 6))
    log = []
    for ax, (t, lab) in zip(axes, snaps):
        solve_pose(model, cs, bs, state, defaults, names, is_rot, float(t), target_Y)
        pos = {}
        for nm in body_names:
            g = bs.get(nm).getPositionInGround(state)
            pos[nm] = np.array([g.get(0), g.get(1), g.get(2)])
        for _, chain, color in chains:
            xs, ys = [], []
            for b in chain:
                if b in pos:
                    xs.append(pos[b][0]); ys.append(pos[b][1])
            ax.plot(xs, ys, '-o', color=color, ms=3, lw=1.5)
        # Fill foot outline
        for side in ('r','l'):
            c = pos[f'calcn_{side}']; tp = pos[f'toes_{side}']
            ax.plot([c[0], tp[0]], [c[1], tp[1]], 'o-', color='saddlebrown', ms=6, lw=3)
        # GRF arrows
        for side, col in [('calcn_r', 'tab:green'), ('calcn_l', 'tab:olive')]:
            p = pos[side]
            ax.annotate('', xy=(p[0], p[1] + 0.18), xytext=(p[0], p[1]),
                        arrowprops=dict(arrowstyle='->', color=col, lw=2))
        ank_r = np.degrees(cs.get('ankle_angle_r').getValue(state))
        ank_l = np.degrees(cs.get('ankle_angle_l').getValue(state))
        pty = cs.get('pelvis_ty').getValue(state)
        fa = foot_angle(bs, state, 'r')
        log.append((t, pos['calcn_r'][1], pos['toes_r'][1], ank_r, fa, pty))
        ax.set_title(f't={t:.2f}s {lab}\nα={alpha(t):.2f} ankle={ank_r:+.1f}° pelvis_ty={pty:+.3f}')
        ax.axhline(target_Y, color='saddlebrown', lw=0.8, alpha=0.4)
        ax.set_xlabel('X (m)'); ax.set_ylabel('Y (m)')
        ax.set_aspect('equal'); ax.grid(True, alpha=0.3)
        ax.set_xlim(-0.6, 1.0); ax.set_ylim(-1.1, 0.8)
    fig.suptitle('Stoop v5 — slow symmetric 2 s bend / 2 s straighten (flat feet)')
    plt.tight_layout()
    plt.savefig(PNG_OUT, dpi=120, bbox_inches='tight')
    print(f'[png] {PNG_OUT}')

    print('\n--- Verification (heel_Y, toes_Y should match target) ---')
    for t, hy, ty, ak, fa, pty in log:
        print(f'  t={t:.2f}s  heel_Y={hy:+.4f}  toes_Y={ty:+.4f}  '
              f'foot_angle={fa:+.2f}°  ankle={ak:+.1f}°  pelvis_ty={pty:+.4f}')


if __name__ == '__main__':
    main()
