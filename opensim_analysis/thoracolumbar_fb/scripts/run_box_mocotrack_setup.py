"""
Phase 1: Box MocoTrack Setup Verification.

Verifies that all infrastructure components needed for box MocoTrack are
in place and correctly configured before running B_suit0 pilot.

Checks performed:
    S1  Model file exists (no_coupler + forearm_v1)
    S2  base/ modules importable
    S3  SuitConfig sweep generates correct N->Nm mapping
    S4  Motion file exists + time range [0.0, 5.0]
    S5  generate_box_force_sto() produces valid STO
    S6  add_hand_external_force_xml() produces valid XML
    S7  build_model_processor() box task (trans=300, rot=50)
    S8  add_foot_contact_model() adds 4 spheres + 1 halfspace + 4 forces
    S9  setup_for_box_task() MocoStudy constructs (no solve)

Usage:
    python run_box_mocotrack_setup.py
    python run_box_mocotrack_setup.py --write-artifacts

On PASS: proceed with run_box_mocotrack_pilot.py (B_suit0 single condition).
On FAIL: diagnose flagged test before proceeding.

Architecture:
    base/model_setup.py     -- build_model_processor, task_type='box'
    base/contact_model.py   -- add_foot_contact_model, generate_box_force_sto,
                               add_hand_external_force_xml
    base/suit_torque_module -- make_suit_sweep, SuitConfig
    base/moco_track_setup   -- setup_for_box_task

References:
    Dembia 2020 (OpenSim Moco): ModOpAddResiduals(50, 300, 1.0) for box task
    Falisse 2019 (J R Soc Interface): SmoothSphereHalfSpaceForce parameters
    John 2022 (Comput Methods Biomech Biomed Eng): MocoTrack + exo setup
    Hicks 2015 (J Biomech Eng): Reserve thresholds (trans<36.8 N, rot<12.9 Nm)
"""
from __future__ import annotations

import os
import sys
import time
import argparse
from pathlib import Path

os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')

# --- path setup ---
BASE_DIR = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb')
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'scripts'))

# --- constants ---
MODEL_PATH = (
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
    'MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim'
)
MOTION_FILE  = '/data/stoop_motion/box_motion_v11b.mot'
OUT_ROOT     = Path('/data/opensim_results/box_mocotrack_v1')
SHARED_DIR   = OUT_ROOT / 'shared'

# Time window (same as v5: 3 s of active motion)
T_START, T_END = 1.0, 4.0
BOX_MASS_KG    = 20.0
GRASP_TIME     = 2.0         # s — hand forces become active
GRIP_POINT     = (0.40, 0.75, 0.0)  # x, y, z in ground frame (m)


