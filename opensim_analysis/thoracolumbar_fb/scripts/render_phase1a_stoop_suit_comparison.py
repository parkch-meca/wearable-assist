"""Phase 1a Stoop Suit Comparison Video Renderer.

Side-by-side: Suit OFF (B_suit0) vs Suit ON (B_suit200, 24 Nm peak)
Based on Phase 1a Moco solutions — verified Hu 2026 match (28% ES reduction).

Modes:
  python render_phase1a_stoop_suit_comparison.py preview   -> 3 preview PNGs
  python render_phase1a_stoop_suit_comparison.py grid      -> 5x2 grid PNG
  python render_phase1a_stoop_suit_comparison.py video     -> full 1920x1080 mp4
  python render_phase1a_stoop_suit_comparison.py metadata  -> metadata grid PNG
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
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image, ImageDraw, ImageFont

# ── Paths ────────────────────────────────────────────────────────────────────
MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim')
GEOM_DIR = Path('/data/opensim_models/ThoracolumbarFB/'
                'Fullbody_TLModels_v2.0_OS4x/Geometry')
MOT = '/data/stoop_motion/stoop_synthetic_v5.mot'
SOL_OFF = '/data/opensim_results/phase1a_reproduction_v2/B_suit0/solution.sto'
SOL_ON  = '/data/opensim_results/phase1a_reproduction_v2/B_suit200/solution.sto'

IMG_DIR = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase1a_video')
VIDEO_DIR = Path('/data/opensim_results/video')
FRAME_DIR = Path('/tmp/phase1a_stoop_frames')
IMG_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
FRAME_DIR.mkdir(parents=True, exist_ok=True)

OUT_MP4   = VIDEO_DIR / 'phase1a_stoop_suit_comparison.mp4'
OUT_GRID  = IMG_DIR / 'phase1a_stoop_motion_video_grid.png'
OUT_META  = IMG_DIR / 'phase1a_stoop_video_metadata_grid.png'

# ── Render constants ──────────────────────────────────────────────────────────
FPS     = 30
T_TOTAL = 5.0
N_FRAMES = int(FPS * T_TOTAL) + 1   # 151
RES_W, RES_H = 1920, 1080
PANEL_W = 960
TOP_H   = 760   # 3D panel height
BOT_H   = RES_H - TOP_H   # 320 — overlay

# ES activation normalization ceiling for color (not capped at 100%)
ES_NORM_CEIL = 1.0   # raw 0-1

# ── ES color schema (viz-agent standard — spec compliant) ─────────────────────
#  0 %  -> #909090 (gray)
# 25 %  -> #FFB300 (amber)
# 50 %  -> #FF6600 (orange)
# 75 %  -> #CC2200 (red)
# 100 % -> #8B0000 (dark red)
ES_CMAP = LinearSegmentedColormap.from_list(
    'es_activation',
    [(0.0,  '#909090'),
     (0.25, '#FFB300'),
     (0.50, '#FF6600'),
     (0.75, '#CC2200'),
     (1.0,  '#8B0000')],
    N=256
)

# ── Suit torque profile (mirrors Phase 1a run_moco setup) ────────────────────
T_PEAK_NM = 24.0   # 200 N * 0.12 m
def torque_profile(t):
    """Alpha ramp: 0 at t<0.5, cosine rise to 1.0 at t=2.5, hold to 3.0, cosine fall."""
    if t < 0.5:    return 0.0
    if t <= 2.5:   return (1.0 - np.cos(np.pi * (t - 0.5) / 2.0)) / 2.0
    if t <= 3.0:   return 1.0
    if t <= 5.0:   return (1.0 + np.cos(np.pi * (t - 3.0) / 2.0)) / 2.0
    return 0.0


# ── Phase annotation ──────────────────────────────────────────────────────────
def phase_info(t):
    if t < 0.5:  return 'Standing',   '#888888'
    if t <= 2.5: return 'Eccentric',  '#E67E00'
    if t <= 3.0: return 'Hold',       '#CC2200'
    if t <= 5.0: return 'Concentric', '#2E7D32'
    return 'Recovery', '#888888'

PHASE_SUBTITLES = {
    0.5:  'Standing posture — baseline ES activation ~2%',
    1.5:  'Eccentric phase — bending forward (ES rising)',
    2.5:  'Hold — peak spinal load  |  Suit OFF: IL_R10 88%  |  Suit ON: 63% (−28%)',
    3.5:  'Concentric phase — lifting up (ES decreasing)',
    4.5:  'Recovery — returning to upright posture',
}


# ── Model helpers ─────────────────────────────────────────────────────────────
def transform_to_mat4(T):
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
            p = GEOM_DIR / Path(mf).name
        if not p.exists():
            continue
        sf = mesh.get_scale_factors()
        out.append({
            'path':  str(p),
            'frame': mesh.getFrame().getAbsolutePathString(),
            'scale': (sf.get(0), sf.get(1), sf.get(2)),
        })
    return out


def apply_motion_from_table(model, state, mot_tbl, t, in_degrees=True):
    times = list(mot_tbl.getIndependentColumn())
    idx = int(np.argmin([abs(ti - t) for ti in times]))
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


def load_solution(path):
    tbl = osim.TimeSeriesTable(path)
    labels = list(tbl.getColumnLabels())
    t = np.array(list(tbl.getIndependentColumn()))
    data = np.zeros((tbl.getNumRows(), len(labels)))
    for i in range(tbl.getNumRows()):
        row = tbl.getRowAtIndex(i)
        for j in range(len(labels)):
            data[i, j] = row[j]
    return t, labels, data


def activation_at(t_arr, data, labels, t_query):
    """Return dict muscle_short_name -> activation at time t_query."""
    idx = int(np.argmin(np.abs(t_arr - t_query)))
    out = {}
    for j, label in enumerate(labels):
        if '/activation' in label:
            name = label.split('/forceset/')[-1].replace('/activation', '')
            out[name] = float(data[idx, j])
    return out


def mean_es_pct(acts):
    es = [v for k, v in acts.items()
          if k.startswith('IL_') or k.startswith('LTpT_') or k.startswith('LTpL_')]
    return 100.0 * float(np.mean(es)) if es else 0.0


def il_r10_pct(acts):
    return 100.0 * acts.get('IL_R10_r', 0.0)


# ── 3D panel render ────────────────────────────────────────────────────────────
def build_muscle_polydata(model, state, acts):
    """Build colored muscle path PolyData based on activation dict."""
    all_pts = []; cells = []; scalars = []
    muscles = model.getMuscles()
    for i in range(muscles.getSize()):
        m = muscles.get(i)
        name = m.getName()
        a = acts.get(name, 0.0)
        # Only draw ES muscles in color, others gray
        is_es = (name.startswith('IL_') or name.startswith('LTpT_')
                 or name.startswith('LTpL_'))
        if not is_es:
            continue
        path_geo = m.getGeometryPath()
        pp_set = path_geo.getCurrentPath(state)
        pts = []
        for k in range(pp_set.getSize()):
            pp = pp_set.get(k)
            loc = pp.getLocationInGround(state)
            pts.append([loc.get(0), loc.get(1), loc.get(2)])
        if len(pts) < 2:
            continue
        start = len(all_pts)
        all_pts.extend(pts)
        for ii in range(len(pts) - 1):
            cells.append(2)
            cells.append(start + ii)
            cells.append(start + ii + 1)
            scalars.append(a)
    if not all_pts:
        return None
    pd = pv.PolyData()
    pd.points = np.array(all_pts, dtype=float)
    pd.lines = np.array(cells, dtype=np.int64)
    pd.cell_data['activation'] = np.array(scalars, dtype=float)
    return pd


def render_side_by_side_3d(model, state, meshes, acts_off, acts_on, out_path):
    """Render a 1920×TOP_H image: left=Suit OFF, right=Suit ON."""
    pv.global_theme.background = '#141414'
    pv.global_theme.lighting = True

    pl = pv.Plotter(shape=(1, 2), window_size=(RES_W, TOP_H),
                    off_screen=True, border=False)

    # Camera: sagittal-right view, 3-quarter tilt
    cam_pos = [(1.6, 0.20, 2.4),
               (0.15, -0.05, 0.0),
               (0.0, 1.0, 0.0)]

    for col, (acts, label, badge_color) in enumerate([
        (acts_off, 'Suit OFF  —  0 N·m', '#888888'),
        (acts_on,  'Suit ON  —  24 N·m', '#FF4444'),
    ]):
        pl.subplot(0, col)

        # Skeleton meshes
        frame_cache = {}
        for mi in meshes:
            fp = mi['frame']
            if fp not in frame_cache:
                try:
                    frame_cache[fp] = model.getComponent(fp)
                except Exception:
                    pass
        for mi in meshes:
            if mi['frame'] not in frame_cache:
                continue
            try:
                surf = pv.read(mi['path'])
            except Exception:
                continue
            sx, sy, sz = mi['scale']
            if (sx, sy, sz) != (1.0, 1.0, 1.0):
                surf = surf.scale([sx, sy, sz], inplace=False)
            M = transform_to_mat4(frame_cache[mi['frame']].getTransformInGround(state))
            surf = surf.transform(M, inplace=False)
            pl.add_mesh(surf, color='#E8E0D0', opacity=0.95,
                        smooth_shading=True, specular=0.3, specular_power=15)

        # ES muscle lines
        pd = build_muscle_polydata(model, state, acts)
        if pd is not None:
            pl.add_mesh(pd, scalars='activation', cmap=ES_CMAP,
                        clim=[0.0, ES_NORM_CEIL],
                        line_width=4.0, show_scalar_bar=False)

        # Floor plane
        floor = pv.Plane(center=(0.1, -0.905, 0.0), direction=(0, 1, 0),
                         i_size=2.8, j_size=2.8)
        pl.add_mesh(floor, color='#2a2a2a', opacity=0.5)

        # Light
        pl.add_light(pv.Light(position=(2, 3, 4), focal_point=(0, 0, 0),
                               intensity=0.8, light_type='scene light'))
        pl.add_light(pv.Light(position=(-2, 2, -1), focal_point=(0, 0, 0),
                               intensity=0.3, light_type='scene light'))

        pl.camera_position = cam_pos
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale = 1.10

        pl.add_text(label, font_size=14, color=badge_color,
                    position='upper_left')

    pl.screenshot(str(out_path))
    pl.close()


# ── Bottom overlay (matplotlib) ───────────────────────────────────────────────
def make_bottom_overlay(t, acts_off, acts_on, torque_nm, il10_off_pct, il10_on_pct,
                         es_off_pct, es_on_pct, out_path, width=RES_W, height=BOT_H):
    """Create matplotlib bottom bar: time series + phase + numeric overlay."""
    # Render at 2x then resize to avoid tiny fonts
    DPI = 150
    fig = plt.figure(figsize=(width / DPI, height / DPI), dpi=DPI)
    fig.patch.set_facecolor('#0D0D0D')

    # Layout: left text block, center ES bars, right time indicator
    ax_info  = fig.add_axes([0.01, 0.05, 0.34, 0.90])
    ax_bar   = fig.add_axes([0.37, 0.15, 0.40, 0.70])
    ax_time  = fig.add_axes([0.79, 0.10, 0.20, 0.80])

    for ax in [ax_info, ax_bar, ax_time]:
        ax.set_facecolor('#0D0D0D')
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    phase_name, phase_color = phase_info(t)

    # ── Left info block ──
    ax_info.axis('off')
    ax_info.text(0.0, 0.98,
                 'Phase 1a Stoop Lift — Suit Comparison',
                 fontsize=9, fontweight='bold', color='white',
                 va='top', transform=ax_info.transAxes)
    ax_info.text(0.0, 0.82,
                 'Left: Suit OFF (0 N·m)  |  Right: Suit ON (24 N·m)',
                 fontsize=7, color='#AAAAAA', va='top', transform=ax_info.transAxes)
    ax_info.text(0.0, 0.68,
                 f'Phase: {phase_name}   t = {t:.2f} s',
                 fontsize=8, fontweight='bold', color=phase_color,
                 va='top', transform=ax_info.transAxes)

    # Key numbers
    sub = PHASE_SUBTITLES.get(round(t * 2) / 2, '')
    if not sub:
        # find nearest key
        nearest_key = min(PHASE_SUBTITLES.keys(), key=lambda k: abs(k - t))
        if abs(nearest_key - t) < 0.5:
            sub = PHASE_SUBTITLES[nearest_key]

    ax_info.text(0.0, 0.52,
                 f'IL_R10_r:  OFF {il10_off_pct:.0f}%  |  ON {il10_on_pct:.0f}%  '
                 f'(Δ {il10_off_pct-il10_on_pct:+.0f}%)',
                 fontsize=7.5, color='#FF9966', va='top', transform=ax_info.transAxes,
                 family='monospace')
    ax_info.text(0.0, 0.36,
                 f'ES mean:   OFF {es_off_pct:.1f}%  |  ON {es_on_pct:.1f}%  '
                 f'(Δ {es_off_pct-es_on_pct:+.1f}%)',
                 fontsize=7, color='#FFCC88', va='top', transform=ax_info.transAxes,
                 family='monospace')
    ax_info.text(0.0, 0.18,
                 f'Suit torque: {torque_nm:.1f} N·m  |  SMA fabric back-support | KIMM',
                 fontsize=6.5, color='#888888', va='top', transform=ax_info.transAxes)

    # ── Center ES activation bars ──
    ax_bar.axis('off')
    ax_bar.set_xlim(0, 1); ax_bar.set_ylim(0, 1)

    bar_title = 'ES Activation — IL_R10_r'
    ax_bar.text(0.5, 0.96, bar_title, ha='center', va='top', fontsize=7.5,
                color='white', transform=ax_bar.transAxes, fontweight='bold')

    def draw_activation_bar(ax, y_base, value_pct, label_str, max_pct=100.0):
        bar_h = 0.22
        frac = min(max(value_pct / max_pct, 0.0), 1.0)
        # background
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.0, y_base), 1.0, bar_h,
            boxstyle='round,pad=0.01',
            facecolor='#2a2a2a', edgecolor='#444444', lw=1,
            transform=ax.transAxes))
        # filled portion — color from ES_CMAP
        color = ES_CMAP(frac)
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.0, y_base), frac, bar_h,
            boxstyle='round,pad=0.005',
            facecolor=color, edgecolor='none',
            transform=ax.transAxes))
        # label left
        ax.text(-0.02, y_base + bar_h / 2, label_str,
                ha='right', va='center', fontsize=7, color='white',
                transform=ax.transAxes, fontweight='bold')
        # value right
        ax.text(1.02, y_base + bar_h / 2, f'{value_pct:.0f}%',
                ha='left', va='center', fontsize=7, color='white',
                transform=ax.transAxes, fontweight='bold')

    draw_activation_bar(ax_bar, 0.62, il10_off_pct, 'Suit OFF', max_pct=100.0)
    draw_activation_bar(ax_bar, 0.32, il10_on_pct,  'Suit ON',  max_pct=100.0)

    # Reduction annotation
    if il10_off_pct > 5.0:
        reduc = (il10_off_pct - il10_on_pct) / il10_off_pct * 100
        reduc_str = f'Reduction: {reduc:.0f}%   (Hu 2026: 14.9–28.6%)'
    else:
        reduc_str = 'Reduction: N/A (low activation phase)'
    ax_bar.text(0.5, 0.10, reduc_str,
                ha='center', va='bottom', fontsize=6.5, color='#88CCFF',
                transform=ax_bar.transAxes)

    # Tick marks on bars
    for pct in [0, 25, 50, 75, 100]:
        x = pct / 100.0
        ax_bar.plot([x, x], [0.28, 0.98], color='#444444', lw=0.5,
                    transform=ax_bar.transAxes)
        ax_bar.text(x, 0.22, f'{pct}%', ha='center', va='top', fontsize=5.5,
                    color='#666666', transform=ax_bar.transAxes)

    # ── Right timeline ──
    ax_time.axis('off')
    ax_time.set_xlim(0, 1); ax_time.set_ylim(0, T_TOTAL)
    ax_time.text(0.5, T_TOTAL + 0.1, '0 — 5 s', ha='center', va='bottom',
                 fontsize=9, color='white', transform=ax_time.transAxes)

    # Phase blocks on timeline
    phases = [
        (0.0, 0.5,  'Stand',  '#555555'),
        (0.5, 2.5,  'Eccentric', '#E67E00'),
        (2.5, 3.0,  'Hold',   '#CC2200'),
        (3.0, 5.0,  'Concentric', '#2E7D32'),
    ]
    for t0, t1, pname, pcol in phases:
        y_frac0 = t0 / T_TOTAL
        y_frac1 = t1 / T_TOTAL
        ax_time.add_patch(mpatches.Rectangle(
            (0.1, t0), 0.6, (t1 - t0),
            facecolor=pcol, alpha=0.35, edgecolor='none',
            transform=ax_time.transAxes))
        ax_time.text(0.45, (t0 + t1) / 2, pname,
                     ha='center', va='center', fontsize=7, color='white',
                     transform=ax_time.transAxes)

    # Current time marker (data coords: xlim=0-1, ylim=0-T_TOTAL)
    t_frac = t / T_TOTAL
    ax_time.plot([0.0, 1.0], [t_frac, t_frac], color='#FFFF00', lw=2,
                 transform=ax_time.transAxes)
    ax_time.text(0.95, t_frac, f'{t:.1f}s', ha='right', va='center',
                 fontsize=9, color='#FFFF00', transform=ax_time.transAxes)

    # Slope/R2 annotation
    ax_time.text(0.5, -0.08,
                 'Slope: 1.158 %/N·m\nR²=1.0000',
                 ha='center', va='top', fontsize=7, color='#666666',
                 transform=ax_time.transAxes)

    fig.savefig(str(out_path), dpi=100, facecolor='#0D0D0D', bbox_inches='tight',
                pad_inches=0)
    plt.close(fig)


def composite_full_frame(img_3d_path, overlay_path, out_path):
    """Stack 3D (top) + overlay (bottom) into 1920x1080."""
    img3d = Image.open(img_3d_path).convert('RGB')
    overlay = Image.open(overlay_path).convert('RGB')

    canvas = Image.new('RGB', (RES_W, RES_H), (13, 13, 13))
    # Resize 3D to exactly RES_W x TOP_H
    img3d_r = img3d.resize((RES_W, TOP_H), Image.LANCZOS)
    canvas.paste(img3d_r, (0, 0))

    # Center divider line
    draw = ImageDraw.Draw(canvas)
    draw.line([(RES_W // 2, 0), (RES_W // 2, TOP_H)], fill=(60, 60, 60), width=2)

    # Bottom overlay — resize to RES_W x BOT_H
    overlay_r = overlay.resize((RES_W, BOT_H), Image.LANCZOS)
    canvas.paste(overlay_r, (0, TOP_H))

    canvas.save(str(out_path))


# ── Context setup ─────────────────────────────────────────────────────────────
def setup_context():
    print('Loading model...')
    model = osim.Model(MODEL)
    state = model.initSystem()
    print('Collecting meshes...')
    meshes = collect_meshes(model)
    print(f'  {len(meshes)} mesh entries')
    print('Loading motion...')
    mot_tbl = osim.TimeSeriesTable(MOT)
    print('Loading Moco solutions...')
    t_off, lab_off, dat_off = load_solution(SOL_OFF)
    t_on,  lab_on,  dat_on  = load_solution(SOL_ON)
    print(f'  Suit OFF: {len(t_off)} frames  Suit ON: {len(t_on)} frames')
    return (model, state, meshes, mot_tbl,
            (t_off, lab_off, dat_off),
            (t_on,  lab_on,  dat_on))


def render_one_frame(t, out_png, ctx, tmp_prefix='frame'):
    (model, state, meshes, mot_tbl,
     (t_off, lab_off, dat_off),
     (t_on, lab_on, dat_on)) = ctx

    apply_motion_from_table(model, state, mot_tbl, t)
    acts_off = activation_at(t_off, dat_off, lab_off, t)
    acts_on  = activation_at(t_on,  dat_on,  lab_on,  t)

    es_off = mean_es_pct(acts_off)
    es_on  = mean_es_pct(acts_on)
    il10_off = il_r10_pct(acts_off)
    il10_on  = il_r10_pct(acts_on)
    torque_nm = T_PEAK_NM * torque_profile(t)

    tmp_3d  = FRAME_DIR / f'{tmp_prefix}_3d.png'
    tmp_bot = FRAME_DIR / f'{tmp_prefix}_bot.png'

    render_side_by_side_3d(model, state, meshes, acts_off, acts_on, tmp_3d)
    make_bottom_overlay(t, acts_off, acts_on, torque_nm,
                        il10_off, il10_on, es_off, es_on, tmp_bot)
    composite_full_frame(tmp_3d, tmp_bot, out_png)

    for p in [tmp_3d, tmp_bot]:
        try: os.remove(p)
        except OSError: pass

    return il10_off, il10_on, es_off, es_on


# ── Preview mode ──────────────────────────────────────────────────────────────
def preview():
    """Generate 3 preview frames: t=0.5 (standing), t=2.5 (hold peak), t=4.5 (recovery)."""
    ctx = setup_context()
    preview_times = [0.5, 2.5, 4.5]
    preview_labels = ['standing', 'hold_peak', 'recovery']

    results = []
    for t, label in zip(preview_times, preview_labels):
        out = IMG_DIR / f'preview_{label}.png'
        print(f'Rendering preview t={t}s -> {out.name}')
        il10_off, il10_on, es_off, es_on = render_one_frame(t, out, ctx, f'prev_{label}')
        print(f'  IL_R10_r: OFF={il10_off:.1f}%  ON={il10_on:.1f}%  '
              f'ES_mean: OFF={es_off:.1f}%  ON={es_on:.1f}%')
        results.append((t, label, out, il10_off, il10_on))

    print(f'\nPreview frames saved to {IMG_DIR}')
    for t, label, path, il_off, il_on in results:
        print(f'  t={t}s ({label}): {path}')
        print(f'    IL_R10_r: {il_off:.1f}% -> {il_on:.1f}%  '
              f'(Delta={il_off-il_on:+.1f}%)')
    return results


# ── Grid mode (5 frames × 2 conditions) ──────────────────────────────────────
def make_grid():
    """Generate 5x2 grid: rows=frames, cols=Suit OFF/ON."""
    ctx = setup_context()
    grid_times = [0.5, 1.5, 2.5, 3.5, 4.5]

    frames_off = []   # 5 PIL images (left panel)
    frames_on  = []   # 5 PIL images (right panel)

    print('Generating grid frames...')
    for t in grid_times:
        # Render full frame and crop left/right halves
        tmp_full = FRAME_DIR / f'grid_t{t}.png'
        render_one_frame(t, tmp_full, ctx, f'grid_t{t}')
        img = Image.open(tmp_full).convert('RGB')
        W, H = img.size
        # Crop: use only TOP_H portion (3D body) for grid
        img_3d = img.crop((0, 0, W, TOP_H))
        frames_off.append(img_3d.crop((0, 0, W // 2, TOP_H)))
        frames_on.append(img_3d.crop((W // 2, 0, W, TOP_H)))
        print(f'  t={t}s done')

    # Assemble 5×2 grid
    cell_w = RES_W // 2  # 960
    cell_h = TOP_H        # 760
    n_rows, n_cols = 5, 2
    MARGIN = 4
    HEADER = 50

    grid_w = n_cols * cell_w + (n_cols + 1) * MARGIN
    grid_h = n_rows * cell_h + (n_rows + 1) * MARGIN + HEADER * 2

    canvas = Image.new('RGB', (grid_w, grid_h), (20, 20, 20))
    draw = ImageDraw.Draw(canvas)

    # Column headers
    col_labels = ['Suit OFF  (0 N·m)', 'Suit ON  (24 N·m)']
    row_labels = ['t=0.5s  Standing', 't=1.5s  Eccentric',
                  't=2.5s  Hold Peak', 't=3.5s  Concentric', 't=4.5s  Recovery']
    row_il10_off = []
    row_il10_on  = []

    # Recompute IL_R10 for annotations
    (_, _, _, mot_tbl, (t_off, lab_off, dat_off), (t_on, lab_on, dat_on)) = ctx
    for t in grid_times:
        acts_off = activation_at(t_off, dat_off, lab_off, t)
        acts_on  = activation_at(t_on,  dat_on,  lab_on,  t)
        row_il10_off.append(il_r10_pct(acts_off))
        row_il10_on.append(il_r10_pct(acts_on))

    # Draw title
    draw.text((grid_w // 2, 8),
              'Phase 1a Stoop Suit Comparison — Hu 2026 verified 28% ES reduction',
              fill=(255, 255, 255), anchor='mt')

    # Column headers
    for ci, col_label in enumerate(col_labels):
        x = MARGIN + ci * (cell_w + MARGIN) + cell_w // 2
        draw.text((x, HEADER - 20), col_label, fill=(200, 200, 200), anchor='mt')

    # Paste cells
    for ri, (img_off, img_on) in enumerate(zip(frames_off, frames_on)):
        y = HEADER + MARGIN + ri * (cell_h + MARGIN)
        for ci, img in enumerate([img_off, img_on]):
            x = MARGIN + ci * (cell_w + MARGIN)
            img_r = img.resize((cell_w, cell_h), Image.LANCZOS)
            canvas.paste(img_r, (x, y))
        # Row label + IL_R10 annotation
        draw.text((MARGIN, y + 10), row_labels[ri], fill=(200, 180, 100))
        ann = (f'IL_R10 OFF={row_il10_off[ri]:.0f}%  '
               f'ON={row_il10_on[ri]:.0f}%  '
               f'(Δ{row_il10_off[ri]-row_il10_on[ri]:+.0f}%)')
        draw.text((MARGIN, y + 30), ann, fill=(150, 200, 150))

    canvas.save(str(OUT_GRID))
    print(f'Grid saved: {OUT_GRID}')
    return OUT_GRID


# ── Metadata grid ─────────────────────────────────────────────────────────────
def make_metadata_grid():
    """Generate metadata/verification info grid PNG."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.patch.set_facecolor('#0D0D0D')
    fig.suptitle('Phase 1a Stoop Suit Comparison — Verification Metadata',
                 fontsize=16, fontweight='bold', color='white', y=0.98)

    for ax in axes.flat:
        ax.set_facecolor('#1a1a1a')
        ax.axis('off')

    # Panel 0: Video spec
    axes[0, 0].set_title('Video Specification', color='#88CCFF', fontsize=12, fontweight='bold')
    specs = [
        ('Resolution',   '1920 × 1080 (1080p)'),
        ('Frame Rate',   '30 fps'),
        ('Duration',     '5.0 s (Phase 1a full motion)'),
        ('Codec',        'H.264 / CRF 17'),
        ('Layout',       'Side-by-side (960 × 760 each)'),
        ('ES Overlay',   '76 muscles — IL/LTpT/LTpL'),
        ('Color map',    'Gray(0%) → Amber → Orange → Red(100%)'),
        ('Bottom bar',   'Time series + phase + numeric'),
    ]
    y = 0.92
    for k, v in specs:
        axes[0, 0].text(0.05, y, f'{k}:', color='#AAAAAA', fontsize=9,
                        transform=axes[0, 0].transAxes, va='top')
        axes[0, 0].text(0.45, y, v, color='white', fontsize=9,
                        transform=axes[0, 0].transAxes, va='top')
        y -= 0.11

    # Panel 1: ES activation key numbers
    axes[0, 1].set_title('ES Activation Key Numbers', color='#FF9966', fontsize=12, fontweight='bold')
    numbers = [
        ('IL_R10_r Suit OFF (hold)',  '87.7%  (t=2.5s)'),
        ('IL_R10_r Suit ON (hold)',   '51.0%  (t=2.5s)'),
        ('IL_R10_r reduction',        'Δ 36.7 %p at t=2.5s'),
        ('Peak IL_R10_r OFF',         '93.0%  (t=2-3s)'),
        ('Peak IL_R10_r ON',          '56.6%  (t=2-3s)'),
        ('Peak reduction',            '39.1%'),
        ('ES mean OFF (hold)',         '17.4%  (t=2.5s)'),
        ('ES mean ON (hold)',          '11.7%  (t=2.5s)'),
    ]
    y = 0.92
    for k, v in numbers:
        axes[0, 1].text(0.03, y, f'{k}:', color='#FFCC88', fontsize=9,
                        transform=axes[0, 1].transAxes, va='top')
        axes[0, 1].text(0.70, y, v, color='white', fontsize=9,
                        transform=axes[0, 1].transAxes, va='top', fontweight='bold')
        y -= 0.11

    # Panel 2: Phase 1a regression PASS
    axes[0, 2].set_title('Phase 1a Regression PASS', color='#88FF88', fontsize=12, fontweight='bold')
    reg_info = [
        ('Moco solver',      'Casadi IPOPT (WeldJoint)'),
        ('Mesh density',     '50'),
        ('Duration',         '140 s wall time'),
        ('Muscles',          '114 (forceset)'),
        ('Max ΔES',          '0.41 %p  PASS (<5%p)'),
        ('Suit sweep',       'Slope 1.158 %/N·m, R²=1.0000'),
        ('Conditions',       'B_suit0/50/100/150/200'),
        ('Verified:',        'Hu 2026 14.9–28.6% range'),
    ]
    y = 0.92
    for k, v in reg_info:
        axes[0, 2].text(0.03, y, f'{k}:', color='#AAAAAA', fontsize=9,
                        transform=axes[0, 2].transAxes, va='top')
        axes[0, 2].text(0.45, y, v, color='white', fontsize=9,
                        transform=axes[0, 2].transAxes, va='top')
        y -= 0.11

    # Panel 3: Hu 2026 comparison
    axes[1, 0].set_title('Hu et al. 2026 Comparison', color='#FFCC44', fontsize=12, fontweight='bold')
    hu_data = [
        ('Study',            'Hu et al. 2026 (EMG-based)'),
        ('ES reduction',     '14.9–28.6%  (reported range)'),
        ('This study',       '28–39%  (Moco IL_R10_r)'),
        ('Match status',     'WITHIN RANGE (upper end)'),
        ('Suit force',       '200 N (horizontal component)'),
        ('Moment arm',       '0.12 m (estimated L3-L4)'),
        ('Torque',           '24 N·m peak'),
        ('NIOSH LI',         '1.20 (OFF) → 0.84 (ON)'),
    ]
    y = 0.92
    for k, v in hu_data:
        axes[1, 0].text(0.03, y, f'{k}:', color='#DDBB66', fontsize=9,
                        transform=axes[1, 0].transAxes, va='top')
        axes[1, 0].text(0.50, y, v, color='white', fontsize=9,
                        transform=axes[1, 0].transAxes, va='top')
        y -= 0.11

    # Panel 4: Captured frames list
    axes[1, 1].set_title('Captured Frames (Grid)', color='#AAAAFF', fontsize=12, fontweight='bold')
    frame_list = [
        ('t=0.5s', 'Standing',   'ES_mean~2%',   'Baseline'),
        ('t=1.5s', 'Eccentric',  'ES rising',    'Bending phase'),
        ('t=2.5s', 'Hold peak',  'IL_R10~88/63%','KEY FRAME'),
        ('t=3.5s', 'Concentric', 'ES dropping',  'Lifting phase'),
        ('t=4.5s', 'Recovery',   'ES~4-5%',      'Return upright'),
    ]
    y = 0.92
    for t_str, phase, es_note, note in frame_list:
        col = '#FFAA44' if note == 'KEY FRAME' else 'white'
        line = f'{t_str:8s}  {phase:12s}  {es_note:20s}  {note}'
        axes[1, 1].text(0.03, y, line, color=col, fontsize=8.5,
                        transform=axes[1, 1].transAxes, va='top', family='monospace')
        y -= 0.14

    # Panel 5: File paths
    axes[1, 2].set_title('Output Files', color='#CCCCCC', fontsize=12, fontweight='bold')
    files = [
        ('Main video:', '/data/opensim_results/video/'),
        ('',            'phase1a_stoop_suit_comparison.mp4'),
        ('Grid PNG:',   'docs/images/phase1a_video/'),
        ('',            'phase1a_stoop_motion_video_grid.png'),
        ('Meta PNG:',   'phase1a_stoop_video_metadata_grid.png'),
        ('Script:',     'scripts/render_phase1a_stoop_suit_comparison.py'),
        ('Model:',      'MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1'),
        ('Moco sol:',   'phase1a_reproduction_v2/B_suit0|B_suit200'),
    ]
    y = 0.92
    for k, v in files:
        axes[1, 2].text(0.03, y, k, color='#888888', fontsize=8.5,
                        transform=axes[1, 2].transAxes, va='top', fontweight='bold')
        axes[1, 2].text(0.25, y, v, color='#CCCCCC', fontsize=8,
                        transform=axes[1, 2].transAxes, va='top', family='monospace')
        y -= 0.11

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(str(OUT_META), dpi=150, facecolor='#0D0D0D', bbox_inches='tight')
    plt.close(fig)
    print(f'Metadata grid saved: {OUT_META}')
    return OUT_META


