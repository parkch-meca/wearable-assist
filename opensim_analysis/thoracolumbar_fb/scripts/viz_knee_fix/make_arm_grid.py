"""[4] 다관절 1단계 — 사전검증 + 어깨·팔꿈치 슈트 기하 검증 그리드."""
import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

KF = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fm.fontManager.addfont(KF)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = [fm.FontProperties(fname=KF).get_name()]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'font.size': 9, 'figure.facecolor': 'white',
                     'savefig.facecolor': 'white'})

OUT = ('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/suit_multijoint')
os.makedirs(OUT, exist_ok=True)
G = json.load(open('/data/suit_multijoint/arm_suit_geom.json'))
A5 = json.load(open('/data/suit_multijoint/arm_demand_5motion.json'))
GREEN, RED, ORANGE, BLUE, PURPLE = '#1a7f37', '#c44e52', '#b3541e', '#4c72b0', '#7d5ba6'

fig = plt.figure(figsize=(17.4, 11.8))
gs = fig.add_gridspec(2, 3, hspace=0.50, wspace=0.30,
                      left=0.075, right=0.975, top=0.880, bottom=0.075)
fig.suptitle('다관절 1단계 — 어깨·팔꿈치 슈트 기하 검증 및 사전 부하 조사',
             fontsize=14.5, fontweight='bold', y=0.957)
fig.text(0.5, 0.918,
         '모델 ThoracolumbarFB v2.0 + 팔꿈치근 14개 · 체표면 = 근육 외피 + 피하 10 + 의복 5 mm · '
         'k = 5 N/mm · 편측 100 N  |  주의: 전부 미제작 설계 제안  |  2026-08-17',
         ha='center', fontsize=9.2, color='0.3')


def panel(ax, t):
    ax.set_title(t, fontsize=10.4, fontweight='bold', pad=8, loc='left')


# ── (1) 5동작 팔 부하 ────────────────────────────────────────────
ax = fig.add_subplot(gs[0, 0])
panel(ax, '(1) ★ 사전검증 — 동작별 팔 요구 모멘트')
NM = {'stoop': '스툽', 'squat': '스쿼트', 'box': '들기', 'gait': '보행', 'carry': '운반'}
ORD = ['stoop', 'squat', 'gait', 'box', 'carry']
x = np.arange(len(ORD))
elb = [A5[k]['elbow'] for k in ORD]
shl = [A5[k]['elv'] for k in ORD]
ax.bar(x - 0.19, elb, 0.36, label='팔꿈치 굴곡', color=PURPLE, ec='k', lw=.6)
ax.bar(x + 0.19, shl, 0.36, label='어깨 시상굴곡', color=ORANGE, ec='k', lw=.6)
for xi, (a, b) in enumerate(zip(elb, shl)):
    ax.text(xi - 0.19, a + 0.6, f'{a:.1f}', ha='center', fontsize=7.6)
    ax.text(xi + 0.19, b + 0.6, f'{b:.1f}', ha='center', fontsize=7.6)
ax.set_xticks(x)
ax.set_xticklabels([NM[k] for k in ORD], fontsize=9)
ax.set_ylabel('요구 모멘트 (N·m, 창내 평균)', fontsize=8.8)
ax.legend(fontsize=8, loc='upper left', framealpha=0.95)
ax.grid(axis='y', alpha=.3)
ax.set_ylim(0, 30)
ax.axvspan(-0.5, 2.5, color=RED, alpha=0.07)
ax.text(1.0, 19.5, '팔 무부하\n슈트 효과 측정 불가', ha='center', fontsize=8.2,
        color=RED, linespacing=1.4, fontweight='bold')
ax.text(3.5, 28.0, '팔 유의 부하', ha='center', fontsize=8.6, color=GREEN,
        fontweight='bold')

# ── (2) 스팬 정합 ────────────────────────────────────────────────
ax = fig.add_subplot(gs[0, 1])
panel(ax, '(2) ★ 스팬 정합 — 이두근은 견갑 기점 이관절근')
ax.axis('off')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
SEG = [('견갑\nscapula', 0.86), ('상완\nhumerus', 0.58), ('전완\nradius', 0.30)]
for lab, y in SEG:
    ax.add_patch(FancyBboxPatch((0.05, y - 0.055), 0.20, 0.11,
                                boxstyle='round,pad=0.012', fc='#eef2f7', ec='0.4', lw=1.0))
    ax.text(0.15, y, lab, ha='center', va='center', fontsize=8.4, linespacing=1.3)
