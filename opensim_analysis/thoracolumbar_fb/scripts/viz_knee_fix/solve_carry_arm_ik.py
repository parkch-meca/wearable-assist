"""Carry-walk 팔 IK 재해결 스크립트.

문제: 이전 버전에서 hand pelvis-frame y = +0.006~+0.020m (골반 높이)
원인: shoulder_rot_r = +42 deg 내회전 과다 → 전완 교차
목표: pelvis-frame y = +0.15~+0.20m (배꼽~명치), z = ±0.15m, x = +0.20~+0.24m

방법:
  1. 대표 carry 포즈 (lean-back 적용) 설정
  2. 팔 4각 (shoulder_elv, elv_angle, shoulder_rot, elbow_flexion)을
     Nelder-Mead 최적화로 pelvis-frame 목표에 맞춤
  3. 해결된 상수를 gen_carry_walk.py에 반영
"""

import numpy as np
import opensim as osim
from scipy.optimize import minimize

MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim'
GAIT_FILE = '/data/gait_motion/gait_retarget_so.mot'

# ─── 대표 프레임: 걷기 중립 프레임 (t~0.583s, 중간 보행) ───────────────────
# 실제 gait 데이터의 첫 프레임 값 사용 (t=0.4s)
# pelvis_tilt=5.186, pelvis_ty=1.045 로 lean-back 후 대표적 하체 자세

# Lean-back 오프셋 (6 lumbar seg × -0.833 deg = -5 deg 총 신전)
LEAN_BACK_DEG = -5.0 / 6.0  # = -0.8333 deg per segment

# 목표 손 위치 (pelvis body frame)
TARGET_R = np.array([+0.22, +0.17, +0.15])   # x=전방, y=위, z=우
TARGET_L = np.array([+0.22, +0.17, -0.15])   # z=좌

# 허용 공차
X_TOL = 0.02   # ±0.02m
Y_LO, Y_HI = 0.13, 0.22   # y range
Z_TARGET_R, Z_TARGET_L = +0.15, -0.15
Z_TOL = 0.025

print('Loading model...')
m = osim.Model(MODEL)
s = m.initSystem()
cs = m.getCoordinateSet()
names = [cs.get(i).getName() for i in range(cs.getSize())]
mtype = {cs.get(i).getName(): cs.get(i).getMotionType() for i in range(cs.getSize())}

def set_coord(nm, val_deg):
    if nm not in names:
        return
    cc = cs.get(nm)
    if mtype[nm] == 1:  # rotational
        cc.setValue(s, np.deg2rad(val_deg), False)
    else:
        cc.setValue(s, val_deg, False)

def get_pos_ground(body_name):
    p = m.getBodySet().get(body_name).getPositionInGround(s)
    return np.array([p.get(0), p.get(1), p.get(2)])

def get_transform_pelvis():
    """pelvis body의 ground-frame Transform 반환."""
    pelvis = m.getBodySet().get('pelvis')
    T = pelvis.getTransformInGround(s)
    R = T.R()  # Rotation 3x3
    p = T.p()  # position Vec3
    R_mat = np.array([[R.get(0,0), R.get(0,1), R.get(0,2)],
                       [R.get(1,0), R.get(1,1), R.get(1,2)],
                       [R.get(2,0), R.get(2,1), R.get(2,2)]])
    p_vec = np.array([p.get(0), p.get(1), p.get(2)])
    return R_mat, p_vec

def hand_in_pelvis_frame(body_name):
    """손 위치를 pelvis body frame 기준으로 반환 (회전 포함)."""
    R_mat, p_pelvis = get_transform_pelvis()
    p_hand = get_pos_ground(body_name)
    # pelvis frame: R^T * (p_hand - p_pelvis)
    delta = p_hand - p_pelvis
    return R_mat.T @ delta

# ─── 대표 포즈 설정 ──────────────────────────────────────────────────────────
# gait 첫 프레임 기준값 읽기
tab = osim.TimeSeriesTable(GAIT_FILE)
tvec = list(tab.getIndependentColumn())
cols = list(tab.getColumnLabels())

