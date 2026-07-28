"""Carry-walk (20 kg box anterior) suit comparison video — 5th motion, public / 일반인용.
Left 슈트없음 | Right 슈트착용, ES color spine + box + Korean overlay.
Pipeline: box_stoop + gait_video 계승, viz-mirror (girdle z반사) 적용.
Modes: preview | video
"""
import os, sys, shutil, subprocess, time
os.environ.setdefault('DISPLAY', ':1')
from pathlib import Path
import numpy as np, opensim as osim, pyvista as pv
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib import font_manager as fm
from PIL import Image, ImageDraw, ImageFont

KF = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(KF)
plt.rcParams['font.family'] = fm.FontProperties(fname=KF).get_name()
plt.rcParams['axes.unicode_minus'] = False
def pilfont(sz): return ImageFont.truetype(KF, sz)

# ── 경로 ──────────────────────────────────────────────────────────────────────
MODEL = ('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/'
         'MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim')
GEOM  = Path('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry')
MOT   = '/data/gait_motion/carry_walk_so.mot'          # 73 fr, 0.4-1.6 s, 제자리 루프 적합
SO_OFF = '/data/carry_results/carry_off/so_StaticOptimization_activation.sto'
SO_ON  = '/data/carry_results/carry_on/so_StaticOptimization_activation.sto'

IMG_DIR   = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box')
IMG_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR  = Path('/data/opensim_results')
FRAME_DIR  = Path('/tmp/carry_walk_vid')
FRAME_DIR.mkdir(parents=True, exist_ok=True)
OUT_MP4    = VIDEO_DIR / 'carry_walk_suit_video.mp4'

# ── 렌더 설정 ─────────────────────────────────────────────────────────────────
FPS      = 20
LOOP_SEC = 8.0          # 목표 총 길이 (~8초)
RES_W, RES_H = 1600, 1000
TITLE_H  = 68
TOP_H    = 670
BOT_H    = RES_H - TITLE_H - TOP_H   # 262 px

GROUND   = 0.135        # 바닥 y (carry_walk 모션 기준)
BOX_HALF = 0.15         # 30cm 정육면체 반치수

# ES 색상 — windowed clim: 하한 올려 OFF(빨강) vs ON(회색~옅은주황) 대비 극대화
# clim=(0.55, 1.0): OFF(0.74~1.0)=옅은주황~짙은빨강 / ON(0.47~0.89)=회색~옅은주황
# → mid-stance: OFF 허리=빨강, ON 허리=회색/옅음으로 한눈에 구분
ES_CMAP = LinearSegmentedColormap.from_list(
    'es', [(0,'#909090'),(0.20,'#FFCC00'),(0.45,'#FF6600'),(0.70,'#CC1100'),(1,'#7B0000')], N=256)
ES_CLIM_LO = 0.55   # windowed 하한: 활성 0.55 이하는 회색
ES_CLIM_HI = 1.00   # windowed 상한
ES_CLIM     = ES_CLIM_HI   # 하위 호환 (막대 정규화용)

# 카메라: 3-quarter 전방 사선 — 정면 쪽으로 더 당겨 양팔·박스 보이게
# DX 줄이고 DZ 늘려 정면 성분 증가
CAM_DX, CAM_DY, CAM_DZ = 1.2, 0.9, 3.2   # position offset from pelvis_x
CAM_TGT_DY = 0.9                           # target y
PARALLEL_SCALE = 1.05

# VIZ-MIRROR: shoulder girdle + arm 키
_MIRROR_R = ('clavicle_R','scapula_R','humerus_R','ulna_R','radius_R','hand_R')
_MIRROR_L = ('clavicle_L','scapula_L','humerus_L','ulna_L','radius_L','hand_L')

# ES 근육 판별
def is_es(n): return n.startswith(('IL_', 'LTpT_', 'LTpL_'))

def arm_side(fp):
    if any(k in fp for k in _MIRROR_R): return 'R'
    if any(k in fp for k in _MIRROR_L): return 'L'
    return None


