"""[3] 동영상 프리뷰 — 본 렌더 전 승인용 4프레임 그리드.

(가) 허리 경로 비교 : 스툽, 조건 A(L1→허벅지) vs 조건 B(T8→천골→허벅지) 좌우 분할
(나) 다부위 통합    : 운반, 조건 B + 팔꿈치 (어깨는 이번 범위 제외)

공통 사양
  · 슈트 경로를 선으로 표시하고 **장력에 따라 색·굵기**를 바꾼다
  · 근육 활성도 컬러맵 (ES 계열 / 팔꿈치 굴근)
  · 하단에 3지표 실시간 수치

⚠️ 프리뷰만 만든다. 본 MP4 렌더는 사용자 승인 후.
"""
import os
import sys
import json
os.environ.setdefault('DISPLAY', ':1')
from pathlib import Path
import numpy as np
import opensim as osim
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_model as sm
import suit_moment_arm_fix as F
import suit_span_conditions as SC
import suit_arm_geom as AG
import suit_multijoint_conditions as MC

KF = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
GEOM = Path('/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry')
OUT = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/suit_multijoint')
OUT.mkdir(parents=True, exist_ok=True)
TMP = Path('/tmp/mj_preview')
TMP.mkdir(exist_ok=True)
D2R = np.pi / 180
PW, PH = 620, 760          # 패널 1개 크기
CAPH = 92                  # 하단 지표 띠
ES_CLIM = (5.0, 60.0)
K_SER = 5.0


def pilfont(sz):
    return ImageFont.truetype(KF, sz)


def transform_mat4(T):
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
        p = GEOM / mf
        if not p.exists():
            p = GEOM / Path(mf).name
        if not p.exists():
            continue
        sf = mesh.get_scale_factors()
        out.append({'path': str(p), 'frame': mesh.getFrame().getAbsolutePathString(),
                    'scale': (sf.get(0), sf.get(1), sf.get(2))})
    return out


def load_act(path):
    t = osim.TimeSeriesTable(path)
    labs = list(t.getColumnLabels())
    T = np.array(list(t.getIndependentColumn()))
    D = np.array([[t.getRowAtIndex(i)[j] for j in range(len(labs))]
                  for i in range(t.getNumRows())])
    return T, labs, D


def acts_at(T, D, labs, tq):
    i = int(np.argmin(np.abs(T - tq)))
    return {labs[j]: float(D[i, j]) for j in range(len(labs))}


def muscle_pd(model, state, acts, keep):
    pts, cells, sc = [], [], []
    M = model.getMuscles()
    for i in range(M.getSize()):
        m = M.get(i)
        nm = m.getName()
        if not nm.startswith(keep):
            continue
        a = acts.get(nm, 0.0) * 100
        pp = m.getGeometryPath().getCurrentPath(state)
        pl = [[pp.get(k).getLocationInGround(state).get(j) for j in range(3)]
              for k in range(pp.getSize())]
        if len(pl) < 2:
            continue
        s = len(pts)
        pts.extend(pl)
        for ii in range(len(pl) - 1):
            cells += [2, s + ii, s + ii + 1]
            sc.append(a)
    if not pts:
        return None
    pd = pv.PolyData()
    pd.points = np.array(pts, float)
    pd.lines = np.array(cells, np.int64)
    pd.cell_data['a'] = np.array(sc, float)
    return pd


def path_ground(model, state, P):
    bs = model.getBodySet()
    return [np.array([(q := bs.get(b).findStationLocationInGround(state, osim.Vec3(*loc))).get(0),
                      q.get(1), q.get(2)]) for b, loc in P]


def suit_pd(G):
    pd = pv.PolyData()
    pd.points = np.array(G, float)
    pd.lines = np.array([[2, i, i + 1] for i in range(len(G) - 1)], np.int64).ravel()
    return pd


def tension_color(t):
    """장력 0~100 N → 어두운 파랑(느슨) ~ 밝은 청록(최대).

    ⚠️ 근육 컬러맵(inferno = 보라·주황·노랑)과 색이 겹치지 않는 계열을 쓴다.
    """
    f = float(np.clip(t / 100.0, 0, 1))
    return (0.10 + 0.20 * f, 0.35 + 0.60 * f, 0.75 + 0.25 * f)


def hand_mid(model, state):
    """양손 중점 (ground) — 박스 글리프 위치."""
    bs = model.getBodySet()
    P = []
    for b in ('hand_R', 'hand_L'):
        try:
            q = bs.get(b).getPositionInGround(state)
        except Exception:
            return None
        P.append(np.array([q.get(0), q.get(1), q.get(2)]))
    return 0.5 * (P[0] + P[1])


