"""carry-walk 왼팔 진짜 미러 FK 검증 스크립트.

목적:
  오른팔 4각 확정값 유지하고, 왼팔을 부호 미러 규칙으로 설정.
  elv_angle_l 두 후보(+5.04, -5.04)를 FK로 시험, 팔꿈치·상완·손 모두
  z-미러 오차 최소인 것 채택.

미러 규칙 (armfix 모델 기준):
  shoulder_elv_l   = -shoulder_elv_r  (부호반전)
  shoulder_rot_l   = -shoulder_rot_r  (부호반전)
  elbow_flexion_l  = +elbow_flexion_r (동일, hinge 불변)
  elv_angle_l      = +5.04 OR -5.04  -> FK 실증으로 결정

대칭 지표 (pelvis-frame):
  hand:    L.x==R.x, L.y==R.y, L.z==-R.z
  elbow:   ulna_L.x==ulna_R.x, ulna_L.y==ulna_R.y, ulna_L.z==-ulna_R.z
  humerus: humerus_L.x==humerus_R.x, etc.
"""

import numpy as np
import opensim as osim
from pathlib import Path

MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim'
GAIT_FILE = '/data/gait_motion/gait_retarget_so.mot'

# 확정된 오른팔 4각
SHOULDER_ELV_R  = +27.19
ELV_ANGLE_R     = +5.04
SHOULDER_ROT_R  = +19.63
ELBOW_FLEX_R    = +97.92

# 부호 미러 왼팔 후보 (elv_angle_l만 두 후보)
ELV_ANGLE_L_CANDIDATES = [+5.04, -5.04]

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
    if mtype[nm] == 1:
        cc.setValue(s, np.deg2rad(val_deg), False)
    else:
        cc.setValue(s, val_deg, False)

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

# ─── 대표 프레임 설정 (gait 중간 프레임 t~0.7s) ──────────────────────────────
tab = osim.TimeSeriesTable(GAIT_FILE)
tvec = list(tab.getIndependentColumn())
cols = list(tab.getColumnLabels())
mid_idx = 36
row_vals = {c: tab.getDependentColumn(c)[mid_idx] for c in cols}
t_mid = tvec[mid_idx]
print(f'Representative frame: t={t_mid:.4f}s, pelvis_ty={row_vals["pelvis_ty"]:.4f}m')

# 전체 하체 설정
for nm in cols:
    if nm in names:
        set_coord(nm, row_vals[nm])

# lean-back (-0.8333 deg × 6 segs)
LUMBAR_SEGS = ['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L2_L3_FE', 'L1_L2_FE', 'T12_L1_FE']
for seg in LUMBAR_SEGS:
    if seg in names:
        cc = cs.get(seg)
        cur = cc.getValue(s)
        cc.setValue(s, cur + np.deg2rad(-5.0/6.0), False)

# 공통 설정
for nm in ['clav_prot_r','clav_prot_l']:
    set_coord(nm, 5.0)
for nm in ['clav_elev_r','clav_elev_l',
           'pro_sup_r','pro_sup_l',
           'wrist_flex_r','wrist_flex_l',
           'wrist_dev_r','wrist_dev_l']:
    set_coord(nm, 0.0)

# 오른팔 설정 (확정)
set_coord('shoulder_elv_r',  SHOULDER_ELV_R)
set_coord('elv_angle_r',     ELV_ANGLE_R)
set_coord('shoulder_rot_r',  SHOULDER_ROT_R)
set_coord('elbow_flexion_r', ELBOW_FLEX_R)
m.realizePosition(s)

# 오른팔 pelvis-frame 기준값
hR_pf    = body_in_pelvis_frame('hand_R')
elbR_pf  = body_in_pelvis_frame('ulna_R')
humR_pf  = body_in_pelvis_frame('humerus_R')

print(f'\nRight arm pelvis-frame:')
print(f'  hand_R:     ({hR_pf[0]:+.4f}, {hR_pf[1]:+.4f}, {hR_pf[2]:+.4f}) m')
print(f'  ulna_R:     ({elbR_pf[0]:+.4f}, {elbR_pf[1]:+.4f}, {elbR_pf[2]:+.4f}) m')
print(f'  humerus_R:  ({humR_pf[0]:+.4f}, {humR_pf[1]:+.4f}, {humR_pf[2]:+.4f}) m')

# 예상 미러 타겟
print(f'\nExpected z-mirror (left) targets:')
print(f'  hand_L target:    ({hR_pf[0]:+.4f}, {hR_pf[1]:+.4f}, {-hR_pf[2]:+.4f}) m')
print(f'  ulna_L target:    ({elbR_pf[0]:+.4f}, {elbR_pf[1]:+.4f}, {-elbR_pf[2]:+.4f}) m')
print(f'  humerus_L target: ({humR_pf[0]:+.4f}, {humR_pf[1]:+.4f}, {-humR_pf[2]:+.4f}) m')