# ── 유틸: OpenSim ────────────────────────────────────────────────────────────
def transform_mat4(T):
    R, p = T.R(), T.p()
    M = np.eye(4)
    for i in range(3):
        for j in range(3): M[i, j] = R.get(i, j)
        M[i, 3] = p.get(i)
    return M

def collect_meshes(model):
    out = []
    for c in list(model.getComponentsList()):
        if c.getConcreteClassName() != 'Mesh': continue
        mesh = osim.Mesh.safeDownCast(c)
        mf = mesh.get_mesh_file()
        if not mf: continue
        p = GEOM / mf
        if not p.exists(): p = GEOM / Path(mf).name
        if not p.exists(): continue
        sf = mesh.get_scale_factors()
        out.append({'path': str(p), 'frame': mesh.getFrame().getAbsolutePathString(),
                    'scale': (sf.get(0), sf.get(1), sf.get(2))})
    return out

def load_so(path):
    tbl = osim.TimeSeriesTable(path)
    labs = list(tbl.getColumnLabels())
    t    = np.array(list(tbl.getIndependentColumn()))
    dat  = np.array([[tbl.getRowAtIndex(i)[j] for j in range(len(labs))]
                     for i in range(tbl.getNumRows())])
    return t, labs, dat

def acts_at(t_arr, dat, labs, tq):
    i = int(np.argmin(np.abs(t_arr - tq)))
    return {labs[j]: float(dat[i, j]) for j in range(len(labs))}

def es_peak_pct(a):
    v = [a[k] for k in a if is_es(k)]
    return 100.0 * max(v) if v else 0.0

def set_pose(model, state, mot_tbl, cols, mtypes, frame_idx):
    """모션 테이블 frame_idx 행을 state에 적용."""
    row = mot_tbl.getRowAtIndex(frame_idx)
    cs  = model.getCoordinateSet()
    for ci, nm in enumerate(cols):
        if not cs.contains(nm): continue
        v = row[ci]
        if mtypes[nm] == 1: v = np.radians(v)
        cs.get(nm).setValue(state, v, False)
    model.realizePosition(state)

def get_pelvis_tx(model, state):
    cs = model.getCoordinateSet()
    if cs.contains('pelvis_tx'): return cs.get('pelvis_tx').getValue(state)
    return 0.0

def get_hand_midpoint(model, state):
    """오른손 ground position 반환 (viz-mirror이므로 좌손=z반사 → 박스 z=0).
    generator 조기 종료 방지: list() 변환 후 순회."""
    result = None
    for comp in list(model.getComponentsList()):
        if comp.getName() != 'hand_R': continue
        pf = osim.PhysicalFrame.safeDownCast(comp)
        if pf is None: continue
        p = pf.getPositionInGround(state)
        result = np.array([p.get(0), p.get(1), p.get(2)])
        break
    return result

def muscle_pd(model, state, acts):
    """ES 근육 geometry path를 polyline으로 구성. scalar 수 = cell 수 (segment당 1값)."""
    pts = []; cells = []; sc = []
    M = model.getMuscles()
    for i in range(M.getSize()):
        m = M.get(i); nm = m.getName()
        if not is_es(nm): continue
        a = acts.get(nm, 0.0)
        pp = m.getGeometryPath().getCurrentPath(state)
        pl_pts = [[pp.get(k).getLocationInGround(state).get(j) for j in range(3)]
                  for k in range(pp.getSize())]
        if len(pl_pts) < 2: continue
        s = len(pts); pts.extend(pl_pts)
        for ii in range(len(pl_pts) - 1):
            cells += [2, s + ii, s + ii + 1]
            sc.append(a)   # 각 segment(cell)마다 activation 값 1개
    if not pts: return None
    pd = pv.PolyData()
    pd.points    = np.array(pts, float)
    pd.lines     = np.array(cells, np.int64)
    pd.cell_data['a'] = np.array(sc, float)
    return pd


