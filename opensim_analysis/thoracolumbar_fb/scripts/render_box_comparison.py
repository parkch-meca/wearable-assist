"""Side-by-side box-lift render: 0N suit (left) vs 200N suit (right).

20 kg box drawn (brown) between hands while held (t >= 2.0 s). 3-second motion,
30 fps -> 91 frames. Same camera as stoop_suit_comparison_v2.

Modes:
  python render_box_comparison.py preview   # 3 snapshot frames
  python render_box_comparison.py video     # full mp4
"""
import os, sys, shutil, subprocess, time
os.environ.setdefault('DISPLAY', ':1')
from pathlib import Path
import numpy as np
import opensim as osim
import pyvista as pv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim'
GEOM_DIR = Path('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry')
MOT = '/data/stoop_motion/stoop_box20kg_v2.mot'
SO_LEFT  = '/data/stoop_results/box_lift_v2/B_suit0/so_B_suit0_StaticOptimization_activation.sto'
SO_RIGHT = '/data/stoop_results/box_lift_v2/B_suit200/so_B_suit200_StaticOptimization_activation.sto'

VIDEO_DIR = Path('/data/opensim_results/video'); VIDEO_DIR.mkdir(parents=True, exist_ok=True)
FRAME_DIR = Path('/tmp/stoop_box_frames'); FRAME_DIR.mkdir(parents=True, exist_ok=True)
OUT_MP4 = VIDEO_DIR / 'stoop_box_comparison_v2.mp4'
OUT_PREVIEW = Path('/data/opensim_results/box_lift_preview_v6.png')

FPS = 30
T_TOTAL = 3.0
N_FRAMES = int(FPS * T_TOTAL) + 1  # 91
ES_PREFIXES = ('IL_', 'LTpT_', 'LTpL_')
ACT_MAX = 0.25
RES_W, RES_H = 1920, 1080
TOP_H = 820

# Suit + box schedule (mirrors run_box_so.py)
BOX_MASS_KG = 20.4   # 2 * 100 N / 9.8
BOX_START_T = 2.0
T_PEAK_NM = 24.0     # 200 N * 0.12 m
def alpha_spine(t):
    if t < 1.0:  return 0.0
    if t <= 2.0: return (1.0 - np.cos(np.pi * (t - 1.0))) / 2.0
    if t <= 3.0: return (1.0 + np.cos(np.pi * (t - 2.0))) / 2.0
    return 0.0

# Box geometry
BOX_SIZE = (0.20, 0.15, 0.20)   # x, y, z (m) — width, height, depth
# Forward offset added to hand-center position after grasp (avoids torso clipping)
BOX_HAND_X_OFFSET = 0.08
# Floor pose (before grasp): box bottom sits exactly on rendered grid y=−0.905.
# Box center = grid_y + BOX_SIZE.y/2 = −0.905 + 0.075 = −0.83.
# Known limitation: hand at t=2.0 is at y=−0.606 (see KNOWN_LIMITATIONS.md) →
# 15 cm vertical pop at grasp. Accepted as interim until Moco motion regen.
BOX_FLOOR_X = 0.706   # hand_center.x(t=2.0) + BOX_HAND_X_OFFSET
BOX_FLOOR_Y = -0.905 + BOX_SIZE[1] / 2.0   # = -0.83, bottom on grid
BOX_FLOOR_Z = -0.032  # hand_center.z(t=2.0)


# ---------------- model helpers ----------------
def transform_to_mat(T):
    R, p = T.R(), T.p()
    M = np.eye(4)
    for i in range(3):
        for j in range(3): M[i, j] = R.get(i, j)
        M[i, 3] = p.get(i)
    return M


def collect_meshes(model):
    out = []
    for c in list(model.getComponentsList()):
        if c.getConcreteClassName() != 'Mesh':
            continue
        mesh = osim.Mesh.safeDownCast(c)
        mf = mesh.get_mesh_file()
        if not mf:
            continue
        p = GEOM_DIR / mf
        if not p.exists():
            continue
        sf = mesh.get_scale_factors()
        out.append({'path': str(p), 'frame': mesh.getFrame().getAbsolutePathString(),
                    'scale': (sf.get(0), sf.get(1), sf.get(2))})
    return out