def log(msg: str) -> None:
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def run_setup_checks(write_artifacts: bool = False) -> dict:
    """Execute S1-S9 setup verification checks."""
    results: dict = {}

    # ------------------------------------------------------------------ S1
    log('S1: Model file exists...')
    s1_pass = os.path.isfile(MODEL_PATH)
    results['S1_model_exists'] = {
        'pass': s1_pass,
        'detail': MODEL_PATH if s1_pass else f'NOT FOUND: {MODEL_PATH}',
    }

    # ------------------------------------------------------------------ S2
    log('S2: base/ modules importable...')
    try:
        from base import (
            build_model_processor, get_default_model_path,
            SuitConfig, make_suit_sweep,
            setup_for_box_task,
            add_foot_contact_model, generate_box_force_sto,
            add_hand_external_force_xml,
            DEFAULT_RESIDUALS_ROT_BOX, DEFAULT_RESIDUALS_TRANS_BOX,
            HICKS_TRANS_THRESHOLD_N, HICKS_ROT_THRESHOLD_NM,
        )
        results['S2_base_imports'] = {
            'pass': True,
            'detail': 'All base/ symbols imported successfully',
        }
    except Exception as exc:
        results['S2_base_imports'] = {
            'pass': False,
            'detail': f'ImportError: {exc}',
        }
        # Cannot continue without base/
        results['__overall__'] = False
        return results

    # ------------------------------------------------------------------ S3
    log('S3: SuitConfig sweep generates correct N->Nm mapping...')
    try:
        sweep = make_suit_sweep([0, 50, 100, 150, 200])
        expected = [(0, 0.0), (50, 6.0), (100, 12.0), (150, 18.0), (200, 24.0)]
        s3_pass = True
        details = []
        for cfg, (exp_n, exp_nm) in zip(sweep, expected):
            ok = (cfg.force_N == exp_n and abs(cfg.torque_Nm - exp_nm) < 1e-9)
            s3_pass = s3_pass and ok
            details.append(f'{cfg.name}: {cfg.force_N}N -> {cfg.torque_Nm}Nm {"OK" if ok else "FAIL"}')
        results['S3_suit_sweep_mapping'] = {
            'pass': s3_pass,
            'detail': ' | '.join(details),
        }
    except Exception as exc:
        results['S3_suit_sweep_mapping'] = {'pass': False, 'detail': f'ERROR: {exc}'}

    # ------------------------------------------------------------------ S4
    log('S4: Motion file exists + time range...')
    s4_pass = os.path.isfile(MOTION_FILE)
    s4_detail = ''
    if s4_pass:
        try:
            import opensim as osim
            tbl = osim.TimeSeriesTable(MOTION_FILE)
            times = list(tbl.getIndependentColumn())
            t0, t1 = times[0], times[-1]
            n_rows = len(times)
            s4_detail = (
                f't=[{t0:.3f}, {t1:.3f}] s, nRows={n_rows}. '
                f'MocoTrack window=[{T_START}, {T_END}] s OK={T_START >= t0 and T_END <= t1}'
            )
            s4_pass = (T_START >= t0 and T_END <= t1)
        except Exception as exc:
            s4_detail = f'Could not read time range: {exc}'
            s4_pass = False
    else:
        s4_detail = f'NOT FOUND: {MOTION_FILE}'
    results['S4_motion_time_range'] = {'pass': s4_pass, 'detail': s4_detail}

    # ------------------------------------------------------------------ S5
    log('S5: generate_box_force_sto() produces valid STO...')
    sto_path = str(SHARED_DIR / 'box_hand_force.sto')
    try:
        SHARED_DIR.mkdir(parents=True, exist_ok=True)
        out = generate_box_force_sto(
            output_sto_path=sto_path,
            motion_file=MOTION_FILE,
            box_mass_kg=BOX_MASS_KG,
            grasp_start_time=GRASP_TIME,
            grip_point_ground=GRIP_POINT,
        )
        s5_pass = os.path.isfile(out)
        if s5_pass:
            # Quick validation: check file size and key content
            with open(out) as f:
                content = f.read()
            has_header = 'endheader' in content.lower()
            has_force_col = 'hand_r_force_vy' in content
            # Expected force per hand = 20 * 9.81 / 2 = 98.1 N
            expected_f = f'{BOX_MASS_KG * 9.81 / 2:.4f}'
            has_force_val = expected_f in content
            s5_pass = has_header and has_force_col and has_force_val
            s5_detail = (
                f'STO created: {out} '
                f'| header={has_header} | force_col={has_force_col} '
                f'| force_val({expected_f}N)={has_force_val}'
            )
        else:
            s5_detail = f'Output file not found after generation: {out}'
    except Exception as exc:
        s5_pass = False
        s5_detail = f'ERROR: {exc}'
    results['S5_box_force_sto'] = {'pass': s5_pass, 'detail': s5_detail}

    # ------------------------------------------------------------------ S6
    log('S6: add_hand_external_force_xml() produces valid XML...')
    xml_path = str(SHARED_DIR / 'box_hand_loads.xml')
    try:
        SHARED_DIR.mkdir(parents=True, exist_ok=True)
        if not os.path.isfile(sto_path):
            # Create a minimal STO for xml generation test
            generate_box_force_sto(
                output_sto_path=sto_path,
                motion_file=MOTION_FILE,
                box_mass_kg=BOX_MASS_KG,
                grasp_start_time=GRASP_TIME,
                grip_point_ground=GRIP_POINT,
            )
        out_xml = add_hand_external_force_xml(
            output_xml_path=xml_path,
            hand_force_data_sto=sto_path,
        )
        s6_pass = os.path.isfile(out_xml)
        if s6_pass:
            with open(out_xml) as f:
                xml_content = f.read()
            has_hand_r = 'hand_r' in xml_content.lower()
            has_hand_l = 'hand_l' in xml_content.lower()
            has_external_loads = 'ExternalLoads' in xml_content
            s6_pass = has_hand_r and has_hand_l and has_external_loads
            s6_detail = (
                f'XML created: {out_xml} '
                f'| hand_r={has_hand_r} | hand_l={has_hand_l} '
                f'| ExternalLoads={has_external_loads}'
            )
        else:
            s6_detail = f'Output XML not found: {out_xml}'
    except Exception as exc:
        s6_pass = False
        s6_detail = f'ERROR: {exc}'
    results['S6_hand_force_xml'] = {'pass': s6_pass, 'detail': s6_detail}

    # ------------------------------------------------------------------ S7
    log('S7: build_model_processor() box task (trans=300, rot=50)...')
    try:
        mp = build_model_processor(
            model_path=MODEL_PATH,
            task_type='box',
            reserves_scale=1.0,
        )
        # Verify residual defaults match box spec
        from base import DEFAULT_RESIDUALS_ROT_BOX, DEFAULT_RESIDUALS_TRANS_BOX
        rot_ok   = (DEFAULT_RESIDUALS_ROT_BOX   == 50.0)
        trans_ok = (DEFAULT_RESIDUALS_TRANS_BOX  == 300.0)
        s7_pass  = (mp is not None) and rot_ok and trans_ok
        s7_detail = (
            f'ModelProcessor OK | rot={DEFAULT_RESIDUALS_ROT_BOX} N·m '
            f'(expect 50) {chr(10004) if rot_ok else chr(10008)} | '
            f'trans={DEFAULT_RESIDUALS_TRANS_BOX} N '
            f'(expect 300) {chr(10004) if trans_ok else chr(10008)}'
        )
    except Exception as exc:
        s7_pass = False
        s7_detail = f'ERROR: {exc}'
    results['S7_model_processor_box'] = {'pass': s7_pass, 'detail': s7_detail}

    # ------------------------------------------------------------------ S8
    log('S8: add_foot_contact_model() adds 4 spheres + halfspace + 4 forces...')
    try:
        import opensim as osim
        from base import (
            add_foot_contact_model,
            count_contact_geometry, count_contact_forces,
            verify_falisse2019_compatibility,
        )
        model = osim.Model(MODEL_PATH)
        model = add_foot_contact_model(model)
        model.finalizeConnections()
        geom = count_contact_geometry(model)
        forces = count_contact_forces(model)
        falisse_ok = verify_falisse2019_compatibility(model)
        s8_pass = (
            geom['spheres'] == 4
            and geom['halfspaces'] >= 1
            and forces == 4
            and falisse_ok
        )
        s8_detail = (
            f'spheres={geom["spheres"]} (expect 4), '
            f'halfspaces={geom["halfspaces"]} (expect >=1), '
            f'forces={forces} (expect 4), '
            f'Falisse2019_ok={falisse_ok}'
        )
    except Exception as exc:
        s8_pass = False
        s8_detail = f'ERROR: {exc}'
    results['S8_foot_contact_model'] = {'pass': s8_pass, 'detail': s8_detail}

    # ------------------------------------------------------------------ S9
    log('S9: setup_for_box_task() MocoStudy constructs (no solve)...')
    try:
        import opensim as osim
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            mp_study = build_model_processor(
                model_path=MODEL_PATH,
                task_type='box',
                reserves_scale=1.0,
            )
        ref = osim.TableProcessor(MOTION_FILE)
        study = setup_for_box_task(mp_study, ref, T_START, T_END)
        s9_pass = isinstance(study, osim.MocoStudy)
        s9_detail = (
            f'MocoStudy constructed: {type(study).__name__} '
            f'| time=[{T_START}, {T_END}] s | no solve (verification only)'
        )
    except Exception as exc:
        s9_pass = False
        s9_detail = f'ERROR: {exc}'
    results['S9_moco_study_box'] = {'pass': s9_pass, 'detail': s9_detail}

    # --- overall ---
    check_keys = [k for k in results if not k.startswith('__')]
    overall = all(results[k]['pass'] for k in check_keys)
    results['__overall__'] = overall
    return results


