"""carry-walk 왼팔 IK 재해결 — 손+팔꿈치 동시 z-미러 최적화.

문제 진단 (2026-07-28):
  shoulder_elv 축이 좌우 완전 z-mirror가 아님:
    R: axis = (-0.998, +0.002, +0.059)
    L: axis = (+0.998, -0.002, +0.059)  <- z성분 +0.059 동일 (미러면 -0.059여야)
  결과: 단순 부호반전으로 팔꿈치(ulna) z 오차 0.225m — 허용 불가.

해결:
  왼팔 4각 (shoulder_elv_l, elv_angle_l, shoulder_rot_l, elbow_flexion_l)을
  Nelder-Mead + basin-hopping으로 최적화.
  비용함수: hand + ulna(elbow) 두 body의 pelvis-frame z-미러 오차 최소화.
  (x, y 오차도 포함하여 전체 대칭 최적화)

제약:
  - shoulder_elv_l:  [-120, 0]  (좌측 convention)
  - elv_angle_l:     [-30, 30]
  - shoulder_rot_l:  [-90, 60]
  - elbow_flexion_l: [0, 140]

목표 좌표 (pelvis-frame, 오른팔 기준 z-미러):
  hand_L:  (+0.2200, +0.1700, -0.1500)
  ulna_L:  (-0.0054, +0.1404, -0.2724)

가중치: hand 1.0, ulna(elbow) 1.0 (동등)
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
print(f'Representative frame: t={tvec[mid_idx]:.4f}s')

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

# 오른팔 pelvis-frame 기준값 (미러 목표)
hR_pf   = body_in_pelvis_frame('hand_R')
ulR_pf  = body_in_pelvis_frame('ulna_R')
humR_pf = body_in_pelvis_frame('humerus_R')

print(f'\nRight arm pelvis-frame (mirror targets for left):')
print(f'  hand_R:    ({hR_pf[0]:+.4f}, {hR_pf[1]:+.4f}, {hR_pf[2]:+.4f})')
print(f'  ulna_R:    ({ulR_pf[0]:+.4f}, {ulR_pf[1]:+.4f}, {ulR_pf[2]:+.4f})')
print(f'  humerus_R: ({humR_pf[0]:+.4f}, {humR_pf[1]:+.4f}, {humR_pf[2]:+.4f})')

# 미러 타겟
TARGET_HAND_L  = np.array([hR_pf[0],  hR_pf[1],  -hR_pf[2]])
TARGET_ULNA_L  = np.array([ulR_pf[0], ulR_pf[1], -ulR_pf[2]])
TARGET_HUM_L   = np.array([humR_pf[0],humR_pf[1],-humR_pf[2]])

print(f'\nTarget (z-mirror):')
print(f'  hand_L:    ({TARGET_HAND_L[0]:+.4f}, {TARGET_HAND_L[1]:+.4f}, {TARGET_HAND_L[2]:+.4f})')
print(f'  ulna_L:    ({TARGET_ULNA_L[0]:+.4f}, {TARGET_ULNA_L[1]:+.4f}, {TARGET_ULNA_L[2]:+.4f})')

# ─── 왼팔 IK 비용함수 ────────────────────────────────────────────────────────
def arm_fk_L(params):
    """왼팔 4각 -> [hand_L, ulna_L, humerus_L] pelvis-frame."""
    elv, ea, rot, flex = params
    set_coord('shoulder_elv_l',  elv)
    set_coord('elv_angle_l',     ea)
    set_coord('shoulder_rot_l',  rot)
    set_coord('elbow_flexion_l', flex)
    m.realizePosition(s)
    hL   = body_in_pelvis_frame('hand_L')
    ulL  = body_in_pelvis_frame('ulna_L')
    humL = body_in_pelvis_frame('humerus_L')
    return hL, ulL, humL

def cost_L(params):
    elv, ea, rot, flex = params
    # ROM 패널티 (좌측 convention: elv 음수)
    penalty = 0.0
    if not (-120 <= elv <= 0):
        penalty += 1000*(max(0,elv)**2 + max(0,-elv-120)**2)
    if not (-30 <= ea <= 30):
        penalty += 1000*(max(0,-30-ea)**2 + max(0,ea-30)**2)
    if not (-90 <= rot <= 60):
        penalty += 1000*(max(0,-90-rot)**2 + max(0,rot-60)**2)
    if not (0 <= flex <= 140):
        penalty += 1000*(max(0,-flex)**2 + max(0,flex-140)**2)

    hL, ulL, humL = arm_fk_L(params)
    # 손: x,y,z 모두 매칭
    err_hand = np.sum((hL - TARGET_HAND_L)**2)
    # 팔꿈치: x,y,z 모두 매칭
    err_ulna = np.sum((ulL - TARGET_ULNA_L)**2)
    # 상완: 추가 (가중치 0.5)
    err_hum  = 0.5 * np.sum((humL - TARGET_HUM_L)**2)
    return err_hand + err_ulna + err_hum + penalty

# ─── 1단계: Differential Evolution (global search) ────────────────────────────
print('\n' + '='*70)
print('Stage 1: Differential Evolution (global search)')
print('='*70)

bounds = [(-120, 0),   # shoulder_elv_l
          (-30, 30),   # elv_angle_l
          (-90, 60),   # shoulder_rot_l
          (0, 140)]    # elbow_flexion_l

de_result = differential_evolution(
    cost_L, bounds,
    seed=42, maxiter=500, tol=1e-8,
    workers=1, mutation=(0.5, 1.5), recombination=0.9,
    popsize=20,
    callback=lambda xk, convergence: None
)
print(f'DE best cost: {de_result.fun:.6f}')
hL_de, ulL_de, humL_de = arm_fk_L(de_result.x)
print(f'  DE params: elv={de_result.x[0]:+.2f}, ea={de_result.x[1]:+.2f}, rot={de_result.x[2]:+.2f}, flex={de_result.x[3]:+.2f}')
print(f'  hand_L:   ({hL_de[0]:+.4f}, {hL_de[1]:+.4f}, {hL_de[2]:+.4f})')
print(f'  ulna_L:   ({ulL_de[0]:+.4f}, {ulL_de[1]:+.4f}, {ulL_de[2]:+.4f})')

# ─── 2단계: Nelder-Mead refine (DE 해 주변) ──────────────────────────────────
print('\n' + '='*70)
print('Stage 2: Nelder-Mead refinement (multi-start)')
print('='*70)

best_cost = de_result.fun
best_params = de_result.x.copy()

init_points = [de_result.x.copy()]
# 추가 초기점: 이전 버전 해 주변
init_points += [
    [-27.19, +5.04,  -19.63, +97.92],   # 단순 부호반전
    [-27.19, -5.04,  -19.63, +97.92],
    [-53.73, +24.49, -27.63, +92.55],   # v3 이전 해
    [-40.0,  +10.0,  -15.0,  +95.0],
    [-50.0,  +5.0,   -20.0,  +90.0],
    [-35.0,  +15.0,  -25.0,  +100.0],
    [-45.0,  +0.0,   -10.0,  +97.92],
    [-60.0,  +5.0,   -20.0,  +90.0],
    [-30.0,  +10.0,  -15.0,  +97.92],
    de_result.x + np.array([5, 2, -3, 2]),
    de_result.x + np.array([-5, -2, 3, -2]),
]

for g0 in init_points:
    g0 = np.array(g0, dtype=float)
    res = minimize(cost_L, g0, method='Nelder-Mead',
                   options={'xatol':1e-6, 'fatol':1e-10, 'maxiter':10000})
    if res.fun < best_cost:
        best_cost = res.fun
        best_params = res.x.copy()
        hL_best, ulL_best, humL_best = arm_fk_L(res.x)
        print(f'  New best! cost={res.fun:.6f}  elv={res.x[0]:+.2f} ea={res.x[1]:+.2f} rot={res.x[2]:+.2f} flex={res.x[3]:+.2f}')
        print(f'    hand_L: ({hL_best[0]:+.4f},{hL_best[1]:+.4f},{hL_best[2]:+.4f})')
        print(f'    ulna_L: ({ulL_best[0]:+.4f},{ulL_best[1]:+.4f},{ulL_best[2]:+.4f})')

# 최종 FK
elv_L, ea_L, rot_L, flex_L = best_params
hL_final, ulL_final, humL_final = arm_fk_L(best_params)

# ─── 결과 요약 ───────────────────────────────────────────────────────────────
print('\n' + '='*70)
print('FINAL RESULT — 왼팔 확정값 (손+팔꿈치 동시 z-미러 최적화)')
print('='*70)
print(f'  shoulder_elv_l   = {elv_L:+.2f} deg')
print(f'  elv_angle_l      = {ea_L:+.2f} deg')
print(f'  shoulder_rot_l   = {rot_L:+.2f} deg')
print(f'  elbow_flexion_l  = {flex_L:+.2f} deg')
print(f'  best cost        = {best_cost:.6f}')

print(f'\n[FK 대칭 요약표] pelvis-frame (m)')
print(f'{"Body":<14} {"R x":>8} {"R y":>8} {"R z":>8}   {"L x":>8} {"L y":>8} {"L z":>8}   {"Δx":>7} {"Δy":>7} {"Δz(+)":>8}')
print('-'*90)

bodies = [
    ('hand',         hR_pf,  hL_final),
    ('ulna(elbow)',  ulR_pf, ulL_final),
    ('humerus',      humR_pf,humL_final),
]
max_err_overall = 0.0
for bname, R, L in bodies:
    dx = abs(L[0]-R[0])
    dy = abs(L[1]-R[1])
    dz = abs(L[2]+R[2])   # z-mirror: L.z + R.z ~ 0
    max_b = max(dx,dy,dz)
    max_err_overall = max(max_err_overall, max_b)
    flag = 'OK' if max_b < 0.03 else ('WARN' if max_b < 0.06 else 'FAIL')
    print(f'{bname:<14} {R[0]:+8.4f} {R[1]:+8.4f} {R[2]:+8.4f}   {L[0]:+8.4f} {L[1]:+8.4f} {L[2]:+8.4f}   {dx:7.4f} {dy:7.4f} {dz:8.4f}  {flag}')

print(f'\n최대 대칭 오차: {max_err_overall:.4f} m  -> {"PASS (<3cm)" if max_err_overall<0.03 else ("OK (<6cm)" if max_err_overall<0.06 else "MARGINAL")}')

# 손-손 간격
set_coord('shoulder_elv_l',  elv_L)
set_coord('elv_angle_l',     ea_L)
set_coord('shoulder_rot_l',  rot_L)
set_coord('elbow_flexion_l', flex_L)
m.realizePosition(s)
hR_gf = get_pos_ground('hand_R')
hL_gf = get_pos_ground('hand_L')
hand_sep = abs(hR_gf[2] - hL_gf[2])
print(f'손-손 z 간격: {hand_sep:.4f} m  (0.28~0.32 = 박스폭 OK? {"PASS" if 0.28<=hand_sep<=0.32 else "FAIL/CHECK"})')

# shoulder 크기 대칭
print(f'\nshoulder_elv:  R={R_ELV:+.2f}, L={elv_L:+.2f}  크기차이={abs(abs(elv_L)-abs(R_ELV)):.2f} deg')
print(f'shoulder_rot:  R={R_ROT:+.2f}, L={rot_L:+.2f}  크기차이={abs(abs(rot_L)-abs(R_ROT)):.2f} deg')
print(f'elbow_flexion: R={R_FLEX:+.2f}, L={flex_L:+.2f}  차이={abs(flex_L-R_FLEX):.2f} deg')

# 허벅지 간섭 (mid 프레임)
femR_gf = get_pos_ground('femur_r')
femL_gf = get_pos_ground('femur_l')
box_cen_x = (hR_gf[0] + hL_gf[0]) / 2
box_back = box_cen_x - 0.15
print(f'\n--- 허벅지 간섭 ---')
print(f'  femur_r x={femR_gf[0]:+.3f}  박스후면={box_back:+.3f}  gap={box_back-femR_gf[0]:+.3f}m  {"OK" if box_back>femR_gf[0] else "WARN"}')
print(f'  femur_l x={femL_gf[0]:+.3f}  박스후면={box_back:+.3f}  gap={box_back-femL_gf[0]:+.3f}m  {"OK" if box_back>femL_gf[0] else "WARN"}')

print('\n' + '='*70)
print('gen_carry_walk.py ARM_CARRY_L 업데이트 값:')
print('='*70)
print(f"ARM_CARRY_L = {{")
print(f"    'shoulder_elv_l':  {elv_L:.2f},   # 손+팔꿈치 동시 z-미러 IK")
print(f"    'elv_angle_l':     {ea_L:.2f},   # 좌측 축 비대칭 보정값")
print(f"    'shoulder_rot_l':  {rot_L:.2f},   # 손+팔꿈치 IK 결과")
print(f"    'elbow_flexion_l': {flex_L:.2f},   # 손+팔꿈치 IK 결과")
print(f"    'clav_prot_l':      5.0,")
print(f"    'clav_elev_l':      0.0,")
print(f"}}")
print('\nDONE.')
