"""
Step 2 Week 2 — Integration Test Suite (P1-P8, B1-B11).

Tests four base modules end-to-end for Phase 1a stoop and box scenarios.
No actual Moco solve is performed (setup-only verification).

Usage:
    cd /data/wearable-assist
    /home/sysop/miniconda3/envs/opensim/bin/python tests/test_integration.py

Results:
    Phase 1a stoop path (P1-P8)  — build_model + suit + moco_track + ExternalLoads STO
    Box scenario path  (B1-B11)  — + contact_model (4 spheres) + hand force
"""

from __future__ import annotations

import os
import sys
import tempfile

# Add project root to path for `base` imports
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BASE_DIR = os.path.join(
    _REPO_ROOT,
    'opensim_analysis', 'thoracolumbar_fb',
)
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

import opensim as osim

# ---------------------------------------------------------------------------
# Known paths (verified on this system)
# ---------------------------------------------------------------------------
_MODEL_PATH = (
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
    'MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim'
)
_STOOP_MOTION = '/data/stoop_motion/stoop_synthetic_v5.mot'
_STOOP_GRF_XML = '/data/stoop_motion/stoop_grf_v5.xml'
_BOX_MOTION = '/data/stoop_motion/box_motion_v11b.mot'

# Temporary output directory for generated test files
_TMP_DIR = tempfile.mkdtemp(prefix='week2_integration_')


# ===========================================================================
# Phase 1a Stoop Integration Tests (P1-P8)
# ===========================================================================

