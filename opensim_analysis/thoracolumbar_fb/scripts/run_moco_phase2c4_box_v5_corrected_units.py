"""Phase 2.C.4 v5 — 단위 정정 재실행 (Corrected Units).

== 단위 정정 배경 (2026-04-29 CHEOL HOON님 발견) ==

  v1/v2/v3 오류:
    CONDITIONS = [('B_suit200', 200.0)]  → 200.0이 N·m로 직접 적용
    실슈트 24 N·m의 8.33배 초과 오류

  v5 정정:
    실제 SMA 슈트 spec: 수축력 200 N × 모멘트암 0.12 m = 24 N·m
    Phase 1a (run_moco_phase1a_suit.py) 동일 변환 적용:
      SUIT_FORCE_N × MOMENT_ARM = N·m

  참조:
    Phase 1a L20: SUIT_FORCE_N=200 → SUIT_TORQUE_PEAK = 24.0 N·m → ES 28% 감소 검증됨
    v5 B_suit200: 동일 24 N·m → Phase 1a와 정량 일치 기대

== v5 vs v3 차이 ==

  변경: CONDITIONS 단위 정정 + 5 conditions (v3는 4 conditions)
  동일: muscle set v2 (158 muscles), v11b motion, GRF (stoop_grf_v5),
         ModOpAddReserves(10.0), hand ExternalForce (98.1 N/hand), mesh=50, t=1.0-4.0s

== v5 Conditions ==

  B_suit0   :  0 N (수축력)  →  0.0 N·m
  B_suit50  : 50 N (수축력)  →  6.0 N·m
  B_suit100 :100 N (수축력)  → 12.0 N·m
  B_suit150 :150 N (수축력)  → 18.0 N·m
  B_suit200 :200 N (수축력)  → 24.0 N·m  ← Phase 1a L20과 동일 토크

Usage:
  python run_moco_phase2c4_box_v5_corrected_units.py              # all 5
  python run_moco_phase2c4_box_v5_corrected_units.py B_suit0      # single
  python run_moco_phase2c4_box_v5_corrected_units.py B_suit0 B_suit50  # multiple
"""
import os, sys, time
os.environ.setdefault('OPENSIM_USE_VISUALIZER', '0')
from pathlib import Path
import numpy as np
import opensim as osim

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts')
sys.path.insert(0, str(SCRIPT_DIR))
from muscle_set_v2 import MUSCLE_SET_V2

SRC_MODEL = (
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
    'MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim'
)
MOT          = '/data/stoop_motion/box_motion_v11b.mot'
GRF_STO_BASE = '/data/stoop_motion/stoop_grf_v5.sto'    # body weight only (75 kg)
OUT_ROOT     = Path('/data/opensim_results/phase2c4_box_v11b_v5_corrected_units')

# ── Timing ─────────────────────────────────────────────────────────────────
T_START, T_END = 1.0, 4.0
MESH           = 50
RESERVE_OPTF   = 10.0

# ── Physical constants ─────────────────────────────────────────────────────
BOX_MASS          = 20.0    # kg
GRAVITY           = 9.81    # m/s²
HAND_FORCE_EACH   = BOX_MASS * GRAVITY / 2.0   # 98.1 N per hand (upward)
GRASP_T           = 2.0     # s — grasp starts
RAMP_DUR          = 0.5     # s — ramp from 0 to full force

# ── 단위 정정 (2026-04-29) ──────────────────────────────────────────────────
# 실제 SMA 슈트 spec: 200 N 수축력 × 0.12 m 모멘트암 = 24 N·m 토크
# Phase 1a L20 (200 N → 24 N·m) 동일 변환 적용
# 200 N·m 직접 적용 X (실슈트 8.33× 초과, v1-v3 이전 오류 정정)
MOMENT_ARM = 0.12  # m — Phase 1a와 동일

