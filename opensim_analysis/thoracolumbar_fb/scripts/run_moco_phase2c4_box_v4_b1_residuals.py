"""Phase 2.C.4 v4-B1 — ModOpAddResiduals 분리 적용 (단계별 검증 B-1).

== 변경 사항 (v3 대비 정확히 1줄 → 2줄) ==

  변경 전 (v3):
      model_proc.append(osim.ModOpAddReserves(10.0))

  변경 후 (v4-B1):
      model_proc.append(osim.ModOpAddResiduals(300.0, 50.0, 1.0))
      model_proc.append(osim.ModOpAddReserves(1.0))

  절대 미적용 (B-3까지 유보):
      # osim.ModOpScaleActiveFiberForceCurveWidthDGF(1.5)

== 변경 의도 ==

  pelvis_ty   reserve v3: 3570 N  → 목표 < 500 N (가능하면 < 100 N)
  pelvis_tilt reserve v3: 269 N·m → 목표 부분 감소

  ModOpAddResiduals: pelvis 번역(300 N) + 회전(50 N·m) 전용 잔류력 추가
  ModOpAddReserves(1.0): 다른 관절 reserve scale 1.0 (v3 10.0에서 감소)

== Parameter 출처 ==

  Dembia CL et al. (2020). OpenSim Moco. PLoS Comput Biol 16(12).
  OpenSim exampleMocoInverse.py (공식 예제)
  Hicks JL et al. (2015). Is my model good enough? J Biomech Eng 137(2):020905.

== 3 시나리오 기준 ==

  시나리오 1 (명확한 개선):
    pelvis_ty  < 500 N + IPOPT Optimal + ES < 5%p 변화
    → B-2 진행 추천

  시나리오 2 (부분 개선):
    pelvis_ty  1500-500 N 또는 pelvis_tilt 변화 없음
    → 사용자 협의 필수

  시나리오 3 (새 issue):
    IPOPT 수렴 X 또는 inf_pr > 1e-2 또는 ES > 10%p
    → 추정 X, 즉시 진단 + 사용자 협의

== B-1 실행 ==

  1 condition만 실행: B_noload (suit=0 N·m)
  자동 다음 단계 X — 사용자 명시 승인 후 B-2 진행

  모든 다른 설정은 v3와 동일:
  - Motion: box_motion_v11b.mot (변경 없음)
  - GRF: stoop_grf_v5.sto (변경 없음)
  - Hand ExternalForce: 98.1 N/hand (변경 없음)
  - Muscle set: v2 (158 muscles, 변경 없음)
  - Mesh: 50 (변경 없음)
  - Time: t=1.0-4.0s (변경 없음)

Usage:
  python run_moco_phase2c4_box_v4_b1_residuals.py              # B_noload만 (기본)
  python run_moco_phase2c4_box_v4_b1_residuals.py B_noload     # 명시적 single
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
OUT_ROOT     = Path('/data/opensim_results/phase2c4_box_v11b_v4_b1')

# ── Timing ─────────────────────────────────────────────────────────────────
T_START, T_END = 1.0, 4.0
MESH           = 50

# ── ⭐ B-1 핵심 변경 (v3 대비) ─────────────────────────────────────────────
# v3: RESERVE_OPTF = 10.0  →  model_proc.append(osim.ModOpAddReserves(10.0))
# v4-B1:
RESIDUAL_FORCE_NM  = 300.0   # pelvis 번역 residual 한계 [N]
RESIDUAL_MOMENT_NM = 50.0    # pelvis 회전 residual 한계 [N·m]
RESIDUAL_SCALE     = 1.0     # residual scale
RESERVE_OPTF       = 1.0     # 다른 관절 reserve scale (v3 10.0 → 1.0)

# ── Physical constants (v3와 동일) ──────────────────────────────────────────
BOX_MASS          = 20.0    # kg
GRAVITY           = 9.81    # m/s²
HAND_FORCE_EACH   = BOX_MASS * GRAVITY / 2.0   # 98.1 N per hand (upward)
GRASP_T           = 2.0     # s — grasp starts
RAMP_DUR          = 0.5     # s — ramp from 0 to full force

# ── Conditions: B-1에서는 B_noload만 실행 ──────────────────────────────────
CONDITIONS = [
    ('B_noload',  0.0),
    # ('B_suit50',  50.0),   # B-2 이후 사용자 승인 후 추가
    # ('B_suit100', 100.0),
    # ('B_suit200', 200.0),
]

# ── Column definitions (v3와 동일) ─────────────────────────────────────────
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

# ── ES muscle list (peak 분석용) ────────────────────────────────────────────
ES_MUSCLES = [
    'IL_R10_r', 'IL_R10_l', 'IL_R11_r', 'IL_R11_l',
    'IL_R12_r', 'IL_R12_l', 'IL_L1_r',  'IL_L1_l',
    'IL_L2_r',  'IL_L2_l',  'IL_L3_r',  'IL_L3_l',
    'IL_L4_r',  'IL_L4_l',  'LTpL_L5_r','LTpL_L5_l',
    'LT_T10_r', 'LT_T10_l', 'LT_T11_r', 'LT_T11_l',
    'LT_T12_r', 'LT_T12_l', 'LT_L1_r',  'LT_L1_l',
    'LT_L2_r',  'LT_L2_l',  'LT_L3_r',  'LT_L3_l',
    'LT_L4_r',  'LT_L4_l',  'LT_L5_r',  'LT_L5_l',
]


def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def alpha_box(t):
    """Suit assist ramp profile (v3와 동일)."""
    if t < 0.5:    return 0.0
    if t <= 2.0:   return (1.0 - np.cos(np.pi * (t - 0.5) / 1.5)) / 2.0
    if t <= 2.5:   return 1.0
    if t <= 4.0:   return (1.0 + np.cos(np.pi * (t - 2.5) / 1.5)) / 2.0
    return 0.0


def alpha_grasp(t):
    """Hand force ramp profile (v3와 동일)."""
    if t < GRASP_T:
        return 0.0
    elif t < GRASP_T + RAMP_DUR:
        return (1.0 - np.cos(np.pi * (t - GRASP_T) / RAMP_DUR)) / 2.0
    else:
        return 1.0


def prepare_model(out_path):
    """Trim model to MUSCLE_SET_V2 (158 muscles). v3와 동일."""
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
    log(f'Model v4-B1: kept {kept_mus} muscles + {kept_other} forces, removed {removed}')
    log(f'  Muscle set v2: {len(MUSCLE_SET_V2)} requested, {kept_mus} found in model')
    return out_path


def prepare_reference(out_path):
    """Convert motion to radians + Savitzky-Golay smoothing. v3와 동일."""
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
        f'box_v11b_moco_ref_smooth_v4b1\nversion=1\nnRows={n}\n'
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


def write_extloads_v4b1(out_mot, out_xml, suit_torque_nm):
    """Write combined external loads: foot GRF + suit + hand forces. v3와 동일."""
    tbl     = osim.TimeSeriesTable(GRF_STO_BASE)
    times   = np.array(list(tbl.getIndependentColumn()))
    grf_lab = list(tbl.getColumnLabels())
    n       = tbl.getNumRows()

    grf = np.zeros((n, len(GRF_COLS)))
    for i in range(n):
        row = tbl.getRowAtIndex(i)
        for j, c in enumerate(GRF_COLS):
            if c in grf_lab:
                grf[i, j] = row[grf_lab.index(c)]

    suit   = np.zeros((n, len(SUIT_COLS)))
    i_thor = SUIT_COLS.index('thor_T_z')
    i_pel  = SUIT_COLS.index('pel_T_z')
    for i, t in enumerate(times):
        Tz = suit_torque_nm * alpha_box(float(t))
        suit[i, i_thor] = +Tz
        suit[i, i_pel]  = -Tz

    hand   = np.zeros((n, len(HAND_COLS)))
    vy_R   = HAND_COLS.index('hand_R_force_vy')
    vy_L   = HAND_COLS.index('hand_L_force_vy')
    for i, t in enumerate(times):
        alpha = alpha_grasp(float(t))
        F     = HAND_FORCE_EACH * alpha
        hand[i, vy_R] = F
        hand[i, vy_L] = F

    data     = np.hstack([grf, suit, hand])
    mot_name = Path(out_mot).name
    header = (
        f'phase2c4_box_v11b_v4b1_extloads  suit={suit_torque_nm}Nm  hand={HAND_FORCE_EACH:.1f}N\n'
        f'version=1\nnRows={n}\nnColumns={1 + len(ALL_COLS)}\n'
        'inDegrees=no\n\n'
        'Units are S.I. units (second, meters, Newtons, ...)\n\nendheader\n'
        'time\t' + '\t'.join(ALL_COLS) + '\n'
    )
    with open(out_mot, 'w') as f:
        f.write(header)
        for i, t in enumerate(times):
            f.write('\t'.join([f'{t:.6f}'] + [f'{v:.6f}' for v in data[i]]) + '\n')

    xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
  <ExternalLoads name="phase2c4_box_v11b_v4b1">
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

      <!-- Suit torque pair -->
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

      <!-- Hand forces: upward reaction to box weight -->
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
    log(f'Sanity check @ t=2.5: total_Fy={total_vy:.1f} N  body+box weight={body_box_weight:.1f} N'
        f'  delta={total_vy - body_box_weight:.1f} N')
    log(f'Hand force @ t=2.5: {hand[t_grasp_idx, vy_R]:.1f} N each hand')
    log(f'External loads written: {Path(out_mot).name}')
    return out_mot, out_xml


def run_condition(label, suit_torque_nm, model_path, ref_path):
    cond_dir = OUT_ROOT / label
    cond_dir.mkdir(parents=True, exist_ok=True)

    ext_mot  = cond_dir / 'ext_loads.mot'
    ext_xml  = cond_dir / 'ext_loads.xml'
    sol_path = cond_dir / 'solution.sto'

    log(f'--- Condition: {label}  suit={suit_torque_nm} N·m ---')
    write_extloads_v4b1(str(ext_mot), str(ext_xml), suit_torque_nm)

    log('Setting up MocoInverse...')
    inverse = osim.MocoInverse()
    inverse.setName(f'phase2c4_v4b1_{label}')

    model_proc = osim.ModelProcessor(str(model_path))
    model_proc.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    model_proc.append(osim.ModOpIgnoreTendonCompliance())
    model_proc.append(osim.ModOpIgnorePassiveFiberForcesDGF())
    model_proc.append(osim.ModOpAddExternalLoads(str(ext_xml)))

    # ⭐ B-1 핵심 변경 (v3 대비 정확히 이 부분만 다름)
    # v3: model_proc.append(osim.ModOpAddReserves(10.0))
    # v4-B1:
    model_proc.append(osim.ModOpAddResiduals(RESIDUAL_FORCE_NM, RESIDUAL_MOMENT_NM, RESIDUAL_SCALE))
    model_proc.append(osim.ModOpAddReserves(RESERVE_OPTF))

    inverse.setModel(model_proc)
    inverse.setKinematics(osim.TableProcessor(str(ref_path)))
    inverse.set_initial_time(T_START)
    inverse.set_final_time(T_END)
    inverse.set_mesh_interval((T_END - T_START) / MESH)
    inverse.set_kinematics_allow_extra_columns(True)

    log(f'Solving... (mesh={MESH}, t=[{T_START},{T_END}], suit={suit_torque_nm} N·m, '
        f'muscles=158, hand_force={HAND_FORCE_EACH:.1f} N/hand)')
    log(f'  ModOpAddResiduals: force={RESIDUAL_FORCE_NM} N, moment={RESIDUAL_MOMENT_NM} N·m, '
        f'scale={RESIDUAL_SCALE}')
    log(f'  ModOpAddReserves: scale={RESERVE_OPTF} (v3: 10.0)')

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

    # ── Reserve 분석 ──────────────────────────────────────────────────────────
    log('=== Reserve Analysis (v4-B1) ===')
    tbl    = osim.TimeSeriesTable(str(sol_path))
    labs   = list(tbl.getColumnLabels())
    nrows  = tbl.getNumRows()

    # Residual columns (ModOpAddResiduals 추가분) — scale=1.0 (no re-scaling)
    res_cols    = [(i, L) for i, L in enumerate(labs) if 'reserve' in L.lower()]
    resid_cols  = [(i, L) for i, L in enumerate(labs) if 'residual' in L.lower()]

    log(f'  Reserve columns: {len(res_cols)}')
    log(f'  Residual columns: {len(resid_cols)}')

    # Reserve data (scale=RESERVE_OPTF)
    if res_cols:
        data_res = np.zeros((nrows, len(res_cols)))
        for i in range(nrows):
            row = tbl.getRowAtIndex(i)
            for j, (idx, _) in enumerate(res_cols):
                data_res[i, j] = row[idx] * RESERVE_OPTF
        max_res = np.abs(data_res).max(axis=0)
        order   = np.argsort(-max_res)
        log('  Top Reserve values (scaled):')
        for j in order[:12]:
            L = res_cols[j][1]
            print(f'    {L}: max={max_res[j]:.1f}', flush=True)

    # Residual data (scale=1.0 — they are already in SI units)
    if resid_cols:
        data_rid = np.zeros((nrows, len(resid_cols)))
        for i in range(nrows):
            row = tbl.getRowAtIndex(i)
            for j, (idx, _) in enumerate(resid_cols):
                data_rid[i, j] = row[idx]  # no extra scaling
        max_rid = np.abs(data_rid).max(axis=0)
        order_r = np.argsort(-max_rid)
        log('  Residual values:')
        for j in order_r:
            L = resid_cols[j][1]
            print(f'    {L}: max={max_rid[j]:.1f}', flush=True)

    # Key reserve comparison (B-1 핵심 검증)
    KEY = {
        'pelvis_ty':      ('N',   3570.2),   # v3 baseline
        'pelvis_tilt':    ('N·m', 269.3),    # v3 baseline
        'pelvis_tx':      ('N',   90.1),
        'hip_flexion_r':  ('N·m', 42.2),
        'hip_flexion_l':  ('N·m', 42.2),
        'hip_adduction_r':('N·m', 42.0),
        'hip_adduction_l':('N·m', 42.0),
    }
    log('  === Key Reserve Comparison v3 → v4-B1 ===')
    log(f'  {"Coord":<20} {"Unit":<6} {"v3 baseline":>12} {"v4-B1":>10} {"delta":>8}')
    for nm, (unit, v3_val) in KEY.items():
        v4_val = None
        # Check reserves
        for j, (idx, L) in enumerate(res_cols):
            if nm in L:
                v4_val = max_res[j]
                break
        # Check residuals
        if v4_val is None and resid_cols:
            for j, (idx, L) in enumerate(resid_cols):
                if nm in L:
                    v4_val = max_rid[j]
                    break
        if v4_val is not None:
            delta = v4_val - v3_val
            pct   = delta / v3_val * 100 if v3_val != 0 else 0
            log(f'  {nm:<20} {unit:<6} {v3_val:>12.1f} {v4_val:>10.1f} {delta:>+8.1f} ({pct:+.0f}%)')
        else:
            log(f'  {nm:<20} {unit:<6} {v3_val:>12.1f} {"N/A":>10}')

    return {
        'label':       label,
        'suit_nm':     suit_torque_nm,
        'success':     success,
        'status':      status,
        'wall_time_s': t_el,
        'sol_path':    str(sol_path),
    }


def analyze_es_activation(sol_path, label):
    """ES peak activation 분석 (v3 비교용)."""
    log(f'=== ES Activation Analysis: {label} ===')

    # v3 B_noload reference values from known results
    V3_ES = {
        'Eccentric':  {'peak': 100.0, 'phase': (1.0, 2.0)},
        'Grasp':      {'peak': 99.8,  'phase': (2.0, 2.5)},
        'Concentric': {'peak': 100.0, 'phase': (2.5, 4.0)},
    }

    tbl   = osim.TimeSeriesTable(sol_path)
    labs  = list(tbl.getColumnLabels())
    times = np.array(list(tbl.getIndependentColumn()))
    nrows = tbl.getNumRows()

    PHASES = {
        'Eccentric':  (1.0, 2.0),
        'Grasp':      (2.0, 2.5),
        'Concentric': (2.5, 4.0),
    }

    # Find ES columns
    es_cols = {}
    for L in labs:
        for mus in ES_MUSCLES:
            if mus in L and ('activation' in L or 'excitation' in L):
                es_cols[mus] = labs.index(L)
                break

    if not es_cols:
        # Try generic ES pattern
        for L in labs:
            if any(pat in L for pat in ['IL_R', 'IL_L', 'LTpL', 'LT_T', 'LT_L']):
                if 'activation' in L or 'excitation' in L:
                    short = L.split('/')[-2] if '/' in L else L
                    es_cols[short] = labs.index(L)

    log(f'  ES columns found: {len(es_cols)}')

    if not es_cols:
        log('  WARNING: No ES columns found in solution. Check column names.')
        all_act = [L for L in labs if 'activation' in L.lower()]
        log(f'  Available activation columns (first 10): {all_act[:10]}')
        return

    # Extract activation data
    data = np.zeros((nrows, len(es_cols)))
    for i in range(nrows):
        row = tbl.getRowAtIndex(i)
        for j, (_, idx) in enumerate(es_cols.items()):
            data[i, j] = row[idx]

    log(f'  {"Phase":<12} {"v3 IL_R10":>12} {"v4-B1 peak":>12} {"delta":>8} {"status":>8}')
    for phase, (t0, t1) in PHASES.items():
        mask  = (times >= t0) & (times <= t1)
        if mask.sum() == 0:
            log(f'  {phase:<12}  no data in [{t0},{t1}]')
            continue
        phase_data = data[mask, :]
        peak_v4    = phase_data.max() * 100.0
        mean_v4    = phase_data.mean() * 100.0
        v3_peak    = V3_ES.get(phase, {}).get('peak', float('nan'))
        delta      = peak_v4 - v3_peak
        ok         = 'OK' if abs(delta) < 5.0 else 'WARN'
        log(f'  {phase:<12} {v3_peak:>12.1f}% {peak_v4:>11.1f}% {delta:>+7.1f}%p {ok:>8}')

    # IL_R10_r specific (sentinel muscle)
    il_r10_key = next((k for k in es_cols if 'IL_R10_r' in k), None)
    if il_r10_key:
        idx = list(es_cols.keys()).index(il_r10_key)
        log('  --- IL_R10_r (sentinel) ---')
        for phase, (t0, t1) in PHASES.items():
            mask = (times >= t0) & (times <= t1)
            if mask.sum() > 0:
                peak = data[mask, idx].max() * 100.0
                log(f'    {phase:<12}: {peak:.1f}%')


def main():
    # B-1: B_noload만 실행 (명시적 확인)
    if len(sys.argv) > 1:
        requested = set(sys.argv[1:])
        conds = [(lbl, nm) for lbl, nm in CONDITIONS if lbl in requested]
        if not conds:
            log(f'Unknown or not-enabled condition(s): {sys.argv[1:]}')
            log(f'v4-B1 available: {[c[0] for c in CONDITIONS]}')
            sys.exit(2)
    else:
        conds = CONDITIONS   # B_noload만 (조건 1개)

    log('=== Phase 2.C.4 v4-B1 — ModOpAddResiduals 분리 적용 ===')
    log(f'  Model : {Path(SRC_MODEL).name}')
    log(f'  Motion: {Path(MOT).name}')
    log(f'  GRF   : {Path(GRF_STO_BASE).name}')
    log(f'  Conditions (B-1 제한): {[c[0] for c in conds]}')
    log(f'  Mesh={MESH}, t=[{T_START},{T_END}]')
    log(f'')
    log(f'  ⭐ KEY CHANGE (v3 → v4-B1):')
    log(f'    BEFORE: ModOpAddReserves(10.0)')
    log(f'    AFTER : ModOpAddResiduals({RESIDUAL_FORCE_NM}, {RESIDUAL_MOMENT_NM}, {RESIDUAL_SCALE})')
    log(f'            ModOpAddReserves({RESERVE_OPTF})')
    log(f'')
    log(f'  TARGET: pelvis_ty 3570 N → <500 N')
    log(f'          pelvis_tilt 269 N·m → partial reduction')

    shared_dir = OUT_ROOT / 'shared'
    shared_dir.mkdir(parents=True, exist_ok=True)
    model_path = shared_dir / 'phase2c4_v4b1_model.osim'
    ref_path   = shared_dir / 'states_reference.sto'

    log(f'Preparing shared model ({len(MUSCLE_SET_V2)} muscles)...')
    prepare_model(model_path)

    log('Preparing motion reference (degrees → radians + smoothing)...')
    prepare_reference(ref_path)

    results  = []
    t_total  = time.time()

    for label, suit_nm in conds:
        try:
            r = run_condition(label, suit_nm, model_path, ref_path)
            results.append(r)

            # ES activation check
            if r['success'] and Path(r['sol_path']).exists():
                analyze_es_activation(r['sol_path'], label)

        except Exception as e:
            log(f'FATAL in {label}: {e}')
            import traceback; traceback.print_exc()
            results.append({
                'label': label, 'suit_nm': suit_nm,
                'success': False, 'status': str(e),
                'wall_time_s': 0, 'sol_path': 'FAILED',
            })

        # B-1 원칙: 1 condition 후 즉시 중단 + 보고
        if results:
            last = results[-1]
            log(f'')
            log(f'=== B-1 RESULT (보고용) ===')
            log(f'  Condition: {last["label"]}')
            log(f'  Success  : {last["success"]}')
            log(f'  Status   : {last["status"]}')
            log(f'  Wall time: {last["wall_time_s"]:.1f} s')
            log(f'')
            log(f'  ⚠️ B-1 단독 결과 보고 완료. 자동 다음 단계 X.')
            log(f'  ⚠️ 사용자 명시 승인 후 B-2 진행.')
            break   # 명시적 1 condition 후 종료

    log(f'Total wall time: {time.time() - t_total:.1f}s')

    import json
    summary_path = OUT_ROOT / 'solve_summary_b1.json'
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    log(f'Summary saved: {summary_path}')

    # 시나리오 판정 기준 출력
    if results:
        r = results[0]
        log('')
        log('=== 시나리오 판정 기준 (사용자 확인용) ===')
        log('  시나리오 1 (명확한 개선): pelvis_ty < 500 N + Optimal + ES < 5%p')
        log('  시나리오 2 (부분 개선) : pelvis_ty 500-1500 N 또는 moment 무변화')
        log('  시나리오 3 (새 issue) : IPOPT 수렴 X 또는 inf_pr > 1e-2 또는 ES > 10%p')
        if r['success']:
            log(f'  → IPOPT: {r["status"]}  (Optimal = 시나리오 1/2 판단으로 진입)')
        else:
            log(f'  → IPOPT FAILED: {r["status"]}  (시나리오 3 진입 필요)')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f'FATAL: {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)
