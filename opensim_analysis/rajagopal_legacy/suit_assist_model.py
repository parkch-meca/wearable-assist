#!/usr/bin/env python3
"""
Wearable exosuit assistive force modeling for OpenSim Rajagopal2016.

Models SMA (Shape Memory Alloy) fabric actuators as CoordinateActuators
that apply assistive torques at target joints, reducing biological muscle demand.

Suit specification:
  - SMA fabric actuator: 200N force capacity
  - Moment arm: 10-13 cm (adjustable per joint)
  - Max torque per actuator: 20-26 Nm

Assist configurations:
  - Back only: lumbar extension assist
  - Shoulder only: shoulder flexion assist
  - Full suit: back + shoulder + elbow assist

Usage:
    python suit_assist_model.py --model /data/opensim_models/Rajagopal2016.osim \
                                --config full_suit \
                                --assist-ratio 0.3 \
                                --output /data/opensim_analysis/Rajagopal_suited.osim
"""

import argparse
import os
import opensim as osim


# ─── Suit Actuator Definitions ────────────────────────────────────────────────

SUIT_ACTUATORS = {
    # Back support — assists lumbar extension (erector spinae relief)
    'suit_lumbar_ext': {
        'coordinate': 'lumbar_extension',
        'max_force': 200.0,     # N from SMA
        'moment_arm': 0.13,     # 13 cm
        'max_torque': 26.0,     # N × m
        'direction': 1,         # positive = extension assist
        'description': 'SMA back support — erector spinae relief',
    },

    # Shoulder support — assists arm flexion (deltoid relief)
    'suit_shoulder_flex_r': {
        'coordinate': 'arm_flex_r',
        'max_force': 200.0,
        'moment_arm': 0.10,     # 10 cm
        'max_torque': 20.0,
        'direction': 1,
        'description': 'SMA right shoulder support — deltoid relief',
    },
    'suit_shoulder_flex_l': {
        'coordinate': 'arm_flex_l',
        'max_force': 200.0,
        'moment_arm': 0.10,
        'max_torque': 20.0,
        'direction': 1,
        'description': 'SMA left shoulder support — deltoid relief',
    },

    # Elbow support — assists elbow flexion (biceps relief)
    'suit_elbow_flex_r': {
        'coordinate': 'elbow_flex_r',
        'max_force': 200.0,
        'moment_arm': 0.10,
        'max_torque': 20.0,
        'direction': 1,
        'description': 'SMA right elbow support — biceps relief',
    },
    'suit_elbow_flex_l': {
        'coordinate': 'elbow_flex_l',
        'max_force': 200.0,
        'moment_arm': 0.10,
        'max_torque': 20.0,
        'direction': 1,
        'description': 'SMA left elbow support — biceps relief',
    },

    # Hip support — assists hip extension (gluteus relief during stoop)
    'suit_hip_ext_r': {
        'coordinate': 'hip_flexion_r',
        'max_force': 200.0,
        'moment_arm': 0.12,
        'max_torque': 24.0,
        'direction': -1,        # negative = extension assist (hip_flexion coord)
        'description': 'SMA right hip support — gluteus/hamstring relief',
    },
    'suit_hip_ext_l': {
        'coordinate': 'hip_flexion_l',
        'max_force': 200.0,
        'moment_arm': 0.12,
        'max_torque': 24.0,
        'direction': -1,
        'description': 'SMA left hip support — gluteus/hamstring relief',
    },
}

# Named configurations
CONFIGS = {
    'back_only': ['suit_lumbar_ext'],
    'shoulder_only': ['suit_shoulder_flex_r', 'suit_shoulder_flex_l'],
    'back_shoulder': ['suit_lumbar_ext', 'suit_shoulder_flex_r', 'suit_shoulder_flex_l'],
    'full_suit': ['suit_lumbar_ext', 'suit_shoulder_flex_r', 'suit_shoulder_flex_l',
                  'suit_elbow_flex_r', 'suit_elbow_flex_l'],
    'full_suit_hip': list(SUIT_ACTUATORS.keys()),
    'none': [],
}


