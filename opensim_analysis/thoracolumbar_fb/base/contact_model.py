"""
Contact Model Module — foot-ground contact + hand external force.

Sources (verified):
    - Falisse et al. 2019 (J R Soc Interface, ~250 citations):
        SmoothSphereHalfSpaceForce + Hunt-Crossley for predictive walking
    - OpenSim 2D_gait.osim (official example):
        Heel sphere radius 0.035 m, ball 0.015 m, stiffness 1e6 N/m^2
    - John 2022 (MocoTrack with contact)
    - Architecture §2.1 (integrated_system_architecture.md)

Background:
    Box motion v3-v11 used ExternalLoads STO with stoop GRF, leading to
    motion-GRF dynamics mismatch (pelvis_ty residual 3,570 N spike at t=4.0 s).
    Contact model resolves this structurally: GRF auto-computed from
    foot-ground sphere contact, no external STO needed for box/squat/walk.

    Phase 1a stoop path (ExternalLoads STO) is preserved; this module is
    an optional add-on for box/squat tasks and does NOT conflict with stoop.

Usage:
    from base.contact_model import add_foot_contact_model, add_hand_external_force
    model = osim.Model(model_path)
    model = add_foot_contact_model(model)   # 4 spheres, auto GRF
    model = add_hand_external_force(model, 'hand_r')
    model.finalizeConnections()
"""
from __future__ import annotations

import os
import textwrap

import opensim as osim

# ---------------------------------------------------------------------------
# Falisse 2019 + OpenSim 2D_gait verified parameters
# ---------------------------------------------------------------------------

CONTACT_SPHERES: dict = {
    'heel_r': {
        'radius': 0.035,
        'location': (0.0, -0.04, 0.0),
        'parent_body': 'calcn_r',
    },
    'ball_r': {
        'radius': 0.015,
        'location': (0.18, -0.04, 0.0),
        'parent_body': 'calcn_r',
    },
    'heel_l': {
        'radius': 0.035,
        'location': (0.0, -0.04, 0.0),
        'parent_body': 'calcn_l',
    },
    'ball_l': {
        'radius': 0.015,
        'location': (0.18, -0.04, 0.0),
        'parent_body': 'calcn_l',
    },
}

CONTACT_PARAMS: dict = {
    'stiffness': 1e6,            # N/m^2  (Hunt-Crossley, Falisse 2019 Table 1)
    'dissipation': 2.0,          # s/m    (Hunt-Crossley, Falisse 2019 Table 1)
    'static_friction': 0.8,      # dimensionless
    'dynamic_friction': 0.8,     # dimensionless
    'viscous_friction': 0.5,     # dimensionless
    'transition_velocity': 0.2,  # m/s
    'smoothing': 300,            # smoothing constant (Falisse 2019 Eq. 6)
}