# ─── elv_angle_l 두 후보 FK 검증 ─────────────────────────────────────────────
print('\n' + '='*70)
print('elv_angle_l 후보 비교 (부호 미러 규칙 적용)')
print('='*70)
print(f'  shoulder_elv_l   = {-SHOULDER_ELV_R:+.2f} (부호반전 고정)')
print(f'  shoulder_rot_l   = {-SHOULDER_ROT_R:+.2f} (부호반전 고정)')
print(f'  elbow_flexion_l  = {+ELBOW_FLEX_R:+.2f} (동일 고정)')
print()

results_table = []

for ea_l in ELV_ANGLE_L_CANDIDATES:
    set_coord('shoulder_elv_l',  -SHOULDER_ELV_R)
    set_coord('elv_angle_l',     ea_l)
    set_coord('shoulder_rot_l',  -SHOULDER_ROT_R)
    set_coord('elbow_flexion_l', +ELBOW_FLEX_R)
    m.realizePosition(s)

    hL_pf   = body_in_pelvis_frame('hand_L')
    elbL_pf = body_in_pelvis_frame('ulna_L')
    humL_pf = body_in_pelvis_frame('humerus_L')

    # z-미러 오차 계산 (x,y는 동일해야, z는 부호반전해야)
    hand_err_x  = abs(hL_pf[0] - hR_pf[0])
    hand_err_y  = abs(hL_pf[1] - hR_pf[1])
    hand_err_z  = abs(hL_pf[2] - (-hR_pf[2]))
    elb_err_x   = abs(elbL_pf[0] - elbR_pf[0])
    elb_err_y   = abs(elbL_pf[1] - elbR_pf[1])
    elb_err_z   = abs(elbL_pf[2] - (-elbR_pf[2]))
    hum_err_x   = abs(humL_pf[0] - humR_pf[0])
    hum_err_y   = abs(humL_pf[1] - humR_pf[1])
    hum_err_z   = abs(humL_pf[2] - (-humR_pf[2]))

    max_hand = max(hand_err_x, hand_err_y, hand_err_z)
    max_elb  = max(elb_err_x, elb_err_y, elb_err_z)
    max_hum  = max(hum_err_x, hum_err_y, hum_err_z)
    total_err = max_hand + max_elb + max_hum

    print(f'--- elv_angle_l = {ea_l:+.2f} deg ---')
    print(f'  hand_L pelvis-frame:     ({hL_pf[0]:+.4f}, {hL_pf[1]:+.4f}, {hL_pf[2]:+.4f})')
    print(f'  ulna_L pelvis-frame:     ({elbL_pf[0]:+.4f}, {elbL_pf[1]:+.4f}, {elbL_pf[2]:+.4f})')
    print(f'  humerus_L pelvis-frame:  ({humL_pf[0]:+.4f}, {humL_pf[1]:+.4f}, {humL_pf[2]:+.4f})')
    print(f'  [hand 대칭 오차]  x={hand_err_x:.4f} y={hand_err_y:.4f} z={hand_err_z:.4f}  max={max_hand:.4f} m')
    print(f'  [elbow 대칭 오차] x={elb_err_x:.4f} y={elb_err_y:.4f} z={elb_err_z:.4f}  max={max_elb:.4f} m')
    print(f'  [humerus 대칭 오차] x={hum_err_x:.4f} y={hum_err_y:.4f} z={hum_err_z:.4f}  max={max_hum:.4f} m')
    print(f'  -> total_err = {total_err:.4f} m\n')

    results_table.append({
        'ea_l': ea_l,
        'hL': hL_pf, 'elbL': elbL_pf, 'humL': humL_pf,
        'max_hand': max_hand, 'max_elb': max_elb, 'max_hum': max_hum,
        'total_err': total_err,
    })

# ─── 최선 후보 선택 ───────────────────────────────────────────────────────────
best = min(results_table, key=lambda r: r['total_err'])
print('='*70)
print(f'최선 elv_angle_l 후보: {best["ea_l"]:+.2f} deg  (total_err={best["total_err"]:.4f} m)')
if best['total_err'] < 0.02:
    print('판정: 부호 미러로 완전 대칭 PASS (max err < 0.02 m)')
elif best['total_err'] < 0.05:
    print('판정: 부호 미러 근사 대칭 OK (max err < 0.05 m)')
else:
    print('판정: 부호 미러로도 팔꿈치 대칭 불충분 (모델 비대칭) — 아래 상세 확인 필요')

print()
print('확정 왼팔 4각 (미러 규칙):')
print(f'  shoulder_elv_l   = {-SHOULDER_ELV_R:+.2f}  [= -shoulder_elv_r]')
print(f'  elv_angle_l      = {best["ea_l"]:+.2f}  [FK 실증 최적]')
print(f'  shoulder_rot_l   = {-SHOULDER_ROT_R:+.2f}  [= -shoulder_rot_r]')
print(f'  elbow_flexion_l  = {+ELBOW_FLEX_R:+.2f}  [= +elbow_flexion_r]')

