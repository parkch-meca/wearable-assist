"""carry-walk 전 프레임 FK 검증 스크립트.

새 팔 상수 적용 후 모든 프레임에서:
  - hand pelvis-frame (x,y,z) 분포
  - ground z 분산 (pelvis 이동에 따른 변화 확인)
  - 박스-골반 분리
  - 박스 바닥 위치 (허벅지/사타구니 위인지)
  - 전완 교차 여부 (z 부호 유지 확인)
"""
import numpy as np
import opensim as osim

MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim'
GAIT_FILE = '/data/gait_motion/gait_retarget_so.mot'

# 새 팔 상수 (IK 해결값)
ARM_CARRY_R_NEW = {
    'shoulder_elv_r':   27.2,
    'elv_angle_r':       5.0,
    'shoulder_rot_r':   19.6,
    'elbow_flexion_r':  97.9,
    'clav_prot_r':       5.0,
    'clav_elev_r':       0.0,
}
ARM_CARRY_L_NEW = {
    'shoulder_elv_l':  -17.6,
    'elv_angle_l':       9.3,
    'shoulder_rot_l':   -7.8,
    'elbow_flexion_l':  92.6,
    'clav_prot_l':       5.0,
    'clav_elev_l':       0.0,
}

LUMBAR_SEGS = ['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE', 'L2_L3_FE', 'L1_L2_FE', 'T12_L1_FE']
LEAN_OFFSET = -5.0 / 6.0   # -0.8333 deg per seg

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

def hand_in_pelvis_frame(body_name):
    pelvis = m.getBodySet().get('pelvis')
    T = pelvis.getTransformInGround(s)
    R = T.R()
    p = T.p()
    R_mat = np.array([[R.get(0,0), R.get(0,1), R.get(0,2)],
                       [R.get(1,0), R.get(1,1), R.get(1,2)],
                       [R.get(2,0), R.get(2,1), R.get(2,2)]])
    p_pelvis = np.array([p.get(0), p.get(1), p.get(2)])
    p_hand = get_pos_ground(body_name)
    return R_mat.T @ (p_hand - p_pelvis)

# 원본 gait 로드
tab = osim.TimeSeriesTable(GAIT_FILE)
tvec = list(tab.getIndependentColumn())
cols = list(tab.getColumnLabels())
n = len(tvec)
print(f'Frames: {n}, t=[{tvec[0]:.4f}, {tvec[-1]:.4f}]')

# 전 프레임 처리
hR_pf_all = np.zeros((n, 3))
hL_pf_all = np.zeros((n, 3))
hR_gf_all = np.zeros((n, 3))
hL_gf_all = np.zeros((n, 3))
calcn_y_all = np.zeros(n)
femR_all = np.zeros((n, 3))
femL_all = np.zeros((n, 3))
pelvis_y_all = np.zeros(n)

print('Running FK for all frames...')
for i in range(n):
    row_vals = {c: tab.getDependentColumn(c)[i] for c in cols}

    # 하체/체간 설정
    for nm in cols:
        if nm in names:
            set_coord(nm, row_vals[nm])

    # lean-back 추가
    for seg in LUMBAR_SEGS:
        if seg in names:
            cc = cs.get(seg)
            cur = cc.getValue(s)
            cc.setValue(s, cur + np.deg2rad(LEAN_OFFSET), False)

    # 팔 상수 적용
    for nm, v in ARM_CARRY_R_NEW.items():
        set_coord(nm, v)
    for nm, v in ARM_CARRY_L_NEW.items():
        set_coord(nm, v)
    set_coord('pro_sup_r', 0.0); set_coord('pro_sup_l', 0.0)
    set_coord('wrist_flex_r', 0.0); set_coord('wrist_flex_l', 0.0)
    set_coord('wrist_dev_r', 0.0); set_coord('wrist_dev_l', 0.0)

    m.realizePosition(s)

    hR_pf_all[i] = hand_in_pelvis_frame('hand_R')
    hL_pf_all[i] = hand_in_pelvis_frame('hand_L')
    hR_gf_all[i] = get_pos_ground('hand_R')
    hL_gf_all[i] = get_pos_ground('hand_L')
    calcn_y_all[i] = get_pos_ground('calcn_r')[1]
    femR_all[i] = get_pos_ground('femur_r')
    femL_all[i] = get_pos_ground('femur_l')
    p_pel = get_pos_ground('pelvis')
    pelvis_y_all[i] = p_pel[1]

    if i % 20 == 0:
        print(f'  frame {i}/{n}: hR_pf=({hR_pf_all[i,0]:+.3f},{hR_pf_all[i,1]:+.3f},{hR_pf_all[i,2]:+.3f})')