# Ground plane: y+ up, half-space occupies y < 0
# Rotation of 90 deg about -z axis brings the half-space normal to +y
GROUND_HALFSPACE_ORIENTATION: tuple = (0.0, 0.0, -1.5707963)  # rad


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def add_foot_contact_model(
    model: osim.Model,
    spheres: dict | None = None,
    params: dict | None = None,
    ground_plane_height: float = 0.0,
) -> osim.Model:
    """
    Add 4 foot contact spheres + SmoothSphereHalfSpaceForce pairs.

    Resolves motion-GRF mismatch: GRF is auto-computed by contact physics,
    no external STO file required for box/squat tasks.

    Parameters
    ----------
    model : osim.Model
        Input OpenSim model (typically _no_coupler variant for box tasks).
    spheres : dict, optional
        Contact sphere configuration dict. Keys: sphere name.
        Each value must contain 'radius', 'location' (3-tuple), 'parent_body'.
        Defaults to Falisse 2019 + 2D_gait verified CONTACT_SPHERES.
    params : dict, optional
        Hunt-Crossley parameters. Defaults to Falisse 2019 CONTACT_PARAMS.
    ground_plane_height : float
        Y coordinate of ground plane (default 0.0).

    Returns
    -------
    osim.Model
        Modified model with contact geometry and force objects added.
        Call model.finalizeConnections() after all modifications.

    Notes
    -----
    Sphere layout (Falisse 2019, OpenSim 2D_gait.osim):
        heel_r/l : radius 35 mm, attached at calcn origin (posterior)
        ball_r/l : radius 15 mm, attached 18 cm anterior on calcn (metatarsal)

    Phase 1a stoop compatibility:
        This function adds components but does NOT replace ExternalLoads STO.
        For stoop tasks, do not call this function (stoop uses GRF STO).
        For box/squat tasks, call this function and omit ExternalLoads.
    """
    if spheres is None:
        spheres = CONTACT_SPHERES
    if params is None:
        params = CONTACT_PARAMS

    # ------------------------------------------------------------------ #
    # 1. Ground contact half-space (single, shared by all spheres)
    # ------------------------------------------------------------------ #
    ground = model.getGround()

    ground_half = osim.ContactHalfSpace()
    ground_half.setName('ground_contact')
    ground_half.setBody(ground)
    ground_half.setLocation(osim.Vec3(0.0, ground_plane_height, 0.0))
    ground_half.setOrientation(osim.Vec3(*GROUND_HALFSPACE_ORIENTATION))
    model.addContactGeometry(ground_half)

    # ------------------------------------------------------------------ #
    # 2. Foot contact spheres + SmoothSphereHalfSpaceForce pairs
    # ------------------------------------------------------------------ #
    for sphere_name, cfg in spheres.items():
        parent_body = model.getBodySet().get(cfg['parent_body'])

        # Contact sphere geometry
        sphere = osim.ContactSphere()
        sphere.setName(f'{sphere_name}_sphere')
        sphere.setBody(parent_body)
        sphere.setLocation(osim.Vec3(*cfg['location']))
        sphere.setRadius(cfg['radius'])
        model.addContactGeometry(sphere)

        # SmoothSphereHalfSpaceForce (Hunt-Crossley model)
        contact_force = osim.SmoothSphereHalfSpaceForce()
        contact_force.setName(f'{sphere_name}_contact_force')
        contact_force.connectSocket_sphere(sphere)
        contact_force.connectSocket_half_space(ground_half)
        contact_force.set_stiffness(params['stiffness'])
        contact_force.set_dissipation(params['dissipation'])
        contact_force.set_static_friction(params['static_friction'])
        contact_force.set_dynamic_friction(params['dynamic_friction'])
        contact_force.set_viscous_friction(params['viscous_friction'])
        contact_force.set_transition_velocity(params['transition_velocity'])
        contact_force.set_constant_contact_force(1e-5)
        contact_force.set_hertz_smoothing(params['smoothing'])
        contact_force.set_hunt_crossley_smoothing(params['smoothing'])
        model.addForce(contact_force)

    return model


def add_hand_external_force(
    model: osim.Model,
    body_name: str = 'hand_r',
    force_xml_path: str | None = None,
    force_identifier: str | None = None,
    point_identifier: str | None = None,
) -> osim.Model:
    """
    Hand external force setup for box/tool interactions.

    For box lifting, the recommended path is ModOpAddExternalLoads in the
    ModelProcessor pipeline rather than directly adding an OpenSim Force
    component, because ExternalLoads handles time-varying data from an STO.

    Recommended usage (box lifting):
        mp = osim.ModelProcessor(model_path)
        mp.append(osim.ModOpAddExternalLoads(box_loads_xml_path))
    See setup_box_lifting_contact() and add_hand_external_force_xml() for
    the complete integration example including XML and STO generation.

    Parameters
    ----------
    model : osim.Model
    body_name : str
        Body to apply force to ('hand_r' or 'hand_l').
    force_xml_path : str, optional
        Path to ExternalLoads XML. Binding done at ModelProcessor stage.
    force_identifier : str, optional
        Column identifier in force STO file.
    point_identifier : str, optional
        Point column identifier in force STO file.

    Returns
    -------
    osim.Model
        Model returned unchanged (data binding is done via ModelProcessor).
    """
    # NOTE: ExternalLoads for box weight on hand is handled via
    # ModOpAddExternalLoads(box_loads_xml) in the ModelProcessor pipeline.
    # Direct Force addition here is not required for the standard box-lifting
    # workflow. This function exists as a documented integration point.
    _ = (body_name, force_xml_path, force_identifier, point_identifier)
    return model


