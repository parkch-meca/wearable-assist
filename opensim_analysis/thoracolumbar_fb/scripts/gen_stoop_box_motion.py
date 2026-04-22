"""Generate stoop_box20kg.mot — deep-bend stoop with arms completely passive.

Per user spec:
  - shoulders/elbows UNCHANGED (all arm coords = 0)
  - knee flexed to -60° (deep squat) so hands reach floor
  - hip_flexion 80°, pelvis_tilt -45°
  - pelvis drops (pelvis_ty negative) so feet stay on floor in deep squat
"""
import opensim as osim
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim'
MOT_OUT = Path('/data/stoop_motion/stoop_box20kg.mot')
PNG_OUT = Path('/data/opensim_results/stoop_box_motion_check_v4.png')

FPS = 120
T_TOTAL = 3.0
N_FRAMES = int(T_TOTAL * FPS) + 1

BOX_W, BOX_H = 0.22, 0.18
# Box pre-grasp position — set at runtime to match the hand's actual reach
# at t=2s so visually the box is exactly where the hand arrives.
BOX_FLOOR_FIXED = None

SPINE_TARGETS = {
    'pelvis_tilt':  -45.0,
    'pelvis_ty':    -0.22,    # drop pelvis so feet stay near floor in deep squat
    'hip_flexion_r': 80.0, 'hip_flexion_l': 80.0,
    'knee_angle_r': -60.0, 'knee_angle_l': -60.0,
    'L5_S1_FE': -5.0, 'L4_L5_FE': -5.0, 'L3_L4_FE': -5.0,
    'L2_L3_FE': -5.0, 'L1_L2_FE': -5.0, 'T12_L1_FE': -3.0,
}
# No arm targets — shoulders/elbows stay at defaults (passive).


def alpha_spine(t):
    if t < 1.0:  return 0.0
    if t <= 2.0: return (1.0 - np.cos(np.pi * (t - 1.0))) / 2.0
    if t <= 3.0: return (1.0 + np.cos(np.pi * (t - 2.0))) / 2.0
    return 0.0


def set_state_at(model, cs, state, defaults, names, is_rot, t):
    for i in range(len(names)):
        cs.get(i).setValue(state, defaults[i], False)
    a = alpha_spine(t)
    for coord, target in SPINE_TARGETS.items():
        j = names.index(coord)
        val = (np.radians(target) if is_rot[j] else target) * a
        cs.get(j).setValue(state, val, False)
    model.assemble(state)  # enforce coupler constraints (shoulder compensation)


