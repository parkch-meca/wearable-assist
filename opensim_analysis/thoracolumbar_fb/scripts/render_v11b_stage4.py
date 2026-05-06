"""
v11b Stage 4 Grid renderer
5 frames x 3 views = 15 snapshots + composite grid
DISPLAY=:1 pyvista off-screen rendering

Key v11 -> v11b change:
  Box now follows hand_center trajectory from box_motion_v11b_box.sto
  t<2.0: box fixed on ground (bottom y = -0.905)
  t>=2.0: box ascends with hands (carry phase)
  t=3.0: box_y ~ -0.579 (ascending)
  t=5.0: box_y ~ -0.049 (chest height carry)
"""

import sys
import os
import numpy as np
import pandas as pd

# OpenSim
sys.path.insert(0, '/home/sysop/miniconda3/envs/opensim/lib/python3.11/site-packages')
import opensim as osim

# PyVista
os.environ['DISPLAY'] = ':1'
import pyvista as pv

# Matplotlib for grid composition
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# ── Paths ──────────────────────────────────────────────────────────────────────
MODEL_PATH = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim'
MOT_PATH   = '/data/stoop_motion/box_motion_v11b.mot'
BOX_TRJ_PATH = '/data/stoop_motion/box_motion_v11b_box.sto'
OUT_DIR    = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box'

os.makedirs(OUT_DIR, exist_ok=True)

# ── Motion data ────────────────────────────────────────────────────────────────
with open(MOT_PATH, 'r') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'endheader' in line:
        header_end = i
        break
df = pd.read_csv(MOT_PATH, skiprows=header_end + 1, sep='\t')
print(f'Motion loaded: {len(df)} rows, t=[{df["time"].min():.2f}, {df["time"].max():.2f}]')

# ── Box trajectory ─────────────────────────────────────────────────────────────
with open(BOX_TRJ_PATH, 'r') as f:
    blines = f.readlines()
for i, line in enumerate(blines):
    if 'endheader' in line:
        box_header_end = i
        break
df_box = pd.read_csv(BOX_TRJ_PATH, skiprows=box_header_end + 1, sep='\t')
print(f'Box trajectory loaded: {len(df_box)} rows')
print(f'Box columns: {list(df_box.columns)}')

def get_box_center(t):
    """Return (cx, cy, cz) box center from trajectory at time t."""
    idx = (df_box['time'] - t).abs().idxmin()
    row = df_box.iloc[idx]
    # box.sto stores box center positions (tx, ty, tz = center)
    cx = float(row['box_tx'])
    cy = float(row['box_ty'])
    cz = float(row['box_tz'])
    return (cx, cy, cz)

# Print box positions at key frames for verification
print('\n=== Box positions at key frames ===')
for t_check in [0.0, 1.5, 2.0, 3.0, 5.0]:
    cx, cy, cz = get_box_center(t_check)
    print(f'  t={t_check:.1f}: center=({cx:.3f}, {cy:.3f}, {cz:.3f})')

# ── Model ──────────────────────────────────────────────────────────────────────
model = osim.Model(MODEL_PATH)
model.setUseVisualizer(False)
state = model.initSystem()
print(f'\nModel loaded: {model.getBodySet().getSize()} bodies')

# ── FK helper ─────────────────────────────────────────────────────────────────
def set_state_at_time(model, state, df, t):
    """Set model coordinates from mot file at time t."""
    row_idx = (df['time'] - t).abs().idxmin()
    row = df.iloc[row_idx]
    cs = model.getCoordinateSet()
    for j in range(cs.getSize()):
        c = cs.get(j)
        name = c.getName()
        if name in row.index:
            val = row[name]
            motion_type = c.getMotionType()
            if motion_type == 1:  # rotational
                c.setValue(state, np.deg2rad(float(val)))
            else:  # translational (2) or coupled
                c.setValue(state, float(val))
    model.realizePosition(state)

def get_body_pos(model, state, body_name):
    """Return [x, y, z] position of body COM in ground frame."""
    body = model.getBodySet().get(body_name)
    pos = body.getPositionInGround(state)
    return np.array([pos[0], pos[1], pos[2]])

# ── Skeleton connectivity ──────────────────────────────────────────────────────
SKELETON_PAIRS = [
    # Spine (bottom up)
    ('pelvis', 'lumbar5'),
    ('lumbar5', 'lumbar4'),
    ('lumbar4', 'lumbar3'),
    ('lumbar3', 'lumbar2'),
    ('lumbar2', 'lumbar1'),
    ('lumbar1', 'thoracic12'),
    ('thoracic12', 'thoracic6'),
    ('thoracic6', 'thoracic1'),
    ('thoracic1', 'head_neck'),
    # Right arm
    ('thoracic1', 'humerus_R'),
    ('humerus_R', 'ulna_R'),
    ('ulna_R', 'hand_R'),
    # Left arm
    ('thoracic1', 'humerus_L'),
    ('humerus_L', 'ulna_L'),
    ('ulna_L', 'hand_L'),
    # Right leg
    ('pelvis', 'femur_r'),
    ('femur_r', 'tibia_r'),
    ('tibia_r', 'calcn_r'),
    ('calcn_r', 'toes_r'),
    # Left leg
    ('pelvis', 'femur_l'),
    ('femur_l', 'tibia_l'),
    ('tibia_l', 'calcn_l'),
    ('calcn_l', 'toes_l'),
]

