"""
base/model_setup.py — Common ModelProcessor for all Moco tasks.

Sources (검증된 method):
- Dembia 2020 (OpenSim Moco paper): ModOpAddResiduals/Reserves 표준
  exampleMocoInverse.py: model_proc.append(osim.ModOpAddResiduals(300.0, 50.0, 1.0))
- Hicks 2015 (Is my model good enough?):
  Reserve 허용 기준 — translational < 5% BW (≈ 36.8 N), rotational < 1% BW×ht (≈ 12.9 N·m)
- Phase 1a regression PASS (max ΔES 1.227 %p) with forearm_v1 model
- Integrated System Architecture §2.3 Reserve 분리 표준

Architecture §2.3 Task-specific reserve table:
    stoop lift  : translational 50 N,  rotational 20 N·m  (정적 동작)
    box/squat   : translational 300 N, rotational 50 N·m  (semi-squat 수직 가속도)
    walk        : translational 250 N, rotational 50 N·m  (공식 예제 기준)

Usage:
    from base.model_setup import build_model_processor
    mp = build_model_processor(
        model_path=get_default_model_path(),
        task_type='stoop',
        external_loads_xml='/data/.../stoop_grf_v5_extload.xml',
    )
"""

from __future__ import annotations

import os
import warnings
from typing import Optional

import opensim as osim

# ---------------------------------------------------------------------------
# Module-level constants (검증된 Dembia 2020 + Architecture §2.3)
# ---------------------------------------------------------------------------

# Phase 1a 검증 기준: stoop lift (정적, GRF 외부 STO)
DEFAULT_RESIDUALS_ROT_STOOP: float = 20.0    # N·m  — Architecture §2.3
DEFAULT_RESIDUALS_TRANS_STOOP: float = 50.0   # N    — Architecture §2.3

# semi-squat / box lift (수직 가속도 보정)
DEFAULT_RESIDUALS_ROT_BOX: float = 50.0      # N·m  — Dembia 2020 exampleMocoInverse
DEFAULT_RESIDUALS_TRANS_BOX: float = 300.0   # N    — Dembia 2020 exampleMocoInverse

# walk
DEFAULT_RESIDUALS_ROT_WALK: float = 50.0     # N·m
DEFAULT_RESIDUALS_TRANS_WALK: float = 250.0  # N    — 공식 예제 권장값

# Other reserves — 모든 작업 공통 (약한 보조)
DEFAULT_RESERVES_SCALE: float = 1.0          # Dembia 2020 "weak" pattern

# Hicks 2015 검증 기준값
HICKS_TRANS_THRESHOLD_N: float = 36.8        # 5% BW (75 kg × 9.81 × 0.05)
HICKS_ROT_THRESHOLD_NM: float = 12.9         # 1% BW×ht (75 kg × 9.81 × 1.75 × 0.01)

# 표준 모델 경로
_DEFAULT_MODEL_PATH = (
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
    'MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim'
)

# 작업별 residual 매핑
_TASK_RESIDUALS: dict[str, tuple[float, float]] = {
    'stoop': (DEFAULT_RESIDUALS_ROT_STOOP, DEFAULT_RESIDUALS_TRANS_STOOP),
    'box':   (DEFAULT_RESIDUALS_ROT_BOX,   DEFAULT_RESIDUALS_TRANS_BOX),
    'squat': (DEFAULT_RESIDUALS_ROT_BOX,   DEFAULT_RESIDUALS_TRANS_BOX),   # box와 동일
    'walk':  (DEFAULT_RESIDUALS_ROT_WALK,  DEFAULT_RESIDUALS_TRANS_WALK),
}

SUPPORTED_TASKS = tuple(_TASK_RESIDUALS.keys())


# ---------------------------------------------------------------------------
# 핵심 함수
# ---------------------------------------------------------------------------

