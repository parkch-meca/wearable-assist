"""[5] 운반 다부위 본 해석 검증 그리드."""
import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch
from PIL import Image

KF = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fm.fontManager.addfont(KF)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = [fm.FontProperties(fname=KF).get_name()]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'font.size': 9, 'figure.facecolor': 'white',
                     'savefig.facecolor': 'white'})

IMG = '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/suit_multijoint'
M = json.load(open('/data/suit_carry/metrics.json'))
G = json.load(open('/data/suit_multijoint/arm_suit_geom.json'))
GREEN, RED, ORANGE, BLUE, PURPLE = '#1a7f37', '#c44e52', '#b3541e', '#4c72b0', '#7d5ba6'
R, ADD = M['res'], M['add']

fig = plt.figure(figsize=(17.6, 12.6))
gs = fig.add_gridspec(3, 3, hspace=0.52, wspace=0.30, height_ratios=[1, 1, 0.92],
                      left=0.070, right=0.978, top=0.895, bottom=0.045)
fig.suptitle('운반 20 kg 다부위 본 해석 — 허리(조건 B) + 팔꿈치 · 어깨 제외',
             fontsize=14.8, fontweight='bold', y=0.962)
fig.text(0.5, 0.930,
         '모델 = ThoracolumbarFB v2.0 + 팔꿈치근 14개 · 척추/팔 reserve·액추에이터 전부 opt 5 · '
         '창 0.533~1.483 s  |  주의: 미제작 설계 제안, 기존 5동작 운반 −25.7 % 와 직접 비교 불가  |  2026-08-18',
         ha='center', fontsize=9.0, color='0.3')


def panel(ax, t):
    ax.set_title(t, fontsize=10.4, fontweight='bold', pad=8, loc='left')


def rel(o, n):
    return 100.0 * (n - o) / o if abs(o) > 1e-9 else float('nan')


# ── (1) 어깨 캡 재설계 ───────────────────────────────────────────
ax = fig.add_subplot(gs[0, 0])
panel(ax, '(1) 어깨 캡 재설계 — 부호 반전은 해소되지 않았다')
for d, c, ls, lab in (('shoulder_cap', '0.55', '--', '구 캡 (하단 = 상완)'),
                      ('shoulder_cap2', RED, '-', '재설계 (하단·랩 = 견갑)')):
    rows = G['sweeps'][d]['rows']
    ax.plot([r['angle'] for r in rows], [r['r'] for r in rows], ls, color=c, lw=2.2,
            label=lab)
rows = G['sweeps']['shoulder_cap2']['rows']
ax.plot([r['angle'] for r in rows], [r['prime_max'] for r in rows], ':', color=BLUE,
        lw=1.8, label='삼각근 (참고)')
ax.axhline(0, color='k', lw=1.2)
ax.axvspan(50, 140, color=RED, alpha=0.10)
ax.text(95, -55, '부호 반전 구간\n= 굴곡 보조가\n신전 저항으로 바뀜', ha='center',
        fontsize=8.0, color=RED, linespacing=1.45, fontweight='bold')
ax.axvline(5, color=GREEN, lw=1.6, ls='-.')
ax.text(11, 84, '운반 어깨각 5°', color=GREEN, fontsize=8.0, va='top')
ax.set_xlabel('어깨 굴곡각 elv_angle (°)', fontsize=8.8)
ax.set_ylabel('모멘트 암 (mm)', fontsize=8.8)
ax.legend(fontsize=7.4, loc='lower left')
ax.grid(alpha=.3)
ax.set_ylim(-90, 90)

# ── (2) 3지표 ────────────────────────────────────────────────────
ax = fig.add_subplot(gs[0, 1:])
panel(ax, '(2) ★ ES 3지표 — 운반 4조건 (OFF 대비 변화율)')
CD = [('waist', '허리만\nT8→천골→허벅지'), ('elbow', '팔꿈치만\n기본안'),
      ('elbow_ext', '팔꿈치만\n연장안'), ('all', '전체 ON\n허리+팔꿈치')]
x = np.arange(len(CD))
keys = [('peak', '(a) ES peak', '0.62'), ('act_sum', '(b) 활성도 합', GREEN),
        ('force_sum', '(c) 근력 합', BLUE)]
for i, (k, lab, c) in enumerate(keys):
    v = [rel(R['off']['ES'][k], R[t]['ES'][k]) for t, _ in CD]
    b = ax.bar(x + (i - 1) * 0.26, v, 0.25, label=lab, color=c, ec='k', lw=.6)
    for xi, vv in zip(x + (i - 1) * 0.26, v):
        ax.text(xi, vv - 0.9, f'{vv:+.1f}', ha='center', va='top', fontsize=7.8,
                fontweight='bold')