JOINT_SPHERES = [
    ('pelvis', 0.06),
    ('lumbar3', 0.04),
    ('thoracic1', 0.05),
    ('head_neck', 0.09),
    ('humerus_R', 0.04),
    ('humerus_L', 0.04),
    ('hand_R', 0.035),
    ('hand_L', 0.035),
    ('femur_r', 0.055),
    ('femur_l', 0.055),
    ('tibia_r', 0.045),
    ('tibia_l', 0.045),
    ('calcn_r', 0.04),
    ('calcn_l', 0.04),
]

# ── Box geometry ────────────────────────────────────────────────────────────────
# Box dimensions: 30cm(W) x 25cm(H) x 30cm(D) in meters
# BUT spec says 30x30x25 cm (W x H x D) — using that
BOX_W  = 0.30   # width  (z-axis, lateral)
BOX_H  = 0.30   # height (y-axis)
BOX_D  = 0.25   # depth  (x-axis, fore-aft)

def make_box_mesh(cx, cy, cz):
    """Build box mesh centered at (cx, cy, cz)."""
    box = pv.Box(bounds=(
        cx - BOX_D/2, cx + BOX_D/2,   # x: depth
        cy - BOX_H/2, cy + BOX_H/2,   # y: height
        cz - BOX_W/2, cz + BOX_W/2,   # z: width
    ))
    return box

# ── Build human mesh at given time ────────────────────────────────────────────
def build_human_meshes(model, state, df, t):
    """Return list of (mesh, color) tuples for human skeleton."""
    set_state_at_time(model, state, df, t)
    meshes = []

    # Cylinder sticks
    for (a_name, b_name) in SKELETON_PAIRS:
        try:
            pa = get_body_pos(model, state, a_name)
            pb = get_body_pos(model, state, b_name)
            length = np.linalg.norm(pb - pa)
            if length < 0.001:
                continue
            center = (pa + pb) / 2.0
            direction = (pb - pa) / length
            cyl = pv.Cylinder(center=center, direction=direction,
                               radius=0.018, height=length, resolution=12)
            meshes.append((cyl, '#3A6EA5'))  # blue-grey
        except Exception:
            pass

    # Joint spheres
    for (body_name, radius) in JOINT_SPHERES:
        try:
            pos = get_body_pos(model, state, body_name)
            sph = pv.Sphere(radius=radius, center=pos,
                             theta_resolution=12, phi_resolution=12)
            meshes.append((sph, '#2E86AB'))
        except Exception:
            pass

    return meshes

# ── Camera definitions ─────────────────────────────────────────────────────────
# OpenSim ground: X=forward, Y=up, Z=lateral(right)

VIEWS = {
    'sagittal': {
        # Right side view (z+)
        'position': (0.0, 0.4, 4.0),
        'focal_point': (0.0, 0.0, 0.0),
        'up': (0.0, 1.0, 0.0),
        'label': 'Sagittal (Right)',
    },
    'anterior': {
        # Front view (x-)
        'position': (-4.0, 0.4, 0.0),
        'focal_point': (0.0, 0.0, 0.0),
        'up': (0.0, 1.0, 0.0),
        'label': 'Anterior (Front)',
    },
    '3quarter': {
        # 3/4 view
        'position': (-2.2, 0.8, 3.0),
        'focal_point': (0.2, 0.0, 0.0),
        'up': (0.0, 1.0, 0.0),
        'label': '3-Quarter View',
    },
}

# ── Frame timing ───────────────────────────────────────────────────────────────
FRAMES = [
    (0.0,  'Quiet Standing'),
    (1.5,  'Eccentric Mid'),
    (2.0,  'Grasp Peak'),
    (3.0,  'Concentric Mid'),
    (5.0,  'Carry Final'),
]

