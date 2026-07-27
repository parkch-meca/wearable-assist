"""carry-walk 왼팔 IK 최종판 — 시각 대칭 우선 최적화.

분석 결과 (2026-07-28):
  모델 shoulder_elv 축이 좌우 완전 z-mirror가 아님 (z 성분 동일 방향):
    R: axis = (-0.998, +0.002, +0.059)
    L: axis = (+0.998, -0.002, +0.059)  <- z = +0.059 (미러면 -0.059여야)
  결과: ulna(팔꿈치)의 z 위치는 모델 구조상 완전 대칭 달성 불가.
  ulna_R.z = +0.272m vs 최적 ulna_L.z = -0.166m (차이 0.107m, 구조적 한계).

전략 변경 (시각 대칭 우선):
  1. 손(hand) z-미러 최우선 (보는 사람이 가장 먼저 보는 것)
  2. shoulder_elv 크기 동일 강제 (|elv_L| = |elv_R| = 27.19)
     -> 어깨 높낮이 대칭 (정면에서 어깨선 수평)
  3. 팔꿈치 x,y 대칭 가능 범위 내 최대화
  4. elbow_flexion_l = 97.92 고정 (오른팔과 동일)

미러 규칙 (시각 대칭 판):
  shoulder_elv_l   = -27.19 (크기 고정)
  elbow_flexion_l  = +97.92 (동일)
  최적화 변수: elv_angle_l, shoulder_rot_l  (2 DOF)
"""

import numpy as np
import opensim as osim
from scipy.optimize import minimize, differential_evolution
from pathlib import Path

MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim'
GAIT_FILE = '/data/gait_motion/gait_retarget_so.mot'

# 오른팔 확정값
R_ELV   = +27.19
R_EA    = +5.04
R_ROT   = +19.63
R_FLEX  = +97.92

# 왼팔 고정값
L_ELV   = -27.19   # 크기 동일, 부호반전 (어깨 대칭)
L_FLEX  = +97.92   # 팔꿈치 동일

print('Loading model...')
m = osim.Model(MODEL)
s = m.initSystem()
cs = m.getCoordinateSet()
names = [cs.get(i).getName() for i in range(cs.getSize())]
mtype = {cs.get(i).getName(): cs.get(i).getMotionType() for i in range(cs.getSize())}

def set_coord(nm, val_deg):
    if nm not in names: return
    cc = cs.get(nm)
    cc.setValue(s, np.deg2rad(val_deg) if mtype[nm]==1 else val_deg, False)

def get_pos_ground(body_name):
    p = m.getBodySet().get(body_name).getPositionInGround(s)
    return np.array([p.get(0), p.get(1), p.get(2)])

def get_transform_pelvis():
    pelvis = m.getBodySet().get('pelvis')
    T = pelvis.getTransformInGround(s)
    R_osim = T.R()
    p_osim = T.p()
    R_mat = np.array([[R_osim.get(0,0), R_osim.get(0,1), R_osim.get(0,2)],
                      [R_osim.get(1,0), R_osim.get(1,1), R_osim.get(1,2)],
                      [R_osim.get(2,0), R_osim.get(2,1), R_osim.get(2,2)]])
    p_vec = np.array([p_osim.get(0), p_osim.get(1), p_osim.get(2)])
    return R_mat, p_vec

def body_in_pelvis_frame(body_name):
    R_mat, p_pelvis = get_transform_pelvis()
    p_body = get_pos_ground(body_name)
    delta = p_body - p_pelvis
    return R_mat.T @ delta

# ─── 대표 포즈 설정 ──────────────────────────────────────────────────────────
tab = osim.TimeSeriesTable(GAIT_FILE)
tvec = list(tab.getIndependentColumn())
cols = list(tab.getColumnLabels())
mid_idx = 36
row_vals = {c: tab.getDependentColumn(c)[mid_idx] for c in cols}
print(f'Representative frame: t={tvec[mid_idx]:.4f}s  pelvis_ty={row_vals["pelvis_ty"]:.4f}m')

for nm in cols:
    if nm in names:
        set_coord(nm, row_vals[nm])

LUMBAR_SEGS = ['L5_S1_FE','L4_L5_FE','L3_L4_FE','L2_L3_FE','L1_L2_FE','T12_L1_FE']
for seg in LUMBAR_SEGS:
    if seg in names:
        cc = cs.get(seg)
        cur = cc.getValue(s)
        cc.setValue(s, cur + np.deg2rad(-5.0/6.0), False)

