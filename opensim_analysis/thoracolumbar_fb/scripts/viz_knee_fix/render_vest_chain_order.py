"""[정정 2] 수정된 허리 사슬 순서 — 구동부(Active 200 mm)가 어디에 놓이는지.

사용자 정정: BOA 는 엉덩이 아래 허벅지 밴드 바로 위다.
  순서 = 견봉(어깨끈) → 조끼 등판 → 근육옷감 구동부(천골 포함) → BOA → 허벅지 밴드

색   회색 굵은 선 = 등판(강체 웨빙)   주황 = 구동부 200 mm   청록 점 = BOA
"""
import os
import sys
os.environ.setdefault('DISPLAY', ':1')
from pathlib import Path
import numpy as np
import opensim as osim
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_multijoint_preview as MP
import suit_vest_geom as VG
import suit_span_conditions as SC

OUT = Path('/data/suit_vest/snap')
OUT.mkdir(parents=True, exist_ok=True)
KF = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
PW, PH = 760, 950
D2R = np.pi / 180
L_ACT = 200.0          # mm — 구동부 길이
BOA_OFFSET = 30.0      # mm — 허벅지 밴드 위 BOA 위치 (경로 따라)
STOOP_MOT = '/data/stoop_results/stoop_v5/v5_30fps_armfix.mot'


def station(m, s, b, v):
    q = m.getBodySet().get(b).findStationLocationInGround(s, osim.Vec3(*v))
    return np.array([q.get(0), q.get(1), q.get(2)])


def polyline(G):
    """경로를 따라 누적 길이(mm)와 점 목록."""
    d = [0.0]
    for i in range(len(G) - 1):
        d.append(d[-1] + np.linalg.norm(G[i + 1] - G[i]) * 1000)
    return np.array(d)


def point_at(G, s_mm):
    """경로 시작(어깨)에서 s_mm 떨어진 점."""
    d = polyline(G)
    s_mm = float(np.clip(s_mm, 0, d[-1]))
    i = int(np.searchsorted(d, s_mm) - 1)
    i = max(0, min(i, len(G) - 2))
    f = (s_mm - d[i]) / max(d[i + 1] - d[i], 1e-9)
    return G[i] + f * (G[i + 1] - G[i])


def split(G):
    """(등판 구간, 구동부 구간, BOA 점, 밴드 점) — 하단 기준으로 나눈다."""
    d = polyline(G)
    total = d[-1]
    s_boa = total - BOA_OFFSET
    s_top = s_boa - L_ACT
    pts = []
    for s_mm in np.linspace(0, total, 240):
        pts.append(point_at(G, s_mm))
    pts = np.array(pts)
    ss = np.linspace(0, total, 240)
    web = pts[ss <= s_top]
    act = pts[(ss >= s_top) & (ss <= s_boa)]
    return web, act, point_at(G, s_boa), G[-1], s_top, s_boa, total