def run_phase1a_tests() -> dict:
    """Execute P1-P8 integration tests for the stoop pipeline."""
    from base import (
        build_model_processor,
        get_default_model_path,
        SuitConfig,
        make_suit_sweep,
        create_suit_actuators,
        setup_for_stoop_task,
        verify_john2022_compatibility,
        DEFAULT_MESH_INTERVAL,
        PHASE1A_FORCE_N,
        PHASE1A_MOMENT_ARM,
        PHASE1A_TORQUE_NM,
    )

    results: dict = {}

    # ------------------------------------------------------------------ P1 --
    # Import all required Phase 1a symbols
    try:
        assert build_model_processor is not None
        assert get_default_model_path is not None
        assert SuitConfig is not None
        assert make_suit_sweep is not None
        assert create_suit_actuators is not None
        assert setup_for_stoop_task is not None
        assert verify_john2022_compatibility is not None
        results['P1'] = {'pass': True,
                         'detail': '7 Phase 1a symbols imported OK'}
    except Exception as exc:
        results['P1'] = {'pass': False, 'detail': f'ImportError: {exc}'}

    # ------------------------------------------------------------------ P2 --
    # ModelProcessor with stoop residuals (20 N·m / 50 N)
    try:
        model_path = get_default_model_path()
        mp = build_model_processor(
            model_path=model_path,
            task_type='stoop',
        )
        assert mp is not None
        from base import DEFAULT_RESIDUALS_ROT_STOOP, DEFAULT_RESIDUALS_TRANS_STOOP
        rot_ok = DEFAULT_RESIDUALS_ROT_STOOP == 20.0
        trans_ok = DEFAULT_RESIDUALS_TRANS_STOOP == 50.0
        passed = rot_ok and trans_ok
        results['P2'] = {
            'pass': passed,
            'detail': (
                f'ModelProcessor OK, residuals rot={DEFAULT_RESIDUALS_ROT_STOOP} N·m '
                f'trans={DEFAULT_RESIDUALS_TRANS_STOOP} N '
                f'(expect 20/50)'
            ),
        }
    except Exception as exc:
        results['P2'] = {'pass': False, 'detail': f'ERROR: {exc}'}

    # ------------------------------------------------------------------ P3 --
    # SuitConfig L20 = 24 N·m verified
    try:
        cfg = SuitConfig('L20', force_N=PHASE1A_FORCE_N,
                         moment_arm_m=PHASE1A_MOMENT_ARM)
        torque_ok = abs(cfg.torque_Nm - PHASE1A_TORQUE_NM) < 1e-9
        results['P3'] = {
            'pass': torque_ok,
            'detail': (
                f'SuitConfig L20 torque_Nm={cfg.torque_Nm} '
                f'(expect {PHASE1A_TORQUE_NM})'
            ),
        }
    except Exception as exc:
        results['P3'] = {'pass': False, 'detail': f'ERROR: {exc}'}

    # ------------------------------------------------------------------ P4 --
    # MocoStudy from setup_for_stoop_task
    study_stoop = None
    if os.path.isfile(_MODEL_PATH) and os.path.isfile(_STOOP_MOTION):
        try:
            mp_stoop = build_model_processor(
                model_path=_MODEL_PATH, task_type='stoop'
            )
            ref_motion = osim.TableProcessor(_STOOP_MOTION)
            study_stoop = setup_for_stoop_task(mp_stoop, ref_motion, 0.0, 5.0)
            passed = isinstance(study_stoop, osim.MocoStudy)
            results['P4'] = {
                'pass': passed,
                'detail': f'setup_for_stoop_task returned {type(study_stoop).__name__}',
            }
        except Exception as exc:
            results['P4'] = {'pass': False, 'detail': f'ERROR: {exc}'}
    else:
        missing = []
        if not os.path.isfile(_MODEL_PATH):
            missing.append('model')
        if not os.path.isfile(_STOOP_MOTION):
            missing.append('stoop_motion')
        results['P4'] = {'pass': False, 'detail': f'Files missing: {missing}'}

    # ------------------------------------------------------------------ P5 --
    # verify_john2022_compatibility == True
    if study_stoop is not None:
        try:
            compat = verify_john2022_compatibility(study_stoop)
            results['P5'] = {
                'pass': compat,
                'detail': f'verify_john2022_compatibility={compat} (expect True)',
            }
        except Exception as exc:
            results['P5'] = {'pass': False, 'detail': f'ERROR: {exc}'}
    else:
        results['P5'] = {'pass': False, 'detail': 'Skipped (P4 FAIL)'}

    # ------------------------------------------------------------------ P6 --
    # ExternalLoads GRF STO correctly loaded
    if os.path.isfile(_STOOP_GRF_XML):
        try:
            if os.path.isfile(_MODEL_PATH):
                mp_ext = build_model_processor(
                    model_path=_MODEL_PATH,
                    task_type='stoop',
                    external_loads_xml=_STOOP_GRF_XML,
                )
                passed = mp_ext is not None
                results['P6'] = {
                    'pass': passed,
                    'detail': (
                        f'ExternalLoads XML loaded: {os.path.basename(_STOOP_GRF_XML)}'
                    ),
                }
            else:
                results['P6'] = {'pass': False, 'detail': 'Model file missing'}
        except Exception as exc:
            results['P6'] = {'pass': False, 'detail': f'ERROR: {exc}'}
    else:
        results['P6'] = {
            'pass': False,
            'detail': f'GRF XML not found: {_STOOP_GRF_XML}',
        }

    # ------------------------------------------------------------------ P7 --
    # Mesh interval 0.02 s (250 mesh / 5 s)
    try:
        mi = DEFAULT_MESH_INTERVAL
        passed = abs(mi - 0.02) < 1e-9
        n_mesh_expected = int(5.0 / mi)   # 250 for 5 s at 0.02 s
        results['P7'] = {
            'pass': passed,
            'detail': (
                f'DEFAULT_MESH_INTERVAL={mi} s '
                f'→ {n_mesh_expected} intervals for 5 s motion '
                f'(expect 0.02 s / 250 mesh)'
            ),
        }
    except Exception as exc:
        results['P7'] = {'pass': False, 'detail': f'ERROR: {exc}'}

    # ------------------------------------------------------------------ P8 --
    # Suit 5 actuators, 4.8 N·m each (24 N·m / 5 segments)
    try:
        cfg_l20 = SuitConfig('L20', force_N=200.0, moment_arm_m=0.12)
        actuators = create_suit_actuators(cfg_l20)
        n = len(actuators)
        torque_per = cfg_l20.torque_Nm / 5
        passed = (n == 5) and (abs(torque_per - 4.8) < 1e-6)
        results['P8'] = {
            'pass': passed,
            'detail': (
                f'{n} actuators, {torque_per:.2f} N·m each '
                f'(expect 5 × 4.8 N·m = 24 N·m total)'
            ),
        }
    except Exception as exc:
        results['P8'] = {'pass': False, 'detail': f'ERROR: {exc}'}

    overall = all(v['pass'] for v in results.values())
    results['__overall__'] = overall
    return results


# ===========================================================================
# Box Scenario Integration Tests (B1-B11)
# ===========================================================================

