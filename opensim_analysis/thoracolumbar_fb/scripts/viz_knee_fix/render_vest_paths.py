"""[정정 1] 조끼 구조 경로 스냅샷 — 시상면 · 후면, 중립과 스툽.

사진과 나란히 놓고 검증하기 위한 그림만 만든다 (SO 실행 없음).
경로색  허리 청록 · 어깨 주황 · 팔꿈치 연두   (근육 컬러맵과 겹치지 않는 계열)
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
PW, PH = 720, 900
D2R = np.pi / 180
COL = {'waist': (0.20, 0.85, 0.95), 'shoulder': (1.00, 0.62, 0.20),
       'elbow': (0.60, 0.95, 0.35)}
STOOP_MOT = '/data/stoop_results/stoop_v5/v5_30fps_armfix.mot'
STOOP_T = 2.75


def station(m, s, body, loc):
    q = m.getBodySet().get(body).findStationLocationInGround(s, osim.Vec3(*loc))
    return np.array([q.get(0), q.get(1), q.get(2)])


def set_pose_from_mot(m, s, tq):
    T, K = SC.load_mot(STOOP_MOT)
    fi = int(np.argmin(np.abs(T - tq)))
    cs = m.getCoordinateSet()
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
    return s


def render(m, s, paths, title, out_png, view='sag'):
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
        pl.add_mesh(mesh, color='#d8d2c4', opacity=0.30, smooth_shading=True,
                    specular=0.15, show_scalar_bar=False)
    for reg, sides in paths.items():
        for sd, pts in sides.items():
            G = [station(m, s, b, v) for b, v in pts]
            pd = pv.PolyData()
            pd.points = np.array(G, float)
            pd.lines = np.array([[2, i, i + 1] for i in range(len(G) - 1)],
                                np.int64).ravel()
            pl.add_mesh(pd, color=COL[reg], line_width=7, show_scalar_bar=False)
            for i, g in enumerate(G):
                r = 0.018 if i in (0, len(G) - 1) else 0.009
                c = '#ffe14d' if i == 0 else ('#7ec8ff' if i == len(G) - 1 else COL[reg])
                pl.add_mesh(pv.Sphere(radius=r, center=g), color=c,
                            show_scalar_bar=False)
    cx, cy, cz = (0.5 * (bb[0] + bb[1]), 0.5 * (bb[2] + bb[3]), 0.5 * (bb[4] + bb[5]))
    ex, ey = bb[1] - bb[0], bb[3] - bb[2]
    ez = bb[5] - bb[4]
    aspect = PW / PH
    if view == 'sag':
        pl.camera.position = (cx + 0.05, cy, cz + 3.0)
        scale = 0.60 * max(ey, ex / aspect) * 1.16
    else:                                   # 후면 — 등 쪽에서 본다 (+x 가 전방)
        pl.camera.position = (cx - 3.0, cy, cz)
        scale = 0.60 * max(ey, ez / aspect) * 1.16
    pl.camera.focal_point = (cx, cy, cz)
    pl.camera.up = (0, 1, 0)
    pl.enable_parallel_projection()
    pl.camera.parallel_scale = scale
    pl.screenshot(str(out_png))
    pl.close()
    im = Image.open(out_png).convert('RGB')
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, PW, 36], fill=(20, 20, 20))
    d.text((10, 8), title, font=ImageFont.truetype(KF, 20), fill=(240, 240, 240))
    im.save(out_png)
    return out_png


def main():
    m, P = VG.model_with_paths(sides=('R', 'L'))
    paths = {reg: {sd: P[sd][reg] for sd in P} for reg in ('waist', 'shoulder', 'elbow')}
    jobs = [
        ('neutral', 'sag', '중립 기립 · 시상면'),
        ('neutral', 'post', '중립 기립 · 후면'),
        ('stoop', 'sag', f'스툽 t={STOOP_T:.2f} s · 시상면'),
        ('stoop', 'post', f'스툽 t={STOOP_T:.2f} s · 후면'),
    ]
    outs = []
    for posture, view, title in jobs:
        s = VG.pose(m)
        if posture == 'stoop':
            s = set_pose_from_mot(m, s, STOOP_T)
        p = OUT / f'vest_{posture}_{view}.png'
        render(m, s, paths, title, p, view=view)
        outs.append(str(p))
        print('SAVED', p, flush=True)
    return outs


if __name__ == '__main__':
    main()
