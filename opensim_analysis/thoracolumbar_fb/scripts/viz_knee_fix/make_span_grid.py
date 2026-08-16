"""[5] 재분배 원인 분리 + 상부 고정 높이 스윕 검증 그리드."""
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
R = json.load(open('/data/suit_span/results.json'))
M5 = json.load(open('/data/suit_span/redistribution_5motion.json'))
SP = json.load(open('/data/suit_multijoint/level_depths.json'))
GREEN, RED, ORANGE, BLUE = '#1a7f37', '#c44e52', '#b3541e', '#4c72b0'
C = R['cond']

fig = plt.figure(figsize=(17.2, 11.6))
gs = fig.add_gridspec(2, 3, hspace=0.52, wspace=0.34,
                      left=0.115, right=0.975, top=0.885, bottom=0.085)
fig.suptitle('재분배 원인 분리 — 부여 스팬 vs 부여 방식 · 상부 고정 높이 스윕',
             fontsize=14.5, fontweight='bold', y=0.958)
fig.text(0.5, 0.922,
         '스툽 · 전 조건 16.5 N·m · 모델 해시 ca12f321326e · tight reserve · OFF 재사용  |  '
         '주의: 현 하드웨어는 L1 고정, 그 위는 설계 제안  |  2026-08-16',
         ha='center', fontsize=9.3, color='0.3')


def panel(ax, t):
    ax.set_title(t, fontsize=10.4, fontweight='bold', pad=8, loc='left')


# ── (1) 4조건 근육군 히트맵 ───────────────────────────────────
ax = fig.add_subplot(gs[0, :2])
panel(ax, '(1) ★ 원인 분리 — 4조건 × 근육군 변화율 (%)  음수 = 감소(좋음)')
ROWS = [('(i) 커플 · T1↔골반', 'couple_T1_16', '스팬 넓음 · 커플'),
        ('(ii) 커플 · L1↔골반', 'couple_L1', '스팬 좁음 · 커플'),
        ('(iii) 경로힘 · L1→허벅지', 'path_L1', '스팬 좁음 · 경로힘'),
        ('(iv) 경로힘 · T8→허벅지', 'path_T8', '스팬 넓음 · 경로힘')]
GS = ['IL', 'LTpL', 'LTpT', 'ES']
Z = np.array([[C[k][g]['rel'] for g in GS] for _, k, _ in ROWS])
vmax = np.abs(Z).max()
im = ax.imshow(Z, cmap='RdBu_r', vmin=-vmax, vmax=vmax, aspect='auto')
for i in range(Z.shape[0]):
    for j in range(Z.shape[1]):
        ax.text(j, i, f'{Z[i, j]:+.1f}', ha='center', va='center',
                fontsize=10.5, fontweight='bold',
                color='white' if abs(Z[i, j]) > vmax * 0.55 else 'k')
ax.set_xticks(range(len(GS)))
ax.set_xticklabels(['IL\n(장늑근)', 'LTpL\n(최장근 요추부)', 'LTpT\n(최장근 흉추부)',
                    'ES 전체'], fontsize=8.8, linespacing=1.4)
ax.set_yticks(range(len(ROWS)))
ax.set_yticklabels([f'{a}\n{c}' for a, _, c in ROWS], fontsize=7.8, linespacing=1.35)
plt.colorbar(im, ax=ax, fraction=0.028, pad=0.02, label='변화율 (%)')
ax.set_xlabel('근육군', fontsize=9)

# ── (2) 원인 분리 판정 ────────────────────────────────────────
ax = fig.add_subplot(gs[0, 2]); panel(ax, '(2) ★ 지배 원인 판정')
ax.axis('off'); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
e = {k: C[k]['ES']['rel'] for k in C}
d_span = e['couple_L1'] - e['couple_T1_16']
d_mode = e['path_L1'] - e['couple_L1']
y = 0.94
for lab, k, note in ROWS:
    ax.text(0.0, y, lab, fontsize=8.6, fontweight='bold')
    ax.text(0.04, y - 0.055, note, fontsize=7.8, color='0.4')
    v = e[k]
    ax.text(0.97, y - 0.03, f'{v:+.1f} %', fontsize=10.5, ha='right', fontweight='bold',
            color=GREEN if v < -5 else (RED if v > 5 else ORANGE))
    y -= 0.145
ax.plot([0, 1], [0.36, 0.36], color='0.5', lw=0.9)
ax.text(0.0, 0.31, f'스팬 효과  (i)→(ii)', fontsize=8.6)
ax.text(0.97, 0.31, f'{d_span:+.1f} %p', fontsize=9.4, ha='right', fontweight='bold')
ax.text(0.0, 0.245, f'방식 효과  (ii)→(iii)', fontsize=8.6)
ax.text(0.97, 0.245, f'{d_mode:+.1f} %p', fontsize=9.4, ha='right', fontweight='bold')
dom = '부여 스팬' if abs(d_span) > abs(d_mode) else '부여 방식 (지점 집중)'
ax.add_patch(FancyBboxPatch((0.0, 0.02), 1.0, 0.17, boxstyle='round,pad=0.012',
                            fc='#eaf6ec', ec=GREEN, lw=1.3))
ax.text(0.5, 0.105, f'지배 원인: {dom}', ha='center', va='center',
        fontsize=10.0, fontweight='bold', color=GREEN)