# ── 3D 렌더 (좌|우 2패널) ────────────────────────────────────────────────────
def render_3d(model, state, meshes, fc, acts_off, acts_on, px, box_c, out_png):
    pv.global_theme.background = '#141414'
    pl = pv.Plotter(shape=(1, 2), window_size=(RES_W, TOP_H), off_screen=True, border=False)

    for col, acts in enumerate([acts_off, acts_on]):
        pl.subplot(0, col)

        # ── 신체 mesh (VIZ-MIRROR) ────────────────────────────────────────────
        for mi in meshes:
            if mi['frame'] not in fc: continue
            sd = arm_side(mi['frame'])
            if sd == 'L': continue   # 왼팔 girdle 완전 스킵

            try: surf = pv.read(mi['path'])
            except Exception: continue
            sx, sy, sz = mi['scale']
            if (sx, sy, sz) != (1, 1, 1):
                surf = surf.scale([sx, sy, sz], inplace=False)
            surf = surf.transform(transform_mat4(fc[mi['frame']].getTransformInGround(state)),
                                  inplace=False)
            pl.add_mesh(surf, color='#E8E0D0', opacity=0.96,
                        smooth_shading=True, specular=0.3, specular_power=15)

            if sd == 'R':   # 오른팔 girdle z=0 반사 → 왼팔 (viz-mirror)
                mir = surf.reflect((0, 0, 1), point=(0, 0, 0))
                pl.add_mesh(mir, color='#E8E0D0', opacity=0.96,
                            smooth_shading=True, specular=0.3, specular_power=15,
                            culling=False)   # culling=False: non-triangle mesh 법선 반전 안 함

        # ── ES 근육선 ─────────────────────────────────────────────────────────
        pd = muscle_pd(model, state, acts)
        if pd is not None:
            pl.add_mesh(pd, scalars='a', cmap=ES_CMAP, clim=[ES_CLIM_LO, ES_CLIM_HI],
                        line_width=12.0, show_scalar_bar=False)

        # ── 박스 (30cm 정육면체, 배 앞 안기) ──────────────────────────────────
        bx, by, bz = box_c
        box_mesh = pv.Box(bounds=(bx - BOX_HALF, bx + BOX_HALF,
                                  by - BOX_HALF, by + BOX_HALF,
                                  bz - BOX_HALF, bz + BOX_HALF))
        pl.add_mesh(box_mesh, color='#C8802A', opacity=1.0, specular=0.2)

        # ── 바닥 ─────────────────────────────────────────────────────────────
        pl.add_mesh(pv.Plane(center=(px, GROUND - 0.003, 0), direction=(0, 1, 0),
                             i_size=3.2, j_size=1.4), color='#2a2a2a', opacity=0.7)
        for gx in np.arange(round(px - 1.6, 1), px + 1.6, 0.25):
            pl.add_mesh(pv.Line((gx, GROUND, -0.65), (gx, GROUND, 0.65)),
                        color='#3c3c3c', line_width=1)

        # ── 조명 ─────────────────────────────────────────────────────────────
        pl.add_light(pv.Light(position=(px + 2, 3, 4), focal_point=(px, 0.0, 0),
                              intensity=0.85))
        pl.add_light(pv.Light(position=(px - 2, 2, -1), focal_point=(px, 0.0, 0),
                              intensity=0.35))
        pl.add_light(pv.Light(light_type='headlight', intensity=0.30))

        # ── 카메라: 3-quarter (약간 전방 사선) ───────────────────────────────
        cam_pos = (px + CAM_DX, CAM_DY, CAM_DZ)
        cam_tgt = (px, CAM_TGT_DY, 0.0)
        pl.camera_position = [cam_pos, cam_tgt, (0, 1, 0)]
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale      = PARALLEL_SCALE

    pl.screenshot(str(out_png)); pl.close()


