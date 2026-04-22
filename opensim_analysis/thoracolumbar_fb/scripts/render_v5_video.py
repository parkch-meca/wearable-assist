"""Render v5 stoop (slow symmetric, flat feet, modified model) as high-quality MP4.

Single-view 3D render in OpenSim-GUI-like style: ivory bones + muscle lines
colored by SO activation + floor reference + phase-shaded time bar overlay.

Outputs /data/opensim_results/video/stoop_v5_gui_quality.mp4
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
SO_ACT = '/data/stoop_results/stoop_v5/so_v5_StaticOptimization_activation.sto'

VIDEO_DIR = Path('/data/opensim_results/video'); VIDEO_DIR.mkdir(parents=True, exist_ok=True)
FRAME_DIR = Path('/tmp/stoop_v5_frames'); FRAME_DIR.mkdir(parents=True, exist_ok=True)
OUT_MP4 = VIDEO_DIR / 'stoop_v5_gui_quality_v2.mp4'

FPS = 30
T_TOTAL = 5.0
N_FRAMES = int(FPS * T_TOTAL) + 1  # 151
ES_PREFIXES = ('IL_', 'LTpT_', 'LTpL_')
ACT_MAX = 0.25
RES_W, RES_H = 1920, 1080


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


def composite_frame(img_3d_path, out_path, t, es_mean_pct, es_max_pct):
    img3d = Image.open(img_3d_path).convert('RGB')
    W, H = RES_W, RES_H
    canvas = Image.new('RGB', (W, H), (240, 240, 240))
    top_h = 820
    img3d_r = img3d.resize((W, top_h), Image.LANCZOS)
    canvas.paste(img3d_r, (0, 0))

    fig = plt.figure(figsize=(W / 100, (H - top_h) / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    fig.patch.set_facecolor('#f0f0f0')

    phase, pcolor = phase_label(t)
    ax.text(0.02, 0.82, 'Asymmetric Stoop v5  —  ThoracolumbarFB',
            fontsize=22, fontweight='bold', color='black', transform=ax.transAxes)
    ax.text(0.02, 0.58, f'Phase: {phase}  •  slow symmetric (2 s bend / 2 s straighten)',
            fontsize=14, color=pcolor, transform=ax.transAxes, fontweight='bold')
    meta = (f't = {t:4.2f} s   |   ES mean = {es_mean_pct:4.1f} %   |   '
            f'ES max = {es_max_pct:4.1f} %')
    ax.text(0.02, 0.30, meta, fontsize=16, family='monospace',
            color='#222', transform=ax.transAxes)

    # Time-progress bar with phase shading
    bar_l, bar_r = 0.02, 0.98
    bar_y, bar_h = 0.05, 0.14
    for t0, t1, col in [(0.0, 0.5, 'gray'), (0.5, 2.5, 'tab:orange'),
                        (2.5, 3.0, 'tab:red'), (3.0, 5.0, 'tab:green')]:
        x0 = bar_l + (bar_r - bar_l) * (t0 / T_TOTAL)
        x1 = bar_l + (bar_r - bar_l) * (t1 / T_TOTAL)
        ax.add_patch(plt.Rectangle((x0, bar_y), x1 - x0, bar_h,
                                    transform=ax.transAxes, facecolor=col,
                                    alpha=0.2, edgecolor='black', lw=0.5))
    # Current time marker
    x_now = bar_l + (bar_r - bar_l) * (t / T_TOTAL)
    ax.plot([x_now, x_now], [bar_y - 0.02, bar_y + bar_h + 0.02],
            color='red', lw=2.5, transform=ax.transAxes, clip_on=False)

    fig.savefig(str(out_path).replace('.png', '_full.png'), dpi=100,
                facecolor='#f0f0f0')
    plt.close(fig)
    overlay = Image.open(str(out_path).replace('.png', '_full.png')).convert('RGB')
    canvas.paste(overlay, (0, top_h))
    canvas.save(out_path)
    try: os.remove(str(out_path).replace('.png', '_full.png'))
    except OSError: pass


def render():
    model = osim.Model(MODEL); state = model.initSystem()
    meshes = collect_meshes(model)
    mot_tbl = osim.TimeSeriesTable(MOT)
    t_act, lab_act, dat_act = read_activation_table(SO_ACT)
    muscle_names = [model.getMuscles().get(i).getName()
                    for i in range(model.getMuscles().getSize())]
    es_names = [n for n in muscle_names if n.startswith(ES_PREFIXES)]

    out_dir = FRAME_DIR
    if out_dir.exists(): shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    pv.global_theme.background = '#1a1a1a'
    pv.global_theme.lighting = True

    t0 = time.time()
    for fi in range(N_FRAMES):
        t = fi / FPS
        apply_motion(model, state, mot_tbl, t)
        acts = activations_at(t_act, dat_act, t, lab_act, muscle_names)
        es_vals = np.array([acts[n] for n in es_names])
        es_mean_pct = 100.0 * float(es_vals.mean())
        es_max_pct  = 100.0 * float(es_vals.max())

        pl = pv.Plotter(window_size=(1920, 820), off_screen=True, border=False)
        build_bone_actor(pl, model, state, meshes, color='ivory')
        pd = build_muscle_polydata(model, state, muscle_names, acts)
        if pd is not None:
            pl.add_mesh(pd, scalars='activation', cmap='coolwarm',
                        clim=[0, ACT_MAX], line_width=3.0, show_scalar_bar=False)
        # Floor grid
        floor = pv.Plane(center=(0.1, -0.905, 0.0), direction=(0, 1, 0),
                         i_size=2.5, j_size=2.5)
        pl.add_mesh(floor, color='#444444', opacity=0.4, show_edges=True,
                    edge_color='#666666', line_width=1)
        # Parallel projection: visible vertical = 2 * parallel_scale.
        # 1.05 -> 2.1 m view; focal shifted up to clear skull crown (~+0.70 m).
        pl.camera_position = [
            (1.5, 0.25, 2.6),     # oblique 3/4 view direction
            (0.2, -0.10, 0.0),    # focal — shifted up for headroom
            (0.0, 1.0, 0.0),      # up axis
        ]
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale = 1.05
        img_path = out_dir / f'3d_{fi:04d}.png'
        pl.screenshot(str(img_path))
        pl.close()

        full_path = out_dir / f'frame_{fi:04d}.png'
        composite_frame(img_path, full_path, t, es_mean_pct, es_max_pct)

        if fi % 15 == 0:
            print(f'  frame {fi+1}/{N_FRAMES}  t={t:.2f}s  '
                  f'ES={es_mean_pct:.1f}%  elapsed={time.time()-t0:.1f}s')
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
    render()