# 중간 프레임 선택 (보행 중간, t~0.7s 근처: row index ~17)
# gait 73 frames, 0.4~1.6s => 중간 = 36번째 row
mid_idx = 36
row_vals = {c: tab.getDependentColumn(c)[mid_idx] for c in cols}
t_mid = tvec[mid_idx]
print(f'Representative frame: t={t_mid:.4f}s')
print(f'  pelvis_tilt={row_vals["pelvis_tilt"]:.3f} deg, pelvis_ty={row_vals["pelvis_ty"]:.4f} m')
print(f'  pelvis_tx={row_vals["pelvis_tx"]:.4f} m, pelvis_tz={row_vals["pelvis_tz"]:.4f} m')

# 전체 조인트 설정 (하체 포즈 + lean-back)
for nm in cols:
    if nm in names:
        set_coord(nm, row_vals[nm])

# lean-back 적용 (lumbar FE 6개에 -0.833 deg 추가)
LUMBAR_SEGS = ['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L2_L3_FE', 'L1_L2_FE', 'T12_L1_FE']
for seg in LUMBAR_SEGS:
    if seg in names:
        cc = cs.get(seg)
        cur = cc.getValue(s)
        cc.setValue(s, cur + np.deg2rad(LEAN_BACK_DEG), False)

# 초기화 (gait shoulder_elv 제거 -> 팔 중립으로 시작)
# clav_prot = +5 고정
set_coord('clav_prot_r', 5.0)
set_coord('clav_prot_l', 5.0)
set_coord('clav_elev_r', 0.0)
set_coord('clav_elev_l', 0.0)
set_coord('pro_sup_r', 0.0)
set_coord('pro_sup_l', 0.0)
set_coord('wrist_flex_r', 0.0)
set_coord('wrist_flex_l', 0.0)
set_coord('wrist_dev_r', 0.0)
set_coord('wrist_dev_l', 0.0)
m.realizePosition(s)

# pelvis 위치/방향 확인
R_pel, p_pel = get_transform_pelvis()
print(f'\nPelvis ground pos: ({p_pel[0]:+.4f}, {p_pel[1]:+.4f}, {p_pel[2]:+.4f}) m')
print(f'Pelvis rotation matrix (row0): {R_pel[0,:]}')


# ─── 우측 팔 IK ─────────────────────────────────────────────────────────────
print('\n' + '='*70)
print('RIGHT ARM IK (target pelvis-frame: x=+0.22, y=+0.17, z=+0.15)')
print('='*70)

# 팔 4각: [shoulder_elv_r, elv_angle_r, shoulder_rot_r, elbow_flexion_r]
# 이전값: [19, -2, 42, 68] → z가 +0.15 맞지만 y가 너무 낮음

def arm_fk_R(params):
    """우측 팔 4각 -> hand_R pelvis-frame 위치."""
    elv, elv_ang, rot, flex = params
    set_coord('shoulder_elv_r',  elv)
    set_coord('elv_angle_r',     elv_ang)
    set_coord('shoulder_rot_r',  rot)
    set_coord('elbow_flexion_r', flex)
    m.realizePosition(s)
    return hand_in_pelvis_frame('hand_R')

def cost_R(params):
    elv, elv_ang, rot, flex = params
    # ROM 패널티
    penalty = 0.0
    if not (0 <= elv <= 120):   penalty += 1000*(max(0,-elv)**2 + max(0,elv-120)**2)
    if not (-30 <= elv_ang <= 30): penalty += 1000*(max(0,-30-elv_ang)**2 + max(0,elv_ang-30)**2)
    if not (-60 <= rot <= 90):  penalty += 1000*(max(0,-60-rot)**2 + max(0,rot-90)**2)
    if not (0 <= flex <= 140):  penalty += 1000*(max(0,-flex)**2 + max(0,flex-140)**2)

    pos = arm_fk_R(params)
    dx = pos[0] - TARGET_R[0]
    dy = pos[1] - TARGET_R[1]
    dz = pos[2] - TARGET_R[2]
    return dx**2 + dy**2 + dz**2 + penalty

