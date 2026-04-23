"""Render 3 motion snapshots for stoop_box20kg_v2.mot with captions.

Output: /data/opensim_results/box_motion_v2_snapshots/
  t0.00_standing.png
  t2.00_grasp.png
  t2.33_liftoff.png

Each PNG (1920x1080): top 820 px is 3D (ivory bones, coolwarm-ready muscle lines
at default activation 0, floor plane, brown box when grasped), bottom 260 px is
metadata caption. Camera matches render_suit_comparison_v2 / render_box_comparison.
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
from PIL import Image, ImageDraw

MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim'
GEOM_DIR = Path('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry')
MOT = '/data/stoop_motion/stoop_box20kg_v2.mot'

OUT_DIR = Path('/data/opensim_results/box_motion_v2_snapshots'); OUT_DIR.mkdir(parents=True, exist_ok=True)
RES_W, RES_H = 1920, 1080
TOP_H = 820

# Same box geometry as render_box_comparison.py
BOX_SIZE = (0.20, 0.15, 0.20)
BOX_FLOOR_X = 0.706
BOX_FLOOR_Y = -0.85 + BOX_SIZE[1] / 2.0
BOX_FLOOR_Z = -0.032
BOX_HAND_X_OFFSET = 0.08
GRASP_T = 2.0


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


def apply_motion(model, state, mot_tbl, t):
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
        if c.getMotionType() == 1:
            v = np.radians(v)
        c.setValue(state, v, False)
    model.assemble(state)
    model.realizePosition(state)


def body_pos(model, state, nm):
    g = model.getBodySet().get(nm).getPositionInGround(state)
    return np.array([g.get(0), g.get(1), g.get(2)])


def render_3d(model, state, meshes, box_center_or_none, out_path):
    pv.global_theme.background = '#1a1a1a'
    pv.global_theme.lighting = True
    pl = pv.Plotter(window_size=(RES_W, TOP_H), off_screen=True, border=False)
    # bones
    frame_cache = {}
    for mi in meshes:
        if mi['frame'] not in frame_cache:
            frame_cache[mi['frame']] = model.getComponent(mi['frame'])
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
        pl.add_mesh(surf, color='ivory', opacity=1.0, smooth_shading=True,
                    specular=0.2, specular_power=10)
    # muscle lines (uncolored grey — this is a kinematic check, not SO)
    muscles = model.getMuscles()
    all_pts = []; cells = []
    for i in range(muscles.getSize()):
        m = muscles.get(i)
        pp_set = m.getGeometryPath().getCurrentPath(state)
        pts = []
        for k in range(pp_set.getSize()):
            loc = pp_set.get(k).getLocationInGround(state)
            pts.append([loc.get(0), loc.get(1), loc.get(2)])
        if len(pts) < 2: continue
        start = len(all_pts); all_pts.extend(pts)
        for j in range(len(pts) - 1):
            cells.append(2); cells.append(start + j); cells.append(start + j + 1)
    if all_pts:
        pd = pv.PolyData()
        pd.points = np.array(all_pts, dtype=float)
        pd.lines = np.array(cells, dtype=np.int64)
        pl.add_mesh(pd, color='#4080ff', opacity=0.7, line_width=1.5)
    # box
    if box_center_or_none is not None:
        bc = box_center_or_none
        box = pv.Cube(center=(bc[0], bc[1], bc[2]),
                      x_length=BOX_SIZE[0], y_length=BOX_SIZE[1], z_length=BOX_SIZE[2])
        pl.add_mesh(box, color='#8b5a2b', opacity=1.0, smooth_shading=False,
                    specular=0.1, specular_power=5, show_edges=True,
                    edge_color='#5a3a1a', line_width=1.5)
    # floor
    floor = pv.Plane(center=(0.1, -0.905, 0.0), direction=(0, 1, 0),
                     i_size=2.5, j_size=2.5)
    pl.add_mesh(floor, color='#444444', opacity=0.4, show_edges=True,
                edge_color='#666666', line_width=1)
    pl.camera_position = [(1.5, 0.25, 2.6), (0.2, -0.10, 0.0), (0.0, 1.0, 0.0)]
    pl.camera.parallel_projection = True
    pl.camera.parallel_scale = 1.05
    pl.screenshot(str(out_path))
    pl.close()


def compose(img_3d_path, out_path, caption_lines):
    img3d = Image.open(img_3d_path).convert('RGB')
    canvas = Image.new('RGB', (RES_W, RES_H), (240, 240, 240))
    canvas.paste(img3d.resize((RES_W, TOP_H), Image.LANCZOS), (0, 0))
    fig = plt.figure(figsize=(RES_W / 100, (RES_H - TOP_H) / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    fig.patch.set_facecolor('#f0f0f0')
    ax.text(0.02, 0.78, caption_lines[0], fontsize=22, fontweight='bold',
            color='black', transform=ax.transAxes)
    for i, line in enumerate(caption_lines[1:]):
        ax.text(0.02, 0.52 - i * 0.22, line, fontsize=14, family='monospace',
                color='#222', transform=ax.transAxes)
    tmp = str(out_path).replace('.png', '_cap.png')
    fig.savefig(tmp, dpi=100, facecolor='#f0f0f0'); plt.close(fig)
    canvas.paste(Image.open(tmp).convert('RGB'), (0, TOP_H))
    canvas.save(out_path)
    try: os.remove(tmp)
    except OSError: pass


def clearances(model, state):
    thorax = body_pos(model, state, 'thoracic8')
    thigh_mid = 0.5 * (body_pos(model, state, 'femur_r') + body_pos(model, state, 'tibia_r'))
    ulna_r = body_pos(model, state, 'ulna_R'); tibia_r = body_pos(model, state, 'tibia_r')
    knee_mid = 0.5 * (body_pos(model, state, 'tibia_r') + body_pos(model, state, 'tibia_l'))
    hc = 0.5 * (body_pos(model, state, 'hand_R') + body_pos(model, state, 'hand_L'))
    return {
        'torso_thigh': np.linalg.norm(thorax - thigh_mid),
        'elbow_knee':  np.linalg.norm(ulna_r - tibia_r),
        'hand_knee':   np.linalg.norm(hc - knee_mid),
    }


def main():
    model = osim.Model(MODEL); state = model.initSystem()
    meshes = collect_meshes(model)
    mot_tbl = osim.TimeSeriesTable(MOT)

    targets = [
        (0.00, 'standing'),
        (2.00, 'grasp'),
        (2.33, 'liftoff'),
    ]
    for t, tag in targets:
        apply_motion(model, state, mot_tbl, t)
        hR = body_pos(model, state, 'hand_R')
        hL = body_pos(model, state, 'hand_L')
        hc = 0.5 * (hR + hL)
        clr = clearances(model, state)
        if t < GRASP_T - 1e-6:
            box_c = np.array([BOX_FLOOR_X, BOX_FLOOR_Y, BOX_FLOOR_Z])
        else:
            box_c = np.array([hc[0] + BOX_HAND_X_OFFSET, hc[1], hc[2]])
        tmp3d = OUT_DIR / f't{t:.2f}_{tag}_3d.png'
        render_3d(model, state, meshes, box_c, tmp3d)
        out = OUT_DIR / f't{t:.2f}_{tag}.png'
        lines = [
            f'v2 motion  —  t = {t:.2f} s  ({tag})',
            f'hand_center = ({hc[0]:+.3f}, {hc[1]:+.3f}, {hc[2]:+.3f}) m   '
            f'hand_y = {hc[1]:+.3f} m',
            f'clearances  torso-thigh = {clr["torso_thigh"]*100:4.1f} cm   '
            f'elbow-knee = {clr["elbow_knee"]*100:4.1f} cm   '
            f'hand-knee = {clr["hand_knee"]*100:4.1f} cm',
        ]
        compose(tmp3d, out, lines)
        try: os.remove(tmp3d)
        except OSError: pass
        print(f'  wrote {out}   hand_y={hc[1]:+.3f}  '
              f'clear(t-th,e-k,h-k)=({clr["torso_thigh"]*100:.1f},'
              f'{clr["elbow_knee"]*100:.1f},{clr["hand_knee"]*100:.1f})cm')


if __name__ == '__main__':
    main()
