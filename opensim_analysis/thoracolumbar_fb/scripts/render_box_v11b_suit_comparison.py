"""
Box v11b Suit Comparison Video (Option C Hybrid)
=================================================
Side-by-side: B_noload (Suit OFF) | B_suit200 (Suit ON 200 N*m)

Layout 1920x900:
  Top 700px: 3D body (960px each), muscle activation color-coded
  Bottom 200px: IL_R10_r time series + ES mean bar overlay

ES muscle color: gray=0%, red=100% activation
Suit OFF: saturated red at lift phase
Suit ON:  near-zero (gray) throughout

Output:
  /data/opensim_results/video/box_v11b_suit_comparison.mp4
  /data/wearable-assist/.../docs/videos/box_v11b_suit_comparison.mp4

Usage:
  python render_box_v11b_suit_comparison.py preview
  python render_box_v11b_suit_comparison.py video
"""
import os, sys, shutil, subprocess, time
os.environ['DISPLAY'] = ':1'
from pathlib import Path
import numpy as np
import opensim as osim
import pyvista as pv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from PIL import Image

# ── Paths ──────────────────────────────────────────────────────────────────
MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim')
GEOM_DIR = Path('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry')
MOT      = '/data/stoop_motion/box_motion_v11b.mot'
BOX_STO  = '/data/stoop_motion/box_motion_v11b_box.sto'
SOL_NOLOAD  = '/data/opensim_results/phase2c4_box_v11b/B_noload/solution.sto'
SOL_SUIT200 = '/data/opensim_results/phase2c4_box_v11b/B_suit200/solution.sto'

VIDEO_DIR = Path('/data/opensim_results/video')
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
FRAME_DIR = Path('/tmp/box_v11b_cmp_frames')
OUT_MP4   = VIDEO_DIR / 'box_v11b_suit_comparison.mp4'
REPO_VIDEO = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/videos')
REPO_VIDEO.mkdir(parents=True, exist_ok=True)

# ── Render settings ─────────────────────────────────────────────────────────
FPS     = 30
# Moco covers t=1.0~4.0; render motion t=1.0~4.0 (3 seconds = 90 frames)
T_START = 1.0
T_END   = 4.0
T_TOTAL = T_END - T_START
N_FRAMES = int(FPS * T_TOTAL) + 1   # 91 frames

RES_W, RES_H = 1920, 900
TOP_H        = 700
BOT_H        = RES_H - TOP_H        # 200
PANEL_W      = RES_W // 2           # 960

ES_PREFIXES = ('/forceset/IL_', '/forceset/LTpT_', '/forceset/LTpL_')

# Key business message numbers
IL_R10_NOLOAD_PEAK  = 100.0
IL_R10_SUIT200_PEAK = 0.8


# ── Helpers: model / motion ──────────────────────────────────────────────────
def transform_to_mat(T):
    R, p = T.R(), T.p()
    M = np.eye(4)
    for i in range(3):
        for j in range(3):
            M[i, j] = R.get(i, j)
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
        out.append({
            'path': str(p),
            'frame': mesh.getFrame().getAbsolutePathString(),
            'scale': (sf.get(0), sf.get(1), sf.get(2))
        })
    return out


def apply_motion(model, state, mot_tbl, box_tbl, t):
    """Apply joint angles + realize position. Returns box pos."""
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

    # box position
    bt = list(box_tbl.getIndependentColumn())
    bidx = min(range(len(bt)), key=lambda i: abs(bt[i] - t))
    brow = box_tbl.getRowAtIndex(bidx)
    blabs = list(box_tbl.getColumnLabels())
    bpos = {l: brow[i] for i, l in enumerate(blabs)}
    return bpos


def read_activation_table(path):
    tbl = osim.TimeSeriesTable(path)
    labels = list(tbl.getColumnLabels())
    t = np.array(list(tbl.getIndependentColumn()))
    data = np.zeros((tbl.getNumRows(), tbl.getNumColumns()))
    for ri in range(tbl.getNumRows()):
        row = tbl.getRowAtIndex(ri)
        for ci in range(tbl.getNumColumns()):
            data[ri, ci] = row[ci]
    return t, labels, data


