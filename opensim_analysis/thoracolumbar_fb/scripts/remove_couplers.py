"""Step 2.B.1 — Remove 4 shoulder coupler constraints from ThoracolumbarFB model.

Creates two no-coupler variants:
  MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler.osim   (Phase 1a base)
  MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim     (box motion base)

Validation:
  - initSystem() succeeds
  - ConstraintSet has 0 entries
  - assemble() at neutral and stoop poses succeeds
  - Shoulder is independent of pelvis_tilt (no enforcement)
"""
import os
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
import numpy as np
import opensim as osim
import shutil

SRC = [
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_moco_stoop.osim',
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim',
]
COUPLERS = ['coupler_shoulder_elv_r', 'coupler_shoulder_elv_l',
            'coupler_elv_angle_r', 'coupler_elv_angle_l']


def remove_and_save(src):
    base = src[:-5]
    dst = base + '_no_coupler.osim'
    print(f'\n=== Processing {os.path.basename(src)} ===')

    # Use OpenSim API: load, remove constraints, save
    m = osim.Model(src)
    state = m.initSystem()
    cs = m.getConstraintSet()
    print(f'  Initial constraints: {cs.getSize()}')
    for i in range(cs.getSize()):
        print(f'    [{i}] {cs.get(i).getName()}')
    removed = []
    for nm in COUPLERS:
        try:
            cs.remove(cs.get(nm))
            removed.append(nm)
        except Exception as e:
            print(f'  WARN: failed to remove {nm}: {e}')
    print(f'  Removed: {removed}')
    print(f'  Constraints after removal: {cs.getSize()}')
    m.printToXML(dst)
    print(f'  Saved {dst}')

    # Validation
    print(f'\n  --- Validation ---')
    m2 = osim.Model(dst)
    state2 = m2.initSystem()
    cs2 = m2.getConstraintSet()
    print(f'  reload constraints: {cs2.getSize()}')
    coords = m2.getCoordinateSet()
    names_idx = {coords.get(i).getName(): i for i in range(coords.getSize())}

    # Test 1: neutral pose
    for i in range(coords.getSize()):
        coords.get(i).setValue(state2, coords.get(i).getDefaultValue(), False)
    m2.assemble(state2)
    print(f'  neutral pose: assemble OK')

    # Test 2: stoop pose with shoulder hanging
    coords.get(names_idx['pelvis_tilt']).setValue(state2, np.radians(-40), False)
    coords.get(names_idx['hip_flexion_r']).setValue(state2, np.radians(110), False)
    coords.get(names_idx['hip_flexion_l']).setValue(state2, np.radians(110), False)
    coords.get(names_idx['knee_angle_r']).setValue(state2, np.radians(-45), False)
    coords.get(names_idx['knee_angle_l']).setValue(state2, np.radians(-45), False)
    for nm in ['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE','T12_L1_FE']:
        if nm in names_idx:
            coords.get(names_idx[nm]).setValue(state2, np.radians(-10), False)
    coords.get(names_idx['shoulder_elv_r']).setValue(state2, 0.0, False)
    coords.get(names_idx['shoulder_elv_l']).setValue(state2, 0.0, False)
    coords.get(names_idx['elv_angle_r']).setValue(state2, 0.0, False)
    coords.get(names_idx['elv_angle_l']).setValue(state2, 0.0, False)
    m2.assemble(state2)
    sh_e_r = np.degrees(coords.get(names_idx['shoulder_elv_r']).getValue(state2))
    sh_e_l = np.degrees(coords.get(names_idx['shoulder_elv_l']).getValue(state2))
    elv_r = np.degrees(coords.get(names_idx['elv_angle_r']).getValue(state2))
    print(f'  stoop pose with sh_elv set to 0:')
    print(f'    pelvis_tilt = -40°')
    print(f'    sh_elv_r after assemble = {sh_e_r:+.3f}°  (expect 0 if coupler gone)')
    print(f'    sh_elv_l after assemble = {sh_e_l:+.3f}°  (expect 0)')
    print(f'    elv_angle_r after assemble = {elv_r:+.3f}°  (expect 0)')
    if abs(sh_e_r) < 0.1 and abs(sh_e_l) < 0.1:
        print(f'    PASS: coupler removed (sh_elv stays at user-set 0)')
    else:
        print(f'    FAIL: coupler still active')

    # Test 3: shoulder set to specific value, ensure not overridden
    coords.get(names_idx['shoulder_elv_r']).setValue(state2, np.radians(20), False)
    m2.assemble(state2)
    sh_e_r = np.degrees(coords.get(names_idx['shoulder_elv_r']).getValue(state2))
    print(f'  set sh_elv_r=20°, after assemble: {sh_e_r:+.3f}° (expect 20)')

    return dst


def main():
    outs = []
    for s in SRC:
        if not os.path.exists(s):
            print(f'SKIP {s} (not found)')
            continue
        outs.append(remove_and_save(s))
    print(f'\n=== Done ===')
    for o in outs:
        print(f'  {o}')


if __name__ == '__main__':
    main()