def add_suit_actuators(model, config_name='full_suit', assist_ratio=0.3):
    """
    Add suit assistive actuators to an OpenSim model.

    Parameters
    ----------
    model : osim.Model
        OpenSim model to modify (in place)
    config_name : str
        One of CONFIGS keys
    assist_ratio : float
        Fraction of biological torque to assist (0.0 = no assist, 1.0 = full replacement)

    Returns
    -------
    list of str
        Names of added actuators
    """
    actuator_names = CONFIGS.get(config_name, [])
    added = []

    for act_name in actuator_names:
        spec = SUIT_ACTUATORS[act_name]

        actuator = osim.CoordinateActuator()
        actuator.setName(act_name)
        actuator.set_coordinate(spec['coordinate'])

        # Scale max torque by assist ratio
        effective_torque = spec['max_torque'] * assist_ratio
        actuator.setOptimalForce(effective_torque)
        actuator.setMinControl(-1.0)
        actuator.setMaxControl(1.0)

        model.addForce(actuator)
        added.append(act_name)

    return added


def create_suit_controls(model, mot_path, id_sto_path, config_name='full_suit',
                         assist_ratio=0.3, output_path=None):
    """
    Create a controls .sto file that specifies the suit actuator activations
    based on inverse dynamics results.

    The suit provides constant assist proportional to the biological torque demand.
    """
    if output_path is None:
        output_path = os.path.splitext(mot_path)[0] + "_suit_controls.sto"

    import numpy as np

    id_sto = osim.Storage(id_sto_path)
    n_frames = id_sto.getSize()

    actuator_names = CONFIGS.get(config_name, [])

    # Extract time
    time_arr = osim.ArrayDouble()
    id_sto.getTimeColumn(time_arr)

    with open(output_path, 'w') as f:
        f.write("suit_controls\nversion=1\n")
        f.write(f"nRows={n_frames}\nnColumns={len(actuator_names)+1}\n")
        f.write("inDegrees=no\nendheader\n")
        f.write("time\t" + "\t".join(actuator_names) + "\n")

        for i in range(n_frames):
            t = time_arr.getitem(i)
            vals = []
            for act_name in actuator_names:
                spec = SUIT_ACTUATORS[act_name]
                # Get biological torque at this joint
                moment_col = spec['coordinate'] + '_moment'
                try:
                    bio_data = osim.ArrayDouble()
                    id_sto.getDataColumn(moment_col, bio_data)
                    bio_torque = bio_data.getitem(i)
                except:
                    bio_torque = 0.0

                # Suit provides assist_ratio of the biological torque
                suit_activation = np.clip(
                    -bio_torque * assist_ratio / spec['max_torque'],
                    -1.0, 1.0
                )
                vals.append(f"{suit_activation:.6f}")

            f.write(f"{t:.6f}\t" + "\t".join(vals) + "\n")

    return output_path


def create_suited_model(model_path, config_name='full_suit', assist_ratio=0.3,
                        output_path=None):
    """
    Create a new .osim model file with suit actuators added.
    """
    if output_path is None:
        base = os.path.splitext(model_path)[0]
        output_path = f"{base}_{config_name}_ar{int(assist_ratio*100)}.osim"

    model = osim.Model(model_path)
    added = add_suit_actuators(model, config_name, assist_ratio)
    model.initSystem()

    model.printToXML(output_path)
    print(f"Suited model saved: {output_path}")
    print(f"  Config: {config_name}, Assist ratio: {assist_ratio:.0%}")
    print(f"  Added actuators: {added}")
    print(f"  Total forces: {model.getForceSet().getSize()}")

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add suit actuators to OpenSim model")
    parser.add_argument("--model", default="/data/opensim_models/Rajagopal2016.osim")
    parser.add_argument("--config", default="full_suit", choices=list(CONFIGS.keys()))
    parser.add_argument("--assist-ratio", type=float, default=0.3)
    parser.add_argument("--output", "-o", default=None)
    args = parser.parse_args()

    create_suited_model(args.model, args.config, args.assist_ratio, args.output)