# ── 하단 오버레이 (matplotlib, 한국어 자막) ──────────────────────────────────
def gait_phase_ko(frac):
    """정규화 보행 위상 frac(0-1) → (라벨 한국어, 색)."""
    if frac < 0.18: return '오른발 디딤 — 충격 흡수', '#E67E00'
    if frac < 0.42: return '오른발 중간 — 중심 이동',  '#CC2200'
    if frac < 0.65: return '왼발 디딤 — 충격 흡수',   '#E67E00'
    if frac < 0.88: return '왼발 중간 — 중심 이동',   '#CC2200'
    return '발 전환 중', '#888888'

def bottom_overlay(t_global, cycle_frac, es_off, es_on, out_png):
    """t_global: 동영상 재생 시간(루프 포함), cycle_frac 0-1."""
    DPI = 150
    fig = plt.figure(figsize=(RES_W / DPI, BOT_H / DPI), dpi=DPI)
    fig.patch.set_facecolor('#0D0D0D')

    ax  = fig.add_axes([0.03, 0.14, 0.62, 0.76])
    axt = fig.add_axes([0.69, 0.12, 0.28, 0.80])
    for a in (ax, axt):
        a.set_facecolor('#0D0D0D')
        a.axis('off')
        for s in a.spines.values(): s.set_visible(False)

    phase_lbl, phase_col = gait_phase_ko(cycle_frac)

    # ── 헤드라인 & 동작 라벨 ──────────────────────────────────────────────────
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.0, 0.98, '무거운 박스를 안고 걸을 때, 허리 근육이 받는 부담',
            fontsize=11, fontweight='bold', color='white', va='top', transform=ax.transAxes)
    ax.text(0.0, 0.80, f'동작: {phase_lbl}', fontsize=9, fontweight='bold',
            color=phase_col, va='top', transform=ax.transAxes)

    # ── ES% 막대그래프 — windowed clim과 동일 매핑 (3D 색과 일치)
    # 막대 길이: 0~100% 절대 척도 (포화 정직 표시)
    # 막대 색:   windowed clim(55~100%) 기준 → 3D 근육선과 동일 색상
    cap = 100.0
    def bar(y, val, lab):
        frac = min(max(val / cap, 0), 1)
        # windowed 색 정규화: (val/100 - LO) / (HI - LO)
        val_frac = float(val) / 100.0
        cmap_t = (val_frac - ES_CLIM_LO) / (ES_CLIM_HI - ES_CLIM_LO)
        cmap_t = min(max(cmap_t, 0.0), 1.0)
        bar_color = ES_CMAP(cmap_t)
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.16, y), 0.64, 0.14, boxstyle='round,pad=0.006',
            facecolor='#2a2a2a', edgecolor='#444', lw=1, transform=ax.transAxes))
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.16, y), 0.64 * frac, 0.14, boxstyle='round,pad=0.004',
            facecolor=bar_color, edgecolor='none',
            transform=ax.transAxes))
        ax.text(0.14, y + 0.07, lab, ha='right', va='center', fontsize=9,
                color='white', fontweight='bold', transform=ax.transAxes)
        ax.text(0.81, y + 0.07, f'{val:.0f}%', ha='left', va='center', fontsize=9,
                color='white', fontweight='bold', transform=ax.transAxes)

    bar(0.52, es_off, '슈트 없음')
    bar(0.30, es_on,  '슈트 착용')

    # ── headline 감소 수치 (고정) / 대비 서사 ─────────────────────────────────
    # mid-stance −25.4%p 근거 → "약 25% 감소" 고정 문구
    ax.text(0.40, 0.13, '허리 근육 부담  ↓ 약 25% 감소',
            ha='center', va='bottom', fontsize=13, fontweight='bold',
            color='#5bc8ff', transform=ax.transAxes)

    # ── 대비 서사 (걷기 동영상 연결) ──────────────────────────────────────────
    ax.text(0.40, 0.02,
            '그냥 걸을 땐 거의 그대로 — 무거운 걸 안고 걸으면 25%↓ (슈트는 부하가 있을 때 작동)',
            ha='center', va='bottom', fontsize=7.5, color='#9ddff5',
            transform=ax.transAxes)

    # ── 타임라인 ─────────────────────────────────────────────────────────────
    axt.set_xlim(0, 1); axt.set_ylim(0, 1)
    axt.text(0.5, 0.98, '위상', ha='center', va='top', fontsize=9, color='white',
             transform=axt.transAxes)
    axt.add_patch(mpatches.Rectangle((0.15, 0.12), 0.7, 0.78,
                                     facecolor='#222', edgecolor='#444', transform=axt.transAxes))
    axt.add_patch(mpatches.Rectangle((0.15, 0.12), 0.7, 0.78 * cycle_frac,
                                     facecolor='#2471a3', alpha=0.5, transform=axt.transAxes))
    fr = 0.12 + 0.78 * cycle_frac
    axt.plot([0.15, 0.85], [fr, fr], color='#FFFF00', lw=2, transform=axt.transAxes)
    axt.text(0.5, 0.05, '슈트: SMA 직물 허리보조 24N·m | KIMM', ha='center', va='top',
             fontsize=6.5, color='#777', transform=axt.transAxes)

    fig.savefig(str(out_png), dpi=100, facecolor='#0D0D0D',
                bbox_inches='tight', pad_inches=0)
    plt.close(fig)