def main():
    MOT_OUT.parent.mkdir(parents=True, exist_ok=True)
    PNG_OUT.parent.mkdir(parents=True, exist_ok=True)

    model = osim.Model(MODEL)
    state = model.initSystem()
    cs = model.getCoordinateSet()
    n = cs.getSize()
    names = [cs.get(i).getName() for i in range(n)]
    defaults = [cs.get(i).getDefaultValue() for i in range(n)]
    is_rot = [cs.get(i).getMotionType() == 1 for i in range(n)]

    times = np.linspace(0.0, T_TOTAL, N_FRAMES)
    data_native = np.tile(np.array(defaults), (N_FRAMES, 1))
    for i, t in enumerate(times):
        # Set state including spine targets, assemble (enforces coupler), then
        # read back ALL coord values (so dependent shoulder_elv / elv_angle values
        # are captured from the constraint).
        set_state_at(model, cs, state, defaults, names, is_rot, t)
        for j in range(n):
            data_native[i, j] = cs.get(j).getValue(state)

    data_out = data_native.copy()
    for j in range(n):
        if is_rot[j]:
            data_out[:, j] = np.degrees(data_native[:, j])

    header = (
        "stoop_box20kg\nversion=1\n"
        f"nRows={N_FRAMES}\nnColumns={1+n}\ninDegrees=yes\n\n"
        "Units are S.I. units (second, meters, Newtons, ...)\n\nendheader\n"
        "time\t" + "\t".join(names) + "\n"
    )
    with open(MOT_OUT, 'w') as f:
        f.write(header)
        for i, t in enumerate(times):
            f.write("\t".join([f"{t:.6f}"] + [f"{v:.6f}" for v in data_out[i]]) + "\n")
    print(f"[mot] {MOT_OUT}  ({N_FRAMES} frames)")

    # --- snapshot ---
    bs = model.getBodySet()
    body_names = [bs.get(i).getName() for i in range(bs.getSize())]
    chains = [
        ('spine',  ['pelvis','sacrum','lumbar5','lumbar4','lumbar3','lumbar2','lumbar1',
                    'thoracic12','thoracic10','thoracic8','thoracic6','thoracic4',
                    'thoracic2','thoracic1','head_neck'], 'k'),
        ('R leg',  ['pelvis','femur_r','tibia_r','talus_r','calcn_r','toes_r'], 'tab:blue'),
        ('L leg',  ['pelvis','femur_l','tibia_l','talus_l','calcn_l','toes_l'], 'tab:cyan'),
        ('R arm',  ['thoracic1','clavicle_R','scapula_R','humerus_R','ulna_R','radius_R','hand_R'], 'tab:red'),
        ('L arm',  ['thoracic1','clavicle_L','scapula_L','humerus_L','ulna_L','radius_L','hand_L'], 'tab:orange'),
    ]
    snapshots = [('t=0.0s upright', 0.0),
                 ('t=2.0s bend (grasp)', 2.0),
                 ('t=3.0s upright (carry)', 3.0)]
    fig, axes = plt.subplots(1, 3, figsize=(15, 7))
    log = {}

    # Compute box pre-grasp position = mid-hand at t=2
    set_state_at(model, cs, state, defaults, names, is_rot, 2.0)
    model.realizePosition(state)
    h2R = bs.get('hand_R').getPositionInGround(state)
    h2L = bs.get('hand_L').getPositionInGround(state)
    BOX_PRE = (0.5 * (h2R.get(0) + h2L.get(0)),
               0.5 * (h2R.get(1) + h2L.get(1)))
    print(f'[box] pre-grasp at {BOX_PRE}')
    for ax, (label, t) in zip(axes, snapshots):
        set_state_at(model, cs, state, defaults, names, is_rot, t)
        model.realizePosition(state)
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

        hR = pos['hand_R']; hL = pos['hand_L']; fR = pos['calcn_r']
        log[t] = {'hand_R': hR, 'hand_L': hL, 'foot_R': fR}
        for side, col in [('hand_R','tab:red'), ('hand_L','tab:orange')]:
            p = pos[side]
            ax.plot(p[0], p[1], 'o', color=col, ms=10, markeredgecolor='k')

        if t < 2.0 - 1e-6:
            bx_c, by_c = BOX_PRE
            phase = 'pre-grasp'
        else:
            bx_c = 0.5 * (hR[0] + hL[0])
            by_c = 0.5 * (hR[1] + hL[1])
            phase = 'lifted'
        ax.add_patch(plt.Rectangle(
            (bx_c - BOX_W/2, by_c - BOX_H/2), BOX_W, BOX_H,
            facecolor='peru', edgecolor='saddlebrown', alpha=0.65))
        ax.text(bx_c, by_c, '20 kg', ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        # floor line — follow feet height at each frame
        ax.axhline(fR[1], color='saddlebrown', lw=0.8, alpha=0.5)
        ax.set_title(f'{label}  (box: {phase})')
        ax.set_xlabel('X forward (m)'); ax.set_ylabel('Y up (m)')
        ax.set_aspect('equal'); ax.grid(True, alpha=0.3)
        ax.set_xlim(-0.8, 1.2); ax.set_ylim(-1.1, 0.8)

    fig.suptitle('Stoop + 20 kg box lift — deep squat, arms fully passive')
    plt.tight_layout()
    plt.savefig(PNG_OUT, dpi=120, bbox_inches='tight')
    print(f'[png] {PNG_OUT}')

    print('\n--- Positions (X, Y) ---')
    for t, d in log.items():
        hR, hL, fR = d['hand_R'], d['hand_L'], d['foot_R']
        print(f'  t={t:.1f}s  hand_R=({hR[0]:+.3f},{hR[1]:+.3f})  '
              f'hand_L=({hL[0]:+.3f},{hL[1]:+.3f})  foot_R=({fR[0]:+.3f},{fR[1]:+.3f})')


if __name__ == '__main__':
    main()