# ── (3) 상부 고정 높이 스윕 ───────────────────────────────────
ax = fig.add_subplot(gs[1, 0]); panel(ax, '(3) ★ 상부 고정 높이 스윕 (경로힘)')
SW = [('L1\n(현재)', 'path_L1'), ('T12', 'path_T12'), ('T8', 'path_T8'), ('T4', 'path_T4')]
x = np.arange(len(SW))
es = [C[k]['ES']['rel'] for _, k in SW]
cols = ['0.62'] + [GREEN if v < -5 else (RED if v > 5 else ORANGE) for v in es[1:]]
ax.bar(x, es, 0.55, color=cols, ec='k', lw=.7)
for xi, v in zip(x, es):
    ax.text(xi, v + (1.2 if v >= 0 else -2.6), f'{v:+.1f} %', ha='center',
            fontsize=9.0, fontweight='bold')
ax.axhline(0, color='k', lw=1)
ax.axhline(e['couple_T1_16'], color=BLUE, ls='--', lw=1.6)
ax.text(len(SW) - 0.4, e['couple_T1_16'] - 1.6, f"이상적 분산 부여 {e['couple_T1_16']:+.1f} %",
        fontsize=8.0, color=BLUE, ha='right')
ax.set_xticks(x); ax.set_xticklabels([l for l, _ in SW], fontsize=8.6, linespacing=1.35)
ax.set_ylabel('ES peak 변화율 (%)', fontsize=8.8)
ax.grid(axis='y', alpha=.3)
lo = min(es + [e['couple_T1_16']]); hi = max(es)
ax.set_ylim(lo - 6, hi + 6)
ax.text(0.5, 0.04, '주의: 현 하드웨어는 L1. T12 이상은 설계 제안',
        transform=ax.transAxes, ha='center', fontsize=8.0, color='0.3',
        bbox=dict(boxstyle='round,pad=0.28', fc='white', ec='0.6', lw=0.7))

# ── (4) 5동작 재집계 ──────────────────────────────────────────
ax = fig.add_subplot(gs[1, 1]); panel(ax, '(4) 5동작 근육군 변화 방향 재집계')
NM = {'squat': '스쿼트', 'stoop': '스툽', 'box': '들기', 'gait': '보행', 'carry': '운반'}
ORD = ['gait', 'squat', 'stoop', 'carry', 'box']
G3 = ['IL', 'LTpL', 'LTpT']
Z2 = np.array([[M5[k][g]['rel'] for g in G3] for k in ORD])
v2 = np.abs(Z2).max()
im2 = ax.imshow(Z2, cmap='RdBu_r', vmin=-v2, vmax=v2, aspect='auto')
for i in range(Z2.shape[0]):
    for j in range(Z2.shape[1]):
        ax.text(j, i, f'{Z2[i, j]:+.0f}', ha='center', va='center', fontsize=9.4,
                fontweight='bold',
                color='white' if abs(Z2[i, j]) > v2 * 0.55 else 'k')
ax.set_xticks(range(3)); ax.set_xticklabels(G3, fontsize=8.8)
ax.set_yticks(range(len(ORD)))
ax.set_yticklabels([f"{NM[k]}\nOFF {M5[k]['IL']['off']:.0f} %" for k in ORD],
                   fontsize=8.0, linespacing=1.35)
plt.colorbar(im2, ax=ax, fraction=0.04, pad=0.03, label='변화율 (%)')
ax.text(0.5, 0.02, '5동작은 전부 흉추1↔골반 커플(넓은 스팬).\n'
        '재분배는 보행 1건뿐 — 원인은 스팬이 아니라 과보조.',
        transform=ax.transAxes, ha='center', va='bottom', fontsize=7.8,
        linespacing=1.5, color='0.2',
        bbox=dict(boxstyle='round,pad=0.28', fc='white', ec='0.55', lw=0.7))

# ── (5) 시상면 경로 오버레이 ──────────────────────────────────
ax = fig.add_subplot(gs[1, 2]); panel(ax, '(5) 시상면 — L1 고정 vs 흉추 고정')
LUMB = ['L1_L2_FE', 'L2_L3_FE', 'L3_L4_FE', 'L4_L5_FE', 'L5_S1_FE']   # 위 → 아래
ys = [SP[c]['jc'][1] for c in LUMB]
jx = [SP[c]['jc'][0] for c in LUMB]
esx = [SP[c]['jc'][0] - SP[c]['es_depth'] / 1000 for c in LUMB]
sx = [x - 0.015 for x in esx]
FEM = (-0.075, -0.14)
ax.plot(jx, ys, 'o-', color='k', lw=1.5, ms=5, label='관절 중심 (요추)')
ax.plot(esx, ys, 's-', color=BLUE, lw=1.3, ms=4, label='ES 후방 외피')
ax.plot(sx + [FEM[0]], ys + [FEM[1]], 'D-', color=ORANGE, lw=2.6, ms=6, mec='k',
        label='현 하드웨어 (L1 → 허벅지)')
TOPX, TOPY = [-0.086, -0.084, -0.081], [0.45, 0.38, 0.31]      # T4 · T6 · T8 근사
ax.plot(TOPX[::-1] + sx + [FEM[0]], TOPY[::-1] + ys + [FEM[1]], '^--', color=GREEN,
        lw=2.0, ms=6, mec='k', label='설계 제안 (T8 → 허벅지)')
ax.axhspan(0.26, 0.48, color=GREEN, alpha=0.10)
ax.text(-0.021, 0.415, '흉추 구간\n(현 하드웨어는\n보조 없음)', fontsize=7.6, color=GREEN,
        linespacing=1.4, ha='left', va='top')
ax.set_xlabel('전후 위치 x (m) — 왼쪽이 후방', fontsize=8.8)
ax.set_ylabel('상하 위치 y (m)', fontsize=8.8)
ax.invert_xaxis(); ax.grid(alpha=.3); ax.legend(fontsize=7.0, loc='lower left')

P = f'{OUT}/span_verification_grid.png'
fig.savefig(P, dpi=150)
print('SAVED', P)
