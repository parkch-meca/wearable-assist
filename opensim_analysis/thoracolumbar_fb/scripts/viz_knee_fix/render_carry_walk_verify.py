"""carry_walk_v2.mot 동작 검증용 시각 산출물 생성.

산출물 1: 보행 주기 5 프레임 × 2 view (sagittal + anterior) grid
산출물 2: 관절각 시계열 plot grid (팔 상수 확인 + 하체 보행 + lumbar lean-back)

모델: armfix (좌우 독립 팔).
VIZ-MIRROR 적용:
  - 어깨 girdle 전체 (clavicle_L, scapula_L, humerus_L, ulna_L, radius_L, hand_L) 숨김
  - 오른팔 girdle 전체를 z=0 평면 반사 (surf.reflect((0,0,1), point=0)) 해 왼팔로 렌더
  - culling=False (non-triangle mesh 법선 문제 회피)
  - flip_normals 사용 안 함 (non-triangle 실패)
  - knee-fix: PyVista 직접 transform 기반이라 viz-mirror와 무관하게 자동 정상
박스: 30cm 정육면체, 양손 중점 배꼽/명치 높이 안은 자세 (전 구간 안고 걷기).
  viz-mirror로 왼손=오른손의 거울이 되므로 박스 중심은 정중앙(z=0).
v2 변경: shoulder_elv_r=27, elbow_flexion 93~98, shoulder_rot 크게 감소, 박스 배꼽 높이로 상승.
"""
import os, sys
os.environ.setdefault('DISPLAY', ':1')

from pathlib import Path
import numpy as np
import opensim as osim
import pyvista as pv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib import font_manager as fm

# ── 경로 설정 ──────────────────────────────────────────────────────────────────
MODEL_PATH = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim'
GEOM_DIR   = Path('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry')
MOT_PATH   = '/data/gait_motion/carry_walk_v2.mot'
IMG_DIR    = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box')
IMG_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR    = Path('/tmp/carry_walk_verify')
TMP_DIR.mkdir(parents=True, exist_ok=True)

# 보행 주기 5 프레임 (idx, 영어 라벨) — carry_walk_v2.mot 기준
# t=[0.40, 1.60], 73 frames
FRAMES = [
    (3,  'Initial Contact R\nt=0.45s'),
    (12, 'Loading Response\nt=0.60s'),
    (27, 'Mid-Stance\nt=0.85s'),
    (42, 'Terminal Stance\nt=1.10s'),
    (60, 'Pre-Swing\nt=1.40s'),
]

# 박스 치수
BOX_HALF = 0.15   # 30cm 정육면체 반치수

# 한국어 폰트
KF = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
if Path(KF).exists():
    fm.fontManager.addfont(KF)
    plt.rcParams['font.family'] = fm.FontProperties(fname=KF).get_name()
plt.rcParams['axes.unicode_minus'] = False

# ── 모델 + 모션 로드 ──────────────────────────────────────────────────────────
print('Loading model...')
model = osim.Model(MODEL_PATH)
state = model.initSystem()
cs    = model.getCoordinateSet()
coord_names = [cs.get(i).getName() for i in range(cs.getSize())]
coord_mtype = {cs.get(i).getName(): cs.get(i).getMotionType() for i in range(cs.getSize())}

print('Loading motion...')
mot   = osim.TimeSeriesTable(MOT_PATH)
t_vec = list(mot.getIndependentColumn())
mot_cols = list(mot.getColumnLabels())
n_frames = len(t_vec)
print(f'  {n_frames} frames, t=[{t_vec[0]:.4f}, {t_vec[-1]:.4f}] s')

# 전체 관절각 배열 로드 (각도 시계열 plot 용)
data = {}
for c in mot_cols:
    data[c] = np.array([mot.getDependentColumn(c)[i] for i in range(n_frames)])


