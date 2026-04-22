#!/usr/bin/env python3
"""
Convert BONES-SEED SOMA BVH files to OpenSim .mot format for Rajagopal2016 model.

SOMA BVH: 77 joints, 120fps, Euler angles in degrees (ZYX root rotation order)
OpenSim Rajagopal: 39 coordinates, degrees

Usage:
    python convert_bvh_to_opensim.py <bvh_file> [--output <output.mot>] [--fps 120]
    python convert_bvh_to_opensim.py /data/bones-seed/soma_uniform/bvh/221125/neutral_stoop_down_R_002__A073.bvh

Author: auto-generated for wearable exosuit research pipeline
"""

import argparse
import re
import numpy as np
import os
from dataclasses import dataclass, field


# ─── BVH Parser ──────────────────────────────────────────────────────────────

@dataclass
class BVHJoint:
    name: str
    offset: np.ndarray
    channels: list
    children: list = field(default_factory=list)
    channel_indices: list = field(default_factory=list)  # global indices into frame data


def parse_bvh(filepath):
    """Parse a BVH file and return the skeleton hierarchy + motion data."""
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    # ── Parse HIERARCHY ──
    idx = 0
    assert lines[idx] == "HIERARCHY", f"Expected HIERARCHY, got {lines[idx]}"
    idx += 1

    joints = {}
    joint_stack = []
    channel_count = 0
    root_name = None

    while idx < len(lines) and lines[idx] != "MOTION":
        line = lines[idx]
        parts = line.split()

        if parts[0] in ("ROOT", "JOINT"):
            name = parts[1]
            if parts[0] == "ROOT":
                root_name = name
            idx += 1  # skip '{'

            # Read OFFSET
            idx += 1
            offset_parts = lines[idx].split()
            assert offset_parts[0] == "OFFSET"
            offset = np.array([float(x) for x in offset_parts[1:4]])

            # Read CHANNELS
            idx += 1
            chan_parts = lines[idx].split()
            assert chan_parts[0] == "CHANNELS"
            n_chan = int(chan_parts[1])
            channels = chan_parts[2:2+n_chan]

            joint = BVHJoint(
                name=name,
                offset=offset,
                channels=channels,
                channel_indices=list(range(channel_count, channel_count + n_chan))
            )
            channel_count += n_chan
            joints[name] = joint

            if joint_stack:
                joints[joint_stack[-1]].children.append(name)

            joint_stack.append(name)

        elif parts[0] == "End":
            # End Site — skip offset + closing brace
            idx += 1  # {
            idx += 1  # OFFSET line
            idx += 1  # }

        elif parts[0] == "}":
            if joint_stack:
                joint_stack.pop()

        idx += 1

    # ── Parse MOTION ──
    assert lines[idx] == "MOTION"
    idx += 1

    frames_line = lines[idx].split()
    n_frames = int(frames_line[1])
    idx += 1

    frametime_line = lines[idx].split()
    frame_time = float(frametime_line[2])  # "Frame Time: 0.008333"
    idx += 1

    motion_data = np.zeros((n_frames, channel_count))
    for f in range(n_frames):
        if idx + f < len(lines):
            vals = lines[idx + f].split()
            motion_data[f, :len(vals)] = [float(v) for v in vals[:channel_count]]

    return joints, root_name, motion_data, frame_time, n_frames


# ─── SOMA → OpenSim Joint Mapping ────────────────────────────────────────────

# SOMA 77-joint skeleton → Rajagopal 39-coordinate mapping
# SOMA joints (estimated from standard humanoid BVH):
#   Hips (root), Spine, Spine1, Spine2, Neck, Head,
#   LeftUpLeg, LeftLeg, LeftFoot, LeftToeBase,
#   RightUpLeg, RightLeg, RightFoot, RightToeBase,
#   LeftShoulder, LeftArm, LeftForeArm, LeftHand,
#   RightShoulder, RightArm, RightForeArm, RightHand,
#   + finger joints + face joints