def render_panel(model, state, meshes, mot_tbl, cols, mtypes, fi,
                 acts, paths_tension, title, out_png, cam_dz=3.0, keep_arm=False,
                 box=False):
    """한 패널 = 3D 뷰 1장."""
    row = mot_tbl.getRowAtIndex(fi)
    cs = model.getCoordinateSet()
    for ci, nm in enumerate(cols):
        if not cs.contains(nm):
            continue
        v = row[ci]
        if mtypes[nm] == 1:
            v = np.radians(v)
        cs.get(nm).setValue(state, v, False)
    model.realizePosition(state)

    pv.global_theme.background = '#141414'
    pl = pv.Plotter(window_size=(PW, PH), off_screen=True, border=False)
    bb = [1e9, -1e9, 1e9, -1e9]      # 실제 메쉬 경계로 화면을 맞춘다 (추측 금지)
    for mi in meshes:
        try:
            fr = model.getComponent(mi['frame'])
            M = transform_mat4(osim.PhysicalFrame.safeDownCast(fr).getTransformInGround(state))
        except Exception:
            continue
        try:
            mesh = pv.read(mi['path'])
        except Exception:
            continue
        mesh.scale(mi['scale'], inplace=True)
        mesh.transform(M, inplace=True)
        b = mesh.bounds
        bb[0] = min(bb[0], b[0]); bb[1] = max(bb[1], b[1])
        bb[2] = min(bb[2], b[2]); bb[3] = max(bb[3], b[3])
        pl.add_mesh(mesh, color='#d8d2c4', opacity=0.32, smooth_shading=True,
                    specular=0.15, show_scalar_bar=False)
    pd = muscle_pd(model, state, acts, ('IL_', 'LTpL', 'LTpT'))
    if pd is not None:
        pl.add_mesh(pd, scalars='a', cmap='inferno', clim=ES_CLIM, line_width=6,
                    show_scalar_bar=False)
    if keep_arm:
        pa = muscle_pd(model, state, acts, ('BIClong', 'BICshort', 'BRA_', 'BRD_'))
        if pa is not None:
            pl.add_mesh(pa, scalars='a', cmap='viridis', clim=(0, 40), line_width=7,
                        show_scalar_bar=False)
    for G, tens in paths_tension:
        w = 3.0 + 5.0 * float(np.clip(tens / 100.0, 0, 1))
        pl.add_mesh(suit_pd(G), color=tension_color(tens), line_width=w,
                    show_scalar_bar=False)
        # 상·하단 앵커 마커 — 조건 간 부여 스팬 차이가 눈에 보이도록
        for pt, r, cc in ((G[0], 0.022, '#ffe14d'), (G[-1], 0.017, '#7ec8ff')):
            pl.add_mesh(pv.Sphere(radius=r, center=pt), color=cc,
                        show_scalar_bar=False)

    if box:
        c = hand_mid(model, state)
        if c is not None:
            c = c + np.array([0.045, 0.02, 0.0])
            pl.add_mesh(pv.Cube(center=c, x_length=0.30, y_length=0.24, z_length=0.34),
                        color='#b98a52', opacity=0.85, show_scalar_bar=False)
            pl.add_mesh(pv.Cube(center=c, x_length=0.302, y_length=0.242, z_length=0.342),
                        color='#5d4326', style='wireframe', line_width=2,
                        show_scalar_bar=False)
    cx, cy = 0.5 * (bb[0] + bb[1]), 0.5 * (bb[2] + bb[3])
    ex, ey = bb[1] - bb[0], bb[3] - bb[2]
    aspect = PW / PH
    scale = 0.60 * max(ey, ex / aspect) * 1.18      # 여백 18 %
    # 시상면 측면 사선 — 등을 따라가는 슈트 경로가 가장 잘 보인다
    pl.camera.position = (cx + 0.40, cy, cam_dz)
    pl.camera.focal_point = (cx, cy, 0.0)
    pl.camera.up = (0, 1, 0)
    pl.enable_parallel_projection()
    pl.camera.parallel_scale = scale
    pl.screenshot(str(out_png))
    pl.close()
    im = Image.open(out_png).convert('RGB')
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, PW, 34], fill=(20, 20, 20))
    d.text((10, 7), title, font=pilfont(19), fill=(240, 240, 240))
    im.save(out_png)
    return out_png


def caption_strip(w, lines):
    im = Image.new('RGB', (w, CAPH), (24, 24, 24))
    d = ImageDraw.Draw(im)
    y = 8
    for txt, col, sz in lines:
        d.text((14, y), txt, font=pilfont(sz), fill=col)
        y += sz + 7
    return im


