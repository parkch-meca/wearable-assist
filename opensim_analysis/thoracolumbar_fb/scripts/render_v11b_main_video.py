"""
Box motion v11b — Main Video Render (2-panel: sagittal + 3-quarter)

v11b adopted: lift + carry + box trajectory, 31/31 PASS, user-verified 8/8.

Layout: side-by-side
  Left panel  (960 x 720): Sagittal (right-side view)
  Right panel (960 x 720): 3-Quarter view
Total resolution: 1920 x 720 (HD wide)

Box trajectory: box_motion_v11b_box.sto
  t < 2.0:  ground fixed   (center_y = -0.755 m)
  t >= 2.0: hand_center tracking (ascending to ~-0.049 at t=5.0)

Outputs
  /data/opensim_results/box_motion_v11b/box_motion_v11b_main.mp4
  /data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/videos/box_motion_v11b_main.mp4

USAGE:
  DISPLAY=:1 /home/sysop/miniconda3/envs/opensim/bin/python render_v11b_main_video.py [--preview]
  --preview  -> render 3 key frames only, skip video encoding
"""

import os
import sys
import time
import shutil
import subprocess
import argparse
import numpy as np
import pandas as pd

os.environ['DISPLAY'] = ':1'

sys.path.insert(0, '/home/sysop/miniconda3/envs/opensim/lib/python3.11/site-packages')
import opensim as osim
import pyvista as pv

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image, ImageDraw, ImageFont

# ── Paths ──────────────────────────────────────────────────────────────────────
MODEL_PATH = (
    '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
    'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim'
)
MOT_PATH     = '/data/stoop_motion/box_motion_v11b.mot'
BOX_TRJ_PATH = '/data/stoop_motion/box_motion_v11b_box.sto'

OUT_DIR_DATA = '/data/opensim_results/video'
OUT_DIR_REPO = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/videos'
FRAME_DIR    = '/tmp/v11b_frames'
PREVIEW_DIR  = '/tmp/v11b_preview'

os.makedirs(OUT_DIR_DATA, exist_ok=True)
os.makedirs(OUT_DIR_REPO, exist_ok=True)
os.makedirs(FRAME_DIR,    exist_ok=True)
os.makedirs(PREVIEW_DIR,  exist_ok=True)

# ── Render spec ────────────────────────────────────────────────────────────────
FPS        = 30
T_TOTAL    = 5.0
N_FRAMES   = int(FPS * T_TOTAL) + 1  # 151

PANEL_W    = 960
PANEL_H    = 720
TOTAL_W    = PANEL_W * 2   # 1920
TOTAL_H    = PANEL_H       # 720 (no bottom bar — clean side-by-side)

# ── Box geometry (30 W x 30 H x 25 D cm) ──────────────────────────────────────
BOX_W = 0.30   # lateral (z)
BOX_H = 0.30   # vertical (y)
BOX_D = 0.25   # fore-aft (x)

# ── Skeleton connectivity ──────────────────────────────────────────────────────
SKELETON_PAIRS = [
    # Spine
    ('pelvis',     'lumbar5'),
    ('lumbar5',    'lumbar4'),
    ('lumbar4',    'lumbar3'),
    ('lumbar3',    'lumbar2'),
    ('lumbar2',    'lumbar1'),
    ('lumbar1',    'thoracic12'),
    ('thoracic12', 'thoracic6'),
    ('thoracic6',  'thoracic1'),
    ('thoracic1',  'head_neck'),
    # Right arm
    ('thoracic1',  'humerus_R'),
    ('humerus_R',  'ulna_R'),
    ('ulna_R',     'hand_R'),
    # Left arm
    ('thoracic1',  'humerus_L'),
    ('humerus_L',  'ulna_L'),
    ('ulna_L',     'hand_L'),
    # Right leg
    ('pelvis',     'femur_r'),
    ('femur_r',    'tibia_r'),
    ('tibia_r',    'calcn_r'),
    ('calcn_r',    'toes_r'),
    # Left leg
    ('pelvis',     'femur_l'),
    ('femur_l',    'tibia_l'),
    ('tibia_l',    'calcn_l'),
    ('calcn_l',    'toes_l'),
]