# ── 제목 + 3D + 하단 합성 (PIL) ──────────────────────────────────────────────
def composite(img3d, imgbot, out_png):
    c = Image.new('RGB', (RES_W, RES_H), (13, 13, 13))
    d = ImageDraw.Draw(c)

    # 제목 배너
    d.rectangle([0, 0, RES_W, TITLE_H], fill=(18, 20, 26))
    d.text((RES_W // 2, TITLE_H // 2),
           '무거운 박스를 안고 걸을 때, 허리 근육이 받는 부담',
           font=pilfont(28), fill=(255, 255, 255), anchor='mm')

    # 3D 패널
    t3 = Image.open(img3d).convert('RGB').resize((RES_W, TOP_H), Image.LANCZOS)
    c.paste(t3, (0, TITLE_H))

    # 패널 구분선 + 라벨
    d.line([(RES_W // 2, TITLE_H), (RES_W // 2, TITLE_H + TOP_H)],
           fill=(70, 70, 70), width=2)
    d.text((RES_W // 4,      TITLE_H + 14), '슈트 없음',
           font=pilfont(26), fill=(230, 150, 150), anchor='mm')
    d.text((3 * RES_W // 4, TITLE_H + 14), '슈트 착용',
           font=pilfont(26), fill=(150, 200, 255), anchor='mm')

    # 하단 오버레이
    tb = Image.open(imgbot).convert('RGB').resize((RES_W, BOT_H), Image.LANCZOS)
    c.paste(tb, (0, TITLE_H + TOP_H))

    c.save(str(out_png))


# ── 프레임 렌더 ───────────────────────────────────────────────────────────────
def render_frame(model, state, meshes, fc, mot_tbl, mot_cols, mot_mt,
                 t_off, dat_off, labs_off, t_on, dat_on, labs_on,
                 n_mot_frames, frame_idx, t_global, out_png, pfx='f'):
    """frame_idx: 0-based index into mot_tbl (looped).
    t_global: absolute elapsed time in the output video (sec).
    """
    # 모션 적용
    set_pose(model, state, mot_tbl, mot_cols, mot_mt, frame_idx)
    px = get_pelvis_tx(model, state)

    # 박스 위치: 배꼽~명치 (손 위치 기준)
    hR = get_hand_midpoint(model, state)
    if hR is not None:
        # viz-mirror: 왼손=오른손 z반사 → 박스 z=0 중앙
        box_c = (hR[0], hR[1], 0.0)
    else:
        # fallback
        box_c = (px + 0.20, GROUND + 0.80, 0.0)

    # SO 활성화 보간 (carry_walk_so 시간 기준)
    t_vec = np.array(list(mot_tbl.getIndependentColumn()))
    tq = t_vec[frame_idx]
    ao = acts_at(t_off, dat_off, labs_off, tq)
    an = acts_at(t_on,  dat_on,  labs_on,  tq)
    eo = es_peak_pct(ao)
    en = es_peak_pct(an)

    # 보행 위상 (정규화 0-1, 루프 내 frame_idx 기준)
    cycle_frac = frame_idx / (n_mot_frames - 1)

    # 3D 렌더
    p3  = FRAME_DIR / f'{pfx}_3d.png'
    pb  = FRAME_DIR / f'{pfx}_bot.png'
    render_3d(model, state, meshes, fc, ao, an, px, box_c, str(p3))
    bottom_overlay(t_global, cycle_frac, eo, en, str(pb))
    composite(str(p3), str(pb), str(out_png))

    for p in (p3, pb):
        try: os.remove(p)
        except OSError: pass

    return eo, en


# ── 초기화 ────────────────────────────────────────────────────────────────────
def setup():
    model = osim.Model(MODEL)
    state = model.initSystem()
    meshes = collect_meshes(model)

    mot_tbl = osim.TimeSeriesTable(MOT)
    mot_cols = list(mot_tbl.getColumnLabels())
    cs = model.getCoordinateSet()
    mot_mt = {nm: cs.get(nm).getMotionType() for nm in mot_cols if cs.contains(nm)}

    t_off, labs_off, dat_off = load_so(SO_OFF)
    t_on,  labs_on,  dat_on  = load_so(SO_ON)

    # 프레임 캐시
    fc = {}
    for mi in meshes:
        if mi['frame'] not in fc:
            try: fc[mi['frame']] = model.getComponent(mi['frame'])
            except Exception: pass

    return model, state, meshes, fc, mot_tbl, mot_cols, mot_mt, \
           t_off, labs_off, dat_off, t_on, labs_on, dat_on


# ── 메인 ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'preview'

    ctx = setup()
    (model, state, meshes, fc, mot_tbl, mot_cols, mot_mt,
     t_off, labs_off, dat_off, t_on, labs_on, dat_on) = ctx

    n_mot = mot_tbl.getNumRows()          # 73
    t_mot_arr = np.array(list(mot_tbl.getIndependentColumn()))

    # ── warmup (첫 렌더 어두움 방지) ─────────────────────────────────────────
    _w = pv.Plotter(off_screen=True, window_size=(80, 80))
    _w.add_mesh(pv.Sphere()); _w.screenshot('/tmp/_w_carry.png'); _w.close()

    if mode == 'preview':
        # 5 대표 프레임 — 보행 위상 균등 샘플
        preview_idxs = [0, 14, 27, 41, 60]   # IC, LR, midstance, terminal, preswing 근사
        preview_outs = []
        for fi in preview_idxs:
            out = IMG_DIR / f'carry_walk_preview_f{fi}.png'
            eo, en = render_frame(
                model, state, meshes, fc, mot_tbl, mot_cols, mot_mt,
                t_off, dat_off, labs_off, t_on, dat_on, labs_on,
                n_mot, fi, t_mot_arr[fi], out, pfx=f'prev_{fi}')
            print(f'preview frame {fi} t={t_mot_arr[fi]:.3f}s: ES OFF={eo:.0f}% ON={en:.0f}% -> {out}')
            preview_outs.append((out, fi, eo, en))

        # 프리뷰 grid (5 × 1)
        import matplotlib.image as mpimg
        fig, axes = plt.subplots(1, len(preview_outs), figsize=(5 * len(preview_outs), 4.5))
        fig.patch.set_facecolor('#0d0d0d')
        for k, (p, fi, eo, en) in enumerate(preview_outs):
            axes[k].imshow(mpimg.imread(str(p)))
            axes[k].axis('off')
            frac = fi / (n_mot - 1)
            ph_lbl, _ = gait_phase_ko(frac)
            axes[k].set_title(f'f{fi} t={t_mot_arr[fi]:.2f}s\nOFF {eo:.0f}% ON {en:.0f}%\n{ph_lbl}',
                              color='white', fontsize=8)
        fig.suptitle('carry_walk_suit_video PREVIEW — 5 keyframes × 1 row', color='white', fontsize=11)
        fig.tight_layout()
        gpath = IMG_DIR / 'carry_walk_preview_grid.png'
        fig.savefig(str(gpath), dpi=90, facecolor='#0d0d0d')
        plt.close(fig)
        print(f'PREVIEW GRID: {gpath}')

    elif mode == 'video':
        # 루프: carry_walk_so는 1주기(73프레임, 1.2s)
        # 8초 채우기 위해 반복 루프
        N_video  = int(FPS * LOOP_SEC)           # ~160 프레임
        frames_needed = list(range(N_video))

        if FRAME_DIR.exists(): shutil.rmtree(FRAME_DIR)
        FRAME_DIR.mkdir(parents=True)

        t0 = time.time()
        for vi in frames_needed:
            # 루프: mot 프레임 순환
            fi      = vi % n_mot               # 0-72 루프
            t_glob  = vi / FPS                 # 전체 경과 시간

            out_f = FRAME_DIR / f'frame_{vi:04d}.png'
            eo, en = render_frame(
                model, state, meshes, fc, mot_tbl, mot_cols, mot_mt,
                t_off, dat_off, labs_off, t_on, dat_on, labs_on,
                n_mot, fi, t_glob, out_f, pfx=f'f{vi:04d}')

            if vi % FPS == 0:
                print(f'  frame {vi}/{N_video} t={t_glob:.1f}s fi={fi} '
                      f'ES OFF={eo:.0f}% ON={en:.0f}% elapsed={time.time()-t0:.0f}s',
                      flush=True)

        # ffmpeg 합성
        subprocess.run([
            'ffmpeg', '-y', '-loglevel', 'error',
            '-framerate', str(FPS),
            '-i', str(FRAME_DIR / 'frame_%04d.png'),
            '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            '-crf', '18', '-preset', 'medium', '-movflags', '+faststart',
            str(OUT_MP4)
        ], check=True)
        print(f'VIDEO: {OUT_MP4}  ({OUT_MP4.stat().st_size/1e6:.1f} MB)')

    elif mode == 'keyframes':
        # 키프레임 grid (5~6 시점 × 좌우 패널 보이도록 full composite)
        kf_idxs = [0, 12, 27, 42, 60, 72]
        kf_outs = []
        for fi in kf_idxs:
            out = FRAME_DIR / f'kf_{fi:02d}.png'
            eo, en = render_frame(
                model, state, meshes, fc, mot_tbl, mot_cols, mot_mt,
                t_off, dat_off, labs_off, t_on, dat_on, labs_on,
                n_mot, fi, t_mot_arr[fi], out, pfx=f'kf{fi}')
            kf_outs.append((out, fi, eo, en))
            frac = fi / (n_mot - 1)
            ph, _ = gait_phase_ko(frac)
            print(f'kf {fi} t={t_mot_arr[fi]:.2f}s OFF={eo:.0f}% ON={en:.0f}% [{ph}]')

        import matplotlib.image as mpimg
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.patch.set_facecolor('#0d0d0d')
        for k, (p, fi, eo, en) in enumerate(kf_outs):
            r, c_ = k // 3, k % 3
            axes[r, c_].imshow(mpimg.imread(str(p)))
            axes[r, c_].axis('off')
            frac = fi / (n_mot - 1)
            ph, _ = gait_phase_ko(frac)
            axes[r, c_].set_title(
                f'frame {fi}  t={t_mot_arr[fi]:.2f}s\nOFF {eo:.0f}% ON {en:.0f}%  |  {ph}',
                color='white', fontsize=9)
        fig.suptitle(
            '나르기 보행 슈트 비교 동영상 — 키프레임 grid\n'
            '(좌 슈트없음 | 우 슈트착용, viz-mirror, ES 회색→빨강, 박스 안기)',
            color='white', fontsize=12)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        gpath = IMG_DIR / 'carry_walk_video_keyframes.png'
        fig.savefig(str(gpath), dpi=110, facecolor='#0d0d0d')
        plt.close(fig)
        print(f'KEYFRAME GRID: {gpath}')