def grid(images, caps, out, ncol=2):
    nrow = int(np.ceil(len(images) / ncol))
    cw = images[0].width
    ch = images[0].height + CAPH
    canvas = Image.new('RGB', (cw * ncol, ch * nrow), (12, 12, 12))
    for i, (im, cap) in enumerate(zip(images, caps)):
        r, c = divmod(i, ncol)
        canvas.paste(im, (c * cw, r * ch))
        canvas.paste(caption_strip(cw, cap), (c * cw, r * ch + im.height))
    canvas.save(out)
    return out


# ── (가) 허리 경로 비교 — 스툽 조건 A vs B ─────────────────────────────────
STOOP_MODEL = F.MODEL
STOOP_MOT = '/data/stoop_results/stoop_v5/v5_30fps_armfix.mot'
A_STO = '/data/suit_16Nm/path16/so_StaticOptimization_activation.sto'
B_STO = '/data/suit_span/path_T8_sacfem/so_StaticOptimization_activation.sto'
STOOP_FRAMES = [1.4, 2.2, 2.75, 3.4]


def load_mot(path):
    tbl = osim.TimeSeriesTable(path)
    cols = list(tbl.getColumnLabels())
    T = np.array(list(tbl.getIndependentColumn()))
    return tbl, cols, T


def mtypes_of(model, cols):
    cs = model.getCoordinateSet()
    return {c: (cs.get(c).getMotionType() if cs.contains(c) else 0) for c in cols}


def waist_path_pts(model_path, top, bottom):
    m0 = osim.Model(model_path)
    m0.initSystem()
    s0 = F.neutral(m0)
    return {sd: SC.path_points(m0, s0, top, sd, bottom=bottom) for sd in ('R', 'L')}


def tens_for(model, state, P, L0):
    G = path_ground(model, state, P)
    L = sum(np.linalg.norm(G[i + 1] - G[i]) for i in range(len(G) - 1)) * 1000
    Ft, _, _ = sm.solve(L - L0, K_SER, sm.calibrate_T0(K_SER))
    return G, Ft


def neutral_L(model_path, P):
    m = osim.Model(model_path)
    m.initSystem()
    s = F.neutral(m)
    G = path_ground(m, s, P)
    return sum(np.linalg.norm(G[i + 1] - G[i]) for i in range(len(G) - 1)) * 1000


def preview_waist():
    model = osim.Model(STOOP_MODEL)
    state = model.initSystem()
    meshes = collect_meshes(model)
    tbl, cols, Tm = load_mot(STOOP_MOT)
    mt = mtypes_of(model, cols)
    CONDS = [
        ('A', '조건 A · L1→허벅지 (현 하드웨어)',
         waist_path_pts(STOOP_MODEL, 'L1', 'femur'), load_act(A_STO)),
        ('B', '조건 B · T8→천골→허벅지 (설계 제안)',
         waist_path_pts(STOOP_MODEL, 'T8', 'sacrum_femur'), load_act(B_STO)),
    ]
    # ⚠️ 기준장은 그 조건의 SO 를 만들 때 쓴 것과 같아야 한다.
    #    스툽 경로힘 조건은 모션 첫 프레임을 기준장으로 만들었다 (suit_span_conditions).
    row0 = tbl.getRowAtIndex(0)
    cs0 = model.getCoordinateSet()
    for ci, nm in enumerate(cols):
        if cs0.contains(nm):
            v = row0[ci]
            cs0.get(nm).setValue(state, np.radians(v) if mt[nm] == 1 else v, False)
    model.realizePosition(state)
    L0 = {}
    for key, _, P, _ in CONDS:
        L0[key] = {}
        for sd in P:
            G = path_ground(model, state, P[sd])
            L0[key][sd] = sum(np.linalg.norm(G[i + 1] - G[i])
                              for i in range(len(G) - 1)) * 1000
    ims, caps = [], []
    for k, tq in enumerate(STOOP_FRAMES):
        fi = int(np.argmin(np.abs(Tm - tq)))
        panels, vals = [], []
        for key, title, P, (Tt, ll, Dd) in CONDS:
            acts = acts_at(Tt, Dd, ll, tq)
            row = tbl.getRowAtIndex(fi)
            cs = model.getCoordinateSet()
            for ci, nm in enumerate(cols):
                if cs.contains(nm):
                    v = row[ci]
                    cs.get(nm).setValue(state, np.radians(v) if mt[nm] == 1 else v, False)
            model.realizePosition(state)
            pts_t = [tens_for(model, state, P[sd], L0[key][sd]) for sd in ('R', 'L')]
            es = 100 * max(v for kk, v in acts.items()
                           if kk.startswith(('IL_', 'LTpL', 'LTpT')))
            vals.append((es, float(np.mean([t for _, t in pts_t]))))
            png = TMP / f'w_{k}_{key}.png'
            panels.append(render_panel(model, state, meshes, tbl, cols, mt, fi,
                                       acts, pts_t, title, png, cam_dz=3.0))
        a, b = Image.open(panels[0]), Image.open(panels[1])
        comb = Image.new('RGB', (a.width + b.width, a.height), (12, 12, 12))
        comb.paste(a, (0, 0))
        comb.paste(b, (a.width, 0))
        ims.append(comb)
        caps.append([(f't = {tq:.2f} s', (235, 235, 235), 20),
                     (f'ES peak    A {vals[0][0]:5.1f} %    |    B {vals[1][0]:5.1f} %',
                      (255, 190, 120), 18),
                     (f'슈트 장력   A {vals[0][1]:5.1f} N    |    B {vals[1][1]:5.1f} N'
                      + ('   (양쪽 상한 포화)' if min(vals[0][1], vals[1][1]) >= 99.9 else ''),
                      (150, 200, 255), 18)])
    return grid(ims, caps, OUT / 'preview_waist_AvsB.png', ncol=2)