def activations_at(t_series, data, t_query):
    """Return activation row (array) at closest time."""
    idx = int(np.argmin(np.abs(t_series - t_query)))
    return data[idx, :]


# ── 3D rendering helpers ─────────────────────────────────────────────────────
def build_bone_meshes(plotter, model, state, meshes_info):
    frame_cache = {}
    for mi in meshes_info:
        fp = mi['frame']
        if fp not in frame_cache:
            try:
                frame_cache[fp] = model.getComponent(fp)
            except Exception:
                continue
    actors = []
    for mi in meshes_info:
        fp = mi['frame']
        if fp not in frame_cache:
            continue
        try:
            surf = pv.read(mi['path'])
        except Exception:
            continue
        sx, sy, sz = mi['scale']
        if (sx, sy, sz) != (1.0, 1.0, 1.0):
            surf = surf.scale([sx, sy, sz], inplace=False)
        try:
            M = transform_to_mat(frame_cache[fp].getTransformInGround(state))
            surf = surf.transform(M, inplace=False)
        except Exception:
            continue
        a = plotter.add_mesh(surf, color='#d4c5a9', opacity=0.95,
                              smooth_shading=True, specular=0.3, specular_power=15)
        actors.append(a)
    return actors


def build_muscle_pd(model, state, muscle_names, acts_arr, labels):
    """Build PyVista PolyData with activation scalar for ES muscles."""
    all_pts = []
    cells = []
    scalars = []
    muscles = model.getMuscles()
    name_to_m = {}
    for i in range(muscles.getSize()):
        m = muscles.get(i)
        name_to_m[m.getName()] = m

    for name in muscle_names:
        m = name_to_m.get(name)
        if m is None:
            continue
        # activation value
        col_key = f'/forceset/{name}/activation'
        if col_key in labels:
            cidx = labels.index(col_key)
            a = float(acts_arr[cidx])
        else:
            a = 0.0
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
        for i in range(len(pts) - 1):
            cells.extend([2, start + i, start + i + 1])
            scalars.append(a)

    if not all_pts:
        return None
    pd = pv.PolyData()
    pd.points = np.array(all_pts, dtype=float)
    pd.lines = np.array(cells, dtype=np.int64)
    pd.cell_data['activation'] = np.array(scalars, dtype=float)
    return pd


def add_box_mesh(plotter, bpos, color='#8B6914', opacity=0.85):
    """Draw 20kg box at given position."""
    tx = bpos.get('box_tx', 0.25)
    ty = bpos.get('box_ty', -0.75)
    tz = bpos.get('box_tz', 0.0)
    # Box dimensions: ~0.38x0.27x0.25m (W x H x D)
    box = pv.Box(bounds=(
        tx - 0.19, tx + 0.19,
        ty,         ty + 0.27,
        tz - 0.125, tz + 0.125
    ))
    plotter.add_mesh(box, color=color, opacity=opacity, show_edges=True,
                     edge_color='#5c4a1e', line_width=1.0)


def render_3d_panel(model, state, meshes_info, es_muscle_names,
                    acts_noload, labs_noload,
                    acts_suit200, labs_suit200,
                    bpos, out_path):
    """Render 1920x700 side-by-side 3D panel."""
    pv.global_theme.background = '#1c1c2e'
    pv.global_theme.lighting = True

    pl = pv.Plotter(shape=(1, 2), window_size=(RES_W, TOP_H),
                    off_screen=True, border=False)

    camera_pos = [
        (1.8, 0.20, 2.8),   # position
        (0.15, -0.15, 0.0), # focal
        (0.0, 1.0, 0.0),    # up
    ]

    for col, (acts_arr, labs, title, badge_color) in enumerate([
        (acts_noload,  labs_noload,  'SUIT OFF  |  B_noload', '#ff5555'),
        (acts_suit200, labs_suit200, 'SUIT ON  |  B_suit200  (200 N·m)', '#55ff55'),
    ]):
        pl.subplot(0, col)
        build_bone_meshes(pl, model, state, meshes_info)

        # ES muscles — color by activation (gray=0%, red=100%)
        pd = build_muscle_pd(model, state, es_muscle_names, acts_arr, labs)
        if pd is not None:
            pl.add_mesh(pd, scalars='activation', cmap='Reds',
                        clim=[0.0, 1.0], line_width=5.0,
                        show_scalar_bar=False)

        # Box
        add_box_mesh(pl, bpos)

        # Floor
        floor = pv.Plane(center=(0.1, -0.91, 0.0), direction=(0, 1, 0),
                         i_size=3.0, j_size=3.0)
        pl.add_mesh(floor, color='#333355', opacity=0.45,
                    show_edges=True, edge_color='#555577', line_width=0.8)

        pl.camera_position = camera_pos
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale = 1.10

        # Title badge
        pl.add_text(title, font_size=16, color=badge_color,
                    position='upper_left', font='courier')

    pl.screenshot(str(out_path))
    pl.close()