for nm in ['clav_prot_r','clav_prot_l']: set_coord(nm, 5.0)
for nm in ['clav_elev_r','clav_elev_l',
           'pro_sup_r','pro_sup_l',
           'wrist_flex_r','wrist_flex_l',
           'wrist_dev_r','wrist_dev_l']: set_coord(nm, 0.0)

# 오른팔 설정 (확정)
set_coord('shoulder_elv_r',  R_ELV)
set_coord('elv_angle_r',     R_EA)
set_coord('shoulder_rot_r',  R_ROT)
set_coord('elbow_flexion_r', R_FLEX)
m.realizePosition(s)

# 오른팔 pelvis-frame 기준값
hR_pf   = body_in_pelvis_frame('hand_R')
ulR_pf  = body_in_pelvis_frame('ulna_R')
humR_pf = body_in_pelvis_frame('humerus_R')
hR_gf   = get_pos_ground('hand_R')

print(f'\nRight arm pelvis-frame:')
print(f'  hand_R:    ({hR_pf[0]:+.4f}, {hR_pf[1]:+.4f}, {hR_pf[2]:+.4f})')
print(f'  ulna_R:    ({ulR_pf[0]:+.4f}, {ulR_pf[1]:+.4f}, {ulR_pf[2]:+.4f})')
print(f'  humerus_R: ({humR_pf[0]:+.4f}, {humR_pf[1]:+.4f}, {humR_pf[2]:+.4f})')

TARGET_HAND_L = np.array([hR_pf[0], hR_pf[1], -hR_pf[2]])
TARGET_ULNA_L = np.array([ulR_pf[0], ulR_pf[1], -ulR_pf[2]])
TARGET_HUM_L  = np.array([humR_pf[0], humR_pf[1], -humR_pf[2]])

print(f'\nMirror targets:')
print(f'  hand_L:    ({TARGET_HAND_L[0]:+.4f}, {TARGET_HAND_L[1]:+.4f}, {TARGET_HAND_L[2]:+.4f})')
print(f'  ulna_L:    ({TARGET_ULNA_L[0]:+.4f}, {TARGET_ULNA_L[1]:+.4f}, {TARGET_ULNA_L[2]:+.4f})')

# ─── 2-DOF 최적화 (shoulder_rot_l, elv_angle_l) ──────────────────────────────
# shoulder_elv_l = -27.19 (고정), elbow_flexion_l = 97.92 (고정)

def arm_fk_L(params):
    """[elv_angle_l, shoulder_rot_l] -> 손,팔꿈치,상완 pelvis-frame."""
    ea, rot = params
    set_coord('shoulder_elv_l',  L_ELV)
    set_coord('elv_angle_l',     ea)
    set_coord('shoulder_rot_l',  rot)
    set_coord('elbow_flexion_l', L_FLEX)
    m.realizePosition(s)
    hL   = body_in_pelvis_frame('hand_L')
    ulL  = body_in_pelvis_frame('ulna_L')
    humL = body_in_pelvis_frame('humerus_L')
    return hL, ulL, humL

def cost_L(params):
    ea, rot = params
    penalty = 0.0
    if not (-30 <= ea <= 30):
        penalty += 1000*(max(0,-30-ea)**2 + max(0,ea-30)**2)
    if not (-90 <= rot <= 60):
        penalty += 1000*(max(0,-90-rot)**2 + max(0,rot-60)**2)

    hL, ulL, humL = arm_fk_L(params)
    # 손 오차 (우선순위 최고, 가중치 3.0)
    err_hand = 3.0 * np.sum((hL - TARGET_HAND_L)**2)
    # 팔꿈치 x,y 오차 (z는 구조적 한계 있으므로 가중치 낮춤)
    err_ulna_xy = 1.0 * ((ulL[0]-TARGET_ULNA_L[0])**2 + (ulL[1]-TARGET_ULNA_L[1])**2)
    err_ulna_z  = 0.3 * (ulL[2]-TARGET_ULNA_L[2])**2  # z: 가중치 0.3
    # 상완 오차 (가중치 0.5)
    err_hum = 0.5 * np.sum((humL - TARGET_HUM_L)**2)
    return err_hand + err_ulna_xy + err_ulna_z + err_hum + penalty