# ── (나) 다부위 통합 — 운반 조건 B + 팔꿈치 ───────────────────────────────
CARRY_STO = '/data/suit_carry/all/so_StaticOptimization_activation.sto'
CARRY_FRAMES = [0.60, 0.85, 1.15, 1.42]


def preview_carry():
    model = osim.Model(MC.MODEL)
    state = model.initSystem()
    meshes = collect_meshes(model)
    tbl, cols, Tm = load_mot(MC.MOT)
    mt = mtypes_of(model, cols)
    PW_ = {sd: MC.waist_points(sd) for sd in ('R', 'L')}
    PE_ = {sd: MC.elbow_points(sd, extended=True) for sd in ('R', 'L')}
    L0w = {sd: MC.neutral_length(PW_[sd]) for sd in PW_}
    Tt, ll, Dd = load_act(CARRY_STO)
    ims, caps = [], []
    L0e = None
    for k, tq in enumerate(CARRY_FRAMES):
        fi = int(np.argmin(np.abs(Tm - tq)))
        row = tbl.getRowAtIndex(fi)
        cs = model.getCoordinateSet()
        for ci, nm in enumerate(cols):
            if cs.contains(nm):
                v = row[ci]
                cs.get(nm).setValue(state, np.radians(v) if mt[nm] == 1 else v, False)
        model.realizePosition(state)
        if L0e is None:
            L0e = {}
            for sd in PE_:
                G = path_ground(model, state, PE_[sd])
                L0e[sd] = sum(np.linalg.norm(G[i + 1] - G[i])
                              for i in range(len(G) - 1)) * 1000
        pts_t = [tens_for(model, state, PW_[sd], L0w[sd]) for sd in ('R', 'L')]
        pts_e = [tens_for(model, state, PE_[sd], L0e[sd]) for sd in ('R', 'L')]
        acts = acts_at(Tt, Dd, ll, tq)
        es = 100 * max(v for kk, v in acts.items()
                       if kk.startswith(('IL_', 'LTpL', 'LTpT')))
        eb = 100 * np.mean([v for kk, v in acts.items()
                            if kk.startswith(('BIClong', 'BICshort', 'BRA_', 'BRD_'))])
        png = TMP / f'c_{k}.png'
        ims.append(Image.open(render_panel(model, state, meshes, tbl, cols, mt, fi,
                                           acts, pts_t + pts_e,
                                           '운반 20 kg · 조건 B + 팔꿈치 (어깨 제외)', png,
                                           cam_dz=3.1, keep_arm=True, box=True)))
        caps.append([(f't = {tq:.2f} s', (235, 235, 235), 20),
                     (f'ES peak {es:5.1f} %   |   팔꿈치 굴근 평균 {eb:5.2f} %',
                      (255, 190, 120), 18),
                     (f'허리 장력 {np.mean([t for _, t in pts_t]):5.1f} N   |   '
                      f'팔꿈치 장력 {np.mean([t for _, t in pts_e]):5.1f} N',
                      (150, 200, 255), 18)])
    return grid(ims, caps, OUT / 'preview_carry_multijoint.png', ncol=2)


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'both'
    if which in ('waist', 'both'):
        print('SAVED', preview_waist())
    if which in ('carry', 'both'):
        print('SAVED', preview_carry())
