"""[벤치 ■1·■2] 승인용 검증 그리드 — 영상 vs 모델 자세 · ΔL·장력 · 요구 모멘트 수계산.

SO 는 실행하지 않는다 (사용자 지시: ■1·■2 승인 후 ■3 진행).
"""
import os
import sys
import json
os.environ.setdefault('DISPLAY', ':1')
import numpy as np
import opensim as osim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image, ImageDraw, ImageFont
import pyvista as pv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_multijoint_preview as MP
import suit_vest_geom as VG
import bench_posture as BP

KF = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fm.fontManager.addfont(KF)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = [fm.FontProperties(fname=KF).get_name()]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'font.size': 9, 'figure.facecolor': 'white',
                     'savefig.facecolor': 'white'})

IMG = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/suit_multijoint'
SNAP = '/data/suit_bench/snap'
os.makedirs(SNAP, exist_ok=True)
OVL = '/data/suit_bench/overlay'
R = json.load(open('/data/suit_bench/posture.json'))
CY, OR, GR, BLUE, RED, GREY = ('#159fb5', '#d98324', '#4f9d2e', '#4c72b0',
                               '#c44e52', '0.55')
PW, PH = 760, 900


def render_posture(key, out_png):
    m = osim.Model(BP.MODEL)
    m.initSystem()
    v = R[key]
    s = BP.set_pose(m, v['phi'], v['pelvis_tilt'], v['hip_flex'], arm=v['arm'])
    m0 = osim.Model(BP.MODEL)
    m0.initSystem()
    s0 = VG.neutral(m0)
    P = {sd: VG.vest_waist_points(m0, s0, sd) for sd in ('R', 'L')}
    meshes = MP.collect_meshes(m)
    pv.global_theme.background = '#141414'
    pl = pv.Plotter(window_size=(PW, PH), off_screen=True, border=False)
    bb = [1e9, -1e9, 1e9, -1e9]
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
        bb[0] = min(bb[0], b[0]); bb[1] = max(bb[1], b[1])
        bb[2] = min(bb[2], b[2]); bb[3] = max(bb[3], b[3])
        pl.add_mesh(mesh, color='#d8d2c4', opacity=0.30, smooth_shading=True,
                    specular=0.15, show_scalar_bar=False)
    for sd, pts in P.items():
        Gs = [BP.station(m, s, b, loc) for b, loc in pts]
        pd = pv.PolyData()
        pd.points = np.array(Gs, float)
        pd.lines = np.array([[2, i, i + 1] for i in range(len(Gs) - 1)],
                            np.int64).ravel()
        pl.add_mesh(pd, color=(0.10, 0.85, 0.95), line_width=8,
                    show_scalar_bar=False)
        pl.add_mesh(pv.Sphere(radius=0.020, center=Gs[0]), color='#ffe14d')
        pl.add_mesh(pv.Sphere(radius=0.018, center=Gs[-1]), color='#7ec8ff')
    # 케틀벨 글리프
    hd = 0.5 * (BP.station(m, s, 'hand_R', (0, 0, 0)) +
                BP.station(m, s, 'hand_L', (0, 0, 0)))
    pl.add_mesh(pv.Sphere(radius=0.085, center=hd + np.array([0, -0.085, 0])),
                color='#404040')
    # 벤치 글리프 — 허벅지 패드(대퇴 중앙 전면) · 발목 롤러
    hip = BP.joint_center(m, s, 'hip_flexion_r')
    kn = BP.joint_center(m, s, 'knee_angle_r')
    pad = hip + 0.35 * (kn - hip)
    pl.add_mesh(pv.Cylinder(center=pad + np.array([0.07, 0.05, 0]),
                            direction=(0, 0, 1), radius=0.055, height=0.30),
                color='#e8c33a', opacity=0.85)
    ank = BP.station(m, s, 'calcn_r', (0, 0, 0)) if True else None
    pl.add_mesh(pv.Cylinder(center=ank + np.array([-0.06, 0.13, 0]),
                            direction=(0, 0, 1), radius=0.045, height=0.28),
                color='#7a7a7a', opacity=0.9)
    cx, cy = 0.5 * (bb[0] + bb[1]), 0.5 * (bb[2] + bb[3])
    ex, ey = bb[1] - bb[0], bb[3] - bb[2]
    pl.camera.position = (cx, cy, -3.2)   # 영상과 같은 방향(좌측을 향함)으로 본다
    pl.camera.focal_point = (cx, cy, 0.0)
    pl.camera.up = (0, 1, 0)
    pl.enable_parallel_projection()
    pl.camera.parallel_scale = 0.60 * max(ey, ex / (PW / PH)) * 1.15
    pl.screenshot(str(out_png))
    pl.close()
    im = Image.open(out_png).convert('RGB')
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, PW, 36], fill=(20, 20, 20))
    d.text((10, 8), f'모델 {key} — 요추 굴곡 {v["phi"]:.0f}°', fill=(240, 240, 240),
           font=ImageFont.truetype(KF, 20))
    im.save(out_png)
    return out_png