def apply_motion(model, state, mot_tbl, t, in_degrees=True):
    times = list(mot_tbl.getIndependentColumn())
    idx = min(range(len(times)), key=lambda i: abs(times[i] - t))
    row = mot_tbl.getRowAtIndex(idx)
    labels = list(mot_tbl.getColumnLabels())
    cs = model.getCoordinateSet()
    for ci, name in enumerate(labels):
        if not cs.contains(name):
            continue
        v = row[ci]
        c = cs.get(name)
        if c.getMotionType() == 1 and in_degrees:
            v = np.radians(v)
        c.setValue(state, v, False)
    model.assemble(state)
    model.realizePosition(state)


def read_activation_table(path):
    tbl = osim.TimeSeriesTable(path)
    labels = list(tbl.getColumnLabels())
    t = np.array(list(tbl.getIndependentColumn()))
    data = np.zeros((tbl.getNumRows(), tbl.getNumColumns()))
    for i in range(tbl.getNumRows()):
        row = tbl.getRowAtIndex(i)
        for j in range(tbl.getNumColumns()):
            data[i, j] = row[j]
    return t, labels, data


def activations_at(t_series, data, t, labels, muscle_names):
    idx = int(np.argmin(np.abs(t_series - t)))
    return {n: data[idx, labels.index(n)] if n in labels else 0.0 for n in muscle_names}


def hand_center_ground(model, state):
    """Midpoint between hand_R and hand_L body origins, in ground."""
    bR = model.getBodySet().get('hand_R')
    bL = model.getBodySet().get('hand_L')
    pR = bR.getTransformInGround(state).p()
    pL = bL.getTransformInGround(state).p()
    c = np.array([(pR.get(i) + pL.get(i)) * 0.5 for i in range(3)])
    return c


def box_center(model, state, t):
    """Box center position; post-grasp = hand rests on top (box top at hand_y)."""
    if t < BOX_START_T - 1e-6:
        return np.array([BOX_FLOOR_X, BOX_FLOOR_Y, BOX_FLOOR_Z]), False
    hc = hand_center_ground(model, state)
    # Hand on top of box → box center BELOW hand by half the box height
    return np.array([hc[0] + BOX_HAND_X_OFFSET,
                     hc[1] - BOX_SIZE[1] / 2.0,
                     hc[2]]), True


def build_bone_actor(plotter, model, state, meshes, color='ivory'):
    frame_cache = {}
    for mi in meshes:
        fp = mi['frame']
        if fp not in frame_cache:
            frame_cache[fp] = model.getComponent(fp)
    for mi in meshes:
        try:
            surf = pv.read(mi['path'])
        except Exception:
            continue
        sx, sy, sz = mi['scale']
        if (sx, sy, sz) != (1.0, 1.0, 1.0):
            surf = surf.scale([sx, sy, sz], inplace=False)
        M = transform_to_mat(frame_cache[mi['frame']].getTransformInGround(state))
        surf = surf.transform(M, inplace=False)
        plotter.add_mesh(surf, color=color, opacity=1.0, smooth_shading=True,
                         specular=0.2, specular_power=10)


def build_muscle_polydata(model, state, muscle_names, activations):
    all_pts = []; cells = []; scalars = []
    muscles = model.getMuscles()
    name_to_m = {muscles.get(i).getName(): muscles.get(i) for i in range(muscles.getSize())}
    for name in muscle_names:
        m = name_to_m.get(name)
        if m is None:
            continue
        path = m.getGeometryPath()
        pp_set = path.getCurrentPath(state)
        pts = []
        for k in range(pp_set.getSize()):
            pp = pp_set.get(k)
            loc = pp.getLocationInGround(state)
            pts.append([loc.get(0), loc.get(1), loc.get(2)])
        if len(pts) < 2:
            continue
        start = len(all_pts)
        all_pts.extend(pts)
        a = float(activations.get(name, 0.0))
        for i in range(len(pts) - 1):
            cells.append(2); cells.append(start + i); cells.append(start + i + 1)
            scalars.append(a)
    if not all_pts:
        return None
    pd = pv.PolyData()
    pd.points = np.array(all_pts, dtype=float)
    pd.lines = np.array(cells, dtype=np.int64)
    pd.cell_data['activation'] = np.array(scalars, dtype=float)
    return pd