JOINT_SPHERES = [
    ('pelvis',     0.060),
    ('lumbar3',    0.040),
    ('thoracic1',  0.050),
    ('head_neck',  0.090),
    ('humerus_R',  0.040),
    ('humerus_L',  0.040),
    ('hand_R',     0.035),
    ('hand_L',     0.035),
    ('femur_r',    0.055),
    ('femur_l',    0.055),
    ('tibia_r',    0.045),
    ('tibia_l',    0.045),
    ('calcn_r',    0.040),
    ('calcn_l',    0.040),
]

BONE_COLOR  = '#3A6EA5'
JOINT_COLOR = '#2E86AB'

# ── Camera views ───────────────────────────────────────────────────────────────
# OpenSim ground: X=forward, Y=up, Z=right
VIEWS = {
    'sagittal': {
        'position':    (0.0, 0.25, 4.5),
        'focal_point': (0.1, 0.05, 0.0),
        'up':          (0.0, 1.0,  0.0),
        'label':       'Sagittal (Right Side)',
    },
    '3quarter': {
        'position':    (-2.0, 0.8, 3.5),
        'focal_point': (0.2,  0.0, 0.0),
        'up':          (0.0,  1.0, 0.0),
        'label':       '3-Quarter View',
    },
}

# ── Phase labels ───────────────────────────────────────────────────────────────
def phase_info(t):
    if   t <  0.5: return 'Standing',          '#555555'
    elif t <= 2.0: return 'Eccentric (lower)', '#1565C0'
    elif t <= 2.5: return 'Grasp',             '#CC2222'
    elif t <= 4.0: return 'Concentric (lift)', '#2E7D32'
    else:          return 'Carry',             '#6A1B9A'


# ── Data loading ───────────────────────────────────────────────────────────────
def load_mot(path):
    with open(path) as f:
        lines = f.readlines()
    for i, l in enumerate(lines):
        if 'endheader' in l:
            skip = i + 1
            break
    df = pd.read_csv(path, skiprows=skip, sep='\t')
    print(f'MOT loaded: {len(df)} rows, t=[{df.time.min():.2f}, {df.time.max():.2f}]')
    return df


def load_box_trj(path):
    with open(path) as f:
        lines = f.readlines()
    for i, l in enumerate(lines):
        if 'endheader' in l:
            skip = i + 1
            break
    df = pd.read_csv(path, skiprows=skip, sep='\t')
    print(f'Box TRJ loaded: {len(df)} rows')
    return df


def get_box_center(df_box, t):
    idx = (df_box['time'] - t).abs().idxmin()
    row = df_box.iloc[idx]
    return float(row['box_tx']), float(row['box_ty']), float(row['box_tz'])


# ── OpenSim model helpers ──────────────────────────────────────────────────────
def set_state_at_time(model, state, df, t):
    row_idx = (df['time'] - t).abs().idxmin()
    row = df.iloc[row_idx]
    cs = model.getCoordinateSet()
    for j in range(cs.getSize()):
        c = cs.get(j)
        name = c.getName()
        if name in row.index:
            val = row[name]
            if c.getMotionType() == 1:   # rotational
                c.setValue(state, np.deg2rad(float(val)))
            else:                        # translational
                c.setValue(state, float(val))
    model.realizePosition(state)


def get_body_pos(model, state, body_name):
    body = model.getBodySet().get(body_name)
    pos  = body.getPositionInGround(state)
    return np.array([pos[0], pos[1], pos[2]])


# ── Mesh builders ──────────────────────────────────────────────────────────────
def make_box_mesh(cx, cy, cz):
    return pv.Box(bounds=(
        cx - BOX_D/2, cx + BOX_D/2,
        cy - BOX_H/2, cy + BOX_H/2,
        cz - BOX_W/2, cz + BOX_W/2,
    ))


def build_human_meshes(model, state, df, t):
    set_state_at_time(model, state, df, t)
    meshes = []
    for (a, b) in SKELETON_PAIRS:
        try:
            pa = get_body_pos(model, state, a)
            pb = get_body_pos(model, state, b)
            L  = np.linalg.norm(pb - pa)
            if L < 0.001:
                continue
            ctr = (pa + pb) / 2.0
            d   = (pb - pa) / L
            cyl = pv.Cylinder(center=ctr, direction=d,
                               radius=0.018, height=L, resolution=12)
            meshes.append((cyl, BONE_COLOR))
        except Exception:
            pass
    for (bname, r) in JOINT_SPHERES:
        try:
            pos = get_body_pos(model, state, bname)
            sph = pv.Sphere(radius=r, center=pos,
                             theta_resolution=12, phi_resolution=12)
            meshes.append((sph, JOINT_COLOR))
        except Exception:
            pass
    return meshes