SUIT_CONDITIONS_N = [0, 50, 100, 150, 200]  # 수축력 N
CONDITIONS = [
    (f'B_suit{N}', N * MOMENT_ARM)  # N → N·m 변환
    for N in SUIT_CONDITIONS_N
]
# 결과:
#   ('B_suit0',   0.0)  N·m
#   ('B_suit50',  6.0)  N·m
#   ('B_suit100', 12.0) N·m
#   ('B_suit150', 18.0) N·m
#   ('B_suit200', 24.0) N·m  ← Phase 1a L20과 동일

# ── Column definitions ─────────────────────────────────────────────────────
GRF_COLS = [
    'ground_force_R_vx', 'ground_force_R_vy', 'ground_force_R_vz',
    'ground_force_R_px', 'ground_force_R_py', 'ground_force_R_pz',
    'ground_torque_R_x', 'ground_torque_R_y', 'ground_torque_R_z',
    'ground_force_L_vx', 'ground_force_L_vy', 'ground_force_L_vz',
    'ground_force_L_px', 'ground_force_L_py', 'ground_force_L_pz',
    'ground_torque_L_x', 'ground_torque_L_y', 'ground_torque_L_z',
]
SUIT_COLS = [
    'thor_F_vx', 'thor_F_vy', 'thor_F_vz', 'thor_T_x', 'thor_T_y', 'thor_T_z',
    'thor_P_px', 'thor_P_py', 'thor_P_pz',
    'pel_F_vx',  'pel_F_vy',  'pel_F_vz',  'pel_T_x',  'pel_T_y',  'pel_T_z',
    'pel_P_px',  'pel_P_py',  'pel_P_pz',
]
HAND_COLS = [
    'hand_R_force_vx', 'hand_R_force_vy', 'hand_R_force_vz',
    'hand_R_force_px', 'hand_R_force_py', 'hand_R_force_pz',
    'hand_L_force_vx', 'hand_L_force_vy', 'hand_L_force_vz',
    'hand_L_force_px', 'hand_L_force_py', 'hand_L_force_pz',
]
ALL_COLS = GRF_COLS + SUIT_COLS + HAND_COLS


def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def alpha_box(t):
    """Suit assist ramp profile (same as v1/v2/v3)."""
    if t < 0.5:    return 0.0
    if t <= 2.0:   return (1.0 - np.cos(np.pi * (t - 0.5) / 1.5)) / 2.0
    if t <= 2.5:   return 1.0
    if t <= 4.0:   return (1.0 + np.cos(np.pi * (t - 2.5) / 1.5)) / 2.0
    return 0.0


def alpha_grasp(t):
    """Hand force ramp profile (same as v3)."""
    if t < GRASP_T:
        return 0.0
    elif t < GRASP_T + RAMP_DUR:
        return (1.0 - np.cos(np.pi * (t - GRASP_T) / RAMP_DUR)) / 2.0
    else:
        return 1.0


def prepare_model(out_path):
    """Trim model to MUSCLE_SET_V2 (158 muscles). Same as v3."""
    keep = set(MUSCLE_SET_V2)
    import xml.etree.ElementTree as ET
    tree = ET.parse(SRC_MODEL)
    root = tree.getroot()
    removed = kept_mus = kept_other = 0
    MUSCLE_TYPES = {
        'Millard2012EquilibriumMuscle', 'Thelen2003Muscle',
        'DeGrooteFregly2016Muscle', 'ActivationFiberLengthMuscle',
        'Muscle', 'SimpleMuscle', 'RigidTendonMuscle',
    }
    for fs in root.iter('ForceSet'):
        obj = fs.find('objects')
        if obj is None:
            continue
        for child in list(obj):
            name = child.get('name')
            if name is None:
                continue
            if child.tag in MUSCLE_TYPES or 'Muscle' in child.tag:
                if name in keep:
                    kept_mus += 1
                else:
                    obj.remove(child)
                    removed += 1
            else:
                kept_other += 1
    tree.write(str(out_path), encoding='utf-8', xml_declaration=True)
    log(f'Model v5: kept {kept_mus} muscles + {kept_other} forces, removed {removed}')
    return out_path