def render(m, s, P, title, out_png, view='sag'):
    meshes = MP.collect_meshes(m)
    pv.global_theme.background = '#141414'
    pl = pv.Plotter(window_size=(PW, PH), off_screen=True, border=False)
    bb = [1e9, -1e9, 1e9, -1e9, 1e9, -1e9]
    for mi in meshes:
        try:
            fr = m.getComponent(mi['frame'])
            M = MP.transform_mat4(
                osim.PhysicalFrame.safeDownCast(fr).getTransformInGround(s))
            mesh = pv.read(mi['path'])
        except Exception:
            continue
        mesh.scale(mi['scale'], inplace=True)
        mesh.transform(M, inplace=True)
        b = mesh.bounds
        for i in range(6):
            bb[i] = min(bb[i], b[i]) if i % 2 == 0 else max(bb[i], b[i])
        pl.add_mesh(mesh, color='#d8d2c4', opacity=0.28, smooth_shading=True,
                    specular=0.15, show_scalar_bar=False)
    info = {}
    for sd, pts in P.items():
        G = [station(m, s, b, v) for b, v in pts]
        web, act, boa, band, s_top, s_boa, total = split(G)
        info[sd] = dict(total=float(total), s_top=float(s_top), s_boa=float(s_boa))
        for arr, col, w in ((web, '#9aa0a6', 6), (act, '#ff8c2b', 11)):
            if len(arr) < 2:
                continue
            pd = pv.PolyData()
            pd.points = np.array(arr, float)
            pd.lines = np.array([[2, i, i + 1] for i in range(len(arr) - 1)],
                                np.int64).ravel()
            pl.add_mesh(pd, color=col, line_width=w, show_scalar_bar=False)
        pl.add_mesh(pv.Sphere(radius=0.020, center=G[0]), color='#ffe14d',
                    show_scalar_bar=False)                     # 견봉(어깨끈)
        pl.add_mesh(pv.Sphere(radius=0.016, center=boa), color='#19d3d3',
                    show_scalar_bar=False)                     # BOA
        pl.add_mesh(pv.Sphere(radius=0.018, center=band), color='#7ec8ff',
                    show_scalar_bar=False)                     # 허벅지 밴드
    cx, cy, cz = (0.5 * (bb[0] + bb[1]), 0.5 * (bb[2] + bb[3]), 0.5 * (bb[4] + bb[5]))
    ex, ey, ez = bb[1] - bb[0], bb[3] - bb[2], bb[5] - bb[4]
    aspect = PW / PH
    if view == 'sag':
        pl.camera.position = (cx + 0.05, cy, cz + 3.0)
        scale = 0.60 * max(ey, ex / aspect) * 1.12
    else:
        pl.camera.position = (cx - 3.0, cy, cz)
        scale = 0.60 * max(ey, ez / aspect) * 1.12
    pl.camera.focal_point = (cx, cy, cz)
    pl.camera.up = (0, 1, 0)
    pl.enable_parallel_projection()
    pl.camera.parallel_scale = scale
    pl.screenshot(str(out_png))
    pl.close()
    im = Image.open(out_png).convert('RGB')
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, PW, 38], fill=(20, 20, 20))
    d.text((10, 9), title, font=ImageFont.truetype(KF, 20), fill=(240, 240, 240))
    im.save(out_png)
    return info


def main():
    m0 = osim.Model(VG.MODEL)
    m0.initSystem()
    s0 = VG.neutral(m0)
    P = {sd: VG.vest_waist_points(m0, s0, sd) for sd in ('R', 'L')}
    m = osim.Model(VG.MODEL)
    m.initSystem()
    s = VG.pose(m)
    i1 = render(m, s, P, '중립 기립 — 회색=등판 · 주황=구동부 200 mm · 청록=BOA',
                OUT / 'chain_order_neutral_sag.png')
    print('중립', {k: {kk: round(vv, 1) for kk, vv in v.items()} for k, v in i1.items()})
    # 스툽
    T, K = SC.load_mot(STOOP_MOT)
    fi = int(np.argmin(np.abs(T - 2.75)))
    cs = m.getCoordinateSet()
    s = VG.pose(m)
    for c in K:
        try:
            co = cs.get(c)
        except Exception:
            continue
        if co.getLocked(s):
            continue
        co.setValue(s, K[c][fi] * D2R if co.getMotionType() == 1 else K[c][fi], False)
    m.assemble(s)
    m.realizePosition(s)
    i2 = render(m, s, P, '스툽 t=2.75 s — 경로가 길어진 만큼 구동부+사슬이 흡수',
                OUT / 'chain_order_stoop_sag.png')
    print('스툽', {k: {kk: round(vv, 1) for kk, vv in v.items()} for k, v in i2.items()})
    print('SAVED', OUT / 'chain_order_neutral_sag.png', OUT / 'chain_order_stoop_sag.png')


if __name__ == '__main__':
    main()