def phase_label(t):
    if t < 1.0: return 'reach down (no box)', 'gray'
    if t < 2.0: return 'grasp & ramp suit', 'tab:orange'
    if t <= 2.5: return 'lift 20 kg box (peak)', 'tab:red'
    if t <= 3.0: return 'stand up with box', 'tab:green'
    return 'idle', 'gray'


# ---------------- 3D panel render ----------------
def render_3d_panel(model, state, meshes, muscle_names, acts_l, acts_r, t,
                    out_path):
    pv.global_theme.background = '#1a1a1a'
    pv.global_theme.lighting = True
    pl = pv.Plotter(shape=(1, 2), window_size=(1920, TOP_H), off_screen=True,
                    border=False)
    bc, grasped = box_center(model, state, t)

    for col, (tag, acts, badge) in enumerate([
        ('no suit  —  0 N · 20 kg box',  acts_l, '#cccccc'),
        ('SMA suit  —  200 N (24 N·m peak) · 20 kg box', acts_r, '#ff6060'),
    ]):
        pl.subplot(0, col)
        build_bone_actor(pl, model, state, meshes, color='ivory')
        pd = build_muscle_polydata(model, state, muscle_names, acts)
        if pd is not None:
            pl.add_mesh(pd, scalars='activation', cmap='coolwarm',
                        clim=[0, ACT_MAX], line_width=3.0, show_scalar_bar=False)
        # Brown box — always visible; on floor before grasp, tracks hands after
        box = pv.Cube(center=(bc[0], bc[1], bc[2]),
                      x_length=BOX_SIZE[0], y_length=BOX_SIZE[1],
                      z_length=BOX_SIZE[2])
        pl.add_mesh(box, color='#8b5a2b', opacity=1.0, smooth_shading=False,
                    specular=0.1, specular_power=5, show_edges=True,
                    edge_color='#5a3a1a', line_width=1.5)
        pl.add_point_labels(np.array([[bc[0], bc[1] + BOX_SIZE[1] * 0.7, bc[2]]]),
                            ['20 kg'], font_size=13,
                            text_color='white' if grasped else '#ffd060',
                            point_size=1, shape=None, always_visible=True,
                            bold=True)
        # Floor
        # Floor grid bumped to opacity 0.75 (was 0.4) to visually occlude
        # feet-below-grid during peak bend (motion lacks ground contact constraint).
        floor = pv.Plane(center=(0.1, -0.905, 0.0), direction=(0, 1, 0),
                         i_size=2.5, j_size=2.5)
        pl.add_mesh(floor, color='#444444', opacity=0.75, show_edges=True,
                    edge_color='#666666', line_width=1)
        # Camera rotated +35° azimuth (front-right 3/4) to reduce visibility of
        # motion's ground-contact clipping (feet go 15 cm below grid at peak bend).
        pl.camera_position = [
            (2.756, 0.25, 1.385),   # was (1.5, 0.25, 2.6) — +35° rotation about focal
            (0.2, -0.10, 0.0),
            (0.0, 1.0, 0.0),
        ]
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale = 1.05
        pl.add_text(tag, font_size=13, color=badge, position='upper_left')
    pl.screenshot(str(out_path))
    pl.close()