def prepare_reference(out_path):
    """Convert motion to radians + Savitzky-Golay smoothing. Same as v3."""
    from scipy.signal import savgol_filter
    tbl = osim.TimeSeriesTable(MOT)
    times  = np.array(list(tbl.getIndependentColumn()))
    labels = list(tbl.getColumnLabels())

    m = osim.Model(SRC_MODEL)
    m.initSystem()
    cs = m.getCoordinateSet()

    is_rot = []
    for L in labels:
        if cs.contains(L):
            is_rot.append(cs.get(L).getMotionType() == 1)
        else:
            is_rot.append(False)

    mask = (times >= T_START - 1e-9) & (times <= T_END + 1e-9)
    keep = np.where(mask)[0]
    n    = len(keep)

    data = np.zeros((len(times), len(labels)))
    for i in range(len(times)):
        row = tbl.getRowAtIndex(i)
        for j in range(len(labels)):
            v = row[j]
            if is_rot[j]:
                v = np.radians(v)
            data[i, j] = v

    ARM_COORDS = [
        'elbow_flexion_r', 'elbow_flexion_l',
        'shoulder_elv_r',  'shoulder_elv_l',
        'elv_angle_r',     'elv_angle_l',
        'shoulder_rot_r',  'shoulder_rot_l',
    ]
    SMOOTH_WIN = 51
    SMOOTH_ORD = 3
    dt = times[1] - times[0]
    for lab in ARM_COORDS:
        if lab in labels:
            idx = labels.index(lab)
            orig = data[:, idx]
            sm   = savgol_filter(orig, window_length=SMOOTH_WIN, polyorder=SMOOTH_ORD)
            vel_before = np.abs(np.diff(orig)).max() / dt
            vel_after  = np.abs(np.diff(sm)).max()  / dt
            data[:, idx] = sm
            log(f'  Smoothed {lab}: vel {vel_before:.1f} → {vel_after:.1f} rad/s')

    header = (
        f'box_v11b_moco_ref_smooth_v5\nversion=1\nnRows={n}\n'
        f'nColumns={1 + len(labels)}\ninDegrees=no\n\n'
        'Units are S.I. units.\n\nendheader\n'
        'time\t' + '\t'.join(labels) + '\n'
    )
    with open(out_path, 'w') as f:
        f.write(header)
        for i in keep:
            vals = [f'{times[i]:.6f}'] + [f'{data[i, j]:.6f}' for j in range(len(labels))]
            f.write('\t'.join(vals) + '\n')
    log(f'Reference: {n} frames  t=[{times[keep[0]]:.3f},{times[keep[-1]]:.3f}]')
    return out_path