BARS = [('BRA\n단관절', 0.355, 0.58, 0.30, GREEN, 0.245),
        ('BIClong·BICshort\n★ 이관절', 0.535, 0.86, 0.30, RED, 0.245),
        ('슈트 기본\n상완→전완', 0.715, 0.58, 0.30, BLUE, 0.245),
        ('슈트 연장안\n견갑→전완', 0.895, 0.86, 0.30, PURPLE, 0.245)]
for lab, xx, y1, y2, c, ylab in BARS:
    ax.plot([xx, xx], [y2, y1], color=c, lw=6, solid_capstyle='butt', alpha=.85)
    ax.plot([xx - 0.022, xx + 0.022], [y1, y1], color=c, lw=2)
    ax.plot([xx - 0.022, xx + 0.022], [y2, y2], color=c, lw=2)
    ax.text(xx, ylab, lab, ha='center', va='top', fontsize=7.0, color=c,
            linespacing=1.35, fontweight='bold')
ax.add_patch(FancyBboxPatch((0.30, 0.605), 0.67, 0.285, boxstyle='round,pad=0.012',
                            fc='none', ec=RED, ls='--', lw=1.3))
ax.text(0.635, 0.955, '견갑–상완 구간을 기본안이 비운다', ha='center', fontsize=8.4,
        color=RED, fontweight='bold')
ax.text(0.5, 0.035,
        '허리에서 L1 고정이 L5_S1 을 건너뛴 것과 동일한 구조.\n'
        '연장안은 어깨 모멘트 암 15.5 mm 를 함께 만든다.',
        ha='center', va='center', fontsize=8.2, linespacing=1.5, color='0.2',
        bbox=dict(boxstyle='round,pad=0.30', fc='white', ec='0.55', lw=0.7))

# ── (3) 게이트 ───────────────────────────────────────────────────
ax = fig.add_subplot(gs[0, 2])
panel(ax, '(3) ★ 게이트 — 슈트 모멘트 암 vs 주동근 최대 근속')
for d, c, ls, lab in (('shoulder_strap', ORANGE, '-', '어깨 스트랩'),
                      ('shoulder_cap', RED, '--', '어깨 캡'),
                      ('elbow_bow', PURPLE, '-', '팔꿈치')):
    R = G['sweeps'][d]['rows']
    aa = [r['angle'] for r in R]
    ax.plot(aa, [r['r'] for r in R], ls, color=c, lw=2.0, label=f'{lab} 슈트 r')
R = G['sweeps']['shoulder_strap']['rows']
ax.plot([r['angle'] for r in R], [r['prime_max'] for r in R], ':', color='0.35', lw=2.0,
        label='어깨 주동근 (삼각근)')
R = G['sweeps']['elbow_bow']['rows']
ax.plot([r['angle'] for r in R], [r['prime_max'] for r in R], ':', color='0.6', lw=2.0,
        label='팔꿈치 주동근 (이두근)')
ax.axhline(0, color='k', lw=1.0)
ax.set_xlabel('관절 굴곡각 (°)', fontsize=8.8)
ax.set_ylabel('모멘트 암 (mm)', fontsize=8.8)
ax.grid(alpha=.3)
ax.legend(fontsize=7.0, loc='lower left', ncol=1)
ax.set_ylim(-80, 90)
ax.text(0.98, 0.96, '슈트 곡선이 주동근 점선보다\n위에 있어야 통과',
        transform=ax.transAxes, ha='right', va='top', fontsize=7.6, color='0.25',
        linespacing=1.4, bbox=dict(boxstyle='round,pad=0.26', fc='white', ec='0.6', lw=0.6))

# ── (4) 장력·토크 vs 각도 ────────────────────────────────────────
ax = fig.add_subplot(gs[1, 0])
panel(ax, '(4) 장력 소실(이완) — 깊게 굽히면 SMA 가 스트로크를 다 쓴다')
for d, c, lab in (('shoulder_strap', ORANGE, '어깨 스트랩'), ('elbow_bow', PURPLE, '팔꿈치')):
    R = G['sweeps'][d]['rows']
    aa = [r['angle'] for r in R]
    ax.plot(aa, [r['tension'] for r in R], '-o', color=c, lw=2.0, ms=3.5, label=f'{lab} 장력')
    z = [r['angle'] for r in R if r['tension'] < 1.0]
    if z:
        ax.axvline(z[0], color=c, ls='--', lw=1.2, alpha=.7)
        ax.text(z[0] + 2, 92, f'이완 {z[0]}°', color=c, fontsize=8.0, rotation=90,
                va='top')