print('\n' + '='*70)
print('전 프레임 pelvis-frame 손 위치 통계')
print('='*70)
print(f'\n  hand_R pelvis-frame:')
print(f'    x: mean={hR_pf_all[:,0].mean():+.4f}  std={hR_pf_all[:,0].std():.4f}  min={hR_pf_all[:,0].min():+.4f}  max={hR_pf_all[:,0].max():+.4f}')
print(f'    y: mean={hR_pf_all[:,1].mean():+.4f}  std={hR_pf_all[:,1].std():.4f}  min={hR_pf_all[:,1].min():+.4f}  max={hR_pf_all[:,1].max():+.4f}')
print(f'    z: mean={hR_pf_all[:,2].mean():+.4f}  std={hR_pf_all[:,2].std():.4f}  min={hR_pf_all[:,2].min():+.4f}  max={hR_pf_all[:,2].max():+.4f}')
print(f'\n  hand_L pelvis-frame:')
print(f'    x: mean={hL_pf_all[:,0].mean():+.4f}  std={hL_pf_all[:,0].std():.4f}  min={hL_pf_all[:,0].min():+.4f}  max={hL_pf_all[:,0].max():+.4f}')
print(f'    y: mean={hL_pf_all[:,1].mean():+.4f}  std={hL_pf_all[:,1].std():.4f}  min={hL_pf_all[:,1].min():+.4f}  max={hL_pf_all[:,1].max():+.4f}')
print(f'    z: mean={hL_pf_all[:,2].mean():+.4f}  std={hL_pf_all[:,2].std():.4f}  min={hL_pf_all[:,2].min():+.4f}  max={hL_pf_all[:,2].max():+.4f}')

# y 범위 기준 통과 여부 (매 프레임)
y_pass_R = np.sum((hR_pf_all[:,1] >= 0.13) & (hR_pf_all[:,1] <= 0.22))
y_pass_L = np.sum((hL_pf_all[:,1] >= 0.13) & (hL_pf_all[:,1] <= 0.22))
print(f'\n  V4 pelvis-y 범위(0.13~0.22) PASS 프레임:')
print(f'    hand_R: {y_pass_R}/{n} 프레임 PASS')
print(f'    hand_L: {y_pass_L}/{n} 프레임 PASS')

x_pass_R = np.sum((hR_pf_all[:,0] >= 0.10) & (hR_pf_all[:,0] <= 0.24))
x_pass_L = np.sum((hL_pf_all[:,0] >= 0.10) & (hL_pf_all[:,0] <= 0.24))
print(f'  V3 pelvis-x 범위(0.10~0.24) PASS 프레임:')
print(f'    hand_R: {x_pass_R}/{n} 프레임 PASS')
print(f'    hand_L: {x_pass_L}/{n} 프레임 PASS')

# 손-손 간격 (ground frame z)
hand_sep_gf = np.abs(hR_gf_all[:,2] - hL_gf_all[:,2])
print(f'\n  V6 손-손 간격(ground z): mean={hand_sep_gf.mean():.4f} std={hand_sep_gf.std():.4f}  min={hand_sep_gf.min():.4f}  max={hand_sep_gf.max():.4f}')
# pelvis-frame으로 계산
hand_sep_pf = np.abs(hR_pf_all[:,2] - hL_pf_all[:,2])
print(f'  V6 손-손 간격(pelvis-z):  mean={hand_sep_pf.mean():.4f} std={hand_sep_pf.std():.4f}  min={hand_sep_pf.min():.4f}  max={hand_sep_pf.max():.4f}')

# ground frame z 분포 (pelvis 이동 효과 확인)
print(f'\n  hand_R ground z: mean={hR_gf_all[:,2].mean():+.4f} std={hR_gf_all[:,2].std():.4f}  (pelvis 이동 포함)')
print(f'  hand_L ground z: mean={hL_gf_all[:,2].mean():+.4f} std={hL_gf_all[:,2].std():.4f}  (pelvis 이동 포함)')
print(f'  [INFO] pelvis_tz range: {tab.getDependentColumn("pelvis_tz")[0]:.4f}~{tab.getDependentColumn("pelvis_tz")[n-1]:.4f}')