def run_box_tests() -> dict:
    """Execute B1-B11 integration tests for the box lifting pipeline."""
    from base import (
        build_model_processor,
        get_default_model_path,
        SuitConfig,
        make_suit_sweep,
        add_foot_contact_model,
        setup_box_lifting_contact,
        count_contact_geometry,
        count_contact_forces,
        verify_falisse2019_compatibility,
        setup_for_box_task,
        add_hand_external_force_xml,
        generate_box_force_sto,
        DEFAULT_RESIDUALS_ROT_BOX,
        DEFAULT_RESIDUALS_TRANS_BOX,
    )

    results: dict = {}

    # ------------------------------------------------------------------ B1 --
    # Import all box-related symbols
    try:
        assert add_foot_contact_model is not None
        assert setup_box_lifting_contact is not None
        assert count_contact_geometry is not None
        assert count_contact_forces is not None
        assert verify_falisse2019_compatibility is not None
        assert add_hand_external_force_xml is not None
        assert generate_box_force_sto is not None
        results['B1'] = {'pass': True,
                         'detail': '7 box-related symbols imported OK'}
    except Exception as exc:
        results['B1'] = {'pass': False, 'detail': f'ImportError: {exc}'}

    # ------------------------------------------------------------------ B2 --
    # ModelProcessor with box residuals (50 N·m / 300 N)
    try:
        rot_ok = DEFAULT_RESIDUALS_ROT_BOX == 50.0
        trans_ok = DEFAULT_RESIDUALS_TRANS_BOX == 300.0
        passed = rot_ok and trans_ok
        results['B2'] = {
            'pass': passed,
            'detail': (
                f'box residuals rot={DEFAULT_RESIDUALS_ROT_BOX} N·m '
                f'trans={DEFAULT_RESIDUALS_TRANS_BOX} N (expect 50/300)'
            ),
        }
    except Exception as exc:
        results['B2'] = {'pass': False, 'detail': f'ERROR: {exc}'}

    # ------------------------------------------------------------------ B3 --
    # Model.process() returns a valid Model
    base_model = None
    if os.path.isfile(_MODEL_PATH):
        try:
            mp = build_model_processor(
                model_path=_MODEL_PATH, task_type='box'
            )
            base_model = mp.process()
            n_bodies = base_model.getBodySet().getSize()
            passed = (base_model is not None) and (n_bodies > 0)
            results['B3'] = {
                'pass': passed,
                'detail': (
                    f'mp.process() returned Model with '
                    f'{n_bodies} bodies'
                ),
            }
        except Exception as exc:
            results['B3'] = {'pass': False, 'detail': f'ERROR: {exc}'}
    else:
        results['B3'] = {'pass': False, 'detail': f'Model not found: {_MODEL_PATH}'}

    # ------------------------------------------------------------------ B4 --
    # add_foot_contact_model adds 4 contact spheres
    model_with_contact = None
    if base_model is not None:
        try:
            model_with_contact = add_foot_contact_model(base_model)
            geom = count_contact_geometry(model_with_contact)
            n_sph = geom['spheres']
            n_hs = geom['halfspaces']
            passed = (n_sph == 4) and (n_hs >= 1)
            results['B4'] = {
                'pass': passed,
                'detail': (
                    f'add_foot_contact_model: spheres={n_sph} '
                    f'halfspaces={n_hs} (expect 4 spheres, >=1 hs)'
                ),
            }
        except Exception as exc:
            results['B4'] = {'pass': False, 'detail': f'ERROR: {exc}'}
    else:
        results['B4'] = {'pass': False, 'detail': 'Skipped (B3 FAIL)'}

    # ------------------------------------------------------------------ B5 --
    # count_contact_forces == 4
    if model_with_contact is not None:
        try:
            n_forces = count_contact_forces(model_with_contact)
            passed = (n_forces == 4)
            results['B5'] = {
                'pass': passed,
                'detail': (
                    f'count_contact_forces={n_forces} '
                    f'(expect 4 SmoothSphereHalfSpaceForce)'
                ),
            }
        except Exception as exc:
            results['B5'] = {'pass': False, 'detail': f'ERROR: {exc}'}
    else:
        results['B5'] = {'pass': False, 'detail': 'Skipped (B4 FAIL)'}

    # ------------------------------------------------------------------ B6 --
    # setup_box_lifting_contact box_force = 98.1 N per hand
    if model_with_contact is not None:
        try:
            # Use a freshly processed model to avoid double contact addition
            mp2 = build_model_processor(
                model_path=_MODEL_PATH, task_type='box'
            )
            fresh_model = mp2.process()
            box_info = setup_box_lifting_contact(fresh_model, box_mass_kg=20.0)
            force_n = box_info['box_force_N_per_hand']
            expected = 20.0 * 9.81 / 2.0   # 98.1
            passed = abs(force_n - expected) < 1e-3
            results['B6'] = {
                'pass': passed,
                'detail': (
                    f'box_force_N_per_hand={force_n:.2f} N '
                    f'(expect {expected:.2f} N = 20 kg × 9.81 / 2)'
                ),
            }
        except Exception as exc:
            results['B6'] = {'pass': False, 'detail': f'ERROR: {exc}'}
    else:
        results['B6'] = {'pass': False, 'detail': 'Skipped (B3 FAIL)'}

    # ------------------------------------------------------------------ B7 --
    # make_suit_sweep 5 conditions → torques [0, 6, 12, 18, 24] N·m
    try:
        sweep = make_suit_sweep([0, 50, 100, 150, 200])
        n = len(sweep)
        torques = [s.torque_Nm for s in sweep]
        expected_torques = [0.0, 6.0, 12.0, 18.0, 24.0]
        all_ok = all(
            abs(t - e) < 1e-9 for t, e in zip(torques, expected_torques)
        )
        passed = (n == 5) and all_ok
        results['B7'] = {
            'pass': passed,
            'detail': (
                f'{n} sweep conditions, torques={torques} N·m '
                f'(expect [0,6,12,18,24] N·m)'
            ),
        }
    except Exception as exc:
        results['B7'] = {'pass': False, 'detail': f'ERROR: {exc}'}

    # ------------------------------------------------------------------ B8 --
    # MocoStudy from setup_for_box_task
    study_box = None
    if os.path.isfile(_MODEL_PATH) and os.path.isfile(_BOX_MOTION):
        try:
            mp_box = build_model_processor(
                model_path=_MODEL_PATH, task_type='box'
            )
            ref_box = osim.TableProcessor(_BOX_MOTION)
            study_box = setup_for_box_task(mp_box, ref_box, 1.0, 4.0)
            passed = isinstance(study_box, osim.MocoStudy)
            results['B8'] = {
                'pass': passed,
                'detail': (
                    f'setup_for_box_task returned {type(study_box).__name__} '
                    f'(t=1.0–4.0 s)'
                ),
            }
        except Exception as exc:
            results['B8'] = {'pass': False, 'detail': f'ERROR: {exc}'}
    else:
        missing = []
        if not os.path.isfile(_MODEL_PATH):
            missing.append('model')
        if not os.path.isfile(_BOX_MOTION):
            missing.append('box_motion')
        results['B8'] = {'pass': False, 'detail': f'Files missing: {missing}'}

    # ------------------------------------------------------------------ B9 --
    # verify_falisse2019_compatibility == True
    if model_with_contact is not None:
        try:
            compat = verify_falisse2019_compatibility(model_with_contact)
            results['B9'] = {
                'pass': compat,
                'detail': (
                    f'verify_falisse2019_compatibility={compat} (expect True)'
                ),
            }
        except Exception as exc:
            results['B9'] = {'pass': False, 'detail': f'ERROR: {exc}'}
    else:
        results['B9'] = {'pass': False, 'detail': 'Skipped (B4 FAIL)'}

    # ------------------------------------------------------------------ B10 --
    # add_hand_external_force_xml generates XML file
    xml_path = os.path.join(_TMP_DIR, 'hand_external_loads_test.xml')
    if os.path.isfile(_BOX_MOTION):
        sto_path_dummy = os.path.join(_TMP_DIR, 'hand_forces_dummy.sto')
        # Create a minimal placeholder STO so the XML generator passes
        with open(sto_path_dummy, 'w') as fh:
            fh.write('placeholder\nversion=1\nnRows=1\nnColumns=1\n'
                     'inDegrees=no\nendheader\ntime\n0.0\n')
        try:
            result_path = add_hand_external_force_xml(
                output_xml_path=xml_path,
                hand_force_data_sto=sto_path_dummy,
                body_r='hand_r',
                body_l='hand_l',
            )
            xml_exists = os.path.isfile(result_path)
            # Quick content check
            with open(result_path) as fh:
                content = fh.read()
            has_r = 'hand_r_box_force' in content
            has_l = 'hand_l_box_force' in content
            has_sto = 'hand_forces_dummy.sto' in content
            passed = xml_exists and has_r and has_l and has_sto
            results['B10'] = {
                'pass': passed,
                'detail': (
                    f'XML file exists={xml_exists}, '
                    f'hand_r={has_r}, hand_l={has_l}, sto_ref={has_sto}'
                ),
            }
        except Exception as exc:
            results['B10'] = {'pass': False, 'detail': f'ERROR: {exc}'}
    else:
        results['B10'] = {
            'pass': False,
            'detail': f'box_motion not found (need time range): {_BOX_MOTION}',
        }

    # ------------------------------------------------------------------ B11 --
    # generate_box_force_sto generates STO with correct columns
    sto_out = os.path.join(_TMP_DIR, 'box_hand_forces_test.sto')
    if os.path.isfile(_BOX_MOTION):
        try:
            result_sto = generate_box_force_sto(
                output_sto_path=sto_out,
                motion_file=_BOX_MOTION,
                box_mass_kg=20.0,
                grasp_start_time=2.0,
            )
            sto_exists = os.path.isfile(result_sto)
            # Check column presence
            with open(result_sto) as fh:
                content_sto = fh.read()
            required_cols = [
                'hand_r_force_vx', 'hand_r_force_vy', 'hand_r_force_vz',
                'hand_l_force_vx', 'hand_l_force_vy', 'hand_l_force_vz',
                'hand_r_point_px', 'hand_l_point_px',
            ]
            cols_ok = all(c in content_sto for c in required_cols)
            # Verify force value at t > grasp_start_time
            expected_f = 20.0 * 9.81 / 2.0
            # Find a data line with t >= 2.0
            force_ok = False
            in_data = False
            for line in content_sto.split('\n'):
                if 'endheader' in line:
                    in_data = True
                    continue
                if not in_data or not line.strip():
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    try:
                        t = float(parts[0])
                        fy = float(parts[2])
                        if t >= 2.0 and abs(fy - expected_f) < 0.1:
                            force_ok = True
                            break
                    except ValueError:
                        continue
            passed = sto_exists and cols_ok and force_ok
            results['B11'] = {
                'pass': passed,
                'detail': (
                    f'STO exists={sto_exists}, '
                    f'columns OK={cols_ok}, '
                    f'force at t>=2.0 = {expected_f:.1f} N verified={force_ok}'
                ),
            }
        except Exception as exc:
            results['B11'] = {'pass': False, 'detail': f'ERROR: {exc}'}
    else:
        results['B11'] = {
            'pass': False,
            'detail': f'box_motion not found: {_BOX_MOTION}',
        }

    overall = all(v['pass'] for k, v in results.items() if not k.startswith('__'))
    results['__overall__'] = overall
    return results


