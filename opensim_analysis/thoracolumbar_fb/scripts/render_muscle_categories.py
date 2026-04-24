"""Reusable renderer: highlight a subset of muscles by category with colors.

Usage (Phase 1a example):
    from render_muscle_categories import render_categories, CategorySpec

    categories = [
        CategorySpec('IL',   'IL_',   '#1f77b4', 'iliocostalis'),
        CategorySpec('LTpT', 'LTpT_', '#17becf', 'longissimus thoracis'),
        CategorySpec('LTpL', 'LTpL_', '#87ceeb', 'longissimus lumborum'),
        CategorySpec('QL',   'QL_',   '#9467bd', 'quadratus lumborum'),
        CategorySpec('RA',   None,    '#ff7f0e', 'rectus abdominis',
                     exact=['rect_abd_r','rect_abd_l']),
    ]
    render_categories(model_path, categories, out_dir, phase_label='Phase 1a',
                      grey_opacity=0.25)
"""
import os
os.environ.setdefault('DISPLAY', ':1')
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import numpy as np
import opensim as osim
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont

GEOM_DIR = Path('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry')

VIEWS = {
    'sagittal':  ((0.0, -0.1, 4.0),   (0.0, -0.1, 0.0), 1.2),
    'posterior': ((-4.0, -0.1, 0.0),  (0.0, -0.1, 0.0), 1.2),
    '3quarter':  ((-3.0, 0.1, 3.0),   (0.0, -0.1, 0.0), 1.2),  # posterior-right oblique
}
RES_W, RES_H = 1600, 2200


@dataclass
class CategorySpec:
    name: str
    prefix: Optional[str]          # e.g. 'IL_'. Set to None if using exact names only.
    color: str                     # hex color for the PolyData render
    display: str                   # human-readable description for legend
    exact: List[str] = field(default_factory=list)  # additional exact-name matches


def _transform_to_mat(T):
    R, p = T.R(), T.p()
    M = np.eye(4)
    for i in range(3):
        for j in range(3): M[i, j] = R.get(i, j)
        M[i, 3] = p.get(i)
    return M


def _collect_meshes(model):
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
        out.append({'path': str(p),
                    'frame': mesh.getFrame().getAbsolutePathString(),
                    'scale': (sf.get(0), sf.get(1), sf.get(2))})
    return out


def _muscle_polydata(model, state, name_set):
    all_pts = []; cells = []
    ms = model.getMuscles()
    for i in range(ms.getSize()):
        m = ms.get(i)
        if m.getName() not in name_set:
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


def _match_category(model, cat: CategorySpec):
    ms = model.getMuscles()
    names = [ms.get(i).getName() for i in range(ms.getSize())]
    out = set(cat.exact)
    if cat.prefix:
        out.update(n for n in names if n.startswith(cat.prefix))
    return out


def _render_view(model, state, meshes, cat_name_sets, other_set,
                 view_name, out_path, grey_opacity=0.25):
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
        M = _transform_to_mat(frame_cache[mi['frame']].getTransformInGround(state))
        surf = surf.transform(M, inplace=False)
        pl.add_mesh(surf, color='ivory', opacity=1.0, smooth_shading=True,
                    specular=0.2, specular_power=10)

    # other muscles (grey)
    if other_set:
        pd = _muscle_polydata(model, state, other_set)
        if pd is not None:
            pl.add_mesh(pd, color='#cccccc', opacity=grey_opacity, line_width=1.0)

    # per-category muscles (each color)
    for (cat, name_set, color) in cat_name_sets:
        pd = _muscle_polydata(model, state, name_set)
        if pd is not None:
            pl.add_mesh(pd, color=color, opacity=0.95, line_width=2.4)

    pl.camera_position = [cam_pos, focal, (0, 1, 0)]
    pl.camera.parallel_projection = True
    pl.camera.parallel_scale = pscale
    pl.screenshot(str(out_path))
    pl.close()


def _label_image(path, text, pad=42):
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