# ---------------- bottom overlay ----------------
def composite_frame(img_3d_path, out_path, t,
                    es_l_peak, es_r_peak, es_l_mean, es_r_mean,
                    torque_now_nm, box_on):
    """Overlay: primary metric = ES peak (max across ES muscles);
    secondary = ES mean (across 76 muscles). Bar scale 0–100%."""
    img3d = Image.open(img_3d_path).convert('RGB')
    W, H = RES_W, RES_H
    canvas = Image.new('RGB', (W, H), (240, 240, 240))
    img3d_r = img3d.resize((W, TOP_H), Image.LANCZOS)
    canvas.paste(img3d_r, (0, 0))

    # center divider
    draw = ImageDraw.Draw(canvas)
    draw.line([(W // 2, 0), (W // 2, TOP_H)], fill=(80, 80, 80), width=2)

    fig = plt.figure(figsize=(W / 100, (H - TOP_H) / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    fig.patch.set_facecolor('#f0f0f0')

    phase, pcolor = phase_label(t)
    ax.text(0.02, 0.82, 'Box Lift 20 kg (semi-squat)  —  Baseline vs SMA Suit (200 N · 24 N·m peak)',
            fontsize=19, fontweight='bold', color='black', transform=ax.transAxes)
    ax.text(0.02, 0.63, f'Phase: {phase}   •   box grasped at t = 2.0 s',
            fontsize=13, color=pcolor, transform=ax.transAxes, fontweight='bold')

    reduc = (100.0 * (es_l_peak - es_r_peak) / es_l_peak) if es_l_peak > 1e-3 else 0.0
    meta = (f't = {t:4.2f} s   |   ES peak: {es_l_peak:4.1f}% → {es_r_peak:4.1f}%   '
            f'(Δ {reduc:+.1f}%)   |   Suit torque = {torque_now_nm:5.2f} N·m   '
            f'|   Box = {"ON (20 kg)" if box_on else "OFF"}')
    ax.text(0.02, 0.44, meta, fontsize=14, family='monospace',
            color='#222', transform=ax.transAxes)
    ax.text(0.02, 0.28,
            f'(ES mean across 76 muscles: {es_l_mean:4.1f}% → {es_r_mean:4.1f}%)',
            fontsize=11, family='monospace', color='#666', transform=ax.transAxes)

    # ES peak comparison bars (0–100% scale)
    bar_l, bar_r = 0.40, 0.98
    bar_h = 0.10
    y_base = 0.15
    ax.add_patch(plt.Rectangle((bar_l, y_base), bar_r - bar_l, bar_h,
                               transform=ax.transAxes, facecolor='white',
                               edgecolor='black', lw=1))
    frac_b = min(max(es_l_peak / 100.0, 0.0), 1.0)
    ax.add_patch(plt.Rectangle((bar_l, y_base), (bar_r - bar_l) * frac_b, bar_h,
                               transform=ax.transAxes,
                               facecolor=plt.cm.coolwarm(frac_b), edgecolor='none'))
    ax.text(bar_l - 0.005, y_base + bar_h / 2, '0 N',
            fontsize=10, ha='right', va='center', transform=ax.transAxes)
    y_suit = 0.03
    ax.add_patch(plt.Rectangle((bar_l, y_suit), bar_r - bar_l, bar_h,
                               transform=ax.transAxes, facecolor='white',
                               edgecolor='black', lw=1))
    frac_s = min(max(es_r_peak / 100.0, 0.0), 1.0)
    ax.add_patch(plt.Rectangle((bar_l, y_suit), (bar_r - bar_l) * frac_s, bar_h,
                               transform=ax.transAxes,
                               facecolor=plt.cm.coolwarm(frac_s), edgecolor='none'))
    ax.text(bar_l - 0.005, y_suit + bar_h / 2, '200 N',
            fontsize=10, ha='right', va='center', transform=ax.transAxes)
    for pct in (0, 20, 40, 60, 80, 100):
        x = bar_l + (bar_r - bar_l) * (pct / 100.0)
        ax.plot([x, x], [y_suit - 0.02, y_suit], color='k', lw=0.8,
                transform=ax.transAxes, clip_on=False)
        ax.text(x, y_suit - 0.05, f'{pct}', fontsize=9, ha='center',
                transform=ax.transAxes)
    ax.text((bar_l + bar_r) / 2, y_base + bar_h + 0.02,
            'ES peak activation (max across ES muscles, %)  —  scale 0–100%',
            fontsize=10, ha='center', color='#333', transform=ax.transAxes)

    fig.savefig(str(out_path).replace('.png', '_full.png'), dpi=100,
                facecolor='#f0f0f0')
    plt.close(fig)
    overlay = Image.open(str(out_path).replace('.png', '_full.png')).convert('RGB')
    canvas.paste(overlay, (0, TOP_H))
    canvas.save(out_path)
    try: os.remove(str(out_path).replace('.png', '_full.png'))
    except OSError: pass


# ---------------- drivers ----------------
def _setup():
    model = osim.Model(MODEL); state = model.initSystem()
    meshes = collect_meshes(model)
    mot_tbl = osim.TimeSeriesTable(MOT)
    t_l, lab_l, dat_l = read_activation_table(SO_LEFT)
    t_r, lab_r, dat_r = read_activation_table(SO_RIGHT)
    muscle_names = [model.getMuscles().get(i).getName()
                    for i in range(model.getMuscles().getSize())]
    es_names = [n for n in muscle_names if n.startswith(ES_PREFIXES)]
    return model, state, meshes, mot_tbl, muscle_names, es_names, \
           (t_l, lab_l, dat_l), (t_r, lab_r, dat_r)


def render_one(t, out_png, ctx):
    (model, state, meshes, mot_tbl, muscle_names, es_names,
     (t_l, lab_l, dat_l), (t_r, lab_r, dat_r)) = ctx
    apply_motion(model, state, mot_tbl, t)
    acts_l = activations_at(t_l, dat_l, t, lab_l, muscle_names)
    acts_r = activations_at(t_r, dat_r, t, lab_r, muscle_names)
    es_l_peak = 100.0 * float(np.max([acts_l[n] for n in es_names]))
    es_r_peak = 100.0 * float(np.max([acts_r[n] for n in es_names]))
    es_l_mean = 100.0 * float(np.mean([acts_l[n] for n in es_names]))
    es_r_mean = 100.0 * float(np.mean([acts_r[n] for n in es_names]))
    torque_nm = T_PEAK_NM * alpha_spine(t)
    box_on = t >= BOX_START_T - 1e-6
    tmp_3d = Path(str(out_png).replace('.png', '_3d.png'))
    render_3d_panel(model, state, meshes, muscle_names, acts_l, acts_r, t, tmp_3d)
    composite_frame(tmp_3d, out_png, t,
                    es_l_peak, es_r_peak, es_l_mean, es_r_mean,
                    torque_nm, box_on)
    try: os.remove(tmp_3d)
    except OSError: pass
    return es_l_peak, es_r_peak


def preview():
    ctx = _setup()
    # Floor (box visible front), grasp instant (Δ21%), lift-off peak (Δ10%)
    times = [0.0, 2.0, 2.33]
    frames = []
    for i, t in enumerate(times):
        fpath = FRAME_DIR / f'preview_{i}.png'
        es_l, es_r = render_one(t, fpath, ctx)
        print(f'  preview t={t:.2f}s  ES_0N={es_l:.1f}%  ES_200N={es_r:.1f}%')
        frames.append(Image.open(fpath))
    W = frames[0].width; H = frames[0].height
    canvas = Image.new('RGB', (W, H * len(frames)), (240, 240, 240))
    for i, f in enumerate(frames):
        canvas.paste(f, (0, i * H))
    canvas.save(OUT_PREVIEW)
    print(f'Wrote {OUT_PREVIEW}  ({canvas.size[0]}x{canvas.size[1]})')


def video():
    ctx = _setup()
    out_dir = FRAME_DIR
    if out_dir.exists(): shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    t0 = time.time()
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame_path = out_dir / f'frame_{fi:04d}.png'
        es_l_peak, es_r_peak = render_one(t, frame_path, ctx)
        if fi % 10 == 0:
            print(f'  frame {fi+1}/{N_FRAMES}  t={t:.2f}s  '
                  f'ES peak 0N={es_l_peak:.1f}%  200N={es_r_peak:.1f}%  '
                  f'el={time.time()-t0:.1f}s')
    print(f'frames done in {time.time()-t0:.1f}s')

    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error',
        '-framerate', str(FPS),
        '-i', str(out_dir / 'frame_%04d.png'),
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-crf', '18', '-preset', 'medium',
        '-movflags', '+faststart',
        str(OUT_MP4),
    ]
    subprocess.run(cmd, check=True)
    print(f'Wrote {OUT_MP4}')


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'preview'
    if mode == 'preview':
        preview()
    elif mode == 'video':
        video()
    else:
        print('usage: render_box_comparison.py preview|video')
