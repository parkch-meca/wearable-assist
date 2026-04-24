"""Render Phase 1a muscle subset highlighted on the moco_stoop model.

Phase 1a = 114 muscles (IL 24 + LTpT 42 + LTpL 10 + QL 36 + RA 2).
Phase 1a muscles: blue full opacity.
Other muscles: grey 25 % opacity.

Output: /data/opensim_results/moco_phase1a_verification/
  muscles_sagittal.png     1600×2200
  muscles_posterior.png    1600×2200
  muscles_3quarter.png     1600×2200
  muscles_combined_grid.png  4800×2200 (horizontal concat)
"""
import os
os.environ.setdefault('DISPLAY', ':1')
from pathlib import Path
import numpy as np
import opensim as osim
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont

MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_moco_stoop.osim'
GEOM_DIR = Path('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry')
PHASE1A_LIST = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/phase1a_muscle_list.txt'
OUT = Path('/data/opensim_results/moco_phase1a_verification'); OUT.mkdir(parents=True, exist_ok=True)

VIEWS = {
    'sagittal':  ((0.0, -0.1, 4.0),   (0.0, -0.1, 0.0), 1.2),
    'posterior': ((-4.0, -0.1, 0.0),  (0.0, -0.1, 0.0), 1.2),
    '3quarter':  ((-3.0, 0.1, 3.0),   (0.0, -0.1, 0.0), 1.2),  # posterior-right oblique
}
RES_W, RES_H = 1600, 2200


def load_phase1a():
    names = set()
    with open(PHASE1A_LIST) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            names.add(s)
    return names


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
        if not mf: continue
        p = GEOM_DIR / mf
        if not p.exists(): continue
        sf = mesh.get_scale_factors()
        out.append({'path': str(p), 'frame': mesh.getFrame().getAbsolutePathString(),
                    'scale': (sf.get(0), sf.get(1), sf.get(2))})
    return out


def build_muscle_polydata(model, state, filter_set):
    """Return PolyData containing only muscles whose name matches filter_set."""
    all_pts = []; cells = []
    ms = model.getMuscles()
    for i in range(ms.getSize()):
        m = ms.get(i)
        if m.getName() not in filter_set:
            continue
        pp = m.getGeometryPath().getCurrentPath(state)
        pts = []
        for k in range(pp.getSize()):
            loc = pp.get(k).getLocationInGround(state)
            pts.append([loc.get(0), loc.get(1), loc.get(2)])
        if len(pts) < 2: continue
        start = len(all_pts); all_pts.extend(pts)
        for j in range(len(pts) - 1):
            cells += [2, start + j, start + j + 1]
    if not all_pts:
        return None
    pd = pv.PolyData()
    pd.points = np.array(all_pts, dtype=float)
    pd.lines = np.array(cells, dtype=np.int64)
    return pd


def render_view(model, state, meshes, phase1a_set, other_set, view_name, out_path):
    cam_pos, focal, pscale = VIEWS[view_name]
    pv.global_theme.background = '#1a1a1a'
    pv.global_theme.lighting = True
    pl = pv.Plotter(window_size=(RES_W, RES_H), off_screen=True, border=False)

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

    # other muscles (grey, 25%)
    pd_other = build_muscle_polydata(model, state, other_set)
    if pd_other is not None:
        pl.add_mesh(pd_other, color='#888888', opacity=0.25, line_width=1.0)

    # phase1a muscles (blue, full)
    pd_p1a = build_muscle_polydata(model, state, phase1a_set)
    if pd_p1a is not None:
        pl.add_mesh(pd_p1a, color='#2080ff', opacity=0.95, line_width=2.0)

    pl.camera_position = [cam_pos, focal, (0, 1, 0)]
    pl.camera.parallel_projection = True
    pl.camera.parallel_scale = pscale
    pl.screenshot(str(out_path))
    pl.close()


def label_image(path, text, pad=42):
    img = Image.open(path).convert('RGB')
    W, H = img.size
    canvas = Image.new('RGB', (W, H + pad), (32, 32, 32))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
    except Exception:
        font = ImageFont.load_default()
    draw.text((14, 10), text, fill=(240, 240, 240), font=font)
    canvas.paste(img, (0, pad))
    canvas.save(path)


def main():
    phase1a = load_phase1a()
    model = osim.Model(MODEL); state = model.initSystem()
    ms = model.getMuscles()
    all_names = {ms.get(i).getName() for i in range(ms.getSize())}
    other = all_names - phase1a
    print(f'Phase 1a: {len(phase1a)}  Other: {len(other)}  Total: {len(all_names)}')

    meshes = collect_meshes(model)

    # Render 3 views
    out_paths = {}
    labels = {
        'sagittal':  f'PHASE 1a SUBSET · sagittal (right) · {len(phase1a)} blue / {len(other)} grey',
        'posterior': f'PHASE 1a SUBSET · posterior · {len(phase1a)} blue / {len(other)} grey',
        '3quarter':  f'PHASE 1a SUBSET · posterior-right oblique · {len(phase1a)} blue / {len(other)} grey',
    }
    for vn in ['sagittal', 'posterior', '3quarter']:
        out = OUT / f'muscles_{vn}.png'
        render_view(model, state, meshes, phase1a, other, vn, out)
        label_image(out, labels[vn])
        out_paths[vn] = out
        print(f'  wrote {out}')

    # Horizontal concat
    imgs = [Image.open(out_paths[v]).convert('RGB') for v in ['sagittal','posterior','3quarter']]
    W = sum(im.width for im in imgs); H = max(im.height for im in imgs)
    grid = Image.new('RGB', (W, H), (16, 16, 16))
    x = 0
    for im in imgs:
        grid.paste(im, (x, 0)); x += im.width
    grid_path = OUT / 'muscles_combined_grid.png'
    grid.save(grid_path)
    print(f'  grid {grid_path}  {grid.size[0]}x{grid.size[1]}')


if __name__ == '__main__':
    main()