# ── Render single frame + view ─────────────────────────────────────────────────
def render_frame_view(model, state, df, t, view_key, out_path):
    """Render one frame at one view with dynamic box position, save PNG."""
    view = VIEWS[view_key]

    # Get dynamic box center from trajectory
    bx, by, bz = get_box_center(t)
    print(f'    box center at t={t:.1f}: ({bx:.3f}, {by:.3f}, {bz:.3f})')

    pl = pv.Plotter(off_screen=True, window_size=(800, 800))
    pl.set_background('#F8F8F8')  # light grey

    # Ground plane (fixed at y=-0.905)
    ground = pv.Plane(center=(0.1, -0.905, 0),
                      direction=(0, 1, 0),
                      i_size=2.5, j_size=1.5)
    pl.add_mesh(ground, color='#CCCCCC', opacity=0.5)

    # Box — dynamic position from trajectory
    box_mesh = make_box_mesh(bx, by, bz)
    pl.add_mesh(box_mesh, color='#C17F24', opacity=0.88,
                show_edges=True, edge_color='#7A5000', line_width=1.5)

    # Human meshes
    human_meshes = build_human_meshes(model, state, df, t)
    for (mesh, color) in human_meshes:
        pl.add_mesh(mesh, color=color, smooth_shading=True)

    # Camera
    pl.camera.position = view['position']
    pl.camera.focal_point = view['focal_point']
    pl.camera.up = view['up']

    # Lighting
    pl.enable_lightkit()
    pl.add_light(pv.Light(position=(2, 5, 3),
                           focal_point=(0, 0, 0), intensity=0.8))

    pl.screenshot(out_path, transparent_background=False)
    pl.close()
    print(f'  Saved: {os.path.basename(out_path)}')

# ── Main render loop ───────────────────────────────────────────────────────────
print('\n=== Stage 4 rendering: 5 frames x 3 views ===')
frame_paths = {}   # {(t, view_key): path}

for (t, label) in FRAMES:
    print(f'\nFrame t={t:.1f} [{label}]')
    for view_key in ['sagittal', 'anterior', '3quarter']:
        fname = f'v11b_stage4_t{t:.1f}_{view_key}.png'
        out_path = os.path.join(OUT_DIR, fname)
        render_frame_view(model, state, df, t, view_key, out_path)
        frame_paths[(t, view_key)] = out_path

print('\n=== All 15 frames rendered. Compositing grid... ===')

# ── Composite 5x3 grid ─────────────────────────────────────────────────────────
N_ROWS = len(FRAMES)       # 5
N_COLS = len(VIEWS)        # 3
FIG_W  = 4.0 * N_COLS     # inches per panel
FIG_H  = 4.2 * N_ROWS

fig, axes = plt.subplots(N_ROWS, N_COLS, figsize=(FIG_W, FIG_H), dpi=150)
fig.patch.set_facecolor('#FFFFFF')

view_order = ['sagittal', 'anterior', '3quarter']

# Phase annotation colors
PHASE_COLORS = {
    0.0: '#333333',    # standing - dark grey
    1.5: '#1565C0',    # eccentric - blue
    2.0: '#CC2222',    # grasp peak - red (highlight)
    3.0: '#2E7D32',    # concentric - green
    5.0: '#6A1B9A',    # carry - purple (new in v11b)
}
PHASE_BOLD = {0.0: 'normal', 1.5: 'normal', 2.0: 'bold', 3.0: 'bold', 5.0: 'bold'}

# Box phase annotation
BOX_PHASE = {
    0.0: 'box: ground',
    1.5: 'box: ground',
    2.0: 'box: ground (grasp)',
    3.0: 'box: ASCENDING',   # key v11b improvement
    5.0: 'box: chest-high',  # key v11b improvement
}

for row_i, (t, label) in enumerate(FRAMES):
    for col_j, view_key in enumerate(view_order):
        ax = axes[row_i, col_j]
        img_path = frame_paths[(t, view_key)]

        if os.path.exists(img_path):
            img = mpimg.imread(img_path)
            ax.imshow(img)
        else:
            ax.set_facecolor('#DDDDDD')
            ax.text(0.5, 0.5, 'MISSING', ha='center', va='center',
                    transform=ax.transAxes, fontsize=12, color='red')

        ax.axis('off')

        # Column header (top row only)
        if row_i == 0:
            ax.set_title(VIEWS[view_key]['label'], fontsize=13,
                         fontweight='bold', pad=6, color='#222222')

        # Row label (left column)
        if col_j == 0:
            color = PHASE_COLORS[t]
            weight = PHASE_BOLD[t]
            box_note = BOX_PHASE[t]
            ax.set_ylabel(
                f't={t:.1f}s\n{label}\n({box_note})',
                fontsize=9,
                rotation=0, labelpad=80, va='center',
                color=color, fontweight=weight
            )

fig.suptitle(
    'Box Motion v11b — Stage 4 Visual Verification\n'
    'lift + carry + box trajectory  |  31/31 quantitative PASS\n'
    'NEW: box follows hand trajectory (t>=2.0)',
    fontsize=13, fontweight='bold', y=1.005, color='#111111'
)

plt.tight_layout(rect=[0.14, 0, 1, 1])

grid_path = os.path.join(OUT_DIR, 'box_motion_v11b_stage4_grid.png')
plt.savefig(grid_path, bbox_inches='tight', dpi=150, facecolor='white')
plt.close()
print(f'\nGrid saved: {grid_path}')
print('Done.')