def print_results(results: dict) -> None:
    """Print formatted setup check results."""
    print()
    print('=' * 70)
    print('Box MocoTrack Setup Verification — S1-S9')
    print('=' * 70)
    for key, val in results.items():
        if key.startswith('__'):
            continue
        status = 'PASS' if val['pass'] else 'FAIL'
        print(f'  {key:<35} {status}')
        print(f'    {val["detail"]}')
    print()
    overall = results.get('__overall__', False)
    print('=' * 70)
    print(f'Overall: {"PASS" if overall else "FAIL"}')
    if overall:
        print('  -> Ready for run_box_mocotrack_pilot.py (B_suit0 single condition)')
    else:
        fail_keys = [k for k, v in results.items()
                     if not k.startswith('__') and not v['pass']]
        print(f'  -> Fix: {fail_keys}')
    print('=' * 70)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Box MocoTrack Setup Verification (Phase 1)',
    )
    parser.add_argument(
        '--write-artifacts',
        action='store_true',
        help='Write STO + XML artifacts to shared/ (default: temp files cleaned up)',
    )
    args = parser.parse_args()

    log('=== Box MocoTrack Setup Verification ===')
    log(f'Model: {Path(MODEL_PATH).name}')
    log(f'Motion: {Path(MOTION_FILE).name}')
    log(f'Time window: [{T_START}, {T_END}] s')
    log(f'Box mass: {BOX_MASS_KG} kg  |  Grip point: {GRIP_POINT} m')
    log('')

    t0 = time.time()
    results = run_setup_checks(write_artifacts=args.write_artifacts)
    elapsed = time.time() - t0

    print_results(results)
    log(f'Setup check complete: {elapsed:.1f}s')

    return 0 if results.get('__overall__', False) else 1


if __name__ == '__main__':
    sys.exit(main())