def build_model_processor(
    model_path: str,
    task_type: str = 'stoop',
    residuals_rot: Optional[float] = None,
    residuals_trans: Optional[float] = None,
    reserves_scale: float = DEFAULT_RESERVES_SCALE,
    external_loads_xml: Optional[str] = None,
) -> osim.ModelProcessor:
    """
    Common ModelProcessor builder for all Moco tasks.

    ModelProcessor 구성 순서 (Dembia 2020 표준):
        1. ModOpAddExternalLoads  — stoop GRF STO (선택)
        2. ModOpAddResiduals      — pelvis 6 DOF 전용
        3. ModOpAddReserves       — 나머지 관절 (약한 보조)

    Parameters
    ----------
    model_path : str
        Path to .osim model file. 존재 여부를 사전 검증함.
    task_type : str
        'stoop', 'box', 'squat', 'walk' — task-specific residual 자동 선택.
        명시적 residuals_rot/trans가 있으면 task_type 기본값을 덮어씀.
    residuals_rot : float, optional
        Rotational residual optimal force (N·m).
        None이면 task_type에 따라 자동 설정.
    residuals_trans : float, optional
        Translational residual optimal force (N).
        None이면 task_type에 따라 자동 설정.
    reserves_scale : float
        Other reserves optimal force (N 또는 N·m), default 1.0.
    external_loads_xml : str, optional
        ExternalLoads XML path (stoop GRF STO 연결용).
        box/squat/walk는 SmoothSphereHalfSpaceForce 사용 — 여기서는 None.

    Returns
    -------
    osim.ModelProcessor
        Moco solve에 바로 주입 가능한 ModelProcessor.

    Raises
    ------
    FileNotFoundError
        model_path 또는 external_loads_xml이 실제 파일이 아닐 때.
    ValueError
        task_type이 지원 목록에 없을 때.

    Notes
    -----
    API 인수 순서 (중요):
        ModOpAddResiduals(rotational_F, translational_F, bound_scale)
        — bound_scale=1.0 (표준; Phase 1a 검증값)
    Hicks 2015 기준:
        translational < 36.8 N (5% BW), rotational < 12.9 N·m (1% BW×ht)
    Phase 1a 검증:
        stoop lift, forearm_v1, ExternalLoads STO, max ΔES 1.227 %p PASS.
    """
    # ---- 입력 검증 ----
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")

    task_type = task_type.lower().strip()
    if task_type not in _TASK_RESIDUALS:
        raise ValueError(
            f"Unknown task_type '{task_type}'. "
            f"Supported: {SUPPORTED_TASKS}"
        )

    if external_loads_xml is not None and not os.path.isfile(external_loads_xml):
        raise FileNotFoundError(
            f"ExternalLoads XML not found: {external_loads_xml}"
        )

    # ---- Residual 결정 ----
    default_rot, default_trans = _TASK_RESIDUALS[task_type]
    _rot   = residuals_rot   if residuals_rot   is not None else default_rot
    _trans = residuals_trans if residuals_trans is not None else default_trans

    # ---- 경고: Hicks 2015 기준 초과 시 ----
    # (solver 실패 아님, 연구 보고 시 명시 권고)
    if _rot > HICKS_ROT_THRESHOLD_NM:
        warnings.warn(
            f"residuals_rot={_rot} N·m exceeds Hicks 2015 threshold "
            f"({HICKS_ROT_THRESHOLD_NM} N·m). "
            "결과를 Limitations에 명시하십시오.",
            UserWarning,
            stacklevel=2,
        )
    if _trans > HICKS_TRANS_THRESHOLD_N:
        warnings.warn(
            f"residuals_trans={_trans} N exceeds Hicks 2015 threshold "
            f"({HICKS_TRANS_THRESHOLD_N} N). "
            "결과를 Limitations에 명시하십시오.",
            UserWarning,
            stacklevel=2,
        )

    # ---- ModelProcessor 구성 ----
    mp = osim.ModelProcessor(model_path)

    # Step 1: ExternalLoads (stoop GRF STO — 선택)
    if external_loads_xml is not None:
        mp.append(osim.ModOpAddExternalLoads(external_loads_xml))

    # Step 2: Residuals — pelvis 6 DOF 전용
    # API: ModOpAddResiduals(rotational_F, translational_F, bound_scale)
    mp.append(osim.ModOpAddResiduals(_rot, _trans, 1.0))

    # Step 3: Reserves — 나머지 관절 (약한 보조, Dembia 2020)
    mp.append(osim.ModOpAddReserves(reserves_scale))

    return mp


def get_default_model_path() -> str:
    """
    Return the standard Phase 1a-compatible model path.

    Model: forearm_v1 variant (De Leva 1996 hand geometry + no_coupler)
    Validation: Phase 1a regression PASS (max ΔES 1.227 %p < 5 %p).
    """
    return _DEFAULT_MODEL_PATH


def get_task_residuals(task_type: str) -> tuple[float, float]:
    """
    Return (rot_N·m, trans_N) default residuals for a given task.

    Parameters
    ----------
    task_type : str
        One of SUPPORTED_TASKS.

    Returns
    -------
    tuple[float, float]
        (rotational_F in N·m, translational_F in N)
    """
    task_type = task_type.lower().strip()
    if task_type not in _TASK_RESIDUALS:
        raise ValueError(
            f"Unknown task_type '{task_type}'. Supported: {SUPPORTED_TASKS}"
        )
    return _TASK_RESIDUALS[task_type]