# DE global search (2 DOF)
print('\n' + '='*70)
print(f'2-DOF 최적화: shoulder_elv_l={L_ELV:.2f}(고정), elbow_flexion_l={L_FLEX:.2f}(고정)')
print('최적화 변수: elv_angle_l, shoulder_rot_l')
print('='*70)

bounds_2d = [(-30, 30), (-90, 60)]
de_res = differential_evolution(
    cost_L, bounds_2d, seed=42, maxiter=1000, tol=1e-10,
    workers=1, mutation=(0.5,1.5), recombination=0.9, popsize=25,
)
print(f'DE: cost={de_res.fun:.6f}, ea={de_res.x[0]:+.2f}, rot={de_res.x[1]:+.2f}')

# Nelder-Mead refine
best_cost = de_res.fun
best_params = de_res.x.copy()

inits = [de_res.x.copy()]
inits += [
    [+5.04, -19.63],   # 단순 부호반전
    [-5.04, -19.63],
    [+10.0, -20.0],
    [+0.0,  -15.0],
    [+15.0, -25.0],
    [+5.0,  -10.0],
    [+20.0, -15.0],
    [-5.0,  -25.0],
    [+3.0,  -19.63],
    de_res.x + np.array([3, -5]),
    de_res.x + np.array([-3, +5]),
]

print('\n멀티 시작점 Nelder-Mead:')
for g0 in inits:
    g0 = np.array(g0, dtype=float)
    res = minimize(cost_L, g0, method='Nelder-Mead',
                   options={'xatol':1e-7, 'fatol':1e-12, 'maxiter':20000})
    if res.fun < best_cost:
        best_cost = res.fun
        best_params = res.x.copy()
        hL_b, ulL_b, humL_b = arm_fk_L(res.x)
        print(f'  [갱신] cost={res.fun:.7f}  ea={res.x[0]:+.2f} rot={res.x[1]:+.2f}')
        print(f'    hand_L:({hL_b[0]:+.4f},{hL_b[1]:+.4f},{hL_b[2]:+.4f}) '
              f'ulna_L:({ulL_b[0]:+.4f},{ulL_b[1]:+.4f},{ulL_b[2]:+.4f})')

ea_L, rot_L = best_params
hL_final, ulL_final, humL_final = arm_fk_L(best_params)

# ─── 최종 결과 ───────────────────────────────────────────────────────────────
print('\n' + '='*70)
print('FINAL — 왼팔 확정값')
print('='*70)
print(f'  shoulder_elv_l   = {L_ELV:+.2f} deg  [= -shoulder_elv_r, 크기 동일 강제]')
print(f'  elv_angle_l      = {ea_L:+.2f} deg  [최적화 결과]')
print(f'  shoulder_rot_l   = {rot_L:+.2f} deg  [최적화 결과]')
print(f'  elbow_flexion_l  = {L_FLEX:+.2f} deg  [= +elbow_flexion_r, 동일 고정]')
print(f'  best cost        = {best_cost:.6f}')

print(f'\n[FK 대칭 요약표] pelvis-frame (m)')
print(f'{"Body":<14} {"R x":>8} {"R y":>8} {"R z":>8}   {"L x":>8} {"L y":>8} {"L z":>8}   {"Δx":>7} {"Δy":>7} {"Δz(L+R)":>9}  판정')
print('-'*100)

bodies_final = [
    ('hand',         hR_pf,  hL_final),
    ('ulna(elbow)',  ulR_pf, ulL_final),
    ('humerus',      humR_pf,humL_final),
]
max_hand_err = 0.0
max_elbow_err = 0.0
for bname, R, L in bodies_final:
    dx = abs(L[0]-R[0])
    dy = abs(L[1]-R[1])
    dz_sym = abs(L[2]+R[2])   # z-mirror: L.z + R.z = 0이어야
    max_b = max(dx, dy, dz_sym)
    if bname == 'hand':
        max_hand_err = max_b
    elif 'ulna' in bname:
        max_elbow_err = max_b
    flag = 'PASS' if max_b < 0.03 else ('WARN' if max_b < 0.08 else 'LIMIT')
    print(f'{bname:<14} {R[0]:+8.4f} {R[1]:+8.4f} {R[2]:+8.4f}   {L[0]:+8.4f} {L[1]:+8.4f} {L[2]:+8.4f}   {dx:7.4f} {dy:7.4f} {dz_sym:9.4f}  {flag}')

