"""Side-by-side comparison render: 0N (left) vs 200N suit (right) on v5 motion.

Layout: 1920x1080, top 820px is side-by-side 3D (960 each), bottom 260px is
time/phase/torque/ES-bar overlay. Same camera as stoop_v5_gui_quality_v2.

Modes:
  python render_suit_comparison_v2.py preview   # 3 snapshot frames -> png
  python render_suit_comparison_v2.py video     # full mp4
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
from PIL import Image

MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim'
GEOM_DIR = Path('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry')
MOT = '/data/stoop_motion/stoop_synthetic_v5.mot'
SO_LEFT  = '/data/stoop_results/stoop_v5/so_v5_StaticOptimization_activation.sto'
SO_RIGHT = '/data/stoop_results/suit_sweep_v5/F200/suit_v5_F200_StaticOptimization_activation.sto'

VIDEO_DIR = Path('/data/opensim_results/video'); VIDEO_DIR.mkdir(parents=True, exist_ok=True)
FRAME_DIR = Path('/tmp/stoop_cmp_v2_frames'); FRAME_DIR.mkdir(parents=True, exist_ok=True)
OUT_MP4 = VIDEO_DIR / 'stoop_suit_comparison_v2.mp4'
OUT_PREVIEW = Path('/data/opensim_results/stoop_comparison_preview.png')

FPS = 30
T_TOTAL = 5.0
N_FRAMES = int(FPS * T_TOTAL) + 1  # 151
ES_PREFIXES = ('IL_', 'LTpT_', 'LTpL_')
ACT_MAX = 0.25
RES_W, RES_H = 1920, 1080
PANEL_W, TOP_H = 960, 820

# Suit torque profile (mirrors alpha_v5 in run_suit_so_v5.py)
T_PEAK_NM = 24.0  # 200 N * 0.12 m
def alpha_v5(t):
    if t < 0.5:  return 0.0
    if t <= 2.5: return (1.0 - np.cos(np.pi * (t - 0.5) / 2.0)) / 2.0
    if t <= 3.0: return 1.0
    if t <= 5.0: return (1.0 + np.cos(np.pi * (t - 3.0) / 2.0)) / 2.0
    return 0.0


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
    if t < 0.5: return 'upright', 'gray'
    if t <= 2.5: return 'bend (2 s)', 'tab:orange'
    if t <= 3.0: return 'hold (0.5 s)', 'tab:red'
    if t <= 5.0: return 'straighten (2 s)', 'tab:green'
    return 'upright', 'gray'


# ---------------- 3D panel render (single side-by-side image) ----------------
def render_3d_panel(model, state, meshes, muscle_names, acts_l, acts_r, out_path):
    """Render a 1920x820 image: left panel 0N, right panel 200N."""
    pv.global_theme.background = '#1a1a1a'
    pv.global_theme.lighting = True
    pl = pv.Plotter(shape=(1, 2), window_size=(1920, TOP_H), off_screen=True,
                    border=False)
    for col, (tag, acts, badge) in enumerate([
        ('no suit  —  0 N',  acts_l, '#888888'),
        ('SMA suit  —  200 N (24 N·m peak)', acts_r, '#ff6060'),
    ]):
        pl.subplot(0, col)
        build_bone_actor(pl, model, state, meshes, color='ivory')
        pd = build_muscle_polydata(model, state, muscle_names, acts)
        if pd is not None:
            pl.add_mesh(pd, scalars='activation', cmap='coolwarm',
                        clim=[0, ACT_MAX], line_width=3.0, show_scalar_bar=False)
        floor = pv.Plane(center=(0.1, -0.905, 0.0), direction=(0, 1, 0),
                         i_size=2.5, j_size=2.5)
        pl.add_mesh(floor, color='#444444', opacity=0.4, show_edges=True,
                    edge_color='#666666', line_width=1)
        pl.camera_position = [
            (1.5, 0.25, 2.6),
            (0.2, -0.10, 0.0),
            (0.0, 1.0, 0.0),
        ]
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale = 1.05
        pl.add_text(tag, font_size=14, color=badge, position='upper_left')
    pl.screenshot(str(out_path))
    pl.close()


# ---------------- bottom overlay ----------------
def composite_frame(img_3d_path, out_path, t, es_l_pct, es_r_pct, torque_now_nm,
                    show_reduction=True):
    img3d = Image.open(img_3d_path).convert('RGB')
    W, H = RES_W, RES_H
    canvas = Image.new('RGB', (W, H), (240, 240, 240))
    img3d_r = img3d.resize((W, TOP_H), Image.LANCZOS)
    canvas.paste(img3d_r, (0, 0))

    # center divider
    from PIL import ImageDraw
    draw = ImageDraw.Draw(canvas)
    draw.line([(W // 2, 0), (W // 2, TOP_H)], fill=(80, 80, 80), width=2)

    fig = plt.figure(figsize=(W / 100, (H - TOP_H) / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    fig.patch.set_facecolor('#f0f0f0')

    phase, pcolor = phase_label(t)
    ax.text(0.02, 0.80, 'Stoop v5  —  Baseline vs SMA Suit (200 N · 24 N·m peak)',
            fontsize=20, fontweight='bold', color='black', transform=ax.transAxes)
    ax.text(0.02, 0.58, f'Phase: {phase}   •   2 s bend / 0.5 s hold / 2 s straighten',
            fontsize=13, color=pcolor, transform=ax.transAxes, fontweight='bold')

    reduc = (100.0 * (es_l_pct - es_r_pct) / es_l_pct) if es_l_pct > 1e-3 else 0.0
    reduc_s = f'(Δ {reduc:+.1f} %)' if show_reduction else ''
    meta = (f't = {t:4.2f} s   |   ES: {es_l_pct:4.1f} % → {es_r_pct:4.1f} %   '
            f'{reduc_s}   |   Suit torque = {torque_now_nm:5.2f} N·m')
    ax.text(0.02, 0.32, meta, fontsize=15, family='monospace',
            color='#222', transform=ax.transAxes)

    # ES comparison bars: baseline (top) vs suit (bottom)
    bar_l, bar_r = 0.40, 0.98
    bar_h = 0.11
    # Baseline bar (top, gray outline)
    y_base = 0.17
    ax.add_patch(plt.Rectangle((bar_l, y_base), bar_r - bar_l, bar_h,
                               transform=ax.transAxes, facecolor='white',
                               edgecolor='black', lw=1))
    frac_b = min(max(es_l_pct / 25.0, 0.0), 1.0)
    ax.add_patch(plt.Rectangle((bar_l, y_base), (bar_r - bar_l) * frac_b, bar_h,
                               transform=ax.transAxes,
                               facecolor=plt.cm.coolwarm(frac_b), edgecolor='none'))
    ax.text(bar_l - 0.005, y_base + bar_h / 2, '0 N',
            fontsize=11, ha='right', va='center', transform=ax.transAxes)
    # Suit bar (bottom)
    y_suit = 0.03
    ax.add_patch(plt.Rectangle((bar_l, y_suit), bar_r - bar_l, bar_h,
                               transform=ax.transAxes, facecolor='white',
                               edgecolor='black', lw=1))
    frac_s = min(max(es_r_pct / 25.0, 0.0), 1.0)
    ax.add_patch(plt.Rectangle((bar_l, y_suit), (bar_r - bar_l) * frac_s, bar_h,
                               transform=ax.transAxes,
                               facecolor=plt.cm.coolwarm(frac_s), edgecolor='none'))
    ax.text(bar_l - 0.005, y_suit + bar_h / 2, '200 N',
            fontsize=11, ha='right', va='center', transform=ax.transAxes)
    # tick labels
    for pct in (0, 5, 10, 15, 20, 25):
        x = bar_l + (bar_r - bar_l) * (pct / 25.0)
        ax.plot([x, x], [y_suit - 0.02, y_suit], color='k', lw=0.8,
                transform=ax.transAxes, clip_on=False)
        ax.text(x, y_suit - 0.05, f'{pct}', fontsize=9, ha='center',
                transform=ax.transAxes)
    ax.text((bar_l + bar_r) / 2, y_base + bar_h + 0.02,
            'ES mean activation (%)  —  scale 0–25%',
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
    es_l_pct = 100.0 * float(np.mean([acts_l[n] for n in es_names]))
    es_r_pct = 100.0 * float(np.mean([acts_r[n] for n in es_names]))
    torque_nm = T_PEAK_NM * alpha_v5(t)
    tmp_3d = Path(str(out_png).replace('.png', '_3d.png'))
    render_3d_panel(model, state, meshes, muscle_names, acts_l, acts_r, tmp_3d)
    composite_frame(tmp_3d, out_png, t, es_l_pct, es_r_pct, torque_nm)
    try: os.remove(tmp_3d)
    except OSError: pass
    return es_l_pct, es_r_pct


def preview():
    ctx = _setup()
    # Upright, peak bend (hold mid), mid-return
    times = [0.0, 2.75, 4.0]
    frames = []
    for i, t in enumerate(times):
        fpath = FRAME_DIR / f'preview_{i}.png'
        es_l, es_r = render_one(t, fpath, ctx)
        print(f'  preview t={t:.2f}s  ES_0N={es_l:.1f}%  ES_200N={es_r:.1f}%')
        frames.append(Image.open(fpath))
    # Vertical stack for preview
    W = frames[0].width
    H = frames[0].height
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
        es_l, es_r = render_one(t, frame_path, ctx)
        if fi % 15 == 0:
            print(f'  frame {fi+1}/{N_FRAMES}  t={t:.2f}s  '
                  f'ES 0N={es_l:.1f}%  ES 200N={es_r:.1f}%  '
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
        print('usage: render_suit_comparison_v2.py preview|video')