# ---------------------------------------------------------------------------
# Hand ExternalForce XML + STO generators (Week 2 — actual implementation)
# ---------------------------------------------------------------------------

def add_hand_external_force_xml(
    output_xml_path: str,
    hand_force_data_sto: str,
    body_r: str = 'hand_r',
    body_l: str = 'hand_l',
) -> str:
    """
    Generate ExternalLoads XML for bilateral hand box forces.

    Produces an OpenSim ExternalLoads XML file with two ExternalForce
    components: one for each hand.  The forces are expressed in the ground
    frame, applied to the specified hand bodies, and sourced from columns in
    the supplied STO file.

    Column naming convention in the STO file (as generated by
    generate_box_force_sto):
        hand_r_force_vx / vy / vz  — right-hand force vector (ground frame)
        hand_r_point_px / py / pz  — right-hand application point (ground)
        hand_l_force_vx / vy / vz  — left-hand force vector
        hand_l_point_px / py / pz  — left-hand application point

    Parameters
    ----------
    output_xml_path : str
        Absolute path where the XML file will be saved.
    hand_force_data_sto : str
        Absolute path to the STO file containing time-varying force columns
        (as generated by generate_box_force_sto).
    body_r : str
        OpenSim body name for the right hand (default: 'hand_r').
    body_l : str
        OpenSim body name for the left hand (default: 'hand_l').

    Returns
    -------
    str
        Absolute path to the generated XML file (same as output_xml_path).

    Raises
    ------
    FileNotFoundError
        If hand_force_data_sto does not exist.
    ValueError
        If output_xml_path does not end with '.xml'.

    Notes
    -----
    The generated XML is compatible with OpenSim 4.x ExternalLoads format.
    Apply to a ModelProcessor via:
        mp.append(osim.ModOpAddExternalLoads(output_xml_path))
    """
    if not output_xml_path.endswith('.xml'):
        raise ValueError(
            f"output_xml_path must end with '.xml', got: {output_xml_path}"
        )
    if not os.path.isfile(hand_force_data_sto):
        raise FileNotFoundError(
            f"hand_force_data_sto not found: {hand_force_data_sto}"
        )

    sto_basename = os.path.basename(hand_force_data_sto)

    xml_content = textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8" ?>
        <!-- Hand ExternalLoads XML generated by base/contact_model.py -->
        <!-- apply_to: {body_r}, {body_l}  |  data_file: {sto_basename} -->
        <OpenSimDocument Version="40000">
          <ExternalLoads name="hand_external_loads">
            <objects>
              <ExternalForce name="hand_r_box_force">
                <isDisabled>false</isDisabled>
                <applied_to_body>{body_r}</applied_to_body>
                <force_expressed_in_body>ground</force_expressed_in_body>
                <point_expressed_in_body>ground</point_expressed_in_body>
                <force_identifier>hand_r_force_v</force_identifier>
                <point_identifier>hand_r_point_p</point_identifier>
              </ExternalForce>
              <ExternalForce name="hand_l_box_force">
                <isDisabled>false</isDisabled>
                <applied_to_body>{body_l}</applied_to_body>
                <force_expressed_in_body>ground</force_expressed_in_body>
                <point_expressed_in_body>ground</point_expressed_in_body>
                <force_identifier>hand_l_force_v</force_identifier>
                <point_identifier>hand_l_point_p</point_identifier>
              </ExternalForce>
            </objects>
            <datafile>{hand_force_data_sto}</datafile>
          </ExternalLoads>
        </OpenSimDocument>
    """)

    os.makedirs(os.path.dirname(os.path.abspath(output_xml_path)), exist_ok=True)
    with open(output_xml_path, 'w', encoding='utf-8') as fh:
        fh.write(xml_content)

    return output_xml_path


def generate_box_force_sto(
    output_sto_path: str,
    motion_file: str,
    box_mass_kg: float = 20.0,
    grasp_start_time: float = 2.0,
    grip_point_ground: tuple = (0.40, 0.75, 0.0),
) -> str:
    """
    Generate time-varying bilateral hand force STO for box lifting.

    Force profile (ground frame, applied to each hand):
        t < grasp_start_time  : 0 N  (approach phase)
        t >= grasp_start_time : box_mass_kg * 9.81 / 2 N  (lifting phase)

    The force is directed upward (+y in ground frame) on each hand.
    Application point is fixed at grip_point_ground (box side handles).

    Column layout in output STO:
        time
        hand_r_force_vx, hand_r_force_vy, hand_r_force_vz
        hand_r_point_px, hand_r_point_py, hand_r_point_pz
        hand_l_force_vx, hand_l_force_vy, hand_l_force_vz
        hand_l_point_px, hand_l_point_py, hand_l_point_pz

    Parameters
    ----------
    output_sto_path : str
        Absolute path for the output STO file.
    motion_file : str
        Reference motion .mot file. Time range is read from this file.
    box_mass_kg : float
        Box total mass in kg (default: 20 kg, CHEOL HOON spec).
    grasp_start_time : float
        Time (s) at which hand forces become active (default: 2.0 s).
    grip_point_ground : tuple
        (x, y, z) application point in ground frame metres (default: box
        at x=0.40, y=0.75 m above ground, z=0.0).

    Returns
    -------
    str
        Absolute path to the generated STO file.

    Raises
    ------
    FileNotFoundError
        If motion_file does not exist.

    Notes
    -----
    Force magnitude = box_mass_kg * 9.81 / 2 per hand (bilateral split).
    Gravity convention: forces resist gravity, so vy = +98.1 N (upward).
    For box_mass_kg=20: force per hand = 98.1 N upward.
    """
    if not os.path.isfile(motion_file):
        raise FileNotFoundError(f"motion_file not found: {motion_file}")

    # Read time range from motion file header
    t_min, t_max = _read_motion_time_range(motion_file)

    # Generate 100 Hz time vector spanning the full motion
    import numpy as np
    dt = 0.01
    times = np.arange(t_min, t_max + dt * 0.5, dt)

    force_per_hand = box_mass_kg * 9.81 / 2.0   # 98.1 N for 20 kg
    gx, gy, gz = grip_point_ground

    lines = []
    # STO header
    lines.append(f'box_hand_forces')
    lines.append(f'version=1')
    lines.append(f'nRows={len(times)}')
    lines.append(f'nColumns=13')
    lines.append(f'inDegrees=no')
    lines.append(f'# Generated by base/contact_model.generate_box_force_sto')
    lines.append(f'# box_mass_kg={box_mass_kg}, grasp_start_time={grasp_start_time}')
    lines.append(f'# force_per_hand={force_per_hand:.2f} N (upward, ground frame)')
    lines.append('endheader')
    col_header = (
        'time\t'
        'hand_r_force_vx\thand_r_force_vy\thand_r_force_vz\t'
        'hand_r_point_px\thand_r_point_py\thand_r_point_pz\t'
        'hand_l_force_vx\thand_l_force_vy\thand_l_force_vz\t'
        'hand_l_point_px\thand_l_point_py\thand_l_point_pz'
    )
    lines.append(col_header)

    for t in times:
        f = force_per_hand if t >= grasp_start_time else 0.0
        row = (
            f'{t:.4f}\t'
            # hand_r force (upward)
            f'0.0\t{f:.4f}\t0.0\t'
            # hand_r point
            f'{gx:.4f}\t{gy:.4f}\t{-0.13:.4f}\t'
            # hand_l force (upward, symmetric)
            f'0.0\t{f:.4f}\t0.0\t'
            # hand_l point (opposite z-side of box)
            f'{gx:.4f}\t{gy:.4f}\t{0.13:.4f}'
        )
        lines.append(row)

    os.makedirs(os.path.dirname(os.path.abspath(output_sto_path)), exist_ok=True)
    with open(output_sto_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')

    return output_sto_path


def _read_motion_time_range(motion_file: str) -> tuple:
    """
    Read first and last time value from a .mot or .sto file.

    Returns (t_min, t_max) as floats.
    Falls back to (0.0, 5.0) if parsing fails.
    """
    try:
        t_vals = []
        in_data = False
        with open(motion_file, 'r') as fh:
            for line in fh:
                line = line.strip()
                if line.lower() == 'endheader':
                    in_data = True
                    continue
                if not in_data:
                    continue
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if parts:
                    try:
                        t_vals.append(float(parts[0]))
                    except ValueError:
                        pass  # header column label line
        if len(t_vals) >= 2:
            return float(min(t_vals)), float(max(t_vals))
    except Exception:
        pass
    return 0.0, 5.0


def setup_box_lifting_contact(
    model: osim.Model,
    box_mass_kg: float = 20.0,
    grip_points_r: tuple = (0.0, 0.0, 0.0),
    grip_points_l: tuple = (0.0, 0.0, 0.0),
) -> dict:
    """
    Box lifting scenario: foot contact + hand ExternalForce integration.

    Adds foot contact spheres to the model and computes hand force magnitudes
    for 20 kg box (both hands, gravity = 9.81 m/s^2).

    Parameters
    ----------
    model : osim.Model
        Input model for box lifting task.
    box_mass_kg : float
        Box total mass (default 20 kg, CHEOL HOON spec).
    grip_points_r : tuple
        Grip point on hand_r body frame (x, y, z) in metres.
    grip_points_l : tuple
        Grip point on hand_l body frame (x, y, z) in metres.

    Returns
    -------
    dict with keys:
        'model'              : osim.Model — foot contact added
        'box_force_N_per_hand': float    — 98.1 N for 20 kg box
        'grip_points_r'      : tuple     — as supplied
        'grip_points_l'      : tuple     — as supplied
        'hand_force_setup'   : dict      — per-hand force vectors (body frame)
    """
    model = add_foot_contact_model(model)

    gravity_N_per_hand: float = box_mass_kg * 9.81 / 2.0  # 98.1 N for 20 kg

    return {
        'model': model,
        'box_force_N_per_hand': gravity_N_per_hand,
        'grip_points_r': grip_points_r,
        'grip_points_l': grip_points_l,
        'hand_force_setup': {
            'hand_r': {
                'body': 'hand_r',
                'force_N': (0.0, -gravity_N_per_hand, 0.0),   # downward in body frame
            },
            'hand_l': {
                'body': 'hand_l',
                'force_N': (0.0, -gravity_N_per_hand, 0.0),
            },
        },
    }


# ---------------------------------------------------------------------------
# Inspection helpers
# ---------------------------------------------------------------------------

def count_contact_geometry(model: osim.Model) -> dict:
    """
    Count ContactSphere and ContactHalfSpace objects in model.

    Returns
    -------
    dict with keys 'spheres' (int) and 'halfspaces' (int).
    """
    n_sphere = 0
    n_halfspace = 0
    cg_set = model.getContactGeometrySet()
    for i in range(cg_set.getSize()):
        cg = cg_set.get(i)
        cls = cg.getConcreteClassName()
        if cls == 'ContactSphere':
            n_sphere += 1
        elif cls == 'ContactHalfSpace':
            n_halfspace += 1
    return {'spheres': n_sphere, 'halfspaces': n_halfspace}


def count_contact_forces(model: osim.Model) -> int:
    """
    Count SmoothSphereHalfSpaceForce objects in the model ForceSet.

    Returns
    -------
    int : number of SmoothSphereHalfSpaceForce components.
    """
    count = 0
    fs = model.getForceSet()
    for i in range(fs.getSize()):
        f = fs.get(i)
        if 'SmoothSphereHalfSpaceForce' in f.getConcreteClassName():
            count += 1
    return count


def verify_falisse2019_compatibility(model: osim.Model) -> bool:
    """
    Verify contact model matches Falisse 2019 expected configuration.

    Expected: 4 contact spheres, >= 1 half-space, 4 contact force components.

    Returns
    -------
    bool : True if all criteria satisfied.
    """
    geom = count_contact_geometry(model)
    forces = count_contact_forces(model)
    return (
        geom['spheres'] == 4
        and geom['halfspaces'] >= 1
        and forces == 4
    )