ax.axhline(0, color='k', lw=1.1)
ax.set_xticks(x)
ax.set_xticklabels([l for _, l in CD], fontsize=8.4, linespacing=1.35)
ax.set_ylabel('OFF 대비 변화율 (%)', fontsize=8.8)
ax.legend(fontsize=8, loc='lower left')
ax.grid(axis='y', alpha=.3)
ax.set_ylim(-21, 6)
ax.text(0.5, 0.93, '팔꿈치 슈트는 ES 지표에 전혀 나타나지 않는다 (0.0 %) — 부위가 다르기 때문',
        transform=ax.transAxes, ha='center', fontsize=8.4, color='0.25',
        bbox=dict(boxstyle='round,pad=0.30', fc='white', ec='0.6', lw=0.7))

# ── (3) 부위별 주동근 활성도 ─────────────────────────────────────
ax = fig.add_subplot(gs[1, 0])
panel(ax, '(3) ★ 부위별 주동근 활성도 (창내 평균, OFF 대비)')
GN = [('ES', 'ES 계열'), ('DELT', '삼각근'), ('ELBFLX', '팔꿈치 굴근')]
x = np.arange(len(CD))
for i, (g, lab) in enumerate(GN):
    v = [rel(R['off'][g]['mean'], R[t][g]['mean']) for t, _ in CD]
    ax.bar(x + (i - 1) * 0.26, v, 0.25, label=lab,
           color=[ORANGE, PURPLE, GREEN][i], ec='k', lw=.6)
    for xi, vv in zip(x + (i - 1) * 0.26, v):
        ax.text(xi, vv + (0.5 if vv >= 0 else -0.5), f'{vv:+.1f}', ha='center',
                va='bottom' if vv >= 0 else 'top', fontsize=7.4, fontweight='bold')
ax.axhline(0, color='k', lw=1.1)
ax.set_xticks(x)
ax.set_xticklabels([l.replace('\n', ' ') for _, l in CD], fontsize=7.4, rotation=12)
ax.set_ylabel('변화율 (%)', fontsize=8.8)
ax.legend(fontsize=7.6, loc='upper right', framealpha=0.95)
ax.grid(axis='y', alpha=.3)
ax.set_ylim(-22, 14)

# ── (4) ★ 스팬 불일치 실측 증거 ──────────────────────────────────
ax = fig.add_subplot(gs[1, 1])
panel(ax, '(4) ★★ 스팬 불일치의 실측 증거 — 삼각근이 대신 일한다')
lbls = ['팔꿈치 기본안\n상완→전완', '팔꿈치 연장안\n견갑→상완→전완']
delt = [rel(R['off']['DELT']['mean'], R[t]['DELT']['mean']) for t in ('elbow', 'elbow_ext')]
elb = [rel(R['off']['ELBFLX']['mean'], R[t]['ELBFLX']['mean'])
       for t in ('elbow', 'elbow_ext')]
x = np.arange(2)
ax.bar(x - 0.19, elb, 0.36, label='팔꿈치 굴근', color=GREEN, ec='k', lw=.6)
ax.bar(x + 0.19, delt, 0.36, label='삼각근', color=PURPLE, ec='k', lw=.6)
for xi, v in zip(x - 0.19, elb):
    ax.text(xi, v - 0.6, f'{v:+.1f}', ha='center', va='top', fontsize=9,
            fontweight='bold')
for xi, v in zip(x + 0.19, delt):
    ax.text(xi, v + (0.4 if v >= 0 else -0.4), f'{v:+.1f}', ha='center',
            va='bottom' if v >= 0 else 'top', fontsize=9, fontweight='bold',
            color=RED if v > 0 else GREEN)
ax.axhline(0, color='k', lw=1.1)
ax.set_xticks(x)
ax.set_xticklabels(lbls, fontsize=8.4, linespacing=1.35)
ax.set_ylabel('OFF 대비 변화율 (%)', fontsize=8.8)
ax.legend(fontsize=8, loc='lower left')
ax.grid(axis='y', alpha=.3)
ax.set_ylim(-22, 12)
ax.text(0.5, 0.90,
        '기본안은 이두근의 팔꿈치 몫만 덜어 준다.\n'
        '이두근이 어깨에서 하던 몫이 사라져 삼각근이 +6.9 % 더 일한다.\n'
        '견갑까지 연장하면 −1.8 % 로 뒤집힌다.',
        transform=ax.transAxes, ha='center', va='top', fontsize=8.0, linespacing=1.5,
        color='0.2', bbox=dict(boxstyle='round,pad=0.30', fc='#eaf6ec', ec=GREEN, lw=1.0))