def write_extloads_v5(out_mot, out_xml, suit_torque_nm):
    """Write combined external loads: foot GRF + suit (corrected N·m) + hand forces.

    단위 정정:
      suit_torque_nm 는 이미 N·m 단위 (N × MOMENT_ARM 변환 완료)
      B_suit200: 24.0 N·m (Phase 1a L20과 동일)

    GRF: body weight only (75 kg), stoop_grf_v5.sto
    Hand: 98.1 N upward per hand, ramp at t=2.0s (same as v3)
    """
    tbl     = osim.TimeSeriesTable(GRF_STO_BASE)
    times   = np.array(list(tbl.getIndependentColumn()))
    grf_lab = list(tbl.getColumnLabels())
    n       = tbl.getNumRows()

    # GRF
    grf = np.zeros((n, len(GRF_COLS)))
    for i in range(n):
        row = tbl.getRowAtIndex(i)
        for j, c in enumerate(GRF_COLS):
            if c in grf_lab:
                grf[i, j] = row[grf_lab.index(c)]

    # Suit torque
    suit   = np.zeros((n, len(SUIT_COLS)))
    i_thor = SUIT_COLS.index('thor_T_z')
    i_pel  = SUIT_COLS.index('pel_T_z')
    for i, t in enumerate(times):
        Tz = suit_torque_nm * alpha_box(float(t))
        suit[i, i_thor] = +Tz
        suit[i, i_pel]  = -Tz

    # Hand forces
    hand = np.zeros((n, len(HAND_COLS)))
    vy_R = HAND_COLS.index('hand_R_force_vy')
    vy_L = HAND_COLS.index('hand_L_force_vy')
    for i, t in enumerate(times):
        alpha = alpha_grasp(float(t))
        F     = HAND_FORCE_EACH * alpha
        hand[i, vy_R] = F
        hand[i, vy_L] = F

    # Write .mot
    data     = np.hstack([grf, suit, hand])
    mot_name = Path(out_mot).name
    header = (
        f'phase2c4_box_v11b_v5_extloads  suit={suit_torque_nm:.1f}Nm  hand={HAND_FORCE_EACH:.1f}N\n'
        f'version=1\nnRows={n}\nnColumns={1 + len(ALL_COLS)}\n'
        'inDegrees=no\n\n'
        'Units are S.I. units (second, meters, Newtons, ...)\n\nendheader\n'
        'time\t' + '\t'.join(ALL_COLS) + '\n'
    )
    with open(out_mot, 'w') as f:
        f.write(header)
        for i, t in enumerate(times):
            f.write('\t'.join([f'{t:.6f}'] + [f'{v:.6f}' for v in data[i]]) + '\n')

    # Write .xml
    xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
  <ExternalLoads name="phase2c4_box_v11b_v5">
    <objects>

      <!-- Foot GRF (body weight only, 75 kg) -->
      <ExternalForce name="grf_R">
        <isDisabled>false</isDisabled>
        <applied_to_body>calcn_r</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>ground_force_R_v</force_identifier>
        <point_identifier>ground_force_R_p</point_identifier>
        <torque_identifier>ground_torque_R_</torque_identifier>
        <data_source_name>{mot_name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="grf_L">
        <isDisabled>false</isDisabled>
        <applied_to_body>calcn_l</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>ground_force_L_v</force_identifier>
        <point_identifier>ground_force_L_p</point_identifier>
        <torque_identifier>ground_torque_L_</torque_identifier>
        <data_source_name>{mot_name}</data_source_name>
      </ExternalForce>

      <!-- Suit torque pair: thoracic extension / pelvis flexion -->
      <!-- 단위 정정: suit_torque_nm = N × 0.12m (Phase 1a와 동일) -->
      <ExternalForce name="suit_thoracic">
        <isDisabled>false</isDisabled>
        <applied_to_body>thoracic1</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>thor_F_v</force_identifier>
        <point_identifier>thor_P_p</point_identifier>
        <torque_identifier>thor_T_</torque_identifier>
        <data_source_name>{mot_name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="suit_pelvis">
        <isDisabled>false</isDisabled>
        <applied_to_body>pelvis</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>ground</point_expressed_in_body>
        <force_identifier>pel_F_v</force_identifier>
        <point_identifier>pel_P_p</point_identifier>
        <torque_identifier>pel_T_</torque_identifier>
        <data_source_name>{mot_name}</data_source_name>
      </ExternalForce>

      <!-- Hand forces: upward reaction to box weight (same as v3) -->
      <ExternalForce name="hand_R_box_force">
        <isDisabled>false</isDisabled>
        <applied_to_body>hand_R</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>hand_R</point_expressed_in_body>
        <force_identifier>hand_R_force_v</force_identifier>
        <point_identifier>hand_R_force_p</point_identifier>
        <data_source_name>{mot_name}</data_source_name>
      </ExternalForce>
      <ExternalForce name="hand_L_box_force">
        <isDisabled>false</isDisabled>
        <applied_to_body>hand_L</applied_to_body>
        <force_expressed_in_body>ground</force_expressed_in_body>
        <point_expressed_in_body>hand_L</point_expressed_in_body>
        <force_identifier>hand_L_force_v</force_identifier>
        <point_identifier>hand_L_force_p</point_identifier>
        <data_source_name>{mot_name}</data_source_name>
      </ExternalForce>

    </objects>
    <groups />
    <datafile>{mot_name}</datafile>
  </ExternalLoads>
</OpenSimDocument>
"""
    Path(out_xml).write_text(xml)

    # Sanity check
    grf_vy_R = GRF_COLS.index('ground_force_R_vy')
    grf_vy_L = GRF_COLS.index('ground_force_L_vy')
    t_grasp_idx = np.argmin(np.abs(times - 2.5))
    total_vy = (grf[t_grasp_idx, grf_vy_R] + grf[t_grasp_idx, grf_vy_L]
                + hand[t_grasp_idx, vy_R] + hand[t_grasp_idx, vy_L])
    body_box_weight = (75.0 + BOX_MASS) * GRAVITY
    log(f'  Sanity @t=2.5: total_Fy={total_vy:.1f} N  target={body_box_weight:.1f} N'
        f'  delta={total_vy - body_box_weight:.1f} N')
    log(f'  Suit torque applied: {suit_torque_nm:.1f} N·m (from {suit_torque_nm/MOMENT_ARM:.0f} N × {MOMENT_ARM} m)')
    return out_mot, out_xml


def run_condition(label, suit_torque_nm, model_path, ref_path):
    cond_dir = OUT_ROOT / label
    cond_dir.mkdir(parents=True, exist_ok=True)

    ext_mot  = cond_dir / 'ext_loads.mot'
    ext_xml  = cond_dir / 'ext_loads.xml'
    sol_path = cond_dir / 'solution.sto'

    log(f'--- Condition: {label}  suit={suit_torque_nm:.1f} N·m '
        f'(from {suit_torque_nm/MOMENT_ARM:.0f} N × {MOMENT_ARM} m) ---')
    write_extloads_v5(str(ext_mot), str(ext_xml), suit_torque_nm)

    log('Setting up MocoInverse...')
    inverse = osim.MocoInverse()
    inverse.setName(f'phase2c4_v5_{label}')

    model_proc = osim.ModelProcessor(str(model_path))
    model_proc.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    model_proc.append(osim.ModOpIgnoreTendonCompliance())
    model_proc.append(osim.ModOpIgnorePassiveFiberForcesDGF())
    model_proc.append(osim.ModOpAddExternalLoads(str(ext_xml)))
    model_proc.append(osim.ModOpAddReserves(RESERVE_OPTF))
    inverse.setModel(model_proc)

    inverse.setKinematics(osim.TableProcessor(str(ref_path)))
    inverse.set_initial_time(T_START)
    inverse.set_final_time(T_END)
    inverse.set_mesh_interval((T_END - T_START) / MESH)
    inverse.set_kinematics_allow_extra_columns(True)

    log(f'Solving... mesh={MESH}, t=[{T_START},{T_END}], suit={suit_torque_nm:.1f} N·m, '
        f'muscles=158, hand_force={HAND_FORCE_EACH:.1f} N/hand')
    t0  = time.time()
    sol = inverse.solve()
    t_el = time.time() - t0
    moco_sol = sol.getMocoSolution()
    success  = moco_sol.success()
    status   = moco_sol.getStatus()
    log(f'Solve done: {t_el:.1f}s  success={success}  status={status}')

    try:
        moco_sol.unseal()
    except Exception:
        pass
    moco_sol.write(str(sol_path))
    log(f'Saved: {sol_path}')

    # Reserve check
    log('Reserve check...')
    tbl    = osim.TimeSeriesTable(str(sol_path))
    labs   = list(tbl.getColumnLabels())
    nrows  = tbl.getNumRows()
    res_cols = [(i, L) for i, L in enumerate(labs) if 'reserve' in L.lower()]

    data = np.zeros((nrows, len(res_cols)))
    for i in range(nrows):
        row = tbl.getRowAtIndex(i)
        for j, (idx, _) in enumerate(res_cols):
            data[i, j] = row[idx] * RESERVE_OPTF

    max_abs = np.abs(data).max(axis=0)
    top8    = np.argsort(-max_abs)[:8]
    for j in top8:
        L     = res_cols[j][1]
        short = L.split('/')[-2] if '/' in L else L
        log(f'  Reserve {short}: max={max_abs[j]:.1f}')

    KEY_RESERVES = ['pelvis_tilt', 'pelvis_ty', 'pelvis_tx',
                    'hip_flexion_r', 'hip_flexion_l',
                    'hip_adduction_r', 'hip_adduction_l']
    log('  --- Key reserves ---')
    for nm in KEY_RESERVES:
        for j, (idx, L) in enumerate(res_cols):
            if nm in L:
                log(f'  {nm}: {max_abs[j]:.1f}')
                break

    return {
        'label':       label,
        'suit_n':      suit_torque_nm / MOMENT_ARM,
        'suit_nm':     suit_torque_nm,
        'success':     success,
        'status':      status,
        'wall_time_s': t_el,
        'sol_path':    str(sol_path),
    }


def main():
    if len(sys.argv) > 1:
        requested = set(sys.argv[1:])
        conds = [(lbl, nm) for lbl, nm in CONDITIONS if lbl in requested]
        if not conds:
            log(f'Unknown condition(s): {sys.argv[1:]}')
            log(f'Valid: {[c[0] for c in CONDITIONS]}')
            sys.exit(2)
    else:
        conds = CONDITIONS

    log('=== Phase 2.C.4 v5 — 단위 정정 재실행 ===')
    log(f'Model : {Path(SRC_MODEL).name}')
    log(f'Motion: {Path(MOT).name}')
    log(f'Muscle set v2: {len(MUSCLE_SET_V2)} muscles')
    log(f'Moment arm: {MOMENT_ARM} m (Phase 1a와 동일)')
    log(f'Conditions:')
    for lbl, nm in conds:
        log(f'  {lbl}: {nm/MOMENT_ARM:.0f} N → {nm:.1f} N·m')
    log(f'Mesh={MESH}, t=[{T_START},{T_END}], reserveOptF={RESERVE_OPTF}')
    log(f'Hand force: {HAND_FORCE_EACH:.1f} N per hand (ramp at t={GRASP_T}s)')
    log('Note: v1/v2/v3 오류 정정 — 200 N·m → 24 N·m (8.33× 감소)')

    shared_dir = OUT_ROOT / 'shared'
    shared_dir.mkdir(parents=True, exist_ok=True)
    model_path = shared_dir / 'phase2c4_v5_model.osim'
    ref_path   = shared_dir / 'states_reference.sto'

    log(f'Preparing shared model ({len(MUSCLE_SET_V2)} muscles)...')
    prepare_model(model_path)

    log('Preparing motion reference...')
    prepare_reference(ref_path)

    results = []
    t_total = time.time()
    for label, suit_nm in conds:
        try:
            r = run_condition(label, suit_nm, model_path, ref_path)
            results.append(r)
        except Exception as e:
            log(f'FATAL in {label}: {e}')
            import traceback; traceback.print_exc()
            results.append({
                'label': label, 'suit_n': suit_nm / MOMENT_ARM, 'suit_nm': suit_nm,
                'success': False, 'status': str(e),
                'wall_time_s': 0, 'sol_path': 'FAILED',
            })

        if results and not results[-1]['success']:
            log(f'STOPPED: {label} failed.')
            break

    log('')
    log('=== SUMMARY ===')
    log(f'{"Condition":<12} {"Force(N)":<10} {"Torque(Nm)":<12} {"Success":<10} {"Time(s)":<10} Status')
    for r in results:
        log(f'{r["label"]:<12} {r["suit_n"]:<10.0f} {r["suit_nm"]:<12.1f} '
            f'{str(r["success"]):<10} {r["wall_time_s"]:<10.1f} {r["status"]}')
    log(f'Total wall time: {time.time() - t_total:.1f}s')

    import json
    summary_path = OUT_ROOT / 'solve_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    log(f'Summary saved: {summary_path}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f'FATAL: {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)