# ── Bottom overlay (matplotlib) ─────────────────────────────────────────────
def phase_info(t):
    if t < 1.0:  return 'Upright',            '#aaaaaa'
    if t < 1.8:  return 'Eccentric — lower',  '#ff8844'
    if t < 2.3:  return 'Grasp (bottom)',      '#ff4444'
    if t < 3.2:  return 'Concentric — lift',  '#44aaff'
    return              'Carry / upright',     '#44cc44'


def compute_es_mean(acts_arr, labs, es_prefixes):
    es_idx = [i for i, l in enumerate(labs)
              if any(l.startswith(p) for p in es_prefixes)]
    if not es_idx:
        return 0.0
    return float(np.mean(acts_arr[es_idx])) * 100.0


def compute_il_r10(acts_arr, labs):
    for key in ('/forceset/IL_R10_r/activation',
                'IL_R10_r/activation', '/forceset/IL_R10_r'):
        if key in labs:
            return float(acts_arr[labs.index(key)]) * 100.0
    return 0.0


def make_bottom_panel(t,
                      es_noload_pct, es_suit_pct,
                      il_noload_pct, il_suit_pct,
                      t_series, il_noload_series, il_suit_series,
                      out_path):
    """Draw 1920x200 bottom overlay with time-series + bar."""
    fig = plt.figure(figsize=(RES_W / 100, BOT_H / 100), dpi=100)
    fig.patch.set_facecolor('#0d0d1a')

    # Left: IL_R10_r time series (t=1~4s)
    ax_ts = fig.add_axes([0.02, 0.12, 0.45, 0.78])
    ax_ts.set_facecolor('#111122')
    ax_ts.plot(t_series, il_noload_series * 100, color='#ff4444',
               lw=2.0, label='IL_R10_r  Suit OFF')
    ax_ts.plot(t_series, il_suit_series * 100, color='#44cc44',
               lw=2.0, label='IL_R10_r  Suit ON')
    ax_ts.axvline(t, color='white', lw=1.5, ls='--', alpha=0.8)
    ax_ts.set_xlim(T_START, T_END)
    ax_ts.set_ylim(-2, 105)
    ax_ts.set_xlabel('Time (s)', color='white', fontsize=9)
    ax_ts.set_ylabel('IL_R10_r Activation (%)', color='white', fontsize=9)
    ax_ts.tick_params(colors='white', labelsize=8)
    for spine in ax_ts.spines.values():
        spine.set_edgecolor('#444466')
    ax_ts.legend(loc='upper right', fontsize=8, framealpha=0.3,
                 labelcolor='white', facecolor='#222233')
    # Key annotation
    ax_ts.annotate('100% -> 0.8%\n(-99 %p)',
                   xy=(2.2, 100), xytext=(2.8, 65),
                   arrowprops=dict(arrowstyle='->', color='white', lw=1.5),
                   fontsize=9, color='#ffff88',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#333355',
                             edgecolor='#ffff88', alpha=0.9))

    # Right: ES mean bar + key stats
    ax_r = fig.add_axes([0.52, 0.05, 0.46, 0.90])
    ax_r.set_xlim(0, 1); ax_r.set_ylim(0, 1); ax_r.axis('off')
    ax_r.set_facecolor('#0d0d1a')

    phase, pcol = phase_info(t)

    # Header
    ax_r.text(0.50, 0.95, 'Box Motion v11b — Suit Effect Comparison',
              fontsize=11, fontweight='bold', color='white', ha='center',
              transform=ax_r.transAxes)
    ax_r.text(0.50, 0.82,
              f't = {t:.2f} s    Phase: {phase}',
              fontsize=10, color=pcol, ha='center', transform=ax_r.transAxes)

    # ES mean bars
    bar_x0, bar_x1 = 0.12, 0.88
    bw = bar_x1 - bar_x0
    bar_h = 0.10

    # Noload bar
    y0 = 0.58
    ax_r.add_patch(plt.Rectangle((bar_x0, y0), bw, bar_h,
                                  transform=ax_r.transAxes,
                                  facecolor='#222233', edgecolor='#888888', lw=1))
    frac = min(es_noload_pct / 100.0, 1.0)
    ax_r.add_patch(plt.Rectangle((bar_x0, y0), bw * frac, bar_h,
                                  transform=ax_r.transAxes,
                                  facecolor='#ff4444', edgecolor='none', alpha=0.9))
    ax_r.text(bar_x0 - 0.01, y0 + bar_h / 2,
              f'Suit OFF  {es_noload_pct:.1f}%', fontsize=9, ha='right', va='center',
              color='#ff8888', transform=ax_r.transAxes)

    # Suit bar
    y1 = 0.38
    ax_r.add_patch(plt.Rectangle((bar_x0, y1), bw, bar_h,
                                  transform=ax_r.transAxes,
                                  facecolor='#222233', edgecolor='#888888', lw=1))
    frac2 = min(es_suit_pct / 100.0, 1.0)
    ax_r.add_patch(plt.Rectangle((bar_x0, y1), bw * frac2, bar_h,
                                  transform=ax_r.transAxes,
                                  facecolor='#44cc44', edgecolor='none', alpha=0.9))
    ax_r.text(bar_x0 - 0.01, y1 + bar_h / 2,
              f'Suit ON  {es_suit_pct:.1f}%', fontsize=9, ha='right', va='center',
              color='#88ff88', transform=ax_r.transAxes)

    # Bottom key message
    ax_r.text(0.50, 0.18,
              f'IL_R10_r: {il_noload_pct:.0f}% -> {il_suit_pct:.1f}%   '
              f'(Delta -{(il_noload_pct - il_suit_pct):.0f} %p)',
              fontsize=9, color='#ffff88', ha='center', transform=ax_r.transAxes,
              fontfamily='monospace')
    ax_r.text(0.50, 0.06,
              'Suit dose-response slope: -0.129 %/N.m  (R2=0.94)',
              fontsize=8, color='#aaaacc', ha='center', transform=ax_r.transAxes,
              fontfamily='monospace')

    fig.savefig(str(out_path), dpi=100, facecolor='#0d0d1a',
                bbox_inches='tight', pad_inches=0)
    plt.close(fig)