# ── 유틸 함수 ─────────────────────────────────────────────────────────────────
def transform_mat4(T):
    """OpenSim Transform -> 4x4 numpy matrix."""
    R, p = T.R(), T.p()
    M = np.eye(4)
    for i in range(3):
        for j in range(3):
            M[i, j] = R.get(i, j)
        M[i, 3] = p.get(i)
    return M


def collect_meshes(mdl):
    """모델의 모든 Mesh component 수집."""
    out = []
    for comp in list(mdl.getComponentsList()):
        if comp.getConcreteClassName() != 'Mesh':
            continue
        mesh = osim.Mesh.safeDownCast(comp)
        mf   = mesh.get_mesh_file()
        if not mf:
            continue
        p = GEOM_DIR / mf
        if not p.exists():
            p = GEOM_DIR / Path(mf).name
        if not p.exists():
            continue
        sf = mesh.get_scale_factors()
        out.append({
            'path':  str(p),
            'frame': mesh.getFrame().getAbsolutePathString(),
            'scale': (sf.get(0), sf.get(1), sf.get(2)),
        })
    return out


def set_pose(frame_idx):
    """모션 프레임을 모델 state에 적용."""
    for nm in coord_names:
        if nm not in mot_cols:
            continue
        val = mot.getDependentColumn(nm)[frame_idx]
        if coord_mtype[nm] == 1:
            val = np.deg2rad(val)
        cs.get(nm).setValue(state, val, False)
    model.realizePosition(state)


def get_hand_pos():
    """양손 ground frame 위치 반환."""
    hand_R_pos = None
    hand_L_pos = None
    for comp in model.getComponentsList():
        nm = comp.getName()
        pf = osim.PhysicalFrame.safeDownCast(comp)
        if pf is None:
            continue
        if nm == 'hand_R':
            p = pf.getPositionInGround(state)
            hand_R_pos = np.array([p.get(0), p.get(1), p.get(2)])
        elif nm == 'hand_L':
            p = pf.getPositionInGround(state)
            hand_L_pos = np.array([p.get(0), p.get(1), p.get(2)])
    return hand_R_pos, hand_L_pos


# ── 메쉬 사전 수집 ────────────────────────────────────────────────────────────
print('Collecting meshes...')
meshes = collect_meshes(model)
print(f'  {len(meshes)} mesh components found')

# frame → component 캐시
frame_comp_cache = {}
for mi in meshes:
    fn = mi['frame']
    if fn not in frame_comp_cache:
        try:
            frame_comp_cache[fn] = model.getComponent(fn)
        except Exception:
            frame_comp_cache[fn] = None


# ── VIZ-MIRROR 헬퍼 ───────────────────────────────────────────────────────────
# 어깨 girdle 전체 포함 (쇄골·견갑 빠지면 girdle 비대칭 잔존)
_MIRROR_R_KEYS = ('clavicle_R', 'scapula_R', 'humerus_R', 'ulna_R', 'radius_R', 'hand_R')
_MIRROR_L_KEYS = ('clavicle_L', 'scapula_L', 'humerus_L', 'ulna_L', 'radius_L', 'hand_L')


def arm_side(fp):
    """frame path에서 팔 측면 판별 (girdle 전체 포함)."""
    if any(k in fp for k in _MIRROR_R_KEYS):
        return 'R'
    if any(k in fp for k in _MIRROR_L_KEYS):
        return 'L'
    return None