# floor_ht 확인
floor_ht_R = (hR_gf_all[:,1] - calcn_y_all)
floor_ht_L = (hL_gf_all[:,1] - calcn_y_all)
print(f'\n  V5 floor_ht_R (hand_y - calcn_y): mean={floor_ht_R.mean():.4f}  min={floor_ht_R.min():.4f}  max={floor_ht_R.max():.4f}')
print(f'  V5 floor_ht_L (hand_y - calcn_y): mean={floor_ht_L.mean():.4f}  min={floor_ht_L.min():.4f}  max={floor_ht_L.max():.4f}')
v5_pass_R = np.sum((floor_ht_R >= 0.88) & (floor_ht_R <= 1.10))
v5_pass_L = np.sum((floor_ht_L >= 0.88) & (floor_ht_L <= 1.10))
print(f'  V5 PASS 프레임 (0.88~1.10m): R={v5_pass_R}/{n}  L={v5_pass_L}/{n}')

# 박스-골반 분리 (pelvis-frame)
box_back_pf_x = (hR_pf_all[:,0] + hL_pf_all[:,0]) / 2 - 0.15
box_bottom_pf_y = (hR_pf_all[:,1] + hL_pf_all[:,1]) / 2 - 0.15
sep_pass = np.sum(box_back_pf_x > 0.0)
bot_pass = np.sum(box_bottom_pf_y > -0.05)
print(f'\n  [박스-골반 분리]')
print(f'  뒷면 pelvis-x > 0: {sep_pass}/{n} 프레임 PASS (min={box_back_pf_x.min():+.4f})')
print(f'  바닥 pelvis-y > -0.05: {bot_pass}/{n} 프레임 PASS (min={box_bottom_pf_y.min():+.4f})')

# 전완 교차 여부: hand_R.z > hand_L.z (ground frame) 모든 프레임
cross_ok = np.sum(hR_gf_all[:,2] > hL_gf_all[:,2])
print(f'\n  [전완 교차 방지] hand_R.z > hand_L.z: {cross_ok}/{n} 프레임 PASS')

# 허벅지 간섭 (hip 최대 굴곡 프레임)
hip_r_vals = [tab.getDependentColumn('hip_flexion_r')[i] for i in range(n)]
max_hip_idx = int(np.argmax(np.abs(hip_r_vals)))
print(f'\n  [허벅지 간섭 점검]')
print(f'  hip_flexion_r 최대: {hip_r_vals[max_hip_idx]:+.2f} deg at t={tvec[max_hip_idx]:.3f}s')
box_c_x = (hR_gf_all[max_hip_idx,0] + hL_gf_all[max_hip_idx,0]) / 2
box_c_y = (hR_gf_all[max_hip_idx,1] + hL_gf_all[max_hip_idx,1]) / 2
femR = femR_all[max_hip_idx]
femL = femL_all[max_hip_idx]
# 박스 뒷면 x = box_c_x - 0.15
femR_gap = (box_c_x - 0.15) - femR[0]
femL_gap = (box_c_x - 0.15) - femL[0]
print(f'  박스 중심(ground): ({box_c_x:+.3f}, {box_c_y:+.3f})')
print(f'  femur_r: ({femR[0]:+.3f}, {femR[1]:+.3f}), 박스 후면 gap: {femR_gap:+.3f} m {"OK" if femR_gap>0 else "WARN"}')
print(f'  femur_l: ({femL[0]:+.3f}, {femL[1]:+.3f}), 박스 후면 gap: {femL_gap:+.3f} m {"OK" if femL_gap>0 else "WARN"}')

# 박스 pelvis-frame y 안정성 (팔 상수 고정이면 pelvis-frame 변동 작아야)
print(f'\n  [pelvis-frame 안정성] (팔 상수 고정)')
print(f'  hR_pf y std={hR_pf_all[:,1].std():.4f}  L std={hL_pf_all[:,1].std():.4f} (< 0.05 OK)')
print(f'  hR_pf x std={hR_pf_all[:,0].std():.4f}  L std={hL_pf_all[:,0].std():.4f}')
print(f'  hR_pf z std={hR_pf_all[:,2].std():.4f}  L std={hL_pf_all[:,2].std():.4f}')
pel_stab = max(hR_pf_all.std(axis=0).max(), hL_pf_all.std(axis=0).max())
print(f'  최대 std: {pel_stab:.4f} m -> {"PASS" if pel_stab<0.05 else "WARN"}')

print('\n' + '='*70)
print('전체 FK 검증 완료')
print('='*70)