# 다중 초기점 시도
best_cost_R = 1e10
best_params_R = None
best_pos_R = None

init_guesses_R = [
    [45, 10, 10, 90],   # 팔 앞으로 많이 들고, 내회전 약하게
    [50, 15, 5, 85],
    [40, 5, 15, 95],
    [55, 20, 0, 80],
    [35, 10, 20, 100],
    [45, 10, -10, 90],  # 외회전 시도
    [60, 15, 10, 85],
    [30, 5, 25, 80],
]

print('\n초기점 탐색:')
for g0 in init_guesses_R:
    res = minimize(cost_R, g0, method='Nelder-Mead',
                   options={'xatol':1e-5, 'fatol':1e-8, 'maxiter':5000})
    pos = arm_fk_R(res.x)
    print(f'  init={[f"{v:.0f}" for v in g0]} -> cost={res.fun:.6f} '
          f'pos=({pos[0]:+.3f},{pos[1]:+.3f},{pos[2]:+.3f})')
    if res.fun < best_cost_R:
        best_cost_R = res.fun
        best_params_R = res.x.copy()
        best_pos_R = pos.copy()

elv_R, elv_ang_R, rot_R, flex_R = best_params_R
print(f'\nBEST RIGHT: cost={best_cost_R:.6f}')
print(f'  shoulder_elv_r  = {elv_R:+.2f} deg')
print(f'  elv_angle_r     = {elv_ang_R:+.2f} deg')
print(f'  shoulder_rot_r  = {rot_R:+.2f} deg')
print(f'  elbow_flexion_r = {flex_R:+.2f} deg')
print(f'  hand_R pelvis-frame: ({best_pos_R[0]:+.4f}, {best_pos_R[1]:+.4f}, {best_pos_R[2]:+.4f}) m')
print(f'  target:              ({TARGET_R[0]:+.4f}, {TARGET_R[1]:+.4f}, {TARGET_R[2]:+.4f}) m')
print(f'  error: dx={best_pos_R[0]-TARGET_R[0]:+.4f} dy={best_pos_R[1]-TARGET_R[1]:+.4f} dz={best_pos_R[2]-TARGET_R[2]:+.4f} m')


# ─── 좌측 팔 IK ─────────────────────────────────────────────────────────────
print('\n' + '='*70)
print('LEFT ARM IK (target pelvis-frame: x=+0.22, y=+0.17, z=-0.15)')
print('='*70)

def arm_fk_L(params):
    """좌측 팔 4각 -> hand_L pelvis-frame 위치."""
    elv, elv_ang, rot, flex = params
    # 좌측 convention: shoulder_elv_l 음수, shoulder_rot_l 음수
    set_coord('shoulder_elv_l',  elv)    # 음수로 입력
    set_coord('elv_angle_l',     elv_ang)
    set_coord('shoulder_rot_l',  rot)    # 음수로 입력
    set_coord('elbow_flexion_l', flex)
    m.realizePosition(s)
    return hand_in_pelvis_frame('hand_L')

def cost_L(params):
    elv, elv_ang, rot, flex = params
    penalty = 0.0
    # 좌측: shoulder_elv_l은 음수 범위
    if not (-120 <= elv <= 0):  penalty += 1000*(max(0,elv)**2 + max(0,-elv-120)**2)
    if not (-30 <= elv_ang <= 30): penalty += 1000*(max(0,-30-elv_ang)**2 + max(0,elv_ang-30)**2)
    if not (-90 <= rot <= 60):  penalty += 1000*(max(0,-90-rot)**2 + max(0,rot-60)**2)
    if not (0 <= flex <= 140):  penalty += 1000*(max(0,-flex)**2 + max(0,flex-140)**2)

    pos = arm_fk_L(params)
    dx = pos[0] - TARGET_L[0]
    dy = pos[1] - TARGET_L[1]
    dz = pos[2] - TARGET_L[2]
    return dx**2 + dy**2 + dz**2 + penalty

best_cost_L = 1e10
best_params_L = None
best_pos_L = None