# ── Single panel render ────────────────────────────────────────────────────────
def render_panel(model, state, df, df_box, t, view_key, size=(PANEL_W, PANEL_H)):
    view = VIEWS[view_key]
    bx, by, bz = get_box_center(df_box, t)

    pl = pv.Plotter(off_screen=True, window_size=list(size))
    pl.set_background('#1C1C2E')   # dark navy — clean for video

    # Ground plane at y = -0.905 (foot level)
    gnd = pv.Plane(center=(0.1, -0.905, 0), direction=(0, 1, 0),
                   i_size=3.0, j_size=2.0)
    pl.add_mesh(gnd, color='#3A3A4A', opacity=0.6,
                show_edges=True, edge_color='#555566', line_width=0.8)

    # Box
    box_mesh = make_box_mesh(bx, by, bz)
    pl.add_mesh(box_mesh, color='#D4880A', opacity=0.92,
                show_edges=True, edge_color='#7A5000', line_width=1.5)

    # Human skeleton
    human_meshes = build_human_meshes(model, state, df, t)
    for (mesh, color) in human_meshes:
        pl.add_mesh(mesh, color=color, smooth_shading=True)

    # Camera
    pl.camera.position    = view['position']
    pl.camera.focal_point = view['focal_point']
    pl.camera.up          = view['up']

    pl.enable_lightkit()
    pl.add_light(pv.Light(position=(3, 6, 4),
                           focal_point=(0, 0, 0), intensity=0.9))

    img = pl.screenshot(None, return_img=True)   # returns numpy array
    pl.close()
    return img