# ── 단일 프레임 렌더 함수 ─────────────────────────────────────────────────────
def render_frame(frame_idx, view='sagittal', tag=''):
    """
    view: 'sagittal' (측면 z=+3.5) | 'anterior' (정면 x=+3.5)
    VIZ-MIRROR: 왼팔 girdle 숨기고 오른팔 girdle z반사로 대체.
    """
    set_pose(frame_idx)

    # 박스 중심 계산 — viz-mirror로 왼손=오른손 거울이 되므로 z=0 정중앙
    hR, hL = get_hand_pos()
    if hR is not None and hL is not None:
        # viz-mirror 적용 후 왼손은 오른손의 z반사 → 평균 x=hR[0], y=hR[1], z=0
        box_cx = hR[0]
        box_cy = hR[1]
        box_cz = 0.0
    else:
        px_val_fb = cs.get('pelvis_tx').getValue(state)
        py_val_fb = cs.get('pelvis_ty').getValue(state)
        box_cx = px_val_fb + 0.18
        box_cy = py_val_fb - 0.1
        box_cz = 0.0

    px_val = cs.get('pelvis_tx').getValue(state)

    pl = pv.Plotter(window_size=(560, 720), off_screen=True, border=False)
    pv.global_theme.background = '#141414'

    # ── 신체 mesh 렌더 (VIZ-MIRROR 적용) ─────────────────────────────────────
    for mi in meshes:
        comp = frame_comp_cache.get(mi['frame'])
        if comp is None:
            continue

        sd = arm_side(mi['frame'])
        # VIZ-MIRROR: 왼팔 girdle mesh는 완전히 스킵
        if sd == 'L':
            continue

        try:
            surf = pv.read(mi['path'])
        except Exception:
            continue
        sx, sy, sz = mi['scale']
        if (sx, sy, sz) != (1, 1, 1):
            surf = surf.scale([sx, sy, sz], inplace=False)
        try:
            T = osim.Frame.safeDownCast(comp).getTransformInGround(state)
            surf = surf.transform(transform_mat4(T), inplace=False)
        except Exception:
            continue

        fr = mi['frame']
        # carry: 양팔 대칭 안기 → 좌우 동일 색상(기본 bone 색)으로 통일
        col = '#E0D8C8'  # bone color (carry는 좌우 구분 색 불필요)

        pl.add_mesh(surf, color=col, opacity=0.99, smooth_shading=True)

        # VIZ-MIRROR: 오른팔 girdle mesh를 z=0 반사해 왼팔로 추가
        if sd == 'R':
            mir = surf.reflect((0, 0, 1), point=(0, 0, 0))
            # culling=False: non-triangle mesh에서 법선 반전 안 함 (flip_normals 실패 회피)
            pl.add_mesh(mir, color=col, opacity=0.99, smooth_shading=True,
                        culling=False)

    # ── 박스 렌더 (30cm 정육면체, 연한 갈색) ─────────────────────────────────
    box_mesh = pv.Box(bounds=(
        box_cx - BOX_HALF, box_cx + BOX_HALF,
        box_cy - BOX_HALF, box_cy + BOX_HALF,
        box_cz - BOX_HALF, box_cz + BOX_HALF,
    ))
    pl.add_mesh(box_mesh, color='#C8A86B', opacity=0.85, smooth_shading=True)

    # ── 바닥 ─────────────────────────────────────────────────────────────────
    gp = pv.Plane(center=(px_val, 0.135, 0), direction=(0, 1, 0),
                  i_size=3.5, j_size=1.2)
    pl.add_mesh(gp, color='#2a2a2a')
    for gx in np.arange(round(px_val - 1.6, 1), px_val + 1.6, 0.2):
        pl.add_mesh(pv.Line((gx, 0.137, -0.6), (gx, 0.137, 0.6)),
                    color='#555555', line_width=1)

    # ── 조명 ─────────────────────────────────────────────────────────────────
    pl.add_light(pv.Light(position=(px_val + 2, 3, 4), intensity=0.55))
    pl.add_light(pv.Light(position=(px_val - 2, 2, -2), intensity=0.35))
    pl.add_light(pv.Light(light_type='headlight', intensity=0.45))

    # ── 카메라 ───────────────────────────────────────────────────────────────
    if view == 'sagittal':
        # 측면: z 방향에서 바라봄
        pl.camera_position = [
            (px_val, 0.9, 3.8),
            (px_val, 0.9, 0),
            (0, 1, 0),
        ]
    elif view == 'anterior':
        # 정면: x 방향에서 바라봄 (전방에서)
        pl.camera_position = [
            (px_val + 3.5, 0.9, 0),
            (px_val, 0.9, 0),
            (0, 1, 0),
        ]

    pl.camera.parallel_projection = True
    pl.camera.parallel_scale = 1.0

    out_path = str(TMP_DIR / f'carry_{tag}_f{frame_idx}_{view}.png')
    pl.screenshot(out_path)
    pl.close()
    return out_path