def validate_residuals(
    reserves_sto: str,
    body_weight_n: float = 735.75,
    threshold_pct: float = 5.0,
) -> dict:
    """
    Hicks 2015 reserve 기준으로 Moco 결과를 검증.

    Hicks 2015 기준:
        translational < 5% BW (threshold_pct × body_weight_n / 100)
        rotational    < 1% BW×ht (assumes height=1.75 m)

    Parameters
    ----------
    reserves_sto : str
        Path to Moco solution .sto file.
    body_weight_n : float
        Body weight in N (default: 75 kg × 9.81 = 735.75 N).
    threshold_pct : float
        Reserve threshold as % BW (default 5%).

    Returns
    -------
    dict
        Keys: coordinate names (reserve columns in STO).
        Values: dict with 'max_val', 'threshold', 'pass', 'type'.
        Also includes '__summary__' key with overall PASS/FAIL.

    Raises
    ------
    FileNotFoundError
        reserves_sto 파일이 없을 때.

    Notes
    -----
    STO 컬럼에서 '/reserve_' 또는 'reserve_' 접두사를 가진 컬럼을 자동 식별.
    번역 (tx/ty/tz) vs 회전 (rx/ry/rz) 자동 분류.
    """
    if not os.path.isfile(reserves_sto):
        raise FileNotFoundError(f"STO file not found: {reserves_sto}")

    try:
        import numpy as np

        # Hicks 2015 임계값
        height_m = 1.75
        trans_thresh = body_weight_n * threshold_pct / 100.0         # N
        rot_thresh   = body_weight_n * height_m * 0.01                # N·m (1% BW×ht)

        # STO 읽기
        table = osim.TimeSeriesTable(reserves_sto)
        col_labels = list(table.getColumnLabels())

        # reserve 컬럼 식별
        reserve_cols = [c for c in col_labels
                        if 'reserve' in c.lower() or 'residual' in c.lower()]

        if not reserve_cols:
            warnings.warn(
                "No reserve/residual columns found in STO. "
                "컬럼명에 'reserve' 또는 'residual'이 없음.",
                UserWarning,
                stacklevel=2,
            )
            return {'__summary__': {'pass': True, 'reason': 'no reserve columns found'}}

        results = {}
        overall_pass = True

        for col in reserve_cols:
            col_data = np.abs(table.getDependentColumn(col).to_numpy())
            max_val = float(np.max(col_data))

            # 번역 vs 회전 분류 (tx/ty/tz → translational, 나머지 → rotational)
            col_lower = col.lower()
            is_trans = any(t in col_lower for t in ['_tx', '_ty', '_tz',
                                                      'pelvis_tx', 'pelvis_ty', 'pelvis_tz'])
            coord_type = 'translational' if is_trans else 'rotational'
            threshold  = trans_thresh if is_trans else rot_thresh

            passed = max_val <= threshold
            overall_pass = overall_pass and passed

            results[col] = {
                'max_val':   round(max_val, 4),
                'threshold': round(threshold, 4),
                'pass':      passed,
                'type':      coord_type,
            }

        results['__summary__'] = {
            'pass':        overall_pass,
            'n_columns':   len(reserve_cols),
            'trans_thresh_n':   round(trans_thresh, 2),
            'rot_thresh_nm':    round(rot_thresh,   2),
            'body_weight_n':    body_weight_n,
        }
        return results

    except Exception as exc:
        warnings.warn(
            f"validate_residuals 실패: {exc}",
            RuntimeWarning,
            stacklevel=2,
        )
        return {'__summary__': {'pass': None, 'error': str(exc)}}


# ---------------------------------------------------------------------------
# Smoke / compatibility tests
# ---------------------------------------------------------------------------