# This mapping will be refined once actual SOMA joint names are known.
# For now, use common BVH naming conventions.

SOMA_TO_OPENSIM = {
    # Pelvis (root) — SOMA root has 6 channels: Xpos Ypos Zpos Zrot Yrot Xrot
    'pelvis_tilt': {
        'joint': 'ROOT',  # will be replaced with actual root name
        'channel': 'Xrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
    'pelvis_list': {
        'joint': 'ROOT',
        'channel': 'Zrotation',
        'scale': -1.0,
        'offset': 0.0,
    },
    'pelvis_rotation': {
        'joint': 'ROOT',
        'channel': 'Yrotation',
        'scale': -1.0,
        'offset': 0.0,
    },
    'pelvis_tx': {
        'joint': 'ROOT',
        'channel': 'Xposition',
        'scale': 0.01,  # BVH cm → OpenSim m (adjust if BVH is in m)
        'offset': 0.0,
    },
    'pelvis_ty': {
        'joint': 'ROOT',
        'channel': 'Yposition',
        'scale': 0.01,
        'offset': 0.0,
    },
    'pelvis_tz': {
        'joint': 'ROOT',
        'channel': 'Zposition',
        'scale': 0.01,
        'offset': 0.0,
    },

    # Lumbar — mapped from spine joints
    # SOMA likely has Spine, Spine1, Spine2 → combine or use first
    'lumbar_extension': {
        'joint': 'Spine',
        'channel': 'Xrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
    'lumbar_bending': {
        'joint': 'Spine',
        'channel': 'Zrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
    'lumbar_rotation': {
        'joint': 'Spine',
        'channel': 'Yrotation',
        'scale': 1.0,
        'offset': 0.0,
    },

    # Right hip
    'hip_flexion_r': {
        'joint': 'RightUpLeg',
        'channel': 'Xrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
    'hip_adduction_r': {
        'joint': 'RightUpLeg',
        'channel': 'Zrotation',
        'scale': -1.0,
        'offset': 0.0,
    },
    'hip_rotation_r': {
        'joint': 'RightUpLeg',
        'channel': 'Yrotation',
        'scale': -1.0,
        'offset': 0.0,
    },

    # Right knee
    'knee_angle_r': {
        'joint': 'RightLeg',
        'channel': 'Xrotation',
        'scale': 1.0,
        'offset': 0.0,
    },

    # Right ankle
    'ankle_angle_r': {
        'joint': 'RightFoot',
        'channel': 'Xrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
    'subtalar_angle_r': {
        'joint': 'RightFoot',
        'channel': 'Zrotation',
        'scale': 1.0,
        'offset': 0.0,
    },

    # Left hip
    'hip_flexion_l': {
        'joint': 'LeftUpLeg',
        'channel': 'Xrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
    'hip_adduction_l': {
        'joint': 'LeftUpLeg',
        'channel': 'Zrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
    'hip_rotation_l': {
        'joint': 'LeftUpLeg',
        'channel': 'Yrotation',
        'scale': 1.0,
        'offset': 0.0,
    },

    # Left knee
    'knee_angle_l': {
        'joint': 'LeftLeg',
        'channel': 'Xrotation',
        'scale': 1.0,
        'offset': 0.0,
    },

    # Left ankle
    'ankle_angle_l': {
        'joint': 'LeftFoot',
        'channel': 'Xrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
    'subtalar_angle_l': {
        'joint': 'LeftFoot',
        'channel': 'Zrotation',
        'scale': 1.0,
        'offset': 0.0,
    },

    # Right arm
    'arm_flex_r': {
        'joint': 'RightArm',
        'channel': 'Xrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
    'arm_add_r': {
        'joint': 'RightArm',
        'channel': 'Zrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
    'arm_rot_r': {
        'joint': 'RightArm',
        'channel': 'Yrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
    'elbow_flex_r': {
        'joint': 'RightForeArm',
        'channel': 'Xrotation',
        'scale': 1.0,
        'offset': 0.0,
    },

    # Left arm
    'arm_flex_l': {
        'joint': 'LeftArm',
        'channel': 'Xrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
    'arm_add_l': {
        'joint': 'LeftArm',
        'channel': 'Zrotation',
        'scale': -1.0,
        'offset': 0.0,
    },
    'arm_rot_l': {
        'joint': 'LeftArm',
        'channel': 'Yrotation',
        'scale': -1.0,
        'offset': 0.0,
    },
    'elbow_flex_l': {
        'joint': 'LeftForeArm',
        'channel': 'Xrotation',
        'scale': 1.0,
        'offset': 0.0,
    },
}


def get_channel_value(joints, joint_name, channel_name, motion_data, frame_idx):
    """Extract a specific channel value from a frame of motion data."""
    if joint_name not in joints:
        return 0.0
    joint = joints[joint_name]
    for i, ch in enumerate(joint.channels):
        if ch == channel_name:
            global_idx = joint.channel_indices[i]
            return motion_data[frame_idx, global_idx]
    return 0.0


def auto_detect_joint_names(joints):
    """
    Auto-detect SOMA joint names and update the mapping.
    SOMA uses its own naming convention — this function tries common patterns.
    """
    joint_names = list(joints.keys())
    name_map = {}

    # Common BVH naming patterns to search for
    patterns = {
        'ROOT': [r'^(Hips|Root|root|SOMA_Root|pelvis)$'],
        'Spine': [r'^(Spine|spine|Spine_0|LowerSpine)$'],
        'RightUpLeg': [r'^(RightUpLeg|right_hip|R_Hip|RHip|Right_Hip)$'],
        'RightLeg': [r'^(RightLeg|right_knee|R_Knee|RKnee|Right_Knee)$'],
        'RightFoot': [r'^(RightFoot|right_ankle|R_Ankle|RAnkle|Right_Ankle)$'],
        'LeftUpLeg': [r'^(LeftUpLeg|left_hip|L_Hip|LHip|Left_Hip)$'],
        'LeftLeg': [r'^(LeftLeg|left_knee|L_Knee|LKnee|Left_Knee)$'],
        'LeftFoot': [r'^(LeftFoot|left_ankle|L_Ankle|LAnkle|Left_Ankle)$'],
        'RightArm': [r'^(RightArm|right_shoulder|R_Shoulder|RShoulder|Right_Shoulder)$'],
        'RightForeArm': [r'^(RightForeArm|right_elbow|R_Elbow|RElbow|Right_Elbow)$'],
        'LeftArm': [r'^(LeftArm|left_shoulder|L_Shoulder|LShoulder|Left_Shoulder)$'],
        'LeftForeArm': [r'^(LeftForeArm|left_elbow|L_Elbow|LElbow|Left_Elbow)$'],
    }

    for standard_name, regex_list in patterns.items():
        for jn in joint_names:
            for pat in regex_list:
                if re.match(pat, jn, re.IGNORECASE):
                    name_map[standard_name] = jn
                    break

    return name_map


def convert_bvh_to_mot(bvh_path, output_path=None, target_fps=None, print_info=True):
    """
    Convert a SOMA BVH file to OpenSim .mot format.

    Parameters
    ----------
    bvh_path : str
        Path to BVH file
    output_path : str, optional
        Output .mot path. Defaults to same name with .mot extension.
    target_fps : float, optional
        Downsample to this fps. Default: keep original.
    print_info : bool
        Print diagnostic info
    """
    if output_path is None:
        output_path = os.path.splitext(bvh_path)[0] + ".mot"

    # Parse BVH
    joints, root_name, motion_data, frame_time, n_frames = parse_bvh(bvh_path)
    src_fps = 1.0 / frame_time

    if print_info:
        print(f"BVH: {os.path.basename(bvh_path)}")
        print(f"  Joints: {len(joints)}")
        print(f"  Frames: {n_frames}, FPS: {src_fps:.1f}, Duration: {n_frames * frame_time:.2f}s")
        print(f"  Joint names: {list(joints.keys())[:15]}...")

    # Auto-detect joint names
    name_map = auto_detect_joint_names(joints)

    # Replace generic names with actual SOMA names
    # Also handle ROOT substitution
    if root_name and 'ROOT' not in name_map:
        name_map['ROOT'] = root_name

    if print_info:
        print(f"  Name mapping: {name_map}")

    # Downsample if requested
    if target_fps and target_fps < src_fps:
        step = int(round(src_fps / target_fps))
        frame_indices = list(range(0, n_frames, step))
        effective_fps = src_fps / step
    else:
        frame_indices = list(range(n_frames))
        effective_fps = src_fps

    # Build OpenSim coordinate names
    coord_names = list(SOMA_TO_OPENSIM.keys())

    # Detect position scale: check if root Y-position (height) suggests cm or m
    root_joint = joints.get(name_map.get('ROOT', root_name))
    if root_joint:
        y_idx = None
        for i, ch in enumerate(root_joint.channels):
            if ch == 'Yposition':
                y_idx = root_joint.channel_indices[i]
                break
        if y_idx is not None:
            y_val = motion_data[0, y_idx]
            if y_val > 10:  # likely cm
                pos_scale = 0.01
            else:
                pos_scale = 1.0
            if print_info:
                print(f"  Root Y-position frame 0: {y_val:.3f} → scale={pos_scale} (→ {y_val*pos_scale:.3f}m)")

            # Update position scales
            for coord in ['pelvis_tx', 'pelvis_ty', 'pelvis_tz']:
                if coord in SOMA_TO_OPENSIM:
                    SOMA_TO_OPENSIM[coord]['scale'] = pos_scale

    # Write .mot file
    n_out = len(frame_indices)
    duration = (frame_indices[-1]) * frame_time

    with open(output_path, 'w') as f:
        f.write(f"{os.path.basename(bvh_path)}_converted\n")
        f.write("version=1\n")
        f.write(f"nRows={n_out}\n")
        f.write(f"nColumns={len(coord_names)+1}\n")
        f.write("inDegrees=yes\n")
        f.write("endheader\n")
        f.write("time\t" + "\t".join(coord_names) + "\n")

        for fi in frame_indices:
            t = fi * frame_time
            vals = []
            for coord_name in coord_names:
                spec = SOMA_TO_OPENSIM[coord_name]
                soma_joint = name_map.get(spec['joint'], spec['joint'])
                channel = spec['channel']
                scale = spec['scale']
                offset = spec['offset']

                raw = get_channel_value(joints, soma_joint, channel, motion_data, fi)
                vals.append(f"{raw * scale + offset:.6f}")

            f.write(f"{t:.6f}\t" + "\t".join(vals) + "\n")

    if print_info:
        print(f"\nOutput: {output_path}")
        print(f"  Frames: {n_out}, FPS: {effective_fps:.1f}, Duration: {duration:.2f}s")
        # Print key angles at first/mid/last frame
        for label, fi in [("First", frame_indices[0]), ("Mid", frame_indices[len(frame_indices)//2]), ("Last", frame_indices[-1])]:
            hip_r = get_channel_value(joints, name_map.get('RightUpLeg', 'RightUpLeg'), 'Xrotation', motion_data, fi)
            knee_r = get_channel_value(joints, name_map.get('RightLeg', 'RightLeg'), 'Xrotation', motion_data, fi)
            spine = get_channel_value(joints, name_map.get('Spine', 'Spine'), 'Xrotation', motion_data, fi)
            print(f"  {label}: hip_R={hip_r:.1f}°, knee_R={knee_r:.1f}°, spine={spine:.1f}°")

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert SOMA BVH to OpenSim .mot")
    parser.add_argument("bvh_file", help="Path to SOMA BVH file")
    parser.add_argument("--output", "-o", help="Output .mot file path")
    parser.add_argument("--fps", type=float, default=None, help="Target FPS (downsample)")
    args = parser.parse_args()

    convert_bvh_to_mot(args.bvh_file, args.output, args.fps)