# ── Overlay: phase label + time bar ───────────────────────────────────────────
def add_overlay(img_left, img_right, t, fi, n_frames):
    """
    Composite left + right panels and add:
    - Top-left: view labels
    - Bottom bar (40px): phase label + time progress
    """
    W = TOTAL_W
    H_BAR = 48
    H_TOTAL = TOTAL_H + H_BAR

    canvas = Image.new('RGB', (W, H_TOTAL), (10, 10, 20))

    # Paste panels
    left  = Image.fromarray(img_left)
    right = Image.fromarray(img_right)
    canvas.paste(left,  (0,       0))
    canvas.paste(right, (PANEL_W, 0))

    # Center divider line
    draw = ImageDraw.Draw(canvas)
    draw.line([(PANEL_W, 0), (PANEL_W, TOTAL_H)], fill='#555566', width=2)

    # View labels (top corners, small)
    try:
        font_sm = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
        font_md = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
    except IOError:
        font_sm = ImageFont.load_default()
        font_md = font_sm

    draw.text((12, 10), 'Sagittal (Right)',  font=font_sm, fill='#AAAACC')
    draw.text((PANEL_W + 12, 10), '3-Quarter View', font=font_sm, fill='#AAAACC')

    # Bottom bar
    bar_y = TOTAL_H
    draw.rectangle([(0, bar_y), (W, H_TOTAL)], fill=(18, 18, 30))

    # Progress bar
    bar_x0, bar_x1 = 14, W - 14
    bar_my = bar_y + 14
    bar_h  = 8
    # Phase color segments
    phase_segs = [
        (0.0, 0.5,  '#555555'),
        (0.5, 2.0,  '#1565C0'),
        (2.0, 2.5,  '#CC2222'),
        (2.5, 4.0,  '#2E7D32'),
        (4.0, 5.0,  '#6A1B9A'),
    ]
    bar_len = bar_x1 - bar_x0
    for t0, t1, col in phase_segs:
        x0 = int(bar_x0 + bar_len * t0 / T_TOTAL)
        x1 = int(bar_x0 + bar_len * t1 / T_TOTAL)
        r, g, b = int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)
        draw.rectangle([(x0, bar_my), (x1, bar_my + bar_h)],
                        fill=(r, g, b, 160))

    # Current time marker
    x_now = int(bar_x0 + bar_len * t / T_TOTAL)
    draw.line([(x_now, bar_my - 4), (x_now, bar_my + bar_h + 4)],
               fill='white', width=3)

    # Phase text + time
    phase_name, phase_col = phase_info(t)
    r, g, b = int(phase_col[1:3], 16), int(phase_col[3:5], 16), int(phase_col[5:7], 16)
    txt = f'{phase_name}   t = {t:.2f} s'
    draw.text((W // 2 - 120, bar_y + 26), txt, font=font_md, fill=(r, g, b))

    return np.array(canvas)


# ── Preview: 3 key frames ──────────────────────────────────────────────────────
def render_preview(model, state, df, df_box):
    print('\n=== PREVIEW: t=0.0, t=2.5, t=5.0 ===')
    out_paths = []
    for t in [0.0, 2.5, 5.0]:
        img_l = render_panel(model, state, df, df_box, t, 'sagittal')
        img_r = render_panel(model, state, df, df_box, t, '3quarter')
        fi    = int(t * FPS)
        comp  = add_overlay(img_l, img_r, t, fi, N_FRAMES)
        out   = os.path.join(PREVIEW_DIR, f'v11b_preview_t{t:.1f}.png')
        Image.fromarray(comp).save(out)
        print(f'  Saved: {out}')
        out_paths.append(out)
    print('\nPreview done. Please verify camera/box before full render.')
    return out_paths


# ── Full video render ──────────────────────────────────────────────────────────
def render_full(model, state, df, df_box):
    print(f'\n=== FULL RENDER: {N_FRAMES} frames @ {FPS} fps ===')

    # Clear frame dir
    if os.path.exists(FRAME_DIR):
        shutil.rmtree(FRAME_DIR)
    os.makedirs(FRAME_DIR)

    t0 = time.time()
    for fi in range(N_FRAMES):
        t = fi / FPS
        img_l = render_panel(model, state, df, df_box, t, 'sagittal')
        img_r = render_panel(model, state, df, df_box, t, '3quarter')
        comp  = add_overlay(img_l, img_r, t, fi, N_FRAMES)
        frame_path = os.path.join(FRAME_DIR, f'frame_{fi:04d}.png')
        Image.fromarray(comp).save(frame_path)

        if fi % 15 == 0 or fi == N_FRAMES - 1:
            elapsed = time.time() - t0
            eta     = elapsed / (fi + 1) * (N_FRAMES - fi - 1)
            print(f'  [{fi+1:3d}/{N_FRAMES}] t={t:.2f}s  '
                  f'elapsed={elapsed:.1f}s  ETA={eta:.1f}s')

    print(f'\nAll {N_FRAMES} frames done in {time.time()-t0:.1f}s')

    # ffmpeg encode
    out_main = os.path.join(OUT_DIR_DATA, 'box_v11b_main.mp4')
    cmd = [
        'ffmpeg', '-y', '-loglevel', 'warning',
        '-framerate', str(FPS),
        '-i', os.path.join(FRAME_DIR, 'frame_%04d.png'),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '18',
        '-preset', 'medium',
        '-movflags', '+faststart',
        out_main,
    ]
    print(f'\nEncoding: {out_main}')
    subprocess.run(cmd, check=True)
    size_mb = os.path.getsize(out_main) / 1024 / 1024
    print(f'Wrote: {out_main}  ({size_mb:.1f} MB)')

    # Repo copy (same file — mp4 is gitignored but keep in docs/videos)
    out_repo = os.path.join(OUT_DIR_REPO, 'box_v11b_main.mp4')
    shutil.copy2(out_main, out_repo)
    print(f'Repo copy: {out_repo}')

    return out_main, out_repo


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', action='store_true',
                        help='Render 3 preview frames only (no video encoding)')
    args = parser.parse_args()

    print('Loading motion data...')
    df     = load_mot(MOT_PATH)
    df_box = load_box_trj(BOX_TRJ_PATH)

    # Print box positions for verification
    print('\nBox positions at key times:')
    for t in [0.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
        bx, by, bz = get_box_center(df_box, t)
        print(f'  t={t:.1f}: ({bx:.3f}, {by:.3f}, {bz:.3f})')

    print('\nLoading OpenSim model...')
    model = osim.Model(MODEL_PATH)
    model.setUseVisualizer(False)
    state = model.initSystem()
    print(f'Model: {model.getBodySet().getSize()} bodies')

    if args.preview:
        paths = render_preview(model, state, df, df_box)
        print('\n=== Preview paths ===')
        for p in paths:
            print(f'  {p}')
    else:
        out_main, out_repo = render_full(model, state, df, df_box)
        print('\n=== Output ===')
        print(f'  Main:      {out_main}')
        print(f'  Repo copy: {out_repo}')


if __name__ == '__main__':
    main()