# ===========================================================================
# Reporting
# ===========================================================================

def _print_section(title: str, results: dict, prefix: str) -> tuple:
    """Print test results and return (n_pass, n_total)."""
    print(f'\n{"=" * 65}')
    print(f'  {title}')
    print(f'{"=" * 65}')
    keys = [k for k in results if not k.startswith('__') and k.startswith(prefix)]
    n_pass = 0
    n_total = 0
    for key in keys:
        val = results[key]
        status = 'PASS' if val['pass'] else 'FAIL'
        if val['pass']:
            n_pass += 1
        n_total += 1
        flag = '[CRITICAL]' if key in {
            'P5', 'B4', 'B5', 'B6', 'B10', 'B11'
        } else ''
        print(f'  {key:<5}  {status:<5}  {val["detail"]:<55} {flag}')
    print(f'\n  Result: {n_pass}/{n_total} PASS')
    return n_pass, n_total


def run_all() -> bool:
    """Run P1-P8 and B1-B11 and print summary. Returns True if all pass."""
    print('\n' + '=' * 65)
    print('  Step 2 Week 2 — Integration Verification (P1-P8, B1-B11)')
    print('  No Moco solve — setup-only validation')
    print('=' * 65)

    p_results = run_phase1a_tests()
    b_results = run_box_tests()

    p_pass, p_total = _print_section(
        'Phase 1a Stoop Integration (P1-P8)', p_results, 'P'
    )
    b_pass, b_total = _print_section(
        'Box Scenario Integration (B1-B11)', b_results, 'B'
    )

    total_pass = p_pass + b_pass
    total_n = p_total + b_total
    all_pass = (total_pass == total_n)

    print('\n' + '=' * 65)
    print(f'  OVERALL: {total_pass}/{total_n} PASS  '
          f'{"ALL PASS" if all_pass else "SOME FAIL"}')
    print(f'  Temp output dir: {_TMP_DIR}')
    print('=' * 65 + '\n')

    # Structured result dict (for diagram generator)
    return all_pass, p_results, b_results


if __name__ == '__main__':
    ok, _p, _b = run_all()
    sys.exit(0 if ok else 1)