def _legend_banner(width, categories, cat_counts, phase_label):
    """Render a legend banner with colored swatches + counts."""
    banner_h = 90
    banner = Image.new('RGB', (width, banner_h), (28, 28, 36))
    draw = ImageDraw.Draw(banner)
    try:
        font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
        font_sm  = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
    except Exception:
        font_big = ImageFont.load_default()
        font_sm  = ImageFont.load_default()
    total = sum(cat_counts.values())
    draw.text((20, 10), f'{phase_label}  —  {total} muscles selected',
              fill=(250, 250, 250), font=font_big)

    x = 20; y = 50
    for cat in categories:
        # swatch
        sw_size = 24
        draw.rectangle([x, y, x + sw_size, y + sw_size], fill=cat.color,
                       outline=(255, 255, 255))
        x += sw_size + 8
        label = f'{cat.name} ({cat_counts.get(cat.name, 0)})'
        draw.text((x, y + 2), label, fill=(235, 235, 235), font=font_sm)
        tw = int(font_sm.getlength(label))
        x += tw + 24
    return banner


def render_categories(model_path: str, categories: List[CategorySpec],
                      out_dir: Path, phase_label: str = 'Subset',
                      grey_opacity: float = 0.25,
                      out_prefix: str = 'muscles') -> Path:
    """Render 3 views + combined grid with per-category coloring.

    Returns path to the combined grid image.
    """
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    model = osim.Model(model_path); state = model.initSystem()
    meshes = _collect_meshes(model)
    ms = model.getMuscles()
    all_names = {ms.get(i).getName() for i in range(ms.getSize())}

    # resolve each category's name set
    cat_name_sets = []
    cat_counts = {}
    selected = set()
    for cat in categories:
        ns = _match_category(model, cat)
        cat_name_sets.append((cat, ns, cat.color))
        cat_counts[cat.name] = len(ns)
        selected |= ns
    other = all_names - selected

    print(f'{phase_label}: {len(selected)} selected / {len(other)} other / {len(all_names)} total')
    for cat in categories:
        print(f'  {cat.name:8s} ({cat.display}): {cat_counts[cat.name]}  color={cat.color}')

    out_paths = {}
    for vn in ['sagittal', 'posterior', '3quarter']:
        p = out_dir / f'{out_prefix}_{vn}_colored.png'
        _render_view(model, state, meshes, cat_name_sets, other, vn, p,
                     grey_opacity=grey_opacity)
        _label_image(p, f'{phase_label} · {vn}  ({len(selected)} colored / {len(other)} grey)')
        out_paths[vn] = p
        print(f'  wrote {p}')

    # composite grid with legend on top
    imgs = [Image.open(out_paths[v]).convert('RGB') for v in ['sagittal','posterior','3quarter']]
    grid_w = sum(im.width for im in imgs); grid_h = max(im.height for im in imgs)
    legend = _legend_banner(grid_w, categories, cat_counts, phase_label)
    grid = Image.new('RGB', (grid_w, grid_h + legend.height), (16, 16, 16))
    grid.paste(legend, (0, 0))
    x = 0
    for im in imgs:
        grid.paste(im, (x, legend.height)); x += im.width
    grid_path = out_dir / f'{out_prefix}_combined_grid_colored.png'
    grid.save(grid_path)
    print(f'  grid {grid_path}  {grid.size[0]}x{grid.size[1]}')
    return grid_path


# ---------------- Phase 1a invocation ----------------
if __name__ == '__main__':
    MODEL = '/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_moco_stoop.osim'
    OUT = Path('/data/opensim_results/moco_phase1a_verification')

    categories = [
        CategorySpec('IL',   'IL_',   '#1f77b4', 'iliocostalis'),
        CategorySpec('LTpT', 'LTpT_', '#17becf', 'longissimus thoracis'),
        CategorySpec('LTpL', 'LTpL_', '#87ceeb', 'longissimus lumborum'),
        CategorySpec('QL',   'QL_',   '#9467bd', 'quadratus lumborum'),
        CategorySpec('RA',   None,    '#ff7f0e', 'rectus abdominis',
                     exact=['rect_abd_r', 'rect_abd_l']),
    ]
    render_categories(MODEL, categories, OUT,
                      phase_label='Phase 1a',
                      grey_opacity=0.25,
                      out_prefix='muscles')