# ─── 대칭 요약 표 ─────────────────────────────────────────────────────────────
ea_l_best = best['ea_l']
set_coord('shoulder_elv_l',  -SHOULDER_ELV_R)
set_coord('elv_angle_l',     ea_l_best)
set_coord('shoulder_rot_l',  -SHOULDER_ROT_R)
set_coord('elbow_flexion_l', +ELBOW_FLEX_R)
m.realizePosition(s)

hL_pf   = body_in_pelvis_frame('hand_L')
elbL_pf = body_in_pelvis_frame('ulna_L')
humL_pf = body_in_pelvis_frame('humerus_L')

print()
print('='*70)
print('FK 대칭 요약표 (pelvis-frame, 확정 왼팔 적용)')
print('='*70)
print(f'{"Body":<14} {"R x":>8} {"R y":>8} {"R z":>8}   {"L x":>8} {"L y":>8} {"L z":>8}   {"Δx":>7} {"Δy":>7} {"Δz (L.z+R.z)":>14}')
print('-'*95)

bodies = [('hand', hR_pf, hL_pf),
          ('ulna(elbow)', elbR_pf, elbL_pf),
          ('humerus', humR_pf, humL_pf)]
for bname, R, L in bodies:
    dx = abs(L[0]-R[0])
    dy = abs(L[1]-R[1])
    dz = abs(L[2]+R[2])   # z-mirror: L.z == -R.z, so L.z+R.z ~ 0
    print(f'{bname:<14} {R[0]:+8.4f} {R[1]:+8.4f} {R[2]:+8.4f}   {L[0]:+8.4f} {L[1]:+8.4f} {L[2]:+8.4f}   {dx:7.4f} {dy:7.4f} {dz:14.4f}')

# 손-손 간격 (박스 폭)
hR_gf = get_pos_ground('hand_R')
hL_gf = get_pos_ground('hand_L')
hand_sep_z = abs(hR_gf[2] - hL_gf[2])
print(f'\n손-손 z 간격 (ground frame): {hand_sep_z:.4f} m  (박스폭 30cm -> 0.28~0.32 OK?  {"PASS" if 0.28<=hand_sep_z<=0.32 else "FAIL"})')

# shoulder_elv/rot 크기 대칭 확인
print(f'\nshoulder_elv:  R={SHOULDER_ELV_R:+.2f}  L={-SHOULDER_ELV_R:+.2f}  크기 동일={SHOULDER_ELV_R:.2f}=={SHOULDER_ELV_R:.2f} OK')
print(f'shoulder_rot:  R={SHOULDER_ROT_R:+.2f}  L={-SHOULDER_ROT_R:+.2f}  크기 동일={SHOULDER_ROT_R:.2f}=={SHOULDER_ROT_R:.2f} OK')
print(f'elbow_flexion: R={ELBOW_FLEX_R:+.2f}  L={+ELBOW_FLEX_R:+.2f}  동일 OK')

# 허벅지 간섭 (hip_flexion max 프레임)
print('\n--- 허벅지 간섭 점검 (gait 대표 프레임 기준) ---')
# 현재 프레임의 hip_flexion_r 값
hip_val = row_vals.get('hip_flexion_r', 0.0)
femR_gf = get_pos_ground('femur_r')
femL_gf = get_pos_ground('femur_l')
# 박스 중심 (손 z 중점이 0)
box_cen_x = (hR_gf[0] + hL_gf[0]) / 2
box_cen_y = (hR_gf[1] + hL_gf[1]) / 2
print(f'  hip_flexion_r (현 프레임): {hip_val:+.2f} deg')
print(f'  femur_r: ({femR_gf[0]:+.3f}, {femR_gf[1]:+.3f}, {femR_gf[2]:+.3f}) m')
print(f'  femur_l: ({femL_gf[0]:+.3f}, {femL_gf[1]:+.3f}, {femL_gf[2]:+.3f}) m')
print(f'  박스 중심(ground): x={box_cen_x:+.3f} y={box_cen_y:+.3f} z=0.000')
box_back = box_cen_x - 0.15
femR_gap = box_back - femR_gf[0]
femL_gap = box_back - femL_gf[0]
print(f'  femur_r -> 박스 후면 gap: {femR_gap:+.3f} m  {"OK (간섭없음)" if femR_gap > 0 else "WARN"}')
print(f'  femur_l -> 박스 후면 gap: {femL_gap:+.3f} m  {"OK (간섭없음)" if femL_gap > 0 else "WARN"}')

print('\nDONE.')
print()
print('=== gen_carry_walk.py 업데이트 값 ===')
print(f"ARM_CARRY_L = {{")
print(f"    'shoulder_elv_l':  {-SHOULDER_ELV_R:.2f},   # = -shoulder_elv_r (부호미러)")
print(f"    'elv_angle_l':     {ea_l_best:.2f},   # FK 실증 최적값")
print(f"    'shoulder_rot_l':  {-SHOULDER_ROT_R:.2f},   # = -shoulder_rot_r (부호미러)")
print(f"    'elbow_flexion_l': {+ELBOW_FLEX_R:.2f},   # = +elbow_flexion_r (hinge 불변)")
print(f"    'clav_prot_l':      5.0,")
print(f"    'clav_elev_l':      0.0,")
print(f"}}")
