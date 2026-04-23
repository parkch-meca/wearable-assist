"""Generate stoop_box20kg_v2.mot — deeper bend so hands reach the box TOP
surface (y ≈ -0.63 m), not the floor.

Delta from v1 (stoop_box20kg.mot / gen_stoop_box_motion.py):
  hip_flexion_r/l: 80  -> 86  (+6)
  knee_angle_r/l: -60 -> -70  (-10, more flexion in this model's sign convention)
  ankle_angle_r/l: 0 -> +4    (NEW: dorsiflexion, balance)
  pelvis_ty:      -0.22 -> -0.32  (-0.10, pelvis drops further for deeper squat)

All other targets unchanged. Arms stay passive (all arm coords = 0).
Original v1 motion is preserved at /data/stoop_motion/stoop_box20kg.mot.
"""
import numpy as np
import opensim as osim
from pathlib import Path

MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim'
MOT_OUT = Path('/data/stoop_motion/stoop_box20kg_v2.mot')

FPS = 120
T_TOTAL = 3.0
N_FRAMES = int(T_TOTAL * FPS) + 1

SPINE_TARGETS = {
    'pelvis_tilt':   -45.0,
    'pelvis_ty':     -0.32,      # v1: -0.22  → v2: -0.32 (−0.10 m extra drop)
    'hip_flexion_r':  86.0, 'hip_flexion_l':  86.0,   # v1: 80 → v2: 86 (+6)
    'knee_angle_r':  -70.0, 'knee_angle_l':  -70.0,   # v1:-60 → v2:-70 (-10)
    'ankle_angle_r':   4.0, 'ankle_angle_l':   4.0,   # v1: 0 → v2: +4 (NEW)
    'L5_S1_FE': -5.0, 'L4_L5_FE': -5.0, 'L3_L4_FE': -5.0,
    'L2_L3_FE': -5.0, 'L1_L2_FE': -5.0, 'T12_L1_FE': -3.0,
}


def alpha_spine(t):
    if t < 1.0:  return 0.0
    if t <= 2.0: return (1.0 - np.cos(np.pi * (t - 1.0))) / 2.0
    if t <= 3.0: return (1.0 + np.cos(np.pi * (t - 2.0))) / 2.0
    return 0.0


def main():
    MOT_OUT.parent.mkdir(parents=True, exist_ok=True)
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
        for j in range(n):
            cs.get(j).setValue(state, defaults[j], False)
        a = alpha_spine(t)
        for coord, target in SPINE_TARGETS.items():
            j = names.index(coord)
            val = (np.radians(target) if is_rot[j] else target) * a
            cs.get(j).setValue(state, val, False)
        model.assemble(state)
        for j in range(n):
            data_native[i, j] = cs.get(j).getValue(state)

    data_out = data_native.copy()
    for j in range(n):
        if is_rot[j]:
            data_out[:, j] = np.degrees(data_native[:, j])

    header = (
        "stoop_box20kg_v2\nversion=1\n"
        f"nRows={N_FRAMES}\nnColumns={1+n}\ninDegrees=yes\n\n"
        "Units are S.I. units (second, meters, Newtons, ...)\n\nendheader\n"
        "time\t" + "\t".join(names) + "\n"
    )
    with open(MOT_OUT, 'w') as f:
        f.write(header)
        for i, t in enumerate(times):
            f.write("\t".join([f"{t:.6f}"] + [f"{v:.6f}" for v in data_out[i]]) + "\n")
    print(f"[mot] {MOT_OUT}  ({N_FRAMES} frames)")


if __name__ == '__main__':
    main()
