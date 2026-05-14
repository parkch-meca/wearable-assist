"""
base/ — Common infrastructure for all Moco tasks.

Week 1-2 모듈 (Step 2 통합 시스템):
    model_setup.py      — ModelProcessor (Dembia 2020 + Hicks 2015 표준)
    suit_torque_module  — SuitConfig 단위 분리 (Week 1.2 예정)
    moco_track_setup    — MocoTrack 공통 설정 (Week 1.3 예정)
    contact_model       — SmoothSphereHalfSpaceForce (Week 1.4 예정)
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

__all__ = [
    # 핵심 함수
    'build_model_processor',
    'get_default_model_path',
    'get_task_residuals',
    'validate_residuals',
    'test_phase1a_compatibility',
    'run_verification',
    # 상수
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
]