# ── 산출물 1: 5 frames × 2 views grid ────────────────────────────────────────
print('\n=== 산출물 1: 보행 주기 검증 grid ===')
VIEWS = [('sagittal', '측면 (Sagittal)'), ('anterior', '정면 (Anterior)')]

# 첫 프레임 warmup (첫 렌더 어두움 방지)
print('  Warmup render...')
_ = render_frame(FRAMES[0][0], 'sagittal', 'warmup')

rendered = {}
for fi, label in FRAMES:
    for view, _ in VIEWS:
        key = (fi, view)
        lbl_short = label.split('\n')[0]
        print(f'  Rendering {lbl_short} - {view}...')
        path = render_frame(fi, view, f'v{fi}')
        rendered[key] = path

# Grid 조합 (2행: sagittal / anterior, 5열: 5 시점)
fig, axes = plt.subplots(len(VIEWS), len(FRAMES), figsize=(22, 10))
fig.patch.set_facecolor('#0d0d0d')

for row, (view, view_label) in enumerate(VIEWS):
    for col, (fi, frame_label) in enumerate(FRAMES):
        ax = axes[row, col]
        img = mpimg.imread(rendered[(fi, view)])
        ax.imshow(img)
        ax.axis('off')
        if row == 0:
            ax.set_title(frame_label, color='white', fontsize=10, pad=4)
        if col == 0:
            ax.set_ylabel(view_label, color='#aaaaaa', fontsize=9, rotation=90,
                          labelpad=4)

fig.suptitle(
    'carry_walk_v2.mot — 보행 주기 검증 grid (VIZ-MIRROR 적용)\n'
    '왼팔=오른팔 z반사 렌더 (girdle 전체: clavicle+scapula+humerus+ulna+radius+hand)\n'
    '박스(30cm 20kg) z=0 정중앙 | armfix 모델 | culling=False',
    color='white', fontsize=11, weight='bold'
)
fig.tight_layout(rect=[0, 0, 1, 0.93])

grid_path = IMG_DIR / 'carry_walk_verify_grid.png'
fig.savefig(str(grid_path), dpi=110, facecolor='#0d0d0d',
            bbox_inches='tight')
plt.close(fig)
print(f'  SAVED: {grid_path}')


# ── 산출물 2: 관절각 시계열 grid ──────────────────────────────────────────────
print('\n=== 산출물 2: 관절각 시계열 grid ===')
t_arr = np.array(t_vec)

fig2, axes2 = plt.subplots(3, 3, figsize=(16, 12))
fig2.patch.set_facecolor('#f5f5f5')

# Row 0: 팔 관절 (상수 확인)
arm_plots = [
    ('shoulder_elv_r', 'shoulder_elv_l', 'Shoulder Elev (°)', 'upper arm elev'),
    ('elv_angle_r', 'elv_angle_l', 'Elv Angle (°)', 'arm plane of elev'),
    ('elbow_flexion_r', 'elbow_flexion_l', 'Elbow Flexion (°)', 'elbow flex'),
]
for col, (cr, cl, ylabel, title) in enumerate(arm_plots):
    ax = axes2[0, col]
    if cr in data:
        ax.plot(t_arr, data[cr], 'b-', lw=2, label='Right')
    if cl in data:
        ax.plot(t_arr, data[cl], 'r--', lw=2, label='Left')
    ax.set_title(f'ARM: {title}', fontsize=10, weight='bold')
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_xlabel('Time (s)', fontsize=8)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color='gray', lw=0.5)
    # 상수 여부 판정 표시
    for c, color in [(cr, 'blue'), (cl, 'red')]:
        if c in data:
            std_val = data[c].std()
            if std_val < 0.01:
                ax.text(0.98, 0.98 if color == 'blue' else 0.88,
                        f'{c.split("_")[-1].upper()} std={std_val:.4f} [CONST]',
                        transform=ax.transAxes, ha='right', va='top',
                        fontsize=7, color=color, alpha=0.8)