# ── (5) 가산성 ───────────────────────────────────────────────────
ax = fig.add_subplot(gs[1, 2])
panel(ax, '(5) ★ 가산성 — 전체 ON = 허리 + 팔꿈치 인가')
ROWS = [('ES 활성도 합', 'ES.act_sum'), ('ES 근력 합', 'ES.force_sum'),
        ('ES peak', 'ES.peak'), ('팔꿈치 굴근 평균', 'ELBFLX.mean')]
y = np.arange(len(ROWS))[::-1]
gapv = [ADD[k]['gap_pct'] for _, k in ROWS]
ax.axvspan(-5, 5, color=GREEN, alpha=0.12)
ax.barh(y, gapv, 0.42, color=BLUE, ec='k', lw=.7)
for yi, (lab, k) in zip(y, ROWS):
    a_ = ADD[k]
    ax.text(0.35, yi + 0.30, f"합 {a_['sum']:.1f}  vs  전체 ON {a_['all']:.1f}",
            fontsize=7.4, color='0.35', va='center')
    ax.text(a_['gap_pct'] + 0.25, yi, f"{a_['gap_pct']:+.2f} %", fontsize=8.2,
            va='center', fontweight='bold')
ax.set_yticks(y)
ax.set_yticklabels([l for l, _ in ROWS], fontsize=8.4)
ax.axvline(0, color='k', lw=1.1)
ax.set_xlabel('(전체 ON) − (단독 효과의 합)  ÷ 합  [%]', fontsize=8.8)
ax.set_xlim(-6, 6)
ax.grid(axis='x', alpha=.3)
ax.text(0.02, 0.055, '초록 띠 = ±5 % 가산 판정 범위', transform=ax.transAxes,
        fontsize=7.8, color=GREEN)
ax.text(0.02, 0.93, f'차이 최대 {max(abs(v) for v in gapv):.2f} %\n→ 완전 가산적',
        transform=ax.transAxes, ha='left', va='top', fontsize=8.8, fontweight='bold',
        color=GREEN, linespacing=1.5,
        bbox=dict(boxstyle='round,pad=0.30', fc='#eaf6ec', ec=GREEN, lw=1.1))

# ── (6)(7) 동영상 프리뷰 ─────────────────────────────────────────
for j, (fn, t) in enumerate((('preview_waist_AvsB.png', '(6) 프리뷰 (가) 허리 경로 A vs B — 스툽'),
                             ('preview_carry_multijoint.png',
                              '(7) 프리뷰 (나) 다부위 통합 — 운반 20 kg'))):
    ax = fig.add_subplot(gs[2, j])
    panel(ax, t)
    im = Image.open(f'{IMG}/{fn}')
    ax.imshow(np.asarray(im))
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor('0.5')

# ── (8) 판정 ─────────────────────────────────────────────────────
ax = fig.add_subplot(gs[2, 2])
panel(ax, '(8) ★ 판정')
ax.axis('off')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ITEMS = [
    ('허리 (조건 B)', f"ES 활성도 합 {rel(R['off']['ES']['act_sum'], R['waist']['ES']['act_sum']):+.1f} % · "
     f"peak {rel(R['off']['ES']['peak'], R['waist']['ES']['peak']):+.1f} %", GREEN),
    ('팔꿈치', f"굴근 활성도 {rel(R['off']['ELBFLX']['mean'], R['elbow_ext']['ELBFLX']['mean']):+.1f} % · "
     'ES 에는 0.0 %', GREEN),
    ('어깨', '제외 — 50° 부호 반전 (L-08)', RED),
    ('가산성', '완전 가산 (차이 ≤ 0.16 %)', BLUE),
    ('스팬 정합', '연장안 필수 — 기본안은 삼각근 +6.9 %', ORANGE),
]
y = 0.93
for lab, val, c in ITEMS:
    ax.text(0.0, y, lab, fontsize=9.0, fontweight='bold')
    ax.text(0.03, y - 0.058, val, fontsize=8.2, color=c)
    y -= 0.150
ax.add_patch(FancyBboxPatch((0.0, 0.02), 1.0, 0.20, boxstyle='round,pad=0.014',
                            fc='#eef3fb', ec=BLUE, lw=1.3))
ax.text(0.5, 0.155, '본 렌더 대기', ha='center', fontsize=10.2, fontweight='bold',
        color=BLUE)
ax.text(0.5, 0.075, '프리뷰 승인 후 MP4 렌더 진행', ha='center', va='center',
        fontsize=8.4, color='0.25')

P = f'{IMG}/carry_multijoint_grid.png'
fig.savefig(P, dpi=150)
print('SAVED', P)