def show(ax, path, title, crop=None):
    ax.axis('off')
    if not os.path.exists(path):
        ax.text(.5, .5, '없음', ha='center')
        return
    im = Image.open(path)
    if crop:
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h),
                      int(crop[2] * w), int(crop[3] * h)))
    ax.imshow(np.array(im))
    ax.set_title(title, fontsize=9.4, fontweight='bold', loc='left', pad=5,
                 linespacing=1.4)


def main():
    for k in ('A_neutral', 'B_half'):
        render_posture(k, f'{SNAP}/{k}.png')
        print('SAVED', f'{SNAP}/{k}.png', flush=True)

    fig = plt.figure(figsize=(19.2, 13.6))
    gs = fig.add_gridspec(2, 4, hspace=0.24, wspace=0.22,
                          height_ratios=[1.25, 1.0],
                          left=0.045, right=0.980, top=0.900, bottom=0.045)
    fig.suptitle('[벤치 ■1·■2] 등 신전 과제 — 영상 운동학 재구성과 모델 구성안 (SO 실행 전 승인용)',
                 fontsize=15.0, fontweight='bold', y=0.968)
    fig.text(0.5, 0.936,
             '벤치가 다리를 구속(무릎 0~5°) · 몸통 수평에서 케틀벨을 든다 · '
             '가열력 한쪽 100 N / 양측 합 200 N (사양) · 5동작 논문 수치 불변 · 2026-09-27',
             ha='center', fontsize=9.0, color='0.3')

    show(fig.add_subplot(gs[0, 0]), f'{OVL}/nosuit_3.0.png',
         '(1) 영상 NO SUIT · t=3.0 s (최저점, 들지 못함)\n'
         '몸통 −4.4° · 고관절 60.8° · 무릎 3.3° · 대퇴 123.6°',
         crop=(0.0, 0.35, 1.0, 0.95))
    show(fig.add_subplot(gs[0, 1]), f'{OVL}/active_3.0.png',
         '(2) 영상 ACTIVE · t=3.0 s (최저점)\n이후 들어올림 → t=5.8 s 직립',
         crop=(0.0, 0.35, 1.0, 0.95))
    show(fig.add_subplot(gs[0, 2]), f'{SNAP}/A_neutral.png',
         '(3) 모델 변형 A — 요추 굴곡 10° (중립 요추)\n'
         '골반 −86.9° · 고관절 55.0° · 청록 = 슈트 · 노랑 = 벤치 패드',
         crop=(0.10, 0.03, 0.92, 1.0))
    show(fig.add_subplot(gs[0, 3]), f'{SNAP}/B_half.png',
         '(4) 모델 변형 B — 요추 굴곡 30° (절반 분담)\n골반 −72.1° · 고관절 40.2°',
         crop=(0.10, 0.03, 0.92, 1.0))

    # (5) 영상 각도 시계열
    ax = fig.add_subplot(gs[1, 0])
    ax.set_title('(5) 영상 시계열 — ACTIVE 만 들어올린다', fontsize=9.8,
                 fontweight='bold', loc='left', pad=6)
    d0 = json.load(open('/data/suit_bench/pose_raw.json'))
    for key, c, lab in (('nosuit', GREY, 'NO SUIT'), ('active', RED, 'ACTIVE')):
        rows = [r for r in d0['res'][key] if r]
        t = [r['t'] for r in rows]
        tilt = [180.0 - (r['trunk'] if r['trunk'] > 0 else r['trunk'] + 360)
                for r in rows]
        ax.plot(t, tilt, color=c, lw=2.2, label=f'{lab} 몸통 경사')
    ax.axhline(0, color='k', lw=1.0, ls=':')
    ax.set_xlabel('시간 (s)', fontsize=8.8)
    ax.set_ylabel('몸통 경사 (°, 0 = 수평)', fontsize=8.8)
    ax.grid(alpha=.3)
    ax.legend(fontsize=7.8, loc='upper left')
    ax.text(0.97, 0.72, 'NO SUIT 은 수평에서 6 초간 정체\nACTIVE 는 71° 까지 신전',
            transform=ax.transAxes, ha='right', fontsize=8.2, color=RED,
            linespacing=1.5)

    # (6) ΔL 비교
    ax = fig.add_subplot(gs[1, 1])
    ax.set_title('(6) ★ 슈트 경로 신장 ΔL — 벤치는 스툽보다 작다', fontsize=9.8,
                 fontweight='bold', loc='left', pad=6)
    labs = ['벤치 A\n(요추 10°)', '벤치 B\n(요추 30°)', '스툽 v5\n최심', '들기 20 kg\n최심']
    vals = [R['A_neutral']['suit']['R']['dL'], R['B_half']['suit']['R']['dL'],
            135.3, 166.0]
    cols = [CY, CY, GREY, GREY]
    b = ax.bar(range(4), vals, 0.6, color=cols)
    for i, v in enumerate(vals):
        ax.text(i, v + 3, f'{v:.0f}', ha='center', fontsize=9, fontweight='bold')
    ax.axhline(180, color=RED, ls='--', lw=1.5)
    ax.text(3.4, 183, '사슬 무릎점 180 mm', color=RED, fontsize=7.8, ha='right')
    ax.set_xticks(range(4))
    ax.set_xticklabels(labs, fontsize=8.0)
    ax.set_ylabel('ΔL (mm, 한쪽)', fontsize=8.8)
    ax.set_ylim(0, 205)
    ax.grid(alpha=.3, axis='y')

    # (7) 요구 모멘트 vs 슈트 (수계산)
    ax = fig.add_subplot(gs[1, 2])
    ax.set_title('(7) ★ 수계산 — 요구 모멘트 vs 슈트 기여 (변형 A)', fontsize=9.8,
                 fontweight='bold', loc='left', pad=6)
    v = R['A_neutral']
    kb = [0, 20, 36, 40]
    dem = [v['demand'][f'{k}.0']['M_L5S1'] for k in kb]
    demh = [v['demand'][f'{k}.0']['M_hip'] for k in kb]
    ax.plot(kb, dem, 'o-', color=RED, lw=2.4, ms=7, label='L5–S1 요구')
    ax.plot(kb, demh, 's--', color='#8b2f33', lw=1.8, ms=6, label='고관절 요구')
    suit_hot = abs(v['suit_moment_hot']['M_L5S1'])
    suit_max = suit_hot / (2 * v['suit']['R']['F_hot']) * 200.0
    ax.axhline(suit_hot, color=CY, lw=2.2)
    ax.text(1, suit_hot + 6, f'슈트 가열 {suit_hot:.1f} N·m (양측 합 '
            f'{2*v["suit"]["R"]["F_hot"]:.0f} N)', color=CY, fontsize=8.0)
    ax.axhline(suit_max, color=CY, ls=':', lw=1.8)
    ax.text(1, suit_max + 6, f'사양 상한 200 N 이면 {suit_max:.0f} N·m', color=CY,
            fontsize=8.0)
    for x, y in zip(kb, dem):
        ax.annotate(f'{y:.0f}', (x, y), textcoords='offset points', xytext=(5, 6),
                    fontsize=8.0, color=RED)
    ax.set_xlabel('케틀벨 (kg)', fontsize=8.8)
    ax.set_ylabel('모멘트 (N·m)', fontsize=8.8)
    ax.grid(alpha=.3)
    ax.legend(fontsize=7.8, loc='upper left')

    # (8) 판단 요약
    ax = fig.add_subplot(gs[1, 3])
    ax.axis('off')
    A = R['A_neutral']
    r = A['suit']['R']
    kbe = suit_max / (9.80665 * A['demand']['36.0']['hand_x_rel_l5'])
    lines = [
        ('■ ■0 사양 정정 반영', 'k', 9.8, 'bold'),
        ('  가열력 한쪽 100 N 고정 (양측 합 200 N)', '0.15', 8.6, None),
        ('  100 N 조건 재스캔: 선형 사슬 여전히 전부 탈락', '0.15', 8.6, None),
        ('  O1·O2 통과 7조합 — 모두 L_stand 160 · F_plat 10 N', '0.15', 8.6, None),
        ('  기존 대표 사슬(k1 0.2/x180/k2 20) 그대로 통과', GR, 8.6, 'bold'),
        ('', 'k', 3, None),
        ('■ ■1 운동학 (MediaPipe heavy, 249 프레임)', 'k', 9.8, 'bold'),
        ('  무릎 0~5° · 대퇴 57.5° · 최저점 몸통 −4.4°', '0.15', 8.6, None),
        ('  NO SUIT: 수평에서 6 초 정체 (들지 못함)', '0.15', 8.6, None),
        ('  ACTIVE: 71° 까지 신전 (들어올림)', '0.15', 8.6, None),
        ('  ⚠️ 요추/골반 분담은 영상으로 못 나눈다 → A·B 두 안', RED, 8.6, 'bold'),
        ('', 'k', 3, None),
        ('■ ★★ 수계산이 먼저 말하는 것', 'k', 9.8, 'bold'),
        (f'  36 kg 요구 L5–S1 {A["demand"]["36.0"]["M_L5S1"]:.0f} N·m · '
         f'고관절 {A["demand"]["36.0"]["M_hip"]:.0f} N·m', '0.15', 8.6, None),
        (f'  슈트 ΔL {r["dL"]:.0f} mm → 가열 {r["F_hot"]:.0f} N (한쪽) '
         f'= {suit_hot:.1f} N·m', '0.15', 8.6, None),
        (f'  사양 상한 200 N 이어도 {suit_max:.0f} N·m = 요구의 '
         f'{100*suit_max/A["demand"]["36.0"]["M_L5S1"]:.1f} %', RED, 8.8, 'bold'),
        (f'  → 케틀벨 환산 약 {kbe:.1f} kg 분', RED, 8.8, 'bold'),
        ('', 'k', 3, None),
        ('■ ■2 제안 (승인 요청)', 'k', 9.8, 'bold'),
        ('  다리 구속: 골반 residual 은 기존대로(500/1000),', '0.15', 8.6, None),
        ('  고관절·무릎·발목 reserve 를 opt 5 로 조임', '0.15', 8.6, None),
        ('  → 고관절 모멘트를 reserve 가 먹지 않게. 흡수량 보고', '0.15', 8.6, None),
        ('  케틀벨: 양손 중앙 외력, 좌우 대칭 확인 후 적용', '0.15', 8.6, None),
    ]
    y = 0.995
    for txt, col, sz, wgt in lines:
        if txt:
            ax.text(0.0, y, txt, transform=ax.transAxes, fontsize=sz, color=col,
                    fontweight=wgt or 'normal', va='top')
        y -= (sz + 4.0) / 250.0

    out = os.path.join(IMG, 'bench_kinematics_verify_grid.png')
    fig.savefig(out, dpi=104)
    print('SAVED', out)


if __name__ == '__main__':
    main()