# 좌측 초기 추정: shoulder_elv_l 음수, shoulder_rot_l 음수
init_guesses_L = [
    [-45, 10, -10, 90],
    [-50, 15, -5, 85],
    [-40, 5, -15, 95],
    [-55, 20, 0, 80],
    [-35, 10, -20, 100],
    [-45, 10, 10, 90],   # 외회전(+) 시도
    [-60, 15, -10, 85],
    [-30, 5, -25, 80],
]

print('\n초기점 탐색:')
for g0 in init_guesses_L:
    res = minimize(cost_L, g0, method='Nelder-Mead',
                   options={'xatol':1e-5, 'fatol':1e-8, 'maxiter':5000})
    pos = arm_fk_L(res.x)
    print(f'  init={[f"{v:.0f}" for v in g0]} -> cost={res.fun:.6f} '
          f'pos=({pos[0]:+.3f},{pos[1]:+.3f},{pos[2]:+.3f})')
    if res.fun < best_cost_L:
        best_cost_L = res.fun
        best_params_L = res.x.copy()
        best_pos_L = pos.copy()

elv_L, elv_ang_L, rot_L, flex_L = best_params_L
print(f'\nBEST LEFT: cost={best_cost_L:.6f}')
print(f'  shoulder_elv_l  = {elv_L:+.2f} deg')
print(f'  elv_angle_l     = {elv_ang_L:+.2f} deg')
print(f'  shoulder_rot_l  = {rot_L:+.2f} deg')
print(f'  elbow_flexion_l = {flex_L:+.2f} deg')
print(f'  hand_L pelvis-frame: ({best_pos_L[0]:+.4f}, {best_pos_L[1]:+.4f}, {best_pos_L[2]:+.4f}) m')
print(f'  target:              ({TARGET_L[0]:+.4f}, {TARGET_L[1]:+.4f}, {TARGET_L[2]:+.4f}) m')
print(f'  error: dx={best_pos_L[0]-TARGET_L[0]:+.4f} dy={best_pos_L[1]-TARGET_L[1]:+.4f} dz={best_pos_L[2]-TARGET_L[2]:+.4f} m')


# ─── 결과 요약 ───────────────────────────────────────────────────────────────
print('\n' + '='*70)
print('SUMMARY - gen_carry_walk.py에 반영할 상수값')
print('='*70)
print(f"ARM_CARRY_R = {{")
print(f"    'shoulder_elv_r':   {elv_R:.1f},")
print(f"    'elv_angle_r':      {elv_ang_R:.1f},")
print(f"    'shoulder_rot_r':   {rot_R:.1f},")
print(f"    'elbow_flexion_r':  {flex_R:.1f},")
print(f"    'clav_prot_r':       5.0,")
print(f"    'clav_elev_r':       0.0,")
print(f"}}")
print(f"ARM_CARRY_L = {{")
print(f"    'shoulder_elv_l':  {elv_L:.1f},")
print(f"    'elv_angle_l':     {elv_ang_L:.1f},")
print(f"    'shoulder_rot_l':  {rot_L:.1f},")
print(f"    'elbow_flexion_l': {flex_L:.1f},")
print(f"    'clav_prot_l':      5.0,")
print(f"    'clav_elev_l':      0.0,")
print(f"}}")

# ─── 검증: 좌우 대칭 확인 ────────────────────────────────────────────────────
print('\n' + '='*70)
print('FK VALIDATION - 좌우 대칭 및 박스-골반 분리 확인')
print('='*70)

# 최종값으로 양팔 동시 설정
set_coord('shoulder_elv_r',  elv_R)
set_coord('elv_angle_r',     elv_ang_R)
set_coord('shoulder_rot_r',  rot_R)
set_coord('elbow_flexion_r', flex_R)
set_coord('shoulder_elv_l',  elv_L)
set_coord('elv_angle_l',     elv_ang_L)
set_coord('shoulder_rot_l',  rot_L)
set_coord('elbow_flexion_l', flex_L)
m.realizePosition(s)

