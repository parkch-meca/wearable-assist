"""Convert ThoracolumbarFB locked-coordinate joints to WeldJoints for Moco.

This model is derived for sagittal-plane stoop/lift analysis.
Welded DOFs and rationale:

- Group A (rib-spine T1-T12 Y+Z rotation, 48 coords):
  Non-sagittal vertebra rotation not involved in stoop/lift.

- Group B (rib1 → sternum translation, 3 coords):
  Structural fixation, no respiratory dynamics modeled.

- Group C (forearm pro/sup, 2 coords):
  Current scope uses neutral grip for 2-handed box lift.
  Unlock needed for future reach/overhead analyses
  → derive separate model variant (*_moco_reach.osim).

- Group D (wrist deviation + flexion, 4 coords):
  Box grip assumed rigid. Coupled motion would require
  CoordinateCouplerConstraint support in Moco (untested).
  Unlock in future grip-focused analyses → separate variant.

Total: 29 WeldJoints replacing CustomJoints with locked coords,
57 coordinates removed from the optimization.

Usage:
  python prepare_model_for_moco.py
  → produces MaleFullBodyModel_v2.0_OS4_moco_stoop.osim
"""
import json
from pathlib import Path
import opensim as osim

SRC = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim'
DST = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_moco_stoop.osim'


# All 29 joints to be replaced with WeldJoints. Listed alphabetically per group.
WELD_JOINTS = [
    # Group A: costovertebral bilateral × T1–T12 (24 joints)
    'T1_r1R_CVjnt', 'T2_r2R_CVjnt', 'T3_r3R_CVjnt', 'T4_r4R_CVjnt',
    'T5_r5R_CVjnt', 'T6_r6R_CVjnt', 'T7_r7R_CVjnt', 'T8_r8R_CVjnt',
    'T9_r9R_CVjnt', 'T10_r10R_CVjnt', 'T11_r11R_CVjnt', 'T12_r12R_CVjnt',
    'T1_r1L_CVjnt', 'T2_r2L_CVjnt', 'T3_r3L_CVjnt', 'T4_r4L_CVjnt',
    'T5_r5L_CVjnt', 'T6_r6L_CVjnt', 'T7_r7L_CVjnt', 'T8_r8L_CVjnt',
    'T9_r9L_CVjnt', 'T10_r10L_CVjnt', 'T11_r11L_CVjnt', 'T12_r12L_CVjnt',
    # Group B: sternum
    'r1R_sterR_jnt',
    # Group C: radioulnar (pronation/supination)
    'radioulnar', 'radioulnar_l',
    # Group D: radius_hand (wrist flex + dev, coupled motion)
    'radius_hand_r', 'radius_hand_l',
]


def _vec3(v):
    """Build Vec3 from OpenSim's get_translation/get_orientation result."""
    return osim.Vec3(v.get(0), v.get(1), v.get(2))


def extract_frame_offset(frame):
    """Return (base_body, location_in_base, orientation_in_base) for a frame.
    If frame is a PhysicalOffsetFrame, read its translation/orientation relative
    to its parent (which should be the base body). Otherwise the frame IS the
    base body with zero offset."""
    pof = osim.PhysicalOffsetFrame.safeDownCast(frame)
    if pof is None:
        base = frame  # already a Body / Ground
        return base, osim.Vec3(0, 0, 0), osim.Vec3(0, 0, 0)
    base = pof.findBaseFrame()
    return base, _vec3(pof.get_translation()), _vec3(pof.get_orientation())


def replace_with_weld(model, joint_name):
    js = model.getJointSet()
    old_joint = js.get(joint_name)
    parent_frame = old_joint.getParentFrame()
    child_frame = old_joint.getChildFrame()
    p_base, p_loc, p_orient = extract_frame_offset(parent_frame)
    c_base, c_loc, c_orient = extract_frame_offset(child_frame)

    # Construct new WeldJoint with same offsets so kinematics at default pose
    # match the original (coords were all locked at 0, so the transform is fixed).
    new_weld = osim.WeldJoint(
        joint_name,
        osim.PhysicalFrame.safeDownCast(p_base), p_loc, p_orient,
        osim.PhysicalFrame.safeDownCast(c_base), c_loc, c_orient,
    )

    # Remove old joint and append new weld.
    # Note: OpenSim Python API doesn't provide a direct 'remove joint by index'
    # but we can use cloneAndAppend + delete via index.
    for i in range(js.getSize()):
        if js.get(i).getName() == joint_name:
            js.remove(i)
            break
    model.addJoint(new_weld)


def main():
    m = osim.Model(SRC)
    m.initSystem()
    print(f'[src] {SRC}')
    print(f'  muscles   : {m.getMuscles().getSize()}')
    print(f'  coords    : {m.getCoordinateSet().getSize()}')
    print(f'  bodies    : {m.getBodySet().getSize()}')
    print(f'  joints    : {m.getJointSet().getSize()}')

    # Capture baseline body positions at default pose for kinematic verification.
    state0 = m.initSystem()
    bs = m.getBodySet()
    baseline_pos = {}
    for i in range(bs.getSize()):
        b = bs.get(i)
        p = b.getPositionInGround(state0)
        baseline_pos[b.getName()] = (p.get(0), p.get(1), p.get(2))

    # Replace each target joint with a WeldJoint.
    for jn in WELD_JOINTS:
        replace_with_weld(m, jn)
    m.finalizeConnections()

    # Reinitialize and confirm.
    state1 = m.initSystem()
    print(f'\n[after weld] total {len(WELD_JOINTS)} joints welded')
    print(f'  muscles   : {m.getMuscles().getSize()}')
    print(f'  coords    : {m.getCoordinateSet().getSize()}')
    print(f'  bodies    : {m.getBodySet().getSize()}')
    print(f'  joints    : {m.getJointSet().getSize()}')

    # Kinematic verification: compare body positions in default pose
    bs2 = m.getBodySet()
    max_err = 0.0
    worst = ''
    for i in range(bs2.getSize()):
        b = bs2.get(i)
        p = b.getPositionInGround(state1)
        x, y, z = p.get(0), p.get(1), p.get(2)
        b0 = baseline_pos.get(b.getName())
        if b0 is None:
            continue
        err = max(abs(x - b0[0]), abs(y - b0[1]), abs(z - b0[2]))
        if err > max_err:
            max_err = err; worst = b.getName()
    print(f'  kinematic max error: {max_err*1000:.3f} mm at {worst}')

    # Save
    m.printToXML(DST)
    print(f'\n[dst] {DST}')


if __name__ == '__main__':
    main()
