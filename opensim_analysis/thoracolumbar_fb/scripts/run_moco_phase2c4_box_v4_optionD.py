"""Phase 2.C.4 v4 — 옵션 D: API 정정 (ModOpAddResiduals 인수 순서 교환).

== 옵션 D 변경 사항 (B-1 대비) ==

  변경 전 (B-1):
      ModOpAddResiduals(300.0, 50.0, 1.0)  # B-1: force=300N, moment=50 N·m (의도 역전)

  변경 후 (옵션 D):
      ModOpAddResiduals(50.0, 300.0, 1.0)  # D: force=50N, moment=300 N·m (의도 정정)

  API signature: ModOpAddResiduals(rotational_optimal_force,
                                   translational_optimal_force,
                                   scale)
  → arg1=rotational(moment), arg2=translational(force), arg3=scale
  → 따라서: D에서는 rot=50 N·m, trans=300 N (보고서 spec 의도 반영)

  GRF: stoop_grf_v5.sto (이미 상수, t=4.0 spike 없음 — D.1 진단 확인)
       GRF 수정 불필요 (v5는 전 구간 735.75 N 상수, spike X)

== D.1 진단 결과 요약 ==

  - stoop_grf_v5.sto: 전 구간 735.75 N 상수. t=4.0 spike 없음.
  - B-1 inf_pr=3520: GRF 문제 아님. Motion v11b의 dynamic residual (수렴 실패).
  - B-1 solution.sto: 없음 (Maximum iterations exceeded).
  - 근본 원인: 75 kg body GRF(735.75 N) + 박스 (v2=196 N 통합) vs
               motion v11b이 요구하는 동역학 — residual 3520 N 필요.
  - 옵션 D는 trans residual을 300 N (vs B-1 300 N) 유지하면서
    rotational을 50 N·m로 정정하여 pelvis tilt residual 개선 시도.

== 자가 검증 기준 (D.4) ==

  PASS 기준:
    pelvis_ty  residual < 100 N (사용자 기준)
    IPOPT Optimal or Acceptable
    inf_pr final < 1e-4

  FAIL (시나리오 C):
    inf_pr 고착 (변화 < 10% over 100 iterations)
    solution.sto 미생성
    또 새 발견 (예상 못한 결과)

Usage:
  python run_moco_phase2c4_box_v4_optionD.py
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
GRF_STO_BASE = '/data/stoop_motion/stoop_grf_v5.sto'    # 상수 735.75 N, spike 없음 (D.1 확인)
OUT_ROOT     = Path('/data/opensim_results/phase2c4_box_v11b_v4_optionD')

# ── Timing ─────────────────────────────────────────────────────────────────
T_START, T_END = 1.0, 4.0
MESH           = 50

# ── ⭐ 옵션 D 핵심 변경 (B-1 대비 API 인수 순서 정정) ─────────────────────
# ModOpAddResiduals(rotational_optimal_force, translational_optimal_force, scale)
#   B-1 (오류): ModOpAddResiduals(300.0, 50.0, 1.0)  → rot=300, trans=50 (역전)
#   옵션 D (정정): ModOpAddResiduals(50.0, 300.0, 1.0) → rot=50, trans=300 (의도)
RESIDUAL_ROT_NM    = 50.0    # rotational residual (N·m) — pelvis 회전
RESIDUAL_TRANS_N   = 300.0   # translational residual (N) — pelvis 번역
RESIDUAL_SCALE     = 1.0
RESERVE_OPTF       = 1.0     # 다른 관절 reserve scale

# ── Physical constants (v3/B-1과 동일) ──────────────────────────────────────
BOX_MASS          = 20.0    # kg
GRAVITY           = 9.81    # m/s²
HAND_FORCE_EACH   = BOX_MASS * GRAVITY / 2.0   # 98.1 N per hand
BODY_MASS         = 75.0    # kg (GRF = 75 * 9.81 = 735.75 N)
GRASP_T           = 2.0     # s
RAMP_DUR          = 0.5     # s

# ── Conditions: 옵션 D는 B_noload만 실행 ──────────────────────────────────
CONDITIONS = [
    ('B_noload', 0.0),
]

# ── Column definitions (v3/B-1과 동일) ─────────────────────────────────────
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

# ── ES muscle list ─────────────────────────────────────────────────────────
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
    """Suit assist ramp profile."""
    if t < 0.5:    return 0.0
    if t <= 2.0:   return (1.0 - np.cos(np.pi * (t - 0.5) / 1.5)) / 2.0
    if t <= 2.5:   return 1.0
    if t <= 4.0:   return (1.0 + np.cos(np.pi * (t - 2.5) / 1.5)) / 2.0
    return 0.0


def alpha_grasp(t):
    """Hand force ramp profile."""
    if t < GRASP_T:
        return 0.0
    elif t < GRASP_T + RAMP_DUR:
        return (1.0 - np.cos(np.pi * (t - GRASP_T) / RAMP_DUR)) / 2.0
    else:
        return 1.0


def prepare_model(out_path):
    """Trim model to MUSCLE_SET_V2 (158 muscles)."""
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
    log(f'Model optionD: kept {kept_mus} muscles + {kept_other} forces, removed {removed}')
    return out_path


def prepare_reference(out_path):
    """Convert motion to radians + smoothing."""
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
            log(f'  Smoothed {lab}: vel {vel_before:.1f} -> {vel_after:.1f} rad/s')

    header = (
        f'box_v11b_moco_ref_smooth_optionD\nversion=1\nnRows={n}\n'
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


def write_extloads(out_mot, out_xml, suit_torque_nm):
    """Write combined external loads."""
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
        f'phase2c4_box_v11b_v4_optionD  suit={suit_torque_nm}Nm  hand={HAND_FORCE_EACH:.1f}N\n'
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
  <ExternalLoads name="phase2c4_box_v11b_v4optionD">
    <objects>

      <!-- Foot GRF (body weight only, 75 kg = 735.75 N total) -->
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
    body_box_weight = (BODY_MASS + BOX_MASS) * GRAVITY
    log(f'Sanity check @ t=2.5: total_Fy={total_vy:.1f} N  body+box weight={body_box_weight:.1f} N'
        f'  delta={total_vy - body_box_weight:.1f} N')
    log(f'GRF @ t=1.0: {grf[np.argmin(np.abs(times-1.0)), grf_vy_R]:.2f} N/foot (body only)')
    log(f'GRF @ t=4.0: {grf[np.argmin(np.abs(times-4.0)), grf_vy_R]:.2f} N/foot (constant)')
    log(f'Hand force @ t=2.5: {hand[t_grasp_idx, vy_R]:.1f} N each hand')
    log(f'External loads written: {Path(out_mot).name}')
    return out_mot, out_xml


def run_condition(label, suit_torque_nm, model_path, ref_path):
    cond_dir = OUT_ROOT / label
    cond_dir.mkdir(parents=True, exist_ok=True)

    ext_mot  = cond_dir / 'ext_loads.mot'
    ext_xml  = cond_dir / 'ext_loads.xml'
    sol_path = cond_dir / 'solution.sto'

    log(f'--- Condition: {label}  suit={suit_torque_nm} N.m ---')
    write_extloads(str(ext_mot), str(ext_xml), suit_torque_nm)

    log('Setting up MocoInverse...')
    inverse = osim.MocoInverse()
    inverse.setName(f'phase2c4_v4optionD_{label}')

    model_proc = osim.ModelProcessor(str(model_path))
    model_proc.append(osim.ModOpReplaceMusclesWithDeGrooteFregly2016())
    model_proc.append(osim.ModOpIgnoreTendonCompliance())
    model_proc.append(osim.ModOpIgnorePassiveFiberForcesDGF())
    model_proc.append(osim.ModOpAddExternalLoads(str(ext_xml)))

    # ⭐ 옵션 D 핵심 변경:
    # B-1 (오류): ModOpAddResiduals(300.0, 50.0, 1.0) → rot=300 N·m, trans=50 N (역전)
    # 옵션 D (정정): ModOpAddResiduals(50.0, 300.0, 1.0) → rot=50 N·m, trans=300 N
    model_proc.append(osim.ModOpAddResiduals(RESIDUAL_ROT_NM, RESIDUAL_TRANS_N, RESIDUAL_SCALE))
    model_proc.append(osim.ModOpAddReserves(RESERVE_OPTF))

    inverse.setModel(model_proc)
    inverse.setKinematics(osim.TableProcessor(str(ref_path)))
    inverse.set_initial_time(T_START)
    inverse.set_final_time(T_END)
    inverse.set_mesh_interval((T_END - T_START) / MESH)
    inverse.set_kinematics_allow_extra_columns(True)

    log(f'Solving... (mesh={MESH}, t=[{T_START},{T_END}], suit={suit_torque_nm} N.m, '
        f'muscles=158, hand_force={HAND_FORCE_EACH:.1f} N/hand)')
    log(f'  ModOpAddResiduals(rot={RESIDUAL_ROT_NM} N.m, trans={RESIDUAL_TRANS_N} N, '
        f'scale={RESIDUAL_SCALE})')
    log(f'  ModOpAddReserves: scale={RESERVE_OPTF}')
    log(f'  [vs B-1] B-1 had rot=300 N.m, trans=50 N (reversed). D has rot=50, trans=300 (corrected).')

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

    return {
        'label':       label,
        'suit_nm':     suit_torque_nm,
        'success':     success,
        'status':      status,
        'wall_time_s': t_el,
        'sol_path':    str(sol_path),
    }


def analyze_reserves(sol_path):
    """Reserve 분석 — 옵션 D 자가 검증 핵심."""
    log('=== Reserve Analysis (옵션 D) ===')
    tbl   = osim.TimeSeriesTable(str(sol_path))
    labs  = list(tbl.getColumnLabels())
    nrows = tbl.getNumRows()

    res_cols   = [(i, L) for i, L in enumerate(labs) if 'reserve' in L.lower()]
    resid_cols = [(i, L) for i, L in enumerate(labs) if 'residual' in L.lower()]

    log(f'  Reserve columns: {len(res_cols)}')
    log(f'  Residual columns: {len(resid_cols)}')

    res_max = {}
    if res_cols:
        data_res = np.zeros((nrows, len(res_cols)))
        for i in range(nrows):
            row = tbl.getRowAtIndex(i)
            for j, (idx, _) in enumerate(res_cols):
                data_res[i, j] = row[idx] * RESERVE_OPTF
        max_res = np.abs(data_res).max(axis=0)
        order   = np.argsort(-max_res)
        log('  Top Reserve values (scaled, top 15):')
        for j in order[:15]:
            L = res_cols[j][1]
            res_max[L] = max_res[j]
            print(f'    {L}: max={max_res[j]:.1f}', flush=True)

    rid_max = {}
    if resid_cols:
        data_rid = np.zeros((nrows, len(resid_cols)))
        for i in range(nrows):
            row = tbl.getRowAtIndex(i)
            for j, (idx, _) in enumerate(resid_cols):
                data_rid[i, j] = row[idx]
        max_rid = np.abs(data_rid).max(axis=0)
        order_r = np.argsort(-max_rid)
        log('  Residual values (all):')
        for j in order_r:
            L = resid_cols[j][1]
            rid_max[L] = max_rid[j]
            print(f'    {L}: max={max_rid[j]:.1f}', flush=True)

    # Key comparison: v3 baseline vs 옵션 D
    KEY = {
        'pelvis_ty':       ('N',   3570.2),
        'pelvis_tilt':     ('N.m', 269.3),
        'pelvis_tx':       ('N',   90.1),
        'hip_flexion_r':   ('N.m', 42.2),
        'hip_flexion_l':   ('N.m', 42.2),
        'knee_angle_r':    ('N.m', 2.6),
        'ankle_angle_r':   ('N.m', 0.4),
    }
    log('  === Key Reserve Comparison: v3 baseline vs B-1 (failed) vs 옵션 D ===')
    log(f'  {"Coord":<22} {"Unit":<6} {"v3 baseline":>12} {"옵션D":>10} {"delta":>8} {"목표":>8}')

    all_max = {**res_max, **rid_max}
    for nm, (unit, v3_val) in KEY.items():
        d_val = None
        for L, v in all_max.items():
            if nm in L:
                d_val = v
                break
        if d_val is not None:
            delta = d_val - v3_val
            pct   = delta / v3_val * 100 if v3_val != 0 else 0
            # 목표 기준
            if 'pelvis_ty' in nm:
                goal = '<100 N (사용자기준)'
            elif 'pelvis_tilt' in nm:
                goal = '유의미 감소'
            elif 'pelvis_tx' in nm:
                goal = '<50 N'
            else:
                goal = 'reference'
            log(f'  {nm:<22} {unit:<6} {v3_val:>12.1f} {d_val:>10.1f} {delta:>+8.1f} ({pct:+.0f}%) [{goal}]')
        else:
            log(f'  {nm:<22} {unit:<6} {v3_val:>12.1f} {"N/A":>10}')

    return all_max


def analyze_es(sol_path, label):
    """ES peak activation 분석."""
    log(f'=== ES Activation Analysis: {label} ===')

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

    es_cols = {}
    for L in labs:
        for mus in ES_MUSCLES:
            if mus in L and ('activation' in L or 'excitation' in L):
                es_cols[mus] = labs.index(L)
                break
    if not es_cols:
        for L in labs:
            if any(pat in L for pat in ['IL_R', 'IL_L', 'LTpL', 'LT_T', 'LT_L']):
                if 'activation' in L or 'excitation' in L:
                    short = L.split('/')[-2] if '/' in L else L
                    es_cols[short] = labs.index(L)

    log(f'  ES columns found: {len(es_cols)}')
    if not es_cols:
        log('  WARNING: No ES columns found.')
        return

    data = np.zeros((nrows, len(es_cols)))
    for i in range(nrows):
        row = tbl.getRowAtIndex(i)
        for j, (_, idx) in enumerate(es_cols.items()):
            data[i, j] = row[idx]

    log(f'  {"Phase":<12} {"v3 peak":>10} {"optD peak":>10} {"delta":>8} {"status":>8}')
    for phase, (t0, t1) in PHASES.items():
        mask = (times >= t0) & (times <= t1)
        if mask.sum() == 0:
            continue
        phase_data = data[mask, :]
        peak_d = phase_data.max() * 100.0
        v3_p   = V3_ES.get(phase, {}).get('peak', float('nan'))
        delta  = peak_d - v3_p
        ok = 'OK' if abs(delta) < 5.0 else 'WARN'
        log(f'  {phase:<12} {v3_p:>10.1f}% {peak_d:>9.1f}% {delta:>+7.1f}%p {ok:>8}')

    # IL_R10_r sentinel
    il_r10_key = next((k for k in es_cols if 'IL_R10_r' in k), None)
    if il_r10_key:
        idx = list(es_cols.keys()).index(il_r10_key)
        log('  --- IL_R10_r (sentinel) ---')
        for phase, (t0, t1) in PHASES.items():
            mask = (times >= t0) & (times <= t1)
            if mask.sum() > 0:
                peak = data[mask, idx].max() * 100.0
                log(f'    {phase:<12}: {peak:.1f}%')


def print_option_d_verdict(results, reserve_max):
    """D.4 자가 검증 — 시나리오 판정."""
    log('')
    log('=' * 60)
    log('옵션 D 결과 (D.4 자가 검증)')
    log('=' * 60)

    if not results:
        log('[판정] 실행 자체 실패 — 시나리오 C')
        log('=> 옵션 1 즉시 전환')
        return

    r = results[0]
    success = r.get('success', False)
    status  = r.get('status', 'UNKNOWN')

    # 1. Reserve 변화
    log('')
    log('[1. Reserve 변화]')
    def get_val(nm):
        for k, v in reserve_max.items():
            if nm in k:
                return v
        return None

    ty_val   = get_val('pelvis_ty')
    tilt_val = get_val('pelvis_tilt')
    tx_val   = get_val('pelvis_tx')
    hip_val  = get_val('hip_flexion_r')

    log(f'  - pelvis_ty  : 3570 N -> {ty_val:.1f if ty_val else "N/A"} N  '
        f'(목표 < 100 N)')
    log(f'  - pelvis_tilt: 269 N.m -> {tilt_val:.1f if tilt_val else "N/A"} N.m  '
        f'(목표 유의미 감소)')
    log(f'  - pelvis_tx  : 90 N -> {tx_val:.1f if tx_val else "N/A"} N  '
        f'(목표 < 50 N)')
    log(f'  - hip_flexion: 42 N.m -> {hip_val:.1f if hip_val else "N/A"} N.m')

    # 2. ES robust (solution.sto 있을 때만)
    log('')
    log('[2. ES Robust 확인]')
    log('  (ES 분석은 위 analyze_es() 출력 참조)')

    # 3. "또 새 발견" 체크 — 정직 평가
    log('')
    log('[3. "또 새 발견" 체크 (정직 평가)]')

    new_finding = False
    # 수렴 실패 확인
    if not success:
        log(f'  - 예상 못한 결과: Y — IPOPT {status} (수렴 실패)')
        new_finding = True
    else:
        log(f'  - 예상 못한 결과: N — IPOPT {status}')

    # pelvis_ty 판정
    if ty_val is not None and ty_val > 100:
        log(f'  - 또 새 가설 등장: Y — pelvis_ty={ty_val:.1f} N > 100 N 목표 미달')
        new_finding = True
    elif ty_val is not None:
        log(f'  - 또 새 가설 등장: N — pelvis_ty={ty_val:.1f} N (< 100 N 달성)')

    log(f'  - "또 시도 권장" 패턴: N (옵션 D 정책 — 결과 보고만)')
    log(f'  - Endpoint artifact: N — GRF v5 전 구간 상수 확인 (D.1 진단)')

    # 4. 시나리오 판정
    log('')
    log('[4. 시나리오 판정]')

    ty_pass   = ty_val is not None and ty_val < 100
    ipopt_ok  = success and ('Optimal' in status or 'Acceptable' in status)

    if ipopt_ok and ty_pass and not new_finding:
        log('  => 시나리오 A (완전 성공): IPOPT PASS + Reserve PASS + 새 발견 없음')
        log('  => B-2 진행 권장 (Phase 1a regression test)')
    elif success and not new_finding:
        log('  => 시나리오 B (부분 성공): 수렴했으나 Reserve 목표 미달')
        log('  => 사전 결정: 옵션 1 즉시 전환')
    else:
        log('  => 시나리오 C (실패): 수렴 X 또는 새 발견 있음')
        log('  => 사전 결정: 옵션 1 즉시 전환')

    log('')
    log('=' * 60)
    log('CHEOL HOON님 사전 결정 재확인')
    log('=' * 60)
    log('  - 시나리오 A -> B-2 진행 (Phase 1a regression test)')
    log('  - 시나리오 B 또는 C -> 옵션 1 즉시 전환 (박스 마무리 + 범용 모델 path)')
    log('')
    log('  자동 다음 시도 금지')
    log('  "또 한 번만 더" 권장 절대 X')
    log('  CHEOL HOON님 사전 결정 그대로 적용')
    log('=' * 60)


def main():
    log('=== Phase 2.C.4 v4 — 옵션 D (API 정정) ===')
    log(f'  Model : {Path(SRC_MODEL).name}')
    log(f'  Motion: {Path(MOT).name}')
    log(f'  GRF   : {Path(GRF_STO_BASE).name} (상수 735.75 N, spike 없음 확인)')
    log(f'  Conditions: {[c[0] for c in CONDITIONS]}')
    log(f'  Mesh={MESH}, t=[{T_START},{T_END}]')
    log('')
    log('  ⭐ KEY CHANGE (B-1 -> 옵션 D):')
    log(f'    B-1  : ModOpAddResiduals(300.0, 50.0, 1.0) [rot=300 N.m, trans=50 N — 역전]')
    log(f'    옵션D: ModOpAddResiduals({RESIDUAL_ROT_NM}, {RESIDUAL_TRANS_N}, {RESIDUAL_SCALE}) '
        f'[rot={RESIDUAL_ROT_NM} N.m, trans={RESIDUAL_TRANS_N} N — 정정]')
    log('')
    log('  D.1 진단: stoop_grf_v5 전 구간 상수 (no spike). B-1 inf_pr=3520은 GRF 문제 아님.')
    log('  D.1 진단: motion v11b dynamic residual 자체가 3520 N — 근본 문제는 motion/GRF 불균형.')

    shared_dir = OUT_ROOT / 'shared'
    shared_dir.mkdir(parents=True, exist_ok=True)
    model_path = shared_dir / 'phase2c4_optionD_model.osim'
    ref_path   = shared_dir / 'states_reference.sto'

    log(f'Preparing shared model ({len(MUSCLE_SET_V2)} muscles)...')
    prepare_model(model_path)

    log('Preparing motion reference (degrees -> radians + smoothing)...')
    prepare_reference(ref_path)

    results     = []
    reserve_max = {}
    t_total     = time.time()

    for label, suit_nm in CONDITIONS:
        try:
            r = run_condition(label, suit_nm, model_path, ref_path)
            results.append(r)

            if Path(r['sol_path']).exists():
                reserve_max = analyze_reserves(r['sol_path'])
                if r['success']:
                    analyze_es(r['sol_path'], label)

        except Exception as e:
            log(f'FATAL in {label}: {e}')
            import traceback; traceback.print_exc()
            results.append({
                'label': label, 'suit_nm': suit_nm,
                'success': False, 'status': str(e),
                'wall_time_s': 0, 'sol_path': 'FAILED',
            })

    log(f'Total wall time: {time.time() - t_total:.1f}s')

    import json
    summary_path = OUT_ROOT / 'solve_summary_optionD.json'
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    log(f'Summary saved: {summary_path}')

    # D.4 자가 검증 + 시나리오 판정
    print_option_d_verdict(results, reserve_max)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f'FATAL: {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)