print()
print(f'손(hand) 최대 오차: {max_hand_err:.4f} m  ->  {"PASS(<3cm)" if max_hand_err<0.03 else ("NEAR(<5cm)" if max_hand_err<0.05 else "CHECK")}')
print(f'팔꿈치(ulna) 최대 오차: {max_elbow_err:.4f} m  ->  {"PASS(<3cm)" if max_elbow_err<0.03 else ("모델구조적한계" if max_elbow_err>0.06 else "NEAR")}')

# 손-손 간격
set_coord('shoulder_elv_l',  L_ELV)
set_coord('elv_angle_l',     ea_L)
set_coord('shoulder_rot_l',  rot_L)
set_coord('elbow_flexion_l', L_FLEX)
m.realizePosition(s)
hL_gf = get_pos_ground('hand_L')
ulR_gf = get_pos_ground('ulna_R')
ulL_gf = get_pos_ground('ulna_L')
hand_sep_z = abs(hR_gf[2] - hL_gf[2])
elbow_sep_z = abs(ulR_gf[2] - ulL_gf[2])
hand_sep_x = abs(hR_gf[0] - hL_gf[0])

print(f'\n손-손 z 간격(ground): {hand_sep_z:.4f} m  {"PASS" if 0.28<=hand_sep_z<=0.32 else "CHECK"}  (기준: 0.28~0.32m)')
print(f'손-손 x 오차(ground): {hand_sep_x:.4f} m  (0에 가까울수록 좋음)')
print(f'팔꿈치 z 간격(ground): {elbow_sep_z:.4f} m  (시각 참고)')

# shoulder 크기 대칭
print(f'\n어깨 대칭 요약:')
print(f'  shoulder_elv: R={R_ELV:+.2f}, L={L_ELV:+.2f}, 크기차={abs(abs(L_ELV)-abs(R_ELV)):.2f}°  -> 완전 대칭')
print(f'  elbow_flex:   R={R_FLEX:+.2f}, L={L_FLEX:+.2f}, 차이={abs(L_FLEX-R_FLEX):.2f}°  -> 동일')
print(f'  shoulder_rot: R={R_ROT:+.2f}, L={rot_L:+.2f}, 크기차={abs(abs(rot_L)-abs(R_ROT)):.2f}°')

# 허벅지 간섭
femR_gf = get_pos_ground('femur_r')
femL_gf = get_pos_ground('femur_l')
box_cen_x = (hR_gf[0] + hL_gf[0]) / 2
box_back = box_cen_x - 0.15
print(f'\n허벅지 간섭:')
print(f'  femur_r x={femR_gf[0]:+.3f}  박스후면={box_back:+.3f}  gap={box_back-femR_gf[0]:+.3f}m  {"OK" if box_back>femR_gf[0] else "WARN"}')
print(f'  femur_l x={femL_gf[0]:+.3f}  박스후면={box_back:+.3f}  gap={box_back-femL_gf[0]:+.3f}m  {"OK" if box_back>femL_gf[0] else "WARN"}')

print('\n' + '='*70)
print('gen_carry_walk.py 업데이트 값:')
print('='*70)
print(f"ARM_CARRY_R = {{")
print(f"    'shoulder_elv_r':   {R_ELV:.2f},")
print(f"    'elv_angle_r':       {R_EA:.2f},")
print(f"    'shoulder_rot_r':   {R_ROT:.2f},")
print(f"    'elbow_flexion_r':  {R_FLEX:.2f},")
print(f"    'clav_prot_r':       5.0,")
print(f"    'clav_elev_r':       0.0,")
print(f"}}")
print(f"ARM_CARRY_L = {{")
print(f"    'shoulder_elv_l':  {L_ELV:.2f},   # = -shoulder_elv_r (크기 동일)")
print(f"    'elv_angle_l':      {ea_L:.2f},   # 2-DOF 최적화 결과")
print(f"    'shoulder_rot_l':  {rot_L:.2f},   # 2-DOF 최적화 결과")
print(f"    'elbow_flexion_l': {L_FLEX:.2f},   # = +elbow_flexion_r (동일)")
print(f"    'clav_prot_l':      5.0,")
print(f"    'clav_elev_l':      0.0,")
print(f"}}")
print('\nDONE.')
