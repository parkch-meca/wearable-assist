"""
base/ — Common infrastructure for all Moco tasks.

Week 1-2 modules (Step 2 integrated system):
    model_setup.py      — ModelProcessor (Dembia 2020 + Hicks 2015 standard)
    suit_torque_module  — SuitConfig unit safety (Week 1.2)
    moco_track_setup    — MocoTrack common setup (Week 1.3 planned)
    contact_model       — SmoothSphereHalfSpaceForce (Week 1.4 planned)
"""

from .model_setup import (
    build_model_processor,
    get_default_model_path,
    get_task_residuals,
    validate_residuals,
    test_phase1a_compatibility,
    run_verification,
    DEFAULT_RESIDUALS_ROT_STOOP,
    DEFAULT_RESIDUALS_TRANS_STOOP,
    DEFAULT_RESIDUALS_ROT_BOX,
    DEFAULT_RESIDUALS_TRANS_BOX,
    DEFAULT_RESIDUALS_ROT_WALK,
    DEFAULT_RESIDUALS_TRANS_WALK,
    DEFAULT_RESERVES_SCALE,
    HICKS_TRANS_THRESHOLD_N,
    HICKS_ROT_THRESHOLD_NM,
    SUPPORTED_TASKS,
)

from .suit_torque_module import (
    SuitConfig,
    make_suit_sweep,
    create_suit_actuators,
    verify_phase1a_consistency,
    PHASE1A_FORCE_N,
    PHASE1A_MOMENT_ARM,
    PHASE1A_TORQUE_NM,
)

__all__ = [
    # model_setup
    'build_model_processor',
    'get_default_model_path',
    'get_task_residuals',
    'validate_residuals',
    'test_phase1a_compatibility',
    'run_verification',
    'DEFAULT_RESIDUALS_ROT_STOOP',
    'DEFAULT_RESIDUALS_TRANS_STOOP',
    'DEFAULT_RESIDUALS_ROT_BOX',
    'DEFAULT_RESIDUALS_TRANS_BOX',
    'DEFAULT_RESIDUALS_ROT_WALK',
    'DEFAULT_RESIDUALS_TRANS_WALK',
    'DEFAULT_RESERVES_SCALE',
    'HICKS_TRANS_THRESHOLD_N',
    'HICKS_ROT_THRESHOLD_NM',
    'SUPPORTED_TASKS',
    # suit_torque_module
    'SuitConfig',
    'make_suit_sweep',
    'create_suit_actuators',
    'verify_phase1a_consistency',
    'PHASE1A_FORCE_N',
    'PHASE1A_MOMENT_ARM',
    'PHASE1A_TORQUE_NM',
]