ax.set_xlabel('관절 굴곡각 (°)', fontsize=8.8)
ax.set_ylabel('편측 장력 (N)', fontsize=8.8)
ax.grid(alpha=.3)
ax.legend(fontsize=8, loc='upper right')
ax.set_ylim(0, 105)
ax.axvspan(82, 90, color=RED, alpha=0.12)
ax.text(86, 45, '스툽의\n어깨각\n88°', ha='center', fontsize=7.8, color=RED,
        linespacing=1.4, fontweight='bold')

# ── (5) 보조 토크 vs 요구 ────────────────────────────────────────
ax = fig.add_subplot(gs[1, 1])
panel(ax, '(5) 보조 토크(양측 합) 최대치 vs 실제 요구')
LBL = ['어깨\n스트랩', '어깨\n캡(무효)', '팔꿈치']
sup = [G['gates']['shoulder_strap']['tau_max'], G['gates']['shoulder_cap']['tau_max'],
       G['gates']['elbow_bow']['tau_max']]
x = np.arange(3)
cols = [ORANGE, '0.7', PURPLE]
ax.bar(x, sup, 0.5, color=cols, ec='k', lw=.7)
for xi, v in zip(x, sup):
    ax.text(xi, v + 0.4, f'{v:.1f}', ha='center', fontsize=9, fontweight='bold')
ax.axhline(A5['carry']['elv'], color=ORANGE, ls='--', lw=1.5)
ax.text(2.45, A5['carry']['elv'] + 0.5, f"운반 어깨 요구 {A5['carry']['elv']:.1f}",
        ha='right', fontsize=7.8, color=ORANGE)
ax.axhline(A5['carry']['elbow'], color=PURPLE, ls=':', lw=1.5)
ax.text(2.45, A5['carry']['elbow'] + 0.5, f"운반 팔꿈치 요구 {A5['carry']['elbow']:.1f}",
        ha='right', fontsize=7.8, color=PURPLE)
ax.set_xticks(x)
ax.set_xticklabels(LBL, fontsize=8.4, linespacing=1.35)
ax.set_ylabel('토크 (N·m)', fontsize=8.8)
ax.grid(axis='y', alpha=.3)
ax.set_ylim(0, 28)
ax.text(0.5, 0.055, '팔 슈트가 낼 수 있는 최대 보조는 요구의 21~24 %',
        transform=ax.transAxes, ha='center', fontsize=8.2, color='0.25',
        bbox=dict(boxstyle='round,pad=0.28', fc='white', ec='0.6', lw=0.7))

# ── (6) 판정 ─────────────────────────────────────────────────────
ax = fig.add_subplot(gs[1, 2])
panel(ax, '(6) ★ 판정 — 본 해석(SO 5조건) 착수 전 중단')
ax.axis('off')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ITEMS = [
    ('게이트 · 팔꿈치', '통과 7/7  (r 51.3 vs 주동근 30.9 mm)', GREEN),
    ('게이트 · 어깨', '미달 — 스트랩 4/8, 캡은 50° 이상 경로 무효', RED),
    ('스팬 정합', '이두근 견갑 기점 → 기본안 불일치 확인', ORANGE),
    ('스툽 팔 부하', '팔꿈치 0.09 · 어깨 0.73 N·m → 사실상 0', RED),
    ('스툽 어깨각', '88° — 슈트 이완(80°) 구간 → 어깨 보조 0', RED),
]
y = 0.93
for lab, val, c in ITEMS:
    ax.text(0.0, y, lab, fontsize=8.8, fontweight='bold')
    ax.text(0.03, y - 0.052, val, fontsize=8.0, color=c)
    y -= 0.135
ax.add_patch(FancyBboxPatch((0.0, 0.02), 1.0, 0.24, boxstyle='round,pad=0.014',
                            fc='#fdecea', ec=RED, lw=1.4))
ax.text(0.5, 0.185, '■2·■3 착수 보류', ha='center', fontsize=10.4,
        fontweight='bold', color=RED)
ax.text(0.5, 0.095,
        '어깨 게이트 미달 + 스툽 팔 무부하.\n'
        '스툽 5조건 분해는 0 근처 노이즈 비교가 된다.\n'
        '운반(어깨 23.1 · 팔꿈치 24.7 N·m)으로 전환 필요.',
        ha='center', va='center', fontsize=8.2, linespacing=1.55, color='0.2')

P = f'{OUT}/arm_suit_phase1_grid.png'
fig.savefig(P, dpi=150)
print('SAVED', P)
