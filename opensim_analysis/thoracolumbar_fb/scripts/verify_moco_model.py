"""Visual + numeric verification of MaleFullBodyModel_v2.0_OS4_moco_stoop.osim.

Produces:
  1. static 4-view comparison (original vs moco_stoop) → 2×4 grid
  2. dynamic motion replay (7 timepoints along stoop_synthetic_v5.mot) → stack
  3. numeric kinematic error table (per body, per timepoint)

Output dir: /data/opensim_results/moco_model_verification/
"""
import os
os.environ.setdefault('DISPLAY', ':1')
from pathlib import Path
import numpy as np
import opensim as osim
import pyvista as pv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

MODELS = {
    'original':   '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim',
    'moco_stoop': '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_moco_stoop.osim',
}
GEOM_DIR = Path('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry')
MOT = '/data/stoop_motion/stoop_synthetic_v5.mot'
OUT = Path('/data/opensim_results/moco_model_verification')
OUT.mkdir(parents=True, exist_ok=True)

VIEWS = {
    # name : (camera_pos, focal, parallel_scale)
    'anterior':  ((4.0, -0.1, 0.0),   (0.0, -0.1, 0.0), 1.0),
    'sagittal':  ((0.0, -0.1, 4.0),   (0.0, -0.1, 0.0), 1.0),
    'posterior': ((-4.0, -0.1, 0.0),  (0.0, -0.1, 0.0), 1.0),
    '3quarter':  ((3.0, 0.1, 3.0),    (0.0, -0.1, 0.0), 1.0),
}
STATIC_RES = 1200  # per view
DYN_RES_W, DYN_RES_H = 900, 1600  # sagittal-profile aspect


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
        try:
            c.setValue(state, v, False)
        except Exception:
            pass
    model.assemble(state); model.realizePosition(state)


def render_view(model, state, meshes, view_name, out_path, res=1200, show_muscles=True):
    cam_pos, focal, pscale = VIEWS[view_name]
    pv.global_theme.background = '#1a1a1a'
    pv.global_theme.lighting = True
    pl = pv.Plotter(window_size=(res, res), off_screen=True, border=False)

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

    # muscles (all, grey-blue)
    if show_muscles:
        muscles = model.getMuscles()
        all_pts = []; cells = []
        for i in range(muscles.getSize()):
            m = muscles.get(i)
            pp = m.getGeometryPath().getCurrentPath(state)
            pts = []
            for k in range(pp.getSize()):
                loc = pp.get(k).getLocationInGround(state)
                pts.append([loc.get(0), loc.get(1), loc.get(2)])
            if len(pts) < 2: continue
            start = len(all_pts); all_pts.extend(pts)
            for j in range(len(pts) - 1):
                cells += [2, start + j, start + j + 1]
        if all_pts:
            pd = pv.PolyData()
            pd.points = np.array(all_pts, dtype=float)
            pd.lines = np.array(cells, dtype=np.int64)
            pl.add_mesh(pd, color='#4080ff', opacity=0.7, line_width=1.2)

    pl.camera_position = [cam_pos, focal, (0, 1, 0)]
    pl.camera.parallel_projection = True
    pl.camera.parallel_scale = pscale
    pl.screenshot(str(out_path))
    pl.close()


def label_image(path, text, pad=30, bg=(32, 32, 32), fg=(240, 240, 240)):
    img = Image.open(path).convert('RGB')
    W, H = img.size
    canvas = Image.new('RGB', (W, H + pad), bg)
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    except Exception:
        font = ImageFont.load_default()
    draw.text((10, 6), text, fill=fg, font=font)
    canvas.paste(img, (0, pad))
    canvas.save(path)


def static_grid():
    """Render both models in default pose across 4 views → 2×4 grid."""
    per_view = {}
    for tag, path in MODELS.items():
        model = osim.Model(path); state = model.initSystem()
        meshes = collect_meshes(model)
        for vname in VIEWS:
            out = OUT / f'static_{tag}_{vname}.png'
            render_view(model, state, meshes, vname, out, res=STATIC_RES)
            label_image(out, f'{tag.upper()} · {vname}', pad=30)
            per_view.setdefault(tag, {})[vname] = out
        print(f'[static] {tag} done')

    # Composite 2 rows × 4 cols
    view_order = ['anterior', 'sagittal', 'posterior', '3quarter']
    W = STATIC_RES; H = STATIC_RES + 30
    grid = Image.new('RGB', (W * 4, H * 2), (16, 16, 16))
    for ri, tag in enumerate(['original', 'moco_stoop']):
        for ci, vn in enumerate(view_order):
            img = Image.open(per_view[tag][vn]).convert('RGB')
            grid.paste(img, (ci * W, ri * H))
    out = OUT / 'model_comparison_grid.png'
    grid.save(out)
    print(f'[grid] {out}  {grid.size[0]}x{grid.size[1]}')
    return out