hR_pf = hand_in_pelvis_frame('hand_R')
hL_pf = hand_in_pelvis_frame('hand_L')
hR_gf = get_pos_ground('hand_R')
hL_gf = get_pos_ground('hand_L')
p_pelvis = get_pos_ground('pelvis')

print(f'\n  hand_R pelvis-frame: ({hR_pf[0]:+.4f}, {hR_pf[1]:+.4f}, {hR_pf[2]:+.4f}) m')
print(f'  hand_L pelvis-frame: ({hL_pf[0]:+.4f}, {hL_pf[1]:+.4f}, {hL_pf[2]:+.4f}) m')
print(f'  hand_R ground-frame: ({hR_gf[0]:+.4f}, {hR_gf[1]:+.4f}, {hR_gf[2]:+.4f}) m')
print(f'  hand_L ground-frame: ({hL_gf[0]:+.4f}, {hL_gf[1]:+.4f}, {hL_gf[2]:+.4f}) m')
print(f'  pelvis ground-frame: ({p_pelvis[0]:+.4f}, {p_pelvis[1]:+.4f}, {p_pelvis[2]:+.4f}) m')

# 박스 중심 및 분리 확인
box_center_pf_x = (hR_pf[0] + hL_pf[0]) / 2
box_center_pf_y = (hR_pf[1] + hL_pf[1]) / 2
box_back_pf_x = box_center_pf_x - 0.15   # 박스 뒷면 = 중심 - 반폭(0.15)
box_bottom_pf_y = box_center_pf_y - 0.15  # 박스 바닥 = 중심 - 반높이(0.15)

print(f'\n  [박스 분리 확인]')
print(f'  박스 pelvis-frame 중심: x={box_center_pf_x:+.3f}, y={box_center_pf_y:+.3f}')
print(f'  박스 뒷면(pelvis-frame x): {box_back_pf_x:+.3f} m', end='')
print(f'  -> {"OK (골반 앞, 관통없음)" if box_back_pf_x > 0.0 else "WARN (골반과 겹침 가능성)"}')
print(f'  박스 바닥(pelvis-frame y): {box_bottom_pf_y:+.3f} m', end='')
print(f'  -> {"OK (골반 위, 사타구니 아님)" if box_bottom_pf_y > -0.05 else "WARN (골반보다 낮음)"}')

# V1-V5 기준 재확인
print(f'\n  [V1-V5 기준 재확인]')
print(f'  V1 hand_R.z = {hR_gf[2]:+.4f} m  (target +0.15±0.03)  {"PASS" if 0.12<=hR_gf[2]<=0.18 else "FAIL"}')
print(f'  V2 hand_L.z = {hL_gf[2]:+.4f} m  (target -0.15±0.03)  {"PASS" if -0.18<=hL_gf[2]<=-0.12 else "FAIL"}')
print(f'  V3 hand_R pelvis-x = {hR_pf[0]:+.4f}  (target +0.10~+0.24)  {"PASS" if 0.10<=hR_pf[0]<=0.24 else "FAIL"}')
print(f'  V3 hand_L pelvis-x = {hL_pf[0]:+.4f}  (target +0.10~+0.24)  {"PASS" if 0.10<=hL_pf[0]<=0.24 else "FAIL"}')
print(f'  V4 hand_R pelvis-y = {hR_pf[1]:+.4f}  (new target +0.13~+0.22)  {"PASS" if 0.13<=hR_pf[1]<=0.22 else "FAIL"}')
print(f'  V4 hand_L pelvis-y = {hL_pf[1]:+.4f}  (new target +0.13~+0.22)  {"PASS" if 0.13<=hL_pf[1]<=0.22 else "FAIL"}')

# 박스폭 확인
hand_sep = abs(hR_gf[2] - hL_gf[2])
print(f'  V6 손-손 간격(z) = {hand_sep:.4f} m  (target 0.28~0.32)  {"PASS" if 0.28<=hand_sep<=0.32 else "FAIL"}')

print('\nDONE. 위 ARM_CARRY 값을 gen_carry_walk.py에 복사하여 적용하세요.')