# Row 1: 하체 (보행 진동 확인)
lower_plots = [
    ('hip_flexion_r', 'hip_flexion_l', 'Hip Flexion (°)', 'hip flex/ext'),
    ('knee_angle_r', 'knee_angle_l', 'Knee Angle (°)', 'knee flex'),
    ('ankle_angle_r', 'ankle_angle_l', 'Ankle Angle (°)', 'ankle df/pf'),
]
for col, (cr, cl, ylabel, title) in enumerate(lower_plots):
    ax = axes2[1, col]
    if cr in data:
        ax.plot(t_arr, data[cr], 'b-', lw=2, label='Right')
    if cl in data:
        ax.plot(t_arr, data[cl], 'r--', lw=2, label='Left')
    ax.set_title(f'LOWER: {title}', fontsize=10, weight='bold')
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_xlabel('Time (s)', fontsize=8)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color='gray', lw=0.5)
    # 5 프레임 수직선
    for fi, fl in FRAMES:
        ax.axvline(t_vec[fi], color='orange', lw=0.8, alpha=0.5)

# Row 2: Lumbar lean-back + pelvis + shoulder_rot
misc_plots = [
    (['L5_S1_FE', 'L4_L5_FE', 'L3_L4_FE'], 'Lumbar FE (°)', 'lumbar FE (lean-back)'),
    (['pelvis_tilt', 'pelvis_list'], 'Pelvis (°)', 'pelvis tilt/list'),
    (['shoulder_rot_r', 'shoulder_rot_l'], 'Shoulder Rot (°)', 'shoulder internal rot'),
]
colors_misc = ['#e64b4b', '#3a9bff', '#44cc44', '#ff9900']
for col, (col_list, ylabel, title) in enumerate(misc_plots):
    ax = axes2[2, col]
    for k, c in enumerate(col_list):
        if c in data:
            ax.plot(t_arr, data[c], color=colors_misc[k % len(colors_misc)],
                    lw=2, label=c)
    ax.set_title(f'{title}', fontsize=10, weight='bold')
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_xlabel('Time (s)', fontsize=8)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color='gray', lw=0.5)
    for fi, fl in FRAMES:
        ax.axvline(t_vec[fi], color='orange', lw=0.8, alpha=0.5)

# lean-back 참고 값 표시
ax_lb = axes2[2, 0]
if 'L5_S1_FE' in data:
    mean_val = data['L5_S1_FE'].mean()
    ax_lb.axhline(mean_val, color='#e64b4b', lw=1, ls='--', alpha=0.6)
    ax_lb.text(t_arr[-1], mean_val + 0.2, f'mean={mean_val:.2f}°',
               ha='right', fontsize=8, color='#e64b4b')

fig2.suptitle(
    'carry_walk_v2.mot — 관절각 시계열 검증 (VIZ-MIRROR 적용 재렌더)\n'
    '팔 관절 상수(std~0) | 하체 보행 진동 | Lumbar lean-back 오프셋\n'
    '주황 수직선 = 검증 grid 5 시점 | shoulder_rot 크게 감소 확인',
    fontsize=12, weight='bold'
)
fig2.tight_layout(rect=[0, 0, 1, 0.92])

angles_path = IMG_DIR / 'carry_walk_angles.png'
fig2.savefig(str(angles_path), dpi=110, bbox_inches='tight')
plt.close(fig2)
print(f'  SAVED: {angles_path}')

print('\n=== 완료 ===')
print(f'산출물 1: {grid_path}')
print(f'산출물 2: {angles_path}')