def dynamic_timeline():
    """Replay stoop_v5 at 7 timepoints, sagittal view, side-by-side per row."""
    timepoints = [0.0, 1.0, 2.0, 2.5, 3.0, 4.0, 5.0]
    mot_tbl = osim.TimeSeriesTable(MOT)

    # Also collect kinematic errors
    key_bodies = ['pelvis', 'thoracic10', 'calcn_r', 'hand_R', 'femur_r',
                  'tibia_r', 'head_neck', 'humerus_R', 'radius_R']
    err_table = []

    per_tag = {'original': {}, 'moco_stoop': {}}
    for tag, path in MODELS.items():
        model = osim.Model(path); state = model.initSystem()
        meshes = collect_meshes(model)
        for t in timepoints:
            apply_motion(model, state, mot_tbl, t)
            out = OUT / f'motion_{tag}_t{t:.1f}.png'
            render_view(model, state, meshes, 'sagittal', out,
                        res=min(DYN_RES_W, DYN_RES_H), show_muscles=True)
            label_image(out, f'{tag.upper()} · t={t:.1f}s', pad=28)
            per_tag[tag][t] = out
        print(f'[dynamic] {tag} done')

    # Compute kinematic errors using fresh models
    m1 = osim.Model(MODELS['original']);   m1.initSystem()
    m2 = osim.Model(MODELS['moco_stoop']); m2.initSystem()
    for t in timepoints:
        s1 = m1.initSystem()
        apply_motion(m1, s1, mot_tbl, t)
        s2 = m2.initSystem()
        apply_motion(m2, s2, mot_tbl, t)
        bs1 = m1.getBodySet(); bs2 = m2.getBodySet()
        for b in key_bodies:
            try:
                p1 = bs1.get(b).getPositionInGround(s1)
                p2 = bs2.get(b).getPositionInGround(s2)
                dx = abs(p1.get(0) - p2.get(0))
                dy = abs(p1.get(1) - p2.get(1))
                dz = abs(p1.get(2) - p2.get(2))
                err_table.append({'t': t, 'body': b,
                                   'err_mm': 1000 * max(dx, dy, dz)})
            except Exception:
                pass

    # Timeline compose — 7 rows, each row = original | moco_stoop
    thumbs = []
    for t in timepoints:
        a = Image.open(per_tag['original'][t]).convert('RGB')
        b = Image.open(per_tag['moco_stoop'][t]).convert('RGB')
        # trim to same height
        row = Image.new('RGB', (a.width + b.width, max(a.height, b.height)),
                        (16, 16, 16))
        row.paste(a, (0, 0)); row.paste(b, (a.width, 0))
        thumbs.append(row)
    total_w = thumbs[0].width
    total_h = sum(t.height for t in thumbs)
    tl = Image.new('RGB', (total_w, total_h), (16, 16, 16))
    y = 0
    for r in thumbs:
        tl.paste(r, (0, y)); y += r.height
    out = OUT / 'motion_timeline_compare.png'
    tl.save(out)
    print(f'[timeline] {out}  {total_w}x{total_h}')

    # Write numeric table
    max_err = max(r['err_mm'] for r in err_table) if err_table else 0
    tbl_path = OUT / 'kinematic_error_table.md'
    lines = [f'# Kinematic error: original vs moco_stoop', '',
             f'Max error across {len(key_bodies)} bodies × {len(timepoints)} timepoints: **{max_err:.4f} mm**', '',
             '| t (s) | body | err (mm) |', '|---|---|---|']
    for r in err_table:
        lines.append(f"| {r['t']:.1f} | {r['body']} | {r['err_mm']:.4f} |")
    tbl_path.write_text('\n'.join(lines))
    print(f'[table] {tbl_path}  max_err={max_err:.4f}mm')
    return out, max_err


if __name__ == '__main__':
    print('=== static grid ===')
    static_grid()
    print('\n=== dynamic timeline ===')
    dynamic_timeline()