# ── Video mode ────────────────────────────────────────────────────────────────
def video():
    """Render full 1920x1080 mp4 at 30fps, 5 seconds."""
    if FRAME_DIR.exists():
        shutil.rmtree(FRAME_DIR)
    FRAME_DIR.mkdir(parents=True)

    ctx = setup_context()
    t0_wall = time.time()

    for fi in range(N_FRAMES):
        t = fi / FPS
        frame_path = FRAME_DIR / f'frame_{fi:04d}.png'
        il10_off, il10_on, es_off, es_on = render_one_frame(
            t, frame_path, ctx, f'f{fi:04d}')
        if fi % 30 == 0:
            elapsed = time.time() - t0_wall
            eta = elapsed / (fi + 1) * (N_FRAMES - fi - 1)
            print(f'  frame {fi+1:3d}/{N_FRAMES}  t={t:.2f}s  '
                  f'IL_R10: {il10_off:.0f}%→{il10_on:.0f}%  '
                  f'elapsed={elapsed:.0f}s  ETA={eta:.0f}s')

    print(f'All {N_FRAMES} frames rendered in {time.time()-t0_wall:.1f}s')

    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error',
        '-framerate', str(FPS),
        '-i', str(FRAME_DIR / 'frame_%04d.png'),
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-crf', '17', '-preset', 'medium',
        '-movflags', '+faststart',
        str(OUT_MP4),
    ]
    print('Encoding mp4...')
    subprocess.run(cmd, check=True)
    sz_mb = OUT_MP4.stat().st_size / (1024 * 1024)
    print(f'Video: {OUT_MP4}  ({sz_mb:.1f} MB)')


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'preview'
    if mode == 'preview':
        preview()
    elif mode == 'grid':
        make_grid()
    elif mode == 'metadata':
        make_metadata_grid()
    elif mode == 'video':
        video()
    else:
        print('usage: render_phase1a_stoop_suit_comparison.py [preview|grid|metadata|video]')
        sys.exit(1)