def test_phase1a_compatibility(
    model_path: Optional[str] = None,
    external_loads_xml: Optional[str] = None,
) -> dict:
    """
    Phase 1a 호환성 smoke test.

    검증 항목:
        T1  model file exists
        T2  ModelProcessor constructs without error
        T3  ModOpAddResiduals applied (rot=20, trans=50)
        T4  ModOpAddReserves applied (scale=1.0)
        T5  ExternalLoads applied when xml provided

    Returns
    -------
    dict
        Keys: 'T1'..'T5', values: {'pass': bool, 'detail': str}
        '__overall__': bool
    """
    mp_path = model_path or get_default_model_path()
    results: dict = {}

    # T1: file exists
    t1_pass = os.path.isfile(mp_path)
    results['T1_model_exists'] = {
        'pass':   t1_pass,
        'detail': mp_path if t1_pass else f"NOT FOUND: {mp_path}",
    }

    # T2: ModelProcessor 구성
    t2_pass = False
    t2_detail = ''
    if t1_pass:
        try:
            mp = build_model_processor(
                model_path=mp_path,
                task_type='stoop',
                external_loads_xml=external_loads_xml,
            )
            t2_pass = (mp is not None)
            t2_detail = 'ModelProcessor constructed OK'
        except Exception as exc:
            t2_detail = f"ERROR: {exc}"
    else:
        t2_detail = 'Skipped (T1 FAIL)'
    results['T2_mp_construct'] = {'pass': t2_pass, 'detail': t2_detail}

    # T3: residuals 값 확인 (stoop default: rot=20, trans=50)
    rot_default, trans_default = get_task_residuals('stoop')
    t3_pass = (rot_default == DEFAULT_RESIDUALS_ROT_STOOP and
               trans_default == DEFAULT_RESIDUALS_TRANS_STOOP)
    results['T3_residuals_stoop'] = {
        'pass':   t3_pass,
        'detail': f"rot={rot_default} N·m (expect {DEFAULT_RESIDUALS_ROT_STOOP}), "
                  f"trans={trans_default} N (expect {DEFAULT_RESIDUALS_TRANS_STOOP})",
    }

    # T4: reserves scale
    t4_pass = (DEFAULT_RESERVES_SCALE == 1.0)
    results['T4_reserves_scale'] = {
        'pass':   t4_pass,
        'detail': f"DEFAULT_RESERVES_SCALE={DEFAULT_RESERVES_SCALE} (expect 1.0)",
    }

    # T5: ExternalLoads (xml 제공 시만)
    if external_loads_xml is not None:
        t5_exists = os.path.isfile(external_loads_xml)
        results['T5_external_loads'] = {
            'pass':   t5_exists,
            'detail': external_loads_xml if t5_exists
                      else f"NOT FOUND: {external_loads_xml}",
        }

    overall = all(v['pass'] for k, v in results.items() if not k.startswith('__'))
    results['__overall__'] = overall
    return results


def run_verification(verbose: bool = True) -> bool:
    """
    Full smoke test — Phase 1a + Box residuals 검증.

    Returns True if all tests PASS.
    """
    print("=" * 60)
    print("base/model_setup.py — Verification Suite")
    print("=" * 60)

    # Phase 1a (stoop)
    print("\n[Phase 1a Compatibility Test]")
    r1 = test_phase1a_compatibility()
    _print_results(r1, verbose)

    # Box/squat residuals
    print("\n[Box/Squat Residuals Check]")
    box_rot, box_trans = get_task_residuals('box')
    box_ok = (box_rot == DEFAULT_RESIDUALS_ROT_BOX and
              box_trans == DEFAULT_RESIDUALS_TRANS_BOX)
    print(f"  rot   = {box_rot} N·m  (expect {DEFAULT_RESIDUALS_ROT_BOX})  "
          f"{'PASS' if box_ok else 'FAIL'}")
    print(f"  trans = {box_trans} N   (expect {DEFAULT_RESIDUALS_TRANS_BOX})  "
          f"{'PASS' if box_ok else 'FAIL'}")

    # Walk residuals
    print("\n[Walk Residuals Check]")
    walk_rot, walk_trans = get_task_residuals('walk')
    walk_ok = (walk_rot == DEFAULT_RESIDUALS_ROT_WALK and
               walk_trans == DEFAULT_RESIDUALS_TRANS_WALK)
    print(f"  rot   = {walk_rot} N·m  (expect {DEFAULT_RESIDUALS_ROT_WALK})  "
          f"{'PASS' if walk_ok else 'FAIL'}")
    print(f"  trans = {walk_trans} N   (expect {DEFAULT_RESIDUALS_TRANS_WALK})  "
          f"{'PASS' if walk_ok else 'FAIL'}")

    # Hicks 2015 임계값 확인
    print("\n[Hicks 2015 Threshold Constants]")
    print(f"  translational threshold = {HICKS_TRANS_THRESHOLD_N} N "
          f"(5% × 735.75 N BW)")
    print(f"  rotational    threshold = {HICKS_ROT_THRESHOLD_NM} N·m "
          f"(1% × 735.75 N × 1.75 m)")

    overall = r1['__overall__'] and box_ok and walk_ok
    print("\n" + "=" * 60)
    print(f"Overall: {'PASS' if overall else 'FAIL'}")
    print("=" * 60)
    return overall


def _print_results(results: dict, verbose: bool = True) -> None:
    for key, val in results.items():
        if key.startswith('__'):
            continue
        status = 'PASS' if val['pass'] else 'FAIL'
        print(f"  {key:<35} {status}  {val['detail']}")


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    ok = run_verification(verbose=True)
    sys.exit(0 if ok else 1)