def composite_frame(img_3d_path, bot_path, out_path):
    img3d = Image.open(img_3d_path).convert('RGB')
    img_bot = Image.open(bot_path).convert('RGB')
    canvas = Image.new('RGB', (RES_W, RES_H), (13, 13, 26))
    # 3D panel — fit to TOP_H
    img3d_r = img3d.resize((RES_W, TOP_H), Image.LANCZOS)
    canvas.paste(img3d_r, (0, 0))
    # Bottom panel — fit to BOT_H
    img_bot_r = img_bot.resize((RES_W, BOT_H), Image.LANCZOS)
    canvas.paste(img_bot_r, (0, TOP_H))
    # Center divider line on 3D portion
    from PIL import ImageDraw
    draw = ImageDraw.Draw(canvas)
    draw.line([(RES_W // 2, 0), (RES_W // 2, TOP_H)], fill=(100, 100, 120), width=2)
    canvas.save(str(out_path), quality=95)


# ── Setup context ─────────────────────────────────────────────────────────────
def setup():
    print("Loading model...")
    model = osim.Model(MODEL)
    state = model.initSystem()
    print("Collecting meshes...")
    meshes_info = collect_meshes(model)
    print(f"  {len(meshes_info)} mesh components")

    print("Loading motion tables...")
    mot_tbl = osim.TimeSeriesTable(MOT)
    box_tbl = osim.TimeSeriesTable(BOX_STO)

    print("Loading Moco solutions...")
    t_nl, labs_nl, dat_nl = read_activation_table(SOL_NOLOAD)
    t_s2, labs_s2, dat_s2 = read_activation_table(SOL_SUIT200)
    print(f"  B_noload: t={t_nl[0]:.2f}-{t_nl[-1]:.2f}s, N={len(t_nl)}")
    print(f"  B_suit200: t={t_s2[0]:.2f}-{t_s2[-1]:.2f}s, N={len(t_s2)}")

    # ES muscle names (full activation column key based lookup)
    es_muscle_names = []
    muscles = model.getMuscles()
    for i in range(muscles.getSize()):
        mn = muscles.get(i).getName()
        col = f'/forceset/{mn}/activation'
        if col in labs_nl and any(col.startswith(f'/forceset{p[8:]}') for p in
                                   ['/forceset/IL_', '/forceset/LTpT_', '/forceset/LTpL_']):
            es_muscle_names.append(mn)
    # simpler: use prefix on name
    es_muscle_names = [muscles.get(i).getName() for i in range(muscles.getSize())
                       if any(muscles.get(i).getName().startswith(p)
                              for p in ('IL_', 'LTpT_', 'LTpL_'))]
    print(f"  ES muscles: {len(es_muscle_names)}")

    # Pre-build IL_R10_r series for overlay
    il_r10_key_nl  = '/forceset/IL_R10_r/activation'
    il_r10_key_s2  = '/forceset/IL_R10_r/activation'
    il_nl_idx  = labs_nl.index(il_r10_key_nl)  if il_r10_key_nl  in labs_nl  else None
    il_s2_idx  = labs_s2.index(il_r10_key_s2)  if il_r10_key_s2  in labs_s2  else None

    il_nl_series = dat_nl[:, il_nl_idx] if il_nl_idx is not None else np.zeros(len(t_nl))
    il_s2_series = dat_s2[:, il_s2_idx] if il_s2_idx is not None else np.zeros(len(t_s2))

    return {
        'model': model, 'state': state,
        'meshes_info': meshes_info,
        'mot_tbl': mot_tbl, 'box_tbl': box_tbl,
        't_nl': t_nl, 'labs_nl': labs_nl, 'dat_nl': dat_nl,
        't_s2': t_s2, 'labs_s2': labs_s2, 'dat_s2': dat_s2,
        'es_muscle_names': es_muscle_names,
        'il_nl_series': il_nl_series, 'il_s2_series': il_s2_series,
    }


def render_one_frame(t, frame_path, ctx, tmp_dir):
    model   = ctx['model']
    state   = ctx['state']
    meshes_info = ctx['meshes_info']
    mot_tbl = ctx['mot_tbl']
    box_tbl = ctx['box_tbl']
    t_nl    = ctx['t_nl'];  labs_nl = ctx['labs_nl'];  dat_nl = ctx['dat_nl']
    t_s2    = ctx['t_s2'];  labs_s2 = ctx['labs_s2'];  dat_s2 = ctx['dat_s2']
    es_names = ctx['es_muscle_names']

    # Apply motion
    bpos = apply_motion(model, state, mot_tbl, box_tbl, t)

    # Get activations at time t
    acts_nl = activations_at(t_nl, dat_nl, t)
    acts_s2 = activations_at(t_s2, dat_s2, t)

    # Compute ES mean and IL_R10
    es_nl  = compute_es_mean(acts_nl, labs_nl, ES_PREFIXES)
    es_s2  = compute_es_mean(acts_s2, labs_s2, ES_PREFIXES)
    il_nl  = compute_il_r10(acts_nl, labs_nl)
    il_s2  = compute_il_r10(acts_s2, labs_s2)

    # 3D render
    tmp_3d  = Path(tmp_dir) / 'tmp_3d.png'
    tmp_bot = Path(tmp_dir) / 'tmp_bot.png'
    render_3d_panel(model, state, meshes_info, es_names,
                    acts_nl, labs_nl, acts_s2, labs_s2, bpos, tmp_3d)

    # Bottom overlay
    make_bottom_panel(t, es_nl, es_s2, il_nl, il_s2,
                      ctx['t_nl'], ctx['il_nl_series'], ctx['il_s2_series'],
                      tmp_bot)

    # Composite
    composite_frame(tmp_3d, tmp_bot, frame_path)
    return es_nl, es_s2, il_nl, il_s2


# ── Preview mode ──────────────────────────────────────────────────────────────
def preview():
    ctx = setup()
    tmp_dir = Path('/tmp/box_v11b_cmp_preview')
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # 5 representative frames
    preview_times = [1.0, 1.5, 2.0, 3.0, 4.0]
    frames = []
    for i, t in enumerate(preview_times):
        fpath = tmp_dir / f'preview_{i}.png'
        es_nl, es_s2, il_nl, il_s2 = render_one_frame(t, fpath, ctx, tmp_dir)
        print(f"  t={t:.1f}s  ES: {es_nl:.1f}% -> {es_s2:.1f}%  "
              f"IL_R10: {il_nl:.1f}% -> {il_s2:.1f}%")
        frames.append(Image.open(fpath).convert('RGB'))

    # Vertical stack
    W = frames[0].width
    H = frames[0].height
    canvas = Image.new('RGB', (W, H * len(frames)), (13, 13, 26))
    for i, f in enumerate(frames):
        canvas.paste(f, (0, i * H))
    out = Path('/data/opensim_results/box_v11b_suit_cmp_preview.png')
    canvas.save(str(out))
    print(f"\nPreview saved: {out}  ({canvas.size[0]}x{canvas.size[1]})")
    return str(out)


# ── Video mode ────────────────────────────────────────────────────────────────
def video():
    ctx = setup()

    if FRAME_DIR.exists():
        shutil.rmtree(FRAME_DIR)
    FRAME_DIR.mkdir(parents=True)

    tmp_work = Path('/tmp/box_v11b_cmp_work')
    tmp_work.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    for fi in range(N_FRAMES):
        t = T_START + fi / FPS
        frame_path = FRAME_DIR / f'frame_{fi:04d}.png'
        es_nl, es_s2, il_nl, il_s2 = render_one_frame(t, frame_path, ctx, tmp_work)
        if fi % 15 == 0:
            el = time.time() - t0
            eta = el / (fi + 1) * (N_FRAMES - fi - 1)
            print(f"  [{fi+1:03d}/{N_FRAMES}] t={t:.2f}s  "
                  f"ES: {es_nl:.1f}%->{es_s2:.1f}%  "
                  f"IL_R10: {il_nl:.1f}%->{il_s2:.1f}%  "
                  f"el={el:.0f}s ETA={eta:.0f}s")

    print(f"All frames done in {time.time()-t0:.1f}s")

    # ffmpeg encode
    cmd = [
        'ffmpeg', '-y', '-loglevel', 'warning',
        '-framerate', str(FPS),
        '-i', str(FRAME_DIR / 'frame_%04d.png'),
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-crf', '17', '-preset', 'medium',
        '-movflags', '+faststart',
        str(OUT_MP4),
    ]
    subprocess.run(cmd, check=True)
    file_mb = OUT_MP4.stat().st_size / 1e6
    print(f"Wrote {OUT_MP4}  ({file_mb:.1f} MB)")

    # Copy to repo
    import shutil as _sh
    repo_mp4 = REPO_VIDEO / 'box_v11b_suit_comparison.mp4'
    _sh.copy2(str(OUT_MP4), str(repo_mp4))
    print(f"Copied to repo: {repo_mp4}")
    return str(OUT_MP4)


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'preview'
    if mode == 'preview':
        preview()
    elif mode == 'video':
        video()
    else:
        print("Usage: render_box_v11b_suit_comparison.py preview|video")
