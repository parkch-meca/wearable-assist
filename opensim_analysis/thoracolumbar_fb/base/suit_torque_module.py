"""
Suit Torque Module — SMA suit force-to-torque conversion with unit safety.

Background:
    Phase 2.C.4 v1-v3 had 200 N·m direct application bug (8.33× over actual
    SMA suit spec of 24 N·m). This module structurally prevents recurrence
    through type-enforced SuitConfig dataclass with assertions.

Sources (verified):
    - Phase 1a (verified): SUIT_FORCE_N (200 N) × MOMENT_ARM (0.12 m) = 24 N·m
    - CHEOL HOON SMA suit spec: 200 N contraction force, ~10-13 cm moment arm
    - Architecture §4 (integrated_system_architecture.md)
"""
from dataclasses import dataclass

try:
    import opensim as osim
    _OPENSIM_AVAILABLE = True
except ImportError:
    _OPENSIM_AVAILABLE = False

# Phase 1a verified constants
PHASE1A_FORCE_N = 200.0     # SMA suit max contraction force (N)
PHASE1A_MOMENT_ARM = 0.12   # Standard moment arm (m, 12 cm)
PHASE1A_TORQUE_NM = 24.0    # = 200 × 0.12, verified L20 condition

# SMA suit physical limits (assertion bounds)
SMA_FORCE_MAX_N = 250.0     # SMA max contraction force
SMA_MOMENT_ARM_MIN = 0.05   # Minimum moment arm (m, 5 cm)
SMA_MOMENT_ARM_MAX = 0.20   # Maximum moment arm (m, 20 cm)


@dataclass
class SuitConfig:
    """SMA suit configuration with unit-safe torque calculation.

    Parameters
    ----------
    name : str
        Condition name (e.g., 'B_suit200', 'L20')
    force_N : float
        Contraction force in Newtons (0-250 N range for SMA suit)
    moment_arm_m : float
        Moment arm in meters (0.05-0.20 m range, default 0.12 m)

    Properties
    ----------
    torque_Nm : float
        Computed torque = force_N × moment_arm_m

    Examples
    --------
    >>> sma_l20 = SuitConfig('L20', force_N=200, moment_arm_m=0.12)
    >>> sma_l20.torque_Nm
    24.0

    >>> # Bug prevention: this raises AssertionError (out of range)
    >>> SuitConfig('bad', force_N=1666.67)  # User mistakenly entered torque
    AssertionError: force_N 1666.67 out of SMA range (0-250 N)
    """
    name: str
    force_N: float
    moment_arm_m: float = PHASE1A_MOMENT_ARM

    @property
    def torque_Nm(self) -> float:
        return self.force_N * self.moment_arm_m

    def __post_init__(self):
        # Force range check (SMA suit max 250 N)
        assert 0 <= self.force_N <= SMA_FORCE_MAX_N, (
            f"force_N {self.force_N} out of SMA range (0-{SMA_FORCE_MAX_N} N). "
            f"Did you mean torque (N·m)? Use force in N. "
            f"For 24 N·m at 0.12 m arm, use force_N=200."
        )

        # Moment arm range check
        assert SMA_MOMENT_ARM_MIN <= self.moment_arm_m <= SMA_MOMENT_ARM_MAX, (
            f"moment_arm_m {self.moment_arm_m} out of range "
            f"({SMA_MOMENT_ARM_MIN}-{SMA_MOMENT_ARM_MAX} m)"
        )


def make_suit_sweep(
    force_levels_N: list = None,
    moment_arm_m: float = PHASE1A_MOMENT_ARM,
) -> list:
    """Generate suit sweep conditions from force levels.

    Standard 5-level sweep [0, 50, 100, 150, 200] N → [0, 6, 12, 18, 24] N·m.

    Parameters
    ----------
    force_levels_N : list of float, optional
        Force levels in Newtons. Default: [0, 50, 100, 150, 200].
    moment_arm_m : float, optional
        Moment arm in meters. Default: 0.12 m (PHASE1A_MOMENT_ARM).

    Returns
    -------
    list of SuitConfig
        One SuitConfig per force level, name = 'B_suit{force}'.
    """
    if force_levels_N is None:
        force_levels_N = [0, 50, 100, 150, 200]
    return [
        SuitConfig(
            name=f'B_suit{int(f)}',
            force_N=float(f),
            moment_arm_m=moment_arm_m,
        )
        for f in force_levels_N
    ]


def create_suit_actuators(
    config: SuitConfig,
    coords: list = None,
    n_segments: int = 5,
) -> list:
    """Create CoordinateActuator list with torque distributed across lumbar segments.

    Each segment receives total_torque / n_segments.

    Parameters
    ----------
    config : SuitConfig
        Suit configuration (unit-safe, validated at construction).
    coords : list of str, optional
        Lumbar coordinate names. Default: L5_S1 through L1_L2 (5 FE DOFs).
    n_segments : int, optional
        Number of lumbar segments. Default: 5.

    Returns
    -------
    list of opensim.CoordinateActuator
        One actuator per coordinate; optimal force = torque_Nm / n_segments.

    Raises
    ------
    ImportError
        If opensim is not available in the current environment.
    AssertionError
        If len(coords) != n_segments.
    """
    if not _OPENSIM_AVAILABLE:
        raise ImportError(
            "opensim package not available. "
            "Activate environment: /home/sysop/miniconda3/envs/opensim/bin/python"
        )

    if coords is None:
        coords = ['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L2_L3_FE', 'L1_L2_FE']

    assert len(coords) == n_segments, (
        f"coords count {len(coords)} != n_segments {n_segments}"
    )

    torque_per_segment = config.torque_Nm / n_segments
    actuators = []
    for coord in coords:
        ca = osim.CoordinateActuator(coord)
        ca.setName(f'suit_{coord}_{config.name}')
        ca.setOptimalForce(torque_per_segment)
        ca.setMinControl(-1.0)
        ca.setMaxControl(1.0)
        actuators.append(ca)
    return actuators


def verify_phase1a_consistency() -> bool:
    """Verify Phase 1a L20 condition (24 N·m) reproducible.

    Returns
    -------
    bool
        True if SuitConfig('L20', 200, 0.12).torque_Nm == 24.0.
    """
    l20 = SuitConfig('L20', force_N=PHASE1A_FORCE_N, moment_arm_m=PHASE1A_MOMENT_ARM)
    return abs(l20.torque_Nm - PHASE1A_TORQUE_NM) < 1e-9
